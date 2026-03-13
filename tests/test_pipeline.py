"""Tests for the pipeline module."""
from pathlib import Path
from unittest.mock import MagicMock, patch

import numpy as np
import pytest

from soccer_analytics.config import Config


class TestPipeline:
    @patch("soccer_analytics.pipeline.VideoAnnotator")
    @patch("soccer_analytics.pipeline.TeamClassifier")
    @patch("soccer_analytics.pipeline.ObjectTracker")
    @patch("soccer_analytics.pipeline.SoccerDetector")
    @patch("soccer_analytics.pipeline.sv")
    def test_run_processes_frames(
        self, mock_sv, mock_detector_cls, mock_tracker_cls,
        mock_classifier_cls, mock_annotator_cls, tmp_path
    ):
        # Setup mock video info
        mock_video_info = MagicMock()
        mock_video_info.total_frames = 5
        mock_video_info.fps = 30
        mock_video_info.width = 640
        mock_video_info.height = 480
        mock_sv.VideoInfo.from_video_path.return_value = mock_video_info

        # Mock frame generators (one for calibration, one for full processing)
        dummy_frame = np.zeros((480, 640, 3), dtype=np.uint8)
        mock_sv.get_video_frames_generator.side_effect = [
            iter([dummy_frame] * 5),  # calibration
            iter([dummy_frame] * 5),  # full processing
        ]

        # Mock VideoSink
        mock_sink = MagicMock()
        mock_sv.VideoSink.return_value.__enter__ = MagicMock(return_value=mock_sink)
        mock_sv.VideoSink.return_value.__exit__ = MagicMock(return_value=False)

        # Mock detector
        import supervision as sv_real
        mock_detector = MagicMock()
        empty_det = sv_real.Detections.empty()
        mock_detector.detect.return_value = (empty_det, empty_det)
        mock_detector_cls.return_value = mock_detector

        # Mock classifier
        mock_classifier = MagicMock()
        mock_classifier._jersey_colors = list(range(10))
        mock_classifier.predict.return_value = np.array([])
        mock_classifier_cls.return_value = mock_classifier

        # Mock tracker
        mock_tracker = MagicMock()
        mock_tracker.update.return_value = empty_det
        mock_tracker_cls.return_value = mock_tracker

        # Mock annotator
        mock_annotator = MagicMock()
        mock_annotator.annotate.return_value = dummy_frame
        mock_annotator_cls.return_value = mock_annotator

        # Create dummy input file
        input_file = tmp_path / "test.mp4"
        input_file.touch()
        output_file = tmp_path / "output.mp4"

        config = Config()
        config.team_classification.calibration_frames = 3

        from soccer_analytics.pipeline import run
        run(str(input_file), str(output_file), config)

        # Detector should be called for calibration + full processing
        assert mock_detector.detect.call_count > 0
        # Sink should have written frames
        assert mock_sink.write_frame.call_count == 5
