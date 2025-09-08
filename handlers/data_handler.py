import logging
import re
from urllib.parse import urlparse

import aiohttp
from aiogram.types import Message

from api.api_client import ShakaSportsApiClient

from aiogram.fsm.context import FSMContext
from typing import Dict, Union, Any


# Настройка логирования
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


async def get_event_id(state: FSMContext) -> Union[int, str, None]:
    """
    Извлекает идентификатор события (event_id) из хранилища состояний FSM.

    Args:
        state: Объект контекста FSM (Finite State Machine).

    Returns:
        Идентификатор события (event_id) в виде целого числа (int) или строки (str),
        либо None, если event_id не найден в данных состояния.
    """
    # Получаем все данные из хранилища состояний FSM.
    data = await state.get_data()
    # Извлекаем значение по ключу 'event_id' из словаря data.
    # Если ключ не найден, метод get() вернет None.
    event_id = data.get("event_id")
    # Возвращаем полученный event_id.
    return event_id


def has_empty_dict(dict: Dict[Any, str]) -> Dict[Any, str]:
    """
    Проверяет, есть ли в словаре (dict) пустые строки ('').
    Если есть, возвращает новый словарь по умолчанию, иначе возвращает исходный словарь.

    Args:
        dict:  Словарь, в котором значения (values) являются строками.

    Returns:
          Если в переданном словаре есть хотя бы одно значение в виде пустой строки,
          то будет возвращен словарь по умолчанию {'0': 'Без разделения'}.
          В противном случае, вернется исходный словарь.
    """
    # Словарь по умолчанию, который будет возвращен, если есть пустые строки.
    no_choice_dict = {0: "Без разделения"}
    # Проходимся по всем значениям словаря.
    for val in dict.values():
        # Если хотя бы одно значение является пустой строкой...
        if val == "":
            # Возвращаем словарь по умолчанию.
            return no_choice_dict
        # Если текущее значение не является пустой строкой...
        else:
            # Возвращаем исходный словарь. (Первое непустое значение)
            return dict


async def get_valid_event_id(message: Message):
    """
    Извлекает последние цифры из URL или напрямую введенный номер мероприятия.
    Если ввод не является ни URL, ни корректным числом, возвращает None.

    Args:
         message (Message): aiogram Message object.

    Returns:
        int: event_id (int) or None
    """
    logger.info(f"Начало обработки сообщения: {message.text}")
    input_str = message.text
    input_str = input_str.strip()  # Удаляем пробелы в начале и конце
    logger.info(f"Текст сообщения после удаления пробелов: '{input_str}'")

    # Проверка на число
    if input_str.isdigit():
        logger.info(f"Ввод является числом: '{input_str}'")
        try:
            event_id = int(input_str)
            logger.info(f"Преобразовано в int: {event_id}")
            return event_id
        except ValueError:
            logger.warning(f"Не удалось преобразовать в int: '{input_str}'")
            return None

    # Проверка на URL
    try:
        logger.debug(f"Попытка разбора URL: '{input_str}'")
        parsed_url = urlparse(input_str)
        if not parsed_url.scheme or not parsed_url.netloc:
            return None
    except ValueError:
        logger.warning(f"Не удалось разобрать URL: '{input_str}'")
        return None

    logger.debug(f"URL разобран: {parsed_url}")
    match = re.search(r"/(\d+)$", parsed_url.path)
    if match:
        logger.debug(f"Найдено совпадение в URL: {match.group(0)}")
        event_id_str = match.group(1)
        if event_id_str and event_id_str.isdigit():
            logger.debug(f"Извлеченный ID: '{event_id_str}' является числом")
            try:
                event_id = int(event_id_str)
                logger.debug(f"Извлеченный ID преобразован в int: {event_id}")
                return event_id
            except ValueError:
                logger.warning(f"Не удалось преобразовать ID в int: '{event_id_str}'")
                return None
        else:
            logger.debug(f"Извлеченный ID не является числом: '{event_id_str}'")
            return None
    else:
        return None


async def check_valid_event_id(message: Message, event_id):
    """
    Проверяет, является ли event_id корректным, обращаясь к API ShakaSports.

    Args:
        message: Объект сообщения от пользователя (для отправки ответа в случае ошибки).
        event_id: Идентификатор события, который нужно проверить. Может быть целым числом или строкой.

    Returns:
        Корректный event_id, если проверка прошла успешно, или None в случае ошибки.
    """
    logger.info(f"Начало проверки event_id: {event_id}")
    try:
        # Создаем экземпляр API клиента, передавая event_id
        logger.info(f"Создание клиента API ShakaSports с event_id: {event_id}")
        async with ShakaSportsApiClient(event_id) as client:
            # Вызываем метод для получения данных о возрастных категориях.
            # Если вызов успешен, значит, event_id корректный
            logger.info("Вызов метода client.get_age_divisions()")
            await client.get_age_divisions()
            logger.info(f"Проверка event_id {event_id} прошла успешно.")
        return event_id
    except aiohttp.ClientError as e:
        # Отправляем пользователю сообщение об ошибке.
        logger.warning(f"Ошибка при проверке event_id: {e}")
        await message.answer(
            "Турнир не найден или организатор не открыл к нему доступ через бота, также, возможно, вы ввели "
            "некорректную ссылку или номер."
        )
        return None
    except Exception:
        await message.answer(
            "Турнир не найден или организатор не открыл к нему доступ через бота, также, возможно, вы ввели "
            "некорректную ссылку или номер."
        )
        return None


async def show_event_title(message: Message, event_id):
    """
    Получает и отображает название турнира (event title) по его идентификатору (event_id).

    Args:
        message: Объект сообщения от пользователя (для отправки ответа с названием турнира).
        event_id: Идентификатор события (турнира), может быть целым числом или строкой.
        state (FSMContext): Объект FSM контекста.
    """
    async with ShakaSportsApiClient(event_id) as client:
        title = await client.get_event_title()
        await message.answer(f"Турнир найден - {title}")


def get_division_info(data_dict):
    """
    Извлекает информацию о возрастных дивизионах из словаря.

    Args:
        data_dict: Словарь, содержащий информацию о дивизионах.
                   Ожидается, что значениями могут быть словари, содержащие ключи 'id' и 'title'.

    Returns:
         Словарь, где ключами являются идентификаторы дивизионов (id), а значениями - их названия (title).
         Возвращает пустой словарь, если входные данные не являются словарем или не содержат нужную структуру.
    """
    # Проверяем, является ли входной параметр словарем.
    if not isinstance(data_dict, dict):
        # Если не является, возвращаем пустой словарь.
        return {}

    # Создаем пустой словарь, в котором будем хранить результат.
    age_division_dict: Dict[Any, str] = {}
    # Проходимся по всем парам ключ-значение во входном словаре.
    for key, value in data_dict.items():
        # Проверяем, является ли значение словарем и содержит ли ключи 'id' и 'title'.
        if isinstance(value, dict) and "id" in value and "title" in value:
            # Если да, то добавляем пару id - title в результирующий словарь.
            age_division_dict[value["id"]] = value["title"]
    return age_division_dict
