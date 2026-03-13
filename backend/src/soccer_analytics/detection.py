from __future__ import annotations

import os

import numpy as np
import supervision as sv

from soccer_analytics.config import DetectionConfig


# Class names from the Roboflow soccer model
_PLAYER_CLASSES = {"player", "goalkeeper"}
_BALL_CLASSES = {"ball"}


class SoccerDetector:
    """Wraps a Roboflow soccer detection model."""

    def __init__(self, config: DetectionConfig | None = None) -> None:
        config = config or DetectionConfig()

        api_key = os.environ.get("ROBOFLOW_API_KEY")
        if not api_key:
            raise EnvironmentError(
                "ROBOFLOW_API_KEY environment variable is required. "
                "Get one at https://roboflow.com/settings/api-key"
            )

        from inference import get_model

        self._model = get_model(model_id=config.model_id, api_key=api_key)
        self._confidence = config.confidence

    def detect(
        self, frame: np.ndarray
    ) -> tuple[sv.Detections, sv.Detections]:
        """Run detection on a frame.

        Returns:
            (player_detections, ball_detections)
        """
        results = self._model.infer(frame, confidence=self._confidence)[0]
        detections = sv.Detections.from_inference(
            results.dict(by_alias=True, exclude_none=True)
        )

        if len(detections) == 0:
            empty = sv.Detections.empty()
            return empty, empty

        class_names = detections.data.get("class_name", np.array([]))

        player_mask = np.array(
            [cn in _PLAYER_CLASSES for cn in class_names], dtype=bool
        )
        ball_mask = np.array(
            [cn in _BALL_CLASSES for cn in class_names], dtype=bool
        )

        return detections[player_mask], detections[ball_mask]
