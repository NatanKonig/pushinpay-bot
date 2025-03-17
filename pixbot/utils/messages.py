"""
Mensagens padronizadas e templates para uso no bot
"""
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton

# Mensagens principais (padronizadas para usar * para destaque)
WELCOME_MESSAGE = """
👋 **Bem-vindo ao Bot de Pagamentos PIX!**

Com este bot, você pode:
• Gerar QR Codes para receber pagamentos
• Verificar o status dos seus pagamentos
• Receber notificações automáticas

Use os botões abaixo para começar.
"""

HELP_MESSAGE = """
❓ **Ajuda e Instruções**

Este bot permite gerar pagamentos PIX de forma simples e rápida.

**Como usar:**
1. Clique em 'Gerar Pagamento'
2. Selecione um valor ou insira um valor personalizado
3. Compartilhe o QR Code gerado ou use a chave Copia e Cola
4. O bot notificará quando o pagamento for confirmado

**Comandos disponíveis:**
/start - Inicia o bot
/payment - Atalho para gerar um novo pagamento
"""

ABOUT_MESSAGE = """
ℹ️ **Sobre o Bot de Pagamentos PIX**

Este bot foi desenvolvido com Pyrogram e integra-se à API de pagamentos PushinPay 
para fornecer uma solução completa de pagamentos via PIX diretamente no Telegram.

Desenvolvido com ❤️ usando Python e Pyrogram.

Versão: 1.0.0
"""

PAYMENT_OPTIONS_MESSAGE = """
💰 **Selecione o valor do pagamento:**

Escolha um dos valores pré-definidos ou selecione 'Valor Personalizado' para inserir outro valor.
"""

CUSTOM_AMOUNT_MESSAGE = """
💸 **Digite o valor desejado para o pagamento**

Por favor, envie o valor em reais. Exemplos:
- `15.90` para R$ 15,90
- `42` para R$ 42,00

📝 Envie apenas o número, sem símbolos ou letras.
Você tem 60 segundos para responder ou pode cancelar clicando abaixo.
"""

PROCESSING_MESSAGE = """
⏳ **Processando sua solicitação...**

Estamos gerando seu QR Code PIX, isso pode levar alguns segundos.
"""

TIMEOUT_MESSAGE = """
⏰ **Tempo esgotado**

Você não enviou um valor dentro do tempo limite. 
Por favor, inicie o processo novamente se ainda desejar fazer um pagamento.
"""

INVALID_VALUE_MESSAGE = """
❌ **Valor inválido**

O valor deve ser maior que zero.
"""

INVALID_FORMAT_MESSAGE = """
❌ **Valor inválido**

Por favor, envie apenas números. Exemplos:
- `15.90` para R$ 15,90
- `42` para R$ 42,00
"""

ERROR_MESSAGE = """
❌ **Ocorreu um erro**

{details}

Por favor, tente novamente mais tarde.
"""

PAYMENT_CANCELED_MESSAGE = """
✅ **Solicitação cancelada**

O pagamento foi cancelado. O que deseja fazer agora?
"""

QR_CODE_CAPTION = """
🔍 **QR Code PIX**

Valor: R$ {amount:.2f}

Escaneie com seu aplicativo bancário para efetuar o pagamento.
"""

PAYMENT_DETAILS_MESSAGE = """
🧾 **Detalhes do pagamento:**

💰 *Valor:* R$ {amount:.2f}

{status_msg}

ID da transação: `{transaction_id}`
"""

# Status de pagamento
def payment_status_message(status: str) -> str:
    """
    Retorna a mensagem correspondente ao status do pagamento
    """
    status_messages = {
        "pending": "⏳ **Aguardando pagamento**\nO pagamento ainda não foi confirmado.",
        "paid": "✅ **Pagamento confirmado!**\nObrigado por utilizar nosso serviço.",
        "expired": "⌛ **Pagamento expirado**\nO tempo para pagamento expirou.",
        "canceled": "❌ **Pagamento cancelado**\nEsta transação foi cancelada.",
        "failed": "⚠️ **Falha no pagamento**\nOcorreu um erro durante o processamento."
    }
    
    return status_messages.get(status, f"Status desconhecido: {status}")

def format_payment_message(value: float, qr_code: str, transaction_id: str) -> str:
    """
    Formata a mensagem de pagamento PIX
    """
    if qr_code:
        return (
            f"🧾 **Detalhes do pagamento:**\n\n"
            f"💰 **Valor:** R$ {value:.2f}\n\n"
            f"📲 **Chave Copia e Cola:**\n"
            f"`{qr_code}`\n\n"
            f"👉 Você também pode visualizar o QR Code e escanear com seu aplicativo bancário.\n\n"
            f"ID da transação: `{transaction_id}`"
        )
    else:
        return (
            f"🧾 **Detalhes do pagamento:**\n\n"
            f"💰 **Valor:** R$ {value:.2f}\n\n"
        )

# Teclados comuns
def main_menu_keyboard() -> InlineKeyboardMarkup:
    """Retorna o teclado do menu principal"""
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("💰 Gerar Pagamento", callback_data="show_payment_options")
        ],
        [
            InlineKeyboardButton("❓ Ajuda", callback_data="help"),
            InlineKeyboardButton("ℹ️ Sobre", callback_data="about")
        ]
    ])

def payment_details_keyboard(transaction_id: str) -> InlineKeyboardMarkup:
    """Retorna o teclado para detalhes do pagamento"""
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("👁️ Ver QR Code", callback_data=f"show_qr:{transaction_id}")],
        [InlineKeyboardButton("🔄 Verificar Pagamento", callback_data=f"check_payment:{transaction_id}")],
        [InlineKeyboardButton("◀️ Voltar", callback_data="back_to_start")]
    ])

def error_keyboard() -> InlineKeyboardMarkup:
    """Retorna o teclado para mensagens de erro"""
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🔄 Tentar Novamente", callback_data="show_payment_options")],
        [InlineKeyboardButton("◀️ Voltar ao Início", callback_data="back_to_start")]
    ])

def custom_amount_keyboard() -> InlineKeyboardMarkup:
    """Retorna o teclado para entrada de valor personalizado"""
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("❌ Cancelar", callback_data="cancel_payment")]
    ])

def retry_custom_amount_keyboard() -> InlineKeyboardMarkup:
    """Retorna o teclado para tentar novamente o valor personalizado"""
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🔄 Tentar Novamente", callback_data="payment:custom")],
        [InlineKeyboardButton("◀️ Voltar", callback_data="show_payment_options")]
    ])

def payment_canceled_keyboard() -> InlineKeyboardMarkup:
    """Retorna o teclado para quando o pagamento é cancelado"""
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("💰 Novo Pagamento", callback_data="show_payment_options")],
        [InlineKeyboardButton("◀️ Voltar ao Início", callback_data="back_to_start")]
    ])

def get_pending_payment_keyboard(transaction_id: str) -> InlineKeyboardMarkup:
    """Retorna o teclado para pagamentos pendentes"""
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("👁️ Ver QR Code", callback_data=f"show_qr:{transaction_id}")],
        [InlineKeyboardButton("🔄 Verificar Novamente", callback_data=f"check_payment:{transaction_id}")],
        [InlineKeyboardButton("◀️ Voltar", callback_data="back_to_start")]
    ])

def get_completed_payment_keyboard() -> InlineKeyboardMarkup:
    """Retorna o teclado para pagamentos concluídos"""
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🏠 Voltar ao Início", callback_data="back_to_start")]
    ])

def get_failed_payment_keyboard() -> InlineKeyboardMarkup:
    """Retorna o teclado para pagamentos que falharam"""
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("💰 Novo Pagamento", callback_data="show_payment_options")],
        [InlineKeyboardButton("◀️ Voltar", callback_data="back_to_start")]
    ])

def back_button_keyboard() -> InlineKeyboardMarkup:
    """Retorna um teclado com apenas o botão de voltar"""
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("◀️ Voltar", callback_data="back_to_start")]
    ])