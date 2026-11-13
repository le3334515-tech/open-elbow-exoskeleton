# Third-party sources and notices

No third-party CAD, vendor firmware, human photographs, or proprietary schematic packages are copied into this repository. Commercial part envelopes were created from basic publicly documented dimensions and are explicitly simplified. Links are references, not endorsements or proof of system performance.

| Source/dependency | Use | License / source handling |
|---|---|---|
| Python | Bench tools and generation | PSF; external runtime |
| pyserial3.5 | Serial port access | BSD-3-Clause; installed dependency |
| matplotlib | Plots, dashboard and telemetry animation | Matplotlib license; installed dependency |
| pytest | Software test runner | MIT; development dependency |
| CadQuery2.6.1 / OCP / OpenCASCADE | Parametric geometry and STEP/STL export | Apache-2.0 / LGPL-2.1 with exception; external dependencies, not bundled |
| GNU Arm Embedded14.3.Rel1 | STM32 compilation; runtime linked into binary | GCC runtime/Newlib notices in [firmware/third_party_licenses](firmware/third_party_licenses/README.md) |
| Zig0.14.1 | Native Windows C build | MIT compiler plus native runtime notices; see firmware notices |
| GitHub Actions checkout/setup-python/upload-artifact | CI orchestration | MIT; invoked remote actions, not vendored |
| SPDX license-list-data | Verbatim license texts | Official license texts under LICENSES/; fetched from https://github.com/spdx/license-list-data/tree/main/text |
| Pololu4692 product and37D documentation | Dimensions, nominal/extrapolated motor specs and USD price | Vendor copyright; linked only; [source log](hardware/source_checks.json) |
| Cytron MD10C materials | PWM/DIR interface and driver selection | Vendor copyright; linked only; inaccessible pages explicitly noted in source log |
| ST RM0090 / STM32F407 datasheet | Register mapping and pin functions | ST copyright; original register-level implementation, no copied HAL |
| ams AS5600, TI INA240/LM339B, Nexperia logic datasheets | Interface/threshold component selection | Vendor copyright; linked only, see [procurement sources](hardware/sources.md) |

Python plotting/CAD dependencies may install additional transitive packages; they retain their own licenses. Runtime packages and download caches are excluded from source control. Binary releases include the applicable firmware runtime notices. Documentation and original design license scope is specified in [LICENSE.md](LICENSE.md).

