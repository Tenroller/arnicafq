# Soccer Analytics

Automated soccer video analysis — detects players and the ball, tracks them across frames, classifies teams by jersey color, computes game statistics, and produces an annotated output video. Available as a **CLI tool** and a **Web UI** powered by FastAPI + React.

## Features

- **Player & Ball Detection** — Roboflow inference model for real-time object detection
- **Multi-Object Tracking** — ByteTrack for persistent identity across frames
- **Team Classification** — KMeans clustering on jersey colors with auto-calibration
- **Game Analytics** — Ball possession, per-player stats (distance, speed, sprints), event detection (passes, shots, goals)
- **Annotated Output** — Bounding boxes, team colors, movement traces, heatmap, possession bar overlay
- **JSON Export** — Full analytics data saved alongside the output video
- **Web UI** — Upload videos, monitor progress in real time, and explore results in a dashboard

## Repo Structure

```
├── backend/
│   ├── config/
│   │   └── default.yaml              # Default pipeline configuration
│   ├── src/soccer_analytics/
│   │   ├── api/                       # FastAPI REST API
│   │   │   ├── app.py                 # App factory + CORS setup
│   │   │   ├── routes.py             # /api endpoints
│   │   │   ├── schemas.py            # Pydantic request/response models
│   │   │   └── jobs.py               # Background job runner
│   │   ├── analytics.py               # Possession, player stats, events
│   │   ├── annotation.py              # Video frame annotation + overlays
│   │   ├── cli.py                     # CLI interface (Click)
│   │   ├── config.py                  # Config dataclasses + YAML loader
│   │   ├── detection.py               # Roboflow object detection
│   │   ├── pipeline.py                # Two-phase processing pipeline
│   │   ├── team_classifier.py         # KMeans jersey color classification
│   │   └── tracking.py                # ByteTrack multi-object tracker
│   ├── tests/                         # pytest suite (30 tests)
│   ├── main.py                        # CLI entry point
│   └── pyproject.toml                 # Python project metadata + deps
├── frontend/
│   ├── src/
│   │   ├── App.jsx                    # 3-stage state machine (idle → processing → done)
│   │   ├── api.js                     # API client helpers
│   │   └── components/
│   │       ├── UploadForm.jsx         # Drag-and-drop video upload
│   │       ├── JobProgress.jsx        # Real-time progress bar (polls every 2s)
│   │       ├── ResultsDashboard.jsx   # Multi-panel results view
│   │       ├── VideoPlayer.jsx        # HTML5 annotated video player
│   │       ├── PossessionChart.jsx    # Horizontal possession bar chart
│   │       ├── PlayerStatsTable.jsx   # Sortable stats table
│   │       └── EventsTimeline.jsx     # Color-coded event list
│   ├── package.json
│   └── vite.config.js                 # Vite config with /api proxy to :8000
└── README.md
```

## Requirements

- Python 3.10+
- Node.js 18+ (for the frontend)
- [Roboflow API key](https://roboflow.com/settings/api-key)

## Setup

### Backend

```bash
cd backend

# Install dependencies (using uv)
uv sync

# Or with pip
pip install -e .

# Set your Roboflow API key
echo "ROBOFLOW_API_KEY=your_key_here" > .env
```

### Frontend

```bash
cd frontend
npm install
```

## CLI Usage

Run from the `backend/` directory:

```bash
cd backend
source .env && python main.py input.mp4
```

### CLI Options

| Flag | Type | Default | Description |
|------|------|---------|-------------|
| `input` | positional | — | Path to input soccer video (required) |
| `-o, --output` | string | `<input>_analyzed.mp4` | Output video path |
| `-c, --config` | string | `config/default.yaml` | YAML config file |
| `--confidence` | float | from config (0.3) | Detection confidence threshold |
| `--no-heatmap` | flag | — | Disable heatmap overlay |
| `--no-traces` | flag | — | Disable movement traces |

### CLI Output

| File | Description |
|------|-------------|
| `output.mp4` | Annotated video with bounding boxes, team colors, traces, heatmap, possession bar |
| `output.json` | Possession %, player stats, and detected events |
| Console report | Summary printed to terminal |

## Web UI

Start the API and frontend dev server in two terminals:

```bash
# Terminal 1 — API
cd backend
source .env && uv run uvicorn soccer_analytics.api.app:app --reload --port 8000

# Terminal 2 — Frontend
cd frontend
npm run dev
```

Open `http://localhost:5173`. The Vite dev server proxies `/api` requests to the backend.

### Workflow

1. **Upload** — Drag-and-drop or browse to select a video
2. **Processing** — Real-time progress bar shows calibration and processing phases
3. **Results** — Dashboard with annotated video player, possession chart, sortable player stats table, and color-coded events timeline

### API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/api/upload` | Upload a video file, returns `{ job_id, status }` |
| `GET` | `/api/jobs/{job_id}/status` | Job status with phase, frame progress, and error info |
| `GET` | `/api/jobs/{job_id}/analytics` | Possession, player stats, and events after completion |
| `GET` | `/api/jobs/{job_id}/video` | Download the annotated output video |

## Pipeline

The pipeline runs in two phases:

1. **Calibration** — Detects players across the first N frames (default 50) and fits a KMeans model on jersey colors to distinguish teams.
2. **Full Processing** — For each frame: detect players/ball, track with ByteTrack, classify teams, compute analytics, annotate, and write to output. Saves a JSON report and prints a summary when done.

## Configuration

All settings live in `backend/config/default.yaml`:

| Section | Key Settings |
|---------|-------------|
| `detection` | `model_id`, `confidence` (0.3) |
| `tracking` | `track_activation_threshold` (0.25), `lost_track_buffer` (30), `frame_rate` (30) |
| `team_classification` | `calibration_frames` (50), `n_clusters` (2), `jersey_crop_ratio` (0.4) |
| `annotation` | `team_colors`, `ball_color`, `trace_length` (60), `show_traces`, `show_heatmap` |
| `analytics` | `possession_distance_threshold` (150px), `sprint_speed_threshold` (15px/s), pass/shot/goal thresholds, `save_json`, `overlay_stats` |

## Tests

```bash
cd backend
uv run pytest tests/ -v
```

30 tests covering detection, tracking, team classification, analytics, and pipeline integration.

## License

MIT
