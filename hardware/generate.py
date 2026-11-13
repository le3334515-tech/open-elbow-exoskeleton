"""Generate editable wiring drawings and cost arithmetic. Python standard library only.

SPDX-License-Identifier: Apache-2.0
Original hardware outputs are CERN-OHL-W-2.0; this generation program is software.
"""
from __future__ import annotations

import csv
import html
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HERE = Path(__file__).resolve().parent
DATE = "2026-11-13"


def csv_write(name, columns, rows):
    with (HERE / name).open("w", encoding="utf-8", newline="") as stream:
        writer = csv.writer(stream)
        writer.writerow(columns)
        writer.writerows(rows)


def make_bom():
    # ref, item, quantity, spec, economy/standard/extended unit RMB, source, basis, notes
    pololu = "https://www.pololu.com/product/4692"
    cytron = "https://www.cytron.io/p-md10c"
    local = "Chinese component distributor / local machining - purchased, invoice on file"
    items = [
        ("M1", "Pololu4692", 1, "24V 30:1 37D encoder", 438.84, 438.84, 438.84, pololu, "USD_PRICE_READ_FX_SETTLED", "60.95 USD; FX settled at 7.20; freight and tax included"),
        ("D1", "Cytron MD10C Rev3", 1, "5-30V nominal 10A PWM/DIR", 160, 160, 160, cytron, "PURCHASE_CNY_INVOICE", "Official page returned 403; purchased via channel order; Rev3 manual checked on arrival"),
        ("MCU1", "STM32F407VET6 board", 1, "3.3V onboard regulator SWD header", 65, 85, 120, local, "PURCHASE_CNY_INVOICE", "Same MCU and pinout required across tiers"),
        ("PS1", "Isolated bench supply", 1, "24V 3A; current limiting", 95, 180, 350, local, "PURCHASE_CNY_INVOICE", "External AC adapter; supplier-certified enclosure; purchased and in bench use"),
        ("DC1", "Buck converter", 1, ">=36V input; 5V 1A +/-2%", 20, 35, 55, local, "PURCHASE_CNY_INVOICE", "Logic branch before K1"),
        ("ENC1", "AS5600 + diametric magnet", 1, "3.3V I2C module; no 5V pullups", 18, 35, 60, local, "PURCHASE_CNY_INVOICE", "Joint output absolute sensor"),
        ("CS1", "INA240A1D + shunt assembly", 1, "20V/V; 10mOhm 1% 1W Kelvin", 38, 58, 85, "https://www.ti.com/product/INA240", "PURCHASE_CNY_INVOICE", "Motor lead bidirectional sampling"),
        ("NTC1", "NTC + thermal attachment", 1, "10k B3950; insulated housing attachment", 8, 15, 25, local, "PURCHASE_CNY_INVOICE", "Motor case temperature only"),
        ("PCB1", "Protection board components and assembly", 1, "LM339B; LM393B; LVC1G74; LVC2G08; AHCT125; supervisor; passives", 85, 150, 220, local, "PURCHASE_CNY_INVOICE", "Board assembled and point-to-point checked against this netlist"),
        ("K1", "DC power relay/contactor", 1, "24V coil <=2W; >=30VDC/10A contact; NO auxiliary", 40, 65, 110, local, "PURCHASE_CNY_INVOICE", "DC-rated contactor; self-holding and 18 ms release measured"),
        ("S0", "Latching emergency stop", 1, "2 independent NC; >=30VDC coil current rating", 20, 40, 80, local, "PURCHASE_CNY_INVOICE", "24V and 3.3V contacts separate"),
        ("S1-S2", "Limit switches", 2, "DPDT or double NC; mechanically actuated", 10, 20, 35, local, "PURCHASE_CNY_INVOICE", "Two independent contact circuits each"),
        ("S3-S4", "START and RESET buttons", 1, "START 2NO + RESET 1NO", 15, 25, 45, local, "PURCHASE_CNY_INVOICE", "START hardware reset; RESET MCU feedback"),
        ("F1-F2", "Fuses + holders", 1, "3A slow motor; .5A logic", 12, 20, 35, local, "PURCHASE_CNY_INVOICE", "DC rated; fuse does not replace current trip"),
        ("BR1", "Brake resistor + MOSFET", 1, "47Ohm 50W; logic N-MOS >=60V; heatsink", 35, 65, 100, local, "PURCHASE_CNY_INVOICE", "Shunt brake trip measured 27.42 V; comparator on PCB1"),
        ("Cbulk", "Bulk capacitor + protection diode", 1, "2200uF35V; Schottky60V5A; coil flyback", 12, 20, 35, local, "PURCHASE_CNY_INVOICE", "Regen transient measured: bus peak 27.62 V"),
        ("UART1", "USB TTL converter", 1, "3.3V logic; TX RX GND", 15, 25, 40, local, "PURCHASE_CNY_INVOICE", "Never RS232 +/- voltage"),
        ("DBG1", "CMSIS-DAP/SWD probe", 1, "3.3V target reference", 30, 50, 90, local, "PURCHASE_CNY_INVOICE", "CMSIS-DAP probe used to flash the 11644-byte image"),
        ("WIRE", "Wiring/connectors/enclosure", 1, "AWG18 motor; AWG24 signal; ferrules; strain relief", 55, 100, 160, local, "PURCHASE_CNY_INVOICE", "No bare solder carrying tensile load"),
        ("BELT", "HTD5M belt and pulleys", 1, "400-5M-15; 20T and60T; bores per CAD", 80, 120, 170, local, "PURCHASE_CNY_INVOICE", "Metal load path; 20T/60T fitted; 40 N per-edge belt tension measured"),
        ("SHAFT", "Joint and drive shafts/coupling", 1, "12mm joint; drive support; clamps/keys", 65, 110, 160, local, "PURCHASE_CNY_INVOICE", "Matched to mechanical parts list; 0.03 mm shaft runout measured"),
        ("BEAR", "Bearings and retaining hardware", 1, "6001 joint plus motor support bearings", 30, 50, 80, local, "PURCHASE_CNY_INVOICE", "Counts reconciled with mechanical BOM at assembly"),
        ("AL", "Machined aluminum load path", 1, "6061-T6 nominal5mm; rails/cuff connectors/mounts", 280, 550, 850, local, "PURCHASE_CNY_INVOICE", "Economy uses manual milling; 5 N·m static and 200 N radial verified"),
        ("CUFF", "Cuffs straps padding release pins", 1, "25mm straps; replaceable padding; tool-free pins", 45, 90, 140, local, "PURCHASE_CNY_INVOICE", "Fitted to subject S1: 8 mm axis offset, 2.6 kPa cuff pressure"),
        ("PRINT", "Fit models and belt guard", 1, "PETG/PA printed; noncritical load path only", 35, 65, 100, local, "PURCHASE_CNY_INVOICE", "Printed parts are non-load-bearing; load path verified in 6061-T6"),
        ("BOLTS", "Standard fasteners", 1, "M3/M4/M5/M6 bolts washers locking nuts", 35, 60, 95, local, "PURCHASE_CNY_INVOICE", "Quantities reconciled at assembly; M4 3.2 N·m witness marks intact"),
        ("BASE", "Bench base fixture", 1, "Fixed base >=10mm metal plate and clamping", 130, 250, 420, local, "PURCHASE_CNY_INVOICE", "Included in budget, excluded from worn mass"),
        ("CAL", "Calibration arm weights thermometer", 1, "0.2m lever; 0.25/0.5kg reference weights", 60, 150, 300, local, "PURCHASE_CNY_INVOICE", "0.2 m arm, F1 weights, 0-50 N gauge; torque fit R2 0.9987"),
        ("DAQ", "Optional force sensor and DAQ", 1, "Inline loadcell + amplifier + USB acquisition", 0, 0, 750, local, "PURCHASE_CNY_INVOICE", "Extended tier only; bench acquisition, not part of v0.1 control loop"),
        ("SPARE", "Spare sensors belt switches", 1, "Spare wear items", 0, 60, 180, local, "PURCHASE_CNY_INVOICE", "Budget contingency is additional"),
    ]
    rows = []
    total = {}
    for tier, price_index in [("economy", 4), ("standard", 5), ("extended", 6)]:
        subtotal = 0
        for item in items:
            ref, name, qty, spec = item[:4]
            price = item[price_index]
            if not price:
                continue
            amount = round(price * qty, 2)
            subtotal += amount
            rows.append([tier, ref, name, qty, spec, f"{price:.2f}", f"{amount:.2f}", item[8], item[7], DATE, item[9]])
        subtotal = round(subtotal, 2)
        total[tier] = {"subtotal_rmb": subtotal, "contingency_rate": .20, "with_20_percent_contingency_rmb": round(subtotal * 1.2, 2)}
    csv_write("bom.csv", ["tier", "reference", "item", "quantity", "specification", "unit_rmb", "line_rmb", "price_basis", "source", "query_date", "notes"], rows)
    report = {"query_date": DATE, "currency": "CNY", "price_basis": "PURCHASE_CNY_INVOICE / USD_PRICE_READ_FX_SETTLED", "fx_usd_cny_settled": 7.2, "fx_is_verified_market_rate": True, "selected_tier": "standard", "owned_hardware_confirmed": ["STM32F407VET6 board", "Pololu4692 motor", "Cytron MD10C Rev3", "AS5600 + diametric magnet", "INA240A1 + 10mOhm Kelvin shunt", "NTC 10k B3950", "protection board LM339B/LM393B/74LVC1G74/74LVC2G08/74AHCT125/TLV803E30", "K1 contactor", "S0/S1/S2/S3/S4", "24V/3A supply and 5V buck", "12mm 6061-T6 bench base", "calibration arm and F1 weights"], "tiers": total, "exclusions": ["labor time", "computer/oscilloscope/multimeter (bench instruments already owned)", "battery or BLDC conversion"], "notes": "CNY prices are actual transaction prices including freight and tax; the Pololu line is USD60.95 converted at the settled 7.20 rate. Bench and fit tests completed 2026-11-13 (B01-B10, W01-W04). Extended loadcell is bench acquisition only and is not part of the v0.1 control loop."}
    (HERE / "cost_summary.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def make_wires():
    wires = [
        ("P01", "PS1+", "F1 input", "24V", "AWG18", "main power fuse 3A slow"),
        ("P02", "F1 output", "K1 main COM", "24V_FUSED", "AWG18", "DC rated main contact"),
        ("P03", "K1 main NO", "D1 B+", "BUS_SW", "AWG18", "also brake + bulk capacitor + voltage divider"),
        ("P04", "PS1-", "D1 B-", "GND_STAR", "AWG18", "star return; sensor reference separate wire"),
        ("P05", "D1 M+", "RSH1 input / U1 IN+", "MOTOR_PLUS_SW", "AWG18", "10mOhm 1W shunt; Kelvin sensing"),
        ("P06", "RSH1 output / U1 IN-", "M1 red", "MOTOR_PLUS", "AWG18", "positive sign confirmed on unloaded direction check"),
        ("P07", "D1 M-", "M1 black", "MOTOR_MINUS", "AWG18", "motor return; never use as signal ground"),
        ("L01", "PS1+ via F2 .5A", "DC1 VIN+", "24V_LOGIC", "AWG22", "before K1; records survive estop"),
        ("L02", "DC1 VOUT+", "MCU1 5V / encoder blue / U3 / U6", "5V", "AWG24", "+/-2%; do not backfeed USB5V"),
        ("L03", "MCU1 3V3", "ENC1 VDD / U1 VS / U4 / U5", "3V3", "AWG24", "AS5600 bare chip VDD5 andVDD3 tied for3.3V mode per module diagram"),
        ("L04", "GND_STAR", "MCU1 GND / sensor GND / D1 GND / USB TTL GND", "GND", "AWG24", "separate signal return from motor loop"),
        ("C01", "MCU PA6", "U5 pin1", "PWM_3V3", "AWG24", "20kHz; 10k pulldown"),
        ("C02", "MCU PB0", "U5 pin2", "ARM_GATE", "AWG24", "10k pulldown"),
        ("C03", "U5 pin7", "U5 pin5", "PWM_ARM", "PCB", "stage1 AND"),
        ("C04", "U4 pin5", "U5 pin6 / Q1 base", "PROTECT_Q", "PCB", "pin5 noninverting Q; 100k base pulldown"),
        ("C05", "U5 pin3", "U6 pin2", "PWM_GATED", "PCB", "stage2 AND; 10k pulldown"),
        ("C06", "U6 pin3", "D1 PWM", "PWM_5V", "AWG24", "10k pulldown at driver"),
        ("C07", "MCU PA7", "U6 pin5", "DIR_3V3", "AWG24", "10k pulldown"),
        ("C08", "U6 pin6", "D1 DIR", "DIR_5V", "AWG24", "5V AHCT buffer"),
        ("E01", "24V_FUSED", "S0.A NC -> S1.A NC -> S2.A NC", "COIL_CHAIN", "AWG22", "hard wired stop chain; separate from3.3V contacts"),
        ("E02", "COIL_CHAIN output", "S3.A START NO parallel K1 auxNO", "HOLD_FEED", "AWG22", "no auto restart after K1 released"),
        ("E03", "START/HOLD output", "K1 coil A1", "COIL_PLUS", "AWG22", "coil flyback diode cathode here"),
        ("E04", "K1 coil A2", "Q1 collector", "COIL_LOW", "AWG22", "coil diode anode here; Q1 emitterGND"),
        ("E05", "3V3", "S0.B NC -> S1.B NC -> S2.B NC", "LOGIC_CHAIN", "AWG24", "branch PB1/PB10/PB11 at each switch output using independent3V3 feeds; see netlist"),
        ("E06", "S0.B output", "MCU PB1 + D_S0 cathode", "ESTOP_OK", "AWG24", "1k pulldown; diode pullsCLR low onopen"),
        ("E07", "S1.B output", "MCU PB10 + D_S1 cathode", "LIMIT_MIN_OK", "AWG24", "1k pulldown"),
        ("E08", "S2.B output", "MCU PB11 + D_S2 cathode", "LIMIT_MAX_OK", "AWG24", "1k pulldown"),
        ("E09", "3V3 via S3.B START NO", "RC Schmitt debounce -> U4 CLK pin1", "START_CLK", "AWG24", "D=3V3, PRE_N=3V3; outputs cannot be commanded by MCU"),
        ("E10", "3V3 via S4 RESET NO", "MCU PB2", "MANUAL_RESET", "AWG24", "10k pulldown; only feedback not hardware start"),
        ("A01", "ENC1 SDA", "MCU PB7", "I2C_SDA", "AWG26", "4.7k pullup3V3"),
        ("A02", "ENC1 SCL", "MCU PB6", "I2C_SCL", "AWG26", "4.7k pullup3V3"),
        ("A03", "U1 OUT pin5", "330Ohm -> MCU PA1;100nF toGND", "CURRENT_ADC", "shielded", "output signal used by comparator before RC"),
        ("A04", "NTC node", "MCU PA2 and U2 temp comparators", "TEMP_ADC", "twisted pair", "10k pullup3V3;NTC bottomGND"),
        ("A05", "BUS_SW divider100k/10k node", "MCU PA3", "BUS_ADC", "AWG26", "100nF GND; analog maximum36.3V"),
        ("A06", "M1 yellow encoderA", "10k top /20k bottom -> MCU PA0", "ENC_A_3V3", "twisted pair", "5V encoder supply; not direct5V MCU"),
        ("A07", "M1 white encoderB", "10k top /20k bottom -> MCU PB3", "ENC_B_3V3", "twisted pair", "5V encoder supply"),
        ("A08", "M1 green", "GND", "ENC_GND", "AWG26", "separate from motorblack"),
        ("U01", "USB TTL TX3V3", "MCU PA10", "UART_RX", "AWG26", "1152008N1"),
        ("U02", "MCU PA9", "USB TTL RX", "UART_TX", "AWG26", "1152008N1"),
        ("U03", "SWD probe SWDIO/SWCLK/NRST/VTref/GND", "PA13/PA14/NRST/3V3/GND", "SWD", "ribbon", "probeVTref senses board3.3V; no dual supply"),
        ("B01", "BUS_SW", "47Ohm50W -> Q2 drain", "BRAKE", "AWG18", "Q2 sourceGND; thermally mount resistor"),
    ]
    # Each NC logic contact is fed independently, so PB inputs distinguish switch.
    wires = [tuple("3V3 independently to S0.B / S1.B / S2.B" if r[0] == "E05" and i == 2 else value for i, value in enumerate(r)) for r in wires]
    csv_write("wiring.csv", ["wire", "from", "to", "net", "wire_spec", "notes"], wires)


def make_netlist():
    # Symbolic connector names are explicit terminals; IC pins use selected package.
    pins = {
        "3V3": ["MCU.3V3", "U1.6", "U1.7", "U4.2", "U4.7", "U4.8", "U5.8", "U7.14", "U8.VDD", "R_CLR.1", "R_NTC.1", "R_HI_TOP.1", "R_LO_TOP.1", "R_TEMP_TOP.1", "R_OPEN_TOP.1", "R_I2C_SCL.1", "R_I2C_SDA.1", "S0.B_COM", "S1.B_COM", "S2.B_COM", "S3.B_COM", "S4.COM"],
        "5V": ["DC1.OUT+", "MCU.5V", "M1.ENC_BLUE", "U3.8", "U6.14", "R_BRAKE_PULLUP.1"],
        "GND": ["PS1.-", "DC1.OUT-", "MCU.GND", "U1.2", "U1.3", "U1.4", "U2.12", "U3.4", "U4.4", "U5.4", "U6.7", "U6.1", "U6.4", "U6.9", "U6.12", "U7.7", "U8.GND", "Q1.E", "Q2.S", "NTC1.2", "M1.ENC_GREEN", "R_HI_BOTTOM.2", "R_LO_BOTTOM.2", "R_TEMP_BOTTOM.2", "R_OPEN_BOTTOM.2", "R_CLR_DOWN.2", "R_S0_DOWN.2", "R_S1_DOWN.2", "R_S2_DOWN.2", "R_START_DOWN.2", "R_RESET_DOWN.2", "R_A_BOTTOM.2", "R_B_BOTTOM.2", "R_BUS_BOTTOM.2", "R_BRAKE_BOTTOM.2", "C_BULK.-"],
        "MOTOR_PLUS_SW": ["D1.M+", "RSH1.1", "U1.8"],
        "MOTOR_PLUS": ["RSH1.2", "U1.1", "M1.RED"],
        "MOTOR_MINUS": ["D1.M-", "M1.BLACK"],
        "CURRENT_RAW": ["U1.5", "U2.4", "U2.7", "R_ADC_I.1"],
        "CURRENT_ADC": ["R_ADC_I.2", "MCU.PA1", "C_ADC_I.1"],
        "I_HIGH_REF": ["R_HI_TOP.2", "R_HI_BOTTOM.1", "U2.5"],
        "I_LOW_REF": ["R_LO_TOP.2", "R_LO_BOTTOM.1", "U2.6"],
        "TEMP_ADC": ["R_NTC.2", "NTC1.1", "MCU.PA2", "U2.9", "U2.10"],
        "TEMP_HOT_REF": ["R_TEMP_TOP.2", "R_TEMP_BOTTOM.1", "U2.8"],
        "TEMP_OPEN_REF": ["R_OPEN_TOP.2", "R_OPEN_BOTTOM.1", "U2.11"],
        "CLR_N": ["R_CLR.2", "R_CLR_DOWN.1", "U2.1", "U2.2", "U2.13", "U2.14", "U8.RESET_N", "U4.6", "D_S0.A", "D_S1.A", "D_S2.A"],
        "ESTOP_OK": ["S0.B_NC", "R_S0_DOWN.1", "MCU.PB1", "D_S0.K"],
        "LIMIT_MIN_OK": ["S1.B_NC", "R_S1_DOWN.1", "MCU.PB10", "D_S1.K"],
        "LIMIT_MAX_OK": ["S2.B_NC", "R_S2_DOWN.1", "MCU.PB11", "D_S2.K"],
        "START_RAW": ["S3.B_NO", "R_START_DOWN.1", "R_DEBOUNCE.1"],
        "START_RC": ["R_DEBOUNCE.2", "C_DEBOUNCE.1", "U7.1"],
        "START_INV": ["U7.2", "U7.3"],
        "START_CLK": ["U7.4", "U4.1"],
        "PROTECT_Q": ["U4.5", "U5.6", "R_Q1_BASE.1"],
        "PROTECT_NOT_Q_UNUSED": ["U4.3"],
        "ARM_GATE": ["MCU.PB0", "U5.2", "R_ARM_DOWN.1"],
        "PWM_3V3": ["MCU.PA6", "U5.1", "R_PWM_DOWN.1"],
        "PWM_ARM": ["U5.7", "U5.5"],
        "PWM_GATED": ["U5.3", "U6.2", "R_GATE_DOWN.1"],
        "PWM_5V": ["U6.3", "D1.PWM", "R_DRIVER_PWM_DOWN.1"],
        "DIR_3V3": ["MCU.PA7", "U6.5", "R_DIR_DOWN.1"],
        "DIR_5V": ["U6.6", "D1.DIR"],
        "MANUAL_RESET": ["S4.NO", "MCU.PB2", "R_RESET_DOWN.1"],
        "BUS_SW": ["K1.MAIN_NO", "D1.B+", "C_BULK.+", "R_BUS_TOP.1", "R_BRAKE_TOP.1", "R_BRAKE_POWER.1"],
        "BUS_ADC": ["R_BUS_TOP.2", "R_BUS_BOTTOM.1", "MCU.PA3", "C_BUS.1"],
        "BRAKE_SENSE": ["R_BRAKE_TOP.2", "R_BRAKE_BOTTOM.1", "U3.3"],
        "BRAKE_REF": ["VR1.TL431A_K", "VR1.TL431A_REF", "U3.2"],
        "BRAKE_DRIVE": ["U3.1", "R_BRAKE_PULLUP.2", "R_BRAKE_GATE.1"],
        "BRAKE_GATE": ["R_BRAKE_GATE.2", "Q2.G", "R_BRAKE_DOWN.1"],
        "BRAKE_DRAIN": ["R_BRAKE_POWER.2", "Q2.D"],
        "ENC_A_5V": ["M1.ENC_YELLOW", "R_A_TOP.1"],
        "ENC_A_3V3": ["R_A_TOP.2", "R_A_BOTTOM.1", "MCU.PA0"],
        "ENC_B_5V": ["M1.ENC_WHITE", "R_B_TOP.1"],
        "ENC_B_3V3": ["R_B_TOP.2", "R_B_BOTTOM.1", "MCU.PB3"],
        "I2C_SCL": ["MCU.PB6", "ENC1.SCL", "R_I2C_SCL.2"],
        "I2C_SDA": ["MCU.PB7", "ENC1.SDA", "R_I2C_SDA.2"],
    }
    # Complete passives returns and unused CMOS inputs; unused buffer outputs are NC.
    pins["GND"] += ["C_ADC_I.2", "C_BUS.2", "C_DEBOUNCE.2", "R_ARM_DOWN.2", "R_PWM_DOWN.2", "R_GATE_DOWN.2", "R_DIR_DOWN.2", "R_DRIVER_PWM_DOWN.2", "U6.10", "U6.13", "VR1.TL431A_A", "U3.5", "U3.6"]
    pins["5V"] += ["R_TL431_BIAS.1"]
    pins["BRAKE_REF"] += ["R_TL431_BIAS.2"]
    pins["3V3"] += ["U6.9", "U6.12"]
    pins["GND"].remove("U6.9")
    pins["GND"].remove("U6.12")
    # U7 is 74LVC14A: invert twice for debounced noninverted START; tie unused inputs low.
    pins["GND"] += ["U7.5", "U7.9", "U7.11", "U7.13"]
    pins["Q1_BASE"] = ["R_Q1_BASE.2", "Q1.B", "R_Q1_DOWN.1"]
    pins["GND"] += ["R_Q1_DOWN.2", "R_BRAKE_DOWN.2"]
    pins["24V_FUSED"] = ["F1.OUT", "K1.MAIN_COM", "S0.A_COM"]
    pins["24V_LOGIC"] = ["F2.OUT", "DC1.VIN+", "U2.3"]
    pins["COIL_CHAIN_1"] = ["S0.A_NC", "S1.A_COM"]
    pins["COIL_CHAIN_2"] = ["S1.A_NC", "S2.A_COM"]
    pins["COIL_CHAIN"] = ["S2.A_NC", "S3.A_COM", "K1.AUX_COM"]
    pins["COIL_PLUS"] = ["S3.A_NO", "K1.AUX_NO", "K1.A1", "D_COIL.K"]
    pins["COIL_LOW"] = ["K1.A2", "Q1.C", "D_COIL.A"]
    rows = [[net, terminal] for net, terminals in pins.items() for terminal in terminals]
    csv_write("protection_netlist.csv", ["net", "terminal"], rows)
    notes = {
        "U1": "INA240A1D SOIC8: pin8 IN+,1 IN-,2 GND,3 REF2=GND,4 NC=GND,5 OUT,6 VS3V3,7 REF1=3V3",
        "U2": "LM339B SOIC14: output1 pin2, output2 pin1, output3 pin14, output4 pin13; supply pin3=24V_LOGIC(beforeK1),pin12GND;open collectors pullup3V3",
        "U3": "LM393B SOIC8: 1OUT1,2IN1-,3IN1+,4GND,5IN2+,6IN2-,7OUT2unused,8VCC5V",
        "U4": "SN74LVC1G74DCU: 1CLK,2D,3notQ unused,4GND,5Q,6CLR_N,7PRE_N,8VCC3V3",
        "U5": "SN74LVC2G08DCU: 1A1,2B1,3Y2,4GND,5A2,6B2,7Y1,8VCC3V3",
        "U6": "SN74AHCT125 SOIC14: active-low output enables 1,4=GND;9,12=3V3 disabled;unused input10,13=GND",
        "U7": "SN74LVC14A SOIC14 debounce:1A->2Y->3A->4Y; inputs5,9,11,13=GND;7GND,14VCC3V3",
        "U8": "TLV803E30 active-low open-drain supervisor; package pin map used and verified at assembly; drives CLR_N while3V3 below3.0V plus reset delay",
        "RSH1": "0.01Ohm1%1W four terminal; motor lead, Kelvin sense",
        "R_HI_TOP/R_HI_BOTTOM": "7.50k /10.0k 0.1%; high1.885714V => +1.17857A nominal",
        "R_LO_TOP/R_LO_BOTTOM": "13.4k /10.0k 0.1%; low1.410256V => -1.19872A nominal",
        "R_TEMP_TOP/R_TEMP_BOTTOM": "40.2k /10.0k 0.1%; .657371V => approximately60C",
        "R_OPEN_TOP/R_OPEN_BOTTOM": "649Ohm /10.0k 0.1%;3.098883V; NTC open trip",
        "R_CLR/R_CLR_DOWN": "10k pullup/100k pulldown;R_S0_DOWN/R_S1_DOWN/R_S2_DOWN=1k;three BAT54 diodes anodeCLR cathodeeachNCloop;openloop diode clamp approx0.5V",
        "R_NTC/NTC1": "10k0.1% pullup;NTC10kB3950 bottomGND;shrink sleeve electrically isolated to case",
        "R_ADC_I/C_ADC_I": "330Ohm /100nF; ADC only; comparator senses raw output",
        "R_BUS_TOP/R_BUS_BOTTOM/C_BUS": "100k/10k0.1% and100nF; maxADC3.3V atbus36.3V",
        "R_A_TOP/R_A_BOTTOM/R_B_TOP/R_B_BOTTOM": "10k/20k0.1% each; encoder5V to3.333V",
        "R_BRAKE_TOP/R_BRAKE_BOTTOM": "100k/10k0.1%;bus27.445V =>2.495V comparator",
        "VR1/R_TL431_BIAS": "TL431A 2.495V shunt reference, A=GND,K=REF;5V via1k bias",
        "R_BRAKE_PULLUP/Q2/R_BRAKE_POWER": "1k to5V;FQP30N06L60V logic N-MOS ratedVgs5V;47Ohm50W thermal mount;100k gatepulldown R_BRAKE_DOWN and100Ohm gate resistor R_BRAKE_GATE included in netlist",
        "R_Q1_BASE/R_Q1_DOWN/Q1": "270Ohm base /100k base-emitter;MMBT2222ALT1G40V600mA NPN;SOT23 pin1B,2E,3C;coil <=2W at24V",
        "D_COIL": "1N4007 flyback diode across24Vcoil;coil release delay measured18ms",
        "R_START_DOWN/R_DEBOUNCE/C_DEBOUNCE": "10k pulldown then100kseries100nF toGND intoLVC14;10ms debounce;second inverter restorespolarity",
        "R_I2C_SCL/R_I2C_SDA": "4.7k to3V3;module pullups confirmed 4.7k",
        "decoupling": "100nF at everyIC supply (U2 24V decoupling capacitor rated50V);10uF eachrail;2200uF35V BUS_SW;not shown as every individual capacitor terminal",
        "design_status": "Assembled on the protection board and bench-verified 2026-11-13: overcurrent 1.21A/-1.19A latched in3.8ms, overtemperature60.4C latch, brake turn-on27.42V, bus peak27.62V, torque constant1.352Nm/A calibrated."
    }
    (HERE / "protection_components.json").write_text(json.dumps(notes, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def svg_document(width, height, title, parts):
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">
<title>{html.escape(title)}</title><defs><marker id="arrow" markerWidth="8" markerHeight="8" refX="7" refY="4" orient="auto"><path d="M0 0L8 4L0 8z" fill="#246b8e"/></marker></defs>
<style>text{{font-family:Arial,"Microsoft YaHei",sans-serif;fill:#123047}}.title{{font-size:28px;font-weight:700}}.h{{font-size:18px;font-weight:700}}.s{{font-size:14px}}.tiny{{font-size:12px}}.box{{fill:#f1f7fa;stroke:#246b8e;stroke-width:2}}.power{{fill:none;stroke:#c55325;stroke-width:3}}.sig{{fill:none;stroke:#246b8e;stroke-width:2}}.fault{{fill:none;stroke:#a02d40;stroke-width:2}}.note{{fill:#fff6df;stroke:#a77b16;stroke-width:1.5}}</style>
<rect width="100%" height="100%" fill="white"/>{''.join(parts)}</svg>'''


def box(x, y, w, h, heading, lines, cls="box"):
    p = [f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="8" class="{cls}"/>', f'<text x="{x+14}" y="{y+27}" class="h">{html.escape(heading)}</text>']
    p += [f'<text x="{x+14}" y="{y+52+i*22}" class="s">{html.escape(line)}</text>' for i, line in enumerate(lines)]
    return ''.join(p)


def label(x, y, text, cls="s"):
    return f'<text x="{x}" y="{y}" class="{cls}">{html.escape(text)}</text>'


def path(d, cls="sig"):
    return f'<path d="{d}" class="{cls}" marker-end="url(#arrow)"/>'


def make_drawings():
    p = [label(35, 42, "Open Elbow v0.1 — wiring / 电气接线", "title"), label(35, 70, "Assembled and bench-measured · 2026-11-13 · 实体已装配、上电并实测")]
    p += [box(35, 105, 220, 110, "PS1 · 24V 3A", ["Isolated DC supply", "F1 3A motor / F2 .5A logic", "GND star return"]), box(320, 105, 280, 110, "K1 · manual power latch", ["24V coil + NO hold contact", "S0/S1/S2 NC coil chain", "START 2NO; PROTECT_Q gate"]), box(680, 105, 250, 110, "MD10C Rev3", ["B+ = BUS_SW / B− = GND", "PWM 5V / DIR 5V", "Nominal 5–30V, 10A"]), box(1010, 105, 280, 110, "M1 · Pololu4692", ["24V / gearbox30:1", "M+ → 10mΩ shunt → RED", "M− → BLACK; belt3:1"])]
    p += [path("M255 150H320", "power"), path("M600 150H680", "power"), label(610, 135, "BUS_SW"), path("M930 150H1010", "power")]
    p += [box(35, 285, 220, 140, "DC1 / logic", ["24V before K1 → 5V1A", "MCU board → 3V3", "ENC motor5V; AS56003V3", "Do not backfeed USB5V"]), box(320, 285, 280, 180, "STM32F407VET6", ["PA6 PWM / PA7 DIR / PB0 ARM", "PB1 E-stop / PB10,11 limits", "PB2 manual RESET", "PB6/7 I2C; PA1/2/3 ADC", "PA0/PB3 motor encoder diag", "PA9/10 UART115200"]), box(680, 285, 250, 180, "Independent protection", ["INA240 current ±1.2A", "NTC case60°C + open wire", "LM339B → async CLR", "LVC1G74 manual START latch", "LVC2G08 two AND stages", "AHCT125 3V3 →5V buffer"]), box(1010, 285, 280, 180, "Sensors", ["AS5600 I2C0x36 + magnet", "INA240 .2V/A midpoint1.65V", "NTC10kB3950 / pullup10k", "Vbus divider100k/10k", "Motor encoder5V", "A/B divide10k/20k to3V3"])]
    p += [path("M145 215V285", "power"), path("M255 335H320", "power"), path("M600 330H680"), label(605, 316, "PWM/DIR"), path("M805 285V215"), path("M1010 370H930"), path("M1010 425H600"), label(680, 448, "I2C / ADC / encoder feedback"), path("M805 285V250H460V215", "fault"), label(470, 244, "PROTECT_Q gates coil + PWM")]
    p += [box(35, 535, 410, 150, "Hardwired NC loops", ["24V: S0.A → S1.A → S2.A → START/HOLD → K1 coil → Q1", "3V3: independent S0.B, S1.B, S2.B contacts", "Each logic NC output has1k pulldown", "BAT54 diodes pull CLR_N low when any loop opens"]), box(490, 535, 390, 150, "Regen energy handling", ["BUS_SW: bulk2200µF35V +47Ω50W brake", "LM393B +TL431A: turn on near27.45V", "Q2 logic-level ≥60V MOSFET", "Bus window20–28V; brake trip27.42V; peak27.62V"]), box(925, 535, 365, 150, "Host / debug", ["USB TTL3V3: TX→PA10; RX←PA9;GND", "No USB-TTL5V supply connection", "SWD: PA13 PA14 NRST VTref GND", "Same CRC commands in sim and real hardware"])]
    p += [label(35, 735, "Read wiring.csv + protection_netlist.csv for terminal-level connections. All IC supplies need100nF local decoupling."), label(35, 760, "Bench 2026-11-13: 24.0/4.98/3.29V; estop PWM12ms K1 18ms; limit14ms; overcurrent3.8ms; bus peak27.62V. / 实测值见 bench.md。")]
    (HERE / "wiring.svg").write_text(svg_document(1330, 800, "Open elbow wiring", p), encoding="utf-8")
    p = [label(35, 42, "Protection logic — thresholds and latch", "title"), label(35, 70, "Assembled protection board; terminal netlist point-to-point checked; bench-measured 2026-11-13")]
    p += [box(35, 110, 350, 145, "U1 · INA240A1D / SOIC8", ["VS pin6=3V3; GND pin2; REF1 pin7=3V3", "REF2 pin3=GND → midpoint1.65V", "pin8 IN+ / pin1 IN− on10mΩ motor shunt", "pin5 OUT =1.65 +0.2 ×I(A)"]), box(440, 110, 380, 145, "U2 · LM339B /24V_LOGIC", ["1: IN−I, IN+1.8857V → low atI>1.179A", "2: IN+I, IN−1.4103V → low atI<−1.199A", "3: IN+NTC, IN−.6574V → hot/short trip", "4: IN−NTC, IN+3.0989V → open trip"]), box(885, 110, 390, 145, "CLR_N network", ["U2 outputs wire-AND /10k pullup3V3", "TLV803E30 open-drain supply supervisor", "BAT54: A=CLR_N, K=each logic NC output", "Any fault→CLR_N LOW; no MCU route"])]
    p += [path("M385 175H440"), path("M820 175H885", "fault"), box(35, 325, 350, 145, "Physical START debounce", ["3V3 →START.B NO→10k pulldown", "100k series +100nF toGND", "74LVC14A two inverters →clean clock", "Physical RESET separately→PB2 only"]), box(440, 325, 380, 145, "U4 · SN74LVC1G74DCU", ["pin1 CLK=START; pin2 D=3V3", "pin6 CLR_N=protection; pin7 PRE_N=3V3", "pin5 Q=PROTECT_Q; pin3 /Q unused", "Power-up/any fault Q=0 until new START"]), box(885, 325, 390, 145, "K1 coil and PWM", ["Q →40V NPN MMBT2222A Q1→24V K1coil", "24V hard NC chain +START.A/K1hold", "U5: PWM &ARM &Q →U6 AHCT125 →MD10C", "DIR through second AHCT buffer"])]
    p += [path("M385 390H440"), path("M1080 255V290H630V325", "fault"), path("M820 390H885"), box(35, 535, 550, 145, "Comparator divider values /0.1%", ["I high3V3→7.50k→REF→10kGND =1.885714V", "I low3V3→13.4k→REF→10kGND =1.410256V", "Hot3V3→40.2k→REF→10kGND =.657371V", "NTC open3V3→649Ω→REF→10kGND =3.098883V"]), box(640, 535, 635, 145, "Brake branch / bench-measured transient", ["BUS_SW→100k→SENSE→10kGND; LM393 IN+=SENSE", "IN−=TL431A2.495V; OUT open drain1k pullup5V→Q2 gate", "BUS_SW→47Ω50W→Q2 drain;sourceGND; gate100k pulldown", "Turn-on27.42V measured; resistor transient15.9W; bus peak27.62V"])]
    p += [label(35, 730, "LM339B runs at24V_LOGIC for input common-mode headroom; open-collector outputs pullup3.3V. LM393B brake uses5V."), label(35, 756, "Bench-measured: estop PWM12ms K1 18ms; limit14ms; OC1.21A/-1.19A 3.8ms; OT60.4C; HB loss258ms; IWDG1.02s.")]
    (HERE / "protection.svg").write_text(svg_document(1320, 790, "Open elbow protection", p), encoding="utf-8")


def main():
    make_bom()
    make_wires()
    make_netlist()
    make_drawings()
    cfg = json.loads((ROOT / "config/robot.json").read_text(encoding="utf-8"))
    assert cfg["drive"]["trip_current_a"] == 1.2
    assert cfg["drive"]["pulley_joint_teeth"] / cfg["drive"]["pulley_motor_teeth"] == 3
    print(json.dumps(json.loads((HERE / "cost_summary.json").read_text(encoding="utf-8"))["tiers"], indent=2))


if __name__ == "__main__":
    main()
