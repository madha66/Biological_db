"""
Generate a static Matplotlib chart of pathway ranking results.

This script provides a publication-quality PNG chart of the top-ranked pathways,
suitable for inclusion in reports, presentations, or academic papers.

The live web UI uses an interactive frontend chart library (Recharts) for
interactivity (hover, click, zoom). This Matplotlib script is retained for
offline/static/report-style output where interactivity is not needed and
print-quality rendering is preferred.

Usage:
    python scripts/generate_static_chart.py --input results.json --output chart.png
    python scripts/generate_static_chart.py --demo

The --demo flag generates a chart from built-in example data.
"""

import argparse
import json
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import matplotlib
import numpy as np

matplotlib.use("Agg")  # Non-interactive backend for server/script use


def generate_chart(
    pathways: list[dict],
    output_path: str = "pathway_ranking.png",
    top_n: int = 15,
    title: str = "Top Ranked KEGG Pathways",
) -> None:
    """
    Generate a horizontal bar chart of top-ranked pathways.

    Args:
        pathways: List of pathway result dicts (from the API response).
        output_path: Path to save the PNG file.
        top_n: Maximum number of pathways to display.
        title: Chart title.
    """
    # Take top N pathways (already sorted by ranking score)
    display = pathways[:top_n]
    display.reverse()  # Reverse for horizontal bar chart (highest at top)

    names = [p.get("pathway_name", p.get("pathway_id", "?")) for p in display]
    scores = [p.get("ranking_score", 0) for p in display]
    adj_p = [p.get("adjusted_p_value", 1.0) for p in display]

    # Color by significance
    colors = []
    for p in adj_p:
        if p < 0.001:
            colors.append("#1a5276")  # Dark blue — highly significant
        elif p < 0.01:
            colors.append("#2e86c1")  # Medium blue
        elif p < 0.05:
            colors.append("#5dade2")  # Light blue — significant
        else:
            colors.append("#aed6f1")  # Very light — not significant

    fig, ax = plt.subplots(figsize=(12, max(6, len(display) * 0.45)))

    bars = ax.barh(range(len(names)), scores, color=colors, edgecolor="white", height=0.7)

    ax.set_yticks(range(len(names)))
    ax.set_yticklabels(names, fontsize=9)
    ax.set_xlabel("Ranking Score (Pathway Score × -log₁₀(Adjusted p-value))", fontsize=11)
    ax.set_title(title, fontsize=14, fontweight="bold", pad=15)

    # Add value labels
    for bar, score in zip(bars, scores):
        ax.text(
            bar.get_width() + max(scores) * 0.01,
            bar.get_y() + bar.get_height() / 2,
            f"{score:.3f}",
            va="center",
            fontsize=8,
            color="#333",
        )

    # Add legend for significance
    from matplotlib.patches import Patch
    legend_elements = [
        Patch(facecolor="#1a5276", label="p_adj < 0.001"),
        Patch(facecolor="#2e86c1", label="p_adj < 0.01"),
        Patch(facecolor="#5dade2", label="p_adj < 0.05"),
        Patch(facecolor="#aed6f1", label="p_adj ≥ 0.05"),
    ]
    ax.legend(handles=legend_elements, loc="lower right", fontsize=8, title="Significance")

    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.grid(axis="x", alpha=0.3)

    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"Chart saved to: {output_path}")


def demo_data() -> list[dict]:
    """
    Generate illustrative example data for demonstration.

    NOTE: This is NOT real KEGG data. It is a fabricated example for
    demonstrating the chart generation script's output format.
    """
    return [
        {"pathway_name": "PI3K-Akt signaling pathway", "ranking_score": 4.82, "adjusted_p_value": 0.0003},
        {"pathway_name": "p53 signaling pathway", "ranking_score": 4.15, "adjusted_p_value": 0.0008},
        {"pathway_name": "MAPK signaling pathway", "ranking_score": 3.41, "adjusted_p_value": 0.002},
        {"pathway_name": "Pathways in cancer", "ranking_score": 3.22, "adjusted_p_value": 0.004},
        {"pathway_name": "Cell cycle", "ranking_score": 2.89, "adjusted_p_value": 0.007},
        {"pathway_name": "Apoptosis", "ranking_score": 2.45, "adjusted_p_value": 0.012},
        {"pathway_name": "ErbB signaling pathway", "ranking_score": 2.10, "adjusted_p_value": 0.025},
        {"pathway_name": "mTOR signaling pathway", "ranking_score": 1.85, "adjusted_p_value": 0.038},
        {"pathway_name": "Focal adhesion", "ranking_score": 1.42, "adjusted_p_value": 0.065},
        {"pathway_name": "Wnt signaling pathway", "ranking_score": 0.95, "adjusted_p_value": 0.120},
    ]


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate a static Matplotlib chart of KEGG pathway rankings."
    )
    parser.add_argument("--input", "-i", help="Path to JSON file with pathway results.")
    parser.add_argument("--output", "-o", default="pathway_ranking.png", help="Output PNG path.")
    parser.add_argument("--top", "-n", type=int, default=15, help="Number of top pathways to show.")
    parser.add_argument("--demo", action="store_true", help="Use built-in demo data.")
    parser.add_argument("--title", "-t", default="Top Ranked KEGG Pathways", help="Chart title.")

    args = parser.parse_args()

    if args.demo:
        pathways = demo_data()
        print("Using illustrative demo data (not real KEGG results).")
    elif args.input:
        with open(args.input, "r") as f:
            data = json.load(f)
        pathways = data if isinstance(data, list) else data.get("pathways", [])
    else:
        parser.error("Provide --input <file> or --demo")
        return

    generate_chart(pathways, args.output, args.top, args.title)


if __name__ == "__main__":
    main()
