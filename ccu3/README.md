# CCU3 TRV Boiler Control

A HomeMatic script for the **CCU3 / RaspberryMatic** that switches a boiler
based on how far the **HomeMatic IP radiator thermostats (TRVs)** are open.

This is the HomeMatic IP successor of the original thermeq3 logic for the
eQ-3 MAX! system. It keeps the same idea, including the **SVPNMW** setting
(Single Valve Position, No Matter What), but runs directly on the CCU. No
Arduino Yún, Raspberry Pi or other extra computer is needed.

The heating keeps working even when Home Assistant or any other system is
down. All thresholds are stored in CCU system variables, so you can change
them from the CCU WebUI or from Home Assistant without editing the script.

## Features

- **Automatic TRV discovery.** Every run scans all HmIP eTRV devices. You do
  not need to edit anything when you add or remove a TRV.
- **Valve-count logic with hysteresis.** The boiler turns ON when at least *N*
  valves are open to or beyond the ON threshold. It stays ON while at least *N*
  valves are still open beyond the OFF threshold.
- **Single valve override (SVPNMW).** If any one valve opens to or beyond
  this value, the boiler turns ON regardless of *N*.
- **Unreachable TRVs are ignored.** A stale valve position from a dead or
  out-of-range TRV cannot keep the boiler running.
- **Failsafe.** If no TRV is reachable, the boiler is switched OFF.
- **Selectable controller.** `CCU`, `ESP` (an external OpenTherm thermostat),
  or `Manual`. In ESP mode the CCU takes over automatically if the ESP goes
  silent.
- **Exclude list.** You can skip specific TRVs, for example a bathroom with
  its own heating.
- **Low flash wear.** The script writes to the actuator and to system
  variables only when a value actually changes.
- **Home Assistant ready.** Input variables carry the `HAHM` marker, so the
  [Homematic(IP) Local](https://github.com/SukramJ/custom_homematic)
  integration exposes them as editable entities.
- **Heartbeat.** The script records the time of its last run and the number of
  runs today.

## Hardware

### Required

| Device | Qty | Role | Notes |
|---|---|---|---|
| **CCU3** (HmIP-CCU3) or **RaspberryMatic** | 1 | Runs the script | RaspberryMatic needs a HomeMatic IP capable radio module, e.g. RPI-RF-MOD or HmIP-RFUSB. A current firmware is recommended. |
| **HomeMatic IP radiator thermostat** | 1 or more | Measures the room and reports the valve position (`LEVEL`) | Any device whose type contains `eTRV` is used: HmIP-eTRV, HmIP-eTRV-2, HmIP-eTRV-B, HmIP-eTRV-C, HmIP-eTRV-E and their variants. With `TRV_Min_Count = 2` you need at least 2 TRVs, unless SVPNMW is enabled. |
| **HmIP-WHS2** switching actuator for heating systems | 1 | Switches the boiler's heating demand | Wire one relay output to the boiler's room thermostat input (on/off, volt-free). Check the boiler manual and the WHS2 contact rating before wiring. |
| **Boiler with an on/off room thermostat input** | 1 | Heat source | Most gas boilers have a 2-wire terminal for an on/off room thermostat. |

The script switches one virtual channel of the WHS2 (by default channel `:3`).
The other virtual channels of the same output (`:2`, `:4`) should stay `false`,
because the WHS2 combines its virtual channels with OR logic.

Not supported:

- HomeMatic classic (BidCoS) thermostats such as HM-CC-RT-DN. The script reads
  only `HmIP-RF` devices.
- HomeMatic IP wall thermostats (HmIP-WTH-2, HmIP-BWTH). They have no valve,
  so they are not counted. A wall thermostat paired with TRVs in a room still
  works: the TRVs report their valve positions as usual.

### Optional, per feature

| Feature | Hardware or software needed |
|---|---|
| Control from Home Assistant | A Home Assistant server with the [Homematic(IP) Local](https://github.com/SukramJ/custom_homematic) integration |
| `ESP` controller mode (modulating OpenTherm control) | An ESP32 board, an OpenTherm adapter (for example a DIYLess OpenTherm shield or an Ihor Melnyk OpenTherm adapter) and an OpenTherm-capable boiler, running ESPHome |
| `ESP` mode with WHS2 kept as a safety contact | The WHS2 contact wired in series with the OpenTherm path; set `WHS2_IN_SERIES = true` |
| HTTPS access from the ESP to the CCU | HTTPS enabled on the CCU (port 48181) and its CA certificate in the ESP firmware |

The core features (TRV discovery, valve-count logic, SVPNMW, failsafe, exclude
list, heartbeat) need only the required hardware.

## How it works

The script runs every 5 minutes and goes through these steps:

1. Read the configuration from system variables. If a variable is missing,
   the built-in default is used.
2. Scan all configured eTRV devices and skip those listed in `TRV_Exclude`.
3. For each reachable TRV:
   - round the valve position (`LEVEL`, 0–1) to whole percent;
   - count how many valves are at or above `TRV_Threshold_On`;
   - count how many valves are above `TRV_Threshold_Off`;
   - remember the most open valve.
4. Decide the boiler state:

   | Boiler is | Switch ON when | Switch OFF when |
   |---|---|---|
   | OFF | the number of valves ≥ `On` reaches `TRV_Min_Count`, **or** the most open valve ≥ `TRV_SVPNMW` | – |
   | ON | – | the number of valves > `Off` drops below `TRV_Min_Count`, **and** the most open valve ≤ `TRV_SVPNMW − (On − Off)` |

   If `TRV_SVPNMW` is `0`, only the valve-count rule applies. If no TRV is
   reachable, the boiler is switched OFF.
5. Switch the WHS2 only if its state changes.
6. Update the output variables (TRV list, count, maximum valve position,
   active controller) and the heartbeat.

### Example

Settings: `On = 30 %`, `Off = 25 %`, `Min_Count = 2`, `SVPNMW = 75 %`.

| Valves | Result |
|---|---|
| 35 %, 32 %, 10 % | ON: two valves are at or above 30 % |
| 80 %, 5 %, 0 % | ON: one valve is at or above 75 % (SVPNMW) |
| Boiler ON, valves at 72 %, 5 % | Stays ON: 72 % is still above 75 − 5 = 70 % |
| Boiler ON, valves at 26 %, 24 % | OFF: only one valve is above 25 % |

### Controller modes (`TRV_Boiler_Control`)

| Value | Behaviour |
|---|---|
| `CCU` (0) | The script switches the WHS2. This is the default. |
| `ESP` (1) | An external controller switches the boiler. The script holds the WHS2 in its passive state (see `WHS2_IN_SERIES`). If `TRV_ESP_LastSeen` is older than `ESP_TIMEOUT_MIN`, the script falls back to CCU control until the ESP reports again. |
| `Manual` (2) | The script never touches the WHS2. It only computes the outputs. |

The controller that is actually active, including fallback, is written to
`TRV_Control_Active`.

## Files

| File | Purpose |
|---|---|
| [`create_system_variables.hm`](create_system_variables.hm) | Creates all system variables. Run it once; existing variables are skipped. |
| [`trv_boiler.hm`](trv_boiler.hm) | The boiler control script. |

## Installation

1. **Create the system variables.** Open the CCU WebUI and go to
   *Programs and connections → Programs & CCU connection → Test script*.
   Paste `create_system_variables.hm` and run it. Check the result under
   *Settings → System variables*.
2. **Adjust the constants** at the top of `trv_boiler.hm`:

   ```
   string  WHS2_DP         = "HmIP-RF.<WHS2-SERIAL>:3.STATE";
   boolean WHS2_IN_SERIES  = false;
   integer ESP_TIMEOUT_MIN = 10;
   ```

   - `WHS2_DP`: the datapoint of the WHS2 virtual channel that drives the
     boiler. Replace `<WHS2-SERIAL>` with the serial number of your WHS2.
   - `WHS2_IN_SERIES`: set to `true` if the WHS2 contact is wired in series
     with the external controller (the boiler heats only when both allow
     it). In that case the WHS2 is held **ON** in ESP mode. With `false`
     (independent paths) it is held **OFF**. `false` is the safer default.
   - `ESP_TIMEOUT_MIN`: how long the ESP may be silent before the CCU takes
     over.
3. **Test it.** Paste `trv_boiler.hm` into *Test script* and check the output
   (see below).
4. **Create the program.** Add a new program:
   - **If:** Time control → all day, every 5 minutes (trigger at time).
   - **Then:** Script → paste `trv_boiler.hm` (execute immediately).
   - **Else:** empty.

   Disable any older program that switches the same WHS2 channel.
5. **Recommended WHS2 setting.** In the device configuration, set the
   behaviour after power restoration to *Off*. After a power cut the boiler
   then stays off until the script decides, at most 5 minutes later.

## System variables

### Inputs

These carry the `HAHM` marker and are editable in Home Assistant.

| Name | Type | Range | Default | Description |
|---|---|---|---|---|
| `TRV_Threshold_On` | Number | 0–100 % | 30 | Valve position that counts as "open" for switching ON |
| `TRV_Threshold_Off` | Number | 0–100 % | 25 | Valve position that still counts as "open" for staying ON |
| `TRV_Min_Count` | Number | 1–10 | 2 | Minimum number of open valves (*N*) |
| `TRV_SVPNMW` | Number | 0–100 % | 75 | Single valve override; `0` disables it |
| `TRV_Boiler_Control` | Value list | `CCU;ESP;Manual` | `CCU` | Who switches the boiler |
| `TRV_Exclude` | String | – | empty | TRV addresses to skip, separated by `;` |

If `TRV_Threshold_Off` is set higher than `TRV_Threshold_On`, the script uses
the ON value for both.

### Outputs

| Name | Type | Description |
|---|---|---|
| `TRV_List` | String | Addresses of all used TRVs, separated by `;` |
| `TRV_Count` | Number | Number of TRVs in `TRV_List` |
| `TRV_List_Changed` | String | Time of the last change of `TRV_List` |
| `TRV_Max_Level` | Number (%) | Position of the most open reachable valve |
| `TRV_Control_Active` | String | Active controller: `CCU`, `ESP`, `Manual`, or `CCU fallback (ESP silent)` |
| `TRV_ESP_LastSeen` | String | Written by the ESP on every poll (`YYYY-MM-DD HH:MM:SS`) |
| `TRV_Script_LastRun` | String | Time of the last script run |
| `TRV_Script_RunsToday` | Number | Script runs today; resets at midnight |

Example `TRV_List`:

```
000A1BE99885DA;000A1A49A520F0;000A1A49A520FE;00201A49A56CBB
```

## Example output

```
Control: CCU | ESP age: -1 s
Threshold ON  30% -> 3 valves
Threshold OFF 25% -> 3 valves
SVPNMW 75% (hold > 70%) | max valve 82% Bedroom T | on true hold true
Valid TRV: 10 | unreachable: 0
Min count: 2 | WHS2: false -> true
TRV list (10): 000A1BE99885DA;000A1A49A520F0;...
Last run: 2026-10-24 10:15:00 | runs today: 124
```

## Home Assistant

With the Homematic(IP) Local integration, the system variables appear as
entities:

- Variables with `HAHM` in their description become editable entities:
  `number.*` for numbers, `select.*` for the value list, and `text.*` for
  strings. Reload the integration after adding the marker.
- All other variables appear as read-only sensors.
- To refresh the values manually, call the action
  `homematicip_local.fetch_system_variables`.

## Using the data from an ESP (optional)

An ESP32 (for example an ESPHome OpenTherm thermostat) can read the same data
through the CCU Script API (`/rega.exe`, port 8181, or 48181 for HTTPS):

- Read `TRV_List` and query `ACTUAL_TEMPERATURE`, `SET_POINT_TEMPERATURE`,
  `LEVEL`, and `UNREACH` for each address. New or removed TRVs are then
  picked up without recompiling the firmware.
- Read `TRV_SVPNMW` and `TRV_Boiler_Control` so that all settings live in one
  place.
- On every poll, write the current time to `TRV_ESP_LastSeen` so that the CCU
  can detect a silent ESP and fall back.

Restrict the Script API in the CCU firewall to the ESP's IP address and use
authentication.

## Notes and limitations

- **Start-up.** CCU programs have no "on system start" trigger. After a reboot
  the script runs within 5 minutes. The WHS2 keeps its relay state during a
  CCU reboot.
- **Device names.** If you read names over the Script API, avoid `;`, `|`, and
  non-ASCII characters in TRV device names.
- **Variable creation.** `create_system_variables.hm` uses the
  `dom.CreateObject(OT_VARDP)` method, which is widely used but not officially
  documented. Verify the created variables in the WebUI.
- **Single controller.** Make sure only one controller drives the boiler at a
  time. Use `TRV_Boiler_Control`; do not run two independent automations.

## License

GPL-3.0, the same as the rest of this repository. See [LICENSE](../LICENSE).
