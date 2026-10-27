"""Подсветка клавы (VIA / QMK через raw HID).

Консоль:
    python light.py синий
    python light.py красный 50     # яркость в %
    python light.py off
"""
import colorsys
import sys

import hid

from colors import COLORS

VIA_USAGE_PAGE = 0xFF60
VIA_USAGE = 0x61
CHANNELS = (3, 2)  # 3 = RGB Matrix, 2 = RGBLight


def _open():
    for d in hid.enumerate():
        if d["usage_page"] == VIA_USAGE_PAGE and d["usage"] == VIA_USAGE:
            dev = hid.device()
            dev.open_path(d["path"])
            return dev
    raise RuntimeError("Клава не найдена (закрой вкладку VIA в браузере)")


def _send(dev, *data):
    dev.write(bytes([0x00, *data]) + bytes(32 - len(data)))


def set_rgb(rgb, brightness=100):
    """rgb — (R, G, B) 0..255, brightness — 0..100 %."""
    h, s, _ = colorsys.rgb_to_hsv(*(c / 255 for c in rgb))
    hue, sat = round(h * 255), round(s * 255)
    value = round(max(0, min(100, brightness)) * 255 / 100)
    dev = _open()
    try:
        for ch in CHANNELS:
            _send(dev, 0x07, ch, 4, hue, sat)
            _send(dev, 0x07, ch, 1, value)
    finally:
        dev.close()


def off():
    dev = _open()
    try:
        for ch in CHANNELS:
            _send(dev, 0x07, ch, 1, 0)
    finally:
        dev.close()


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        print("Цвета:", ", ".join(COLORS))
        return
    cmd = sys.argv[1].lower()
    if cmd == "off":
        off()
    elif cmd in COLORS:
        set_rgb(COLORS[cmd], int(sys.argv[2]) if len(sys.argv) > 2 else 100)
    else:
        raise SystemExit(f"Не знаю '{cmd}'. Есть: off, {', '.join(COLORS)}")
    print("ок")


if __name__ == "__main__":
    main()
