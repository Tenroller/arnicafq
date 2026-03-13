from __future__ import annotations

import json
import math
from pathlib import Path

import numpy as np
import pytest
import supervision as sv

from soccer_analytics.analytics import GameAnalytics, GameEvent, PlayerStats
from soccer_analytics.config import AnalyticsConfig


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_detections(
    boxes: list[list[float]],
    tracker_ids: list[int] | None = None,
) -> sv.Detections:
    if not boxes:
        dets = sv.Detections.empty()
        if tracker_ids is not None:
            dets.tracker_id = np.array(tracker_ids, dtype=int)
        return dets
    dets = sv.Detections(xyxy=np.array(boxes, dtype=float))
    if tracker_ids is not None:
        dets.tracker_id = np.array(tracker_ids, dtype=int)
    return dets


def _default_analytics(
    fps: float = 30.0,
    width: int = 1920,
    height: int = 1080,
    **overrides,
) -> GameAnalytics:
    cfg = AnalyticsConfig(**overrides)
    return GameAnalytics(config=cfg, fps=fps, video_width=width, video_height=height)


# ---------------------------------------------------------------------------
# Possession tests
# ---------------------------------------------------------------------------

class TestPossession:
    def test_full_possession_team_0(self):
        ga = _default_analytics(possession_distance_threshold=200.0)

        # Player from team 0 near ball for 10 frames
        player_dets = _make_detections([[100, 100, 120, 120]], tracker_ids=[1])
        ball_dets = _make_detections([[110, 110, 115, 115]], tracker_ids=[10])
        team_ids = np.array([0])

        for i in range(10):
            ga.update(i, player_dets, ball_dets, team_ids)

        poss = ga.get_possession()
        assert poss["team_0"] == 100.0
        assert poss["team_1"] == 0.0

    def test_split_possession(self):
        ga = _default_analytics(possession_distance_threshold=200.0)

        player_t0 = _make_detections([[100, 100, 120, 120]], tracker_ids=[1])
        player_t1 = _make_detections([[500, 500, 520, 520]], tracker_ids=[2])
        ball_near_t0 = _make_detections([[110, 110, 115, 115]], tracker_ids=[10])
        ball_near_t1 = _make_detections([[510, 510, 515, 515]], tracker_ids=[10])

        # 5 frames near team 0
        for i in range(5):
            ga.update(i, player_t0, ball_near_t0, np.array([0]))

        # 5 frames near team 1
        for i in range(5, 10):
            ga.update(i, player_t1, ball_near_t1, np.array([1]))

        poss = ga.get_possession()
        assert poss["team_0"] == 50.0
        assert poss["team_1"] == 50.0

    def test_no_ball(self):
        ga = _default_analytics()
        player_dets = _make_detections([[100, 100, 120, 120]], tracker_ids=[1])
        ball_dets = _make_detections([])
        team_ids = np.array([0])

        ga.update(0, player_dets, ball_dets, team_ids)
        poss = ga.get_possession()
        assert poss["team_0"] == 0.0
        assert poss["team_1"] == 0.0

    def test_ball_too_far(self):
        ga = _default_analytics(possession_distance_threshold=50.0)
        player_dets = _make_detections([[100, 100, 120, 120]], tracker_ids=[1])
        ball_dets = _make_detections([[800, 800, 810, 810]], tracker_ids=[10])
        team_ids = np.array([0])

        ga.update(0, player_dets, ball_dets, team_ids)
        poss = ga.get_possession()
        assert poss["team_0"] == 0.0
        assert poss["team_1"] == 0.0


# ---------------------------------------------------------------------------
# Player stats tests
# ---------------------------------------------------------------------------

class TestPlayerStats:
    def test_distance_calculation(self):
        ga = _default_analytics(fps=30.0)

        # Player moves 10px right each frame for 5 frames
        for i in range(5):
            x = 100 + i * 10
            player_dets = _make_detections([[x, 100, x + 20, 120]], tracker_ids=[1])
            ball_dets = _make_detections([])
            ga.update(i, player_dets, ball_dets, np.array([0]))

        stats = ga.get_player_stats()
        assert len(stats) == 1
        # 4 movements of 10px each = 40px total
        assert stats[0]["distance_px"] == 40.0

    def test_speed_calculation(self):
        ga = _default_analytics(fps=10.0)

        for i in range(3):
            x = 100 + i * 20
            player_dets = _make_detections([[x, 100, x + 20, 120]], tracker_ids=[1])
            ga.update(i, player_dets, _make_detections([]), np.array([0]))

        stats = ga.get_player_stats()
        # 2 displacements of 20px each, total = 40px, 3 frames
        # avg_speed = (40 / 3) * 10 = 133.3
        assert stats[0]["avg_speed_px_per_s"] == pytest.approx(133.3, abs=0.1)
        # max speed = 20 * 10 = 200
        assert stats[0]["max_speed_px_per_s"] == 200.0

    def test_sprint_detection(self):
        ga = _default_analytics(fps=1.0, sprint_speed_threshold=10.0)

        # Frame 0: player at x=100
        ga.update(0, _make_detections([[100, 100, 120, 120]], tracker_ids=[1]),
                  _make_detections([]), np.array([0]))
        # Frame 1: player moved 15px (above sprint threshold)
        ga.update(1, _make_detections([[115, 100, 135, 120]], tracker_ids=[1]),
                  _make_detections([]), np.array([0]))
        # Frame 2: player moved 5px (below sprint threshold)
        ga.update(2, _make_detections([[120, 100, 140, 120]], tracker_ids=[1]),
                  _make_detections([]), np.array([0]))

        stats = ga.get_player_stats()
        assert stats[0]["sprints"] == 1

    def test_multiple_players_independent(self):
        ga = _default_analytics()

        # Two players tracked independently
        for i in range(3):
            p1_x = 100 + i * 10
            p2_x = 500 + i * 20
            player_dets = _make_detections(
                [[p1_x, 100, p1_x + 20, 120], [p2_x, 200, p2_x + 20, 220]],
                tracker_ids=[1, 2],
            )
            ga.update(i, player_dets, _make_detections([]), np.array([0, 1]))

        stats = ga.get_player_stats()
        assert len(stats) == 2
        by_id = {s["tracker_id"]: s for s in stats}
        assert by_id[1]["distance_px"] == 20.0  # 2 * 10
        assert by_id[2]["distance_px"] == 40.0  # 2 * 20

    def test_player_reappearance_skip_large_jump(self):
        ga = _default_analytics(fps=30.0)

        # Frame 0: player at (100, 100)
        ga.update(0, _make_detections([[100, 100, 120, 120]], tracker_ids=[1]),
                  _make_detections([]), np.array([0]))
        # Frame 1: player "reappears" far away (should be skipped)
        ga.update(1, _make_detections([[1800, 1000, 1820, 1020]], tracker_ids=[1]),
                  _make_detections([]), np.array([0]))

        stats = ga.get_player_stats()
        # The jump should be skipped since it's > 50% of frame diagonal
        assert stats[0]["distance_px"] == 0.0


# ---------------------------------------------------------------------------
# Event detection tests
# ---------------------------------------------------------------------------

class TestEvents:
    def test_pass_same_team(self):
        ga = _default_analytics(
            possession_distance_threshold=200.0,
            pass_min_frames=1,
            pass_max_distance=300.0,
        )

        # Player 1 has ball
        p1 = _make_detections([[100, 100, 120, 120]], tracker_ids=[1])
        ball = _make_detections([[110, 110, 115, 115]], tracker_ids=[10])
        for i in range(3):
            ga.update(i, p1, ball, np.array([0]))

        # Ball moves to player 2 (same team)
        p2 = _make_detections([[200, 100, 220, 120]], tracker_ids=[2])
        ball2 = _make_detections([[205, 105, 210, 110]], tracker_ids=[10])
        ga.update(3, p2, ball2, np.array([0]))

        events = ga.get_events()
        pass_events = [e for e in events if e["event_type"] == "pass"]
        assert len(pass_events) >= 1
        assert pass_events[0]["team_id"] == 0
        assert pass_events[0]["details"]["from"] == 1
        assert pass_events[0]["details"]["to"] == 2

    def test_no_pass_different_team(self):
        ga = _default_analytics(
            possession_distance_threshold=200.0,
            pass_min_frames=1,
        )

        # Player 1 (team 0) has ball
        p1 = _make_detections([[100, 100, 120, 120]], tracker_ids=[1])
        ball = _make_detections([[110, 110, 115, 115]], tracker_ids=[10])
        for i in range(3):
            ga.update(i, p1, ball, np.array([0]))

        # Ball moves to player 2 (team 1 — interception, not a pass)
        p2 = _make_detections([[200, 100, 220, 120]], tracker_ids=[2])
        ball2 = _make_detections([[205, 105, 210, 110]], tracker_ids=[10])
        ga.update(3, p2, ball2, np.array([1]))

        events = ga.get_events()
        pass_events = [e for e in events if e["event_type"] == "pass"]
        assert len(pass_events) == 0

    def test_shot_detection(self):
        ga = _default_analytics(
            fps=30.0,
            shot_velocity_threshold=25.0,
            goal_edge_margin=0.1,
            possession_distance_threshold=500.0,
        )

        # Set up possessor
        p1 = _make_detections([[100, 500, 120, 520]], tracker_ids=[1])
        ball1 = _make_detections([[110, 510, 115, 515]], tracker_ids=[10])
        ga.update(0, p1, ball1, np.array([0]))

        # Ball moves fast toward left edge (x < width * margin)
        ball2 = _make_detections([[50, 510, 55, 515]], tracker_ids=[10])
        ga.update(1, p1, ball2, np.array([0]))

        events = ga.get_events()
        shot_events = [e for e in events if e["event_type"] == "shot"]
        assert len(shot_events) >= 1

    def test_goal_detection(self):
        ga = _default_analytics(
            fps=30.0,
            shot_velocity_threshold=25.0,
            goal_edge_margin=0.1,  # 192px margin, goal margin = 96px
            possession_distance_threshold=500.0,
        )

        # Ball starts in play
        p1 = _make_detections([[100, 500, 120, 520]], tracker_ids=[1])
        ball1 = _make_detections([[110, 510, 115, 515]], tracker_ids=[10])
        ga.update(0, p1, ball1, np.array([0]))

        # Ball moves very fast into goal region (x near 0)
        ball2 = _make_detections([[10, 510, 15, 515]], tracker_ids=[10])
        ga.update(1, p1, ball2, np.array([0]))

        events = ga.get_events()
        goal_events = [e for e in events if e["event_type"] == "goal"]
        assert len(goal_events) >= 1


# ---------------------------------------------------------------------------
# Output tests
# ---------------------------------------------------------------------------

class TestOutput:
    def test_report_prints_without_error(self, capsys):
        ga = _default_analytics()
        p = _make_detections([[100, 100, 120, 120]], tracker_ids=[1])
        b = _make_detections([[110, 110, 115, 115]], tracker_ids=[10])
        ga.update(0, p, b, np.array([0]))

        ga.report()
        captured = capsys.readouterr()
        assert "Game Analytics Report" in captured.out
        assert "Possession" in captured.out

    def test_save_json(self, tmp_path):
        ga = _default_analytics()
        p = _make_detections([[100, 100, 120, 120]], tracker_ids=[1])
        b = _make_detections([[110, 110, 115, 115]], tracker_ids=[10])
        ga.update(0, p, b, np.array([0]))

        json_path = tmp_path / "output.json"
        ga.save_json(json_path)

        assert json_path.exists()
        data = json.loads(json_path.read_text())
        assert "possession" in data
        assert "player_stats" in data
        assert "events" in data
        assert "team_0" in data["possession"]
        assert "team_1" in data["possession"]
        assert isinstance(data["player_stats"], list)
        assert isinstance(data["events"], list)


# ---------------------------------------------------------------------------
# Edge cases
# ---------------------------------------------------------------------------

class TestEdgeCases:
    def test_empty_detections(self):
        ga = _default_analytics()
        ga.update(
            0,
            _make_detections([]),
            _make_detections([]),
            np.array([]),
        )
        poss = ga.get_possession()
        assert poss["team_0"] == 0.0
        assert poss["team_1"] == 0.0
        assert ga.get_player_stats() == []
        assert ga.get_events() == []

    def test_single_frame(self):
        ga = _default_analytics(possession_distance_threshold=200.0)
        p = _make_detections([[100, 100, 120, 120]], tracker_ids=[1])
        b = _make_detections([[110, 110, 115, 115]], tracker_ids=[10])
        ga.update(0, p, b, np.array([0]))

        poss = ga.get_possession()
        assert poss["team_0"] == 100.0
        stats = ga.get_player_stats()
        assert len(stats) == 1
        assert stats[0]["distance_px"] == 0.0

    def test_no_tracker_ids(self):
        ga = _default_analytics()
        p = _make_detections([[100, 100, 120, 120]])  # no tracker_ids
        b = _make_detections([[110, 110, 115, 115]])
        ga.update(0, p, b, np.array([0]))
        # Should not crash
        assert ga.get_player_stats() == []
