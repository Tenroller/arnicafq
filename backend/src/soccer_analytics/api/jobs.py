from __future__ import annotations

import traceback
import uuid
from dataclasses import dataclass, field

from dotenv import load_dotenv

from soccer_analytics.config import load_config
from soccer_analytics import pipeline


@dataclass
class Job:
    id: str
    status: str = "pending"  # pending | calibrating | processing | completed | failed
    phase: str | None = None
    current_frame: int = 0
    total_frames: int = 0
    progress_pct: float = 0.0
    input_filename: str = ""
    input_path: str = ""
    output_path: str = ""
    analytics: dict | None = None
    error: str | None = None


_jobs: dict[str, Job] = {}


def create_job(input_filename: str, input_path: str, output_path: str) -> Job:
    job_id = uuid.uuid4().hex[:12]
    job = Job(
        id=job_id,
        input_filename=input_filename,
        input_path=input_path,
        output_path=output_path,
    )
    _jobs[job_id] = job
    return job


def get_job(job_id: str) -> Job | None:
    return _jobs.get(job_id)


def run_pipeline_sync(job: Job) -> None:
    load_dotenv()

    def on_progress(phase: str, current: int, total: int) -> None:
        job.status = phase
        job.phase = phase
        job.current_frame = current
        job.total_frames = total
        job.progress_pct = round(current / total * 100, 1) if total > 0 else 0.0

    try:
        config = load_config()
        result = pipeline.run(
            input_path=job.input_path,
            output_path=job.output_path,
            config=config,
            progress_callback=on_progress,
        )
        job.analytics = result
        job.status = "completed"
        job.progress_pct = 100.0
    except Exception as exc:
        job.status = "failed"
        job.error = f"{exc}\n{traceback.format_exc()}"
