from __future__ import annotations

import sys
from collections.abc import Callable
from pathlib import Path

import supervision as sv

from soccer_analytics.config import Config
from soccer_analytics.detection import SoccerDetector
from soccer_analytics.tracking import ObjectTracker
from soccer_analytics.team_classifier import TeamClassifier
from soccer_analytics.annotation import VideoAnnotator
from soccer_analytics.analytics import GameAnalytics


def run(
    input_path: str,
    output_path: str,
    config: Config,
    progress_callback: Callable[[str, int, int], None] | None = None,
) -> dict | None:
    """Run the full soccer analysis pipeline.

    Phase 1: Calibration — detect players on first N frames to fit team classifier.
    Phase 2: Full processing — detect, track, classify, annotate, write all frames.
    """
    input_path = str(Path(input_path).resolve())
    output_path = str(Path(output_path).resolve())

    video_info = sv.VideoInfo.from_video_path(input_path)
    total_frames = video_info.total_frames
    fps = video_info.fps

    print(f"Input: {input_path}")
    print(f"Resolution: {video_info.width}x{video_info.height} @ {fps} fps")
    print(f"Total frames: {total_frames}")
    print()

    detector = SoccerDetector(config.detection)
    team_classifier = TeamClassifier(config.team_classification)
    calibration_frames = config.team_classification.calibration_frames

    # ── Phase 1: Calibration ──
    print(f"Phase 1: Calibrating team colors ({calibration_frames} frames)...")
    cal_generator = sv.get_video_frames_generator(input_path)

    for i, frame in enumerate(cal_generator):
        if i >= calibration_frames:
            break
        player_dets, _ = detector.detect(frame)
        team_classifier.accumulate(frame, player_dets)
        if progress_callback:
            progress_callback("calibrating", i + 1, calibration_frames)
        else:
            _progress(i + 1, calibration_frames, "Calibrating")

    print()
    team_classifier.fit()
    print(f"Team calibration complete. Collected {len(team_classifier._jersey_colors)} color samples.")
    print()

    # ── Phase 2: Full processing ──
    print("Phase 2: Processing full video...")

    # Fresh tracker instances for clean IDs from frame 0
    player_tracker = ObjectTracker(config.tracking)
    ball_tracker = ObjectTracker(config.tracking)
    annotator = VideoAnnotator(config.annotation)

    analytics: GameAnalytics | None = None
    if config.analytics.enabled:
        analytics = GameAnalytics(
            config=config.analytics,
            fps=fps,
            video_width=video_info.width,
            video_height=video_info.height,
        )

    frame_generator = sv.get_video_frames_generator(input_path)

    with sv.VideoSink(target_path=output_path, video_info=video_info) as sink:
        for i, frame in enumerate(frame_generator):
            player_dets, ball_dets = detector.detect(frame)
            player_dets = player_tracker.update(player_dets)
            ball_dets = ball_tracker.update(ball_dets)

            team_ids = team_classifier.predict(frame, player_dets)

            possession = None
            if analytics is not None:
                analytics.update(i, player_dets, ball_dets, team_ids)
                if config.analytics.overlay_stats:
                    possession = analytics.get_possession()

            annotated = annotator.annotate(
                frame, player_dets, ball_dets, team_ids, possession=possession
            )
            sink.write_frame(annotated)

            if progress_callback:
                progress_callback("processing", i + 1, total_frames)
            else:
                _progress(i + 1, total_frames, "Processing")

    if not progress_callback:
        print()

    analytics_result: dict | None = None
    if analytics is not None:
        analytics_result = {
            "possession": analytics.get_possession(),
            "player_stats": analytics.get_player_stats(),
            "events": analytics.get_events(),
        }
        if not progress_callback:
            analytics.report()
        if config.analytics.save_json:
            json_path = str(Path(output_path).with_suffix(".json"))
            analytics.save_json(json_path)
            if not progress_callback:
                print(f"Analytics JSON saved to: {json_path}")

    if not progress_callback:
        print(f"Done! Output saved to: {output_path}")

    return analytics_result


def _progress(current: int, total: int, label: str) -> None:
    pct = current / total * 100 if total > 0 else 0
    bar_len = 40
    filled = int(bar_len * current / total) if total > 0 else 0
    bar = "=" * filled + "-" * (bar_len - filled)
    sys.stdout.write(f"\r{label}: [{bar}] {current}/{total} ({pct:.1f}%)")
    sys.stdout.flush()
