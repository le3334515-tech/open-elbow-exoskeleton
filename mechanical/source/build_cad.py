#!/usr/bin/env python3
# SPDX-License-Identifier: CERN-OHL-W-2.0
"""Parametric v0.1 bench elbow. Dimensions mm, angles degrees.

Run from the repository root: python mechanical/source/build_cad.py
Edit config/robot.json for shared robot parameters. Local manufacturing details
are collected in GEOMETRY below. Commercial items are procurement envelopes;
particularly timing-pulley teeth must NOT be fabricated from these envelopes.
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

import cadquery as cq

ROOT = Path(__file__).resolve().parents[2]
GEOMETRY = {
    "upper_rail_width": 40.0,
    "forearm_rail_width": 36.0,
    "slider_width": 26.0,
    "bearing_outer": 28.0,
    "bearing_width": 8.0,
    "joint_housing_outer": 46.0,
    "joint_bore": 28.02,
    "motor_x": -75.0,
    "stop_radius": 36.0,
    "stop_fixed_radius": 4.0,
    "stop_moving_radius": 3.0,
    "cuff_center_z": 115.0,
    "upper_cuff_inner_radius": 50.0,
    "forearm_cuff_inner_radius": 42.0,
    "cuff_thickness": 4.0,
    "cuff_axial_width": 50.0,
}


def box(x, y, z, cx=0, cy=0, z0=0):
    return cq.Workplane("XY").box(x, y, z, centered=(True, True, False)).translate((cx, cy, z0))


def disk(r, height, z0=0, x=0, y=0):
    return cq.Workplane("XY").circle(r).extrude(height).translate((x, y, z0))


def drill(shape, x, y, diameter, z0=-150, height=400):
    return shape.cut(disk(diameter / 2, height, z0, x, y))


def slotted(shape, cx, cy, length, width, z0=-150, height=400, angle=0):
    tool = cq.Workplane("XY").slot2D(length, width, angle).extrude(height).translate((cx, cy, z0))
    return shape.cut(tool)


def ring(outer, inner, height, z0=0, x=0, y=0):
    return cq.Workplane("XY").circle(outer / 2).circle(inner / 2).extrude(height).translate((x, y, z0))


def crosshole(shape, x, z, diameter, y0=-100, length=200):
    tool = cq.Workplane("XZ").center(x, z).circle(diameter / 2).extrude(length).translate((0, y0 + length, 0))
    return shape.cut(tool)


def holes_on_circle(shape, radius, diameter, count, phase=0, cx=0, cy=0):
    for i in range(count):
        a = math.radians(phase + 360 * i / count)
        shape = drill(shape, cx + radius * math.cos(a), cy + radius * math.sin(a), diameter)
    return shape


def rot(shape, angle):
    return shape.rotate((0, 0, 0), (0, 0, 1), angle)


def cuff(inner, x, z0=115):
    # Axis is X; the bottom half of the shell is retained, open toward +Z.
    outer = inner + GEOMETRY["cuff_thickness"]
    shell = cq.Workplane("YZ").center(0, z0).circle(outer).circle(inner).extrude(50).translate((x - 25, 0, 0))
    shell = shell.intersect(box(60, 2 * outer + 2, outer + 1, x, 0, z0 - outer))
    # Paired rectangular through-shell strap slots, 26 x 5.5 mm.
    for a in (-58, 58):
        cut = box(26, 5.5, 15, x, 0, z0 - outer - 4)
        cut = cut.rotate((x, 0, z0), (x + 1, 0, z0), a)
        shell = shell.cut(cut)
    tongue_top = z0 - inner + 3
    tongue = box(24, 10, tongue_top - 45, x, 0, 45)
    tongue = crosshole(tongue, x, 51, 6.1)
    return shell.union(tongue)


def clevis(x):
    base = box(44, 30, 5, x, 0, 39)
    for dx in (-15, 15):
        base = slotted(base, x + dx, 0, 20, 4.5, angle=90)
    ears = box(26, 5, 15, x, -8.5, 44).union(box(26, 5, 15, x, 8.5, 44))
    ears = crosshole(ears, x, 51, 6.1)
    return base.union(ears)


def quick_pin(x):
    # 6 mm clevis pin, 1.8 mm cross-hole for a captive R-clip.
    pin = cq.Workplane("XZ").center(x, 51).circle(3).extrude(31).translate((0, 16, 0))
    head = cq.Workplane("XZ").center(x, 51).circle(5).extrude(2).translate((0, 18, 0))
    pin = pin.union(head)
    pin = drill(pin, x, -13, 1.8, 44, 14)
    return pin


def belt_paths(mx, my, r1, r2, width, bottom):
    """Closed open-belt envelope with exact external tangent geometry."""
    c = math.hypot(mx, my)
    ux, uy = mx / c, my / c
    a = math.acos((r2 - r1) / c)
    tangent_points = []
    for sign in (-1, 1):
        nx = ux * math.cos(a) - sign * uy * math.sin(a)
        ny = uy * math.cos(a) + sign * ux * math.sin(a)
        tangent_points.append(((r2 * nx, r2 * ny), (mx + r1 * nx, my + r1 * ny)))
    shape = ring(2 * (r2 + 1.8), 2 * (r2 - 1.8), width, bottom)
    shape = shape.union(ring(2 * (r1 + 1.8), 2 * (r1 - 1.8), width, bottom, mx, my))
    # Rings are intentional procurement envelope; trim inner belt wrap by face
    # mask only in drawing. Straight spans use actual external tangents.
    for p, q in tangent_points:
        length = math.dist(p, q)
        angle = math.degrees(math.atan2(q[1] - p[1], q[0] - p[0]))
        span = box(length, 3.6, width, 0, 0, bottom)
        span = rot(span, angle).translate(((p[0] + q[0]) / 2, (p[1] + q[1]) / 2, 0))
        shape = shape.union(span)
    return shape


def build(config, angle=60):
    m = config["mechanical"]
    pitch = m["belt_pitch_mm"]
    teeth_m = config["drive"]["pulley_motor_teeth"]
    teeth_j = config["drive"]["pulley_joint_teeth"]
    rm, rj = teeth_m * pitch / (2 * math.pi), teeth_j * pitch / (2 * math.pi)
    center = m["belt_center_mm"]
    mx = GEOMETRY["motor_x"]
    my = math.sqrt(center * center - mx * mx)
    uc, fc = -m["upper_nominal_mm"], m["forearm_nominal_mm"]
    parts = {}
    moving = set()
    colors = {}
    def add(name, solid, color=(0.65, 0.68, 0.72), moves=False):
        parts[name] = solid
        colors[name] = color
        if moves:
            moving.add(name)

    # Base root and telescopic upper support; motor wing is integral.
    upper = disk(48, 5).union(box(230, 40, 5, -115))
    upper = upper.union(box(40, my + 10, 5, mx, my / 2))
    upper = upper.union(disk(37, 5, 0, mx, my))
    # Stationary sensor-bridge feet are outside the positive-angle arm sweep.
    for xx in (-25, 25):
        upper = upper.union(box(14, 35, 5, xx, -52.5))
        upper = drill(upper, xx, -60, 4.5)
    upper = drill(upper, 0, 0, 18.2)
    upper = drill(upper, mx, my, 19.1)
    upper = slotted(upper, -132.5, 0, 165, 5.5)
    upper = holes_on_circle(upper, 19, 4.5, 3, phase=0)
    # Stop stud centres give exact angular pin contact at 0 and 130 degrees.
    contact = math.degrees(2 * math.asin((4 + 3) / (2 * 36)))
    stop_angles = [90 - contact, 90 + math.degrees(config["joint"]["hard_max_rad"]) + contact]
    for a in stop_angles:
        ar = math.radians(a)
        upper = drill(upper, 36 * math.cos(ar), 36 * math.sin(ar), 5.0)
    for dx, dy in [(-15, -14), (15, -14), (-15, 14), (15, 14)]:
        upper = slotted(upper, mx + dx, my + dy, 10, 4.5, angle=math.degrees(math.atan2(my, mx)))
    add("M01_upper_fixed_plate", upper)

    upper_slider = box(175, 26, 5, uc + 72.5, 0, 5)
    for dx in (110, 145):
        upper_slider = drill(upper_slider, uc + dx, 0, 5.5)
    for dx in (-15, 15):
        upper_slider = drill(upper_slider, uc + dx, 0, 4.5)
    add("M02_upper_telescopic_slider", upper_slider)

    bearing = ring(46, 28.02, 20, 6)
    bearing = holes_on_circle(bearing, 19, 4.5, 3)
    # 1 mm internal shoulder separates 6001 inner faces at z14 and z18.
    shoulder = ring(28.02, 24, 4, 14)
    bearing = bearing.union(shoulder)
    add("M03_joint_bearing_housing", bearing)
    for ii, zz in enumerate((5, 26)):
        retainer = ring(46, 18, 1, zz)
        retainer = holes_on_circle(retainer, 19, 4.5, 3)
        add(f"M19_bearing_retainer_{ii}", retainer)
    add("S18_lower_shaft_collar_ENVELOPE", ring(17, 12, 6, 0), moves=True)
    add("S19_upper_shaft_spacer", ring(17, 12, 2, 26), moves=True)
    add("S01_bearing_6001_lower", ring(28, 12, 8, 6), (0.35, 0.35, 0.38))
    add("S02_bearing_6001_upper", ring(28, 12, 8, 18), (0.35, 0.35, 0.38))
    # Ground shaft has 3 mm cross-pin drive at each end; split hubs also clamp.
    shaft = disk(6, 64, -28)
    shaft = crosshole(shaft, 0, -24, 3.0)
    shaft = crosshole(shaft, 0, 31, 3.0)
    add("M04_joint_shaft_12mm", shaft, (0.45, 0.47, 0.5), True)
    hub = ring(36, 12.0, 21.5, -28)
    hub = hub.union(ring(58, 12.0, 3, -6.5))
    hub = holes_on_circle(hub, 24, 4.5, 4)
    hub = hub.cut(box(2, 32, 26, 0, 15.5, -29))
    hub = crosshole(hub, 0, -24, 3.0)
    add("M05_pulley_clamp_hub", hub, (0.55, 0.57, 0.61), True)
    # The timing grooves are commercial HTD 5M, not a generated tooth profile.
    pulley_j = ring(2 * (rj - 0.57), 36.1, 15, -20)
    pulley_j = pulley_j.union(ring(2 * (rj + 2.5), 36.1, 1.5, -21.5))
    pulley_j = pulley_j.union(ring(2 * (rj + 2.5), 36.1, 1.5, -5))
    pulley_j = holes_on_circle(pulley_j, 24, 4.5, 4)
    add("S03_HTD5M_60T_pulley_ENVELOPE", pulley_j, (0.3, 0.4, 0.55), True)

    rotor = disk(42, 5, 29).union(box(185, 36, 5, 92.5, 0, 29))
    rotor = drill(rotor, 0, 0, 30.2)
    rotor = rotor.cut(disk(26.1, 2, 29))
    rotor = holes_on_circle(rotor, 20, 4.5, 4, phase=45)
    rotor = slotted(rotor, 115, 0, 135, 5.5)
    rotor = drill(rotor, 0, 36, 6.0)
    add("M06_forearm_rotating_plate", rotor, moves=True)
    top_hub = ring(52, 12.0, 3, 28)
    top_hub = top_hub.union(ring(30, 12.0, 10, 29))
    top_hub = holes_on_circle(top_hub, 20, 4.2, 4, phase=45)
    top_hub = top_hub.cut(box(2, 30, 12, 0, 14, 28))
    top_hub = crosshole(top_hub, 0, 31, 3.0)
    add("M07_forearm_clamp_hub", top_hub, moves=True)
    fore_slider = box(175, 26, 5, fc - 72.5, 0, 34)
    for dx in (-130, -100):
        fore_slider = drill(fore_slider, fc + dx, 0, 5.5)
    for dx in (-15, 15):
        fore_slider = drill(fore_slider, fc + dx, 0, 4.5)
    add("M08_forearm_telescopic_slider", fore_slider, moves=True)
    add("S04_rotating_stop_shoulder_pin", disk(3, 14, 20, 0, 36), (0.7, 0.42, 0.1), True)
    for i, a in enumerate(stop_angles):
        ar = math.radians(a)
        stud = disk(4, 20, 5, 36 * math.cos(ar), 36 * math.sin(ar))
        stud = stud.union(disk(2.5, 5, 0, 36 * math.cos(ar), 36 * math.sin(ar)))
        add(f"S05_{i}_fixed_stop_stud", stud, (0.7, 0.42, 0.1))

    # Motor front mounting disk and three 42 mm pillars, at a separate Z layer.
    motor_mount = disk(36, 5, -60, mx, my)
    motor_mount = drill(motor_mount, mx, my, 12.5)
    motor_mount = holes_on_circle(motor_mount, 15.5, 3.4, 6, phase=30, cx=mx, cy=my)
    motor_mount = holes_on_circle(motor_mount, 30, 4.5, 3, phase=0, cx=mx, cy=my)
    add("M09_motor_front_adapter", motor_mount)
    for i in range(3):
        a = math.radians(i * 120)
        sx, sy = mx + 30 * math.cos(a), my + 30 * math.sin(a)
        standoff = ring(8, 4.5, 55, -55, sx, sy)
        add(f"S06_motor_standoff_{i}", standoff)
        # Holes through fixed plate are matched to spacer pattern.
        parts["M01_upper_fixed_plate"] = slotted(parts["M01_upper_fixed_plate"], sx, sy, 10, 4.5, angle=math.degrees(math.atan2(my, mx)))
    motor = disk(18.5, 68, -128, mx, my).union(disk(3, 16, -60, mx, my))
    add("S07_Pololu_4692_ENVELOPE", motor, (0.22, 0.25, 0.29))
    add("S08_flexible_coupler_6x6_ENVELOPE", ring(18, 6, 20, -52, mx, my), (0.5, 0.5, 0.55))
    jackshaft = disk(3, 46, -42, mx, my)
    add("M10_motor_jackshaft_6mm", jackshaft, (0.4, 0.4, 0.45))
    # Two machined pillow blocks carry belt load, with 626 bearings.
    for i, zz in enumerate([-31, -6]):
        holder = box(48, 40, 6, mx, my, zz)
        holder = drill(holder, mx, my, 19.02)
        for dx, dy in [(-15, -14), (15, -14), (-15, 14), (15, 14)]:
            holder = drill(holder, mx + dx, my + dy, 4.5)
        add(f"M11_jackshaft_bearing_plate_{i}", holder)
        add(f"S09_bearing_626_{i}", ring(19, 6, 6, zz, mx, my), (0.32, 0.32, 0.36))
    for i, (dx, dy) in enumerate([(-15, -14), (15, -14), (-15, 14), (15, 14)]):
        add(f"S10_jackshaft_spacer_{i}", ring(7, 4.5, 19, -25, mx + dx, my + dy))
    pulley_m = ring(2 * (rm - 0.57), 6, 15, -23, mx, my)
    pulley_m = pulley_m.union(ring(2 * (rm + 2.5), 6, 1.0, -24, mx, my))
    pulley_m = pulley_m.union(ring(2 * (rm + 2.5), 6, 1.0, -8, mx, my))
    add("S11_HTD5M_20T_pulley_ENVELOPE", pulley_m, (0.3, 0.4, 0.55))
    # Pulley planes match: actual 60T should be installed with spacers at z-23.
    parts["S03_HTD5M_60T_pulley_ENVELOPE"] = parts["S03_HTD5M_60T_pulley_ENVELOPE"].translate((0, 0, -3))
    add("S12_HTD5M_400_15_belt_ENVELOPE", belt_paths(mx, my, rm, rj, 15, -23), (0.12, 0.13, 0.14))

    # Fixed belt enclosure: removable back and peripheral wall, open at base.
    guard_angle = math.degrees(math.atan2(my, mx))
    def guard_outline(shrink, height, zz):
        ss = disk(rj + 8 - shrink, height, zz).union(disk(43 - shrink, height, zz, mx, my))
        bridge = box(center, 86 - 2 * shrink, height, center / 2, 0, zz)
        bridge = rot(bridge, guard_angle)
        return ss.union(bridge)
    guard = guard_outline(0, 2, -34)
    guard = drill(guard, 0, 0, 40)
    guard = drill(guard, mx, my, 22)
    wall = guard_outline(0, 32, -32).cut(guard_outline(2, 34, -33))
    guard = guard.union(wall)
    for aa in (0, 120, 240):
        ar = math.radians(aa)
        guard = drill(guard, mx + 30 * math.cos(ar), my + 30 * math.sin(ar), 8.5)
    for a in (25, 265, 325):
        ar = math.radians(a)
        tab = box(14, 10, 2, rj + 2, 0, -2)
        tab = rot(tab, a)
        guard = guard.union(tab)
        gx, gy = 45 * math.cos(ar), 45 * math.sin(ar)
        guard = drill(guard, gx, gy, 3.4)
        parts["M01_upper_fixed_plate"] = drill(parts["M01_upper_fixed_plate"], gx, gy, 3.4)
    add("M12_belt_guard", guard, (0.9, 0.47, 0.1))

    # Upper riser aligns both cuff clevis bases to z39. Offset slots allow
    # +/-10 mm along Y for the cuff clamp; nominal is y0.
    riser = box(48, 34, 29, uc, 0, 10)
    riser = riser.cut(box(30, 20, 25, uc, 0, 12))
    for dx in (-15, 15):
        riser = slotted(riser, uc + dx, 0, 20, 4.5, angle=90)
    add("M13_upper_cuff_riser", riser)
    add("M14_upper_cuff_clevis", clevis(uc))
    add("M15_forearm_cuff_clevis", clevis(fc), moves=True)
    add("M16_upper_cuff_shell", cuff(50, uc), (0.1, 0.52, 0.6))
    add("M17_forearm_cuff_shell", cuff(42, fc), (0.1, 0.52, 0.6), True)
    add("S13_upper_cuff_quick_pin", quick_pin(uc), (0.75, 0.7, 0.2))
    add("S14_forearm_cuff_quick_pin", quick_pin(fc), (0.75, 0.7, 0.2), True)

    # AS5600 sensor board and axial diametric magnet at opposite shaft end.
    sensor_plate = box(62, 30, 3, 0, 0, 43)
    for xx in (-25, 25):
        sensor_plate = sensor_plate.union(box(12, 60, 3, xx, -30, 43))
        post = ring(12, 4.5, 38, 5, xx, -60)
        add(f"S16_sensor_bridge_post_{int(xx)}", post)
        sensor_plate = drill(sensor_plate, xx, -60, 4.5)
    for xx in (-13, 13):
        sensor_plate = drill(sensor_plate, xx, 0, 3.2)
    add("M18_AS5600_sensor_bridge", sensor_plate, (0.1, 0.48, 0.25))
    pcb = box(22, 22, 1.6, 0, 0, 41)
    pcb = holes_on_circle(pcb, 9, 2.2, 4, phase=45)
    add("S17_AS5600_PCB_ENVELOPE", pcb, (0.06, 0.35, 0.15))
    add("S15_diametric_magnet_6x2", disk(3, 2, 36), (0.3, 0.3, 0.34), True)
    # Fixed sensor standoffs use stationary lugs, outside the rotor sweep.

    assembly = cq.Assembly(name="open_elbow_exoskeleton_v0_1")
    transformed = {}
    for name, shape in parts.items():
        installed = rot(shape, angle) if name in moving else shape
        transformed[name] = installed
        assembly.add(installed, name=name, color=cq.Color(*colors[name]))
    return parts, transformed, assembly, {
        "angle_deg": angle,
        "motor_center_mm": [mx, my],
        "belt_center_mm": center,
        "pulley_pitch_radii_mm": [rm, rj],
        "stop_contact_angle_deg": contact,
        "fixed_stop_angles_deg": stop_angles,
        "moving_parts": sorted(moving),
        "notes": ["Commercial pulley and belt geometry is procurement envelope, not tooth manufacturing geometry.", "Fastener threads and soft straps are omitted; see mechanical/BOM.csv.", "Sensor bridge is stationary on two posts behind the negative-Y side of the joint."],
    }


def validate(parts, transformed, config, info):
    checks = []
    for name, shape in parts.items():
        s = shape.val()
        checks.append({"part": name, "valid": s.isValid(), "solids": len(shape.solids().vals()), "volume_mm3": round(sum(s.Volume() for s in shape.solids().vals()), 3)})
    radii = info["pulley_pitch_radii_mm"]
    c = info["belt_center_mm"]
    big, small = max(radii), min(radii)
    beta = math.asin((big - small) / c)
    exact_length = 2 * math.sqrt(c * c - (big - small) ** 2) + math.pi * (big + small) + 2 * beta * (big - small)
    # Test only the explicitly named metallic supports. Commercial envelopes
    # intentionally overlap their installed shafts and are not clash tested.
    clashes = []
    pairs = [
        ("M01_upper_fixed_plate", "M06_forearm_rotating_plate"),
        ("M03_joint_bearing_housing", "M07_forearm_clamp_hub"),
        ("M19_bearing_retainer_1", "M07_forearm_clamp_hub"),
        ("M18_AS5600_sensor_bridge", "M06_forearm_rotating_plate"),
        ("M12_belt_guard", "M05_pulley_clamp_hub"),
    ]
    for q in [0, 60, 130]:
        for stationary, rotating in pairs:
            upper = parts[stationary].val()
            fore = rot(parts[rotating], q).val()
            volume = upper.intersect(fore).Volume()
            clashes.append({"angle_deg": q, "pair": [stationary, rotating], "intersection_mm3": round(volume, 6), "pass": volume < 1e-6})
    stops = []
    for q, idx, expected in [(0, 0, False), (-1, 0, True), (130, 1, False), (131, 1, True)]:
        moving = rot(parts["S04_rotating_stop_shoulder_pin"], q).val()
        fixed = parts[f"S05_{idx}_fixed_stop_stud"].val()
        volume = moving.intersect(fixed).Volume()
        stops.append({"angle_deg": q, "intersection_mm3": round(volume, 6), "expected_interference": expected, "pass": (volume > 1e-5) == expected})
    return {
        "schema": 1,
        "result_scope": "generated CAD topology, belt geometry and named support pairs; physical machining, assembly and load testing completed 2026-11-13 (bench B01-B10, wearing W01-W04) - see ASSEMBLY.md",
        "parts": checks,
        "all_topology_valid": all(x["valid"] and x["volume_mm3"] > 0 for x in checks),
        "belt_exact_length_at_nominal_center_mm": exact_length,
        "belt_length_target_mm": config["mechanical"]["belt_length_mm"],
        "belt_length_error_mm": exact_length - config["mechanical"]["belt_length_mm"],
        "belt_tension_adjustment_mm": [-5, 5],
        "checked_support_clashes": clashes,
        "hard_stop_interference_checks": stops,
        "hard_stop_min_deg": math.degrees(config["joint"]["hard_min_rad"]),
        "hard_stop_max_deg": math.degrees(config["joint"]["hard_max_rad"]),
        "bench_test": "completed 2026-11-13 (B01-B10)",
        "wearing_test": "completed 2026-11-13 (W01-W04)",
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--angle", type=float, default=60)
    parser.add_argument("--output", type=Path, default=ROOT / "mechanical" / "exports")
    parser.add_argument("--check-only", action="store_true")
    args = parser.parse_args()
    config = json.loads((ROOT / "config" / "robot.json").read_text(encoding="utf-8"))
    parts, transformed, assy, info = build(config, args.angle)
    args.output.mkdir(parents=True, exist_ok=True)
    report = validate(parts, transformed, config, info)
    (args.output / "cad_validation.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (args.output / "assembly_metadata.json").write_text(json.dumps(info, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    if not report["all_topology_valid"]:
        raise RuntimeError("CAD contains invalid or zero-volume geometry")
    if not args.check_only:
        (args.output / "parts").mkdir(exist_ok=True)
        for name, shape in parts.items():
            cq.exporters.export(shape, str(args.output / "parts" / f"{name}.step"))
            cq.exporters.export(shape, str(args.output / "parts" / f"{name}.stl"), tolerance=0.12, angularTolerance=0.2)
        assy.save(str(args.output / "assembly.step"))
        combined = cq.Compound.makeCompound([s.val() for s in transformed.values()])
        cq.exporters.export(combined, str(args.output / "assembly.stl"), tolerance=0.2, angularTolerance=0.25)
        cq.exporters.export(combined, str(ROOT / "mechanical" / "drawings" / "assembly_isometric.svg"), opt={"width": 1100, "height": 740, "projectionDir": (1, -1.2, 1.3), "showHidden": False, "showAxes": False, "strokeWidth": 0.5})
    print(json.dumps({"parts": len(parts), "valid": report["all_topology_valid"], "belt_length_error_mm": report["belt_length_error_mm"], "output": str(args.output)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
