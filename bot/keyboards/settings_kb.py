from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from bot.config import SIZES, COLORS, OPACITIES, FONTS, POSITIONS


def settings_menu_keyboard(settings) -> InlineKeyboardMarkup:
    """Build the settings overview keyboard with current values displayed."""
    pos_label = POSITIONS.get(settings.position, settings.position)
    alt_label = "вкл" if settings.alternation_enabled else "выкл"

    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text=f"✏️ Текст логотипа: {settings.text or '(не задан)'}",
            callback_data="set_text"
        )],
        [InlineKeyboardButton(
            text=f"🔤 Шрифт: {settings.font}",
            callback_data="set_font"
        )],
        [InlineKeyboardButton(
            text=f"📏 Размер: {settings.size}",
            callback_data="set_size"
        )],
        [InlineKeyboardButton(
            text=f"🎨 Цвет: {settings.color}",
            callback_data="set_color"
        )],
        [InlineKeyboardButton(
            text=f"💧 Прозрачность: {settings.opacity}",
            callback_data="set_opacity"
        )],
        [InlineKeyboardButton(
            text=f"📍 Позиция: {pos_label}",
            callback_data="set_position"
        )],
        [InlineKeyboardButton(
            text=f"🔄 Чередование: {alt_label}",
            callback_data="set_alternation"
        )],
        [InlineKeyboardButton(
            text=f"⏱ Задержка: {getattr(settings, 'delay_seconds', 0)} сек.",
            callback_data="set_delay"
        )],
        [InlineKeyboardButton(text="✅ Готово", callback_data="settings_done")],
    ])


def font_keyboard() -> InlineKeyboardMarkup:
    buttons = [
        [InlineKeyboardButton(text=name, callback_data=f"font:{name}")]
        for name in FONTS.keys()
    ]
    buttons.append([InlineKeyboardButton(text="◀️ Назад", callback_data="open_settings")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def size_keyboard() -> InlineKeyboardMarkup:
    rows = []
    row = []
    for i, size in enumerate(SIZES):
        row.append(InlineKeyboardButton(text=size, callback_data=f"size:{size}"))
        if len(row) == 4:
            rows.append(row)
            row = []
    if row:
        rows.append(row)
    rows.append([InlineKeyboardButton(text="◀️ Назад", callback_data="open_settings")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def color_keyboard() -> InlineKeyboardMarkup:
    rows = []
    row = []
    for i, color in enumerate(COLORS):
        row.append(InlineKeyboardButton(text=color, callback_data=f"color:{color}"))
        if len(row) == 4:
            rows.append(row)
            row = []
    if row:
        rows.append(row)
    rows.append([InlineKeyboardButton(text="◀️ Назад", callback_data="open_settings")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def opacity_keyboard() -> InlineKeyboardMarkup:
    rows = []
    row = []
    for i, op in enumerate(OPACITIES):
        row.append(InlineKeyboardButton(text=op, callback_data=f"opacity:{op}"))
        if len(row) == 5:
            rows.append(row)
            row = []
    if row:
        rows.append(row)
    rows.append([InlineKeyboardButton(text="◀️ Назад", callback_data="open_settings")])
    return InlineKeyboardMarkup(inline_keyboard=rows)
