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

## Web remote

```bash
python web.py           # serves on 0.0.0.0:8000
```

Open `http://<your-computer-ip>:8000` on your phone (it must be on the same Wi-Fi). The page has
power, brightness, warm/cool, a colour picker and scene buttons.

## Files

| File | What it does |
|---|---|
| `bulb.py` | `Bulb` class: on/off, brightness, white temp, RGB, scenes |
| `cli.py` | Command-line interface |
| `web.py` + `templates/index.html` | Flask web remote |
| `docs/SETUP.md` | Getting the local key, plus reverse-engineering notes if your bulb isn't Tuya |

## Security

`config.json` contains your bulb's **local key**. Anyone with it on your LAN can control the bulb.
It is git-ignored, so keep it that way. The web remote has **no authentication**, so only run it
on a trusted home network.
