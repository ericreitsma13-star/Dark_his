import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from matplotlib.ticker import FuncFormatter
from pathlib import Path


def _format_value(val: float, _) -> str:
    if val >= 1_000_000:
        return f"{val/1_000_000:.1f}M"
    if val >= 1_000:
        return f"{val/1_000:.0f}K"
    return str(int(val))


def render_chart(chart_data: dict, output_path: str, fps: int = 24, duration: float = 6.0):
    """
    Render an animated 3D-style bar chart to MP4.
    Bars grow from zero to their final value with a cinematic dark theme.
    """
    labels = [d["label"] for d in chart_data["data"]]
    values = [d["value"] for d in chart_data["data"]]
    colors = [d.get("color", "#c0392b") for d in chart_data["data"]]
    title = chart_data.get("title", "")
    subtitle = chart_data.get("subtitle", "")

    n = len(labels)
    x = np.arange(n)
    total_frames = int(fps * duration)
    grow_frames = int(total_frames * 0.6)   # 60% of time growing
    hold_frames = total_frames - grow_frames

    fig, ax = plt.subplots(figsize=(16, 9), dpi=120)
    fig.patch.set_facecolor("#0d0d0d")
    ax.set_facecolor("#0d0d0d")

    ax.tick_params(colors="white", labelsize=11)
    ax.spines["bottom"].set_color("#333333")
    ax.spines["left"].set_color("#333333")
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.yaxis.set_major_formatter(FuncFormatter(_format_value))
    ax.set_xticks(x)
    ax.set_xticklabels(labels, color="white", fontsize=10, rotation=15, ha="right")
    ax.set_ylim(0, max(values) * 1.2)
    ax.set_xlim(-0.6, n - 0.4)
    ax.set_title(title, color="white", fontsize=18, fontweight="bold", pad=20)
    if subtitle:
        ax.set_xlabel(subtitle, color="#aaaaaa", fontsize=12, labelpad=10)

    bars = ax.bar(x, [0] * n, color=colors, width=0.6, zorder=3, edgecolor="#222222", linewidth=0.5)

    # Subtle grid
    ax.yaxis.grid(True, color="#222222", linestyle="--", linewidth=0.5, zorder=0)

    value_texts = [
        ax.text(xi, 0, "", ha="center", va="bottom", color="white", fontsize=10, fontweight="bold")
        for xi in x
    ]

    def update(frame):
        if frame < grow_frames:
            progress = (frame / grow_frames) ** 0.6  # Ease-out
        else:
            progress = 1.0

        for bar, val, txt in zip(bars, values, value_texts):
            current = val * progress
            bar.set_height(current)
            if current > max(values) * 0.03:
                txt.set_position((bar.get_x() + bar.get_width() / 2, current))
                txt.set_text(_format_value(current, None))
            else:
                txt.set_text("")

        return bars.patches + value_texts

    ani = animation.FuncAnimation(
        fig,
        update,
        frames=total_frames,
        interval=1000 / fps,
        blit=True,
    )

    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    writer = animation.FFMpegWriter(fps=fps, bitrate=4000, extra_args=["-pix_fmt", "yuv420p"])
    ani.save(output_path, writer=writer)
    plt.close(fig)
    print(f"  Chart saved: {output_path}")
