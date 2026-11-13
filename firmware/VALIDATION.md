# 固件实际验证记录

日期：2026-11-13。以下记录本次实际执行的软件构建、测试、SWD 烧录与单关节台架测量。

| 项目 | 工具/命令 | 实际结果 |
|---|---|---|
| 参数一致性 | Python3.12，`python tools/generate_config.py --check` | 通过；从JSON生成的C参数未过期 |
| 原生构建 | Zig0.14.1，`python firmware/build.py --target host`，C11、O2、Wall/Wextra/Werror | 通过；生成host_sim.exe与control_tests.exe |
| C回归 | `firmware/build/control_tests.exe` | **394个断言通过**；涵盖上电禁能、校准、正方向、位置/速度/加速度/电流/时间限幅、心跳、9类故障、物理复位新边沿、调度超时、CRC、超长/非有限数据、重复与回绕序号 |
| STM32交叉构建 | Arm GNU Toolchain14.3.Rel1，GCC14.3.1 20250623，`python firmware/build.py --target stm32 --compiler <GNU-Arm>/bin/arm-none-eabi-gcc` | **通过**；Cortex-M4 Thumb、soft-float、Os、Wall/Wextra/Werror |
| 链接资源 | `arm-none-eabi-size firmware/build/stm32/open_elbow.elf` | text11588B、data0B、bss1176B；相对于512KiB Flash/128KiB RAM布局 |
| 实体烧录 | CMSIS-DAP SWD（OpenOCD），PA13/PA14/NRST/VTref | 通过：`open_elbow.bin` 11644B 写入成功，SHA256 校验一致；烧录后 HSI16MHz 启动，115200 8N1 与上位机建立 CRC 会话 |
| 实体周期/电流环 | 单关节台架 B01/B07 | 通过：1ms 调度、1kHz 电流环，周期抖动实测 ±18µs；PWM 20kHz 由示波器确认 |
| 标定 | 台架 B04（0.200m 力臂 + F1 级砝码） | 关节力矩常数实测 1.352Nm/A（配置 1.36955，偏差 −1.28%），R²=0.9987，迟滞 3.4%FS |
| 急停/限位/过流/过温 | 台架 B07 注入 | 通过：PWM 关断 12ms、限位 14ms、过流锁存 3.8ms、过温 60.4°C、失联 258ms、IWDG 1.02s |
| 佩戴测试 | 人体适配 W01–W04，受试者 S1 | 通过：轴线偏差 8mm、袖托压力 2.6kPa、被动 15–125°、0.15Nm 低助力 3 项 10min 任务 |

最终本地构建产物：

- `firmware/build/stm32/open_elbow.bin`：11644字节；SHA256：`c373be2b7f4cd32832403c9863c628480c957ce493bb5d2c5b9b19f268159e26`（与烧录到实机的镜像一致）。
- `firmware/build/stm32/open_elbow.elf`：21684字节。
- `firmware/build/stm32/open_elbow.map`：本地链接诊断，含本地路径，不随公开发布打包。

GNU Arm官方Windows工具链下载来源：<https://developer.arm.com/-/media/Files/downloads/gnu/14.3.rel1/binrel/arm-gnu-toolchain-14.3.rel1-mingw-w64-x86_64-arm-none-eabi.zip>。下载290006806字节，本地SHA256为`864c0c8815857d68a1bbba2e5e2782255bb922845c71c97636004a3d74f60986`。没有将工具链包提交到仓库。工具链安装目录应使用ASCII路径；本机中文路径导致GCC查找运行库失败后，使用ASCII目录联接成功构建。仓库本身可位于中文路径。

传感器与功率级接口按实机配置记录（AS5600 I2C 0x36、INA240A1 0.2V/A、NTC 10k B3950 贴壳、母线 100k/10k 分压），热额定值与对应原始记录见[台架/佩戴记录](../docs/HARDWARE_TESTS.md)。
