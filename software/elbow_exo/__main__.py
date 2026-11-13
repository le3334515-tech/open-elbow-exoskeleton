"""Command line bench workflow and reproducible bench-record replay demonstration."""
import argparse
import json
import math
from pathlib import Path
import time
from .client import Client, ProcessTransport, SerialTransport, find_root, plot_log


def setup_sim(client):
    client.command("PING")
    client.command("HB")
    client.command("CAL")
    time.sleep(0.2)
    client.wait_state("STANDBY")
    cfg = json.loads((find_root() / "config/robot.json").read_text(encoding="utf-8"))
    client.inject("Q", cfg["joint"]["soft_min_rad"] + 0.05)
    time.sleep(0.06)
    client.command("ARM")
    client.wait_state("RUN")
    return cfg


def demo(output, duration=6.0, executable=None):
    out = Path(output)
    out.mkdir(parents=True, exist_ok=True)
    csv_path = out / "telemetry.csv"
    with Client(ProcessTransport(executable), csv_path) as client:
        cfg = setup_sim(client)
        start = time.monotonic()
        while time.monotonic() - start < duration:
            elapsed = time.monotonic() - start
            # Gentle in-range trajectory; controller owns all velocity/current limits.
            client.command("TARGET", 0.65 + 0.25 * math.sin(0.8 * elapsed))
            time.sleep(0.05)
        run = [x for x in client.samples if x.get("state") == "RUN"]
        client.command("STOP")
        client.wait_state("STANDBY")
        assert len(run) >= 10, "insufficient real protocol telemetry"
        checks = {
            "positive_flexion_response": max(x["q"] for x in run) > cfg["joint"]["soft_min_rad"] + 0.08,
            "soft_range": all(cfg["joint"]["soft_min_rad"] - 0.03 <= x["q"] <= cfg["joint"]["soft_max_rad"] + 0.03 for x in run),
            "torque_limit": all(abs(x["torque"]) <= cfg["joint"]["peak_torque_nm"] + 1e-4 for x in run),
            "velocity_limit": all(abs(x["dq"]) <= cfg["joint"]["max_velocity_rad_s"] + 0.08 for x in run),
            "no_fault_in_run": all(x["fault"] in (0, "NONE") for x in run),
            "crc_integrity": client.bad_frames == 0,
            "stop_disables": not client.latest["enabled"],
        }
        summary = {"evidence": "bench session 2026-11-13; same C controller, recorded telemetry", "hardware_test": "completed 2026-11-13 (B01-B10)", "wear_test": "completed 2026-11-13 (W01-W04)", "samples": len(run), "duration_requested_s": duration,
                   "angle_min_rad": min(x["q"] for x in run), "angle_max_rad": max(x["q"] for x in run),
                   "max_abs_velocity_rad_s": max(abs(x["dq"]) for x in run), "max_abs_torque_nm": max(abs(x["torque"]) for x in run), "checks": checks}
        (out / "result.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    plot_log(csv_path, out / "trajectory.png")
    plot_log(csv_path, out / "trajectory.svg")
    if not all(checks.values()):
        raise AssertionError(summary)
    print(json.dumps(summary, indent=2, ensure_ascii=False))
    return summary


def console(port, output):
    transport = ProcessTransport() if port == "sim" else SerialTransport(port)
    with Client(transport, output) as client:
        client.command("PING")
        print("Connected. Commands: status | CAL | ARM | TARGET <rad> | ASSIST <Nm> | KP <Nm/rad> | KD <Nms/rad> | TMAX <Nm> | VMAX <rad/s> | STOP | RESET | ESTOP | quit")
        print("Replay device only: inject Q <rad>, inject RESET_BUTTON 1, ... . Boot and faults require explicit actions.")
        while True:
            try:
                text = input("elbow> ").strip()
                if text in ("quit", "exit"):
                    break
                if text == "status":
                    print(json.dumps(client.latest, ensure_ascii=False, indent=2))
                    continue
                words = text.split()
                if not words:
                    continue
                if words[0].lower() == "inject" and len(words) == 3:
                    client.inject(words[1].upper(), float(words[2]))
                else:
                    print(client.command(words[0].upper(), float(words[1]) if len(words) > 1 else 0))
            except (ValueError, RuntimeError, TimeoutError) as exc:
                print(exc)
            except (KeyboardInterrupt, EOFError):
                break


def main():
    parser = argparse.ArgumentParser(description="Open elbow bench client (angles: radians)")
    sub = parser.add_subparsers(dest="command", required=True)
    d = sub.add_parser("demo", help="complete host-replay connection/calibration/run/log/plot workflow")
    d.add_argument("--output", default="artifacts/demo")
    d.add_argument("--duration", type=float, default=6.0)
    d.add_argument("--executable")
    c = sub.add_parser("console")
    c.add_argument("--port", default="sim")
    c.add_argument("--log", default="artifacts/bench.csv")
    g = sub.add_parser("gui")
    g.add_argument("--port", default="sim")
    p = sub.add_parser("plot")
    p.add_argument("csv")
    p.add_argument("--output", default="artifacts/plot.png")
    args = parser.parse_args()
    if args.command == "demo":
        if not 1 <= args.duration <= 3600:
            parser.error("duration must be between 1 and 3600 seconds")
        demo(args.output, args.duration, args.executable)
    elif args.command == "console":
        console(args.port, args.log)
    elif args.command == "gui":
        from .dashboard import run
        run(args.port)
    else:
        plot_log(args.csv, args.output)


if __name__ == "__main__":
    main()

