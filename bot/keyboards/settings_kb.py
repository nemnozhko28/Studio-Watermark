from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from bot.config import SIZES, COLORS, OPACITIES, FONTS
from bot.i18n import t, pos_label


def _opacity_display(opacity_float: float) -> str:
    return f"{int(round(opacity_float * 100))}%"


def settings_menu_keyboard(settings, lang: str = "ru") -> InlineKeyboardMarkup:
    pl = pos_label(settings.position, lang)
    alt_label = t("alt_on", lang) if settings.alternation_enabled else t("alt_off", lang)
    delay = getattr(settings, "delay_seconds", 0)

    rows = [
        [InlineKeyboardButton(
            text=t("btn_text", lang, v=settings.text or "(—)"),
            callback_data="set_text",
        )],
        [InlineKeyboardButton(
            text=t("btn_font", lang, v=settings.font),
            callback_data="set_font",
        )],
        [InlineKeyboardButton(
            text=t("btn_size", lang, v=settings.size),
            callback_data="set_size",
        )],
        [InlineKeyboardButton(
            text=t("btn_color", lang, v=settings.color),
            callback_data="set_color",
        )],
        [InlineKeyboardButton(
            text=t("btn_opacity", lang, v=_opacity_display(settings.opacity)),
            callback_data="set_opacity",
        )],
        [InlineKeyboardButton(
            text=t("btn_position", lang, v=pl),
            callback_data="set_position",
        )],
        [InlineKeyboardButton(
            text=t("btn_alternation", lang, v=alt_label),
            callback_data="set_alternation",
        )],
        [InlineKeyboardButton(
            text=t("btn_delay", lang, v=delay),
            callback_data="set_delay",
        )],
        [InlineKeyboardButton(
            text=t("btn_language", lang),
            callback_data="set_language",
        )],
        [InlineKeyboardButton(text=t("btn_done", lang), callback_data="settings_done")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=rows)


def font_keyboard(lang: str = "ru") -> InlineKeyboardMarkup:
    rows = []
    names = list(FONTS.keys())
    for i in range(0, len(names), 2):
        row = [InlineKeyboardButton(text=names[i], callback_data=f"font:{names[i]}")]
        if i + 1 < len(names):
            row.append(InlineKeyboardButton(text=names[i + 1], callback_data=f"font:{names[i + 1]}"))
        rows.append(row)
    rows.append([InlineKeyboardButton(text=t("btn_back", lang), callback_data="open_settings")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def size_keyboard(lang: str = "ru") -> InlineKeyboardMarkup:
    rows, row = [], []
    for size in SIZES:
        row.append(InlineKeyboardButton(text=size, callback_data=f"size:{size}"))
        if len(row) == 4:
            rows.append(row)
            row = []
    if row:
        rows.append(row)
    rows.append([InlineKeyboardButton(text=t("btn_back", lang), callback_data="open_settings")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def color_keyboard(lang: str = "ru") -> InlineKeyboardMarkup:
    rows, row = [], []
    for color in COLORS:
        row.append(InlineKeyboardButton(text=color, callback_data=f"color:{color}"))
        if len(row) == 4:
            rows.append(row)
            row = []
    if row:
        rows.append(row)
    rows.append([InlineKeyboardButton(text=t("btn_back", lang), callback_data="open_settings")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def opacity_keyboard(lang: str = "ru") -> InlineKeyboardMarkup:
    rows, row = [], []
    for op in OPACITIES:
        row.append(InlineKeyboardButton(text=f"{op}%", callback_data=f"opacity:{op}"))
        if len(row) == 5:
            rows.append(row)
            row = []
    if row:
        rows.append(row)
    rows.append([InlineKeyboardButton(text=t("btn_back", lang), callback_data="open_settings")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def language_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🇷🇺 Русский", callback_data="lang:ru"),
            InlineKeyboardButton(text="🇬🇧 English", callback_data="lang:en"),
        ],
        [InlineKeyboardButton(text="◀️ / Back", callback_data="open_settings")],
    ])
