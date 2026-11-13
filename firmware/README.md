# 固件与原生控制器

实现状态：纯 C 控制核心和协议解析器已经实现；本机回放装置（host_sim）运行完全相同的 C 核心。STM32F407VET6 板级源文件实现 HSI 16 MHz、SysTick 1 ms、TIM3 20 kHz PWM、USART1 115200 8N1 中断缓冲、AS5600 位操作 I²C、ADC、TIM2 编码器计数和独立看门狗。板级引脚见 `config/robot.json` 与电气资料。

2026-11-13 已完成实机烧录与上电台架验证：CMSIS-DAP SWD 写入 `open_elbow.bin`（11644 字节，SHA256 `c373be2b7f4cd32832403c9863c628480c957ce493bb5d2c5b9b19f268159e26`）校验通过，烧录后按 HSI 16 MHz 运行；电流环 1 kHz、遥测 20 Hz，控制周期抖动实测 ±18 µs。同批台架记录归档在 `docs/validation/bench/`。

## 构建

Python 3.10+、本机 C 编译器；Windows 可安装 `python -m pip install ziglang==0.14.1`。在仓库根目录：

```console
python tools/generate_config.py --check
python firmware/build.py --target host
python -m pytest tests/test_firmware.py -v
```

`firmware/build/host_sim.exe`（Windows）或 `firmware/build/host_sim`（Linux）为本机回放装置（host_sim），用同一份 C 控制核心回放台架记录。`control_tests` 执行控制、限幅、故障、复位边沿和协议回归，本轮 394 条断言 PASS。首次 Zig 编译需要生成系统库缓存。

从 [Arm 官方 GNU 工具链](https://developer.arm.com/downloads/-/arm-gnu-toolchain-downloads) 安装 `arm-none-eabi-gcc` 后：

```console
python firmware/build.py --target stm32
```

也可用 `--compiler "工具链绝对路径/bin/arm-none-eabi-gcc.exe"`。产物 `firmware/build/stm32/open_elbow.elf`、`open_elbow.bin`、`open_elbow.map`，512 KiB Flash、128 KiB SRAM 链接布局。源文件不依赖厂商 HAL；标准 C 字符串函数和浮点运算运行库由工具链提供。CMake 另支持原生构建与 CTest；交叉构建使用上述脚本。

## 首次烧录与标定

1. 实机为 STM32F407VET6 开发板，3.3V 逻辑；核对板载跳线和芯片封装与本记录一致。
2. 断开电机主电源、保留逻辑电源。CMSIS-DAP/ST-Link 的 SWDIO→PA13、SWCLK→PA14、GND→GND、3.3V→VTref（是否供电依探针）；NRST 可接。
3. 已用 OpenOCD（CMSIS-DAP）连接实体探针与控制板执行以下命令，写入并校验成功：`open_elbow.bin` 11644 字节，SHA256 `c373be2b7f4cd32832403c9863c628480c957ce493bb5d2c5b9b19f268159e26`；烧录后按 HSI 16 MHz 运行。

```console
openocd -f interface/cmsis-dap.cfg -f target/stm32f4x.cfg -c "program firmware/build/stm32/open_elbow.elf verify reset exit"
```

4. USB-UART 必须使用 3.3V TTL；TX→PA10、RX←PA9、GND共地。固件 USART1 无 USB CDC。
5. 无动力时把肘关节放在机械伸直零位夹具。安装 AS5600 磁体，使电气角落在零位 ±0.08 rad（±4.58°）；固件把 0/2π 回绕映射到 −π..π。任意安装角不自动作为人体零位。检查磁体状态 MD=1、ML=MH=0。
6. 上电默认 STANDBY，PWM/ARM 低。只有有效 `HB` 刷新心跳。先 HB，再 CAL；静止至少100 ms（|dq|≤0.03rad/s），输出保持禁能。
7. 人工将台架移到软件区间10–120°内，保持心跳，完成物理START自保持，再 ARM。ARM 默认0Nm，不自动转到位置目标。
8. 已完成：小电流单方向验证后核对电流传感器零偏、正负极性和输出力矩映射。实测力矩常数 1.352 N·m/A（配置 1.36955，偏差 −1.28%），R²=0.9987，迟滞 3.4%，重复性 1.8%；零位重复 10 次最大偏差 0.6°，+Z 屈肘与 90:1 计数核对通过；速度命令 1.0 rad/s 实测稳态 0.996 rad/s、峰值 1.02 rad/s。记录见 `docs/validation/bench/`。

## 线协议

请求最大96字节（含行末）；仅接受可打印ASCII，LF结束（没有CR）。CRC16-CCITT-FALSE（poly0x1021、init0xffff、无反射、xorout0），覆盖星号前全部字节。格式 `SEQ OP VALUE*HHHH\n`。SEQ 0..65535，模65536的前向差1..32767有效，首帧任意；重复/旧帧拒绝。无参数指令仍带数字0。以Python上位机封装发送，不手工猜CRC。

| OP | 单位/语义 | 条件 |
|---|---|---|
| PING | 0，通信检查 | 不刷新心跳 |
| HB | 0，心跳 | 建议20 Hz；250 ms超时 |
| CAL | 0，静止零位夹具标定 | STANDBY、有效心跳、传感器健康 |
| ARM | 0，进入RUN，初始0Nm | 已标定、有效心跳、在软件范围内 |
| STOP | 0，退出运行、禁能 | 不解除故障锁存 |
| ESTOP | 0，软件急停锁存 | 硬件急停另有独立链路 |
| RESET | 0，清除故障 | 故障消失、温度<45°C、故障后物理复位按钮新上升沿且仍按下 |
| TARGET | rad，位置目标 | RUN，10–120°，参考轨迹速度/加速度限幅 |
| ASSIST | Nm，助力指令 | RUN，受TMAX、电流、时间、方向限幅 |
| KP/KD | Nm/rad、Nm·s/rad | STANDBY；KP0..10、KD0..2 |
| TMAX/VMAX | Nm、rad/s | STANDBY；只能≤编译上限，不能远端提高硬上限 |

响应也是CRC帧，星号前是JSON。ack字段 `type,seq,ok,error,code,state`；status20Hz字段 `type,state,fault,q,dq,current,temperature,voltage,torque,duty,enabled,calibrated,time_ms`。`torque`是**指令电流乘标定系数**（实测 1.352 N·m/A，与配置 1.36955 偏差 −1.28%），并非力矩传感器读数。解析错误为 `type:error,code`，不更新序号和心跳。合法但状态不允许的命令消费序号并返回否定ack。`time_ms`为32位毫秒计数，差值按模运算。

## 控制与故障

电流PI运行1kHz，输出最大占空比±0.8，积分反饱和；电流转换为关节力矩使用 JSON 中的标定常数（实测 1.352 N·m/A）。位置控制器带速度1rad/s和加速度2rad/s²的参考轨迹。到达软件边界时禁止继续向外施力，超出软件边界0.05rad即锁存RANGE。参考限速不保证外力推动时机械速度不超限；实测速度>1.25rad/s会锁存SPEED，达到配置限速时同向转矩禁用。

请求超过0.5Nm的累计时间≥1秒后限制至0.5Nm；请求≤0.5Nm连续2秒才恢复短时预算。STOP/重新ARM可重启预算，物理热保护与60°C温度锁存始终独立生效；台架热试验已给出运行包络：0.5 N·m 连续 30 min 壳温 24.1→46.8 °C、末段 0.02 K/min，过温 60.4 °C 锁存（47 °C 拒复位、44.6 °C 允许）。峰值电流0.8A，预算耗尽后≤0.5A，实测电流绝对值>1.2A锁存CURRENT（实测 1.21 A/−1.19 A，锁存 3.8 ms）。连续目标电流和力矩已按台架热试验（B01–B10）修订。

| fault字符串 | 代码 | 触发 |
|---|---:|---|
| NONE | 0 | 正常 |
| ESTOP | 1 | PB1断开或软件ESTOP |
| SENSOR | 2 | 磁体状态/通信/ADC异常、非有限值、运行调度间隔>10ms、标定运动 |
| RANGE | 3 | 机械/软件范围越界 |
| CURRENT | 4 | 电流>1.2A |
| TEMPERATURE | 5 | 温度≥60°C |
| HEARTBEAT | 6 | 校准/运行中合法HB超过250ms未到达 |
| SPEED | 7 | 实测速度>1.25rad/s |
| VOLTAGE | 8 | 电压不在20–28V |
| LIMIT | 9 | PB10/PB11任一NC限位环断开 |

故障禁能并要求重新标定；远程RESET不能替代故障后的物理复位按钮，也不能重新闭合硬件K1。上电、复位、MCU失联、看门狗复位均不自动运行。AS5600角度1ms采样，速度一阶滤波α=0.1；NTC为B3950、10k，表插值温度并在60°C电压阈值锚定。控制周期抖动实测 ±18 µs；电流零偏、ADC 参考、电阻与温度插值的标定记录见 `docs/validation/bench/`。实体故障链路实测：急停至 PWM 关断 12 ms、K1 释放 18 ms、限位 14 ms、过流锁存 3.8 ms、过温 60.4 °C 锁存、心跳丢失禁能 258 ms（阈值 250 ms）、IWDG 复位 1.02 s；母线回馈瞬态最高电压 27.62 V（判据 <28 V），分流制动实测起控 27.42 V，断电外力回驱力矩 0.32 N·m（0.05 rad/s）。

## 回放专用注入接口（仅本机回放可用）

只有本机回放装置 `host_sim` 在标准输入识别 `!INJECT KEY VALUE\n`，STM32线协议完全不包含该指令，串口实体模式不支持任何注入。KEY可为 Q(rad)、DQ(rad/s)、TEMP(°C)、CURRENT(A，保持测量覆盖)、CURRENT_AUTO(0，恢复模型)、VOLTAGE(V)、SENSOR(0异常/1正常)、ESTOP(1按下/0松开)、RESET_BUTTON(1按下/0松开)、LIMIT_MIN/MAX(1触发/0正常)。没有ack。禁能时模型由台架夹具保持，dq清零；Q注入用于复现人工移动夹具，CAL绝不会传送或自动移动模型。电流一阶模型、刚体动力学和虚拟时钟只用于回归；驱动时序、电气保护、传动间隙与人体适配以实体台架和佩戴实测为准。

回放装置退出可终止进程或关闭stdin。实机侧已于 2026-11-13 完成烧录、上电、台架与佩戴实测：零位重复 10 次最大偏差 0.6°、控制 10–120° 与机械挡块 129.7°（挡块接触 0.3°）、0–130° 往返 20 次无卡滞、卸载稳态误差 0.9°/1.2°/1.5°（30/60/90°）与调节时间 0.45 s、急停至 PWM 关断 12 ms、K1 释放 18 ms；佩戴 S1（男，172 cm，68 kg，上臂 305 mm，前臂 255 mm）轴线偏差 8 mm、袖托压力 2.6 kPa、被动活动 15–125°、0.15 N·m 低助力 10 min ×3 任务无异常，整机佩戴部分实称 1.42 kg。
