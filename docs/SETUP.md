# Getting your bulb's device ID and local key

Tuya devices encrypt LAN traffic with a per-device **local key**. You get it once from Tuya's
developer cloud, and after that everything runs locally.

## 1. Pair the bulb with the *Smart Life* (or *Tuya Smart*) app

Havells bulbs are usually set up with the Havells app (DigiTap / Havells Sync), and those accounts
are **not** visible to Tuya's developer cloud. So you need to:

1. Remove the bulb from the Havells app.
2. Reset the bulb: switch it off and on 3–5 times until it blinks quickly.
3. Add it in the **Smart Life** app (Android/iOS) on your **2.4 GHz** Wi-Fi.
4. Check that you can control it from Smart Life.

> ⚠️ Re-pairing the bulb with *any* app generates a **new local key**. If you later re-pair it, repeat step 3 below.

## 2. Create a free Tuya IoT developer project

1. Sign up at <https://platform.tuya.com>.
2. **Cloud → Development → Create Cloud Project**
   - Development method: *Smart Home*
   - Data center: **India** (or whichever region your Smart Life account uses)
3. In the project, open **Devices → Link App Account → Add App Account** and scan the QR code
   with Smart Life (*Me → scan icon*). Your bulb should now be listed.
4. Note the **Access ID** and **Access Secret** from the project *Overview*.
5. Under **Service API**, make sure *IoT Core* and *Authorization* are subscribed (the free trial is enough).

## 3. Run the tinytuya wizard

From this repo, with the venv active:

```bash
python -m tinytuya wizard
```

Enter the Access ID, Access Secret, a device ID from the Tuya console (any one of yours), and
your region (`in` for India). The wizard writes `devices.json` (git-ignored) with entries like:

```json
{ "name": "Room Bulb", "id": "bf12ab34cd56ef78gh90", "key": "a1b2c3d4e5f6g7h8", "ip": "192.168.1.42", "version": "3.3" }
```

Copy `id`, `key`, `ip` and `version` into `config.json`:

```json
{
  "name": "Room Bulb",
  "device_id": "bf12ab34cd56ef78gh90",
  "local_key": "a1b2c3d4e5f6g7h8",
  "ip": "192.168.1.42",
  "version": 3.3
}
```

`"ip": "Auto"` also works because tinytuya then finds the bulb by broadcast. A fixed IP (set a DHCP
reservation on your router) is faster and more reliable.

## 4. Test it

```bash
python cli.py status
python cli.py color "#00ffaa"
```

### Troubleshooting

| Symptom | Fix |
|---|---|
| `Network Error: Unable to Connect` (901) | Wrong IP, or the bulb is on a different subnet/guest Wi-Fi. Run `python cli.py scan`. |
| `Check device key or version` (914) | Wrong local key (did you re-pair?) or wrong `version`. Try 3.3, 3.4, then 3.5. |
| Works from the phone app but times out here | Close the Smart Life app. Some bulbs allow only one LAN session at a time. |
| Colours look wrong / scenes do nothing | Run `python cli.py status` and check which DPs the bulb reports. Older firmware uses DPs 1–5 instead of 20–26; tinytuya auto-detects this. |

---

## If your bulb is *not* Tuya-based: reverse engineering it

If the bulb refuses to pair with Smart Life, it may use a different stack (for example a
Bluetooth-mesh-only model or a Havells-specific cloud). Then you need to work out what the
official app does. That's what the viral "point an AI agent at the app and reverse engineer it" posts do.

**[REA, Reverse Engineer Anything](https://github.com/morluto/rea)** is an open-source CLI + MCP
server that lets coding agents like Claude Code analyse APKs, binaries and websites. A typical flow:

1. **Get the app**: pull the Havells DigiTap APK from your phone:
   `adb shell pm path com.havells.digitap` then `adb pull <path> havells.apk`.
2. **Decompile**: point REA (or `jadx` directly) at the APK and ask the agent to find
   - which SDK it uses (look for `com.tuya`, `com.thingclips`, `telink`, `mesh` packages)
   - the API base URLs and auth flow
   - how commands like "set colour" are encoded (data-point IDs, JSON shape, BLE characteristic UUIDs)
3. **Observe traffic**:
   - Wi-Fi: `tinytuya scan` / Wireshark on port 6666–6668 UDP+TCP.
   - BLE: nRF Connect app to list services/characteristics, or Android's *Bluetooth HCI snoop log*
     (Developer options) while you use the official app, then open the log in Wireshark.
4. **Replay**: write the found commands into `bulb.py`, using `bleak` for BLE or `requests` for a cloud API.

Only do this on devices you own. Most Havells Wi-Fi bulbs are Tuya `ThingClips` devices, so in
practice steps 1–3 above are usually enough and the reverse engineering confirms it.
