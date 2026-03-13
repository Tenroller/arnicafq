from __future__ import annotations

import supervision as sv

from soccer_analytics.config import TrackingConfig


class ObjectTracker:
    """ByteTrack wrapper for persistent object tracking."""

    def __init__(self, config: TrackingConfig | None = None) -> None:
        config = config or TrackingConfig()
        self._tracker = sv.ByteTrack(
            track_activation_threshold=config.track_activation_threshold,
            lost_track_buffer=config.lost_track_buffer,
            minimum_matching_threshold=config.minimum_matching_threshold,
            frame_rate=config.frame_rate,
        )

    def update(self, detections: sv.Detections) -> sv.Detections:
        """Update tracker with new detections, returns detections with tracker_id."""
        if len(detections) == 0:
            return detections
        return self._tracker.update_with_detections(detections)

    def reset(self) -> None:
        """Reset tracker state."""
        self._tracker.reset()
