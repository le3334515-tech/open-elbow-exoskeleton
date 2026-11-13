"""Exercise real subprocess byte streams, acknowledgements and physical reset interlocks."""
import time
import pytest
from elbow_exo.client import Client, ProcessTransport
from elbow_exo.__main__ import setup_sim
from elbow_exo.protocol import request


@pytest.fixture
def bench():
    with Client(ProcessTransport()) as client:
        client.wait_state("STANDBY")
        yield client


def test_boot_inhibited_and_requires_calibration(bench):
    assert not bench.latest["enabled"]
    with pytest.raises(RuntimeError, match="CALIBRATION_REQUIRED"):
        bench.command("ARM")
    assert not bench.latest["enabled"]


def test_real_bytes_calibrate_move_position_stop(bench):
    setup_sim(bench)
    start = bench.latest["q"]
    bench.command("TARGET", 0.5)
    time.sleep(0.6)
    assert bench.latest["q"] > start + 0.015
    assert bench.latest["state"] == "RUN"
    with pytest.raises(RuntimeError, match="RANGE"):
        bench.command("TARGET", 9)
    bench.command("STOP")
    bench.wait_state("STANDBY")
    assert not bench.latest["enabled"]
    assert bench.bad_frames == 0


@pytest.mark.parametrize("kind,value,fault,state", [
    ("ESTOP", 1, "ESTOP", "ESTOP"),
    ("TEMP", 65, "TEMPERATURE", "FAULT"),
    ("CURRENT", 1.4, "CURRENT", "FAULT"),
    ("SENSOR", 0, "SENSOR", "FAULT"),
    ("VOLTAGE", 30, "VOLTAGE", "FAULT"),
    ("LIMIT_MAX", 1, "LIMIT", "FAULT"),
])
def test_sensor_faults_disable_latch_and_cannot_remote_reset(bench, kind, value, fault, state):
    setup_sim(bench)
    bench.inject(kind, value)
    s = bench.wait_state(state)
    assert s["fault"] == fault
    assert not s["enabled"]
    assert s["torque"] == 0
    with pytest.raises(RuntimeError, match="PHYSICAL_RESET_REQUIRED"):
        bench.command("RESET")
    with pytest.raises(RuntimeError):
        bench.command("ARM")


def test_manual_edge_reset_does_not_rearm(bench):
    setup_sim(bench)
    bench.command("ESTOP")
    bench.wait_state("ESTOP")
    bench.inject("RESET_BUTTON", 1)
    time.sleep(0.06)
    bench.command("RESET")
    s = bench.wait_state("STANDBY")
    assert not s["enabled"]
    assert not s["calibrated"]
    with pytest.raises(RuntimeError, match="CALIBRATION_REQUIRED"):
        bench.command("ARM")


def test_corrupt_heartbeat_cannot_prevent_timeout(bench):
    setup_sim(bench)
    bench.heartbeat(False)
    time.sleep(0.08)  # Let any already queued legitimate heartbeat finish.
    for _ in range(7):
        with bench._lock:
            bench.transport.write(b"65000 HB 0*0000\n")
        time.sleep(0.05)
    s = bench.wait_state("FAULT")
    assert s["fault"] == "HEARTBEAT"
    assert not s["enabled"]
    assert any(e.get("code") == "BAD_CRC" for e in bench.events)


def test_config_can_tighten_but_never_expand_frozen_limits(bench):
    bench.command("TMAX", 0.3)
    bench.command("VMAX", 0.4)
    with pytest.raises(RuntimeError, match="RANGE"):
        bench.command("TMAX", 10)
    with pytest.raises(RuntimeError, match="RANGE"):
        bench.command("VMAX", 10)
    setup_sim(bench)
    with pytest.raises(RuntimeError, match="RANGE"):
        bench.command("ASSIST", 0.5)
    with pytest.raises(RuntimeError, match="STANDBY_REQUIRED"):
        bench.command("KP", 3)

