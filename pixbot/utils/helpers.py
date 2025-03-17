"""
Funções auxiliares para o bot
"""
import qrcode
from io import BytesIO
from typing import Dict, Any
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram import enums

from pixbot.logger import logger
from pixbot.settings import Settings
from pixbot.utils.messages import format_payment_message, payment_status_message  # Importando das mensagens

settings = Settings()


def create_qr_code(data: str) -> BytesIO:
    """
    Cria um QR Code a partir de uma string
    
    Args:
        data: String a ser codificada no QR Code
        
    Returns:
        BytesIO contendo a imagem do QR Code
    """
    logger.debug(f"Gerando QR Code para os dados: {data[:20]}...")
    
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(data)
    qr.make(fit=True)

    img = qr.make_image(fill_color="black", back_color="white")
    
    # Converte a imagem para BytesIO
    img_io = BytesIO()
    img.save(img_io, 'PNG')
    img_io.seek(0)
    
    return img_io


def create_payment_keyboard() -> InlineKeyboardMarkup:
    """
    Cria um teclado com os valores de pagamento pré-definidos
    
    Returns:
        InlineKeyboardMarkup com os botões de pagamento
    """
    buttons = []
    
    # Adiciona botões para valores pré-definidos
    row = []
    for i, value in enumerate(settings.payment_values, 1):
        row.append(
            InlineKeyboardButton(
                f"R$ {value:.2f}".replace('.', ','), 
                callback_data=f"payment:{value}"
            )
        )
        
        # Cria nova linha a cada 2 botões
        if i % 2 == 0 or i == len(settings.payment_values):
            buttons.append(row)
            row = []
    
    # Adiciona botão para valor personalizado
    buttons.append([
        InlineKeyboardButton(
            "➕ Valor Personalizado", 
            callback_data="payment:custom"
        )
    ])
    
    return InlineKeyboardMarkup(buttons)