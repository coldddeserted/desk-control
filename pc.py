"""Подсветка компа через OpenRGB (должен быть запущен с включённым SDK Server).

Консоль:
    python pc.py синий
    python pc.py красный 50
    python pc.py off
    python pc.py list      # показать, что OpenRGB видит
"""
import sys

from colors import COLORS

HOST, PORT = "127.0.0.1", 6742


def _client():
    try:
        from openrgb import OpenRGBClient
    except ImportError:
        raise RuntimeError("Нет openrgb-python: pip install -r requirements.txt")
    try:
        return OpenRGBClient(HOST, PORT, name="desk-control")
    except Exception:
        raise RuntimeError("OpenRGB не отвечает — запусти его и включи SDK Server")


def _devices(client, only=None, exclude=("KEYBOARD",)):
    """only / exclude — типы устройств OpenRGB: MOTHERBOARD, HEADSET, KEYBOARD, ..."""
    result = []
    for d in client.devices:
        kind = d.type.name
        if only and kind not in only:
            continue
        if kind in exclude:
            continue
        result.append(d)
    return result


def set_rgb(rgb, brightness=100, only=None, exclude=("KEYBOARD",)):
    from openrgb.utils import RGBColor
    k = max(0, min(100, brightness)) / 100
    color = RGBColor(*(round(c * k) for c in rgb))
    client = _client()
    try:
        for dev in _devices(client, only, exclude):
            try:
                dev.set_mode("direct")
            except Exception:
                pass  # у некоторых нет direct — просто красим
            dev.set_color(color)
    finally:
        client.disconnect()


def off(only=None, exclude=("KEYBOARD",)):
    set_rgb((0, 0, 0), 100, only, exclude)


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return
    cmd = sys.argv[1].lower()
    if cmd == "list":
        client = _client()
        for d in client.devices:
            print(f"- {d.name} ({d.type.name}), светодиодов: {len(d.leds)}")
        client.disconnect()
    elif cmd == "off":
        off()
    elif cmd in COLORS:
        set_rgb(COLORS[cmd], int(sys.argv[2]) if len(sys.argv) > 2 else 100)
    else:
        raise SystemExit(f"Не знаю '{cmd}'")
    print("ок")


if __name__ == "__main__":
    main()
