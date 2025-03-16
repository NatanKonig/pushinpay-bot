"""
Handlers para callbacks gerais que não se encaixam em outros módulos
"""
from pyrogram import Client, filters, enums
from pyrogram.types import CallbackQuery

from pixbot.logger import logger
from pixbot.bot import PixBot

# Lista de callbacks manipulados em outros arquivos
# Isso ajuda a evitar registrar um callback mais de uma vez
callbacks_handled_elsewhere = [
    r"^payment:",
    r"^show_payment_options$",
    r"^help$",
    r"^about$",
    r"^back_to_start$",
    r"^show_qr:",
    r"^check_payment:"
]

@PixBot.on_callback_query(~filters.regex("|".join(callbacks_handled_elsewhere)))
async def unhandled_callback(client: Client, callback_query: CallbackQuery):
    """
    Manipulador para callbacks não reconhecidos
    """
    logger.warning(f"Callback não reconhecido: {callback_query.data} de usuário {callback_query.from_user.id}")
    
    await callback_query.answer(
        "Esta opção não está disponível no momento.",
        show_alert=True
    )

@PixBot.on_callback_query(filters.regex("^cancel_operation$"))
async def cancel_operation(client: Client, callback_query: CallbackQuery):
    """
    Cancela a operação atual e retorna ao menu inicial
    """
    from pixbot.plugins.start import back_to_start
    
    await callback_query.answer("Operação cancelada")
    await back_to_start(client, callback_query)