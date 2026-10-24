# CCU3 TRV Boiler Control

A HomeMatic script for the **CCU3 / RaspberryMatic** that switches a boiler
based on how far the **HomeMatic IP radiator thermostats (TRVs)** are open.

This is the HomeMatic IP successor of the original thermeq3 logic for the
eQ-3 MAX! system. It keeps the same ideas, including **SVPNMW** (Single Valve
Position, No Matter What), summer mode, ventilation detection and settings
checks, but runs directly on the CCU. No Arduino Yún, Raspberry Pi or other
extra computer is needed.

The heating keeps working even when Home Assistant or any other system is
down. All settings are stored in CCU system variables, so you can change them
from the CCU WebUI or from Home Assistant without editing the script.

## Features

- **Automatic TRV discovery.** Every run scans all HmIP eTRV devices. You do
  not need to edit anything when you add or remove a TRV.
- **Valve-count logic with hysteresis.** The boiler turns ON when at least *N*
  valves are open to or beyond the ON threshold. It stays ON while at least *N*
  valves are still open beyond the OFF threshold.
- **Counting by rooms.** Optionally, *N* counts CCU rooms instead of valves.
  A room with two radiators then counts once; its position is the average of
  its valves.
- **Single valve override (SVPNMW).** If any one valve opens to or beyond
  this value, the boiler turns ON regardless of *N*.
- **Summer mode.** Off, On, or Auto by outdoor temperature, with hysteresis
  and an adjustable delay. While it is active, the boiler output is never
  switched ON.
- **Ventilation detection.** When a set number of rooms have an open window,
  the script reports that the house is being ventilated.
- **Settings check.** Invalid or contradictory settings are corrected for the
  current run and reported in a warning variable.
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
| **HomeMatic IP radiator thermostat** | 1 or more | Measures the room and reports the valve position (`LEVEL`) | Any device whose type contains `eTRV` is used: HmIP-eTRV, HmIP-eTRV-2, HmIP-eTRV-B, HmIP-eTRV-C, HmIP-eTRV-E and their variants. With `TRV_Min_Count = 2` you need at least 2 TRVs (or 2 rooms), unless SVPNMW is enabled. |
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
| Counting by rooms | TRVs assigned to rooms in the CCU (*Settings → Rooms*). No extra hardware. |
| Ventilation detection | Works with the TRVs alone (their window-open detection, `WINDOW_STATE`). Window contacts in the same CCU room make it more reliable: HmIP-SWDO, HmIP-SWDO-I, HmIP-SWDO-PL, HmIP-SWDM or HmIP-SRH. |
| Summer mode `Auto` | An outdoor temperature written to `TRV_Outdoor_Temp`, for example by Home Assistant from a weather service or an outdoor sensor |
| Control from Home Assistant | A Home Assistant server with the [Homematic(IP) Local](https://github.com/SukramJ/custom_homematic) integration |
| `ESP` controller mode (modulating OpenTherm control) | An ESP32 board, an OpenTherm adapter (for example a DIYLess OpenTherm shield or an Ihor Melnyk OpenTherm adapter) and an OpenTherm-capable boiler, running ESPHome |
| `ESP` mode with WHS2 kept as a safety contact | The WHS2 contact wired in series with the OpenTherm path; set `WHS2_IN_SERIES = true` |
| HTTPS access from the ESP to the CCU | HTTPS enabled on the CCU (port 48181) and its CA certificate in the ESP firmware |

The core features (TRV discovery, valve-count logic, SVPNMW, summer mode `On`,
failsafe, settings check, exclude list, heartbeat) need only the required
hardware.

## How it works

The script runs every 5 minutes and goes through these steps:

1. **Read and check the settings.** If a variable is missing, the built-in
   default is used. Invalid values are corrected for this run and reported in
   `TRV_Config_Warnings` (see [Settings check](#settings-check)).
2. **Scan the rooms.** For each CCU room, compute the average position of its
   reachable TRVs and check whether a window is open (a TRV `WINDOW_STATE`
   or a window contact).
3. **Scan all TRVs.** Build `TRV_List`, count single valves at or above the
   ON threshold and above the OFF threshold, and find the most open valve.
   A TRV that is not assigned to any room counts as its own room.
4. **Evaluate summer mode, ventilation and SVPNMW.**
5. **Decide the boiler state**, in this order of priority:
   1. summer mode active → OFF;
   2. no reachable TRV → OFF (failsafe);
   3. valve or room count with hysteresis, plus SVPNMW:

   | Boiler is | Switch ON when | Switch OFF when |
   |---|---|---|
   | OFF | the number of valves (rooms) ≥ `On` reaches `TRV_Min_Count`, **or** the most open valve ≥ `TRV_SVPNMW` | – |
   | ON | – | the number of valves (rooms) > `Off` drops below `TRV_Min_Count`, **and** the most open valve ≤ `TRV_SVPNMW − (On − Off)` |

   If `TRV_SVPNMW` is `0`, only the count rule applies.
6. **Switch the WHS2** only if its state changes.
7. **Update the outputs** and the heartbeat.

### Example

Settings: `On = 30 %`, `Off = 25 %`, `Min_Count = 2`, `SVPNMW = 75 %`,
`Count_Mode = Valves`.

| Valves | Result |
|---|---|
| 35 %, 32 %, 10 % | ON: two valves are at or above 30 % |
| 80 %, 5 %, 0 % | ON: one valve is at or above 75 % (SVPNMW) |
| Boiler ON, valves at 72 %, 5 % | Stays ON: 72 % is still above 75 − 5 = 70 % |
| Boiler ON, valves at 26 %, 24 % | OFF: only one valve is above 25 % |

### Counting by rooms (`TRV_Count_Mode`)

| Value | Behaviour |
|---|---|
| `Valves` (0) | `On`, `Off` and `Min_Count` apply to single valves. This is the default. |
| `Rooms` (1) | They apply to CCU rooms. The room position is the **average** of its reachable TRVs, rounded to whole percent. |

- The room of a TRV is the room its channel 1 is assigned to. If the channel
  is in more than one room, the first one is used.
- A TRV that is not assigned to any room counts as a room of its own.
- SVPNMW always applies to single valves, in both modes.

Example with `Rooms`, `On = 30 %`, `Min_Count = 2`: the living room has two
TRVs at 40 % and 30 % (average 35 %), the bedroom has one TRV at 10 %. Only
one room is at or above 30 %, so the boiler stays OFF. In `Valves` mode the
same situation switches it ON, because two valves are at or above 30 %.

### Summer mode (`TRV_Summer_Mode`)

| Value | Behaviour |
|---|---|
| `Off` (0) | Heating allowed. This is the default. |
| `On` (1) | Heating blocked. |
| `Auto` (2) | Blocked when `TRV_Outdoor_Temp` is above `TRV_Summer_Temp`; released when it drops below `TRV_Summer_Temp − 1 °C`. Each change happens only after the condition has lasted `TRV_Summer_Delay` minutes. |

While summer mode is active:

- in `CCU` mode (and during the ESP fallback) the script never switches the
  WHS2 ON, and switches it OFF if it is ON;
- in `ESP` mode with `WHS2_IN_SERIES = true` the WHS2 is held OFF, which
  blocks the boiler also for the ESP. With independent wiring the CCU cannot
  stop the ESP, so the ESP has to read `TRV_Summer_Active` itself;
- in `Manual` mode the WHS2 is not touched.

`TRV_Summer_Pending` shows since when a change is waiting for the delay;
empty means no change is pending.

If the outdoor temperature is missing or older than `OUTDOOR_MAX_AGE_MIN`
(180 minutes by default), `Auto` behaves like `Off`, so heating is allowed,
and a warning is written. Running the heating unnecessarily is safer than
letting the house cool down.

### Ventilation detection

A room has an open window when one of its TRVs reports `WINDOW_STATE = OPEN`,
or one of its window contacts reports open (for a rotary handle sensor,
tilted also counts as open). The script counts **rooms**, not windows: three
open windows in one room still count as one room.

`TRV_Ventilating` is `true` while `TRV_Open_Rooms` ≥ `TRV_Vent_Rooms`.
Set `TRV_Vent_Rooms` to `0` to disable the detection. Ventilation does not
change the boiler decision; it is information for Home Assistant and for the
open window warnings planned for a later version.

### Controller modes (`TRV_Boiler_Control`)

| Value | Behaviour |
|---|---|
| `CCU` (0) | The script switches the WHS2. This is the default. |
| `ESP` (1) | An external controller switches the boiler. The script holds the WHS2 in its passive state (see `WHS2_IN_SERIES`). If `TRV_ESP_LastSeen` is older than `ESP_TIMEOUT_MIN`, the script falls back to CCU control until the ESP reports again. |
| `Manual` (2) | The script never touches the WHS2. It only computes the outputs. |

The controller that is actually active, including fallback, is written to
`TRV_Control_Active`.

### Settings check

The script never changes your input variables. It corrects invalid values only
for the current run, and lists every correction in `TRV_Config_Warnings`
(empty means everything is OK) and in the script output.

| Check | Action |
|---|---|
| `On`, `Off` or `SVPNMW` outside 0–100 % | Clamped to 0–100 % |
| `Off` > `On` | `Off` = `On` |
| `On` = `Off` | Warning only: no hysteresis, the boiler may switch often |
| `On` > 90 % | Warning only: the boiler will rarely start |
| `Min_Count` < 1 | 1 |
| `Min_Count` > number of reachable valves (rooms) | That number is used, otherwise the boiler would never start |
| `SVPNMW` > 0 and < `On` | `SVPNMW` = `On` |
| `Summer_Temp` outside 5–30 °C | 15 °C |
| `Summer_Delay` outside 0–1440 min | Clamped to 0–1440 |
| `Vent_Rooms` < 0 | 0 (disabled) |
| Unknown `Boiler_Control`, `Count_Mode` or `Summer_Mode` value | `CCU`, `Valves`, `Off` |
| Summer mode `Auto` without a valid outdoor temperature | Heating allowed |
| WHS2 datapoint not found | Warning |

## Files

| File | Purpose |
|---|---|
| [`create_system_variables.hm`](create_system_variables.hm) | Creates all system variables. Existing variables are skipped, so you can run it again after an update to add new ones. |
| [`trv_boiler.hm`](trv_boiler.hm) | The boiler control script. |

## Installation

1. **Create the system variables.** Open the CCU WebUI and go to
   *Programs and connections → Programs & CCU connection → Test script*.
   Paste `create_system_variables.hm` and run it. Check the result under
   *Settings → System variables*.
2. **Adjust the constants** at the top of `trv_boiler.hm`:

   ```
   string  WHS2_DP             = "HmIP-RF.<WHS2-SERIAL>:3.STATE";
   boolean WHS2_IN_SERIES      = false;
   integer ESP_TIMEOUT_MIN     = 10;
   integer OUTDOOR_MAX_AGE_MIN = 180;
   real    SUMMER_HYST         = 1.0;
   ```

   - `WHS2_DP`: the datapoint of the WHS2 virtual channel that drives the
     boiler. Replace `<WHS2-SERIAL>` with the serial number of your WHS2.
   - `WHS2_IN_SERIES`: set to `true` if the WHS2 contact is wired in series
     with the external controller (the boiler heats only when both allow
     it). In that case the WHS2 is held **ON** in ESP mode. With `false`
     (independent paths) it is held **OFF**. `false` is the safer default.
   - `ESP_TIMEOUT_MIN`: how long the ESP may be silent before the CCU takes
     over.
   - `OUTDOOR_MAX_AGE_MIN`: after how many minutes without an update the
     outdoor temperature is considered stale; `0` disables the check.
   - `SUMMER_HYST`: hysteresis of summer mode `Auto` in °C.
3. **Assign the TRVs and window contacts to rooms** in the CCU, if you want to
   count by rooms or detect ventilation.
4. **Test it.** Paste `trv_boiler.hm` into *Test script* and check the output
   (see below).
5. **Create the program.** Add a new program:
   - **If:** Time control → all day, every 5 minutes (trigger at time).
   - **Then:** Script → paste `trv_boiler.hm` (execute immediately).
   - **Else:** empty.

   Disable any older program that switches the same WHS2 channel.
6. **Recommended WHS2 setting.** In the device configuration, set the
   behaviour after power restoration to *Off*. After a power cut the boiler
   then stays off until the script decides, at most 5 minutes later.

## System variables

### Inputs

These carry the `HAHM` marker and are editable in Home Assistant.

| Name | Type | Range | Default | Description |
|---|---|---|---|---|
| `TRV_Threshold_On` | Number | 0–100 % | 30 | Position that counts as "open" for switching ON |
| `TRV_Threshold_Off` | Number | 0–100 % | 25 | Position that still counts as "open" for staying ON |
| `TRV_Min_Count` | Number | 1–10 | 2 | Minimum number of open valves or rooms (*N*) |
| `TRV_SVPNMW` | Number | 0–100 % | 75 | Single valve override; `0` disables it |
| `TRV_Boiler_Control` | Value list | `CCU;ESP;Manual` | `CCU` | Who switches the boiler |
| `TRV_Count_Mode` | Value list | `Valves;Rooms` | `Valves` | Count single valves or rooms |
| `TRV_Summer_Mode` | Value list | `Off;On;Auto` | `Off` | Summer mode |
| `TRV_Summer_Temp` | Number | 5–30 °C | 15 | Outdoor temperature limit for summer mode `Auto` |
| `TRV_Summer_Delay` | Number | 0–1440 min | 60 | How long the outdoor condition must last before summer mode changes |
| `TRV_Outdoor_Temp` | Number | −50–60 °C | – | Outdoor temperature, written by Home Assistant |
| `TRV_Vent_Rooms` | Number | 0–20 | 3 | Rooms with an open window that mean ventilating; `0` disables it |
| `TRV_Exclude` | String | – | empty | TRV addresses to skip, separated by `;` |

### Outputs

| Name | Type | Description |
|---|---|---|
| `TRV_List` | String | Addresses of all used TRVs, separated by `;` |
| `TRV_Count` | Number | Number of TRVs in `TRV_List` |
| `TRV_List_Changed` | String | Time of the last change of `TRV_List` |
| `TRV_Max_Level` | Number (%) | Position of the most open reachable valve |
| `TRV_Demand_Rooms` | String | Valves (`Valves` mode) or rooms (`Rooms` mode) at or above `TRV_Threshold_On` |
| `TRV_Open_Rooms` | Number | Rooms with an open window |
| `TRV_Ventilating` | Boolean | The house is being ventilated |
| `TRV_Summer_Active` | Boolean | Summer mode is active, heating blocked |
| `TRV_Summer_Pending` | String | Since when a summer mode change is waiting for the delay; empty = none |
| `TRV_Config_Warnings` | String | Settings warnings; empty = OK |
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
Summer mode: 2 | active: false | outdoor 8.400000 (ok true) | limit 15.000000 | pending since:
Count mode: rooms | valves on/hold/valid 3/3/10 | rooms on/hold/valid 2/2/7
Threshold ON 30% | OFF 25% | Min count: 2 rooms
SVPNMW 75% (hold > 70%) | max valve 82% Bedroom T | on true hold true
Demand: Bedroom, Living room
Open rooms: 1 | ventilating: false (limit 3)
Valid TRV: 10 | unreachable: 0
WHS2: false -> true
Warnings:
TRV list (10): 000A1BE99885DA;000A1A49A520F0;...
Last run: 2026-10-24 10:15:00 | runs today: 124
```

## Home Assistant

With the Homematic(IP) Local integration, the system variables appear as
entities:

- Variables with `HAHM` in their description become editable entities:
  `number.*` for numbers, `select.*` for value lists, and `text.*` for
  strings. Reload the integration after adding the marker.
- All other variables appear as read-only sensors.
- To refresh the values manually, call the action
  `homematicip_local.fetch_system_variables`.

### Writing the outdoor temperature

Summer mode `Auto` needs the outdoor temperature in `TRV_Outdoor_Temp`. Write
it from Home Assistant regularly, more often than `OUTDOOR_MAX_AGE_MIN`. For
example, every 15 minutes:

```yaml
alias: CCU outdoor temperature
triggers:
  - trigger: time_pattern
    minutes: "/15"
actions:
  - action: number.set_value
    target:
      entity_id: number.ccu3_trv_outdoor_temp   # check the entity name in HA
    data:
      value: "{{ state_attr('weather.home', 'temperature') | float(0) }}"
```

Use any outdoor sensor instead of `weather.home` if you have one. Skip the
write when the source is unavailable, so that the CCU can detect the stale
value instead of receiving `0`.

## Using the data from an ESP (optional)

An ESP32 (for example an ESPHome OpenTherm thermostat) can read the same data
through the CCU Script API (`/rega.exe`, port 8181, or 48181 for HTTPS):

- Read `TRV_List` and query `ACTUAL_TEMPERATURE`, `SET_POINT_TEMPERATURE`,
  `LEVEL`, and `UNREACH` for each address. New or removed TRVs are then
  picked up without recompiling the firmware.
- Read `TRV_SVPNMW`, `TRV_Boiler_Control` and `TRV_Summer_Active` so that all
  settings live in one place.
- On every poll, write the current time to `TRV_ESP_LastSeen` so that the CCU
  can detect a silent ESP and fall back.

Restrict the Script API in the CCU firewall to the ESP's IP address and use
authentication.

## Notes and limitations

- **Start-up.** CCU programs have no "on system start" trigger. After a reboot
  the script runs within 5 minutes. The WHS2 keeps its relay state during a
  CCU reboot.
- **Timing.** The script runs every 5 minutes, so `TRV_Summer_Delay` and
  ventilation react with up to 5 minutes of delay.
- **Room names.** Default CCU room names such as `${roomKitchen}` are shown
  without `${ }` (for example `roomKitchen`). Rename the rooms in the CCU to
  get readable names in `TRV_Demand_Rooms`.
- **Outdoor temperature age.** The age check uses the timestamp of
  `TRV_Outdoor_Temp`. If your setup does not update the timestamp when the
  same value is written again, and summer mode `Auto` falls back to `Off`
  during long periods of steady temperature, set `OUTDOOR_MAX_AGE_MIN = 0`.
- **Device names.** If you read names over the Script API, avoid `;`, `|`, and
  non-ASCII characters in TRV device names.
- **Variable creation.** `create_system_variables.hm` uses the
  `dom.CreateObject(OT_VARDP)` method, which is widely used but not officially
  documented. Verify the created variables in the WebUI.
- **Single controller.** Make sure only one controller drives the boiler at a
  time. Use `TRV_Boiler_Control`; do not run two independent automations.

## License

GPL-3.0, the same as the rest of this repository. See [LICENSE](../LICENSE).
