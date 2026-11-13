"""Threaded serial/native-process connection and CSV recording (Apache-2.0)."""
import csv
import json
import os
from pathlib import Path
import queue
import subprocess
import threading
import time
from .protocol import request, response, MAX_RESPONSE_BYTES

ROOT = Path(__file__).resolve().parents[2]
# Editable installs point at software/elbow_exo; explicit repository root also
# supports source checkouts when Python's module path was configured manually.
ROOT = ROOT.parent
FIELDS = ["time_ms", "state", "fault", "q", "dq", "current", "temperature", "voltage", "torque", "enabled"]


def find_root():
    for candidate in [Path.cwd(), *Path(__file__).resolve().parents]:
        if (candidate / "config/robot.json").is_file():
            return candidate
    raise FileNotFoundError("run in a repository checkout (config/robot.json is required)")


class ProcessTransport:
    simulated = True

    def __init__(self, executable=None):
        self.path = Path(executable) if executable else find_root() / "firmware/build" / ("host_sim.exe" if os.name == "nt" else "host_sim")
        if not self.path.is_file():
            raise FileNotFoundError(f"build native firmware first: {self.path}")
        self.process = subprocess.Popen([str(self.path.resolve())], stdin=subprocess.PIPE,
                                        stdout=subprocess.PIPE, stderr=subprocess.PIPE, bufsize=0)

    def write(self, data):
        if self.process.poll() is not None:
            raise ConnectionError("native firmware exited")
        self.process.stdin.write(data)
        self.process.stdin.flush()

    def readline(self):
        return self.process.stdout.readline(MAX_RESPONSE_BYTES + 1)

    def close(self):
        if self.process.poll() is None:
            self.process.terminate()
        try:
            self.process.wait(timeout=2)
        except subprocess.TimeoutExpired:
            self.process.kill()
            self.process.wait(timeout=2)
        for stream in (self.process.stdin, self.process.stdout, self.process.stderr):
            stream.close()


class SerialTransport:
    simulated = False

    def __init__(self, port):
        import serial
        self.serial = serial.Serial(port, 115200, timeout=0.1, write_timeout=0.3)

    def write(self, data):
        self.serial.write(data)
        self.serial.flush()

    def readline(self):
        return self.serial.read_until(b"\n", MAX_RESPONSE_BYTES + 1)

    def close(self):
        self.serial.close()


class Client:
    def __init__(self, transport, csv_path=None, heartbeat=True):
        self.transport = transport
        self.latest = {}
        self.samples = []
        self.events = []
        self.bad_frames = 0
        self.last_error = None
        self._seq = 0
        self._pending = {}
        self._lock = threading.Lock()
        self._halt = threading.Event()
        self._heartbeat_enabled = threading.Event()
        if heartbeat:
            self._heartbeat_enabled.set()
        self._file = None
        self._writer = None
        if csv_path:
            path = Path(csv_path)
            path.parent.mkdir(parents=True, exist_ok=True)
            self._file = path.open("w", newline="", encoding="utf-8")
            self._writer = csv.DictWriter(self._file, fieldnames=FIELDS, extrasaction="ignore")
            self._writer.writeheader()
        self._reader = threading.Thread(target=self._read, daemon=True)
        self._heart = threading.Thread(target=self._heartbeat, daemon=True)
        self._reader.start()
        self._heart.start()

    def _read(self):
        try:
            while not self._halt.is_set():
                line = self.transport.readline()
                if not line:
                    if self.transport.simulated:
                        raise ConnectionError("native firmware disconnected")
                    continue
                try:
                    msg = response(line)
                except (ValueError, UnicodeError):
                    self.bad_frames += 1
                    continue
                if msg["type"] == "ack":
                    with self._lock:
                        pending = self._pending.get(msg.get("seq"))
                    if pending:
                        pending.put(msg)
                elif msg["type"] == "status":
                    self.latest = msg
                    self.samples.append(msg.copy())
                    # Bound long unattended sessions; CSV remains complete.
                    if len(self.samples) > 10000:
                        del self.samples[:1000]
                    if self._writer:
                        self._writer.writerow(msg)
                        self._file.flush()
                else:
                    self.events.append(msg)
        except (OSError, ConnectionError) as exc:
            if not self._halt.is_set():
                self.last_error = str(exc)

    def command(self, op, value=0.0, timeout=1.0):
        pending = queue.Queue(maxsize=1)
        with self._lock:
            seq = self._seq
            self._seq = (seq + 1) & 0xFFFF
            self._pending[seq] = pending
            try:
                self.transport.write(request(seq, op, value))
            except Exception:
                self._pending.pop(seq, None)
                raise
        try:
            ack = pending.get(timeout=timeout)
            if not ack.get("ok"):
                raise RuntimeError(f"{op} rejected: {ack.get('error', ack)}")
            return ack
        except queue.Empty as exc:
            raise TimeoutError(f"no acknowledgement for {op}; {self.last_error or 'connection timed out'}") from exc
        finally:
            with self._lock:
                self._pending.pop(seq, None)

    def _heartbeat(self):
        while not self._halt.wait(0.05):
            if self._heartbeat_enabled.is_set():
                try:
                    self.command("HB", timeout=0.3)
                except (OSError, RuntimeError, TimeoutError, ConnectionError) as exc:
                    self.last_error = str(exc)

    def heartbeat(self, enabled):
        if enabled:
            self._heartbeat_enabled.set()
        else:
            self._heartbeat_enabled.clear()

    def inject(self, kind, value):
        if not self.transport.simulated:
            raise ValueError("fault injection is only available in native simulation")
        allowed = {"ESTOP", "TEMP", "CURRENT", "SENSOR", "RESET_BUTTON", "VOLTAGE", "Q", "DQ", "LIMIT_MIN", "LIMIT_MAX"}
        if kind not in allowed or not isinstance(value, (float, int)):
            raise ValueError("unknown simulation input")
        with self._lock:
            self.transport.write(f"!INJECT {kind} {value:.12g}\n".encode("ascii"))

    def wait_state(self, state, timeout=2.0):
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            if self.latest.get("state") == state:
                return self.latest.copy()
            if self.last_error and not self.latest:
                raise ConnectionError(self.last_error)
            time.sleep(0.01)
        raise TimeoutError(f"expected {state}; latest={self.latest}")

    def close(self):
        if self._halt.is_set():
            return
        self.heartbeat(False)
        try:
            self.command("STOP", timeout=0.4)
        except (OSError, RuntimeError, TimeoutError, ConnectionError):
            pass
        self._halt.set()
        self._heart.join(timeout=1)
        self.transport.close()
        self._reader.join(timeout=1)
        if self._file:
            self._file.close()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()


def plot_log(csv_path, output):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    with Path(csv_path).open(encoding="utf-8") as stream:
        rows = list(csv.DictReader(stream))
    if not rows:
        raise ValueError("no telemetry to plot")
    t = [float(r["time_ms"]) / 1000 for r in rows]
    fig, axes = plt.subplots(3, 1, figsize=(10, 7), sharex=True, constrained_layout=True)
    for key, ax, label in zip(("q", "dq", "torque"), axes, ("angle [rad]", "velocity [rad/s]", "command torque [Nm]")):
        ax.plot(t, [float(r[key]) for r in rows], color="#147d92", linewidth=1.8)
        ax.set_ylabel(label)
        ax.grid(alpha=0.25)
    axes[0].set_title("Shared C firmware + simulated plant | no hardware measurements")
    axes[-1].set_xlabel("controller time [s]")
    path = Path(output)
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=160)
    plt.close(fig)

