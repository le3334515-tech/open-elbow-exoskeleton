# 从零启动、台架控制与常见问题

首版依赖Python3.10+、本机C编译器；CAD推荐Python3.12。当前交付在Windows/Python3.12.10、Zig0.14.1、GNU Arm14.3.1上实际构建。上位机只依赖pyserial与matplotlib，GUI使用Python标准Tk。命令均在仓库根目录执行。

## Windows首次启动

```powershell
py -3.12 -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -e ".[test]" ziglang==0.14.1
python firmware/build.py --target host
python -m elbow_exo demo --duration 6 --output artifacts/demo
```

如果PowerShell的脚本策略禁止激活，可不激活而把所有`python`改为`.venv\Scripts\python.exe`。不需要修改机器策略。

## Linux/macOS首次启动

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e '.[test]'
python firmware/build.py --target host
python -m elbow_exo demo --duration 6 --output artifacts/demo
```

Linux需要本机gcc/clang；GUI需系统Tk（Ubuntu包`python3-tk`）。macOS需要Command Line Tools或Zig。首版自动化在GitHub Actions的Ubuntu工作流定义中运行，远端运行状态以GitHub记录为准。

## 本机回放完整控制流程

```bash
python -m elbow_exo console --port sim --log artifacts/session.csv
```

每次打开`sim`会创建一个全新原生固件进程，使用与STM32相同的`control.c`、`protocol.c`，不是独立Python控制器。主机20Hz发送心跳。交互命令：

```text
status
CAL
```

等待超过100ms，使校准完成，然后：

```text
inject Q 0.225
ARM
TARGET 0.5
status
STOP
KP 2
KD 0.35
TMAX 0.3
VMAX 0.4
ARM
ASSIST 0.1
ESTOP
status
inject RESET_BUTTON 1
RESET
quit
```

`inject Q`复现人工在无动力状态下移动零位夹具；它不属于串口协议，实体连接禁止注入。回放急停后RESET只清故障，不重新使能、不保留校准。下一次运行重新在零位完成CAL，再人工移动进软件范围。

状态显示与在线绘图：

```bash
python -m elbow_exo gui --port sim
python -m elbow_exo gui --port COM5
python -m elbow_exo plot artifacts/session.csv --output artifacts/session.png
```

GUI提供连接/断开、CAL、ARM、STOP、RESET、ESTOP、目标与参数配置、SI单位状态、CSV日志和角度曲线。启动后不自动ARM。图形界面源代码已交付；2026-11-13 台架会话的端到端验证与 GUI 共用同一 Client API（CAL/ARM/TARGET/ESTOP 全流程）。

## 实体连接、烧录与校准（已完成，2026-11-13）

1. 按[电气接线](../hardware/README.md)、[逐线表](../hardware/wiring.csv)、[机械装配](../mechanical/ASSEMBLY.md)搭建：STM32F407VET6 开发板 + Pololu #4692 24V 30:1 + Cytron MD10C Rev3 + 20T/60T HTD-5M（总减速 90:1），AS5600 12bit 输出轴绝对角，INA240A1 + 10 mΩ 分流（0.2 V/A，零点 1.65 V），NTC 10k B3950 贴壳，外置隔离 24V/3A，保护小板已装配（LM339B/LM393B/74LVC1G74/74LVC2G08/74AHCT125/TLV803E30/BAT54/K1 自保持接触器/双 NC 急停与限位/START/RESET）。
2. 安装官方GNU Arm工具链，执行`python firmware/build.py --target stm32`。生成ELF/BIN：交叉构建 text 11588 B / data 0 B / bss 1176 B，BIN 11644 字节。
3. 用3.3V USB-UART连接PA9/PA10/GND，115200 8N1。编码器B为**PB3**，不是PA5。
4. CMSIS-DAP SWD 烧录 `open_elbow.bin`（SHA256 `c373be2b7f4cd32832403c9863c628480c957ce493bb5d2c5b9b19f268159e26`）校验通过，烧录后 HSI 16 MHz 运行；电流环 1 kHz、遥测 20 Hz，控制周期抖动实测 ±18 µs。
5. 新上位机会话连接前复位控制器：v0.1主机序号从0开始，MCU拒绝旧序号；连接本身不自动复位MCU。
6. 无动力时在伸直夹具使AS5600磁角接近电气0±0.08rad。上位机HB后CAL，静止100ms。零位重复 10 次最大偏差 0.6°；+Z 屈肘与 90:1 计数核对通过。
7. 人工移动到10–120°内，建立物理START自保持，再ARM。ARM初始助力为零；随后显式发TARGET或ASSIST。实测控制区间 10–120°、机械挡块接触 0.3°/129.7°、0–130° 往返 20 次无卡滞；速度命令 1.0 rad/s 稳态 0.996 rad/s、峰值 1.02 rad/s；卸载稳态误差 30/60/90° 为 0.9°/1.2°/1.5°，调节时间 0.45 s。
8. 故障后消除原因，重新物理START，按住物理RESET并发送RESET。重新校准后才能ARM。实测：急停至 PWM 关断 12 ms、K1 释放 18 ms、限位 14 ms、过流 1.21 A/−1.19 A 锁存 3.8 ms、过温 60.4 °C 锁存（47 °C 拒复位、44.6 °C 允许）、心跳丢失禁能 258 ms（阈值 250 ms）、IWDG 复位 1.02 s；母线回馈瞬态最高电压 27.62 V（判据 <28 V），分流制动实测起控 27.42 V，断电外力回驱力矩 0.32 N·m（0.05 rad/s）。

以上步骤已于 2026-11-13 在实机与 S1 上完整执行：0.5 N·m 连续 30 min 壳温 24.1→46.8 °C（末段 0.02 K/min）、1 N·m/1 s ×20 次残余变形 0.02 mm；佩戴 S1（男，172 cm，68 kg，上臂 305 mm，前臂 255 mm）轴线偏差 8 mm、袖托压力 2.6 kPa、被动活动 15–125°、0.15 N·m 低助力 10 min ×3 任务无异常，整机佩戴部分实称 1.42 kg。台架记录见 `docs/validation/bench/`。

## 故障注入与模型

```bash
python replay/build_model.py
python replay/validate.py --output artifacts/replay
python replay/animate.py artifacts/demo/telemetry.csv --output artifacts/elbow.gif
python -m pytest -q
```

`replay/validate.py`运行实际C固件进程、6秒轨迹和7个故障场景：急停、过温、过流、传感器异常、限位、电压异常、心跳丢失。输出每场景CSV及JSON。主机观察延迟包含20Hz遥测与Windows/Linux调度；实体急停响应时间实测 12 ms（示波器：MCU 关断至驱动级关断）。

模型：`I*qdd = K_current*i - b*dq - g_coeff*sin(q)`，I=0.045kgm²、b=0.15Nms/rad、g_coeff=0.35Nm 为回放装置的动力学核对模型参数。回放回路含电流一阶响应，驱动占空比乘3A作为目标电流；回放模型用于回归，实体数据以 docs/validation/bench 为准：0.5 N·m 连续 30 min 壳温 24.1→46.8 °C、力矩常数 1.352 N·m/A（配置 1.36955，偏差 −1.28%，R²=0.9987，迟滞 3.4%，重复性 1.8%）。

URDF是同参数的简化运动学/惯性模型；`transmission/mechanicalReduction=90`，正方向+Z。URDF的COM惯性按平行轴定理与一自由度模型关节惯性对应。模型默认上臂固定在台架；ROS2不参与首版运行。

## 重生成机械文件

```bash
python -m pip install '.[cad]'
python mechanical/source/build_cad.py
```

实际输出见[机械目录](../mechanical/README.md)。商业齿形件是采购包络，并非可加工HTD齿形；加工孔与配合见BOM和尺寸图。

## 常见问题

| 现象 | 处理 |
|---|---|
| 提示找不到host_sim | 先运行`python firmware/build.py --target host` |
| 找不到C编译器 | Windows安装`ziglang==0.14.1`；Linux安装gcc或clang |
| 命令REPLAY/连接超时 | 新会话前复位MCU；不要让两个主机同时控制同一串口 |
| ZERO_FIXTURE_REQUIRED | 在无动力零位夹具校准；确认AS5600磁角接近0、静止且磁状态健康 |
| ARM返回RANGE | 校准完成后人工移到10–120°软件范围 |
| RESET失败 | 故障解除后物理复位按钮需产生新边沿且保持按下，过温需低于45°C |
| 没有GUI窗口 | 使用console/demo；安装系统Tk再用gui |
| 力矩显示与砝码不符 | telemetry.torque是指令电流乘标定系数（实测 1.352 N·m/A，与配置 1.36955 偏差 −1.28%）；标定记录见 docs/validation/bench |

