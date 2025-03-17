"""
Handlers para callbacks gerais que não se encaixam em outros módulos
"""

import re
import time

from pyrogram import Client, enums, filters
from pyrogram.errors import MessageNotModified
from pyrogram.types import CallbackQuery

from pixbot.bot import PixBot
from pixbot.logger import logger
from pixbot.models.transaction import TransactionManager
from pixbot.utils.helpers import create_qr_code
from pixbot.utils.messages import (
    PAYMENT_DETAILS_MESSAGE,
    QR_CODE_CAPTION,
    format_payment_message,
    get_completed_payment_keyboard,
    get_failed_payment_keyboard,
    get_pending_payment_keyboard,
    payment_details_keyboard,
    payment_status_message,
)
from pixbot.utils.payment_api import PaymentAPI

payment_check_cooldown = {}
COOLDOWN_SECONDS = 5

# Lista de callbacks manipulados em outros arquivos
# Isso ajuda a evitar registrar um callback mais de uma vez
callbacks_handled_elsewhere = [
    r"^payment:",
    r"^show_payment_options$",
    r"^help$",
    r"^about$",
    r"^back_to_start$",
    r"^show_qr:",
    r"^check_payment:",
]


@Client.on_callback_query(filters.regex(r"^back_to_pix:(.+)$"))
async def back_to_pix_details(client: Client, callback_query: CallbackQuery):
    """
    Retorna à visualização do código PIX original após verificar o status
    """
    match = re.match(r"back_to_pix:(.+)", callback_query.data)
    if match:
        transaction_id = match.group(1)
        logger.info(
            f"Usuário {callback_query.from_user.id} solicitou retorno ao código PIX: {transaction_id}"
        )

        # Busca a transação
        transaction = TransactionManager.get_transaction(transaction_id)

        if transaction:
            # Notifica sobre a ação
            await callback_query.answer("Voltando aos detalhes do pagamento...")

            # Formata a mensagem com os detalhes do pagamento
            message_text = format_payment_message(
                value=transaction.amount,
                qr_code=transaction.qr_code,
                transaction_id=transaction.id,
            )

            # Cria teclado com opções para o pagamento
            keyboard = payment_details_keyboard(transaction.id)

            # Atualiza a mensagem com os detalhes completos do pagamento
            await callback_query.message.edit_text(message_text, reply_markup=keyboard)
        else:
            await callback_query.answer("Transação não encontrada", show_alert=True)
    else:
        await callback_query.answer("Dados inválidos", show_alert=True)


@Client.on_callback_query(filters.regex(r"^check_payment:(.+)$"))
async def check_payment(client: Client, callback_query: CallbackQuery):
    """
    Verifica o status do pagamento
    """
    match = re.match(r"check_payment:(.+)", callback_query.data)
    if match:
        transaction_id = match.group(1)
        user_id = callback_query.from_user.id
        cooldown_key = f"{user_id}:{transaction_id}"
        current_time = time.time()

        # Verifica se está em cooldown
        if cooldown_key in payment_check_cooldown:
            last_check_time = payment_check_cooldown[cooldown_key]
            time_passed = current_time - last_check_time

            if time_passed < COOLDOWN_SECONDS:
                remaining_time = round(COOLDOWN_SECONDS - time_passed)
                await callback_query.answer(
                    f"Aguarde {remaining_time} segundos antes de verificar novamente",
                    show_alert=True,
                )
                return

        # Atualiza o timestamp do último check
        payment_check_cooldown[cooldown_key] = current_time

        logger.info(f"Usuário {user_id} verificando pagamento: {transaction_id}")

        # Busca a transação
        transaction = TransactionManager.get_transaction(transaction_id)

        if transaction:
            old_status = transaction.status

            # Notifica que está verificando
            await callback_query.answer("Verificando pagamento...")

            try:
                # Consulta o status do pagamento
                status_data = await PaymentAPI.check_payment_status(transaction_id)

                # Atualiza a transação com os dados mais recentes
                updated_transaction = TransactionManager.update_transaction(
                    transaction_id, status_data
                )

                if updated_transaction:
                    # Obtém a mensagem formatada para o status
                    status_msg = payment_status_message(updated_transaction.status)

                    # Determina os botões com base no status
                    keyboard = None

                    if updated_transaction.is_paid():
                        keyboard = get_completed_payment_keyboard(transaction_id)
                    elif updated_transaction.is_pending():
                        keyboard = get_pending_payment_keyboard(transaction_id)
                    else:
                        keyboard = get_failed_payment_keyboard(transaction_id)

                    new_message = PAYMENT_DETAILS_MESSAGE.format(
                        amount=updated_transaction.amount,
                        status_msg=status_msg,
                        transaction_id=transaction_id,
                    )

                    try:
                        # Atualiza a mensagem com o status atual
                        await callback_query.message.edit_text(
                            text=new_message, reply_markup=keyboard
                        )
                    except MessageNotModified:
                        # Se o status não mudou, apenas informa ao usuário
                        if old_status == updated_transaction.status:
                            await callback_query.answer(
                                f"O status do pagamento continua como {updated_transaction.status}",
                                show_alert=True,
                            )
                        else:
                            await callback_query.answer(
                                "Informações atualizadas", show_alert=False
                            )
                else:
                    await callback_query.answer(
                        "Erro ao atualizar transação", show_alert=True
                    )
            except Exception as e:
                logger.error(f"Erro ao verificar status do PIX: {str(e)}")
                await callback_query.answer(
                    "Erro ao verificar pagamento", show_alert=True
                )
        else:
            await callback_query.answer("Transação não encontrada", show_alert=True)
    else:
        await callback_query.answer("Dados inválidos", show_alert=True)


@Client.on_callback_query(filters.regex(r"^show_qr:(.+)$"))
async def show_qr_code(client: Client, callback_query: CallbackQuery):
    """
    Exibe o QR Code para o pagamento
    """
    match = re.match(r"show_qr:(.+)", callback_query.data)
    if match:
        transaction_id = match.group(1)
        logger.info(
            f"Usuário {callback_query.from_user.id} solicitou QR code: {transaction_id}"
        )

        # Busca a transação
        transaction = TransactionManager.get_transaction(transaction_id)

        if transaction:
            # Gera o QR Code
            qr_image = create_qr_code(transaction.qr_code)

            # Responde o callback query
            await callback_query.answer("Gerando QR Code...")

            # Envia o QR Code como foto
            await client.send_photo(
                chat_id=callback_query.message.chat.id,
                photo=qr_image,
                caption=QR_CODE_CAPTION.format(amount=transaction.amount),
            )
        else:
            await callback_query.answer("Transação não encontrada", show_alert=True)
    else:
        await callback_query.answer("Dados inválidos", show_alert=True)


@PixBot.on_callback_query(~filters.regex("|".join(callbacks_handled_elsewhere)))
async def unhandled_callback(client: Client, callback_query: CallbackQuery):
    """
    Manipulador para callbacks não reconhecidos
    """
    logger.warning(
        f"Callback não reconhecido: {callback_query.data} de usuário {callback_query.from_user.id}"
    )

    await callback_query.answer(
        "Esta opção não está disponível no momento.", show_alert=True
    )


@PixBot.on_callback_query(filters.regex("^cancel_operation$"))
async def cancel_operation(client: Client, callback_query: CallbackQuery):
    """
    Cancela a operação atual e retorna ao menu inicial
    """
    from pixbot.plugins.start import back_to_start

    await callback_query.answer("Operação cancelada")
    await back_to_start(client, callback_query)
