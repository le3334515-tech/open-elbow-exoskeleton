"""Generate the SI kinematic/inertial URDF directly from canonical parameters."""
import argparse
import json
from pathlib import Path
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]


def generate(destination):
    cfg = json.loads((ROOT / "config/robot.json").read_text(encoding="utf-8"))
    j, model = cfg["joint"], cfg["model"]
    robot = ET.Element("robot", name=cfg["project"])
    ET.SubElement(robot, "link", name="world")
    upper = ET.SubElement(robot, "link", name="upper_arm")
    fore = ET.SubElement(robot, "link", name="forearm")
    upper_len = cfg["mechanical"]["upper_nominal_mm"] / 1000
    fore_len = model["forearm_length_m"]
    for link, length, x, mass, color in [(upper, upper_len, -upper_len / 2, .65, "0.18 0.24 0.34 1"), (fore, fore_len, fore_len / 2, model["forearm_mass_kg"], "0.05 0.55 0.65 1")]:
        inertial = ET.SubElement(link, "inertial")
        ET.SubElement(inertial, "origin", xyz=f"{x} 0 0", rpy="0 0 0")
        ET.SubElement(inertial, "mass", value=str(mass))
        # Model uses inertia about the joint; URDF inertia must be about COM.
        izz = max(0.001, model["inertia_kg_m2"] - mass * x * x) if link is fore else mass * length * length / 12
        ET.SubElement(inertial, "inertia", ixx="0.0003", ixy="0", ixz="0", iyy=str(izz), iyz="0", izz=str(izz))
        for tag in ("visual", "collision"):
            visual = ET.SubElement(link, tag)
            ET.SubElement(visual, "origin", xyz=f"{x} 0 0", rpy="0 0 0")
            geom = ET.SubElement(visual, "geometry")
            ET.SubElement(geom, "box", size=f"{length} 0.035 0.012")
            if tag == "visual":
                material = ET.SubElement(visual, "material", name=link.attrib["name"] + "_color")
                ET.SubElement(material, "color", rgba=color)
    fixed = ET.SubElement(robot, "joint", name="bench_mount", type="fixed")
    ET.SubElement(fixed, "parent", link="world")
    ET.SubElement(fixed, "child", link="upper_arm")
    # x-y is the arm plane, +Z flexes the elbow by the right-hand rule.
    joint = ET.SubElement(robot, "joint", name="elbow_flexion", type="revolute")
    ET.SubElement(joint, "parent", link="upper_arm")
    ET.SubElement(joint, "child", link="forearm")
    ET.SubElement(joint, "origin", xyz="0 0 0", rpy="0 0 0")
    ET.SubElement(joint, "axis", xyz="0 0 1")
    ET.SubElement(joint, "limit", lower=str(j["soft_min_rad"]), upper=str(j["soft_max_rad"]), effort=str(j["peak_torque_nm"]), velocity=str(j["max_velocity_rad_s"]))
    ET.SubElement(joint, "dynamics", damping=str(model["damping_nm_s_rad"]), friction="0")
    transmission = ET.SubElement(robot, "transmission", name="gearbox_and_belt")
    ET.SubElement(transmission, "type").text = "transmission_interface/SimpleTransmission"
    tj = ET.SubElement(transmission, "joint", name="elbow_flexion")
    ET.SubElement(tj, "hardwareInterface").text = "hardware_interface/EffortJointInterface"
    actuator = ET.SubElement(transmission, "actuator", name="brushed_motor")
    ET.SubElement(actuator, "mechanicalReduction").text = str(cfg["drive"]["total_ratio"])
    ET.indent(robot, space="  ")
    dst = Path(destination)
    dst.parent.mkdir(parents=True, exist_ok=True)
    ET.ElementTree(robot).write(dst, encoding="utf-8", xml_declaration=True)
    return dst


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--output", default=str(ROOT / "replay/elbow.urdf"))
    args = p.parse_args()
    print(generate(args.output))

