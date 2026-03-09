# ENVIRO_DL STM32 — User Guide

**Product:** ENVIRO_DL Environmental Data Logger
**Platform:** STM32F417 (ARM Cortex-M4)
**Firmware:** ENVIRO_DL_STM32F
**Manufacturer:** EIPL (Envirotech Instruments Pvt. Ltd.)

---

## Table of Contents

1. [System Overview](#1-system-overview)
2. [Hardware Description](#2-hardware-description)
3. [Getting Started](#3-getting-started)
4. [Front Panel Operation](#4-front-panel-operation)
5. [LCD Display Pages](#5-lcd-display-pages)
6. [Sensor Suite](#6-sensor-suite)
7. [Data Logging](#7-data-logging)
8. [Configuration](#8-configuration)
9. [Communication Interfaces](#9-communication-interfaces)
10. [Terminal Command Reference](#10-terminal-command-reference)
11. [Remote Data Upload](#11-remote-data-upload)
12. [Firmware Over-the-Air (FOTA) Update](#12-firmware-over-the-air-fota-update)
13. [LED Status Indicator](#13-led-status-indicator)
14. [Fault Codes & Troubleshooting](#14-fault-codes--troubleshooting)
15. [SD Card File Reference](#15-sd-card-file-reference)
16. [Technical Specifications](#16-technical-specifications)
17. [Known Limitations](#17-known-limitations)

---

## 1. System Overview

The **ENVIRO_DL** is a rugged, embedded environmental data logger designed for continuous outdoor monitoring. It measures a comprehensive set of meteorological parameters, stores readings locally on an SD card, and transmits data to a remote server via an integrated LTE modem.

### Key Capabilities

- Measures temperature, humidity, pressure, wind speed/direction, rainfall, and solar radiation
- Logs data to an SD card in daily CSV files at a configurable interval (default: every 5 minutes)
- Uploads data to a remote server over LTE (HTTP POST), configurable upload period
- Displays live readings and system status on a 128×64 graphical LCD
- Accepts configuration and commands via USB (virtual COM port) or UART terminal
- Supports Firmware Over-the-Air (FOTA) updates with automatic rollback on failure
- Maintains time across power loss using an external battery-backed RTC (MCP7940)
- Runs FreeRTOS with multiple concurrent tasks for reliable, real-time operation

---

## 2. Hardware Description

### Block Diagram

```
 ┌──────────────────────────────────────────────────────────────────┐
 │                        STM32F417 MCU                            │
 │                                                                  │
 │  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌───────────────┐   │
 │  │SensorTask│  │UploadTask│  │ CmdTask  │  │ KeyboardTask  │   │
 │  └────┬─────┘  └────┬─────┘  └────┬─────┘  └──────┬────────┘   │
 │       │              │              │                │            │
 └───────┼──────────────┼──────────────┼────────────────┼───────────┘
         │              │              │                │
    ┌────▼────┐    ┌────▼────┐   ┌────▼────┐   ┌───────▼───────┐
    │ Sensors │    │LTE Modem│   │USB / UART│  │Keypad + Pulses│
    │I2C/UART │    │(Quectel)│   │(Terminal)│  │Front Panel    │
    └─────────┘    └─────────┘   └──────────┘  └───────────────┘
         │
    ┌────▼──────────────────────────────────────────────────┐
    │  NAU7802 (Temp) | ADS112C04 (Hum/P/Solar/WindDir)    │
    │  RS485 Wind Sensor | SHT25/45/BMP280 | Rain Gauge    │
    └───────────────────────────────────────────────────────┘
```

### Connectors & Ports

| Port | Type | Function |
|------|------|----------|
| USB | USB-B / Micro-USB | Virtual COM port (CDC) for terminal commands & debug |
| UART1 | RS-232 / TTL header | Quectel LTE modem; also alternate terminal interface |
| UART2 / RS485 | 2-wire RS485 | Wind speed sensor (Modbus RTU or Gill ASCII) |
| I2C (Internal) | PCB traces | NAU7802, ADS112C04, SHT25/45, BMP280, MCP7940 RTC |
| SD Card | MicroSD slot | Data logging, configuration, FOTA firmware staging |
| Rain Gauge | 2-pin screw terminal | Tipping bucket pulse input (PG7) |
| LCD | On-board ribbon | 128×64 GLCD display |
| Keypad | On-board or header | 6-button navigation (Up/Down/Left/Right/ESC/Enter) |
| SIM Card | SIM slot (modem) | LTE SIM for data connectivity |
| LED | On-board | Green/Red status indicator (PG4) |

---

## 3. Getting Started

### 3.1 Prerequisites

Before powering on, ensure:

1. **SD card inserted** — FAT32 formatted, minimum 1 GB recommended
2. **SIM card installed** in the LTE modem slot (if remote upload is required)
3. **Sensors connected** per the wiring diagram (rain gauge, wind sensor, analog sensors)
4. **Antenna attached** to the LTE modem SMA connector

### 3.2 First Power-On

1. Apply 5–12 V DC power to the unit
2. The LCD will display the **Envirotech splash screen** for approximately 5 seconds
3. The system will:
   - Synchronize time from the external RTC (MCP7940) if previously set
   - Mount the SD card and load `config.bin`, `nvdata.bin`
   - Initialize all sensors and verify communication
   - Start the FreeRTOS tasks (sensor reading, upload, UI, command)
4. The STATUS LED will begin **blinking at 1 Hz** to indicate healthy operation
5. The LCD will transition to the **status dashboard** (Page 0)

### 3.3 Initial Configuration (Required)

Connect via USB (see [Section 9.1](#91-usb-cdc-virtual-com-port)). All writable configuration is done through the **C02** system config command. Changes are saved to the SD card automatically when the command is accepted.

Set station identity:
```
(?eipl,C02,000000,sid=AWS_ROOF&lkey=SITE01?)
```

Set the primary server IP:
```
(?eipl,C02,000000,sip1=192.168.1.100?)
```

Set the current date and time (format: YYMMDDHHmm, 10 digits):
```
(?eipl,C02,000000,rtc=2603091030?)
```

Read back station info to confirm:
```
(?eipl,C01,000000,?)
```

After configuration, the unit will begin logging and uploading automatically.

---

## 4. Front Panel Operation

### 4.1 Button Functions

| Button | Short Press | Long Press |
|--------|-------------|------------|
| **Up** | Previous LCD page | — |
| **Down** | Next LCD page | — |
| **Left** | Previous item / Decrease value | — |
| **Right** | Next item / Increase value | — |
| **Enter** | Confirm selection | Enter configuration menu |
| **ESC** | Cancel / Exit menu | Return to main dashboard |

### 4.2 Navigation Flow

```
Page 0: Status Bar
   ↕ (Up/Down)
Page 1: Temperature & Humidity
   ↕
Page 2: Wind Speed & Direction
   ↕
Page 3: Rainfall & Solar Radiation
   ↕
Page 4: Uplink Counters
   ↕
Page 5: FOTA Progress (only during update)
```

---

## 5. LCD Display Pages

### Page 0 — System Status Bar

```
 [ANT] GSM:▌▌▌  Bat:12.3V
 2026-03-09  10:25:00
 SD:OK  MOD:OK  RTC:OK
```

| Symbol | Meaning |
|--------|---------|
| `[ANT]` | Antenna / LTE connected |
| `GSM:▌▌▌` | Signal strength (1–5 bars) |
| `Bat:12.3V` | Battery/supply voltage |
| `SD:OK` | SD card healthy |
| `MOD:OK` | LTE modem responding |
| `RTC:OK` | Real-time clock healthy |

### Page 1 — Temperature & Humidity

```
 Temp:  25.3 °C
 Hum:   64.5 %RH
 DewPt: 17.9 °C
 Press: 1013.2 mbar
```

### Page 2 — Wind

```
 Wind Spd:  3.2 m/s
 Wind Dir:  NNE (025°)
 Gust:      5.1 m/s
 Avg(5min): 2.9 m/s
```

### Page 3 — Rainfall & Solar

```
 Rain Today: 12.50 mm
 Rain/Hour:   2.00 mm
 Solar:      450 W/m²
```

### Page 4 — Upload Counters

```
 Uploads Attempted: 145
 Uploads Success:   143
 Last Upload: 10:20:00
 Next Upload: 10:25:00
```

### Page 5 — FOTA Progress (during update only)

```
 FOTA Update in Progress
 [##########          ] 52%
 Downloading firmware...
 DO NOT POWER OFF
```

---

## 6. Sensor Suite

### 6.1 Temperature — NAU7802 + PT1000 RTD

- **Type:** PT1000 resistance temperature detector (RTD)
- **Interface:** I2C, address 0x54
- **Resolution:** 24-bit ADC
- **Accuracy:** ±0.3 °C (sensor dependent)
- **Conversion:** Callendar-Van Dusen polynomial
- **Output channels:** ch2 (primary temperature)

### 6.2 Humidity, Pressure, Solar Radiation, Wind Direction — ADS112C04

- **Type:** 24-bit multi-channel ADC (Texas Instruments ADS112C04)
- **Interface:** I2C
- **Channels used:**

| ADC Channel | Parameter | Unit |
|-------------|-----------|------|
| Ch0 | Relative Humidity | %RH |
| Ch1 | Atmospheric Pressure | mbar |
| Ch3 | Solar Radiation | W/m² |
| Ch4 | Wind Direction (voltage) | degrees |

- **Reference voltage:** Internal 2.048 V or external
- **Calibration:** Gain and offset configurable via C02 command

### 6.3 Wind Speed — RS485 Sensor

- **Interface:** UART2 via RS485 transceiver
- **Supported protocols:**

| Protocol | Sensor Brand | Baud Rate | Format |
|----------|--------------|-----------|--------|
| Modbus RTU | RENKEE | 9600 8N1 | Register query |
| ASCII (Gill) | Gill Instruments | Configurable | `"w?\r\n"` query |

- **Sample rate:** Approximately once per second
- **Computed values:** Minimum, maximum, and average wind speed over the snap interval; gust speed
- **Squall detection:** WMO-standard state machine; triggers on >25% speed increase

### 6.4 Rainfall — Tipping Bucket Gauge

- **Interface:** GPIO falling-edge pulse on pin PG7
- **Debounce:** Software debounce — pulse is confirmed by re-reading the pin 20 ms later
- **Default resolution:** 0.5 mm per tip (configurable via `rain_mm_per_tick`)
- **Accumulators:**
  - `rain_inday` — resets at midnight (or configured reset hour)
  - `rain_inhour` — resets after each upload period
- **Persistence:** Rain counts are saved to SD card (`nvdata.bin`) and survive power loss

### 6.5 Secondary T/H/P — SHT25 / SHT45 / BMP280

- **Purpose:** Secondary/redundant temperature, humidity, and pressure measurement
- **Interface:** I2C
  - SHT25: 0x40
  - SHT45: 0x44
  - BMP280: 0x76
- **Sensor type selected at firmware compile time**
- **User-configurable offsets** applied to all readings (see C09 command)

### 6.6 Dew Point (Computed)

Dew point is computed automatically from temperature and relative humidity using the Magnus formula. It is not a separate sensor and is not currently included as a named channel in the upload packet or CSV log. It is displayed locally on the LCD.

---

## 7. Data Logging

### 7.1 Log File Format

Data is written to the SD card as daily **CSV files** in URL query-string format:

**Filename:** `DDMMYY.csv`
Example: `090326.csv` = 9 March 2026

**Each log line (one per snap interval):**
```
000001&locationkey=SITE01&stationkey=AWS_ROOF&datetime=1741513500&ch1=26.50&ch2=25.30&ch3=24.10&ch4=65.20&ch5=64.50&ch6=63.80&ch7=450.0&ch8=1013.2&ch9=025&ch10=4.80&ch11=3.20&ch12=2.50&ch13=12.50&ch14=12.3
```

### 7.2 Channel Reference

The upload packet and CSV log use the following fixed channel assignments:

| Channel | Parameter | Unit | Source |
|---------|-----------|------|--------|
| ch1 | Temperature Maximum (AT_Max) | °C* | PT1000/NAU7802, MMA over snap interval |
| ch2 | Temperature Average (AT_Avg) | °C* | PT1000/NAU7802, MMA over snap interval |
| ch3 | Temperature Minimum (AT_Min) | °C* | PT1000/NAU7802, MMA over snap interval |
| ch4 | Humidity Maximum (RH_Max) | %RH | ADS112C04, MMA over snap interval |
| ch5 | Humidity Average (RH_Avg) | %RH | ADS112C04, MMA over snap interval |
| ch6 | Humidity Minimum (RH_Min) | %RH | ADS112C04, MMA over snap interval |
| ch7 | Solar Radiation (instantaneous) | W/m²* | ADS112C04, last reading at snap |
| ch8 | Barometric Pressure | mbar* | ADS112C04 / BMP280, last reading at snap |
| ch9 | Wind Direction | degrees | RS485 sensor, last reading at snap |
| ch10 | Wind Speed Maximum (WS_Max) | m/s* | RS485 sensor, MMA over snap interval |
| ch11 | Wind Speed Average (WS_Avg) | m/s* | RS485 sensor, MMA over snap interval |
| ch12 | Wind Speed Minimum (WS_Min) | m/s* | RS485 sensor, MMA over snap interval |
| ch13 | Daily Rainfall | mm | Tipping bucket, accumulated since midnight |
| ch14 | Battery / Supply Voltage | V | Always included |

> \* Unit conversion applies if configured. See [Section 8.4](#84-unit-conversion).
> Channels for disabled sensors are omitted from the packet (not sent as zero).

### 7.3 Snap Interval

The **snap interval** defines how often a line is written to the log file and how often data is uploaded. Default: **5 minutes**.

- Configurable from 1 to 1440 minutes
- At each snap, the system computes min/max/average over all readings collected since the last snap
- Rain accumulator reflects all tips since the start of the current day

### 7.4 Min/Max/Average Computation

Within each snap interval the firmware continuously accumulates:
- Temperature, humidity, pressure, solar: simple running average
- Wind speed: separate min, max, average (1 sample per second)
- Wind gust: peak instantaneous speed, with timestamp and direction

All accumulators reset at the start of each new snap window.

---

## 8. Configuration

Configuration is stored in binary files on the SD card and loaded at boot. Changes made via C02 and C03 are **saved to SD card automatically** — no separate save command is needed.

### 8.1 Station Info — Read Only (C01)

C01 is a **read-only** status report. Send it without parameters to retrieve the current station ID, firmware version, signal level, and fault code:

```
(?eipl,C01,000000,?)
```

**Response fields:**

| Field | Description |
|-------|-------------|
| `SID` | Station/site ID |
| `T` | Current date-time (YYMMDDHHmm) |
| `DID` | Device ID |
| `FW` | Firmware version string |
| `Q` | GSM signal / BER |
| `F` | Fault bitmask (see Section 14.1) |

### 8.2 System Configuration — Read / Write (C02)

C02 is the main configuration command. Send one or more `key=value` pairs in a single packet. Changes are saved automatically.

| Parameter | Description | Example |
|-----------|-------------|---------|
| `sid` | Station/site ID (3–9 chars) | `sid=AWS_ROOF` |
| `lkey` | Location key (1–6 chars) | `lkey=SITE01` |
| `mpm` | Snap interval in minutes (1–1440) | `mpm=5` |
| `upm` | Upload period in minutes (1–1440) | `upm=5` |
| `sip1` | Primary server IP address | `sip1=192.168.1.100` |
| `sip2` | Secondary server IP address | `sip2=192.168.1.101` |
| `rtc` | Set RTC date/time (YYMMDDHHmm, 10 digits) | `rtc=2603091030` |
| `drh` | Daily rain reset hour (0–2350, HHMM) | `drh=0` |
| `rt` | Rain gauge tick value in mm (e.g. 0.5) | `rt=0.5` |
| `smn` | Server mobile number (10–13 digits) | `smn=9440520222` |
| `dmn1` | Device mobile number 1 | `dmn1=9876543210` |
| `dmn2` | Device mobile number 2 | `dmn2=9123456789` |
| `ucf` | Uplink control flags (hex byte) | `ucf=80` (GPRS ON) |

**Examples:**
```
# Set site ID and location key
(?eipl,C02,000000,sid=AWS_ROOF&lkey=SITE01?)

# Set snap interval to 5 min and upload period to 15 min
(?eipl,C02,000000,mpm=5&upm=15?)

# Set primary server IP
(?eipl,C02,000000,sip1=192.168.1.100?)

# Set RTC to 09 March 2026, 10:30
(?eipl,C02,000000,rtc=2603091030?)

# Read all current system config values
(?eipl,C02,000000,?)
```

### 8.3 Sensor Enable / Disable (C03)

C03 enables or disables individual sensors and sets the wind sensor protocol. Disabled sensors are excluded from the upload packet and CSV log.

**Packet format:** `sdiid=enabled,cfgbits[,uc]` groups separated by `;`

| sdiid | Sensor | Upload channels controlled |
|-------|--------|---------------------------|
| `B` | Base ADC (ADS112C04 raw) | — |
| `R` | Rain gauge | ch13 |
| `W` | Wind speed / direction (RS485) | ch9–ch12 |
| `T` | Temperature + Humidity (THP) | ch1–ch6 |
| `H` | Humidity / Pressure ADC slot | ch8 |
| `P` | Pressure / Solar ADC slot | ch7 |
| `S` | Solar radiation ADC slot | — |

**`cfgbits` for Wind sensor (`W`):**

| cfgbits | Protocol | Sensor |
|---------|----------|--------|
| `0x00` | Modbus RTU | RENKEE |
| `0x01` | ASCII (Gill) | Gill Instruments |

**`uc` (unit conversion) field:**

| Sensor | uc value | Unit |
|--------|----------|------|
| T (temperature) | 0 | °C (default) |
| T (temperature) | 1 | °F |
| W (wind speed) | 0 | m/s (default) |
| W (wind speed) | 1 | km/h |
| W (wind speed) | 2 | knots |
| W (wind speed) | 3 | mph |
| H (pressure slot) | 0 | Pa (default) |
| H (pressure slot) | 1 | hPa/mbar |
| H (pressure slot) | 2 | inHg |
| H (pressure slot) | 3 | mmHg |
| P (solar slot) | 0 | W/m² (default) |
| P (solar slot) | 1 | kWh/m² |

**Examples:**
```
# Enable all sensors, RENKEE wind protocol, SI units
(?eipl,C03,000000,R=Y,0x00;W=Y,0x00;T=Y,0x00;H=Y,0x00;P=Y,0x00?)

# Enable Gill wind sensor
(?eipl,C03,000000,W=Y,0x01?)

# Disable rain sensor
(?eipl,C03,000000,R=N,0x00?)

# Set temperature to Fahrenheit (uc=1)
(?eipl,C03,000000,T=Y,0x00,1?)

# Set wind speed to km/h (uc=1)
(?eipl,C03,000000,W=Y,0x00,1?)

# Read all sensor config states
(?eipl,C03,000000,c03?)
```

### 8.4 Read Sensor Description (C04)

C04 is **read-only**. It returns the sensor slot configuration (IDs, ranges, parameters) for diagnostic use:

```
(?eipl,C04,000000,?)
```

### 8.5 FTP Configuration (C05)

C05 configures FTP upload credentials (reserved for future use):

| Parameter | Description |
|-----------|-------------|
| `ftu` | FTP username |
| `ftp` | FTP password |
| `ftd` | FTP directory |
| `fts` | FTP state |

```
(?eipl,C05,000000,ftu=myuser&ftp=mypass&ftd=/data?)
```

### 8.6 Trigger Firmware Update (C06)

C06 initiates a FOTA firmware update check (same as the `startfota` terminal command):

```
(?eipl,C06,000000,?)
```

See [Section 12](#12-firmware-over-the-air-fota-update) for full FOTA details.

### 8.7 THP Sensor Offsets (C09)

Apply field correction offsets to the secondary temperature/humidity/pressure sensor readings:

```
(?eipl,C09,000000,TEMP_offset=+0.5&HUM_offset=-2.0&PRESURE_offset=+1.5?)
```

---

## 9. Communication Interfaces

### 9.1 USB CDC (Virtual COM Port)

The unit appears as a **USB CDC ACM** virtual serial port when connected to a PC.

| Property | Value |
|----------|-------|
| Driver | Native (Windows 10/11, Linux, macOS) |
| Baud Rate | Not applicable (USB CDC) |
| Windows port name | `COMx` (Device Manager → Ports) |
| Linux/macOS port | `/dev/ttyACM0` or `/dev/cu.usbmodem*` |
| Packet size | Up to 512 bytes |

**Recommended terminal software:** PuTTY, TeraTerm, minicom, or any serial terminal at any baud rate.

**Connection steps:**
1. Connect USB cable from PC to unit
2. Open Device Manager; note the COM port assigned (e.g., COM8)
3. Open terminal software, connect to COM8 (baud rate: any)
4. You will see the device boot log or the `>` prompt
5. Send commands as described in [Section 10](#10-terminal-command-reference)

### 9.2 UART1 Terminal

An alternate terminal interface is available on UART1 at **9600 baud, 8N1** (shared with the Quectel modem). This is primarily for factory use or when USB is unavailable.

### 9.3 RS485 Wind Sensor Interface

The unit is the **Modbus master** on the RS485 bus. It queries the wind sensor periodically. It does **not** act as a Modbus slave — external SCADA systems cannot query the ENVIRO_DL over RS485.

| Protocol | Baud | Format | Configuration |
|----------|------|--------|---------------|
| RENKEE Modbus RTU | 9600 | 8N1 | `W=Y,0x00` |
| Gill ASCII | Configurable | `"w?\r\n"` | `W=Y,0x01` |

---

## 10. Terminal Command Reference

### 10.1 Command Packet Format

All configuration commands use the Envirotech packet format:

```
(?eipl,<COMMAND_CODE>,<SEQUENCE>,<PAYLOAD>?)
```

| Field | Description | Example |
|-------|-------------|---------|
| `eipl` | Fixed header | `eipl` |
| Command Code | C01–C24 | `C01` |
| Sequence | 6-digit counter (use `000000`) | `000000` |
| Payload | Key=value pairs delimited by `&` | `key=value&key2=value2` |

### 10.2 Command Summary

| Command | Function | Direction |
|---------|----------|-----------|
| **C01** | Station info (SID, time, FW version, signal, faults) | Read |
| **C02** | System config: sid, lkey, mpm, upm, sip1, sip2, rtc, etc. | Read/Write |
| **C03** | Sensor enable/disable, wind protocol (`cfgbits`), unit conversion (`uc`) | Read/Write |
| **C04** | Sensor slot description (ranges, parameters) | Read |
| **C05** | FTP credentials (ftu, ftp, ftd, fts) | Read/Write |
| **C06** | Trigger FOTA firmware update check | Action |
| **C09** | THP sensor offsets (TEMP_offset, HUM_offset, PRESURE_offset) | Read/Write |
| **C10** | Current status report (latest sensor readings, all channels) | Read |
| **C11** | Retrieve single day's log records from SD card | Read |
| **C12** | Retrieve multi-day log records by date range | Read |
| **C13** | Squall event status report | Read |
| **C21** | System reset | Action |
| **C22** | Clear SD card log | Action |
| **C24** | Reset rain counter (rain_inday → 0) | Action |
| **help** | List all available commands | Read |

### 10.3 Short Terminal Commands

In addition to C-command packets, these short text commands are accepted:

| Command | Response |
|---------|----------|
| `status` | Prints a full C10 status packet |
| `config` | Prints current configuration |
| `getclock` | Queries Quectel modem for network time |
| `getsim` | Returns SIM ICCID, IMSI, MSISDN |
| `getnet` | Returns network registration & signal strength |
| `rawlog` | Enables raw UART1 hex capture to USB |
| `startfota` | Initiates a FOTA firmware update check |

### 10.4 C10 Status Response Example

```
(?eipl,R10A,000001,locationkey=SITE01&stationkey=AWS_ROOF&datetime=1741513500&ch1=26.50&ch2=25.30&ch3=24.10&ch4=65.20&ch5=64.50&ch6=63.80&ch7=450.00&ch8=1013.20&ch9=25.00&ch10=4.80&ch11=3.20&ch12=2.50&ch13=12.50&ch14=12.30?)
```

| Channel | Value in example | Meaning |
|---------|-----------------|---------|
| ch1 | 26.50 | Temperature maximum (°C) |
| ch2 | 25.30 | Temperature average (°C) |
| ch3 | 24.10 | Temperature minimum (°C) |
| ch4 | 65.20 | Humidity maximum (%RH) |
| ch5 | 64.50 | Humidity average (%RH) |
| ch6 | 63.80 | Humidity minimum (%RH) |
| ch7 | 450.00 | Solar radiation (W/m²) |
| ch8 | 1013.20 | Barometric pressure (mbar) |
| ch9 | 25.00 | Wind direction (degrees) |
| ch10 | 4.80 | Wind speed maximum (m/s) |
| ch11 | 3.20 | Wind speed average (m/s) |
| ch12 | 2.50 | Wind speed minimum (m/s) |
| ch13 | 12.50 | Daily rainfall (mm) |
| ch14 | 12.30 | Battery/supply voltage (V) |

---

## 11. Remote Data Upload

### 11.1 HTTP POST Upload

The unit uploads sensor data to a remote server using an **HTTP POST** request via the Quectel LTE modem.

**Request format:**
```
POST /api/data HTTP/1.1
Host: 192.168.1.100
Content-Type: application/x-www-form-urlencoded

datetime=20260309102500&locationkey=MUMBAI01&stationkey=AWS_ROOF&ch1=12.50&ch2=25.30...
```

**Upload frequency:** Controlled by `upm` (upload period minutes). The unit attempts upload at the end of each upload window. On failure, it retries at the next interval.

### 11.2 Upload Failure Handling

- If the server is unreachable, the record is queued and retry attempted next period
- Successful uploads are marked in the log table to avoid duplicate sends
- The upload counter on LCD Page 4 shows attempts vs. successes for diagnostics

### 11.3 LTE Modem Status

Use the terminal command `getnet` to check modem connectivity:
```
getnet
```
Response includes registration status, operator name, and signal quality (RSSI).

Use `getsim` to verify SIM is detected:
```
getsim
```

---

## 12. Firmware Over-the-Air (FOTA) Update

### 12.1 Overview

The ENVIRO_DL supports firmware updates delivered by the Quectel LTE modem from a remote FTP/HTTP server. The process is fully automated with:
- CRC32 integrity verification
- Automatic rollback if the new firmware is corrupted
- Backup of the previous firmware before flashing

### 12.2 Flash Memory Layout

```
0x08000000  ┌─────────────────────────────────┐
            │        Bootloader  (128 KB)      │  Sectors 0–4
0x08020000  ├─────────────────────────────────┤
            │       Application  (896 KB)      │  Sectors 5–11
            │       ENVIRO_DL firmware         │
0x08100000  └─────────────────────────────────┘
```

### 12.3 Update Process

**Automatic (hourly check):**
The `DataUploadManagerTask` checks for a new firmware version every hour. If available, the update begins automatically.

**Manual (terminal command):**
```
startfota
```

**Stages:**
1. STM32 sends `STARTFOTA:\r\n` to modem
2. Modem responds `FOTA:READY,<size>,<version>\r\n` (or `FOTA:NOTAVAIL\r\n` if no update)
3. Firmware is streamed in 510-byte chunks to the SD card as `update.bin`
4. CRC32 is verified against the value sent by the modem
5. On CRC match: STM32 sets RTC backup flags and reboots
6. Bootloader:
   - Backs up existing firmware to `backup.bin` on SD
   - Erases application flash sectors
   - Programs and verifies `update.bin`
   - On success: clears flags, jumps to new application
   - On failure: restores `backup.bin`, continues with previous firmware

### 12.4 During an Update

- The LCD displays a **progress bar** on Page 5
- The STATUS LED blinks rapidly
- **DO NOT power off during a FOTA update**
- If power is lost mid-update, the bootloader will detect incomplete flags and restore from `backup.bin` on the next power cycle

### 12.5 Version Check

After a successful update, the firmware version is reported in the C10 status packet and in the boot log via USB.

---

## 13. LED Status Indicator

The STATUS LED on GPIO PG4 provides visual indication of system health.

| Pattern | Meaning |
|---------|---------|
| **1 Hz blink** (500 ms on/off) | System healthy, normal operation |
| **Solid ON** | Active fault (check LCD Page 0 or USB for fault details) |
| **200 ms single flash** | Sensor reading completed |
| **3 × 100 ms rapid pulses** | Upload succeeded |
| **2-second solid** | Upload failed |
| **Rapid blink** | FOTA update in progress |

---

## 14. Fault Codes & Troubleshooting

### 14.1 Fault Bitmask

The system fault bitmask is reported in the C01 status packet (`F=` field) and displayed on LCD Page 0. It is **not** a numbered channel in the upload packet (ch13 is daily rainfall; ch14 is battery voltage).

| Bit (hex) | Fault | Cause |
|-----------|-------|-------|
| `0x4000` | Power fault | Supply voltage out of range |
| `0x2000` | SD card fault | SD not mounted or write error |
| `0x1000` | Logging fault | File write failed |
| `0x0800` | RTC fault | Internal or external RTC unresponsive |
| `0x0400` | ADC fault | NAU7802 or ADS112C04 not responding |
| `0x0200` | Modem fault | Quectel modem not responding |
| `0x0100` | GPS fault | GPS query timeout (if GPS enabled) |

A value of `0` means no faults. Read via: `(?eipl,C01,000000,?)`

### 14.2 Common Issues

**Unit powers on but STATUS LED stays solid:**
- Check USB terminal for error messages
- LCD Page 0 will show which subsystem (`SD:ERR`, `MOD:ERR`, etc.) is faulted
- Verify SD card is inserted and formatted FAT32
- Verify sensor wiring (I2C pullups, RS485 polarity)

**No data on SD card:**
- Confirm snap interval is configured correctly (`C04`)
- Check SD card is not full
- Verify `config.bin` is loaded at boot (USB terminal will log config load status)

**Data not uploading:**
- Check LTE signal: run `getnet` — should show "registered" and RSSI > -90 dBm
- Verify server IP and page configured correctly (`C06`)
- Check SIM card is active and data plan is enabled (`getsim`)
- Review upload counters on LCD Page 4

**Wind readings are zero:**
- Verify RS485 wiring (A/B polarity)
- Confirm correct protocol selected (`W=Y,0x00` for RENKEE, `W=Y,0x01` for Gill)
- Check wind sensor power supply
- Use USB terminal — boot log will show RS485 initialization status

**Rain counts stuck at zero:**
- Verify rain gauge wire connected to PG7 terminal
- Test by momentarily shorting the rain gauge terminals — count should increment
- Check rain gauge reed switch with multimeter

**Time is wrong after power cycle:**
- Set time via `C07` command
- Verify MCP7940 RTC has a coin cell battery installed
- Check USB boot log for `MCP7940 sync` messages

**Temperature reading is out of range:**
- Check PT1000 probe wiring to NAU7802 ADC
- Verify calibration gain/offset via C02 command
- Confirm NAU7802 I2C address (0x54) on bus

---

## 15. SD Card File Reference

| Filename | Description |
|----------|-------------|
| `DDMMYY.csv` | Daily log file (e.g., `090326.csv` = 9 March 2026) |
| `DDMMYY_bkp.csv` | Backup of previous day's log |
| `config.bin` | Main configuration (snap interval, upload period, server, sensor enables) |
| `nvdata.bin` | Non-volatile data (ADC calibration, battery voltage cal, rain persistence) |
| `thp_cfg.bin` | THP sensor offsets (temperature, humidity, pressure corrections) |
| `ftp_cfg.bin` | FTP server credentials (reserved for future use) |
| `update.bin` | Staged FOTA firmware file (created during update, deleted after flash) |
| `backup.bin` | Previous firmware backup (created by bootloader before flashing) |

**Maintenance tips:**
- Periodically archive and delete old `DDMMYY.csv` files to prevent the card from filling up
- Do not delete `config.bin`, `nvdata.bin`, or `thp_cfg.bin` — these hold your calibration settings
- Do not remove the SD card while the unit is powered

---

## 16. Technical Specifications

### Microcontroller

| Parameter | Value |
|-----------|-------|
| MCU | STM32F417 |
| Core | ARM Cortex-M4 |
| Clock Speed | 168 MHz |
| Flash | 1 MB |
| RAM | 196 KB |
| RTOS | FreeRTOS (CMSIS-RTOS v2) |

### Communication

| Interface | Standard | Notes |
|-----------|----------|-------|
| USB | USB 2.0 Full-Speed CDC | Virtual COM port |
| LTE Modem | Quectel (AT command interface) | HTTP POST, FOTA |
| RS485 | Modbus RTU / ASCII | Wind sensor only |
| I2C | 100/400 kHz | Sensors, RTC |
| SPI | — | LCD, SD card |

### Sensors

| Parameter | Sensor | Resolution | Range |
|-----------|--------|------------|-------|
| Temperature | PT1000 + NAU7802 | 24-bit ADC | -40 to +80 °C |
| Humidity | ADS112C04 | 24-bit ADC | 0–100 %RH |
| Pressure | ADS112C04 / BMP280 | 24-bit ADC | 300–1100 hPa |
| Wind Speed | RS485 sensor | 0.1 m/s | 0–60 m/s (sensor dependent) |
| Wind Direction | ADS112C04 | 1° | 0–360° |
| Solar Radiation | ADS112C04 | — | 0–2000 W/m² |
| Rainfall | Tipping bucket | 0.5 mm/tip | Unlimited accumulation |

### Power

| Parameter | Value |
|-----------|-------|
| Input Voltage | 5–12 V DC |
| Operating Current | ~200–400 mA (typical, modem active) |
| Sleep Current | N/A (always-on operation) |
| RTC Backup | External coin cell via MCP7940 |

---

## 17. Known Limitations

The following features are planned or partially implemented but not yet available in this firmware version:

| Feature | Status | Notes |
|---------|--------|-------|
| GPS / GNSS coordinates | Not implemented | Modem hardware capable; firmware support pending |
| FTP upload | Not implemented | Infrastructure exists; not wired to scheduler |
| Alert SMS on threshold breach | Not implemented | No real-time threshold monitoring |
| Power-on SMS notification | Not implemented | — |
| Network time sync (NTP) | Not implemented | RTC may drift over weeks; set manually via C07 |
| Low-power / sleep mode | Not implemented | Unit is always-on; not suitable for battery-only deployment without external management |
| USB pen drive data export | Not implemented | No USB MSC host stack |
| Real-time streaming (`stream N`) | Not implemented | Terminal command not yet functional |
| Modbus slave (SCADA query) | Not implemented | Unit cannot be queried by external RS485 SCADA |

---

## Appendix A — Quick-Start Command Sequence

```
# 1. Set station ID and location key (saved automatically)
(?eipl,C02,000000,sid=AWS_ROOF&lkey=SITE01?)

# 2. Set primary server IP
(?eipl,C02,000000,sip1=192.168.1.100?)

# 3. Set current date and time (format: YYMMDDHHmm)
(?eipl,C02,000000,rtc=2603091030?)

# 4. Set 5-minute snap interval and upload period
(?eipl,C02,000000,mpm=5&upm=5?)

# 5. Enable all sensors, RENKEE wind protocol, SI units
(?eipl,C03,000000,R=Y,0x00;W=Y,0x00;T=Y,0x00;H=Y,0x00;P=Y,0x00?)

# 6. Verify station info
(?eipl,C01,000000,?)

# 7. Read current sensor status
(?eipl,C10,000000,?)
```

---

## Appendix B — Glossary

| Term | Definition |
|------|------------|
| **CDC** | USB Communications Device Class — provides virtual COM port |
| **FOTA** | Firmware Over-the-Air — remote firmware update via modem |
| **MMA** | Min/Max/Average — statistical aggregation per snap interval |
| **Modbus RTU** | Serial communication protocol used for wind sensor |
| **PT1000** | Platinum resistance temperature detector, 1000 Ω at 0 °C |
| **RTC** | Real-Time Clock — maintains date and time |
| **Snap interval** | Period between log file writes and data uploads |
| **SHT25/SHT45** | Sensirion humidity + temperature sensor (secondary) |
| **BMP280** | Bosch barometric pressure sensor (secondary) |
| **NAU7802** | 24-bit I2C ADC used for PT1000 temperature measurement |
| **ADS112C04** | Texas Instruments 24-bit multi-channel ADC |
| **Squall** | Sudden wind speed increase >25%, detected by WMO state machine |
| **ch13** | Daily rainfall total (mm) in every upload packet |
| **ch14** | Battery / supply voltage (V) — always included in every upload packet |

---

*Document generated from firmware source code — ENVIRO_DL_STM32F, March 2026*
*For technical support, contact SVIOT.*