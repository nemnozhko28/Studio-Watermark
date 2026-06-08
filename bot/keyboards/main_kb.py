from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton


def main_menu_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🎥 Добавить видео", callback_data="add_video")],
        [InlineKeyboardButton(text="⚙️ Настройки водяного знака", callback_data="open_settings")],
        [InlineKeyboardButton(text="📂 Мои задачи", callback_data="my_jobs")],
        [InlineKeyboardButton(text="ℹ️ Помощь", callback_data="help")],
    ])
