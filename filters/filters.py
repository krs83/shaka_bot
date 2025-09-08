from aiogram.filters import Filter
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from config import start_btn


class EmptyStateMessageFilter(Filter):
    """
    Фильтр для сообщений, срабатывает, если состояние FSM пустое
    и текст сообщения не равен кнопке "Начать сначала".
    """

    async def __call__(self, message: Message, state: FSMContext) -> bool:
        """
        Проверяет, что состояние FSM пустое и текст сообщения не равен кнопке "Начать сначала".

        Args:
            message: Объект Message.
            state: Объект FSMContext.

        Returns:
            True, если фильтр срабатывает, False - в противном случае.
        """
        data = await state.get_data()  # Получаем данные из текущего состояния FSM
        if data:
            return False  # Если есть данные, фильтр не срабатывает
        if message.text == start_btn or message.text == "/start":
            return False  # Если текст сообщения равен кнопке "Начать сначала", фильтр не срабатывает
        return True  # В остальных случаях фильтр срабатывает


class EmptyStateCallbackFilter(Filter):
    """
    Фильтр для callback_query, срабатывает, если состояние FSM пустое
    и data callback'а не равен кнопке "Начать сначала".
    """

    async def __call__(self, callback: CallbackQuery, state: FSMContext) -> bool:
        """
        Проверяет, что состояние FSM пустое и data callback'а не равен кнопке "Начать сначала".

        Args:
            callback: Объект CallbackQuery.
            state: Объект FSMContext.

        Returns:
            True, если фильтр срабатывает, False - в противном случае.
        """
        data = await state.get_data()  # Получаем данные из текущего состояния FSM
        if data:
            return False  # Если есть данные, фильтр не срабатывает
        if callback.data == start_btn:
            return False  # Если data callback'а равна кнопке "Начать сначала", фильтр не срабатывает
        return True  # В остальных случаях фильтр срабатывает
