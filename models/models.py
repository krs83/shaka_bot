import re

from pydantic import BaseModel, EmailStr, field_validator, Field


class UserEmail(BaseModel):
    email: EmailStr


class PhoneNumber(BaseModel):
    number: str

    @field_validator("number")
    @classmethod
    def validate_phone_number(cls, v):
        # Убираем все нецифровые символы кроме +
        cleaned = re.sub(r"[^\d+]", "", v)

        # Теперь проверяем очищенную строку
        if not re.match(r"^(\+\d+|\d+)$", cleaned):
            raise ValueError(
                "Номер должен содержать только цифры и может начинаться с +"
            )

        if len(cleaned) < 10:
            raise ValueError("Номер слишком короткий!")

        if len(cleaned) > 12:
            raise ValueError("Похоже номер слишком длинный!")

        return cleaned


class UserName(BaseModel):
    name: str = Field(min_length=3, pattern=r"^[a-zA-Zа-яА-ЯёЁ\s\-]+$")
