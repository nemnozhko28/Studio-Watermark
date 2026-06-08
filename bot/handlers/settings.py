import logging
from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery
from sqlalchemy.ext.asyncio import AsyncSession

from bot.database import (
    get_or_create_settings,
    update_watermark_text,
    update_watermark_font,
    update_watermark_size,
    update_watermark_color,
    update_watermark_opacity,
    update_watermark_position,
    update_alternation,
)
from bot.keyboards import (
    settings_menu_keyboard,
    font_keyboard,
    size_keyboard,
    color_keyboard,
    opacity_keyboard,
    position_keyboard,
    alternation_toggle_keyboard,
)
from bot.states import WatermarkSettingsStates
from bot.config import POSITIONS

logger = logging.getLogger(__name__)
router = Router(name="settings")


async def _show_settings(target, session: AsyncSession, user_id: int, edit: bool = True) -> None:
    settings = await get_or_create_settings(session, user_id)
    pos_label = POSITIONS.get(settings.position, settings.position)
    alt_label = "вкл" if settings.alternation_enabled else "выкл"

    text = (
        "⚙️ <b>Настройки водяного знака</b>\n\n"
        f"✏️ Текст логотипа: <b>{settings.text or '(не задан)'}</b>\n"
        f"🔤 Шрифт: <b>{settings.font}</b>\n"
        f"📏 Размер: <b>{settings.size}</b>\n"
        f"🎨 Цвет: <b>{settings.color}</b>\n"
        f"💧 Прозрачность: <b>{settings.opacity}</b>\n"
        f"📍 Позиция: <b>{pos_label}</b>\n"
        f"🔄 Чередование: <b>{alt_label}</b>"
    )

    if edit:
        await target.message.edit_text(text, reply_markup=settings_menu_keyboard(settings), parse_mode="HTML")
    else:
        await target.answer(text, reply_markup=settings_menu_keyboard(settings), parse_mode="HTML")


@router.callback_query(F.data == "open_settings")
async def cb_open_settings(call: CallbackQuery, session: AsyncSession, state: FSMContext) -> None:
    await state.clear()
    await _show_settings(call, session, call.from_user.id, edit=True)
    await call.answer()


# ─── Text ───────────────────────────────────────────────────────────────────

@router.callback_query(F.data == "set_text")
async def cb_set_text(call: CallbackQuery, state: FSMContext) -> None:
    await call.message.edit_text("✏️ Введите текст водяного знака:")
    await state.set_state(WatermarkSettingsStates.waiting_for_text)
    await call.answer()


@router.message(WatermarkSettingsStates.waiting_for_text)
async def msg_text_received(message: Message, state: FSMContext, session: AsyncSession) -> None:
    text = message.text.strip()
    if len(text) > 200:
        await message.answer("⚠️ Текст слишком длинный. Максимум 200 символов.")
        return
    await update_watermark_text(session, message.from_user.id, text)
    await state.clear()
    settings = await get_or_create_settings(session, message.from_user.id)
    await message.answer(
        f"✅ Текст водяного знака сохранён: <b>{text}</b>",
        parse_mode="HTML",
        reply_markup=settings_menu_keyboard(settings),
    )


# ─── Font ────────────────────────────────────────────────────────────────────

@router.callback_query(F.data == "set_font")
async def cb_set_font(call: CallbackQuery, state: FSMContext) -> None:
    await call.message.edit_text("🔤 Выберите шрифт:", reply_markup=font_keyboard())
    await state.set_state(WatermarkSettingsStates.choosing_font)
    await call.answer()


@router.callback_query(WatermarkSettingsStates.choosing_font, F.data.startswith("font:"))
async def cb_font_chosen(call: CallbackQuery, state: FSMContext, session: AsyncSession) -> None:
    font = call.data.split(":", 1)[1]
    await update_watermark_font(session, call.from_user.id, font)
    await state.clear()
    await call.answer(f"Шрифт: {font}")
    await _show_settings(call, session, call.from_user.id)


# ─── Size ────────────────────────────────────────────────────────────────────

@router.callback_query(F.data == "set_size")
async def cb_set_size(call: CallbackQuery, state: FSMContext) -> None:
    await call.message.edit_text("📏 Выберите размер текста:", reply_markup=size_keyboard())
    await state.set_state(WatermarkSettingsStates.choosing_size)
    await call.answer()


@router.callback_query(WatermarkSettingsStates.choosing_size, F.data.startswith("size:"))
async def cb_size_chosen(call: CallbackQuery, state: FSMContext, session: AsyncSession) -> None:
    size = call.data.split(":", 1)[1]
    await update_watermark_size(session, call.from_user.id, size)
    await state.clear()
    await call.answer(f"Размер: {size}")
    await _show_settings(call, session, call.from_user.id)


# ─── Color ───────────────────────────────────────────────────────────────────

@router.callback_query(F.data == "set_color")
async def cb_set_color(call: CallbackQuery, state: FSMContext) -> None:
    await call.message.edit_text("🎨 Выберите цвет:", reply_markup=color_keyboard())
    await state.set_state(WatermarkSettingsStates.choosing_color)
    await call.answer()


@router.callback_query(WatermarkSettingsStates.choosing_color, F.data.startswith("color:"))
async def cb_color_chosen(call: CallbackQuery, state: FSMContext, session: AsyncSession) -> None:
    color = call.data.split(":", 1)[1]
    await update_watermark_color(session, call.from_user.id, color)
    await state.clear()
    await call.answer(f"Цвет: {color}")
    await _show_settings(call, session, call.from_user.id)


# ─── Opacity ─────────────────────────────────────────────────────────────────

@router.callback_query(F.data == "set_opacity")
async def cb_set_opacity(call: CallbackQuery, state: FSMContext) -> None:
    await call.message.edit_text("💧 Выберите прозрачность:", reply_markup=opacity_keyboard())
    await state.set_state(WatermarkSettingsStates.choosing_opacity)
    await call.answer()


@router.callback_query(WatermarkSettingsStates.choosing_opacity, F.data.startswith("opacity:"))
async def cb_opacity_chosen(call: CallbackQuery, state: FSMContext, session: AsyncSession) -> None:
    opacity_str = call.data.split(":", 1)[1]
    await update_watermark_opacity(session, call.from_user.id, float(opacity_str))
    await state.clear()
    await call.answer(f"Прозрачность: {opacity_str}")
    await _show_settings(call, session, call.from_user.id)


# ─── Position ────────────────────────────────────────────────────────────────

@router.callback_query(F.data == "set_position")
async def cb_set_position(call: CallbackQuery, state: FSMContext) -> None:
    await call.message.edit_text("📍 Выберите позицию водяного знака:", reply_markup=position_keyboard("pos"))
    await state.set_state(WatermarkSettingsStates.choosing_position)
    await call.answer()


@router.callback_query(WatermarkSettingsStates.choosing_position, F.data.startswith("pos:"))
async def cb_position_chosen(call: CallbackQuery, state: FSMContext, session: AsyncSession) -> None:
    position = call.data.split(":", 1)[1]
    await update_watermark_position(session, call.from_user.id, position)
    await state.clear()
    label = POSITIONS.get(position, position)
    await call.answer(f"Позиция: {label}")
    await _show_settings(call, session, call.from_user.id)


# ─── Alternation ─────────────────────────────────────────────────────────────

@router.callback_query(F.data == "set_alternation")
async def cb_set_alternation(call: CallbackQuery, session: AsyncSession) -> None:
    settings = await get_or_create_settings(session, call.from_user.id)
    await call.message.edit_text(
        "🔄 <b>Чередование позиций</b>\n\n"
        "При включении водяной знак будет переключаться между несколькими позициями через заданный интервал.",
        reply_markup=alternation_toggle_keyboard(settings.alternation_enabled),
        parse_mode="HTML",
    )
    await call.answer()


@router.callback_query(F.data == "alt_toggle")
async def cb_alt_toggle(call: CallbackQuery, state: FSMContext, session: AsyncSession) -> None:
    settings = await get_or_create_settings(session, call.from_user.id)
    if settings.alternation_enabled:
        # Disable
        await update_alternation(session, call.from_user.id, False, 5, None)
        await call.answer("Чередование выключено")
        await _show_settings(call, session, call.from_user.id)
    else:
        # Start setup flow
        await call.message.edit_text(
            "⏱ Введите интервал чередования в секундах.\n\n"
            "Например: <code>5</code>\n\n"
            "Введите <code>0</code> чтобы отключить.",
            parse_mode="HTML",
        )
        await state.set_state(WatermarkSettingsStates.waiting_for_interval)
        await call.answer()


@router.message(WatermarkSettingsStates.waiting_for_interval)
async def msg_interval_received(message: Message, state: FSMContext) -> None:
    try:
        interval = int(message.text.strip())
    except ValueError:
        await message.answer("⚠️ Введите целое число.")
        return

    if interval == 0:
        await state.clear()
        await message.answer("Чередование отключено.")
        return

    if interval < 1:
        await message.answer("⚠️ Интервал должен быть не менее 1 секунды.")
        return

    await state.update_data(interval=interval, positions=[])
    await message.answer(
        f"✅ Интервал: {interval} сек.\n\n📍 Выберите позицию 1:",
        reply_markup=position_keyboard("altpos1"),
    )
    await state.set_state(WatermarkSettingsStates.choosing_alt_position_1)


@router.callback_query(WatermarkSettingsStates.choosing_alt_position_1, F.data.startswith("altpos1:"))
async def cb_alt_pos1_chosen(call: CallbackQuery, state: FSMContext) -> None:
    pos = call.data.split(":", 1)[1]
    await state.update_data(alt_pos1=pos)
    await call.message.edit_text(
        f"📍 Позиция 1: <b>{POSITIONS.get(pos, pos)}</b>\n\n"
        "📐 Введите смещение <b>X Y</b> в пикселях.\n\n"
        "Примеры:\n<code>0 0</code>\n<code>0 -50</code>\n<code>-30 0</code>",
        parse_mode="HTML",
    )
    await state.set_state(WatermarkSettingsStates.waiting_for_offset_1)
    await call.answer()


@router.message(WatermarkSettingsStates.waiting_for_offset_1)
async def msg_offset1_received(message: Message, state: FSMContext) -> None:
    parts = message.text.strip().split()
    if len(parts) != 2:
        await message.answer("⚠️ Введите два числа через пробел, например: <code>0 0</code>", parse_mode="HTML")
        return
    try:
        ox, oy = int(parts[0]), int(parts[1])
    except ValueError:
        await message.answer("⚠️ Только целые числа.")
        return

    data = await state.get_data()
    pos1 = data.get("alt_pos1", "right_bottom")
    positions = data.get("positions", [])
    positions.append({"position": pos1, "offset_x": ox, "offset_y": oy})
    await state.update_data(positions=positions)

    await message.answer(
        f"✅ Позиция 1 сохранена: <b>{POSITIONS.get(pos1, pos1)}</b> ({ox:+d}, {oy:+d})\n\n"
        "📍 Выберите позицию 2:",
        parse_mode="HTML",
        reply_markup=position_keyboard("altpos2"),
    )
    await state.set_state(WatermarkSettingsStates.choosing_alt_position_2)


@router.callback_query(WatermarkSettingsStates.choosing_alt_position_2, F.data.startswith("altpos2:"))
async def cb_alt_pos2_chosen(call: CallbackQuery, state: FSMContext) -> None:
    pos = call.data.split(":", 1)[1]
    await state.update_data(alt_pos2=pos)
    await call.message.edit_text(
        f"📍 Позиция 2: <b>{POSITIONS.get(pos, pos)}</b>\n\n"
        "📐 Введите смещение <b>X Y</b> в пикселях.",
        parse_mode="HTML",
    )
    await state.set_state(WatermarkSettingsStates.waiting_for_offset_2)
    await call.answer()


@router.message(WatermarkSettingsStates.waiting_for_offset_2)
async def msg_offset2_received(message: Message, state: FSMContext, session: AsyncSession) -> None:
    parts = message.text.strip().split()
    if len(parts) != 2:
        await message.answer("⚠️ Введите два числа через пробел, например: <code>0 0</code>", parse_mode="HTML")
        return
    try:
        ox, oy = int(parts[0]), int(parts[1])
    except ValueError:
        await message.answer("⚠️ Только целые числа.")
        return

    data = await state.get_data()
    pos2 = data.get("alt_pos2", "left_center")
    interval = data.get("interval", 5)
    positions = data.get("positions", [])
    positions.append({"position": pos2, "offset_x": ox, "offset_y": oy})

    alt_json = {"enabled": True, "interval": interval, "positions": positions}
    await update_alternation(session, message.from_user.id, True, interval, alt_json)
    await state.clear()

    pos1_label = POSITIONS.get(positions[0]["position"], positions[0]["position"])
    pos2_label = POSITIONS.get(positions[1]["position"], positions[1]["position"])

    settings = await get_or_create_settings(session, message.from_user.id)
    await message.answer(
        f"✅ <b>Чередование настроено!</b>\n\n"
        f"⏱ Интервал: <b>{interval} сек.</b>\n"
        f"📍 Позиция 1: <b>{pos1_label}</b>\n"
        f"📍 Позиция 2: <b>{pos2_label}</b>",
        parse_mode="HTML",
        reply_markup=settings_menu_keyboard(settings),
    )
