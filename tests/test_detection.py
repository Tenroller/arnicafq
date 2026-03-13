"""Tests for the detection module."""
import os
from unittest.mock import MagicMock, patch

import numpy as np
import pytest
import supervision as sv

from soccer_analytics.config import DetectionConfig


class TestSoccerDetector:
    def test_missing_api_key_raises(self):
        with patch.dict(os.environ, {}, clear=True):
            os.environ.pop("ROBOFLOW_API_KEY", None)
            from soccer_analytics.detection import SoccerDetector
            with pytest.raises(EnvironmentError, match="ROBOFLOW_API_KEY"):
                SoccerDetector()

    @patch("inference.get_model")
    def test_detect_splits_classes(self, mock_get_model):
        os.environ["ROBOFLOW_API_KEY"] = "test-key"

        mock_model = MagicMock()
        mock_get_model.return_value = mock_model

        # Simulate inference result
        mock_result = MagicMock()
        mock_result.dict.return_value = {
            "predictions": [
                {"x": 100, "y": 100, "width": 50, "height": 100,
                 "confidence": 0.9, "class": "player", "class_id": 0},
                {"x": 200, "y": 200, "width": 50, "height": 100,
                 "confidence": 0.8, "class": "goalkeeper", "class_id": 1},
                {"x": 300, "y": 300, "width": 30, "height": 30,
                 "confidence": 0.7, "class": "ball", "class_id": 2},
                {"x": 400, "y": 400, "width": 50, "height": 100,
                 "confidence": 0.85, "class": "referee", "class_id": 3},
            ],
            "image": {"width": 1920, "height": 1080},
        }
        mock_model.infer.return_value = [mock_result]

        from soccer_analytics.detection import SoccerDetector
        detector = SoccerDetector(DetectionConfig())
        frame = np.zeros((1080, 1920, 3), dtype=np.uint8)
        players, balls = detector.detect(frame)

        # Players should include player + goalkeeper (2), not referee
        assert len(players) == 2
        # Ball should be 1
        assert len(balls) == 1

    @patch("inference.get_model")
    def test_detect_empty_frame(self, mock_get_model):
        os.environ["ROBOFLOW_API_KEY"] = "test-key"

        mock_model = MagicMock()
        mock_get_model.return_value = mock_model

        mock_result = MagicMock()
        mock_result.dict.return_value = {
            "predictions": [],
            "image": {"width": 1920, "height": 1080},
        }
        mock_model.infer.return_value = [mock_result]

        from soccer_analytics.detection import SoccerDetector
        detector = SoccerDetector(DetectionConfig())
        frame = np.zeros((1080, 1920, 3), dtype=np.uint8)
        players, balls = detector.detect(frame)

        assert len(players) == 0
        assert len(balls) == 0
