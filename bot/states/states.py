from aiogram.fsm.state import State, StatesGroup


class WatermarkSettingsStates(StatesGroup):
    waiting_for_text = State()
    choosing_font = State()
    choosing_size = State()
    choosing_color = State()
    choosing_opacity = State()
    choosing_position = State()

    # Delay flow
    waiting_for_delay = State()

    # Alternation flow
    waiting_for_interval = State()
    choosing_alt_position_1 = State()
    waiting_for_offset_1 = State()
    choosing_alt_position_2 = State()
    waiting_for_offset_2 = State()


class VideoStates(StatesGroup):
    waiting_for_video = State()
    confirming_processing = State()
