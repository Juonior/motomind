from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, field_validator
from typing import Optional


class Settings(BaseSettings):
    """Настройки приложения"""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True
    )
    
    # Обязательные настройки
    BOT_TOKEN: str = Field(..., description="Токен Telegram бота")
    
    # OBD настройки
    OBD_PORT: Optional[str] = Field(default=None, description="Порт OBD адаптера (например, /dev/rfcomm0 или COM3)")
    OBD_MAC: Optional[str] = Field(default=None, description="MAC адрес Bluetooth OBD адаптера (для автоматического создания RFCOMM порта)")
    OBD_PROTOCOL: Optional[str] = Field(default=None, description="Протокол OBD (auto если None)")
    
    # Настройки бота
    ADMIN_IDS: Optional[str] = Field(default=None, description="ID администраторов бота (через запятую)")
    
    @property
    def admin_ids_list(self) -> list[int]:
        """Получить список ID администраторов"""
        if not self.ADMIN_IDS:
            return []
        try:
            return [int(x.strip()) for x in self.ADMIN_IDS.split(',') if x.strip()]
        except (ValueError, AttributeError):
            return []


settings = Settings()

