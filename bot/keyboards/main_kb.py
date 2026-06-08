from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from bot.i18n import t


def main_menu_keyboard(lang: str = "ru") -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=t("btn_add_video", lang),  callback_data="add_video")],
        [InlineKeyboardButton(text=t("btn_settings", lang),   callback_data="open_settings")],
        [InlineKeyboardButton(text=t("btn_my_jobs", lang),    callback_data="my_jobs")],
        [InlineKeyboardButton(text=t("btn_help", lang),       callback_data="help")],
    ])
