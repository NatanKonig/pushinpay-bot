import asyncio
import re

from convopyro import listen_message
from pyrogram import Client, enums, filters
from pyrogram.errors import MessageNotModified
from pyrogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
)

from pixbot.bot import PixBot
from pixbot.logger import logger
from pixbot.models.transaction import Transaction, TransactionManager
from pixbot.utils.helpers import create_payment_keyboard, create_qr_code
from pixbot.utils.messages import LIMIT_EXCEEDED_MESSAGE  # Nova mensagem importada
from pixbot.utils.messages import limit_exceeded_keyboard  # Novo teclado importado
from pixbot.utils.messages import (
    CUSTOM_AMOUNT_MESSAGE,
    ERROR_MESSAGE,
    INVALID_FORMAT_MESSAGE,
    INVALID_VALUE_MESSAGE,
    PAYMENT_CANCELED_MESSAGE,
    PAYMENT_OPTIONS_MESSAGE,
    PROCESSING_MESSAGE,
    TIMEOUT_MESSAGE,
    custom_amount_keyboard,
    error_keyboard,
    format_payment_message,
    payment_canceled_keyboard,
    payment_details_keyboard,
    retry_custom_amount_keyboard,
)
from pixbot.utils.payment_api import (
    PaymentAPI,  # Nova exceção importada
    PIXValueExceededError,
)

# Estado para capturar valores personalizados
custom_amount_users = set()


@PixBot.on_message(filters.command("payment") & filters.private)
async def payment_command(client: Client, message: Message):
    """
    Manipulador para o comando /payment
    Atalho para iniciar um novo pagamento
    """
    # Mostra as opções de pagamento
    await show_payment_options_from_message(client, message)


@PixBot.on_callback_query(filters.regex(r"^payment:(\d+\.\d+|\d+)$"))
async def process_payment(client: Client, callback_query: CallbackQuery):
    """
    Processa um pagamento com valor pré-definido
    """
    user = callback_query.from_user
    value_match = re.match(r"payment:(\d+\.\d+|\d+)", callback_query.data)

    if value_match:
        value = float(value_match.group(1))
        logger.info(f"Usuário {user.id} solicitou pagamento de R$ {value:.2f}")

        # Notifica o usuário que o pagamento está sendo processado
        await callback_query.answer("Gerando pagamento, aguarde...")

        # Atualiza a mensagem para informar que está processando
        await callback_query.message.edit_text(PROCESSING_MESSAGE)

        try:
            # Gera o pagamento PIX
            pix_data = await PaymentAPI.generate_pix(value)

            # Cria uma nova transação
            transaction = Transaction.from_api_response(pix_data, user.id)
            TransactionManager.add_transaction(transaction)

            # Formata a mensagem com os detalhes do pagamento
            message_text = format_payment_message(
                value=transaction.amount,
                qr_code=transaction.qr_code,
                transaction_id=transaction.id,
            )

            # Cria teclado com opções para o pagamento
            keyboard = payment_details_keyboard(transaction.id)

            # Atualiza a mensagem com os detalhes do pagamento
            sent_message = await callback_query.message.edit_text(
                message_text,
                reply_markup=keyboard,
            )

            # Atualiza o ID da mensagem na transação
            transaction.message_id = sent_message.id

        except PIXValueExceededError as e:
            logger.warning(
                f"Valor excedido para pagamento: R$ {value:.2f}, limite: R$ {e.limit:.2f}"
            )

            # Notifica o usuário sobre o limite
            await callback_query.message.edit_text(
                LIMIT_EXCEEDED_MESSAGE.format(limit=e.limit),
                reply_markup=limit_exceeded_keyboard(),
            )

        except Exception as e:
            logger.error(f"Erro ao gerar pagamento: {str(e)}")

            # Notifica o usuário sobre o erro
            await callback_query.message.edit_text(
                ERROR_MESSAGE.format(details=str(e)), reply_markup=error_keyboard()
            )
    else:
        await callback_query.answer("Valor inválido")


async def show_payment_options_from_message(client: Client, message: Message):
    """
    Exibe as opções de pagamento a partir de uma mensagem
    """
    user = message.from_user
    logger.info(f"Usuário {user.id} solicitou opções de pagamento via comando")

    # Criar teclado com valores pré-definidos
    payment_keyboard = create_payment_keyboard()

    await message.reply(PAYMENT_OPTIONS_MESSAGE, reply_markup=payment_keyboard)


@PixBot.on_callback_query(filters.regex("^payment:custom$"))
async def request_custom_amount(client: Client, callback_query: CallbackQuery):
    """
    Solicita um valor personalizado para o pagamento usando convopyro
    """
    user_id = callback_query.from_user.id
    chat_id = callback_query.message.chat.id

    # Informa ao usuário que estamos esperando o valor
    await callback_query.message.edit_text(
        CUSTOM_AMOUNT_MESSAGE, reply_markup=custom_amount_keyboard()
    )

    # Responde ao callback query
    await callback_query.answer()

    try:
        # Espera a resposta do usuário com o valor personalizado
        response = await client.listen.Message(
            filters.text & filters.user(user_id), timeout=60
        )

        if response:
            # Remove o estado de captura, já que agora usamos listen
            if user_id in custom_amount_users:
                custom_amount_users.remove(user_id)

            # Tenta converter o texto enviado para um valor numérico
            try:
                # Remove qualquer caractere que não seja número ou ponto
                value_text = re.sub(r"[^\d.]", "", response.text)
                value = float(value_text)

                # Verifica se o valor é válido (maior que zero)
                if value <= 0:
                    await response.reply(
                        INVALID_VALUE_MESSAGE,
                        reply_markup=retry_custom_amount_keyboard(),
                    )
                    return

                # Notifica que está processando o pagamento
                processing_msg = await response.reply(PROCESSING_MESSAGE)

                try:
                    # Gera o pagamento PIX
                    pix_data = await PaymentAPI.generate_pix(value)

                    # Cria uma nova transação
                    transaction = Transaction.from_api_response(pix_data, user_id)
                    TransactionManager.add_transaction(transaction)

                    # Formata a mensagem com os detalhes do pagamento
                    message_text = format_payment_message(
                        value=transaction.amount,
                        qr_code=transaction.qr_code,
                        transaction_id=transaction.id,
                    )

                    # Cria teclado com opções para o pagamento
                    keyboard = payment_details_keyboard(transaction.id)

                    # Atualiza a mensagem com os detalhes do pagamento
                    sent_message = await processing_msg.edit_text(
                        message_text, reply_markup=keyboard
                    )

                    # Atualiza o ID da mensagem na transação
                    transaction.message_id = sent_message.id

                except PIXValueExceededError as e:
                    logger.warning(
                        f"Valor excedido para pagamento: R$ {value:.2f}, limite: R$ {e.limit:.2f}"
                    )

                    # Teclado para tentar novamente com valor menor
                    keyboard = limit_exceeded_keyboard()

                    # Notifica o usuário sobre o limite
                    await processing_msg.edit_text(
                        LIMIT_EXCEEDED_MESSAGE.format(limit=e.limit),
                        reply_markup=keyboard,
                    )

                except Exception as e:
                    logger.error(f"Erro ao gerar pagamento: {str(e)}")

                    # Notifica o usuário sobre o erro
                    await processing_msg.edit_text(
                        ERROR_MESSAGE.format(details=str(e)),
                        reply_markup=error_keyboard(),
                    )

            except ValueError:
                # Valor não pôde ser convertido para float
                await response.reply(
                    INVALID_FORMAT_MESSAGE, reply_markup=retry_custom_amount_keyboard()
                )
    except asyncio.TimeoutError:
        # Se o tempo expirar, notifica o usuário
        await client.send_message(
            chat_id, TIMEOUT_MESSAGE, reply_markup=retry_custom_amount_keyboard()
        )
    except Exception as e:
        logger.error(f"Erro ao processar valor personalizado: {str(e)}")
        await client.send_message(
            chat_id,
            ERROR_MESSAGE.format(details="Não foi possível processar sua solicitação."),
            reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(
                            "◀️ Voltar", callback_data="show_payment_options"
                        )
                    ]
                ]
            ),
        )


@PixBot.on_callback_query(filters.regex("^cancel_payment$"))
async def cancel_payment_request(client: Client, callback_query: CallbackQuery):
    """
    Cancela o pedido de valor personalizado
    """
    user_id = callback_query.from_user.id

    # Cancela a escuta de mensagens para este usuário
    await client.listen.Cancel(filters.user(user_id))

    # Remove do set de usuários esperando valor personalizado (caso esteja usando o método antigo)
    if user_id in custom_amount_users:
        custom_amount_users.remove(user_id)

    await callback_query.message.edit_text(
        PAYMENT_CANCELED_MESSAGE, reply_markup=payment_canceled_keyboard()
    )

    await callback_query.answer("Solicitação de pagamento cancelada")


@PixBot.on_message((filters.private) & (filters.text) & (~filters.regex("^/")))
async def handle_custom_amount(client: Client, message: Message):
    """
    Manipulador genérico para mensagens de texto que não são comandos
    Mantido apenas para compatibilidade, mas não faz nada específico
    já que estamos usando o convopyro para conversas
    """
    # Este handler está vazio, usamos convopyro.listen para gerenciar as entradas do usuário
    pass
