"""Telegram-бот: подсветка клавы и компа кнопками. Запуск: python bot.py

.env рядом:
    BOT_TOKEN=123456:ABC...
    ALLOWED_USER_ID=123456789
"""
import subprocess
import sys
import time
from functools import partial
from pathlib import Path

from telegram import InlineKeyboardButton as Btn, InlineKeyboardMarkup, ReplyKeyboardMarkup, Update
from telegram.ext import Application, CallbackQueryHandler, CommandHandler, ContextTypes, MessageHandler, filters

import light
import pc
from colors import COLORS, EMOJI, PRESETS

PC_ONLY = dict(exclude=("KEYBOARD", "HEADSET"))
HEADSET_ONLY = dict(only=("HEADSET",))

# ключ: (название, функция покраски, функция выключения)
DEVICES = {
    "kb": ("⌨️ Клава", light.set_rgb, light.off),
    "pc": ("🖥 Комп", partial(pc.set_rgb, **PC_ONLY), partial(pc.off, **PC_ONLY)),
    "hs": ("🎧 Наушники", partial(pc.set_rgb, **HEADSET_ONLY), partial(pc.off, **HEADSET_ONLY)),
}
TARGETS = {key: [key] for key in DEVICES} | {"all": list(DEVICES)}

# последнее состояние каждого устройства (чтобы яркость и "Вкл" помнили цвет)
state = {key: {"color": "белый", "brightness": 100} for key in DEVICES}


def load_env():
    env = {}
    path = Path(__file__).with_name(".env")
    if path.exists():
        for line in path.read_text(encoding="utf-8").splitlines():
            if "=" in line and not line.strip().startswith("#"):
                k, v = line.split("=", 1)
                env[k.strip()] = v.strip()
    return env


ENV = load_env()
TOKEN = ENV.get("BOT_TOKEN")
ALLOWED_ID = int(ENV["ALLOWED_USER_ID"]) if ENV.get("ALLOWED_USER_ID") else None


# ---------- действия ----------

def apply(dev_keys, color=None, brightness=None, turn_off=False):
    """Применяет к списку устройств. Возвращает строку с ошибками (или пустую)."""
    errors = []
    for key in dev_keys:
        st = state[key]
        if color:
            st["color"] = color
        if brightness is not None:
            st["brightness"] = brightness
        name, set_rgb, turn_off_fn = DEVICES[key]
        try:
            if turn_off:
                turn_off_fn()
            else:
                set_rgb(COLORS[st["color"]], st["brightness"])
        except Exception as e:
            errors.append(f"{DEVICES[key][0]}: {e}")
    return "\n".join(errors)


def status_text():
    lines = []
    for key, (name, *_) in DEVICES.items():
        st = state[key]
        lines.append(f"{name}: {EMOJI[st['color']]} {st['color']}, {st['brightness']}%")
    return "\n".join(lines)


# ---------- клавиатуры ----------

# нижнее меню (кнопки под полем ввода). Новые функции — добавляй сюда кнопку
# и обработчик в BOTTOM_ACTIONS ниже
BTN_LIGHT = "💡 Подсветка"
BTN_BOT = "⚙️ Бот"
BOTTOM_MENU = ReplyKeyboardMarkup(
    [[BTN_LIGHT, BTN_BOT]],
    resize_keyboard=True,
    is_persistent=True,
)


def main_menu():
    return InlineKeyboardMarkup([
        [Btn("⌨️ Клава", callback_data="t:kb"), Btn("🖥 Комп", callback_data="t:pc"), Btn("🎧 Наушники", callback_data="t:hs")],
        [Btn("🔗 Всё сразу", callback_data="t:all")],
        [Btn("⭐ Пресеты", callback_data="presets")],
        [Btn("💡 Вкл", callback_data="on:all"), Btn("🌑 Выкл", callback_data="off:all")],
    ])


def target_menu(t):
    names = list(COLORS)
    rows = [
        [Btn(f"{EMOJI[n]} {n}", callback_data=f"c:{t}:{n}") for n in names[i:i + 3]]
        for i in range(0, len(names), 3)
    ]
    rows.append([Btn(f"{p}%", callback_data=f"b:{t}:{p}") for p in (25, 50, 75, 100)])
    rows.append([Btn("💡 Вкл", callback_data=f"on:{t}"), Btn("🌑 Выкл", callback_data=f"off:{t}")])
    rows.append([Btn("⬅️ Назад", callback_data="menu")])
    return InlineKeyboardMarkup(rows)


def bot_menu():
    return InlineKeyboardMarkup([[Btn("🔄 Перезапустить", callback_data="restart")]])


def presets_menu():
    rows = [[Btn(name, callback_data=f"p:{i}")] for i, name in enumerate(PRESETS)]
    rows.append([Btn("⬅️ Назад", callback_data="menu")])
    return InlineKeyboardMarkup(rows)


# ---------- хендлеры ----------

def allowed(update: Update) -> bool:
    uid = update.effective_user.id
    print(f"[бот] сообщение от id {uid}")
    return ALLOWED_ID is not None and uid == ALLOWED_ID


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not allowed(update):
        await update.message.reply_text(
            f"Твой id: {update.effective_user.id}\n"
            "Если это ты, хозяин, — впиши его в .env как ALLOWED_USER_ID и перезапусти бота."
        )
        return
    await update.message.reply_text("Меню внизу 👇", reply_markup=BOTTOM_MENU)
    await show_light(update, context)


async def show_light(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(status_text(), reply_markup=main_menu())


async def show_bot(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("⚙️ Управление ботом", reply_markup=bot_menu())


# текст кнопки нижнего меню -> что делать
BOTTOM_ACTIONS = {
    BTN_LIGHT: show_light,
    BTN_BOT: show_bot,
}


def spawn_new_bot(chat_id):
    """Запускает новую копию бота отдельным процессом (без окна)."""
    flags = 0
    if sys.platform == "win32":
        flags = subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP
    subprocess.Popen(
        [sys.executable, str(Path(__file__)), "--restarted", str(chat_id)],
        cwd=Path(__file__).parent,
        creationflags=flags,
        stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    )


async def on_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if not allowed(update):
        await query.answer("нет доступа")
        return

    data = query.data
    if data == "restart":
        await query.answer()
        await query.edit_message_text("🔄 Перезапускаюсь...")
        spawn_new_bot(query.message.chat_id)
        context.application.stop_running()  # старый процесс завершится сам
        return

    kind, *args = data.split(":")
    error = ""
    markup = main_menu()

    if kind == "menu":
        pass
    elif kind == "presets":
        markup = presets_menu()
    elif kind == "t":
        markup = target_menu(args[0])
    elif kind == "c":
        t, color = args
        error = apply(TARGETS[t], color=color)
        markup = target_menu(t)
    elif kind == "b":
        t, value = args
        error = apply(TARGETS[t], brightness=int(value))
        markup = target_menu(t)
    elif kind in ("on", "off"):
        t = args[0]
        error = apply(TARGETS[t], turn_off=(kind == "off"))
        markup = target_menu(t) if t != "all" else main_menu()
    elif kind == "p":
        preset = list(PRESETS.values())[int(args[0])]
        errors = [apply([key], color=c, brightness=b) for key, (c, b) in preset.items()]
        error = "\n".join(e for e in errors if e)
        markup = presets_menu()

    await query.answer()
    text = status_text() + (f"\n\n⚠️ {error}" if error else "")
    try:
        await query.edit_message_text(text, reply_markup=markup)
    except Exception:
        pass  # "message is not modified" — текст не поменялся, это ок


async def on_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Текстом тоже можно: 'синий', 'красный 50', 'off'."""
    if not allowed(update):
        return
    action = BOTTOM_ACTIONS.get(update.message.text)
    if action:
        await action(update, context)
        return
    parts = update.message.text.lower().split()
    cmd = parts[0]
    value = int(parts[1]) if len(parts) > 1 and parts[1].isdigit() else None
    if cmd == "off":
        error = apply(TARGETS["all"], turn_off=True)
    elif cmd == "on":
        error = apply(TARGETS["all"])
    elif cmd in COLORS:
        error = apply(TARGETS["all"], color=cmd, brightness=value)
    else:
        error = f"Не знаю '{cmd}'"
    await update.message.reply_text(status_text() + (f"\n\n⚠️ {error}" if error else ""), reply_markup=main_menu())


def main():
    # запуск без окна (pythonw) — консоли нет, пишем лог в файл
    if sys.stdout is None:
        log = open(Path(__file__).with_name("bot.log"), "a", encoding="utf-8", buffering=1)
        sys.stdout = sys.stderr = log

    if not TOKEN:
        raise SystemExit("Нет BOT_TOKEN в .env")

    # запущены кнопкой перезапуска: даём старому процессу закрыться и потом отчитываемся
    restarted_chat = None
    if len(sys.argv) > 2 and sys.argv[1] == "--restarted":
        restarted_chat = int(sys.argv[2])
        time.sleep(3)

    async def post_init(app):
        if restarted_chat:
            await app.bot.send_message(restarted_chat, "✅ Бот перезапущен", reply_markup=BOTTOM_MENU)

    while True:  # при старте винды интернет может ещё не подняться — пробуем снова
        try:
            app = Application.builder().token(TOKEN).post_init(post_init).build()
            app.add_handler(CommandHandler("start", start))
            app.add_handler(CallbackQueryHandler(on_button))
            app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, on_text))
            print(f"[{time.strftime('%H:%M:%S')}] Бот запущен. Ctrl+C — остановить")
            # после перезапуска выкидываем старые апдейты, чтобы не словить "перезапуск" повторно
            app.run_polling(drop_pending_updates=restarted_chat is not None)
            break  # вышли нормально (Ctrl+C)
        except Exception as e:
            print(f"[{time.strftime('%H:%M:%S')}] Ошибка: {e!r}, перезапуск через 15 сек")
            time.sleep(15)


if __name__ == "__main__":
    main()
