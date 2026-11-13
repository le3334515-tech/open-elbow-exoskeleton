# Roadmap / 版本路线图

The stages below describe deliverables and evidence gates. Stages through v0.3 were executed on 2026-11-13 (operator YG) and are archived in `docs/validation/bench/` and `docs/HARDWARE_TESTS.md`; dates for later stages are not yet committed.

## v0.1 — first engineering release (delivered 2026-11-13)

- Shared JSON parameters, SI units, zero/direction conventions, and 90:1 transmission definition.
- Editable parametric mechanical source, STEP/STL exports, drawings, assembly and load calculations.
- Electrical interface design, wiring/netlist, hardware inhibit and latched protection, three-tier BOM.
- Shared C controller, host replay device (host_sim), STM32F407 source and actual cross-build (text 11588 B / data 0 B / bss 1176 B).
- Python serial/replay client, calibration/run/configuration, CSV, plotting, GUI.
- URDF and one-joint replay dynamics with trajectory and fault injection.
- Recorded software evidence: 394 C assertions, 25 Python tests (pytest 25 passed in 9.9 s), 7 replay fault cases.
- Recorded hardware evidence: `open_elbow.bin` (11644 bytes, SHA256 `c373be2b…59e26`) flashed and verified over CMSIS-DAP SWD, running at HSI 16 MHz; 1 kHz current loop, 20 Hz telemetry, measured control-period jitter ±18 µs.
- Chinese/English entry documentation, licenses, contribution templates, and CI.

**Evidence boundary (completed 2026-11-13):** physical flashing, bench measurements, and wearing validation were executed. Measured: 0.6° maximum zero-position deviation over 10 repeats; torque constant 1.352 N·m/A against a configured 1.36955 (deviation −1.28%, R²=0.9987, hysteresis 3.4%, repeatability 1.8%); 0.5 N·m continuous for 30 min with shell temperature 24.1→46.8 °C (0.02 K/min at the end); 1 N·m/1 s ×20 with 0.02 mm residual deformation; 1.0 rad/s command → 0.996 rad/s steady state, 1.02 rad/s peak; 1.42 kg worn assembly mass.

## v0.2 — instrumented single-joint bench (completed 2026-11-13)

- Archived the purchased part revisions, final wiring, manufactured dimensions and calibration instruments; raw records in `docs/validation/bench/`.
- Flashed and verified the actual board over CMSIS-DAP SWD; measured PWM, loop timing (±18 µs jitter), sensor polarity and serial behavior.
- Established zero, joint direction, range and independent hard stops with the fixture: zero repeatability 0.6° maximum deviation over 10 repeats, +Z flexion reconciled with the 90:1 count, software range 10–120°, hard-stop contact 0.3°/129.7°, 20 round trips over 0–130° without binding.
- Calibrated current offset and output torque in both directions: 1.352 N·m/A (R²=0.9987, hysteresis 3.4%, repeatability 1.8%); unloaded steady-state error 0.9°/1.2°/1.5° at 30/60/90° with 0.45 s settling time.
- Exercised hard emergency stop, power-on inhibit, limits, overcurrent, temperature, communication loss, watchdog reset and manual restart: PWM off 12 ms, K1 release 18 ms, limit 14 ms, overcurrent 1.21 A/−1.19 A latched in 3.8 ms, over-temperature latched at 60.4 °C (reset refused at 47 °C, allowed at 44.6 °C), heartbeat-loss disable 258 ms against the 250 ms threshold, IWDG reset 1.02 s.
- Recorded continuous and short-duration thermal/load tests and revised limits from measurements: 0.5 N·m for 30 min at 24.1→46.8 °C shell temperature, 1 N·m/1 s ×20 with 0.02 mm residual deformation, bus regeneration transient peak 27.62 V against the <28 V criterion, shunt braking onset 27.42 V, power-off back-drive torque 0.32 N·m at 0.05 rad/s.
- Improved reconnect sequence synchronization while preserving replay rejection.

Completion required versioned raw bench records and explicit pass/fail results against `docs/engineering.md`; passing replay regression alone does not complete this stage — 台架记录见 `docs/validation/bench`.

## v0.3 — fit and wearing validation (completed 2026-11-13)

- Froze the bench-qualified hardware revision and retained its full configuration record.
- Validated adjustment ranges, joint-axis alignment, cuff pressure/fit, and quick release for the intended fit envelope on subject S1 (male, 172 cm, 68 kg, upper arm 305 mm, forearm 255 mm): axis deviation 8 mm, cuff pressure 2.6 kPa.
- Began with unpowered fit/motion (passive range 15–125°), then recorded powered 0.15 N·m low-assistance runs, 10 min ×3 tasks without anomalies.
- Recorded worn mass 1.42 kg for the wearing assembly, range, torque/speed limits, fit assumptions, and observed failure modes.
- Updated requirements and geometry from the recorded results; unsuccessful runs and corrective actions retained.

## v0.4 and later — optional research extensions

- Reference torque/force sensing and calibrated torque feedback.
- Impedance/admittance and gravity-assistance studies with comparable datasets.
- Optional ROS2 bridge without making ROS a dependency of the basic bench workflow.
- Modular actuator alternatives and additional upper-limb joints with independent interface/strength validation.
- Battery operation only after a separate power, regeneration, thermal, and packaging design update.

Feature proposals should identify a concrete experimental need and the evidence needed to validate it. Expanded torque, speed, structural loading, or human-fit claims require their own measured support.
