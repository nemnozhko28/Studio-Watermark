from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from bot.i18n import t, pos_label

_POSITION_ORDER = [
    "left_top",    "center_top",    "right_top",
    "left_center", "center",        "right_center",
    "left_bottom", "center_bottom", "right_bottom",
]


def position_keyboard(callback_prefix: str = "pos", lang: str = "ru") -> InlineKeyboardMarkup:
    rows = []
    row = []
    for i, key in enumerate(_POSITION_ORDER):
        row.append(InlineKeyboardButton(
            text=pos_label(key, lang),
            callback_data=f"{callback_prefix}:{key}",
        ))
        if len(row) == 3:
            rows.append(row)
            row = []
    if row:
        rows.append(row)
    rows.append([InlineKeyboardButton(text=t("btn_back", lang), callback_data="open_settings")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def alternation_toggle_keyboard(enabled: bool, lang: str = "ru") -> InlineKeyboardMarkup:
    toggle_text = t("alt_disable", lang) if enabled else t("alt_enable", lang)
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=toggle_text, callback_data="alt_toggle")],
        [InlineKeyboardButton(text=t("btn_back", lang), callback_data="open_settings")],
    ])
