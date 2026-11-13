# 采购与器件资料来源

查询日期：**2026-11-13**。来源网页状态详见`source_checks.json`。本次没有采购，也没有确认具体型号的库存清单；未提供原始实体测试数据。链接不是采购订单。

| 来源 | 本次实际获取情况 | 用于什么 | 价格状态 |
|---|---|---|---|
| [Pololu4692官方页](https://www.pololu.com/product/4692) | HTTP200，已读取正文与结构化报价 | 24V、30:1、330rpm/100mA空载，15kgcm/3A堵转外推；64CPR；6mmD轴/16mm长；编码器3.5–20V | 60.95USD公开单价；7.20CNY/USD是**假设汇率**，得438.84元估算，未含运费税费 |
| [Cytron MD10C官方页](https://www.cytron.io/p-md10c) | HTTP403，未核实当前产品页/价格 | Rev3驱动器候选；标称5–30V/10A等仍需到货手册确认 | BOM160元为估算 |
| [Cytron官方库](https://github.com/CytronTechnologies/CytronMotorDriver) | raw README HTTP200，已读 | 官方列MD10C为PWM_DIR兼容驱动；本项目没有复制或链接该Arduino库 | 无报价 |
| [STM32F407数据手册](https://www.st.com/resource/en/datasheet/stm32f407ve.pdf) | 本次HTTP567，未取得 | MCU选型和资源；开发板线路/电源方式须到货核对 | MCU开发板65/85/120元为渠道预算估算 |
| [AS5600官方产品](https://ams-osram.com/products/sensors/position-sensors/ams-as5600-position-sensor) | 本次SSL连接失败，旧PDF链404 | 3.3V绝对磁编码器候选；裸片/模块3.3V连接差异须复核 | 含磁铁18/35/60元为估算 |
| [INA240 TI数据手册](https://www.ti.com/lit/ds/symlink/ina240.pdf) | HTTP200，已提取PDF正文 | INA240A1增益20；2.7–5.5V供电；−4–80V共模；SOIC8引脚和半电源参考 | 采样小板/分流器38/58/85元为估算 |
| [LM339B TI数据手册](https://www.ti.com/lit/ds/symlink/lm339b.pdf) | HTTP200，已提取PDF正文 | 24V比较器供电；开集电极输出上拉3.3V；引脚与比较方向 | 计入保护板估算 |
| [SN74LVC1G74 TI数据手册](https://www.ti.com/lit/ds/symlink/sn74lvc1g74.pdf) | HTTP200，已提取PDF正文 | 异步CLR；DCU封装**pin5为Q、pin3为反相Q** | 计入保护板估算 |
| [SN74LVC2G08 TI数据手册](https://www.ti.com/lit/ds/symlink/sn74lvc2g08.pdf) | HTTP200，已提取PDF正文 | 3.3V双AND门控，引脚1/2→7、5/6→3 | 计入保护板估算 |

未核实价格的本地加工、紧固件、袖带、限位器、接触器、电源等全部明确标为`ESTIMATE`，不把渠道预算称为实时报价。三档完整逐项数量/单价在`bom.csv`。同一料号跨档价格不同表示质量/采购与装配服务预算，不表示已比较过供应商报价。

经济型约1942元、标准型约3112元、扩展型约5524元；含20%预备费约2330/3734/6629元。经济型和标准型保留同一电机、限幅和保护链，主要差别是结构加工、台架工装、仪表参考和部件渠道预算。扩展型增加参考力传感器、数据采集和备件；这些传感器不属于首版闭环支持功能。

本次没有复制数据手册PDF到公开仓库。原创电路及布线图由公式/规格自行编写，不含厂家电路图拷贝。供应商文件的版权和许可证仍由其持有人保留。
