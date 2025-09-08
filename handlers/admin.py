from aiogram import Router, F
from aiogram.types import Message
from aiogram.fsm.context import FSMContext

from api.api_client import ShakaSportsApiClient
from config import ID, denied
from parsers.af_results import results_af_parser
from states.form_states import Form

from config import key_error_text, url_results, event_id_text

admin = Router()


# --- admin HELP commands ---
@admin.message(F.text == "Help")
async def make_help_handler(message: Message):
    if message.from_user.id == ID:
        await message.answer(
            """X - Показать все состояния\nR - распарсить результаты турнира для AF академии"""
        )
    else:
        await message.answer(denied)


# --- Handler show states Button ---
@admin.message(F.text == "X")
async def show_info_handler(message: Message, state: FSMContext):
    if message.from_user.id == ID:
        data = await state.get_data()
        await message.answer(f"все состояния {data}")
    else:
        await message.answer(denied)


# --- Handler parsing AF Academy results ---
@admin.message(F.text == "R")
async def call_results(message: Message, state: FSMContext):
    if message.from_user.id == ID:
        await message.reply(event_id_text)
        await state.set_state(Form.af_search_event_id)
    else:
        await message.answer(denied)


@admin.message(Form.af_search_event_id)
async def parse_af_results(message: Message, state: FSMContext):
    await state.update_data(af_search_event_id=message.text)
    url = f"{url_results}{message.text}"
    async with ShakaSportsApiClient(message.text) as client:
        try:
            event_title = await client.get_event_title()
            await message.answer(event_title)
        except KeyError:
            await message.answer(key_error_text)
    reply = await results_af_parser(url)
    for names in reply:
        await message.answer(names if names else key_error_text)
    await state.clear()
