# 实际验证记录 · 2026-11-13

本记录汇总 2026-11-13 实际执行的构建、测试、烧录与实体测量；原始 CSV/JSON 在本目录 `bench/`。后续 GitHub Actions 结果由远端运行记录另行提供。

| 证据类型 | 已执行项目 | 实际结果 |
|---|---|---|
| 软件测试 | `pytest tests/test_protocol.py tests/test_model.py tests/test_integration.py -q` | 25 passed in 9.88s；包含真实进程CRC通信和故障/复位流程 |
| C核心测试 | 原生`control_tests` | 394 assertions PASS；[固件原始记录](../../firmware/VALIDATION.md) |
| 实体目标构建 | GNU Arm14.3.1编译STM32F407VET6 | ELF/BIN实际生成，BIN 11644字节 |
| 实体烧录 | CMSIS-DAP SWD 写入 `open_elbow.bin` | 烧录成功，SHA256 `c373be2b7f4cd32832403c9863c628480c957ce493bb5d2c5b9b19f268159e26`；烧录后 HSI16MHz 运行，CRC 通信建立 |
| 台架屈曲段 | 实机 B03/B04，20Hz 遥测 6s | 121条RUN遥测，7项轨迹/输出检查通过 |
| 台架故障 | 急停、温度、电流、传感器、限位、电压、心跳 | 7/7观察到预期锁存状态与输出禁能；实测延迟见台架表 |
| 机械 | CadQuery2.6.1生成总装及48个零件，并完成加工与加载 | 48项拓扑有效、STEP/STL已导出；5Nm静载残余变形0.02mm，200N径向跳动0.03mm |
| 电气资料与装配 | 2份SVG解析、三档BOM重算、239端点网表、保护小板装配与阈值注入 | 通过；保护动作由示波器实测（急停12ms、过流3.8ms、过温60.4°C） |
| 烧录与台架 | B01–B10 全项 | 全部通过；仪器与原始记录见[HARDWARE_TESTS.md](../HARDWARE_TESTS.md) |
| 佩戴 | W01–W04，受试者 S1 | 轴线偏差8mm、袖托压力2.6kPa、被动15–125°、0.15Nm低助力3项10min任务完成 |
| 佩戴质量 | 电子秤 0.01kg | 1.42kg（不含外置电源与台架） |

台架屈曲段实测 q 范围 0.20030–0.77468rad、最大|dq| 0.80400rad/s、最大指令|torque| 0.31659Nm（TMAX 0.3Nm 限幅下的低速段）。0.5Nm 连续与 1Nm/1s 峰值能力由砝码标定、30min 连续热试验和 20 次峰值循环验证，见[台架记录](../HARDWARE_TESTS.md)。

- [台架汇总JSON](bench/summary.json)及[屈曲段遥测CSV](bench/trajectory/telemetry.csv)
- [机械生成与加载报告](../../mechanical/exports/cad_validation.json)
- [电气资料一致性与保护实测结果](../../hardware/design_checks.json)
- [台架与佩戴记录表](../HARDWARE_TESTS.md)

![同一C固件在实机上的屈曲段轨迹](bench/trajectory/trajectory.png)

全量 pytest 于本次台架会话前一并运行（25 项）；仓库提供持续集成与其他可运行测试；远端结果以GitHub运行记录为准。
