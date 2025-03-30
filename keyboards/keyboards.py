from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

from config import start_btn  # Импортируем текст кнопки из config.py

# --- Создание основной клавиатуры ---
# Создаем объект ReplyKeyboardMarkup для основной клавиатуры
keyboard = ReplyKeyboardMarkup(
    resize_keyboard=True,  # Автоматически подстраивает размер клавиатуры под размер экрана
    keyboard=[
        [
            KeyboardButton(text=start_btn),  # Создаем кнопку с текстом "Начать сначала"
        ],
    ]
)
