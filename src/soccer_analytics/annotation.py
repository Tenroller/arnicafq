from __future__ import annotations

import cv2
import numpy as np
import supervision as sv

from soccer_analytics.config import AnnotationConfig


class VideoAnnotator:
    """Composes Supervision annotators for soccer video output."""

    def __init__(self, config: AnnotationConfig | None = None) -> None:
        config = config or AnnotationConfig()

        self._team_colors = [
            sv.Color(r=c[2], g=c[1], b=c[0]) for c in config.team_colors
        ]
        self._ball_color = sv.Color(
            r=config.ball_color[2],
            g=config.ball_color[1],
            b=config.ball_color[0],
        )

        self._box_annotator = sv.BoxAnnotator(thickness=config.thickness)
        self._label_annotator = sv.LabelAnnotator(
            text_thickness=max(1, config.thickness - 1),
            text_scale=0.5,
        )
        self._trace_annotator = sv.TraceAnnotator(
            position=sv.Position.CENTER,
            trace_length=config.trace_length,
            thickness=config.thickness,
        )
        self._ball_marker = sv.TriangleAnnotator(
            base=20,
            height=16,
        )
        self._show_traces = config.show_traces
        self._show_heatmap = config.show_heatmap

        if self._show_heatmap:
            self._heatmap_annotator = sv.HeatMapAnnotator()

    def annotate(
        self,
        frame: np.ndarray,
        player_detections: sv.Detections,
        ball_detections: sv.Detections,
        team_ids: np.ndarray | None = None,
        possession: dict[str, float] | None = None,
    ) -> np.ndarray:
        """Annotate a frame with detections, labels, traces, and optional heatmap."""
        annotated = frame.copy()

        # Build per-detection color list for players
        if team_ids is not None and len(team_ids) > 0 and len(player_detections) > 0:
            colors = [self._team_colors[tid % len(self._team_colors)] for tid in team_ids]
            color_lookup = sv.ColorLookup.INDEX
            palette = sv.ColorPalette(colors=colors)

            box_ann = sv.BoxAnnotator(
                thickness=self._box_annotator.thickness,
                color=palette,
                color_lookup=color_lookup,
            )
            label_ann = sv.LabelAnnotator(
                text_scale=0.5,
                color=palette,
                color_lookup=color_lookup,
            )
        else:
            box_ann = self._box_annotator
            label_ann = self._label_annotator

        # Annotate players
        if len(player_detections) > 0:
            annotated = box_ann.annotate(annotated, player_detections)

            labels = []
            tracker_ids = player_detections.tracker_id
            for i in range(len(player_detections)):
                tid = tracker_ids[i] if tracker_ids is not None else "?"
                team = team_ids[i] if team_ids is not None and i < len(team_ids) else "?"
                labels.append(f"#{tid} T{team}")

            annotated = label_ann.annotate(
                annotated, player_detections, labels=labels
            )

            if self._show_traces:
                annotated = self._trace_annotator.annotate(
                    annotated, player_detections
                )

        # Annotate ball
        if len(ball_detections) > 0:
            annotated = self._ball_marker.annotate(annotated, ball_detections)

        # Heatmap (players only)
        if self._show_heatmap and len(player_detections) > 0:
            annotated = self._heatmap_annotator.annotate(
                annotated, player_detections
            )

        # Possession bar overlay
        if possession is not None:
            annotated = self._draw_possession_bar(annotated, possession)

        return annotated

    def _draw_possession_bar(
        self,
        frame: np.ndarray,
        possession: dict[str, float],
    ) -> np.ndarray:
        h, w = frame.shape[:2]
        bar_height = 30
        bar_y = 10
        bar_x = 50
        bar_width = w - 100

        team_0_pct = possession.get("team_0", 0.0)
        split = int(bar_width * team_0_pct / 100) if team_0_pct > 0 else 0

        # Team 0 (left), Team 1 (right) — use BGR colors from config
        c0 = self._team_colors[0]
        c1 = self._team_colors[1] if len(self._team_colors) > 1 else self._team_colors[0]
        bgr0 = (c0.b, c0.g, c0.r)
        bgr1 = (c1.b, c1.g, c1.r)

        cv2.rectangle(
            frame,
            (bar_x, bar_y),
            (bar_x + split, bar_y + bar_height),
            bgr0,
            -1,
        )
        cv2.rectangle(
            frame,
            (bar_x + split, bar_y),
            (bar_x + bar_width, bar_y + bar_height),
            bgr1,
            -1,
        )
        cv2.rectangle(
            frame,
            (bar_x, bar_y),
            (bar_x + bar_width, bar_y + bar_height),
            (255, 255, 255),
            1,
        )

        team_1_pct = possession.get("team_1", 0.0)
        cv2.putText(
            frame,
            f"{team_0_pct:.0f}%",
            (bar_x + 5, bar_y + bar_height - 8),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.5,
            (255, 255, 255),
            1,
            cv2.LINE_AA,
        )
        cv2.putText(
            frame,
            f"{team_1_pct:.0f}%",
            (bar_x + bar_width - 45, bar_y + bar_height - 8),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.5,
            (255, 255, 255),
            1,
            cv2.LINE_AA,
        )

        return frame
