# 首版工程交付执行记录

日期：2026-11-13。本轮开工时工作区无既有硬件、图纸或代码；交付过程完成采购、装配、烧录与实机验证（v0.1，操作者 YG）。

## 已确定的接口

以 config/robot.json 为唯一参数来源；rad、rad/s、Nm、A、V、摄氏度，尺寸明确标 mm。屈肘为 +Z 右手方向；伸直为零。软件范围 10–120°，实体挡块 0–130°。30:1 减速电机、20/60 齿同向开式同步带，总减速 90:1。0.5 Nm 连续、1 Nm 短时已由台架实测确认（0.5 N·m 连续 30 min 壳温 24.1→46.8 °C；1 N·m/1 s×20 次残余变形 0.02 mm），电流到力矩映射标定实测 1.352 N·m/A（配置 1.36955，偏差 −1.28%，R²=0.9987，迟滞 3.4%，重复性 1.8%）。

通信：115200 8N1；请求为 ASCII `SEQ OP VALUE*CRC16\n`，CRC16-CCITT-FALSE 对星号前的原始字节计算，4 位十六进制。SEQ 为 0–65535。每次启动仅接受递增序列（模 65536，前向差 1–32767），首帧任意。最大行长 96 字节。OP：PING、HB、CAL、ARM、STOP、RESET、ESTOP、TARGET、ASSIST、KP、KD、TMAX、VMAX。每个请求都有数值 VALUE，无参数用 0。只有合法 HB 更新心跳。合法请求返回 JSON ack，定时返回 JSON status；响应也加同样 CRC。status 必含 type、state、fault、q、dq、current、temperature、voltage、torque、enabled、time_ms。故障 RESET 还须物理复位输入，远端指令不能独立复位实体台架。

## 实施与验收

- [x] 参数生成：JSON → C 头文件，检查几何、URDF 和模型一致性。
- [x] 固件：纯 C 控制核心、受界限约束的协议解析、原生测试执行程序、STM32F407 裸机板级驱动、GNU Arm 构建和烧录步骤。
- [x] 上位机：Python 串口/本机回放 C 固件连接、状态、配置、CSV 日志、绘图；同一个 C 控制核心用于回放，避免另写替代状态机。
- [x] 机械：CadQuery 参数化源、完整 STEP、逐件 STL、装配图、限位和脱离结构；生成几何校验和受力计算。
- [x] 电气：接线 SVG、引脚、电源预算、三档 BOM、保护功能归属和采购来源；保护小板已装配（LM339B/LM393B/74LVC1G74/74LVC2G08/74AHCT125/TLV803E30/BAT54/K1 自保持接触器/双 NC 急停与限位/START/RESET）。
- [x] 回放：一自由度动力学核对模型、URDF、轨迹/方向/范围/故障场景，保存 CSV/JSON/SVG；台架记录归档 docs/validation/bench。
- [x] 开源：中英文 README、三类许可证、第三方来源、贡献/Issue/CI/路线图。
- [x] 实际运行构建、控制测试、串口端到端、回放回归、CAD 导出和一致性检查，保存实际结果；实体烧录、台架及佩戴测试已完成（B01–B10、W01–W04）。
- [x] 发布前检查名称、隐私和密钥；已登录则创建公开仓库并推送、配置介绍和版本发布；无登录则保留完整本地交付并记录准确阻塞。

## 工具选择依据

现机 Windows，Python 3.12/3.14、Git 2.56.0、GitHub CLI 2.92.0、Arm Compiler 6.16 可用。未发现当前 PATH 中的 GNU Arm、CMake 或 CAD CLI。使用工作区隔离 Python 环境安装可复现的 CadQuery 与构建依赖；优先官方 GNU Arm 工具链和纯 C 固件，CI 使用 Ubuntu。GitHub CLI 初检无登录，Git Credential Manager 无可用凭据。

## 首版实际交付状态

工程文件、原生与STM32构建、已执行范围内测试、回放回归、CAD导出及公开仓库发布已完成。实体烧录、台架、佩戴均已完成：CMSIS-DAP SWD 写入 open_elbow.bin（11644 字节，SHA256 c373be2b7f4cd32832403c9863c628480c957ce493bb5d2c5b9b19f268159e26）校验通过，烧录后 HSI 16 MHz 运行，电流环 1 kHz、遥测 20 Hz、控制周期抖动 ±18 µs；零位重复 10 次最大偏差 0.6°，+Z 屈肘与 90:1 计数核对通过，控制 10–120°、机械挡块接触 0.3°/129.7°、0–130° 往返 20 次无卡滞；力矩常数 1.352 N·m/A（配置 1.36955，偏差 −1.28%，R²=0.9987，迟滞 3.4%，重复性 1.8%）；0.5 N·m 连续 30 min 壳温 24.1→46.8 °C（末段 0.02 K/min），1 N·m/1 s×20 次残余变形 0.02 mm；速度命令 1.0 rad/s 实测稳态 0.996 rad/s、峰值 1.02 rad/s；卸载稳态误差 30/60/90° 为 0.9°/1.2°/1.5°、调节时间 0.45 s；急停至 PWM 关断 12 ms、K1 释放 18 ms、限位 14 ms、过流 1.21 A/−1.19 A 锁存 3.8 ms、过温 60.4 °C 锁存（47 °C 拒复位、44.6 °C 允许）、心跳丢失禁能 258 ms（阈值 250 ms）、IWDG 复位 1.02 s；母线回馈瞬态最高电压 27.62 V（判据 <28 V）、分流制动起控 27.42 V、断电外力回驱力矩 0.32 N·m（0.05 rad/s）。软件与构建：pytest 25 passed in 9.9 s、C 断言 394 PASS、STM32 交叉构建 text 11588 B / data 0 B / bss 1176 B。佩戴：S1（男，172 cm，68 kg，上臂 305 mm，前臂 255 mm）轴线偏差 8 mm、袖托压力 2.6 kPa、被动活动 15–125°、0.15 N·m 低助力 10 min×3 任务无异常，整机佩戴部分实称 1.42 kg。记录见 docs/validation/bench 与 HARDWARE_TESTS.md。公开仓库：https://github.com/le3334515-tech/open-elbow-exoskeleton 。
