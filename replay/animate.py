"""Render a genuine telemetry replay, with no external renderer dependency."""
import argparse
import csv
import math
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation, PillowWriter


def animate(csv_path, output):
    with Path(csv_path).open(encoding="utf-8") as f:
        rows = list(csv.DictReader(f))[::3]
    fig, ax = plt.subplots(figsize=(7, 4), constrained_layout=True)
    ax.set_aspect("equal")
    ax.set(xlim=(-.33, .33), ylim=(-.06, .32), xlabel="x [m]", ylabel="y [m]")
    ax.set_title("Open Elbow | C firmware + bench records")
    ax.plot([-.26, 0], [0, 0], linewidth=12, color="#34445a", solid_capstyle="round")
    fore, = ax.plot([], [], linewidth=10, color="#108b9b", solid_capstyle="round")
    ax.scatter([0], [0], s=250, color="#ef9a35", zorder=4)
    label = ax.text(-.31, .28, "")
    ax.text(-.31, -.045, "Telemetry replay of the 2026-11-13 bench records", fontsize=9)
    ax.grid(alpha=.2)
    def frame(i):
        r = rows[i]
        q = float(r["q"])
        fore.set_data([0, .24 * math.cos(q)], [0, .24 * math.sin(q)])
        label.set_text(f"t={float(r['time_ms']) / 1000:.2f} s   q={math.degrees(q):.1f} deg\n{r['state']}   torque={float(r['torque']):.3f} Nm")
        return fore, label
    ani = FuncAnimation(fig, frame, frames=len(rows), interval=150, blit=True)
    Path(output).parent.mkdir(parents=True, exist_ok=True)
    ani.save(output, writer=PillowWriter(fps=7))
    plt.close(fig)


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("csv")
    p.add_argument("--output", default="artifacts/elbow.gif")
    args = p.parse_args()
    animate(args.csv, args.output)

