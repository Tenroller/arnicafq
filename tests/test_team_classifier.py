"""Tests for the team classifier module."""
import numpy as np
import pytest
import supervision as sv

from soccer_analytics.team_classifier import TeamClassifier
from soccer_analytics.config import TeamClassificationConfig


def _make_colored_frame(
    color_bgr: tuple[int, int, int], width: int = 640, height: int = 480
) -> np.ndarray:
    """Create a solid-color frame."""
    frame = np.zeros((height, width, 3), dtype=np.uint8)
    frame[:] = color_bgr
    return frame


def _make_detections(n: int = 3) -> sv.Detections:
    """Create dummy detections spread across the frame."""
    boxes = []
    for i in range(n):
        x1 = 50 + i * 100
        y1 = 50
        x2 = x1 + 60
        y2 = y1 + 150
        boxes.append([x1, y1, x2, y2])
    return sv.Detections(
        xyxy=np.array(boxes, dtype=np.float32),
        confidence=np.array([0.9] * n),
    )


class TestTeamClassifier:
    def test_not_fitted_raises_on_predict(self):
        tc = TeamClassifier()
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        dets = _make_detections(1)
        with pytest.raises(RuntimeError, match="fit"):
            tc.predict(frame, dets)

    def test_fit_and_predict(self):
        tc = TeamClassifier(TeamClassificationConfig(calibration_frames=10))

        # Simulate two teams: red jerseys and blue jerseys
        red_frame = _make_colored_frame((0, 0, 200))  # BGR red
        blue_frame = _make_colored_frame((200, 0, 0))  # BGR blue

        red_dets = _make_detections(3)
        blue_dets = _make_detections(3)

        for _ in range(10):
            tc.accumulate(red_frame, red_dets)
            tc.accumulate(blue_frame, blue_dets)

        tc.fit()
        assert tc.is_fitted

        red_teams = tc.predict(red_frame, red_dets)
        blue_teams = tc.predict(blue_frame, blue_dets)

        # All red should be same team, all blue another
        assert len(set(red_teams)) == 1
        assert len(set(blue_teams)) == 1
        assert red_teams[0] != blue_teams[0]

    def test_fit_insufficient_samples(self):
        tc = TeamClassifier()
        with pytest.raises(ValueError, match="Need at least"):
            tc.fit()

    def test_predict_empty_detections(self):
        tc = TeamClassifier()
        # Need to fit first
        frame = _make_colored_frame((100, 100, 100))
        dets = _make_detections(5)
        for _ in range(10):
            tc.accumulate(frame, dets)
        tc.fit()

        empty = sv.Detections.empty()
        result = tc.predict(frame, empty)
        assert len(result) == 0
