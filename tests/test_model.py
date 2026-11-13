import importlib.util
import json
from pathlib import Path
import xml.etree.ElementTree as ET
import pytest

ROOT = Path(__file__).resolve().parents[1]


def test_urdf_and_canonical_config_match(tmp_path):
    spec = importlib.util.spec_from_file_location("build_model", ROOT / "replay/build_model.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    urdf = ET.parse(module.generate(tmp_path / "elbow.urdf")).getroot()
    cfg = json.loads((ROOT / "config/robot.json").read_text())
    joint = urdf.find("joint[@name='elbow_flexion']")
    limit = joint.find("limit")
    assert joint.find("axis").attrib["xyz"] == "0 0 1"
    assert float(limit.attrib["lower"]) == cfg["joint"]["soft_min_rad"]
    assert float(limit.attrib["upper"]) == cfg["joint"]["soft_max_rad"]
    assert float(limit.attrib["effort"]) == cfg["joint"]["peak_torque_nm"]
    assert float(urdf.find("transmission/actuator/mechanicalReduction").text) == cfg["drive"]["gear_ratio"] * cfg["drive"]["belt_ratio"]
    fore = urdf.find("link[@name='forearm']/inertial")
    mass = float(fore.find("mass").attrib["value"])
    x = float(fore.find("origin").attrib["xyz"].split()[0])
    assert float(fore.find("inertia").attrib["izz"]) + mass*x*x == pytest.approx(cfg["model"]["inertia_kg_m2"])

