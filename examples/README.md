# 可直接运行的示例

1. `python -m elbow_exo demo --output artifacts/demo`：无硬件全流程，保存CSV/JSON/PNG/SVG。
2. `python -m elbow_exo console --port sim`：按照[sim_session.txt](sim_session.txt)手工输入，支持故障/复位观察。
3. `python -m elbow_exo gui --port sim`：带状态和实时曲线的台架控制界面。
4. `python simulation/validate.py --output artifacts/simulation`：轨迹与7故障场景。
5. 双击打开[交互运动学展示](../docs/demo.html)：离线查看关节角、限位和尺寸。该页面是运动学示意，不是实物画面或动力学仿真记录。

先按根README安装依赖并编译host_sim。示例默认保持物理台架未连接；实体端口用COMx或/dev/ttyUSBx替换，详见操作文档。
