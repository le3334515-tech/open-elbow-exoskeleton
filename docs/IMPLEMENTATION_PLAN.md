# 首版工程交付执行记录

日期：2026-11-13。工作区无既有硬件、图纸或代码。未假定拥有任何实体部件。

## 已确定的接口

以 config/robot.json 为唯一参数来源；rad、rad/s、Nm、A、V、摄氏度，尺寸明确标 mm。屈肘为 +Z 右手方向；伸直为零。软件范围 10–120°，实体挡块 0–130°。30:1 减速电机、20/60 齿同向开式同步带，总减速 90:1。0.5 Nm 连续、1 Nm 短时均为设计目标，电流到力矩映射为估算。

通信：115200 8N1；请求为 ASCII `SEQ OP VALUE*CRC16\n`，CRC16-CCITT-FALSE 对星号前的原始字节计算，4 位十六进制。SEQ 为 0–65535。每次启动仅接受递增序列（模 65536，前向差 1–32767），首帧任意。最大行长 96 字节。OP：PING、HB、CAL、ARM、STOP、RESET、ESTOP、TARGET、ASSIST、KP、KD、TMAX、VMAX。每个请求都有数值 VALUE，无参数用 0。只有合法 HB 更新心跳。合法请求返回 JSON ack，定时返回 JSON status；响应也加同样 CRC。status 必含 type、state、fault、q、dq、current、temperature、voltage、torque、enabled、time_ms。故障 RESET 还须物理复位输入，远端指令不能独立复位实体台架。

## 实施与验收

- [x] 参数生成：JSON → C 头文件，检查几何、URDF 和模型一致性。
- [x] 固件：纯 C 控制核心、受界限约束的协议解析、原生测试执行程序、STM32F407 裸机板级驱动、GNU Arm 构建和烧录步骤。
- [x] 上位机：Python 串口/模拟 C 固件连接、状态、配置、CSV 日志、绘图；同一个 C 控制核心用于模拟，避免另写替代状态机。
- [x] 机械：CadQuery 参数化源、完整 STEP、逐件 STL、装配图、限位和脱离结构；生成几何校验和受力计算。
- [x] 电气：接线 SVG、引脚、电源预算、三档 BOM、保护功能归属和采购来源。
- [x] 仿真：一自由度动力学、URDF、轨迹/方向/范围/故障场景，保存 CSV/JSON/SVG。
- [x] 开源：中英文 README、三类许可证、第三方来源、贡献/Issue/CI/路线图。
- [x] 实际运行构建、控制测试、串口模拟端到端、仿真、CAD 导出和一致性检查，保存实际结果；台架及佩戴测试写“未执行”。
- [x] 发布前检查名称、隐私和密钥；已登录则创建公开仓库并推送、配置介绍和版本发布；无登录则保留完整本地交付并记录准确阻塞。

## 工具选择依据

现机 Windows，Python 3.12/3.14、Git 2.56.0、GitHub CLI 2.92.0、Arm Compiler 6.16 可用。未发现当前 PATH 中的 GNU Arm、CMake 或 CAD CLI。使用工作区隔离 Python 环境安装可复现的 CadQuery 与构建依赖；优先官方 GNU Arm 工具链和纯 C 固件，CI 使用 Ubuntu。GitHub CLI 初检无登录，Git Credential Manager 无可用凭据。

## 首版实际交付状态

工程文件、原生与STM32构建、已执行范围内测试、仿真、CAD导出及公开仓库发布已完成。实体烧录、台架、佩戴未执行，记录在HARDWARE_TESTS.md。公开仓库：https://github.com/le3334515-tech/open-elbow-exoskeleton 。
