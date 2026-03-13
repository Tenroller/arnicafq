# Soccer Analytics

Automated soccer video analysis — detects players and the ball, tracks them across frames, classifies teams by jersey color, computes game statistics, and produces an annotated output video. Available as a **CLI tool** and a **Web UI** powered by FastAPI + React.

## Features

- **Player & Ball Detection** — Roboflow inference model for real-time object detection
- **Multi-Object Tracking** — ByteTrack for persistent identity across frames
- **Team Classification** — KMeans clustering on jersey colors with auto-calibration
- **Game Analytics** — Ball possession, per-player stats (distance, speed, sprints), event detection (passes, shots, goals)
- **Annotated Output** — Bounding boxes, team colors, movement traces, heatmap, possession bar overlay
- **JSON Export** — Full analytics data saved alongside the output video
- **Web UI** — Upload videos, start analysis jobs, and view results in the browser

## Repo Structure

```
├── backend/
│   ├── config/
│   │   └── default.yaml              # Default configuration
│   ├── src/soccer_analytics/
│   │   ├── api/                       # FastAPI REST API
│   │   │   ├── app.py                 # Application factory
│   │   │   ├── routes.py              # API endpoints
│   │   │   ├── schemas.py             # Pydantic models
│   │   │   └── jobs.py                # Background job runner
│   │   ├── analytics.py               # Game analytics
│   │   ├── annotation.py              # Video annotation
│   │   ├── cli.py                     # CLI interface
│   │   ├── config.py                  # Configuration loader
│   │   ├── detection.py               # Object detection
│   │   ├── pipeline.py                # Two-phase processing pipeline
│   │   ├── team_classifier.py         # Jersey color classification
│   │   └── tracking.py                # ByteTrack tracker
│   ├── tests/                         # pytest test suite
│   ├── main.py                        # CLI entry point
│   └── pyproject.toml                 # Python project metadata
├── frontend/
│   ├── src/                           # React + Tailwind app
│   ├── package.json
│   └── vite.config.js
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

# Basic usage
source .env && python main.py input.mp4

# Specify output path
source .env && python main.py input.mp4 -o output.mp4

# Custom config file
source .env && python main.py input.mp4 -c config/custom.yaml

# Override detection confidence
source .env && python main.py input.mp4 --confidence 0.5

# Disable overlays
source .env && python main.py input.mp4 --no-heatmap --no-traces
```

### CLI Output

| Output | Description |
|--------|-------------|
| `output.mp4` | Annotated video with bounding boxes, team colors, traces, heatmap, and possession bar |
| `output.json` | Possession %, player stats, and detected events |
| Console report | Summary printed to terminal |

## Web UI Usage

Start both the API and frontend dev server in separate terminals:

```bash
# Terminal 1 — API
cd backend
source .env && uv run uvicorn soccer_analytics.api.app:app --reload --port 8000

# Terminal 2 — Frontend
cd frontend
npm run dev
```

Then open the URL printed by Vite (typically `http://localhost:5173`).

## Configuration

All settings live in `backend/config/default.yaml`:

```yaml
detection:
  model_id: "football-players-detection-3zvbc/2"
  confidence: 0.3

tracking:
  track_activation_threshold: 0.25
  lost_track_buffer: 30
  minimum_matching_threshold: 0.8
  frame_rate: 30

team_classification:
  calibration_frames: 50
  n_clusters: 2
  jersey_crop_ratio: 0.4

annotation:
  team_colors:
    - [0, 0, 255]    # red (BGR)
    - [255, 0, 0]    # blue (BGR)
  ball_color: [0, 255, 255]
  trace_length: 60
  thickness: 2
  show_traces: true
  show_heatmap: true

analytics:
  enabled: true
  possession_distance_threshold: 150.0
  sprint_speed_threshold: 15.0
  pass_max_distance: 200.0
  pass_min_frames: 5
  shot_velocity_threshold: 30.0
  goal_edge_margin: 0.05
  save_json: true
  overlay_stats: true
```

## Tests

```bash
cd backend
uv run pytest tests/ -v
```

## License

MIT
