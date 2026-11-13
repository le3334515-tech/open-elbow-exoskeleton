# Contributing

Contributions to the modular elbow platform are welcome. This release is an engineering software/simulation prototype. Report a design target, calculation, simulation, manufacturer specification, and physical measurement as distinct evidence classes.

## Working on a change

1. Open an issue describing the concrete problem and affected subsystem. Include the software revision and evidence provenance.
2. Create a focused branch. Keep unrelated refactors and generated build artifacts out of the change.
3. Read `config/robot.json`, `docs/engineering.md`, and the relevant subsystem README. SI units, zero position, +Z flexion, transmission direction, limits, and board pins are shared interfaces.
4. Change the canonical JSON before derived parameters. Regenerate affected firmware headers, URDF, and CAD exports; describe geometry or pin changes explicitly.
5. Run the checks appropriate to your change and include the actual commands and results in the pull request. An unperformed physical check must remain marked **not executed**.

## Local software checks

```bash
python -m pip install -e '.[test]'
python firmware/build.py --target host
python tools/generate_config.py --check
python -m pytest -q
python simulation/validate.py --output artifacts/simulation
```

Windows without a native C compiler can install `ziglang==0.14.1`. Firmware changes also require `python firmware/build.py --target stm32` with GNU Arm Embedded installed. Mechanical changes use the pinned CAD dependency and `python mechanical/source/build_cad.py`. Do not check in local compiler caches, executable build directories, serial logs containing personal information, or credentials.

## Evidence and engineering changes

- State the test subject: native C controller, simulated plant, physical bench, or worn assembly.
- Preserve raw input, configuration, calibration method, timestamp, software revision, units, and instrument information when reporting measurements.
- Do not replace a missing hardware result with an ideal-model value. Keep design assumptions visible until measured.
- Structural changes should include the load case and calculation basis; motor/driver changes should reconcile voltage, current, interfaces, reduction ratio, and protection thresholds.
- A physical modification does not automatically validate firmware or the matching CAD revision. Identify the exact assembly/configuration tested.

## Style and review

Prefer small modules and explicit names. Keep C control logic independent of board I/O, and keep simulated injection out of the physical protocol. Add regression tests for meaningful parser, control, or fault-handling behavior. Maintain Chinese user instructions and update the English entry points when commands or interfaces change. Pull requests should explain the final behavior, evidence, and remaining verification work.

## Licensing

By submitting original changes, you provide them under the repository license applicable to that directory: Apache-2.0 for software, CERN-OHL-W-2.0 for hardware design, and CC-BY-4.0 for documentation. Identify any third-party material, retain its original notices, and update `THIRD_PARTY.md`. Runtime notices for prebuilt firmware/native binaries must accompany redistribution.
