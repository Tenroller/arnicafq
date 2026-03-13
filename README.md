# Soccer Analytics

Automated soccer video analysis pipeline — detects players and the ball, tracks them across frames, classifies teams by jersey color, computes game statistics, and produces an annotated output video with overlays.

## Features

- **Player & Ball Detection** — Roboflow inference model for real-time object detection
- **Multi-Object Tracking** — ByteTrack for persistent identity across frames
- **Team Classification** — KMeans clustering on jersey colors with auto-calibration
- **Game Analytics** — Ball possession, per-player stats (distance, speed, sprints), event detection (passes, shots, goals)
- **Annotated Output** — Bounding boxes, team colors, movement traces, heatmap, possession bar overlay
- **JSON Export** — Full analytics data saved alongside the output video

## Requirements

- Python 3.10+
- [Roboflow API key](https://roboflow.com/settings/api-key)

## Setup

```bash
# Clone the repo
git clone https://github.com/Tenroller/arnicafq.git
cd arnicafq

# Install dependencies (using uv)
uv sync

# Or with pip
pip install -e .

# Set your Roboflow API key
echo "ROBOFLOW_API_KEY=your_key_here" > .env
```

## Usage

```bash
# Basic usage
python main.py input.mp4

# Specify output path
python main.py input.mp4 -o output.mp4

# Custom config file
python main.py input.mp4 -c config/custom.yaml

# Override detection confidence
python main.py input.mp4 --confidence 0.5

# Disable overlays
python main.py input.mp4 --no-heatmap --no-traces
```

Load the `.env` file before running if your shell doesn't auto-load it:

```bash
source .env && python main.py input.mp4 -o output.mp4
```

### Output

The pipeline produces:

| Output | Description |
|--------|-------------|
| `output.mp4` | Annotated video with bounding boxes, team colors, traces, heatmap, and possession bar |
| `output.json` | JSON file with possession %, player stats, and detected events |
| Console report | Summary printed to terminal after processing |

## Configuration

All settings live in `config/default.yaml`:

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

## Project Structure

```
├── config/
│   └── default.yaml          # Default configuration
├── src/soccer_analytics/
│   ├── analytics.py           # Game analytics (possession, stats, events)
│   ├── annotation.py          # Video annotation with overlays
│   ├── cli.py                 # Command-line interface
│   ├── config.py              # Configuration dataclasses + YAML loader
│   ├── detection.py           # Roboflow object detection
│   ├── pipeline.py            # Two-phase processing pipeline
│   ├── team_classifier.py     # KMeans jersey color classification
│   └── tracking.py            # ByteTrack multi-object tracking
├── tests/
│   ├── test_analytics.py      # Analytics module tests
│   ├── test_detection.py      # Detection tests
│   ├── test_pipeline.py       # Pipeline integration test
│   ├── test_team_classifier.py# Team classifier tests
│   └── test_tracking.py       # Tracker tests
├── main.py                    # Entry point
└── pyproject.toml             # Project metadata and dependencies
```

## Pipeline

The pipeline runs in two phases:

1. **Calibration** — Runs detection on the first N frames to collect jersey color samples, then fits a KMeans model to distinguish teams.
2. **Full Processing** — For each frame: detect players/ball, track, classify teams, compute analytics, annotate, and write to output video. After all frames, prints a report and saves analytics to JSON.

## Tests

```bash
uv run pytest tests/ -v
```

## License

MIT
