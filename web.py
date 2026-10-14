#!/usr/bin/env python3
"""Web app for the bulb.

  /        gyro controller: tilt your phone to change colour and brightness
  /remote  classic sliders and buttons

Run `python web.py` (on Android: inside Termux, see docs/ANDROID.md) and open
http://localhost:8000 in Chrome on the same phone.
"""
import os
import threading

from flask import Flask, jsonify, render_template, request

from bulb import Bulb

app = Flask(__name__)
_bulb = None
_lock = threading.Lock()  # the bulb accepts one TCP session at a time


def bulb():
    global _bulb
    if _bulb is None:
        _bulb = Bulb()
    return _bulb


@app.get("/")
def gyro():
    return render_template("gyro.html", name=_name())


@app.get("/remote")
def remote():
    return render_template("index.html", name=_name())


def _name():
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
        return jsonify(error=f"unknown action {action}"), 404
    return _run(handlers[action])


def _run(fn):
    try:
        with _lock:
            return jsonify(ok=True, result=fn(bulb()))
    except Exception as e:  # network errors from tinytuya, bad input, missing config
        global _bulb
        if not isinstance(e, (ValueError, KeyError)):
            _bulb = None  # reconnect on next request
        return jsonify(ok=False, error=str(e)), 502


if __name__ == "__main__":
    app.run(host=os.environ.get("HOST", "0.0.0.0"), port=int(os.environ.get("PORT", 8000)))
