"""Тест: красит клавиатуру (VIA / QMK) в синий через raw HID."""
import subprocess
import sys

try:
    import hid
except ImportError:
    print("hidapi не найден, ставлю...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "hidapi"])
    import hid

VIA_USAGE_PAGE = 0xFF60
VIA_USAGE = 0x61


def find_via():
    for d in hid.enumerate():
        if d["usage_page"] == VIA_USAGE_PAGE and d["usage"] == VIA_USAGE:
            print(f"Нашёл: {d['manufacturer_string']} {d['product_string']} "
                  f"(VID {d['vendor_id']:04X}, PID {d['product_id']:04X})")
            return d["path"]
    raise SystemExit("VIA-клава не найдена. Закрой вкладку VIA в браузере и попробуй снова.")


def send(dev, *data):
    pkt = bytes([0x00, *data]) + bytes(32 - len(data))  # 0x00 — report id для винды
    dev.write(pkt)


dev = hid.device()
dev.open_path(find_via())

for ch in (3, 2):  # 3 = RGB Matrix, 2 = RGBLight — шлём в оба, лишний просто игнорится
    send(dev, 0x07, ch, 1, 200)       # яркость
    send(dev, 0x07, ch, 4, 170, 255)  # синий (hue=170, sat=255)

dev.close()
print("Готово — клава должна быть синей 🔵")
