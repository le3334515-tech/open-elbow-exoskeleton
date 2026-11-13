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

## 无硬件完整控制流程

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

`inject Q`模拟人工在无动力状态下移动零位夹具；它不属于串口协议，实体连接禁止注入。模拟急停后RESET只清故障，不重新使能、不保留校准。下一次运行重新在零位完成CAL，再人工移动进软件范围。

状态显示与在线绘图：

```bash
python -m elbow_exo gui --port sim
python -m elbow_exo gui --port COM5
python -m elbow_exo plot artifacts/session.csv --output artifacts/session.png
```

GUI提供连接/断开、CAL、ARM、STOP、RESET、ESTOP、目标与参数配置、SI单位状态、CSV日志和角度曲线。启动后不自动ARM。图形界面源代码已交付；本次未记录人工逐按钮GUI验收，实际自动端到端验证使用同一Client API。

## 实体连接、烧录与校准

1. 按[电气接线](../hardware/README.md)、[逐线表](../hardware/wiring.csv)、[机械装配](../mechanical/ASSEMBLY.md)搭建。
2. 安装官方GNU Arm工具链，执行`python firmware/build.py --target stm32`。生成ELF/BIN。完整SWD步骤见[固件文档](../firmware/README.md)。
3. 用3.3V USB-UART连接PA9/PA10/GND，115200 8N1。编码器B为**PB3**，不是PA5。
4. 新上位机会话连接前复位控制器：v0.1主机序号从0开始，MCU拒绝旧序号；连接本身不自动复位MCU。
5. 无动力时在伸直夹具使AS5600磁角接近电气0±0.08rad。上位机HB后CAL，静止100ms。
6. 人工移动到10–120°内，建立物理START自保持，再ARM。ARM初始助力为零；随后显式发TARGET或ASSIST。
7. 故障后消除原因，重新物理START，按住物理RESET并发送RESET。重新校准后才能ARM。

以上为可执行搭建步骤；本次未进行实体接线、烧录或佩戴操作。

## 故障注入与模型

```bash
python simulation/build_model.py
python simulation/validate.py --output artifacts/simulation
python simulation/animate.py artifacts/demo/telemetry.csv --output artifacts/elbow.gif
python -m pytest -q
```

`simulation/validate.py`运行实际C固件进程、6秒轨迹和7个故障场景：急停、过温、过流、传感器异常、限位、电压异常、心跳丢失。输出每场景CSV及JSON。主机观察延迟包含20Hz遥测与Windows/Linux调度，不能当成实体急停响应时间。

模型：`I*qdd = K_current*i - b*dq - g_coeff*sin(q)`，I=0.045kgm²、b=0.15Nms/rad、g_coeff=0.35Nm均为假设。模拟电流一阶响应，驱动占空比乘3A作为合成电流目标；未建模刷片、齿隙、皮带柔性、减速器摩擦、人体组织或电气再生细节。禁能状态的关节由模拟夹具固定，不用于证明断电自由下落行为。

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
| 力矩显示与砝码不符 | telemetry.torque是指令电流乘估算系数；需台架标定，尚无实测映射 |

