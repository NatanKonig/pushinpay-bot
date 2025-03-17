import asyncio

from convopyro import listen_message
from pyrogram import Client, enums, filters
from pyrogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
)

from pixbot.bot import PixBot
from pixbot.logger import logger
from pixbot.utils.helpers import create_payment_keyboard
from pixbot.utils.messages import (
    ABOUT_MESSAGE,
    HELP_MESSAGE,
    PAYMENT_OPTIONS_MESSAGE,
    WELCOME_MESSAGE,
    main_menu_keyboard,
)

# Removida a definição de WELCOME_MESSAGE, agora importada de messages.py


@PixBot.on_message(filters.command("start") & filters.private)
async def start_command(client: Client, message: Message):
    """
    Manipulador para o comando /start
    Envia uma mensagem de boas-vindas com opções para o usuário
    """
    user = message.from_user
    logger.info(f"Usuário {user.id} ({user.first_name}) iniciou o bot")

    # Obtém o teclado do menu principal
    keyboard = main_menu_keyboard()

    # Envia a mensagem de boas-vindas
    await message.reply(WELCOME_MESSAGE, reply_markup=keyboard)


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
        PAYMENT_OPTIONS_MESSAGE, reply_markup=payment_keyboard
    )

    # Responde ao callback query
    await callback_query.answer()


@PixBot.on_callback_query(filters.regex("^help$"))
async def show_help(client: Client, callback_query: CallbackQuery):
    """
    Exibe a mensagem de ajuda
    """
    keyboard = InlineKeyboardMarkup(
        [[InlineKeyboardButton("◀️ Voltar", callback_data="back_to_start")]]
    )

    await callback_query.message.edit_text(HELP_MESSAGE, reply_markup=keyboard)

    await callback_query.answer()


@PixBot.on_callback_query(filters.regex("^about$"))
async def show_about(client: Client, callback_query: CallbackQuery):
    """
    Exibe informações sobre o bot
    """
    keyboard = InlineKeyboardMarkup(
        [[InlineKeyboardButton("◀️ Voltar", callback_data="back_to_start")]]
    )

    await callback_query.message.edit_text(ABOUT_MESSAGE, reply_markup=keyboard)

    await callback_query.answer()


@PixBot.on_callback_query(filters.regex("^back_to_start$"))
async def back_to_start(client: Client, callback_query: CallbackQuery):
    """
    Retorna ao menu inicial
    """
    keyboard = main_menu_keyboard()

    await callback_query.message.edit_text(WELCOME_MESSAGE, reply_markup=keyboard)

    await callback_query.answer()
