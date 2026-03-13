from __future__ import annotations

from pydantic import BaseModel


class JobCreatedResponse(BaseModel):
    job_id: str
    status: str


class JobStatusResponse(BaseModel):
    job_id: str
    status: str
    phase: str | None = None
    current_frame: int = 0
    total_frames: int = 0
    progress_pct: float = 0.0
    error: str | None = None


class PossessionData(BaseModel):
    team_0: float = 0.0
    team_1: float = 0.0


class PlayerStatData(BaseModel):
    tracker_id: int
    team_id: int
    distance_px: float
    avg_speed_px_per_s: float
    max_speed_px_per_s: float
    sprints: int
    time_on_ball_sec: float


class EventData(BaseModel):
    frame_index: int
    timestamp: float
    event_type: str
    team_id: int
    player_id: int
    details: dict = {}


class AnalyticsResponse(BaseModel):
    possession: PossessionData
    player_stats: list[PlayerStatData]
    events: list[EventData]
