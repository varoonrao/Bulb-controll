#!/usr/bin/env python3
"""Local server for the bulb web app (LAN control via tinytuya).

  /         gyro controller: tilt your phone to change colour and brightness
  /remote   classic sliders and buttons

The pages live in public/ and are the same ones deployed to Netlify, where
netlify/functions/bulb.mjs serves /api/* through the Tuya cloud instead.

Run `python web.py` (on Android: inside Termux, see docs/ANDROID.md) and open
http://localhost:8000 in Chrome on the same phone. Set APP_PIN to require a PIN.
"""
import hmac
import os
import threading

from flask import Flask, jsonify, request, send_from_directory

from bulb import Bulb

PUBLIC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "public")
app = Flask(__name__, static_folder=os.path.join(PUBLIC, "static"), static_url_path="/static")
_bulb = None
_lock = threading.Lock()  # the bulb accepts one TCP session at a time


def bulb():
    global _bulb
    if _bulb is None:
        _bulb = Bulb()
    return _bulb


@app.get("/")
def gyro():
    return send_from_directory(PUBLIC, "index.html")


@app.get("/remote")
def remote():
    return send_from_directory(PUBLIC, "remote.html")


@app.before_request
def check_pin():
    pin = os.environ.get("APP_PIN")
    if pin and request.path.startswith("/api/"):
        if not hmac.compare_digest(request.headers.get("X-Bulb-Pin", ""), pin):
            return jsonify(ok=False, error="PIN required"), 401


@app.get("/api/info")
def info():
    return _run(lambda b: None, extra={"backend": "local", "name": bulb_name()})


def bulb_name():
    try:
        return bulb().name
    except Exception:
        return "Bulb"


@app.get("/api/status")
def status():
    return _run(lambda b: b.status())


@app.post("/api/<action>")
def action(action):
    data = request.get_json(silent=True) or {}
    handlers = {
        "on": lambda b: b.on(),
        "off": lambda b: b.off(),
        "toggle": lambda b: b.toggle(),
        "brightness": lambda b: b.brightness(data["value"]),
        "temp": lambda b: b.temperature(data["value"]),
        "white": lambda b: b.white(data.get("brightness", 100), data.get("temp", 50)),
        "color": lambda b: b.hex_color(data["hex"]),
        "hsv": lambda b: b.hsv(data["h"], data.get("s", 100), data.get("v", 100)),
        "scene": lambda b: b.scene(data["name"]),
    }
    if action not in handlers:
        return jsonify(ok=False, error=f"unknown action {action}"), 404
    return _run(handlers[action])


def _run(fn, extra=None):
    global _bulb
    try:
        with _lock:
            return jsonify(ok=True, result=fn(bulb()), **(extra or {}))
    except Exception as e:  # network errors from tinytuya, bad input, missing config
        if not isinstance(e, (ValueError, KeyError)):
            _bulb = None  # reconnect on next request
        return jsonify(ok=False, error=str(e)), 502


if __name__ == "__main__":
    app.run(host=os.environ.get("HOST", "0.0.0.0"), port=int(os.environ.get("PORT", 8000)))
