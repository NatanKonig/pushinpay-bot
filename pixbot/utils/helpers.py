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


def format_payment_message(value: float, qr_code: str, transaction_id: str) -> str:
    """
    Formata a mensagem de pagamento PIX
    
    Args:
        value: Valor do pagamento
        qr_code: Código PIX copia e cola
        transaction_id: ID da transação
        
    Returns:
        Mensagem formatada
    """
    return (
        f"🧾 *Detalhes do pagamento:*\n\n"
        f"💰 *Valor:* R$ {value:.2f}\n\n"
        f"📲 *Chave Copia e Cola:*\n"
        f"`{qr_code}`\n\n"
        f"👉 Você também pode visualizar o QR Code e escanear com seu aplicativo bancário.\n\n"
        f"ID da transação: `{transaction_id}`"
    )


def payment_status_message(status: str) -> str:
    """
    Retorna a mensagem correspondente ao status do pagamento
    
    Args:
        status: Status do pagamento
        
    Returns:
        Mensagem formatada
    """
    status_messages = {
        "pending": "⏳ *Aguardando pagamento*\nO pagamento ainda não foi confirmado.",
        "paid": "✅ *Pagamento confirmado!*\nObrigado por utilizar nosso serviço.",
        "expired": "⌛ *Pagamento expirado*\nO tempo para pagamento expirou.",
        "canceled": "❌ *Pagamento cancelado*\nEsta transação foi cancelada.",
        "failed": "⚠️ *Falha no pagamento*\nOcorreu um erro durante o processamento."
    }
    
    return status_messages.get(status, f"Status desconhecido: {status}")


def is_admin(user_id: int) -> bool:
    """
    Verifica se o usuário é um administrador do bot
    
    Args:
        user_id: ID do usuário
    
    Returns:
        True se for admin, False caso contrário
    """
    return user_id in settings.admin_ids