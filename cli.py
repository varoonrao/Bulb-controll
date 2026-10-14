#!/usr/bin/env python3
"""Command-line control for the Havells smart bulb.

Examples:
  python cli.py on
  python cli.py off
  python cli.py toggle
  python cli.py brightness 40
  python cli.py temp 20            # warm white
  python cli.py white 80 50        # brightness 80 %, neutral white
  python cli.py color "#ff0066"
  python cli.py rgb 255 120 0
  python cli.py scene night
  python cli.py status
  python cli.py scan               # find Tuya devices on your LAN
"""
import argparse
import json
import sys

from bulb import Bulb, SCENES


def main(argv=None):
    p = argparse.ArgumentParser(description="Control a Havells (Tuya) smart bulb over your LAN")
    sub = p.add_subparsers(dest="cmd", required=True)
    for c in ("on", "off", "toggle", "status", "scan"):
        sub.add_parser(c)
    sub.add_parser("brightness").add_argument("pct", type=int)
    sub.add_parser("temp", help="0 = warm, 100 = cool").add_argument("pct", type=int)
    w = sub.add_parser("white")
    w.add_argument("brightness", type=int)
    w.add_argument("temp", type=int, nargs="?", default=50)
    sub.add_parser("color").add_argument("hex")
    rgb = sub.add_parser("rgb")
    for c in ("r", "g", "b"):
        rgb.add_argument(c, type=int)
    sub.add_parser("scene", help=f"one of {', '.join(SCENES)} or a number").add_argument("name")
    args = p.parse_args(argv)

    if args.cmd == "scan":
        import tinytuya
        tinytuya.scan()
        return 0

    try:
        bulb = Bulb()
        if args.cmd == "status":
            print(json.dumps(bulb.status(), indent=2))
            return 0
        if args.cmd in ("on", "off", "toggle"):
            getattr(bulb, args.cmd)()
        elif args.cmd == "brightness":
            bulb.brightness(args.pct)
        elif args.cmd == "temp":
            bulb.temperature(args.pct)
        elif args.cmd == "white":
            bulb.white(args.brightness, args.temp)
        elif args.cmd == "color":
            bulb.hex_color(args.hex)
        elif args.cmd == "rgb":
            bulb.color(args.r, args.g, args.b)
        elif args.cmd == "scene":
            bulb.scene(args.name)
    except (RuntimeError, ValueError) as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    print("ok")
    return 0


if __name__ == "__main__":
    sys.exit(main())
