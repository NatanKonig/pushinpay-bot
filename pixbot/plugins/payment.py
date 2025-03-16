import re
from pyrogram import Client, filters, enums
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from pyrogram.errors import MessageNotModified
import asyncio

from pixbot.logger import logger
from pixbot.utils.payment_api import PaymentAPI
from pixbot.utils.helpers import create_qr_code, format_payment_message, payment_status_message, create_payment_keyboard
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
        await callback_query.message.edit_text(
            "⏳ *Processando sua solicitação...*\n\n"
            "Estamos gerando seu QR Code PIX, isso pode levar alguns segundos."
        )
        
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
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("👁️ Ver QR Code", callback_data=f"show_qr:{transaction.id}")],
                [InlineKeyboardButton("🔄 Verificar Pagamento", callback_data=f"check_payment:{transaction.id}")],
                [InlineKeyboardButton("◀️ Voltar", callback_data="back_to_start")]
            ])
            
            # Atualiza a mensagem com os detalhes do pagamento
            sent_message = await callback_query.message.edit_text(
                message_text,
                reply_markup=keyboard
            )
            
            # Atualiza o ID da mensagem na transação
            transaction.message_id = sent_message.id
            
        except Exception as e:
            logger.error(f"Erro ao gerar pagamento: {str(e)}")
            
            # Notifica o usuário sobre o erro
            await callback_query.message.edit_text(
                f"❌ *Ocorreu um erro ao gerar o pagamento*\n\n"
                f"Detalhes: {str(e)}\n\n"
                f"Por favor, tente novamente mais tarde.",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔄 Tentar Novamente", callback_data="show_payment_options")],
                    [InlineKeyboardButton("◀️ Voltar ao Início", callback_data="back_to_start")]
                ])
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
        "💰 *Selecione o valor do pagamento:*\n\n"
        "Escolha um dos valores pré-definidos ou selecione 'Valor Personalizado' para inserir outro valor.",
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
        "💸 *Digite o valor desejado para o pagamento*\n\n"
        "Por favor, envie o valor em reais. Exemplos:\n"
        "- `15.90` para R$ 15,90\n"
        "- `42` para R$ 42,00\n\n"
        "📝 Envie apenas o número, sem símbolos ou letras.\n"
        "Você tem 60 segundos para responder ou pode cancelar clicando abaixo.",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("❌ Cancelar", callback_data="cancel_payment")]
        ])
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
                        "❌ *Valor inválido*\n\n"
                        "O valor deve ser maior que zero.",
                        reply_markup=InlineKeyboardMarkup([
                            [InlineKeyboardButton("🔄 Tentar Novamente", callback_data="payment:custom")],
                            [InlineKeyboardButton("◀️ Voltar", callback_data="show_payment_options")]
                        ])
                    )
                    return
                
                # Notifica que está processando o pagamento
                processing_msg = await response.reply(
                    "⏳ *Processando sua solicitação...*\n\n"
                    "Estamos gerando seu QR Code PIX, isso pode levar alguns segundos."
                )
                
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
                    keyboard = InlineKeyboardMarkup([
                        [InlineKeyboardButton("👁️ Ver QR Code", callback_data=f"show_qr:{transaction.id}")],
                        [InlineKeyboardButton("🔄 Verificar Pagamento", callback_data=f"check_payment:{transaction.id}")],
                        [InlineKeyboardButton("◀️ Voltar", callback_data="back_to_start")]
                    ])
                    
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
                        f"❌ *Ocorreu um erro ao gerar o pagamento*\n\n"
                        f"Detalhes: {str(e)}\n\n"
                        f"Por favor, tente novamente mais tarde.",
                        reply_markup=InlineKeyboardMarkup([
                            [InlineKeyboardButton("🔄 Tentar Novamente", callback_data="payment:custom")],
                            [InlineKeyboardButton("◀️ Voltar ao Início", callback_data="back_to_start")]
                        ])
                    )
                    
            except ValueError:
                # Valor não pôde ser convertido para float
                await response.reply(
                    "❌ *Valor inválido*\n\n"
                    "Por favor, envie apenas números. Exemplos:\n"
                    "- `15.90` para R$ 15,90\n"
                    "- `42` para R$ 42,00",
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton("🔄 Tentar Novamente", callback_data="payment:custom")],
                        [InlineKeyboardButton("◀️ Voltar", callback_data="show_payment_options")]
                    ])
                )
    except asyncio.TimeoutError:
        # Se o tempo expirar, notifica o usuário
        await client.send_message(
            chat_id,
            "⏰ *Tempo esgotado*\n\n"
            "Você não enviou um valor dentro do tempo limite. "
            "Por favor, inicie o processo novamente se ainda desejar fazer um pagamento.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔄 Tentar Novamente", callback_data="payment:custom")],
                [InlineKeyboardButton("◀️ Voltar", callback_data="show_payment_options")]
            ])
        )
    except Exception as e:
        logger.error(f"Erro ao processar valor personalizado: {str(e)}")
        await client.send_message(
            chat_id,
            f"❌ *Ocorreu um erro*\n\n"
            f"Não foi possível processar sua solicitação. Por favor, tente novamente.",
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
        "✅ *Solicitação cancelada*\n\n"
        "O pagamento foi cancelado. O que deseja fazer agora?",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("💰 Novo Pagamento", callback_data="show_payment_options")],
            [InlineKeyboardButton("◀️ Voltar ao Início", callback_data="back_to_start")]
        ])
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
                caption=f"🔍 *QR Code PIX*\n\nValor: R$ {transaction.amount:.2f}\n\n"
                        f"Escaneie com seu aplicativo bancário para efetuar o pagamento.",
            )
        else:
            await callback_query.answer("Transação não encontrada", show_alert=True)
    else:
        await callback_query.answer("Dados inválidos", show_alert=True)


@PixBot.on_message(filters.command("status") & filters.private)
async def status_command(client: Client, message: Message):
    """
    Exibe os pagamentos recentes do usuário
    """
    user_id = message.from_user.id
    
    # Busca as transações do usuário
    transactions = TransactionManager.get_user_transactions(user_id)
    
    if not transactions:
        await message.reply(
            "📋 *Histórico de Pagamentos*\n\n"
            "Você ainda não realizou nenhum pagamento.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("💰 Novo Pagamento", callback_data="show_payment_options")]
            ])
        )
        return
    
    # Ordena as transações por data (mais recentes primeiro)
    transactions.sort(key=lambda t: t.created_at, reverse=True)
    
    # Limita a exibir apenas as 5 transações mais recentes
    recent_transactions = transactions[:5]
    
    # Cria a mensagem com o histórico de transações
    message_text = "📋 *Suas Transações Recentes*\n\n"
    
    for i, transaction in enumerate(recent_transactions, 1):
        # Formata a data
        date_str = transaction.created_at.strftime("%d/%m/%Y %H:%M")
        
        # Adiciona a transação à mensagem
        message_text += (
            f"*{i}. Pagamento de R$ {transaction.amount:.2f}*\n"
            f"Status: {payment_status_message(transaction.status).split('*')[1]}\n"
            f"Data: {date_str}\n"
            f"ID: `{transaction.id}`\n\n"
        )
    
    # Cria os botões para verificação individual
    buttons = []
    for transaction in recent_transactions:
        buttons.append([
            InlineKeyboardButton(
                f"Verificar R$ {transaction.amount:.2f} ({transaction.status})",
                callback_data=f"check_payment:{transaction.id}"
            )
        ])
    
    buttons.append([InlineKeyboardButton("💰 Novo Pagamento", callback_data="show_payment_options")])
    buttons.append([InlineKeyboardButton("◀️ Voltar ao Início", callback_data="back_to_start")])
    
    keyboard = InlineKeyboardMarkup(buttons)
    
    await message.reply(
        message_text,
        reply_markup=keyboard
    )


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
                    buttons = []
                    
                    if updated_transaction.is_paid():
                        buttons = [
                            [InlineKeyboardButton("🏠 Voltar ao Início", callback_data="back_to_start")]
                        ]
                    elif updated_transaction.is_pending():
                        buttons = [
                            [InlineKeyboardButton("👁️ Ver QR Code", callback_data=f"show_qr:{transaction_id}")],
                            [InlineKeyboardButton("🔄 Verificar Novamente", callback_data=f"check_payment:{transaction_id}")],
                            [InlineKeyboardButton("◀️ Voltar", callback_data="back_to_start")]
                        ]
                    else:
                        buttons = [
                            [InlineKeyboardButton("💰 Novo Pagamento", callback_data="show_payment_options")],
                            [InlineKeyboardButton("◀️ Voltar", callback_data="back_to_start")]
                        ]
                    
                    keyboard = InlineKeyboardMarkup(buttons)
                    
                    # Atualiza a mensagem com o status atual
                    await callback_query.message.edit_text(
                        f"🧾 *Detalhes do pagamento:*\n\n"
                        f"💰 *Valor:* R$ {updated_transaction.amount:.2f}\n\n"
                        f"{status_msg}\n\n"
                        f"ID da transação: `{transaction_id}`",
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