from aiogram.fsm.context import FSMContext
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from api.api_client import ShakaSportsApiClient  # Импортируем класс для взаимодействия с API
from handlers.data_handler import has_empty_dict, get_division_info, get_event_id  # Импортируем функции обработки данных
from config import academy_titles, back_step_btn, start_btn, key_error_text  # Импортируем константы из конфига


def create_academy_keyboard():
    """
    Создает инлайн-клавиатуру для выбора академии.

    Returns:
        InlineKeyboardMarkup: Инлайн-клавиатура с кнопками для каждой академии.
    """
    keyboard = []
    for key, buttons in academy_titles.items():
        keyboard.append([
            InlineKeyboardButton(text=buttons, callback_data=f'ac_{key}')  # Создаем кнопку для каждой академии
        ])
    keyboard.append([create_back_step_button()])  # Добавляем кнопку "Назад"
    return InlineKeyboardMarkup(inline_keyboard=keyboard)  # Возвращаем клавиатуру


async def create_age_division_keyboard(state: FSMContext):
    """
    Создает инлайн-клавиатуру для выбора возрастной категории.

    Args:
        state (FSMContext): FSM контекст для получения данных.
    Returns:
        InlineKeyboardMarkup: Инлайн-клавиатура с кнопками для каждой возрастной категории.
    """
    event_id = await get_event_id(state)  # Получаем id события
    # Инициализируем API клиент
    async with ShakaSportsApiClient(event_id) as client:
        age_divisions = await client.get_age_divisions()  # Получаем возрастные категории из API
        age_divs_info = get_division_info(age_divisions)  # Получаем информацию о возрастных категориях

    keyboard = []
    if event_id:
        for index, (key, buttons) in enumerate(age_divs_info.items()):
            keyboard.append([InlineKeyboardButton(text=buttons,
                                                  callback_data=f'age_{index}')])  # Создаем кнопки для каждой категории

        keyboard.append([create_back_step_button()])  # Добавляем кнопку "Назад"

        return InlineKeyboardMarkup(inline_keyboard=keyboard)  # Возвращаем клавиатуру
    else:
        # если по какой-то причине event_id не указан(например, пользователь перепрыгнул шаги )
        return InlineKeyboardMarkup(inline_keyboard=[[create_some_error_button()]])


async def create_weight_keyboard(state: FSMContext):
    """
    Создает инлайн-клавиатуру для выбора весовой категории.

    Args:
        state (FSMContext): FSM контекст для получения данных.
    Returns:
        InlineKeyboardMarkup: Инлайн-клавиатура с кнопками для каждой весовой категории.
    """
    data = await state.get_data()  # Получаем данные из FSM
    event_id = await get_event_id(state)  # Получаем id события
    age_id_index = data.get('age_id')  # Получаем индекс возрастной категории

    # Инициализируем API клиент
    async with ShakaSportsApiClient(event_id) as client:
        age_divisions = await client.get_age_divisions()  # Получаем возрастные категории из API
        age_id = list(age_divisions.keys())[age_id_index]  # Получаем id возрастной категории
        sex_info = has_empty_dict(age_divisions[age_id]['sex_divisions'])  # Получаем данные о поле
        division_info = has_empty_dict(age_divisions[age_id]['belt_divisions'])  # Получаем данные о поясах
        weight = has_empty_dict(age_divisions[age_id]['weights'])  # Получаем данные о весах

        await state.update_data(sex_info=sex_info, division_info=division_info,
                                weight_info=weight)  # Обновляем данные в FSM
        data = await state.get_data()  # Получаем обновленные данные из FSM
        weight_info = data.get('weight_info', [])  # Получаем информацию о весах

    keyboard = []
    if event_id:
        for age_id_index, (keys, buttons) in enumerate(weight_info.items()):
            keyboard.append([InlineKeyboardButton(text=f'{str(buttons)} кг',
                                                  callback_data=f'w_{age_id_index}')])  # Создаем кнопки для каждой весовой категории

        keyboard.append([create_back_step_button()])  # Добавляем кнопку "Назад"

        return InlineKeyboardMarkup(inline_keyboard=keyboard)  # Возвращаем клавиатуру
    else:
        return InlineKeyboardMarkup(inline_keyboard=[[create_some_error_button()]])


async def create_sex_div_keyboard(state: FSMContext):
    """
    Создает инлайн-клавиатуру для выбора дисциплин (ги или ноу ги или оба сразу).

    Args:
        state (FSMContext): FSM контекст для получения данных.
    Returns:
        InlineKeyboardMarkup: Инлайн-клавиатура с кнопками для каждого пола.
    """
    data = await state.get_data()  # Получаем данные из FSM
    sex_info = data.get('sex_info', [])  # Получаем информацию о поле

    keyboard = []
    if sex_info:
        for index, (keys, buttons) in enumerate(sex_info.items()):
            keyboard.append(
                [InlineKeyboardButton(text=buttons, callback_data=f'sex_{index}')])  # Создаем кнопки для каждого пола

        keyboard.append([create_back_step_button()])  # Добавляем кнопку "Назад"
        return InlineKeyboardMarkup(inline_keyboard=keyboard)  # Возвращаем клавиатуру
    else:
        return InlineKeyboardMarkup(inline_keyboard=[[create_some_error_button()]])


async def create_division_keyboard(state: FSMContext):
    """
    Создает инлайн-клавиатуру для выбора уровня подготовки (пояса).

    Args:
        state (FSMContext): FSM контекст для получения данных.
    Returns:
         InlineKeyboardMarkup: Инлайн-клавиатура с кнопками для каждого уровня подготовки.
    """
    data = await state.get_data()  # Получаем данные из FSM
    division_info = data.get('division_info', [])  # Получаем информацию об уровне подготовки

    keyboard = []
    if division_info:
        for index, (keys, buttons) in enumerate(division_info.items()):
            keyboard.append([InlineKeyboardButton(text=buttons,
                                                  callback_data=f'div_{index}')])  # Создаем кнопки для каждого уровня подготовки

        keyboard.append([create_back_step_button()])  # Добавляем кнопку "Назад"

        return InlineKeyboardMarkup(inline_keyboard=keyboard)  # Возвращаем клавиатуру
    else:
        return InlineKeyboardMarkup(inline_keyboard=[[create_some_error_button()]])


def create_confirm_registration_keyboard():
    """
    Создает инлайн-клавиатуру для подтверждения регистрации.

    Returns:
        InlineKeyboardMarkup: Инлайн-клавиатура с кнопками "Показать" и "Назад".
    """
    return InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text='Показать',
                                                                       callback_data='confirm_reg'),
                                                  # Кнопка "Показать"
                                                  create_back_step_button()]])  # Кнопка "Назад"


def create_finish_registration_keyboard():
    """
    Создает инлайн-клавиатуру для завершения регистрации.

    Returns:
        InlineKeyboardMarkup: Инлайн-клавиатура с кнопками "Зарегистрировать" и "Назад".
    """
    return InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text='Зарегистрировать',
                                                                       callback_data='finish_reg'),
                                                  # Кнопка "Зарегистрировать"
                                                  create_back_step_button()]])  # Кнопка "Назад"


def create_back_step_button():
    """
    Создает инлайн-кнопку "Назад".

    Returns:
        InlineKeyboardButton: Инлайн-кнопка "Назад".
    """
    return InlineKeyboardButton(text=back_step_btn, callback_data=back_step_btn)  # Возвращаем кнопку "Назад"


def create_start_btn_button():
    """
    Создает инлайн-кнопку "Сначала".

    Returns:
        InlineKeyboardButton: Инлайн-кнопка "Сначала".
    """
    return InlineKeyboardButton(text=start_btn, callback_data=start_btn)  # Возвращаем кнопку "Сначала"


def create_back_step_keyboard():
    """
    Создает инлайн-клавиатуру с кнопкой "Назад".

    Returns:
        InlineKeyboardMarkup: Инлайн-клавиатура с кнопкой "Назад".
    """
    return InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text=back_step_btn,
                                                                       callback_data=back_step_btn)]])  # Возвращаем клавиатуру с кнопкой "Назад"


def create_start_btn_keyboard():
    """
    Создает инлайн-клавиатуру с кнопкой "Сначала".

    Returns:
        InlineKeyboardMarkup: Инлайн-клавиатура с кнопкой "Сначала".
    """
    return InlineKeyboardMarkup(
        inline_keyboard=[[create_start_btn_button()]])  # Возвращаем клавиатуру с кнопкой "Сначала"


async def create_new_reg_keyboard(state: FSMContext):
    """
    Создает инлайн-клавиатуру для новой регистрации.

    Args:
        state (FSMContext): FSM контекст для получения данных.
    Returns:
        InlineKeyboardMarkup: Инлайн-клавиатура с кнопками "Начать сначала" и "Зарегистрировать еще".
    """
    event_id = await get_event_id(state)  # Получаем id события
    if event_id:
        return InlineKeyboardMarkup(inline_keyboard=[
            [create_start_btn_button()],  # Кнопка "Начать сначала"
            [InlineKeyboardButton(text=f'Зарегистрировать еще на Турнир №{event_id}', callback_data=event_id)]
            # Кнопка "Зарегистрировать еще"
        ])  # Возвращаем клавиатуру
    else:
        return InlineKeyboardMarkup(inline_keyboard=[[create_some_error_button()]])


def create_some_error_button():
    """
    Создает инлайн-кнопку при пустом списке.

    Returns:
        InlineKeyboardButton: Инлайн-кнопка "key_error_text".
    """
    return InlineKeyboardButton(text=key_error_text, callback_data=start_btn)  # Возвращаем кнопку "key_error_text"
