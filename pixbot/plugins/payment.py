import re
from pyrogram import Client, filters, enums
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from pyrogram.errors import MessageNotModified
import asyncio

from pixbot.logger import logger
from pixbot.utils.payment_api import PaymentAPI
from pixbot.utils.helpers import create_qr_code, create_payment_keyboard
from pixbot.utils.messages import (
    PAYMENT_OPTIONS_MESSAGE, CUSTOM_AMOUNT_MESSAGE, PROCESSING_MESSAGE,
    TIMEOUT_MESSAGE, INVALID_VALUE_MESSAGE, INVALID_FORMAT_MESSAGE,
    ERROR_MESSAGE, PAYMENT_CANCELED_MESSAGE, QR_CODE_CAPTION,
    format_payment_message, payment_status_message,
    payment_details_keyboard, error_keyboard, custom_amount_keyboard,
    retry_custom_amount_keyboard, payment_canceled_keyboard,
    get_pending_payment_keyboard, get_completed_payment_keyboard,
    get_failed_payment_keyboard
)
from pixbot.models.transaction import Transaction, TransactionManager
from pixbot.bot import PixBot
from convopyro import listen_message

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
                transaction_id=transaction.id
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
            
        except Exception as e:
            logger.error(f"Erro ao gerar pagamento: {str(e)}")
            
            # Notifica o usuário sobre o erro
            await callback_query.message.edit_text(
                ERROR_MESSAGE.format(details=str(e)),
                reply_markup=error_keyboard()
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
    
    await message.reply(
        PAYMENT_OPTIONS_MESSAGE,
        reply_markup=payment_keyboard
    )
    
    
@PixBot.on_callback_query(filters.regex("^payment:custom$"))
async def request_custom_amount(client: Client, callback_query: CallbackQuery):
    """
    Solicita um valor personalizado para o pagamento usando convopyro
    """
    user_id = callback_query.from_user.id
    chat_id = callback_query.message.chat.id
    
    # Informa ao usuário que estamos esperando o valor
    await callback_query.message.edit_text(
        CUSTOM_AMOUNT_MESSAGE,
        reply_markup=custom_amount_keyboard()
    )
    
    # Responde ao callback query
    await callback_query.answer()
    
    try:
        # Espera a resposta do usuário com o valor personalizado
        response = await client.listen.Message(
            filters.text & filters.user(user_id),
            timeout=60
        )
        
        if response:
            # Remove o estado de captura, já que agora usamos listen
            if user_id in custom_amount_users:
                custom_amount_users.remove(user_id)
            
            # Tenta converter o texto enviado para um valor numérico
            try:
                # Remove qualquer caractere que não seja número ou ponto
                value_text = re.sub(r'[^\d.]', '', response.text)
                value = float(value_text)
                
                # Verifica se o valor é válido (maior que zero)
                if value <= 0:
                    await response.reply(
                        INVALID_VALUE_MESSAGE,
                        reply_markup=retry_custom_amount_keyboard()
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
                        transaction_id=transaction.id
                    )
                    
                    # Cria teclado com opções para o pagamento
                    keyboard = payment_details_keyboard(transaction.id)
                    
                    # Atualiza a mensagem com os detalhes do pagamento
                    sent_message = await processing_msg.edit_text(
                        message_text,
                        reply_markup=keyboard
                    )
                    
                    # Atualiza o ID da mensagem na transação
                    transaction.message_id = sent_message.id
                    
                except Exception as e:
                    logger.error(f"Erro ao gerar pagamento: {str(e)}")
                    
                    # Notifica o usuário sobre o erro
                    await processing_msg.edit_text(
                        ERROR_MESSAGE.format(details=str(e)),
                        reply_markup=error_keyboard()
                    )
                    
            except ValueError:
                # Valor não pôde ser convertido para float
                await response.reply(
                    INVALID_FORMAT_MESSAGE,
                    reply_markup=retry_custom_amount_keyboard()
                )
    except asyncio.TimeoutError:
        # Se o tempo expirar, notifica o usuário
        await client.send_message(
            chat_id,
            TIMEOUT_MESSAGE,
            reply_markup=retry_custom_amount_keyboard()
        )
    except Exception as e:
        logger.error(f"Erro ao processar valor personalizado: {str(e)}")
        await client.send_message(
            chat_id,
            ERROR_MESSAGE.format(details="Não foi possível processar sua solicitação."),
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("◀️ Voltar", callback_data="show_payment_options")]
            ])
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
        PAYMENT_CANCELED_MESSAGE,
        reply_markup=payment_canceled_keyboard()
    )
    
    await callback_query.answer("Solicitação de pagamento cancelada")


@PixBot.on_callback_query(filters.regex(r"^show_qr:(.+)$"))
async def show_qr_code(client: Client, callback_query: CallbackQuery):
    """
    Exibe o QR Code para o pagamento
    """
    match = re.match(r"show_qr:(.+)", callback_query.data)
    if match:
        transaction_id = match.group(1)
        
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


@PixBot.on_callback_query(filters.regex(r"^check_payment:(.+)$"))
async def check_payment(client: Client, callback_query: CallbackQuery):
    """
    Verifica o status do pagamento
    """
    match = re.match(r"check_payment:(.+)", callback_query.data)
    if match:
        transaction_id = match.group(1)
        
        # Busca a transação
        transaction = TransactionManager.get_transaction(transaction_id)
        
        if transaction:
            # Notifica que está verificando
            await callback_query.answer("Verificando pagamento...")
            
            try:
                # Consulta o status do pagamento
                status_data = await PaymentAPI.check_payment_status(transaction_id)
                
                # Atualiza a transação com os dados mais recentes
                updated_transaction = TransactionManager.update_transaction(transaction_id, status_data)
                
                if updated_transaction:
                    # Obtém a mensagem formatada para o status
                    status_msg = payment_status_message(updated_transaction.status)
                    
                    # Determina os botões com base no status
                    keyboard = None
                    
                    if updated_transaction.is_paid():
                        keyboard = get_completed_payment_keyboard()
                    elif updated_transaction.is_pending():
                        keyboard = get_pending_payment_keyboard(transaction_id)
                    else:
                        keyboard = get_failed_payment_keyboard()
                    
                    # Atualiza a mensagem com o status atual
                    await callback_query.message.edit_text(
                        text=format_payment_message(
                            value=updated_transaction.amount,
                            qr_code="", # Removido propositalmente para mostrar apenas o status
                            transaction_id=transaction_id
                        ).split("📲")[0] + f"\n{status_msg}\n\nID da transação: `{transaction_id}`",
                        reply_markup=keyboard
                    )
                else:
                    await callback_query.answer("Erro ao atualizar transação", show_alert=True)
            except Exception as e:
                logger.error(f"Erro ao verificar status do PIX: {str(e)}")
                await callback_query.answer("Erro ao verificar pagamento", show_alert=True)
        else:
            await callback_query.answer("Transação não encontrada", show_alert=True)
    else:
        await callback_query.answer("Dados inválidos", show_alert=True)