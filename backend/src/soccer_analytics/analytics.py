from __future__ import annotations

import json
import math
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
import supervision as sv

from soccer_analytics.config import AnalyticsConfig


@dataclass
class GameEvent:
    frame_index: int
    timestamp: float
    event_type: str  # "pass", "shot", "goal"
    team_id: int
    player_id: int
    details: dict = field(default_factory=dict)


@dataclass
class PlayerStats:
    tracker_id: int
    team_id: int
    total_distance: float = 0.0
    max_speed: float = 0.0
    sprint_frames: int = 0
    ball_frames: int = 0
    last_center: tuple[float, float] | None = None
    frame_count: int = 0


class GameAnalytics:
    """Heuristic game analytics computed per-frame from detection data."""

    def __init__(
        self,
        config: AnalyticsConfig,
        fps: float,
        video_width: int,
        video_height: int,
    ) -> None:
        self._config = config
        self._fps = fps
        self._video_width = video_width
        self._video_height = video_height
        self._frame_diagonal = math.hypot(video_width, video_height)

        # Possession counters per team
        self._possession_frames: dict[int, int] = {0: 0, 1: 0}
        # Player stats keyed by tracker_id
        self._player_stats: dict[int, PlayerStats] = {}
        # Detected events
        self._events: list[GameEvent] = []

        # Ball state tracking for event detection
        self._last_possessor_id: int | None = None
        self._last_possessor_team: int | None = None
        self._last_ball_center: tuple[float, float] | None = None
        self._frames_since_last_pass: int = 0

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def update(
        self,
        frame_index: int,
        player_detections: sv.Detections,
        ball_detections: sv.Detections,
        team_ids: np.ndarray | None = None,
    ) -> None:
        """Process one frame of data."""
        self._frames_since_last_pass += 1

        player_centers = self._centers(player_detections)
        ball_center = self._ball_center(ball_detections)

        tracker_ids = (
            player_detections.tracker_id
            if player_detections.tracker_id is not None
            else None
        )

        # --- player stats ---
        if tracker_ids is not None and team_ids is not None:
            for idx, tid in enumerate(tracker_ids):
                tid = int(tid)
                team = int(team_ids[idx])
                center = tuple(player_centers[idx])

                if tid not in self._player_stats:
                    self._player_stats[tid] = PlayerStats(
                        tracker_id=tid, team_id=team
                    )

                ps = self._player_stats[tid]
                ps.frame_count += 1
                ps.team_id = team  # update in case of reclassification

                if ps.last_center is not None:
                    dx = center[0] - ps.last_center[0]
                    dy = center[1] - ps.last_center[1]
                    dist = math.hypot(dx, dy)
                    # Skip unreasonably large jumps (tracker reappearance)
                    if dist < self._frame_diagonal * 0.5:
                        ps.total_distance += dist
                        speed = dist  # px/frame
                        if speed > ps.max_speed:
                            ps.max_speed = speed
                        if speed >= self._config.sprint_speed_threshold:
                            ps.sprint_frames += 1

                ps.last_center = center

        # --- possession ---
        if ball_center is not None and tracker_ids is not None and team_ids is not None:
            closest_id, closest_team = self._closest_player_to_ball(
                player_centers, tracker_ids, team_ids, ball_center
            )
            if closest_id is not None:
                self._possession_frames[closest_team] = (
                    self._possession_frames.get(closest_team, 0) + 1
                )
                # Update ball_frames for the possessing player
                if closest_id in self._player_stats:
                    self._player_stats[closest_id].ball_frames += 1

                # --- event detection ---
                self._detect_events(
                    frame_index, closest_id, closest_team, ball_center
                )

                self._last_possessor_id = closest_id
                self._last_possessor_team = closest_team

        # --- shot / goal detection from ball velocity ---
        if ball_center is not None:
            self._detect_shot_goal(frame_index, ball_center)
            self._last_ball_center = ball_center

    def get_possession(self) -> dict[str, float]:
        total = sum(self._possession_frames.values())
        if total == 0:
            return {"team_0": 0.0, "team_1": 0.0}
        return {
            "team_0": round(self._possession_frames.get(0, 0) / total * 100, 1),
            "team_1": round(self._possession_frames.get(1, 0) / total * 100, 1),
        }

    def get_player_stats(self) -> list[dict]:
        results = []
        for ps in self._player_stats.values():
            fps = self._fps if self._fps > 0 else 1
            results.append(
                {
                    "tracker_id": ps.tracker_id,
                    "team_id": ps.team_id,
                    "distance_px": round(ps.total_distance, 1),
                    "avg_speed_px_per_s": (
                        round(ps.total_distance / ps.frame_count * fps, 1)
                        if ps.frame_count > 0
                        else 0.0
                    ),
                    "max_speed_px_per_s": round(ps.max_speed * fps, 1),
                    "sprints": ps.sprint_frames,
                    "time_on_ball_sec": round(ps.ball_frames / fps, 2),
                }
            )
        return results

    def get_events(self) -> list[dict]:
        return [
            {
                "frame_index": e.frame_index,
                "timestamp": e.timestamp,
                "event_type": e.event_type,
                "team_id": e.team_id,
                "player_id": e.player_id,
                "details": e.details,
            }
            for e in self._events
        ]

    def report(self) -> None:
        possession = self.get_possession()
        print("\n=== Game Analytics Report ===")
        print(f"Possession: Team 0 {possession['team_0']}% | Team 1 {possession['team_1']}%")
        print(f"Events detected: {len(self._events)}")
        for e in self._events:
            print(f"  [{e.event_type}] frame {e.frame_index} — team {e.team_id}, player {e.player_id}")
        stats = self.get_player_stats()
        if stats:
            print(f"Player stats ({len(stats)} players tracked):")
            for s in sorted(stats, key=lambda x: x["tracker_id"]):
                print(
                    f"  #{s['tracker_id']} T{s['team_id']}: "
                    f"dist={s['distance_px']}px, "
                    f"avg_spd={s['avg_speed_px_per_s']}px/s, "
                    f"max_spd={s['max_speed_px_per_s']}px/s, "
                    f"sprints={s['sprints']}, "
                    f"ball={s['time_on_ball_sec']}s"
                )
        print("=== End Report ===\n")

    def save_json(self, path: str | Path) -> None:
        data = {
            "possession": self.get_possession(),
            "player_stats": self.get_player_stats(),
            "events": self.get_events(),
        }
        with open(path, "w") as f:
            json.dump(data, f, indent=2)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _centers(detections: sv.Detections) -> np.ndarray:
        if len(detections) == 0:
            return np.empty((0, 2))
        xyxy = detections.xyxy
        return np.column_stack(
            ((xyxy[:, 0] + xyxy[:, 2]) / 2, (xyxy[:, 1] + xyxy[:, 3]) / 2)
        )

    @staticmethod
    def _ball_center(ball_detections: sv.Detections) -> tuple[float, float] | None:
        if len(ball_detections) == 0:
            return None
        xyxy = ball_detections.xyxy[0]
        return ((xyxy[0] + xyxy[2]) / 2, (xyxy[1] + xyxy[3]) / 2)

    def _closest_player_to_ball(
        self,
        player_centers: np.ndarray,
        tracker_ids: np.ndarray,
        team_ids: np.ndarray,
        ball_center: tuple[float, float],
    ) -> tuple[int | None, int]:
        if len(player_centers) == 0:
            return None, 0
        dists = np.hypot(
            player_centers[:, 0] - ball_center[0],
            player_centers[:, 1] - ball_center[1],
        )
        min_idx = int(np.argmin(dists))
        if dists[min_idx] > self._config.possession_distance_threshold:
            return None, 0
        return int(tracker_ids[min_idx]), int(team_ids[min_idx])

    def _detect_events(
        self,
        frame_index: int,
        possessor_id: int,
        possessor_team: int,
        ball_center: tuple[float, float],
    ) -> None:
        # Pass detection: ball transitions between different players on the same team
        if (
            self._last_possessor_id is not None
            and possessor_id != self._last_possessor_id
            and possessor_team == self._last_possessor_team
            and self._frames_since_last_pass >= self._config.pass_min_frames
        ):
            # Check distance between consecutive ball positions isn't too far
            if self._last_ball_center is not None:
                dist = math.hypot(
                    ball_center[0] - self._last_ball_center[0],
                    ball_center[1] - self._last_ball_center[1],
                )
                if dist <= self._config.pass_max_distance:
                    self._events.append(
                        GameEvent(
                            frame_index=frame_index,
                            timestamp=round(frame_index / self._fps, 2),
                            event_type="pass",
                            team_id=possessor_team,
                            player_id=self._last_possessor_id,
                            details={
                                "from": self._last_possessor_id,
                                "to": possessor_id,
                            },
                        )
                    )
                    self._frames_since_last_pass = 0

    def _detect_shot_goal(
        self,
        frame_index: int,
        ball_center: tuple[float, float],
    ) -> None:
        if self._last_ball_center is None:
            return

        dx = ball_center[0] - self._last_ball_center[0]
        dy = ball_center[1] - self._last_ball_center[1]
        velocity = math.hypot(dx, dy)

        margin = self._config.goal_edge_margin
        near_edge = (
            ball_center[0] < self._video_width * margin
            or ball_center[0] > self._video_width * (1 - margin)
        )

        if velocity >= self._config.shot_velocity_threshold and near_edge:
            team = self._last_possessor_team if self._last_possessor_team is not None else -1
            player = self._last_possessor_id if self._last_possessor_id is not None else -1

            self._events.append(
                GameEvent(
                    frame_index=frame_index,
                    timestamp=round(frame_index / self._fps, 2),
                    event_type="shot",
                    team_id=team,
                    player_id=player,
                    details={"velocity": round(velocity, 1)},
                )
            )

            # Goal: ball actually enters the goal region (very close to edge)
            goal_margin = margin * 0.5
            in_goal = (
                ball_center[0] < self._video_width * goal_margin
                or ball_center[0] > self._video_width * (1 - goal_margin)
            )
            if in_goal:
                self._events.append(
                    GameEvent(
                        frame_index=frame_index,
                        timestamp=round(frame_index / self._fps, 2),
                        event_type="goal",
                        team_id=team,
                        player_id=player,
                        details={"velocity": round(velocity, 1)},
                    )
                )
