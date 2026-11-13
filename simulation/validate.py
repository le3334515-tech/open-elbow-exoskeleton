"""Reproducible software-in-loop trajectory and injected-fault evidence."""
import argparse
import csv
import json
from pathlib import Path
import time
from elbow_exo.client import Client, ProcessTransport, find_root
from elbow_exo.__main__ import demo, setup_sim


def run(output):
    out = Path(output)
    out.mkdir(parents=True, exist_ok=True)
    trajectory = demo(out / "trajectory", 6)
    results = []
    cases = [("ESTOP", 1, "ESTOP", "ESTOP"), ("TEMP", 65, "FAULT", "TEMPERATURE"),
             ("CURRENT", 1.4, "FAULT", "CURRENT"), ("SENSOR", 0, "FAULT", "SENSOR"),
             ("LIMIT_MIN", 1, "FAULT", "LIMIT"), ("VOLTAGE", 30, "FAULT", "VOLTAGE"),
             ("HEARTBEAT", 0, "FAULT", "HEARTBEAT")]
    for kind, value, state, fault in cases:
        with Client(ProcessTransport(), out / (kind.lower() + ".csv")) as c:
            setup_sim(c)
            c.command("TARGET", .5)
            time.sleep(.1)
            start = time.monotonic()
            if kind == "HEARTBEAT":
                c.heartbeat(False)
            else:
                c.inject(kind, value)
            s = c.wait_state(state)
            latency = time.monotonic() - start
            check = s["fault"] == fault and not s["enabled"] and s["torque"] == 0
            results.append({"case": kind, "expected_fault": fault, "observed": s, "observed_host_latency_s": round(latency, 4), "pass": check})
    summary = {"date": "2026-11-13", "scope": "software-in-loop using actual compiled firmware/control.c; synthetic sensors and plant; host latency includes 50ms telemetry period and OS scheduling", "trajectory": trajectory, "fault_scenarios": results, "all_pass": all(r["pass"] for r in results), "bench_tests": "未执行", "wear_tests": "未执行"}
    (out / "summary.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    if not summary["all_pass"]:
        raise AssertionError(summary)
    return summary


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--output", default="artifacts/simulation")
    args = p.parse_args()
    print(json.dumps(run(args.output), indent=2, ensure_ascii=False))

