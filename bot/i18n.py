"""
Translations for the Watermark Bot.
Usage:  from bot.i18n import t
        t("welcome", lang, name="Alice")
"""
from __future__ import annotations

_T: dict[str, dict[str, str]] = {
    "ru": {
        # ── Main menu ────────────────────────────────────────────────────────
        "welcome":          "👋 Привет, <b>{name}</b>!\n\nЯ помогу добавить текстовый водяной знак на ваше видео.\nВыберите действие:",
        "what_next":        "Что дальше?",
        "btn_add_video":    "🎥 Добавить видео",
        "btn_settings":     "⚙️ Настройки водяного знака",
        "btn_my_jobs":      "📂 Мои задачи",
        "btn_help":         "ℹ️ Помощь",
        "btn_done":         "✅ Готово",
        "btn_back":         "◀️ Назад",
        "btn_cancel":       "❌ Отмена",
        "btn_start_proc":   "▶️ Начать обработку",

        # ── Help ─────────────────────────────────────────────────────────────
        "help_text": (
            "ℹ️ <b>Как пользоваться ботом:</b>\n\n"
            "1️⃣ Откройте <b>⚙️ Настройки водяного знака</b> и задайте текст, шрифт, цвет, позицию.\n"
            "2️⃣ Нажмите <b>🎥 Добавить видео</b> и отправьте файл.\n"
            "3️⃣ Бот обработает видео и вернёт вам результат.\n\n"
            "<b>Поддерживаемые форматы:</b> mp4, mov, mkv, avi, webm\n"
            "<b>Максимальный размер:</b> до 2 ГБ\n\n"
            "📂 В разделе <b>Мои задачи</b> можно посмотреть историю обработок."
        ),

        # ── Jobs ─────────────────────────────────────────────────────────────
        "no_jobs":       "📂 <b>Мои задачи</b>\n\nУ вас пока нет обработанных видео.",
        "jobs_header":   "📂 <b>Мои задачи (последние 10):</b>\n",
        "job_status_pending":     "⏳",
        "job_status_downloading": "📥",
        "job_status_processing":  "⚙️",
        "job_status_uploading":   "📤",
        "job_status_done":        "✅",
        "job_status_failed":      "❌",

        # ── Settings ─────────────────────────────────────────────────────────
        "settings_header":      "⚙️ <b>Настройки водяного знака</b>\n\n",
        "settings_text_row":    "✏️ Текст логотипа: <b>{v}</b>\n",
        "settings_font_row":    "🔤 Шрифт: <b>{v}</b>\n",
        "settings_size_row":    "📏 Размер: <b>{v}</b>\n",
        "settings_color_row":   "🎨 Цвет: <b>{v}</b>\n",
        "settings_opacity_row": "💧 Прозрачность: <b>{v}</b>\n",
        "settings_pos_row":     "📍 Позиция: <b>{v}</b>\n",
        "settings_alt_row":     "🔄 Чередование: <b>{v}</b>\n",
        "settings_delay_row":   "⏱ Задержка: <b>{v}</b>",
        "alt_on":               "вкл",
        "alt_off":              "выкл",
        "delay_none":           "нет",
        "delay_sec":            "{n} сек.",
        "settings_done_msg":    "✅ Настройки сохранены!\n\nТеперь отправьте видео для обработки.",
        "settings_done_toast":  "Настройки сохранены!",

        # Settings buttons
        "btn_text":         "✏️ Текст: {v}",
        "btn_font":         "🔤 Шрифт: {v}",
        "btn_size":         "📏 Размер: {v}",
        "btn_color":        "🎨 Цвет: {v}",
        "btn_opacity":      "💧 Прозрачность: {v}",
        "btn_position":     "📍 Позиция: {v}",
        "btn_alternation":  "🔄 Чередование: {v}",
        "btn_delay":        "⏱ Задержка: {v} сек.",
        "btn_language":     "🌐 Язык: 🇷🇺 Русский",

        # Set-text flow
        "enter_text":    "✏️ Введите текст водяного знака:",
        "text_too_long": "⚠️ Текст слишком длинный. Максимум 200 символов.",
        "text_saved":    "✅ Текст сохранён: <b>{v}</b>",

        # Set-font
        "choose_font":  "🔤 Выберите шрифт:",
        "font_saved":   "Шрифт: {v}",

        # Set-size
        "choose_size":  "📏 Выберите размер текста:",
        "size_saved":   "Размер: {v}",

        # Set-color
        "choose_color": "🎨 Выберите цвет:",
        "color_saved":  "Цвет: {v}",

        # Set-opacity
        "choose_opacity": "💧 Выберите прозрачность:",
        "opacity_saved":  "Прозрачность: {v}%",

        # Set-position
        "choose_position": "📍 Выберите позицию водяного знака:",
        "position_saved":  "Позиция: {v}",

        # Set-language
        "choose_language": "🌐 Выберите язык / Choose language:",
        "lang_ru":         "🇷🇺 Русский",
        "lang_en":         "🇬🇧 English",
        "language_saved":  "✅ Язык установлен: Русский",

        # Alternation
        "alt_header": (
            "🔄 <b>Чередование позиций</b>\n\n"
            "При включении водяной знак переключается между позициями через заданный интервал."
        ),
        "alt_enable":      "🟢 Включить чередование",
        "alt_disable":     "🔴 Выключить чередование",
        "alt_disabled":    "Чередование выключено",
        "enter_interval":  "⏱ Введите интервал чередования в секундах.\n\nНапример: <code>5</code>",
        "interval_set":    "✅ Интервал: {n} сек.\n\n📍 Выберите позицию 1:",
        "choose_pos1":     "📍 Позиция 1: <b>{pos}</b>\n\n📐 Введите смещение <b>X Y</b> в пикселях.\nПример: <code>0 0</code>",
        "pos1_saved":      "✅ Позиция 1: <b>{pos}</b> ({ox:+d}, {oy:+d})\n\n📍 Выберите позицию 2:",
        "choose_pos2":     "📍 Позиция 2: <b>{pos}</b>\n\n📐 Введите смещение X Y:",
        "alt_configured":  "✅ <b>Чередование настроено!</b>\n\n⏱ Интервал: <b>{n} сек.</b>\n📍 Позиция 1: <b>{p1}</b>\n📍 Позиция 2: <b>{p2}</b>",
        "bad_interval":    "⚠️ Введите целое число.",
        "bad_two_numbers": "⚠️ Два числа через пробел: <code>0 0</code>",
        "bad_integers":    "⚠️ Только целые числа.",
        "interval_zero":   "Чередование отключено.",

        # Delay
        "delay_header": (
            "⏱ <b>Задержка появления логотипа</b>\n\n"
            "Через сколько секунд появится водяной знак?\n\n"
            "<code>0</code> — сразу\n<code>5</code> — через 5 сек."
        ),
        "delay_saved":       "✅ Задержка: <b>{v}</b>",
        "delay_bad":         "⚠️ Введите целое число, например <code>5</code>.",
        "delay_negative":    "⚠️ Задержка не может быть отрицательной.",
        "delay_immediate":   "нет (сразу)",

        # Position labels
        "pos_left_top":      "Лев.верх",
        "pos_center_top":    "Центр верх",
        "pos_right_top":     "Прав.верх",
        "pos_left_center":   "Лев.центр",
        "pos_center":        "Центр",
        "pos_right_center":  "Прав.центр",
        "pos_left_bottom":   "Лев.низ",
        "pos_center_bottom": "Центр низ",
        "pos_right_bottom":  "Прав.низ",

        # Video handling
        "send_video": (
            "🎥 Отправьте видео или документ с видео.\n\n"
            "Поддерживаемые форматы: <b>mp4, mov, mkv, avi, webm</b>\n"
            "Максимальный размер: <b>2 ГБ</b>"
        ),
        "no_settings": (
            "⚠️ Водяной знак не настроен. Нажмите ⚙️ Настройки перед отправкой видео."
        ),
        "no_text_warning": (
            "⚠️ Сначала настройте водяной знак.\n\nУкажите текст логотипа в настройках."
        ),
        "btn_open_settings":   "⚙️ Открыть настройки",
        "unsupported_format":  "⚠️ Формат <b>.{fmt}</b> не поддерживается.\nДопустимые: {fmts}",
        "video_received":      "📥 <b>Видео получено</b>\n\n📄 Файл: <b>{name}</b>\n📦 Размер: <b>{size}</b>\n\nГотово к обработке: <b>{wm}</b>",
        "queued":              "⏳ Задача добавлена в очередь...\nПозиция: {n}",
        "downloading":         "📥 Скачивание: {pct}",
        "processing":          "⚙️ Обработка: {pct}",
        "uploading":           "📤 Загрузка результата: {pct}",
        "done_status":         "✅ Видео с водяным знаком отправлено!",
        "done_caption":        "✅ <b>Готово!</b>\n📄 {name}\n📦 {size}",
        "job_failed":          "❌ Ошибка при обработке видео.\n\n<code>{err}</code>",
        "cancelled":           "❌ Отменено.",
    },

    "en": {
        # ── Main menu ────────────────────────────────────────────────────────
        "welcome":          "👋 Hello, <b>{name}</b>!\n\nI'll help you add a text watermark to your video.\nChoose an action:",
        "what_next":        "What's next?",
        "btn_add_video":    "🎥 Add video",
        "btn_settings":     "⚙️ Watermark settings",
        "btn_my_jobs":      "📂 My jobs",
        "btn_help":         "ℹ️ Help",
        "btn_done":         "✅ Done",
        "btn_back":         "◀️ Back",
        "btn_cancel":       "❌ Cancel",
        "btn_start_proc":   "▶️ Start processing",

        # ── Help ─────────────────────────────────────────────────────────────
        "help_text": (
            "ℹ️ <b>How to use the bot:</b>\n\n"
            "1️⃣ Open <b>⚙️ Watermark settings</b> and set the text, font, color, and position.\n"
            "2️⃣ Press <b>🎥 Add video</b> and send your file.\n"
            "3️⃣ The bot will process the video and return the result.\n\n"
            "<b>Supported formats:</b> mp4, mov, mkv, avi, webm\n"
            "<b>Max size:</b> up to 2 GB\n\n"
            "📂 In <b>My jobs</b> you can view your processing history."
        ),

        # ── Jobs ─────────────────────────────────────────────────────────────
        "no_jobs":       "📂 <b>My jobs</b>\n\nYou have no processed videos yet.",
        "jobs_header":   "📂 <b>My jobs (last 10):</b>\n",
        "job_status_pending":     "⏳",
        "job_status_downloading": "📥",
        "job_status_processing":  "⚙️",
        "job_status_uploading":   "📤",
        "job_status_done":        "✅",
        "job_status_failed":      "❌",

        # ── Settings ─────────────────────────────────────────────────────────
        "settings_header":      "⚙️ <b>Watermark settings</b>\n\n",
        "settings_text_row":    "✏️ Logo text: <b>{v}</b>\n",
        "settings_font_row":    "🔤 Font: <b>{v}</b>\n",
        "settings_size_row":    "📏 Size: <b>{v}</b>\n",
        "settings_color_row":   "🎨 Color: <b>{v}</b>\n",
        "settings_opacity_row": "💧 Opacity: <b>{v}</b>\n",
        "settings_pos_row":     "📍 Position: <b>{v}</b>\n",
        "settings_alt_row":     "🔄 Alternation: <b>{v}</b>\n",
        "settings_delay_row":   "⏱ Delay: <b>{v}</b>",
        "alt_on":               "on",
        "alt_off":              "off",
        "delay_none":           "none",
        "delay_sec":            "{n} sec.",
        "settings_done_msg":    "✅ Settings saved!\n\nNow send a video to process.",
        "settings_done_toast":  "Settings saved!",

        # Settings buttons
        "btn_text":         "✏️ Text: {v}",
        "btn_font":         "🔤 Font: {v}",
        "btn_size":         "📏 Size: {v}",
        "btn_color":        "🎨 Color: {v}",
        "btn_opacity":      "💧 Opacity: {v}",
        "btn_position":     "📍 Position: {v}",
        "btn_alternation":  "🔄 Alternation: {v}",
        "btn_delay":        "⏱ Delay: {v} sec.",
        "btn_language":     "🌐 Language: 🇬🇧 English",

        # Set-text flow
        "enter_text":    "✏️ Enter the watermark text:",
        "text_too_long": "⚠️ Text is too long. Maximum 200 characters.",
        "text_saved":    "✅ Text saved: <b>{v}</b>",

        # Set-font
        "choose_font":  "🔤 Choose a font:",
        "font_saved":   "Font: {v}",

        # Set-size
        "choose_size":  "📏 Choose a text size:",
        "size_saved":   "Size: {v}",

        # Set-color
        "choose_color": "🎨 Choose a color:",
        "color_saved":  "Color: {v}",

        # Set-opacity
        "choose_opacity": "💧 Choose opacity:",
        "opacity_saved":  "Opacity: {v}%",

        # Set-position
        "choose_position": "📍 Choose watermark position:",
        "position_saved":  "Position: {v}",

        # Set-language
        "choose_language": "🌐 Выберите язык / Choose language:",
        "lang_ru":         "🇷🇺 Русский",
        "lang_en":         "🇬🇧 English",
        "language_saved":  "✅ Language set: English",

        # Alternation
        "alt_header": (
            "🔄 <b>Position alternation</b>\n\n"
            "When enabled, the watermark switches between positions at a set interval."
        ),
        "alt_enable":      "🟢 Enable alternation",
        "alt_disable":     "🔴 Disable alternation",
        "alt_disabled":    "Alternation disabled",
        "enter_interval":  "⏱ Enter the alternation interval in seconds.\n\nExample: <code>5</code>",
        "interval_set":    "✅ Interval: {n} sec.\n\n📍 Choose position 1:",
        "choose_pos1":     "📍 Position 1: <b>{pos}</b>\n\n📐 Enter <b>X Y</b> offset in pixels.\nExample: <code>0 0</code>",
        "pos1_saved":      "✅ Position 1: <b>{pos}</b> ({ox:+d}, {oy:+d})\n\n📍 Choose position 2:",
        "choose_pos2":     "📍 Position 2: <b>{pos}</b>\n\n📐 Enter X Y offset:",
        "alt_configured":  "✅ <b>Alternation configured!</b>\n\n⏱ Interval: <b>{n} sec.</b>\n📍 Position 1: <b>{p1}</b>\n📍 Position 2: <b>{p2}</b>",
        "bad_interval":    "⚠️ Enter an integer.",
        "bad_two_numbers": "⚠️ Two numbers separated by a space: <code>0 0</code>",
        "bad_integers":    "⚠️ Integers only.",
        "interval_zero":   "Alternation disabled.",

        # Delay
        "delay_header": (
            "⏱ <b>Watermark appearance delay</b>\n\n"
            "After how many seconds should the watermark appear?\n\n"
            "<code>0</code> — immediately\n<code>5</code> — after 5 sec."
        ),
        "delay_saved":       "✅ Delay: <b>{v}</b>",
        "delay_bad":         "⚠️ Enter an integer, e.g. <code>5</code>.",
        "delay_negative":    "⚠️ Delay cannot be negative.",
        "delay_immediate":   "none (immediate)",

        # Position labels
        "pos_left_top":      "↖ Top Left",
        "pos_center_top":    "⬆ Top Center",
        "pos_right_top":     "↗ Top Right",
        "pos_left_center":   "◀ Left",
        "pos_center":        "⊕ Center",
        "pos_right_center":  "▶ Right",
        "pos_left_bottom":   "↙ Bot Left",
        "pos_center_bottom": "⬇ Bot Center",
        "pos_right_bottom":  "↘ Bot Right",

        # Video handling
        "send_video": (
            "🎥 Send a video or a document with video.\n\n"
            "Supported formats: <b>mp4, mov, mkv, avi, webm</b>\n"
            "Maximum size: <b>2 GB</b>"
        ),
        "no_settings": (
            "⚠️ Watermark is not configured. Press ⚙️ Settings before sending a video."
        ),
        "no_text_warning": (
            "⚠️ Set up the watermark first.\n\nEnter the logo text in Settings."
        ),
        "btn_open_settings":   "⚙️ Open settings",
        "unsupported_format":  "⚠️ Format <b>.{fmt}</b> is not supported.\nAllowed: {fmts}",
        "video_received":      "📥 <b>Video received</b>\n\n📄 File: <b>{name}</b>\n📦 Size: <b>{size}</b>\n\nReady to apply watermark: <b>{wm}</b>",
        "queued":              "⏳ Task added to queue...\nPosition: {n}",
        "downloading":         "📥 Downloading: {pct}",
        "processing":          "⚙️ Processing: {pct}",
        "uploading":           "📤 Uploading result: {pct}",
        "done_status":         "✅ Watermarked video sent!",
        "done_caption":        "✅ <b>Done!</b>\n📄 {name}\n📦 {size}",
        "job_failed":          "❌ Error processing video.\n\n<code>{err}</code>",
        "cancelled":           "❌ Cancelled.",
    },
}


def t(key: str, lang: str = "ru", **kwargs) -> str:
    """Return the translated string for *key* in *lang*, formatting with kwargs."""
    lang = lang if lang in _T else "ru"
    text = _T[lang].get(key) or _T["ru"].get(key, key)
    if kwargs:
        try:
            return text.format(**kwargs)
        except (KeyError, ValueError):
            return text
    return text


def pos_label(position_key: str, lang: str = "ru") -> str:
    """Return the localised label for a position key like 'right_bottom'."""
    return t(f"pos_{position_key}", lang)
