# desk-control

Управление своим сетапом через Telegram-бота. Сейчас — RGB-подсветка:

- ⌨️ клавиатура на QMK/VIA — напрямую через raw HID (`light.py`)
- 🖥 материнка / ARGB и 🎧 наушники — через [OpenRGB](https://openrgb.org) SDK (`pc.py`)
- 📱 бот с кнопками: цвета, яркость, пресеты, вкл/выкл, перезапуск (`bot.py`)

## Установка

```
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

Создай `.env` рядом с `bot.py`:

```
BOT_TOKEN=токен_от_BotFather
ALLOWED_USER_ID=твой_telegram_id
```

Бот отвечает только пользователю с `ALLOWED_USER_ID`. Свой id бот пришлёт в ответ на `/start`, если он ещё не задан.

Для компа и наушников должен быть запущен OpenRGB с сервером на `127.0.0.1:6742`.

## Запуск

- `python bot.py` — в консоли
- `start_bot.cmd` — в фоне без окна (можно положить в `shell:startup` для автозапуска)
- `restart_bot.cmd` / `stop_bot.cmd` — перезапуск / остановка
- логи фонового режима — `bot.log`

Из консоли без бота:

```
python light.py синий 50
python pc.py list
python pc.py красный
```

## Настройка

Цвета и пресеты — в `colors.py`.
