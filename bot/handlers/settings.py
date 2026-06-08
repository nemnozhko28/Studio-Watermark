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
    update_watermark_delay,
    update_language,
)
from bot.database.queries import get_lang
from bot.keyboards import (
    settings_menu_keyboard,
    font_keyboard,
    size_keyboard,
    color_keyboard,
    opacity_keyboard,
    position_keyboard,
    alternation_toggle_keyboard,
    language_keyboard,
)
from bot.states import WatermarkSettingsStates
from bot.i18n import t, pos_label

logger = logging.getLogger(__name__)
router = Router(name="settings")


def _opacity_display(opacity_float: float) -> str:
    return f"{int(round(opacity_float * 100))}%"


async def _show_settings(target, session: AsyncSession, user_id: int, edit: bool = True) -> None:
    settings = await get_or_create_settings(session, user_id)
    lang = get_lang(settings)
    alt_label = t("alt_on", lang) if settings.alternation_enabled else t("alt_off", lang)
    delay = getattr(settings, "delay_seconds", 0)
    delay_label = t("delay_sec", lang, n=delay) if delay else t("delay_none", lang)

    text = (
        t("settings_header", lang)
        + t("settings_text_row", lang, v=settings.text or "(—)")
        + t("settings_font_row", lang, v=settings.font)
        + t("settings_size_row", lang, v=settings.size)
        + t("settings_color_row", lang, v=settings.color)
        + t("settings_opacity_row", lang, v=_opacity_display(settings.opacity))
        + t("settings_pos_row", lang, v=pos_label(settings.position, lang))
        + t("settings_alt_row", lang, v=alt_label)
        + t("settings_delay_row", lang, v=delay_label)
    )

    kb = settings_menu_keyboard(settings, lang)
    if edit:
        await target.message.edit_text(text, reply_markup=kb, parse_mode="HTML")
    else:
        await target.answer(text, reply_markup=kb, parse_mode="HTML")


@router.callback_query(F.data == "open_settings")
async def cb_open_settings(call: CallbackQuery, session: AsyncSession, state: FSMContext) -> None:
    await state.clear()
    await _show_settings(call, session, call.from_user.id, edit=True)
    await call.answer()


# ─── Text ─────────────────────────────────────────────────────────────────────

@router.callback_query(F.data == "set_text")
async def cb_set_text(call: CallbackQuery, state: FSMContext, session: AsyncSession) -> None:
    settings = await get_or_create_settings(session, call.from_user.id)
    lang = get_lang(settings)
    await call.message.edit_text(t("enter_text", lang))
    await state.set_state(WatermarkSettingsStates.waiting_for_text)
    await call.answer()


@router.message(WatermarkSettingsStates.waiting_for_text)
async def msg_text_received(message: Message, state: FSMContext, session: AsyncSession) -> None:
    settings = await get_or_create_settings(session, message.from_user.id)
    lang = get_lang(settings)
    text = message.text.strip()
    if len(text) > 200:
        await message.answer(t("text_too_long", lang))
        return
    await update_watermark_text(session, message.from_user.id, text)
    await state.clear()
    settings = await get_or_create_settings(session, message.from_user.id)
    await message.answer(
        t("text_saved", lang, v=text),
        parse_mode="HTML",
        reply_markup=settings_menu_keyboard(settings, lang),
    )


# ─── Font ─────────────────────────────────────────────────────────────────────

@router.callback_query(F.data == "set_font")
async def cb_set_font(call: CallbackQuery, state: FSMContext, session: AsyncSession) -> None:
    settings = await get_or_create_settings(session, call.from_user.id)
    lang = get_lang(settings)
    await call.message.edit_text(t("choose_font", lang), reply_markup=font_keyboard(lang))
    await state.set_state(WatermarkSettingsStates.choosing_font)
    await call.answer()


@router.callback_query(WatermarkSettingsStates.choosing_font, F.data.startswith("font:"))
async def cb_font_chosen(call: CallbackQuery, state: FSMContext, session: AsyncSession) -> None:
    font = call.data.split(":", 1)[1]
    await update_watermark_font(session, call.from_user.id, font)
    await state.clear()
    settings = await get_or_create_settings(session, call.from_user.id)
    lang = get_lang(settings)
    await call.answer(t("font_saved", lang, v=font))
    await _show_settings(call, session, call.from_user.id)


# ─── Size ─────────────────────────────────────────────────────────────────────

@router.callback_query(F.data == "set_size")
async def cb_set_size(call: CallbackQuery, state: FSMContext, session: AsyncSession) -> None:
    settings = await get_or_create_settings(session, call.from_user.id)
    lang = get_lang(settings)
    await call.message.edit_text(t("choose_size", lang), reply_markup=size_keyboard(lang))
    await state.set_state(WatermarkSettingsStates.choosing_size)
    await call.answer()


@router.callback_query(WatermarkSettingsStates.choosing_size, F.data.startswith("size:"))
async def cb_size_chosen(call: CallbackQuery, state: FSMContext, session: AsyncSession) -> None:
    size = call.data.split(":", 1)[1]
    await update_watermark_size(session, call.from_user.id, size)
    await state.clear()
    settings = await get_or_create_settings(session, call.from_user.id)
    lang = get_lang(settings)
    await call.answer(t("size_saved", lang, v=size))
    await _show_settings(call, session, call.from_user.id)


# ─── Color ────────────────────────────────────────────────────────────────────

@router.callback_query(F.data == "set_color")
async def cb_set_color(call: CallbackQuery, state: FSMContext, session: AsyncSession) -> None:
    settings = await get_or_create_settings(session, call.from_user.id)
    lang = get_lang(settings)
    await call.message.edit_text(t("choose_color", lang), reply_markup=color_keyboard(lang))
    await state.set_state(WatermarkSettingsStates.choosing_color)
    await call.answer()


@router.callback_query(WatermarkSettingsStates.choosing_color, F.data.startswith("color:"))
async def cb_color_chosen(call: CallbackQuery, state: FSMContext, session: AsyncSession) -> None:
    color = call.data.split(":", 1)[1]
    await update_watermark_color(session, call.from_user.id, color)
    await state.clear()
    settings = await get_or_create_settings(session, call.from_user.id)
    lang = get_lang(settings)
    await call.answer(t("color_saved", lang, v=color))
    await _show_settings(call, session, call.from_user.id)


# ─── Opacity ──────────────────────────────────────────────────────────────────

@router.callback_query(F.data == "set_opacity")
async def cb_set_opacity(call: CallbackQuery, state: FSMContext, session: AsyncSession) -> None:
    settings = await get_or_create_settings(session, call.from_user.id)
    lang = get_lang(settings)
    await call.message.edit_text(t("choose_opacity", lang), reply_markup=opacity_keyboard(lang))
    await state.set_state(WatermarkSettingsStates.choosing_opacity)
    await call.answer()


@router.callback_query(WatermarkSettingsStates.choosing_opacity, F.data.startswith("opacity:"))
async def cb_opacity_chosen(call: CallbackQuery, state: FSMContext, session: AsyncSession) -> None:
    pct_str = call.data.split(":", 1)[1]
    await update_watermark_opacity(session, call.from_user.id, float(pct_str) / 100.0)
    await state.clear()
    settings = await get_or_create_settings(session, call.from_user.id)
    lang = get_lang(settings)
    await call.answer(t("opacity_saved", lang, v=pct_str))
    await _show_settings(call, session, call.from_user.id)


# ─── Position ─────────────────────────────────────────────────────────────────

@router.callback_query(F.data == "set_position")
async def cb_set_position(call: CallbackQuery, state: FSMContext, session: AsyncSession) -> None:
    settings = await get_or_create_settings(session, call.from_user.id)
    lang = get_lang(settings)
    await call.message.edit_text(
        t("choose_position", lang), reply_markup=position_keyboard("pos", lang)
    )
    await state.set_state(WatermarkSettingsStates.choosing_position)
    await call.answer()


@router.callback_query(WatermarkSettingsStates.choosing_position, F.data.startswith("pos:"))
async def cb_position_chosen(call: CallbackQuery, state: FSMContext, session: AsyncSession) -> None:
    position = call.data.split(":", 1)[1]
    await update_watermark_position(session, call.from_user.id, position)
    await state.clear()
    settings = await get_or_create_settings(session, call.from_user.id)
    lang = get_lang(settings)
    await call.answer(t("position_saved", lang, v=pos_label(position, lang)))
    await _show_settings(call, session, call.from_user.id)


# ─── Language ─────────────────────────────────────────────────────────────────

@router.callback_query(F.data == "set_language")
async def cb_set_language(call: CallbackQuery, session: AsyncSession) -> None:
    await call.message.edit_text(
        t("choose_language", "ru"),  # bilingual prompt
        reply_markup=language_keyboard(),
    )
    await call.answer()


@router.callback_query(F.data.startswith("lang:"))
async def cb_lang_chosen(call: CallbackQuery, session: AsyncSession) -> None:
    lang = call.data.split(":", 1)[1]
    if lang not in ("ru", "en"):
        await call.answer("?")
        return
    await update_language(session, call.from_user.id, lang)
    settings = await get_or_create_settings(session, call.from_user.id)
    await call.answer(t("language_saved", lang))
    await _show_settings(call, session, call.from_user.id)


# ─── Alternation ──────────────────────────────────────────────────────────────

@router.callback_query(F.data == "set_alternation")
async def cb_set_alternation(call: CallbackQuery, session: AsyncSession) -> None:
    settings = await get_or_create_settings(session, call.from_user.id)
    lang = get_lang(settings)
    await call.message.edit_text(
        t("alt_header", lang),
        reply_markup=alternation_toggle_keyboard(settings.alternation_enabled, lang),
        parse_mode="HTML",
    )
    await call.answer()


@router.callback_query(F.data == "alt_toggle")
async def cb_alt_toggle(call: CallbackQuery, state: FSMContext, session: AsyncSession) -> None:
    settings = await get_or_create_settings(session, call.from_user.id)
    lang = get_lang(settings)
    if settings.alternation_enabled:
        await update_alternation(session, call.from_user.id, False, 5, None)
        await call.answer(t("alt_disabled", lang))
        await _show_settings(call, session, call.from_user.id)
    else:
        await call.message.edit_text(t("enter_interval", lang), parse_mode="HTML")
        await state.set_state(WatermarkSettingsStates.waiting_for_interval)
        await call.answer()


# ─── Delay ────────────────────────────────────────────────────────────────────

@router.callback_query(F.data == "set_delay")
async def cb_set_delay(call: CallbackQuery, state: FSMContext, session: AsyncSession) -> None:
    settings = await get_or_create_settings(session, call.from_user.id)
    lang = get_lang(settings)
    await call.message.edit_text(t("delay_header", lang), parse_mode="HTML")
    await state.set_state(WatermarkSettingsStates.waiting_for_delay)
    await call.answer()


@router.message(WatermarkSettingsStates.waiting_for_delay)
async def msg_delay_received(message: Message, state: FSMContext, session: AsyncSession) -> None:
    settings = await get_or_create_settings(session, message.from_user.id)
    lang = get_lang(settings)
    try:
        delay = int(message.text.strip())
    except ValueError:
        await message.answer(t("delay_bad", lang), parse_mode="HTML")
        return
    if delay < 0:
        await message.answer(t("delay_negative", lang))
        return
    await update_watermark_delay(session, message.from_user.id, delay)
    await state.clear()
    label = t("delay_sec", lang, n=delay) if delay else t("delay_immediate", lang)
    settings = await get_or_create_settings(session, message.from_user.id)
    await message.answer(
        t("delay_saved", lang, v=label),
        parse_mode="HTML",
        reply_markup=settings_menu_keyboard(settings, lang),
    )


# ─── Alternation setup flow ───────────────────────────────────────────────────

@router.message(WatermarkSettingsStates.waiting_for_interval)
async def msg_interval_received(message: Message, state: FSMContext, session: AsyncSession) -> None:
    settings = await get_or_create_settings(session, message.from_user.id)
    lang = get_lang(settings)
    try:
        interval = int(message.text.strip())
    except ValueError:
        await message.answer(t("bad_interval", lang))
        return
    if interval == 0:
        await state.clear()
        await message.answer(t("interval_zero", lang))
        return
    if interval < 1:
        await message.answer(t("bad_interval", lang))
        return
    await state.update_data(interval=interval, positions=[])
    await message.answer(
        t("interval_set", lang, n=interval),
        reply_markup=position_keyboard("altpos1", lang),
    )
    await state.set_state(WatermarkSettingsStates.choosing_alt_position_1)


@router.callback_query(WatermarkSettingsStates.choosing_alt_position_1, F.data.startswith("altpos1:"))
async def cb_alt_pos1_chosen(call: CallbackQuery, state: FSMContext, session: AsyncSession) -> None:
    settings = await get_or_create_settings(session, call.from_user.id)
    lang = get_lang(settings)
    pos = call.data.split(":", 1)[1]
    await state.update_data(alt_pos1=pos)
    await call.message.edit_text(
        t("choose_pos1", lang, pos=pos_label(pos, lang)),
        parse_mode="HTML",
    )
    await state.set_state(WatermarkSettingsStates.waiting_for_offset_1)
    await call.answer()


@router.message(WatermarkSettingsStates.waiting_for_offset_1)
async def msg_offset1_received(message: Message, state: FSMContext, session: AsyncSession) -> None:
    settings = await get_or_create_settings(session, message.from_user.id)
    lang = get_lang(settings)
    parts = message.text.strip().split()
    if len(parts) != 2:
        await message.answer(t("bad_two_numbers", lang), parse_mode="HTML")
        return
    try:
        ox, oy = int(parts[0]), int(parts[1])
    except ValueError:
        await message.answer(t("bad_integers", lang))
        return
    data = await state.get_data()
    pos1 = data.get("alt_pos1", "right_bottom")
    positions = data.get("positions", [])
    positions.append({"position": pos1, "offset_x": ox, "offset_y": oy})
    await state.update_data(positions=positions)
    await message.answer(
        t("pos1_saved", lang, pos=pos_label(pos1, lang), ox=ox, oy=oy),
        parse_mode="HTML",
        reply_markup=position_keyboard("altpos2", lang),
    )
    await state.set_state(WatermarkSettingsStates.choosing_alt_position_2)


@router.callback_query(WatermarkSettingsStates.choosing_alt_position_2, F.data.startswith("altpos2:"))
async def cb_alt_pos2_chosen(call: CallbackQuery, state: FSMContext, session: AsyncSession) -> None:
    settings = await get_or_create_settings(session, call.from_user.id)
    lang = get_lang(settings)
    pos = call.data.split(":", 1)[1]
    await state.update_data(alt_pos2=pos)
    await call.message.edit_text(
        t("choose_pos2", lang, pos=pos_label(pos, lang)),
        parse_mode="HTML",
    )
    await state.set_state(WatermarkSettingsStates.waiting_for_offset_2)
    await call.answer()


@router.message(WatermarkSettingsStates.waiting_for_offset_2)
async def msg_offset2_received(message: Message, state: FSMContext, session: AsyncSession) -> None:
    settings = await get_or_create_settings(session, message.from_user.id)
    lang = get_lang(settings)
    parts = message.text.strip().split()
    if len(parts) != 2:
        await message.answer(t("bad_two_numbers", lang), parse_mode="HTML")
        return
    try:
        ox, oy = int(parts[0]), int(parts[1])
    except ValueError:
        await message.answer(t("bad_integers", lang))
        return
    data = await state.get_data()
    pos2 = data.get("alt_pos2", "left_center")
    interval = data.get("interval", 5)
    positions = data.get("positions", [])
    positions.append({"position": pos2, "offset_x": ox, "offset_y": oy})
    alt_json = {"enabled": True, "interval": interval, "positions": positions}
    await update_alternation(session, message.from_user.id, True, interval, alt_json)
    await state.clear()
    p1 = pos_label(positions[0]["position"], lang)
    p2 = pos_label(positions[1]["position"], lang)
    settings = await get_or_create_settings(session, message.from_user.id)
    await message.answer(
        t("alt_configured", lang, n=interval, p1=p1, p2=p2),
        parse_mode="HTML",
        reply_markup=settings_menu_keyboard(settings, lang),
    )
