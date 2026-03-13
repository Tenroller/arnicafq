from __future__ import annotations

import argparse
import sys
from pathlib import Path

from soccer_analytics.config import load_config
from soccer_analytics.pipeline import run


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="soccer-analytics",
        description="Analyze soccer game video with player detection, tracking, and team classification.",
    )
    parser.add_argument(
        "input",
        help="Path to input soccer video file",
    )
    parser.add_argument(
        "-o", "--output",
        default=None,
        help="Path for output annotated video (default: <input>_analyzed.mp4)",
    )
    parser.add_argument(
        "-c", "--config",
        default=None,
        help="Path to YAML config file (default: config/default.yaml)",
    )
    parser.add_argument(
        "--confidence",
        type=float,
        default=None,
        help="Detection confidence threshold (overrides config)",
    )
    parser.add_argument(
        "--no-heatmap",
        action="store_true",
        help="Disable heatmap overlay",
    )
    parser.add_argument(
        "--no-traces",
        action="store_true",
        help="Disable movement traces",
    )

    args = parser.parse_args()

    input_path = Path(args.input)
    if not input_path.exists():
        print(f"Error: Input file not found: {input_path}", file=sys.stderr)
        sys.exit(1)

    if args.output is None:
        output_path = input_path.with_stem(input_path.stem + "_analyzed").with_suffix(".mp4")
    else:
        output_path = Path(args.output)

    config = load_config(args.config)

    # Apply CLI overrides
    if args.confidence is not None:
        config.detection.confidence = args.confidence
    if args.no_heatmap:
        config.annotation.show_heatmap = False
    if args.no_traces:
        config.annotation.show_traces = False

    run(str(input_path), str(output_path), config)


if __name__ == "__main__":
    main()
