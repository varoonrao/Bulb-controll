# Bulb-controll 💡

Control a **Havells smart bulb** (Glamax / Wi-Fi RGB range) directly over your home Wi-Fi from a
terminal or a phone-friendly web page, without going through the Havells cloud.

Havells Wi-Fi bulbs run **Tuya** firmware (they also pair with the *Tuya Smart* / *Smart Life*
apps), so they speak Tuya's local LAN protocol on TCP port 6668. This project wraps
[`tinytuya`](https://github.com/jasonacox/tinytuya) with a simple CLI and web remote.

## Quick start

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

cp config.example.json config.json   # then fill in device_id + local_key
python cli.py status
```

Getting the `device_id` and `local_key` is the only hard part. Follow
**[docs/SETUP.md](docs/SETUP.md)**, which takes about 15 minutes.

## CLI

```bash
python cli.py on | off | toggle
python cli.py brightness 40        # 0-100 %
python cli.py temp 20              # 0 = warm, 100 = cool white
python cli.py white 80 50          # brightness 80 %, neutral white
python cli.py color "#ff0066"      # hex colour
python cli.py rgb 255 120 0
python cli.py scene night          # night | read | work | leisure | <number>
python cli.py scan                 # find Tuya devices + IPs on your LAN
```

## 🌐 Deploy to Netlify (easiest)

Host the gyro app on Netlify and it controls the bulb through the Tuya cloud. There's nothing to
run on your phone; just open the URL. See **[docs/NETLIFY.md](docs/NETLIFY.md)**.

## 📱 Gyro web app (local, Android + Termux)

Tilt your phone to paint the room: tilt left/right for colour, forward/back for brightness, shake
to switch on/off, and tap the orb to lock a colour. There's also a *Dial* mode where you lay the
phone flat and spin it like a knob.

The server runs on the phone in **Termux** and you open `http://localhost:8000` in Chrome.
Full guide: **[docs/ANDROID.md](docs/ANDROID.md)**.

```bash
./start.sh              # or: python web.py  (serves on 0.0.0.0:8000)
```

- `/` is the gyro controller
- `/remote` has classic sliders, a colour picker and scenes (works from any device on your Wi-Fi)
- Set `APP_PIN=1234` before starting to require a PIN

## Files

| File | What it does |
|---|---|
| `bulb.py` | `Bulb` class: on/off, brightness, white temp, RGB, scenes |
| `cli.py` | Command-line interface |
| `web.py` | Local Flask server for the web app (LAN control) |
| `netlify/functions/bulb.mjs` | Netlify Function: same `/api/*` routes via the Tuya cloud |
| `netlify.toml` | Netlify config |
| `public/index.html` | Gyro controller (`/`) |
| `public/remote.html` | Slider remote (`/remote`) |
| `public/static/` | Shared API client, PWA manifest and icon |
| `docs/NETLIFY.md` | Netlify deployment |
| `start.sh` | Launcher for Termux |
| `docs/ANDROID.md` | Running it on your phone |
| `docs/SETUP.md` | Getting the local key, plus reverse-engineering notes if your bulb isn't Tuya |

## Security

`config.json` contains your bulb's **local key**. Anyone with it on your LAN can control the bulb.
It is git-ignored, so keep it that way. The local server has no PIN unless you set `APP_PIN`.
The Netlify function refuses to run without `APP_PIN`, and its Tuya secrets live only in Netlify
environment variables.
