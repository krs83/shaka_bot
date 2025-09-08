import re

from pydantic import BaseModel, EmailStr, field_validator

class UserEmail(BaseModel):
    email: EmailStr


class PhoneNumber(BaseModel):
    number: str

    @field_validator('number')
    @classmethod
    def validate_phone_number(cls, v):
        # Убираем все нецифровые символы кроме +
        cleaned = re.sub(r'[^\d+]', '', v)

        # Теперь проверяем очищенную строку
        if not re.match(r'^(\+\d+|\d+)$', cleaned):
            raise ValueError('Номер должен содержать только цифры и может начинаться с +')

        if len(cleaned) < 10:
            raise ValueError('Номер слишком короткий!')

        if len(cleaned) > 12:
            raise ValueError('Похоже номер слишком длинный!')

        return cleaned


