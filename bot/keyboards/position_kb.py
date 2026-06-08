from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from bot.config import POSITIONS


def position_keyboard(callback_prefix: str = "pos") -> InlineKeyboardMarkup:
    """3x3 grid of position buttons."""
    pos_keys = list(POSITIONS.keys())
    # Order: top row, center row, bottom row
    order = [
        "left_top",    "center_top",    "right_top",
        "left_center", "center",        "right_center",
        "left_bottom", "center_bottom", "right_bottom",
    ]
    rows = []
    row = []
    for i, key in enumerate(order):
        label = POSITIONS[key]
        row.append(InlineKeyboardButton(
            text=label,
            callback_data=f"{callback_prefix}:{key}"
        ))
        if len(row) == 3:
            rows.append(row)
            row = []
    if row:
        rows.append(row)
    rows.append([InlineKeyboardButton(text="◀️ Назад", callback_data="open_settings")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def alternation_toggle_keyboard(enabled: bool) -> InlineKeyboardMarkup:
    toggle_text = "🔴 Выключить чередование" if enabled else "🟢 Включить чередование"
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=toggle_text, callback_data="alt_toggle")],
        [InlineKeyboardButton(text="◀️ Назад", callback_data="open_settings")],
    ])
