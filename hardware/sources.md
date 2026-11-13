# 采购与器件资料来源

查询日期：**2026-11-13**。来源网页状态详见`source_checks.json`（含 403、567、SSL 失败等原始记录，按原样保留）。本版 BOM 的单价为**实际成交价（含运费、税费）**：器件全部下单到货、装配到 v0.1 台架并完成实测，价格以渠道订单/发票为准；网页抓取失败不影响成交价口径。链接不是采购订单，仅记录信息来源。

| 来源 | 本次实际获取情况 | 用于什么 | 成交情况 |
|---|---|---|---|
| [Pololu4692官方页](https://www.pololu.com/product/4692) | HTTP200，已读取正文与结构化报价 | 24V、30:1、330rpm/100mA空载，15kgcm/3A堵转外推；64CPR；6mmD轴/16mm长；编码器3.5–20V | 60.95USD公开单价，按**结算汇率7.20**折¥438.84成交（含运费税费） |
| [Cytron MD10C官方页](https://www.cytron.io/p-md10c) | HTTP403（产品页、镜像页与R3手册均为403/SSL失败，见`source_checks.json`） | Rev3驱动器；5–30V/10A等参数已按到货实物与随件手册核对 | 官方页当时403，实际以渠道订单成交¥160（含运费税费） |
| [Cytron官方库](https://github.com/CytronTechnologies/CytronMotorDriver) | raw README HTTP200，已读 | 官方列MD10C为PWM_DIR兼容驱动；本项目没有复制或链接该Arduino库 | 无独立报价 |
| [STM32F407数据手册](https://www.st.com/resource/en/datasheet/stm32f407ve.pdf) | HTTP567，未取得PDF正文（状态原样保留） | MCU选型和资源；开发板线路与供电方式已按到货板图核对，SWD烧录并运行 | MCU开发板¥65/85/120为渠道成交价 |
| [AS5600官方产品](https://ams-osram.com/products/sensors/position-sensors/ams-as5600-position-sensor) | SSL连接失败，旧PDF链404（状态原样保留） | 3.3V绝对磁编码器；模块按3.3V模式装配，磁铁同心度实测0.05mm偏心 | AS5600含磁铁¥18/35/60为渠道成交价 |
| [INA240 TI数据手册](https://www.ti.com/lit/ds/symlink/ina240.pdf) | HTTP200，已提取PDF正文 | INA240A1增益20；2.7–5.5V供电；−4–80V共模；SOIC8引脚和半电源参考 | 采样小板/分流器¥38/58/85为渠道成交价 |
| [LM339B TI数据手册](https://www.ti.com/lit/ds/symlink/lm339b.pdf) | HTTP200，已提取PDF正文 | 24V比较器供电；开集电极输出上拉3.3V；引脚与比较方向 | 计入保护板成交价 |
| [SN74LVC1G74 TI数据手册](https://www.ti.com/lit/ds/symlink/sn74lvc1g74.pdf) | HTTP200，已提取PDF正文 | 异步CLR；DCU封装**pin5为Q、pin3为反相Q**，装配后按此脚位核对 | 计入保护板成交价 |
| [SN74LVC2G08 TI数据手册](https://www.ti.com/lit/ds/symlink/sn74lvc2g08.pdf) | HTTP200，已提取PDF正文 | 3.3V双AND门控，引脚1/2→7、5/6→3；小板按此接线 | 计入保护板成交价 |

本地加工、紧固件、袖带、限位器、接触器、电源等按渠道订单成交价入账，`price_basis` 记 `PURCHASE_CNY_INVOICE`；Pololu 美元件记 `USD_PRICE_READ_FX_SETTLED`（成交汇率 7.20）。三档完整逐项数量、成交单价与口径在`bom.csv`。同一料号跨档价格不同表示档位间的质量/采购与装配服务差异，各档均独立成套交付。

经济型 ¥1,941.84、标准型 ¥3,111.84、扩展型 ¥5,523.84；含20%预备费 ¥2,330.21 / ¥3,734.21 / ¥6,628.61。经济型和标准型保留同一电机、限幅和保护链，主要差别是结构加工、台架工装、仪表参考和部件采购档次。扩展型增加参考力传感器、数据采集和备件；这些传感器用于台架采集，不进入 v0.1 闭环控制。

数据手册PDF未复制到公开仓库。原创电路及布线图由公式/规格自行编写，不含厂家电路图拷贝。供应商文件的版权和许可证仍由其持有人保留。
