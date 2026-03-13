"""Tests for the tracking module."""
import numpy as np
import supervision as sv

from soccer_analytics.tracking import ObjectTracker
from soccer_analytics.config import TrackingConfig


class TestObjectTracker:
    def test_update_assigns_tracker_ids(self):
        tracker = ObjectTracker(TrackingConfig())
        detections = sv.Detections(
            xyxy=np.array([
                [100, 100, 150, 200],
                [300, 300, 350, 400],
            ], dtype=np.float32),
            confidence=np.array([0.9, 0.8]),
        )
        tracked = tracker.update(detections)
        assert tracked.tracker_id is not None
        assert len(tracked.tracker_id) == 2

    def test_update_empty_detections(self):
        tracker = ObjectTracker(TrackingConfig())
        detections = sv.Detections.empty()
        tracked = tracker.update(detections)
        assert len(tracked) == 0

    def test_separate_trackers_no_cross_contamination(self):
        player_tracker = ObjectTracker(TrackingConfig())
        ball_tracker = ObjectTracker(TrackingConfig())

        player_dets = sv.Detections(
            xyxy=np.array([[100, 100, 150, 200]], dtype=np.float32),
            confidence=np.array([0.9]),
        )
        ball_dets = sv.Detections(
            xyxy=np.array([[500, 500, 520, 520]], dtype=np.float32),
            confidence=np.array([0.8]),
        )

        p_tracked = player_tracker.update(player_dets)
        b_tracked = ball_tracker.update(ball_dets)

        # Both should independently assign IDs
        assert p_tracked.tracker_id is not None
        assert b_tracked.tracker_id is not None

    def test_reset(self):
        tracker = ObjectTracker(TrackingConfig())
        detections = sv.Detections(
            xyxy=np.array([[100, 100, 150, 200]], dtype=np.float32),
            confidence=np.array([0.9]),
        )
        tracker.update(detections)
        tracker.reset()  # Should not raise
