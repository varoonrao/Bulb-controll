# Run the gyro web app on your Android phone

Browsers can't talk to the bulb directly, because Tuya's LAN protocol is encrypted raw TCP and web
pages can't open raw sockets. So a tiny Python server runs **on the phone itself** inside Termux,
and Chrome on the same phone opens `http://localhost:8000`. Chrome treats `localhost` as a secure
origin, so the gyroscope works without HTTPS.

```
 ┌──────────── Android phone ────────────┐
 │ Chrome  ──http://localhost:8000──▶ Termux: web.py ──Wi-Fi, TCP 6668──▶ 💡 Havells bulb
 │ (gyro)                              (tinytuya)                     │
 └───────────────────────────────────────┘
```

## 1. Install Termux

Install **Termux from F-Droid** (<https://f-droid.org/packages/com.termux/>). The Play Store build is outdated.

## 2. Install Python and get the code

```bash
pkg update
pkg install -y python python-cryptography git
pip install tinytuya flask

git clone https://github.com/varoonrao/Bulb-controll.git
cd Bulb-controll
git checkout claude/havel-smart-bulb-control-024lsd
```

`python-cryptography` comes from Termux's package repo, which saves you compiling it with Rust.

## 3. Configure the bulb

```bash
cp config.example.json config.json
nano config.json
```

`device_id` is already filled in (`d756e7d3b52f4847ba0xdi`, the "Virtual ID" shown in the app).
You still need the bulb's **local key**. Follow [SETUP.md](SETUP.md); you can run
`python -m tinytuya wizard` right here in Termux. Then find the bulb's IP:

```bash
python cli.py scan
python cli.py status        # should print {"is_on": ..., "brightness": ...}
```

## 4. Start the app

```bash
./start.sh
```

Open **Chrome → `http://localhost:8000`** and tap **Start gyro**.

Tip: in Chrome's menu tap **Add to Home screen**. It then opens full-screen like a normal app,
but the Termux server must be running.

## Gestures

| Gesture | Tilt mode (default) | Dial mode |
|---|---|---|
| Tilt left ↔ right | Colour (full hue wheel) | Saturation |
| Tilt forward ↔ back | Brightness | Brightness |
| Spin phone flat on table | — | Colour |
| Shake | Power on/off | Power on/off |
| Tap the orb | Lock/unlock current colour | same |

Buttons: **Power**, **Tilt/Dial** mode switch, **White** (warm white, locks gyro), **Sliders** (classic remote at `/remote`).

## Troubleshooting

- **Red dot / "Bulb error"**: run `python cli.py status` in Termux to see the real error, and check the IP, local key and `version` in SETUP.md.
- **Nothing happens when tilting**: you must open the page on the *same phone* via `localhost`. Over `http://192.168.x.x`, Chrome blocks motion sensors.
- **Server stops when the screen turns off**: `start.sh` calls `termux-wake-lock`. Also disable battery optimisation for Termux in Android settings.
- **Laggy colour**: the app sends at most ~6 updates/second because Tuya bulbs drop faster commands. Raise `SEND_EVERY` in `templates/gyro.html` to make it gentler.
