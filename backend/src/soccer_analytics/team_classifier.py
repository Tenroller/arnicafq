from __future__ import annotations

import cv2
import numpy as np
from sklearn.cluster import KMeans

import supervision as sv
from soccer_analytics.config import TeamClassificationConfig


class TeamClassifier:
    """Classify players into teams by jersey color using KMeans clustering."""

    def __init__(self, config: TeamClassificationConfig | None = None) -> None:
        config = config or TeamClassificationConfig()
        self._n_clusters = config.n_clusters
        self._jersey_crop_ratio = config.jersey_crop_ratio
        self._team_kmeans: KMeans | None = None
        self._jersey_colors: list[np.ndarray] = []

    @property
    def is_fitted(self) -> bool:
        return self._team_kmeans is not None

    def _extract_jersey_color(
        self, frame: np.ndarray, bbox: np.ndarray
    ) -> np.ndarray | None:
        """Extract dominant jersey color from the top portion of a bounding box.

        Args:
            frame: BGR image.
            bbox: [x1, y1, x2, y2] bounding box.

        Returns:
            Dominant color as a 3-element array (HSV), or None if extraction fails.
        """
        x1, y1, x2, y2 = map(int, bbox)
        h = y2 - y1
        w = x2 - x1
        if h <= 0 or w <= 0:
            return None

        # Crop top portion (jersey region)
        jersey_y2 = y1 + int(h * self._jersey_crop_ratio)
        crop = frame[y1:jersey_y2, x1:x2]
        if crop.size == 0:
            return None

        hsv = cv2.cvtColor(crop, cv2.COLOR_BGR2HSV)
        pixels = hsv.reshape(-1, 3).astype(np.float32)

        if len(pixels) < 4:
            return None

        # KMeans on pixels to find 2 dominant colors, pick the one
        # that is less likely to be skin (higher saturation or non-skin hue)
        km = KMeans(n_clusters=2, n_init=1, max_iter=10, random_state=0)
        km.fit(pixels)
        centers = km.cluster_centers_
        counts = np.bincount(km.labels_, minlength=2)

        # Pick the cluster with more pixels as the dominant jersey color
        dominant_idx = np.argmax(counts)
        return centers[dominant_idx]

    def accumulate(
        self, frame: np.ndarray, detections: sv.Detections
    ) -> None:
        """Collect jersey colors from a frame for later fitting."""
        if len(detections) == 0:
            return

        for bbox in detections.xyxy:
            color = self._extract_jersey_color(frame, bbox)
            if color is not None:
                self._jersey_colors.append(color)

    def fit(self) -> None:
        """Fit the team classifier on accumulated jersey colors."""
        if len(self._jersey_colors) < self._n_clusters:
            raise ValueError(
                f"Need at least {self._n_clusters} jersey color samples, "
                f"got {len(self._jersey_colors)}"
            )

        data = np.array(self._jersey_colors)
        self._team_kmeans = KMeans(
            n_clusters=self._n_clusters, n_init=10, random_state=42
        )
        self._team_kmeans.fit(data)

    def predict(
        self, frame: np.ndarray, detections: sv.Detections
    ) -> np.ndarray:
        """Predict team IDs for each detection.

        Returns:
            Array of team IDs (0 or 1) for each detection.
        """
        if self._team_kmeans is None:
            raise RuntimeError("TeamClassifier must be fit() before predict()")

        if len(detections) == 0:
            return np.array([], dtype=int)

        colors = []
        for bbox in detections.xyxy:
            color = self._extract_jersey_color(frame, bbox)
            if color is not None:
                colors.append(color)
            else:
                colors.append(np.zeros(3))

        return self._team_kmeans.predict(np.array(colors))
