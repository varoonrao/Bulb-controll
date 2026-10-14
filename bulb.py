"""Local LAN control for a Havells (Tuya-based) Wi-Fi smart bulb.

Havells Glamax bulbs run Tuya firmware, so they speak the Tuya local
protocol on TCP port 6668. Once you have the device id + local key
(see docs/SETUP.md) you can control the bulb directly with no cloud.
"""
import json
import os

import tinytuya

CONFIG_PATH = os.environ.get("BULB_CONFIG", os.path.join(os.path.dirname(__file__), "config.json"))

SCENES = {"night": 1, "read": 2, "work": 3, "leisure": 4}


def load_config(path=CONFIG_PATH):
    if not os.path.exists(path):
        raise RuntimeError(
            f"Missing {path}. Copy config.example.json to config.json and fill in "
            "device_id / local_key (see docs/SETUP.md)."
        )
    with open(path) as f:
        return json.load(f)


class Bulb:
    def __init__(self, cfg=None):
        cfg = cfg or load_config()
        self.name = cfg.get("name", "Bulb")
        ip = cfg.get("ip") or "Auto"
        self.dev = tinytuya.BulbDevice(
            dev_id=cfg["device_id"],
            address=ip,
            local_key=cfg["local_key"],
            version=float(cfg.get("version", 3.3)),
        )
        self.dev.set_socketTimeout(5)
        self.dev.set_socketRetryLimit(2)
        # keep one TCP session open so rapid gyro updates don't pay a handshake each time
        self.dev.set_socketPersistent(True)

    @staticmethod
    def _check(result):
        if isinstance(result, dict) and "Error" in result:
            raise RuntimeError(f"{result.get('Error')} (code {result.get('Err')}): {result.get('Payload')}")
        return result

    def status(self):
        return self._check(self.dev.state())

    def on(self):
        return self._check(self.dev.turn_on())

    def off(self):
        return self._check(self.dev.turn_off())

    def toggle(self):
        return self.off() if self.status().get("is_on") else self.on()

    def brightness(self, pct):
        return self._check(self.dev.set_brightness_percentage(_clamp(pct)))

    def temperature(self, pct):
        """0 = warmest, 100 = coolest white."""
        return self._check(self.dev.set_colourtemp_percentage(_clamp(pct)))

    def white(self, brightness=100, temp=50):
        return self._check(self.dev.set_white_percentage(_clamp(brightness), _clamp(temp)))

    def color(self, r, g, b):
        return self._check(self.dev.set_colour(int(r), int(g), int(b)))

    def hsv(self, h, s=100, v=100):
        """h in degrees 0-360, s and v in percent 0-100."""
        h = (float(h) % 360) / 360
        return self._check(self.dev.set_hsv(h, _clamp(s) / 100, max(1, _clamp(v)) / 100))

    def hex_color(self, value):
        r, g, b = parse_hex(value)
        return self.color(r, g, b)

    def scene(self, name_or_num):
        num = SCENES.get(str(name_or_num).lower(), name_or_num)
        return self._check(self.dev.set_scene(int(num)))


def _clamp(v, lo=0, hi=100):
    return max(lo, min(hi, int(v)))


def parse_hex(value):
    value = value.lstrip("#")
    if len(value) != 6:
        raise ValueError("Colour must look like #ff8800")
    return tuple(int(value[i:i + 2], 16) for i in (0, 2, 4))
