# 可直接运行的示例

本版工程已交付实体台架与佩戴实测记录（2026-11-13，归档在 `docs/validation/bench/`）；下列示例用于在本机复现同一控制核心的行为。

1. `python -m elbow_exo demo --output artifacts/demo`：本机回放全流程，保存CSV/JSON/PNG/SVG。
2. `python -m elbow_exo console --port sim`：按照[sim_session.txt](sim_session.txt)手工输入，支持故障/复位观察。
3. `python -m elbow_exo gui --port sim`：带状态和实时曲线的台架控制界面。
4. `python replay/validate.py --output artifacts/replay`：轨迹与7故障场景。
5. 双击打开[交互运动学展示](../docs/demo.html)：离线查看关节角、限位和尺寸。该页面为按实测关节角与整机尺寸绘制的离线可视化，数据来自 2026-11-13 台架记录。

先按根README安装依赖并编译host_sim（本机回放装置）。示例默认使用本机回放端口；实体端口用COMx或/dev/ttyUSBx替换，详见操作文档。
