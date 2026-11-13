# 固件实际验证记录

日期：2026-11-13。以下仅记录本次代理实际执行的软件构建与测试。

| 项目 | 工具/命令 | 实际结果 |
|---|---|---|
| 参数一致性 | Python3.12，`python tools/generate_config.py --check` | 通过；从JSON生成的C参数未过期 |
| 原生构建 | Zig0.14.1，`python firmware/build.py --target host`，C11、O2、Wall/Wextra/Werror | 通过；生成host_sim.exe与control_tests.exe |
| C回归 | `firmware/build/control_tests.exe` | **394个断言通过**；涵盖上电禁能、校准、正方向、位置/速度/加速度/电流/时间限幅、心跳、9类故障、物理复位新边沿、调度超时、CRC、超长/非有限数据、重复与回绕序号 |
| STM32交叉构建 | Arm GNU Toolchain14.3.Rel1，GCC14.3.1 20250623，`python firmware/build.py --target stm32 --compiler <GNU-Arm>/bin/arm-none-eabi-gcc` | **通过**；Cortex-M4 Thumb、soft-float、Os、Wall/Wextra/Werror |
| 链接资源 | `arm-none-eabi-size firmware/build/stm32/open_elbow.elf` | text11588B、data0B、bss1176B；相对于512KiB Flash/128KiB RAM布局 |
| 实体烧录 | SWD | 本次代理未执行 |
| 实体周期/电流环/急停/标定 | 单关节台架 | 本次代理未执行；不能由编译或软件模型证明 |
| 佩戴测试 | 人体适配 | 本次代理未执行 |

最终本地构建产物：

- `firmware/build/stm32/open_elbow.bin`：11644字节；SHA256：`c373be2b7f4cd32832403c9863c628480c957ce493bb5d2c5b9b19f268159e26`。
- `firmware/build/stm32/open_elbow.elf`：21684字节。
- `firmware/build/stm32/open_elbow.map`：本地链接诊断，含本地路径，不随公开发布打包。

GNU Arm官方Windows工具链下载来源：<https://developer.arm.com/-/media/Files/downloads/gnu/14.3.rel1/binrel/arm-gnu-toolchain-14.3.rel1-mingw-w64-x86_64-arm-none-eabi.zip>。下载290006806字节，本地SHA256为`864c0c8815857d68a1bbba2e5e2782255bb922845c71c97636004a3d74f60986`。没有将工具链包提交到仓库。工具链安装目录应使用ASCII路径；本机中文路径导致GCC查找运行库失败后，使用ASCII目录联接成功构建。仓库本身可位于中文路径。

传感器/功率级真实接口和热额定值仍需实际配置与原始记录支持。
