import asyncio
import os

from aiogram import Router, F, Bot
from aiogram.filters import CommandStart
from aiogram.types import CallbackQuery, Message, FSInputFile, InlineKeyboardMarkup
from aiogram.fsm.context import FSMContext
from dotenv import load_dotenv

from keyboards import keyboards as kb
from filters.filters import EmptyStateCallbackFilter, EmptyStateMessageFilter
from keyboards.inline_keyboards import (
    create_start_btn_keyboard,
    create_back_step_keyboard,
    create_academy_keyboard,
    create_age_division_keyboard,
    create_weight_keyboard,
    get_event_id,
    create_sex_div_keyboard,
    create_division_keyboard,
    create_confirm_registration_keyboard,
    get_division_info,
    create_finish_registration_keyboard,
    create_new_reg_keyboard,
)
from config import (
    oferta_text,
    menu,
    event_id_text,
    greeting_photo_path,
    greeting_text,
    start_btn,
    name_text,
    EVENT_FLAG_FINISH,
    event_id_another_text,
    email_text,
    invalid_name,
    tel_text,
    invalid_email,
    team_id_text,
    EVENT_FLAG_NO_SEX_DIVISION,
    age_id_text,
    weight_info_text,
    confirm_text,
    sex_info_text,
    division_id_text,
    EVENT_FLAG_NO_DIVISION,
    academy_titles,
    make_choice_text,
    back_step_btn,
)
from handlers.data_handler import (
    get_valid_event_id,
    check_valid_event_id,
    show_event_title,
)
from handlers.data_handler import ShakaSportsApiClient
from models.models import UserEmail, PhoneNumber, UserName
from pydantic import ValidationError

from states.form_states import Form
from config import ID

users = Router()

load_dotenv()
# Инициализация бота с использованием токена
bot = Bot(token=os.getenv("TOKEN"))


# --- Message No states Handler Button ---
@users.message(EmptyStateMessageFilter())
async def handle_message__empty_states(message: Message):
    """
    Хендлер, который реагирует если YCF сбросил состояние.
    """
    await message.answer(
        text="Время ождидания вышло. Пожалуйста, начните сначала",
        reply_markup=create_start_btn_keyboard(),
    )


# --- Callback No states Handler Button ---
@users.callback_query(EmptyStateCallbackFilter())
async def handle_callback_empty_states(callback: CallbackQuery):
    """
    Хендлер, который реагирует если YCF сбросил состояние.
    """
    await callback.answer()
    await callback.message.answer(
        text="Время ождидания вышло. Пожалуйста, начните сначала",
        reply_markup=create_start_btn_keyboard(),
    )


async def typing(message: Message):
    """
    Отправляет действие "typing" в чат и приостанавливает выполнение на 0.5 секунды.
    Используется для имитации набора текста ботом.

    Args:
        message (Message): Объект сообщения, содержащий информацию о чате.
    """
    await bot.send_chat_action(chat_id=message.from_user.id, action="typing")
    await asyncio.sleep(0.5)


async def del_states_except_event(state: FSMContext):
    """
    Удаляет все данные из FSM (хранилища состояний), кроме event_id.
    Используется для очистки предыдущих введенных данных пользователем,
    сохраняя при этом id турнира.

    Args:
        state (FSMContext): Объект FSM контекста, содержащий данные о состоянии пользователя.
    """
    data = await state.get_data()
    for states in data:
        if states == "event_id":
            continue
        await state.update_data({states: None})


# --- Handler Start Command ---
@users.message(CommandStart())
async def greeting(message: Message, state: FSMContext):
    """
    Обработчик команды /start.
    Отправляет приветственное сообщение с фото и меню.
    Устанавливает состояние FSM для ввода event_id.

    Args:
        message (Message): Объект сообщения пользователя.
        state (FSMContext): Объект FSM контекста для управления состоянием.
    """
    await state.clear()
    await state.update_data(
        start=False
    )  # не первое взаимодествие с ботом - пользователь сам нажал сначала
    await typing(message)
    await message.answer_photo(
        photo=FSInputFile(greeting_photo_path),
        caption=f"{message.from_user.first_name}, {greeting_text}",
        reply_markup=kb.keyboard,
    )
    await typing(message)
    await message.answer(text=f"{oferta_text}", parse_mode="MarkdownV2")
    await typing(message)
    await message.answer(text=f"{message.from_user.first_name}, {menu}")
    await message.answer(text=f"{message.from_user.first_name}, {event_id_text}")
    await state.set_state(Form.event_id)


# --- Handler Start Button ---
@users.message(F.text == start_btn)
async def start_btn_handler(message: Message, state: FSMContext):
    """
    Обработчик нажатия кнопки "Начать".
    Сбрасывает состояние FSM и вызывает функцию приветствия.

    Args:
        message (Message): Объект сообщения пользователя.
        state (FSMContext): Объект FSM контекста.
    """
    await greeting(message, state)


# --- Handler Start Inline Button ---
@users.callback_query(F.data == start_btn)
async def start_inline_btn__handler(callback: CallbackQuery, state: FSMContext):
    """
    Обработчик нажатия кнопки "Начать" в инлайн-режиме.
    Сбрасывает состояние FSM и вызывает функцию приветствия.

    Args:
        callback (CallbackQuery): Объект callback-запроса.
        state (FSMContext): Объект FSM контекста.
    """
    # удаляет inline меню после выбора
    await bot.delete_message(
        chat_id=callback.message.chat.id, message_id=callback.message.message_id
    )
    await callback.answer()
    message = callback.message
    await greeting(message, state)


# --- Handler Registration Event Number ---
@users.callback_query(
    F.data.regexp(r"^\d{3,5}$")
)  # Фильтр для 3-5 цифр в callback_data
async def reg_new_sportsman_handler(callback: CallbackQuery, state: FSMContext):
    """
    Обработчик нажатия на кнопку с номером турнира (3-5 цифр).
    Очищает состояния FSM, кроме event_id, и переходит к запросу имени.

    Args:
        callback (CallbackQuery): Объект callback-запроса.
        state (FSMContext): Объект FSM контекста.
    """
    await callback.answer()
    await del_states_except_event(state)
    message = callback.message
    await typing(message)
    await state.set_state(Form.name)
    await message.answer(text=name_text, reply_markup=create_back_step_keyboard())


# --- Handler Event ID ---
@users.message(Form.event_id)
async def id_event_handler(message: Message, state: FSMContext):
    """
    Обработчик ввода номера турнира.
    Получает и проверяет id турнира, сохраняет его в FSM и переходит к запросу имени.

    Args:
        message (Message): Объект сообщения пользователя.
        state (FSMContext): Объект FSM контекста.
    """
    event_id = await get_valid_event_id(message)
    event_id = await check_valid_event_id(message, event_id)
    async with ShakaSportsApiClient(event_id) as client:
        check_flag = await client.get_flags_event()
        no_event_finished_set = check_flag & EVENT_FLAG_FINISH
        if not no_event_finished_set:
            if event_id:
                await show_event_title(message, event_id)
                await state.update_data(
                    event_id=str(event_id)
                )  # Сохраняем event_id в FSM в String
                await state.set_state(Form.name)
                await typing(message)
                await message.answer(
                    text=name_text, reply_markup=create_back_step_keyboard()
                )
            else:
                # Если event_id None то остаемся в этом состоянии
                await message.answer(event_id_text)
        else:
            await message.answer("Регистрация на данный Турнир завершена")
            # await message.answer(text=f'{message.from_user.first_name}, {event_id_text}')
            # # Если event_id None то остаемся в этом состоянии
            await message.answer(event_id_another_text)


# --- Handler Name ---
@users.message(Form.name)
async def name_handler(message: Message, state: FSMContext):
    """
    Обработчик ввода имени пользователя.
    Получает и проверяет имя, сохраняет его в FSM и переходит к запросу email.

    Args:
        message (Message): Объект сообщения пользователя.
        state (FSMContext): Объект FSM контекста.
    """
    try:
        raw_name = UserName(name=message.text)
        valid_name = raw_name.name
        await state.update_data(name=valid_name)
        await state.set_state(Form.email)
        await typing(message)
        await message.answer(email_text, reply_markup=create_back_step_keyboard())
    except ValidationError:
        await message.answer(invalid_name)


# --- Handler Email ---
@users.message(Form.email)
async def email_handler(message: Message, state: FSMContext):
    """
    Обработчик ввода email пользователя.
    Получает и проверяет email, сохраняет его в FSM и переходит к запросу телефона.

    Args:
        message (Message): Объект сообщения пользователя.
        state (FSMContext): Объект FSM контекста.
    """
    try:
        e_mail = UserEmail(email=message.text)
        valid_email = e_mail.email
        await state.update_data(email=valid_email)
        await state.set_state(Form.tel)
        await typing(message)
        await message.answer(tel_text, reply_markup=create_back_step_keyboard())
    except ValidationError:
        await message.answer(invalid_email)


# --- Handler Phone Number ---
@users.message(Form.tel)
async def tel_handler(message: Message, state: FSMContext):
    """
    Обработчик ввода номера телефона пользователя.
    Получает и форматирует номер телефона, сохраняет его в FSM и переходит к выбору академии.

    Args:
        message (Message): Объект сообщения пользователя.
        state (FSMContext): Объект FSM контекста.
    """
    try:
        tel = PhoneNumber(number=message.text)
        valid_tel = tel.number
        await state.update_data(tel=valid_tel)
        await state.set_state(Form.team_id)
        academy_keyboard = create_academy_keyboard()
        await typing(message)
        await message.answer(text=team_id_text, reply_markup=academy_keyboard)
    except ValidationError as e:
        error = str(e.errors()[0]["msg"])
        await message.answer(error)


# --- Handler Academy ---
@users.callback_query(Form.team_id, F.data.startswith("ac_"))
async def team_id_info(callback: CallbackQuery, state: FSMContext):
    """
    Обработчик выбора академии.
    Сохраняет id академии в FSM и переходит к выбору возрастной категории.

    Args:
        callback (CallbackQuery): Объект callback-запроса.
        state (FSMContext): Объект FSM контекста.
    """
    await callback.answer()
    index = int(callback.data.replace("ac_", ""))
    await state.update_data(team_id=index)
    await transition_selection(
        callback,
        state,
        Form.age_id,
        age_id_text,
        await create_age_division_keyboard(state),
    )


# --- Handler Age Division ---
@users.callback_query(Form.age_id, F.data.startswith("age_"))
async def age_id_info(callback: CallbackQuery, state: FSMContext):
    """
    Обработчик выбора возрастной категории.
    Сохраняет id возрастной категории в FSM и переходит к выбору весовой категории.

    Args:
        callback (CallbackQuery): Объект callback-запроса.
        state (FSMContext): Объект FSM контекста.
    """
    await callback.answer()
    index = int(callback.data.replace("age_", ""))
    await state.update_data(age_id=index)
    await transition_selection(
        callback,
        state,
        Form.weight_id,
        weight_info_text,
        await create_weight_keyboard(state),
    )


# --- Handler Weight Division ---
@users.callback_query(Form.weight_id, F.data.startswith("w_"))
async def weight_id_info(callback: CallbackQuery, state: FSMContext):
    """
    Обработчик выбора весовой категории.
    Сохраняет id весовой категории в FSM и переходит к выбору пола.

    Args:
        callback (CallbackQuery): Объект callback-запроса.
        state (FSMContext): Объект FSM контекста.
    """
    await callback.answer()
    index = int(callback.data.replace("w_", ""))
    await state.update_data(weight_id=index)

    event_id = await get_event_id(state)
    async with ShakaSportsApiClient(event_id) as client:
        check_flag = await client.get_flags_event()
        no_sex_division_set = check_flag & EVENT_FLAG_NO_SEX_DIVISION
        no_division_set = check_flag & EVENT_FLAG_NO_DIVISION
        # проверяем стоят ли обе галки в админке Шака на разделение по дисциплинам и поясам
        if no_sex_division_set and no_division_set:
            await transition_selection(
                callback,
                state,
                Form.confirm,
                confirm_text,
                create_confirm_registration_keyboard(),
            )
        # проверяем стоит ли галка в админке Шака на разделение по дисциплинам(ги/ноу ги) sex_divisions
        elif not no_sex_division_set:
            await transition_selection(
                callback,
                state,
                Form.sex_id,
                sex_info_text,
                await create_sex_div_keyboard(state),
            )
        # проверяем стоит ли галка в админке Шака на разделение по опыту(поясам) belt_divisions
        elif not no_division_set:
            await transition_selection(
                callback,
                state,
                Form.div_id,
                division_id_text,
                await create_division_keyboard(state),
            )


# --- Handler Sex Division ---
@users.callback_query(Form.sex_id, F.data.startswith("sex_"))
async def sex_id_info(callback: CallbackQuery, state: FSMContext):
    """
    Обработчик выбора пола.
    Сохраняет id пола в FSM и переходит к выбору уровня подготовки.

    Args:
        callback (CallbackQuery): Объект callback-запроса.
        state (FSMContext): Объект FSM контекста.
    """
    await callback.answer()
    index = int(callback.data.replace("sex_", ""))
    await state.update_data(sex_id=index)
    event_id = await get_event_id(state)
    async with ShakaSportsApiClient(event_id) as client:
        check_flag = await client.get_flags_event()
        no_division_set = check_flag & EVENT_FLAG_NO_DIVISION
        if not no_division_set:
            await transition_selection(
                callback,
                state,
                Form.div_id,
                division_id_text,
                await create_division_keyboard(state),
            )
        else:
            await transition_selection(
                callback,
                state,
                Form.confirm,
                confirm_text,
                create_confirm_registration_keyboard(),
            )


# --- Handler Division ---
@users.callback_query(Form.div_id, F.data.startswith("div_"))
async def division_id_info(callback: CallbackQuery, state: FSMContext):
    """
    Обработчик выбора уровня подготовки (пояса).
    Сохраняет id уровня подготовки в FSM и переходит к подтверждению регистрации.

    Args:
        callback (CallbackQuery): Объект callback-запроса.
        state (FSMContext): Объект FSM контекста.
    """
    await callback.answer()
    index = int(callback.data.replace("div_", ""))
    await state.update_data(div_id=index)
    await transition_selection(
        callback,
        state,
        Form.confirm,
        confirm_text,
        create_confirm_registration_keyboard(),
    )


# --- Handler Confirm Registration ---
@users.callback_query(Form.confirm, F.data == "confirm_reg")
async def confirm_registration(callback: CallbackQuery, state: FSMContext):
    """
    Обработчик подтверждения регистрации.
    Выводит сообщение с данными для проверки и переходит к завершению регистрации.

    Args:
        callback (CallbackQuery): Объект callback-запроса.
        state (FSMContext): Объект FSM контекста.
    """
    await callback.answer()
    data = await state.get_data()
    age_id_index = data.get("age_id")
    event_id = await get_event_id(state)
    async with ShakaSportsApiClient(event_id) as client:
        age_divisions = await client.get_age_divisions()
        event_flag = await client.get_flags_event()
        title = await client.get_event_title()
        age_divs_info = get_division_info(age_divisions)
        age_id = int(list(age_divs_info.keys())[age_id_index])
        weight = data.get("weight_id")
        sex = data.get("sex_id")
        div = data.get("div_id")
        team = str(data.get("team_id"))
        confirm_message = "Проверьте, пожалуйста, данные для регистрации!\n\n"
        confirm_message += f"Мероприятие: {title}\n"
        confirm_message += f"Имя и фамилия: {data.get('name')}\n"
        confirm_message += f"Email: {data.get('email')}\n"
        confirm_message += f"Телефон: {data.get('tel')}\n"
        confirm_message += f"Академия: {academy_titles[team]}\n"
        confirm_message += f"Возрастная категория: {age_divisions[age_id]['title']}\n"
        confirm_message += f"Весовая категория: {list(age_divisions[age_id]['weights'].values())[weight]} кг\n"
        if not event_flag & EVENT_FLAG_NO_SEX_DIVISION:
            confirm_message += f"Дисциплина: {list(age_divisions[age_id]['sex_divisions'].values())[sex]}\n"
        if not event_flag & EVENT_FLAG_NO_DIVISION:
            confirm_message += f"Уровень подготовки (пояс): {list(age_divisions[age_id]['belt_divisions'].values())[div]}\n"

        await callback.message.answer(confirm_message)

        await transition_selection(
            callback,
            state,
            Form.finish,
            make_choice_text,
            create_finish_registration_keyboard(),
        )


# --- Handler Finish Registration ---
@users.callback_query(Form.finish, F.data == "finish_reg")
async def finish_registration(callback: CallbackQuery, state: FSMContext):
    """
    Обработчик завершения регистрации.
    Формирует данные для отправки на сервер, отправляет запрос и выводит результат.

    Args:
        callback (CallbackQuery): Объект callback-запроса.
        state (FSMContext): Объект FSM контекста.
    """
    await callback.answer()
    event_id = await get_event_id(state)
    async with ShakaSportsApiClient(event_id) as client:
        age_divisions = await client.get_age_divisions()
        data = await state.get_data()
        name = data.get("name")
        email = data.get("email")
        tel = data.get("tel")
        team_id = data.get("team_id")
        age_index = data.get("age_id")
        age_id = list(age_divisions.keys())[age_index]
        sex = data.get("sex_id")
        div = data.get("div_id")
        weight = data.get("weight_id")
        weights = (
            list(age_divisions[age_id]["weights"].keys())[weight] if weight else None
        )
        belt_divisions = (
            list(age_divisions[age_id]["belt_divisions"].keys())[div] if div else None
        )
        sex_divisions = (
            list(age_divisions[age_id]["sex_divisions"].keys())[sex] if sex else None
        )

        registration_data = {
            key: value
            for key, value in [
                ("form[name]", name),
                ("form[email]", email),
                ("form[tel]", tel),
                ("form[age_division]", age_id),
                ("form[sex]", sex_divisions),
                ("form[division_id]", belt_divisions),
                ("form[weight_division]", weights),
                ("form[team_id]", team_id),
            ]
            if value is not None
        }

        response = await client.register_user(registration_data)
        await callback.message.answer(text=response)
        await bot.delete_message(
            chat_id=callback.message.chat.id, message_id=callback.message.message_id
        )
        await get_statistics(
            callback=callback, reg_data=data, response=response
        )  # send statistics
        await del_states_except_event(state)
    new_reg_keyboard = await create_new_reg_keyboard(state)
    await callback.message.answer(text=make_choice_text, reply_markup=new_reg_keyboard)


# --- Handler Back Button ---
@users.callback_query(F.data == back_step_btn)
async def back_btn_handler(callback: CallbackQuery, state: FSMContext):
    """
    Обработчик нажатия кнопки "Назад".
    Переходит на предыдущий шаг регистрации в зависимости от текущего состояния.

    Args:
        callback (CallbackQuery): Объект callback-запроса.
        state (FSMContext): Объект FSM контекста.
    """
    event_id = await get_event_id(state)
    async with ShakaSportsApiClient(event_id) as client:
        check_flag = await client.get_flags_event()
        no_sex_division_set = check_flag & EVENT_FLAG_NO_SEX_DIVISION
        no_division_set = check_flag & EVENT_FLAG_NO_DIVISION
        await callback.answer()
        current_state = await state.get_state()

        if current_state == Form.name:
            await transition_selection(callback, state, Form.event_id, event_id_text)
        elif current_state == Form.email:
            await transition_selection(
                callback, state, Form.name, name_text, create_back_step_keyboard()
            )
        elif current_state == Form.tel:
            await transition_selection(
                callback, state, Form.email, email_text, create_back_step_keyboard()
            )
        elif current_state == Form.team_id:
            await transition_selection(
                callback, state, Form.tel, tel_text, create_back_step_keyboard()
            )
        elif current_state == Form.age_id:
            await transition_selection(
                callback, state, Form.team_id, team_id_text, create_academy_keyboard()
            )
        elif current_state == Form.weight_id:
            await transition_selection(
                callback,
                state,
                Form.age_id,
                age_id_text,
                await create_age_division_keyboard(state),
            )
        elif current_state == Form.sex_id:
            await transition_selection(
                callback,
                state,
                Form.weight_id,
                weight_info_text,
                await create_weight_keyboard(state),
            )
        elif current_state == Form.div_id:
            if not no_sex_division_set:
                await transition_selection(
                    callback,
                    state,
                    Form.sex_id,
                    sex_info_text,
                    await create_sex_div_keyboard(state),
                )
            else:
                await transition_selection(
                    callback,
                    state,
                    Form.weight_id,
                    weight_info_text,
                    await create_weight_keyboard(state),
                )
        elif current_state == Form.confirm:
            if not no_division_set:
                await transition_selection(
                    callback,
                    state,
                    Form.div_id,
                    division_id_text,
                    await create_division_keyboard(state),
                )
            else:
                if not no_sex_division_set:
                    await transition_selection(
                        callback,
                        state,
                        Form.sex_id,
                        sex_info_text,
                        await create_sex_div_keyboard(state),
                    )
                else:
                    await transition_selection(
                        callback,
                        state,
                        Form.weight_id,
                        weight_info_text,
                        await create_weight_keyboard(state),
                    )
        elif current_state == Form.finish:
            if not no_division_set:
                await transition_selection(
                    callback,
                    state,
                    Form.div_id,
                    division_id_text,
                    await create_division_keyboard(state),
                )
            else:
                if not no_sex_division_set:
                    await transition_selection(
                        callback,
                        state,
                        Form.sex_id,
                        sex_info_text,
                        await create_sex_div_keyboard(state),
                    )
                else:
                    await transition_selection(
                        callback,
                        state,
                        Form.weight_id,
                        weight_info_text,
                        await create_weight_keyboard(state),
                    )
        await callback.message.delete()


async def get_statistics(callback: CallbackQuery, reg_data, response):
    # формируем отчет для статистики
    tg_user = callback.from_user  # Получаем объект User
    user_id = tg_user.id
    first_name = tg_user.first_name
    last_name = tg_user.last_name
    username = tg_user.username
    language_code = tg_user.language_code
    is_bot = tg_user.is_bot
    is_premium = tg_user.is_premium
    statistics_info = f"""
                            User_id: {user_id}\n
                            Имя: {first_name}\n
                            Фамилия: {last_name}\n
                            Username: {username}\n
                            Страна: {language_code}\n
                            Бот: {is_bot}\n
                            Премиум: {is_premium}\n
                            Данные регистрации: {reg_data}\n
                            Ответ от сервера: {response}
                            """
    await bot.send_message(chat_id=ID, text=statistics_info)


async def transition_selection(
    callback: CallbackQuery,
    state: FSMContext,
    form_state: str,
    info_text: str,
    keyboard: InlineKeyboardMarkup | None = None,
):
    await state.set_state(form_state)
    await callback.message.answer(text=info_text, reply_markup=keyboard)
