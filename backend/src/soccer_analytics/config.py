from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

import yaml


@dataclass
class DetectionConfig:
    model_id: str = "football-players-detection-3zvbc/2"
    confidence: float = 0.3


@dataclass
class TrackingConfig:
    track_activation_threshold: float = 0.25
    lost_track_buffer: int = 30
    minimum_matching_threshold: float = 0.8
    frame_rate: int = 30


@dataclass
class TeamClassificationConfig:
    calibration_frames: int = 50
    n_clusters: int = 2
    jersey_crop_ratio: float = 0.4


@dataclass
class AnnotationConfig:
    team_colors: list[list[int]] = field(
        default_factory=lambda: [[0, 0, 255], [255, 0, 0]]
    )
    ball_color: list[int] = field(default_factory=lambda: [0, 255, 255])
    trace_length: int = 60
    thickness: int = 2
    show_traces: bool = True
    show_heatmap: bool = True


@dataclass
class AnalyticsConfig:
    enabled: bool = True
    possession_distance_threshold: float = 150.0
    sprint_speed_threshold: float = 15.0
    pass_max_distance: float = 200.0
    pass_min_frames: int = 5
    shot_velocity_threshold: float = 30.0
    goal_edge_margin: float = 0.05
    save_json: bool = True
    overlay_stats: bool = True


@dataclass
class Config:
    detection: DetectionConfig = field(default_factory=DetectionConfig)
    tracking: TrackingConfig = field(default_factory=TrackingConfig)
    team_classification: TeamClassificationConfig = field(
        default_factory=TeamClassificationConfig
    )
    annotation: AnnotationConfig = field(default_factory=AnnotationConfig)
    analytics: AnalyticsConfig = field(default_factory=AnalyticsConfig)


def load_config(path: str | Path | None = None) -> Config:
    """Load configuration from a YAML file, falling back to defaults."""
    if path is None:
        path = Path(__file__).resolve().parent.parent.parent / "config" / "default.yaml"
    else:
        path = Path(path)

    if not path.exists():
        return Config()

    with open(path) as f:
        raw = yaml.safe_load(f) or {}

    return Config(
        detection=DetectionConfig(**raw.get("detection", {})),
        tracking=TrackingConfig(**raw.get("tracking", {})),
        team_classification=TeamClassificationConfig(
            **raw.get("team_classification", {})
        ),
        annotation=AnnotationConfig(**raw.get("annotation", {})),
        analytics=AnalyticsConfig(**raw.get("analytics", {})),
    )
