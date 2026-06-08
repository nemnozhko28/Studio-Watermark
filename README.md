# 🎬 Telegram Watermark Bot

Telegram-бот для добавления текстовых водяных знаков на видео. Поддерживает файлы до **2 ГБ**, асинхронную очередь задач и гибкие настройки водяного знака.

---

## ✨ Возможности

- **Водяной знак** — текст, шрифт, размер, цвет, прозрачность, позиция
- **Чередование позиций** — переключение между несколькими позициями через заданный интервал
- **Большие файлы** — до 2 ГБ через Pyrogram (без лимита Telegram Bot API в 20 МБ)
- **Потоковая обработка** — FFmpeg без загрузки в RAM
- **Очередь задач** — несколько пользователей одновременно, настраиваемый пул воркеров
- **Прогресс** — `Скачивание: 45%`, `Обработка: 70%`, `Загрузка результата: 30%`
- **Форвардинг оригиналов** в канал администратора
- **Поддерживаемые форматы**: mp4, mov, mkv, avi, webm

---

## 🚀 Быстрый старт (локально)

### 1. Клонировать репозиторий

```bash
git clone https://github.com/youruser/watermark-bot.git
cd watermark-bot
```

### 2. Создать виртуальное окружение

```bash
python3.11 -m venv .venv
source .venv/bin/activate
```

### 3. Установить зависимости

```bash
pip install -r requirements.txt
```

### 4. Настроить переменные окружения

```bash
cp .env.example .env
# Отредактируйте .env — заполните все переменные
nano .env
```

Получить данные:
- `BOT_TOKEN` — создать бота через [@BotFather](https://t.me/BotFather)
- `API_ID` / `API_HASH` — зарегистрировать приложение на [my.telegram.org](https://my.telegram.org)
- `ADMIN_ID` — ваш Telegram ID (узнать через [@userinfobot](https://t.me/userinfobot))
- `ADMIN_CHANNEL_ID` — ID канала (формат: `-1001234567890`); бот должен быть администратором

### 5. Скачать шрифты

```bash
bash scripts/download_fonts.sh
```

### 6. Запустить бота

```bash
python -m bot.main
```

---

## 🐳 Docker

```bash
docker build -t watermark-bot .
docker run --env-file .env watermark-bot
```

---

## 🚂 Railway (деплой)

### Вариант A — через GitHub

1. Залить проект на GitHub
2. В [Railway](https://railway.app) → **New Project → Deploy from GitHub**
3. Добавить **PostgreSQL** плагин (Railway создаст `DATABASE_URL` автоматически)
4. В настройках сервиса добавить переменные:
   ```
   BOT_TOKEN=...
   API_ID=...
   API_HASH=...
   ADMIN_ID=...
   ADMIN_CHANNEL_ID=...
   MAX_WORKERS=2
   ```
5. Railway обнаружит `Dockerfile` и запустит деплой автоматически

### Вариант B — Railway CLI

```bash
npm install -g @railway/cli
railway login
railway link
railway up
```

### Переменная DATABASE_URL

Railway автоматически выставляет `DATABASE_URL` в формате PostgreSQL. Бот подхватит его без дополнительных настроек.

---

## ⚙️ Структура проекта

```
bot/
├── handlers/          # aiogram роутеры (start, settings, video, admin)
├── keyboards/         # Inline-клавиатуры
├── services/          # FFmpeg, Pyrogram, очередь задач
├── database/          # SQLAlchemy async: подключение и запросы
├── models/            # ORM-модели (User, WatermarkSettings, Job)
├── middlewares/       # DbSessionMiddleware
├── states/            # FSM-состояния aiogram
├── utils/             # Вспомогательные утилиты
├── fonts/             # Шрифты TTF
├── temp/              # Временные файлы (авто-очистка)
├── logs/              # Лог-файлы
├── config.py          # Конфигурация из .env
└── main.py            # Точка входа
```

---

## 🗂 База данных

| Таблица | Описание |
|---------|----------|
| `users` | Telegram-пользователи |
| `watermark_settings` | Настройки водяного знака на пользователя |
| `jobs` | История задач обработки видео |

Поддерживаются **PostgreSQL** (продакшн) и **SQLite** (разработка).

---

## 🔧 Настройки водяного знака

| Параметр | Варианты |
|----------|----------|
| Шрифт | Montserrat-Bold, Arial, Roboto |
| Размер | 2%–20% от ширины видео |
| Цвет | white, black, red, green, blue, yellow, orange, gray |
| Прозрачность | 0.1–1.0 |
| Позиция | 9 позиций (3×3 сетка) |
| Чередование | Между несколькими позициями с интервалом |

---

## 🔑 Переменные окружения

| Переменная | Обязательная | Описание |
|------------|-------------|----------|
| `BOT_TOKEN` | ✅ | Токен Telegram-бота |
| `API_ID` | ✅ | Telegram API ID |
| `API_HASH` | ✅ | Telegram API Hash |
| `ADMIN_ID` | ✅ | Telegram ID администратора |
| `ADMIN_CHANNEL_ID` | ✅ | ID канала для форвардинга |
| `DATABASE_URL` | ✅ | Строка подключения к БД |
| `MAX_WORKERS` | ❌ | Кол-во воркеров (по умолчанию: 2) |

---

## 📋 Команды администратора

| Команда | Описание |
|---------|----------|
| `/admin` | Статистика бота |
| `/stats` | То же, что /admin |
| `/broadcast <текст>` | Рассылка всем пользователям |

---

## 🛡 Примечания по безопасности

- `.env` добавлен в `.gitignore` — никогда не коммитьте его
- Временные файлы автоматически удаляются после обработки
- Ошибки обработки логируются и не кладут бота

---

## 📝 Лицензия

MIT
