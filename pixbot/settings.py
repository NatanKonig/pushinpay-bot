import os
from pathlib import Path

from pydantic import field_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    bot_name: str
    bot_token: str
    api_id: int
    api_hash: str
    admin_ids: list[int] | int
    
    # Configurações da API de Pagamentos PIX
    pix_api_url: str = "https://api.pushinpay.com.br/api/pix/cashIn"
    pix_status_url: str = "https://api.pushinpay.com.br/api/transactions/"
    pix_api_token: str

    # Configurações do webhook para receber notificações de pagamento (opcional)
    webhook_url: str = ""
    
    # Valores pré-definidos para pagamentos (em reais)
    payment_values: list[float] = [5, 10, 20, 50, 100]
    
    # Configurações de logs
    log_level: str = "INFO"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
        extra = "allow"

    def __init__(self, **data):
        super().__init__(**data)
        self.BASE_DIR = Path(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        )
        self._create_directories()

    @field_validator("admin_ids", mode="before")
    def parse_admin_ids(cls, value):
        if isinstance(value, str):
            if "," in value:
                return [int(id.strip()) for id in value.split(",")]
            else:
                return [int(value)]
        elif isinstance(value, int):
            return [value]
        return value
        
    @field_validator("payment_values", mode="before")
    def parse_payment_values(cls, value):
        if isinstance(value, str):
            if "," in value:
                return [float(val.strip()) for val in value.split(",")]
            else:
                return [float(value)]
        return value

    def _create_directories(self):
        """Create necessary directories if they don't exist"""
        os.makedirs("sessions", exist_ok=True)
        os.makedirs("logs", exist_ok=True)