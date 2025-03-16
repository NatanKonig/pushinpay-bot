from pyrogram import Client, filters, enums
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
import asyncio
from convopyro import listen_message

from pixbot.logger import logger
from pixbot.utils.helpers import create_payment_keyboard
from pixbot.bot import PixBot

# Mensagem de boas-vindas
WELCOME_MESSAGE = """
👋 *Bem-vindo ao Bot de Pagamentos PIX!*

Com este bot, você pode:
• Gerar QR Codes para receber pagamentos
• Verificar o status dos seus pagamentos
• Receber notificações automáticas

Use os botões abaixo para começar.
"""


@PixBot.on_message(filters.command("start") & filters.private)
async def start_command(client: Client, message: Message):
    """
    Manipulador para o comando /start
    Envia uma mensagem de boas-vindas com opções para o usuário
    """
    user = message.from_user
    logger.info(f"Usuário {user.id} ({user.first_name}) iniciou o bot")
    
    # Teclado com opções principais
    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("💰 Gerar Pagamento", callback_data="show_payment_options")
        ],
        [
            InlineKeyboardButton("❓ Ajuda", callback_data="help"),
            InlineKeyboardButton("ℹ️ Sobre", callback_data="about")
        ]
    ])
    
    # Envia a mensagem de boas-vindas
    await message.reply(
        WELCOME_MESSAGE,
        reply_markup=keyboard
    )


@PixBot.on_callback_query(filters.regex("^show_payment_options$"))
async def show_payment_options(client: Client, callback_query: CallbackQuery):
    """
    Exibe as opções de pagamento disponíveis
    """
    user = callback_query.from_user
    logger.info(f"Usuário {user.id} solicitou opções de pagamento")
    
    # Obtém o teclado com valores de pagamento
    payment_keyboard = create_payment_keyboard()
    
    await callback_query.message.edit_text(
        "💰 *Selecione o valor do pagamento:*\n\n"
        "Escolha um dos valores pré-definidos ou selecione 'Valor Personalizado' para inserir outro valor.",
        reply_markup=payment_keyboard
    )
    
    # Responde ao callback query
    await callback_query.answer()


@PixBot.on_callback_query(filters.regex("^help$"))
async def show_help(client: Client, callback_query: CallbackQuery):
    """
    Exibe a mensagem de ajuda
    """
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("◀️ Voltar", callback_data="back_to_start")]
    ])
    
    await callback_query.message.edit_text(
        "❓ *Ajuda e Instruções*\n\n"
        "Este bot permite gerar pagamentos PIX de forma simples e rápida.\n\n"
        "*Como usar:*\n"
        "1. Clique em 'Gerar Pagamento'\n"
        "2. Selecione um valor ou insira um valor personalizado\n"
        "3. Compartilhe o QR Code gerado ou use a chave Copia e Cola\n"
        "4. O bot notificará quando o pagamento for confirmado\n\n"
        "*Comandos disponíveis:*\n"
        "/start - Inicia o bot\n"
        "/payment - Atalho para gerar um novo pagamento\n"
        "/status - Verificar status dos seus pagamentos recentes",
        reply_markup=keyboard
    )
    
    await callback_query.answer()


@PixBot.on_callback_query(filters.regex("^about$"))
async def show_about(client: Client, callback_query: CallbackQuery):
    """
    Exibe informações sobre o bot
    """
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("◀️ Voltar", callback_data="back_to_start")]
    ])
    
    await callback_query.message.edit_text(
        "ℹ️ *Sobre o Bot de Pagamentos PIX*\n\n"
        "Este bot foi desenvolvido com Pyrogram e integra-se à API de pagamentos PushinPay "
        "para fornecer uma solução completa de pagamentos via PIX diretamente no Telegram.\n\n"
        "Desenvolvido com ❤️ usando Python e Pyrogram.\n\n"
        "Versão: 1.0.0",
        reply_markup=keyboard
    )
    
    await callback_query.answer()


@PixBot.on_callback_query(filters.regex("^back_to_start$"))
async def back_to_start(client: Client, callback_query: CallbackQuery):
    """
    Retorna ao menu inicial
    """
    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("💰 Gerar Pagamento", callback_data="show_payment_options")
        ],
        [
            InlineKeyboardButton("❓ Ajuda", callback_data="help"),
            InlineKeyboardButton("ℹ️ Sobre", callback_data="about")
        ]
    ])
    
    await callback_query.message.edit_text(
        WELCOME_MESSAGE,
        reply_markup=keyboard
    )
    
    await callback_query.answer()