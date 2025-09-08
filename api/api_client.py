import hashlib
import re
import os
from dotenv import load_dotenv
import asyncio

import phpserialize
import aiohttp
import urllib.parse

# --- Настройки API ---
load_dotenv()
API_SECRET = os.getenv("API_SECRET")
SERVER_URL = "https://shakasports.com"  # Базовый URL API сервера


class ShakaSportsApiClient:
    """
    Клиент для взаимодействия с API ShakaSports.
    """

    def __init__(self, event_id=None, event_user_id=None):
        """
        Инициализация клиента.

        Args:
            event_id (int, optional): ID мероприятия. Defaults to None.
            event_user_id (int, optional): ID пользователя мероприятия (пока не используется). Defaults to None.
        """
        self.event_id = event_id  # ID мероприятия
        self.event_user_id = event_user_id  # ID спортсмена
        self.session = (
            aiohttp.ClientSession()
        )  # Создаем сессию для повторного использования соединений

    async def _api_request(
        self,
        mode,
        data=None,
        method="get",
        content_type="application/x-www-form-urlencoded",
        is_event=True,
    ):
        """
        Общая функция для запросов к API.

        Args:
            mode (str): Режим запроса к API.
            data (dict, optional): Данные для POST запроса. Defaults to None.
            method (str, optional): Метод запроса ('get' или 'post'). Defaults to 'get'.
            content_type (str, optional): Тип контента. Defaults to 'application/x-www-form-urlencoded'.
            is_event (bool, optional): True если запрос к мероприятию, False если к пользователю. Defaults to True.

        Returns:
            str: Текст ответа от сервера.

        Raises:
            ValueError: Если указан некорректный метод запроса.
            aiohttp.ClientError: Если произошла ошибка при выполнении запроса.
        """
        if is_event:
            query_string = f"mode={mode}&id={self.event_id}&{API_SECRET}"
            hash_value = md5_hash(query_string)
            url = f"{SERVER_URL}/pub/api.php?mode={mode}&id={self.event_id}&hash={hash_value}"
        else:
            # если режим = event_info&event_user_id
            query_string = f"mode={mode}={self.event_user_id}&{API_SECRET}"
            hash_value = md5_hash(query_string)
            url = f"{SERVER_URL}/pub/api.php?mode={mode}={self.event_user_id}&hash={hash_value}"

        headers = {}
        if content_type:
            headers["Content-type"] = content_type

        try:
            if method == "get":
                async with self.session.get(url, timeout=30) as response:
                    response.raise_for_status()
                    return await response.text()
            elif method == "post":
                postdata = (
                    urllib.parse.urlencode(data) if data else None
                )  # encode data only if it exists
                async with self.session.post(
                    url=url, headers=headers, data=postdata, timeout=30
                ) as response:
                    response.raise_for_status()
                    return await response.text()
            else:
                raise ValueError(f"Invalid method: {method}. Must be 'get' or 'post'")
        except aiohttp.ClientError as e:
            raise aiohttp.ClientError(f"Error during API request: {e}")

    """
    Чтобы использовать async with, ваш класс ShakaSportsApiClient должен быть асинхронным контекстным менеджером.
     Для этого он должен иметь методы __aenter__ и __aexit__.
    """

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        await self.close()

    async def close(self):
        await self.session.close()

    # Получение общей информации о событии
    async def get_event_info(self):
        """
        Получение общей информации о событии.

        Returns:
            dict: Сериализованный ответ от сервера.
        """
        result_response = await self._api_request(mode="event_info")
        serialized_response = await asyncio.to_thread(
            phpserialize.loads, result_response.encode("utf-8")
        )
        return await asyncio.to_thread(decode_bytes, serialized_response)

    # Получение schedule расписание Турнира - ПЕРЕДЕЛАТЬ ВМЕСТЕ С ГЛАВНОЙ ФУНКЦИЕЙ
    # async def get_schedule(self):
    #     query_string = f'mode=schedule&id={self.event_id}&{API_SECRET}'
    #     hash_value = md5_hash(query_string)
    #     url = f'{SERVER_URL}/pub/api.php?mode=schedule&id={self.event_id}&hash={hash_value}'

    async def get_age_divisions(self):
        """
        Получение данных о возрастных категориях.

        Returns:
            dict: Данные о возрастных категориях.
        """
        event_info = await self.get_event_info()
        rules = event_info["rules"]
        age_divisions = rules["age_divisions"]
        return age_divisions

    async def get_event_title(self):
        """
        Получение названия события.

        Returns:
           str: Название события.
        """
        event_info = await self.get_event_info()
        event = event_info["event"]
        title = event["title"]
        return title

    async def get_flags_event(self):
        """
        Получение флагов события.

        Returns:
           int: Флаг события.
        """
        event_info = await self.get_event_info()
        event = event_info["event"]
        flags = event["flags"]
        return int(flags)

    async def reg_pay(self):
        """
        Получение информации для оплаты регистрации.

        Returns:
            str: Текст с информацией для оплаты.
        """
        result_response = await self._api_request(
            mode="event_info&event_user_id", is_event=False
        )
        serialized_response = await asyncio.to_thread(
            phpserialize.loads, result_response.encode("utf-8")
        )
        # Получение информации о зарегистрированном участнике Турнира
        event_user_info = await asyncio.to_thread(decode_bytes, serialized_response)
        event = event_user_info["event"]
        event_user = event_user_info["event_user"]
        title = event["title"]

        # is_money2 = bool(int(event_user['flags']) & 0x10)
        # money = event_user['money']
        # money2 = event_user['money2']
        # money_amount = money2 if is_money2 else money
        # Стоимость стартового взноса составляет {money_amount} рублей\n

        reg_text = f"""
        {event_user["name"]}, Вы зарегистрировались на турнир {title} в категорию {event_user["cat_title"]}\n
        {remove_html_tags(event["reg_text"])}\n
        Если стартовый взнос не оплачен, заявка на турнир считается недействительной!
        """
        return reg_text

    async def register_user(self, registration_data):
        """
        Регистрация пользователя на мероприятие.

        Args:
            registration_data (dict): Данные для регистрации пользователя.

        Returns:
             str: Сообщение об успехе или ошибке регистрации.
        """
        raw_response = await self._api_request(
            mode="register", data=registration_data, method="post"
        )
        serialized_response = await asyncio.to_thread(
            phpserialize.loads, raw_response.encode("utf-8")
        )
        decoded_response = await asyncio.to_thread(decode_bytes, serialized_response)
        if "message" not in decoded_response:
            self.event_user_id = decoded_response["event_user_id"]
            return await self.reg_pay()
        else:
            return decoded_response["message"]


def md5_hash(s):
    """
    Вычисляет MD5-хеш строки.

    Args:
       s (str): Строка для хеширования.

    Returns:
        str: MD5-хеш строки в шестнадцатеричном формате.
    """
    return hashlib.md5(s.encode()).hexdigest()


def decode_bytes(data):
    """
    Декодирует байтовые строки в словаре или списке.

    Args:
        data: Данные для декодирования (словарь или список).

    Returns:
        Декодированные данные.
    """
    if isinstance(data, dict):
        return {decode_bytes(k): decode_bytes(v) for k, v in data.items()}
    if isinstance(data, list):
        return [decode_bytes(item) for item in data]
    if isinstance(data, bytes):
        try:
            return data.decode("utf-8")
        except UnicodeDecodeError:
            return data.decode("latin-1")
    return data


def remove_html_tags(text):
    """Удаляет HTML-теги из текста.

    Args:
        text: Строка, содержащая HTML-теги.

    Returns:
        Строка без HTML-тегов.
    """
    clean_text = re.sub(r"<[^>]*>", "", text)
    return clean_text
