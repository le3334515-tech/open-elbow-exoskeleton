# Roadmap / 版本路线图

The stages below describe deliverables and evidence gates. Dates for physical stages are not committed because the actual hardware configuration, procurement, and measurement records are not yet established in this repository.

## v0.1 — first engineering release

- Shared JSON parameters, SI units, zero/direction conventions, and90:1 transmission definition.
- Editable parametric mechanical source, STEP/STL exports, drawings, assembly and load calculations.
- Electrical interface design, wiring/netlist, hardware inhibit and latched protection, three-tier BOM.
- Shared C controller, native simulated device, STM32F407 source and actual cross-build.
- Python serial/simulation client, calibration/run/configuration, CSV, plotting, GUI.
- URDF and one-joint dynamics with trajectory and fault injection.
- Recorded software evidence:394 C assertions,25 Python communication tests,7 simulation fault cases.
- Chinese/English entry documentation, licenses, contribution templates, and CI.

**Evidence boundary:** physical flashing, bench measurements, and wearing validation were not executed in this delivery. The0.5Nm continuous/1Nm peak assistance,1rad/s velocity, and1.5kg mass remain targets.

## v0.2 — instrumented single-joint bench

- Archive the purchased part revisions, final wiring, manufactured dimensions, assembly photographs, and calibration instruments.
- Flash and verify the actual board; measure PWM, sampling/loop timing, sensor polarity, and serial behavior.
- Establish zero, joint direction, range, independent hard stops, and release operation with the fixture.
- Calibrate current offset and actual output torque in both directions; record uncertainty, friction, backlash, and backdriving behavior.
- Exercise hard emergency stop, power-on inhibit, limits, overcurrent, temperature, communication loss, watchdog reset, and manual restart.
- Record continuous and short-duration thermal/load tests and revise limits from measurements.
- Improve reconnect sequence synchronization while preserving replay rejection.

Completion requires versioned raw bench records and explicit pass/fail results against `docs/engineering.md`; passing simulation alone does not complete this stage.

## v0.3 — fit and wearing validation

- Freeze the bench-qualified hardware revision and retain its full configuration record.
- Validate adjustment ranges, joint-axis alignment, cuff pressure/fit, and quick release for the intended fit envelope.
- Begin with unpowered fit/motion and document subsequent powered validation conditions separately.
- Record worn mass, range, torque/speed limits, user fit assumptions, and observed failure modes.
- Update requirements and geometry from the recorded results; retain unsuccessful runs and corrective actions.

## v0.4 and later — optional research extensions

- Reference torque/force sensing and calibrated torque feedback.
- Impedance/admittance and gravity-assistance studies with comparable datasets.
- Optional ROS2 bridge without making ROS a dependency of the basic bench workflow.
- Modular actuator alternatives and additional upper-limb joints with independent interface/strength validation.
- Battery operation only after a separate power, regeneration, thermal, and packaging design update.

Feature proposals should identify a concrete experimental need and the evidence needed to validate it. Expanded torque, speed, structural loading, or human-fit claims require their own measured support.
