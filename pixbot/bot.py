import asyncio
import traceback

import uvloop
from pyrogram import Client, idle, enums
from pyrogram.types import BotCommand
from convopyro import Conversation

from pixbot.logger import logger
from pixbot.settings import Settings

# Instala uvloop para melhorar a performance dos loops assíncronos
uvloop.install()


class PixBot(Client):
    """
    Classe principal do bot de pagamentos PIX
    Herda da classe Client do Pyrogram
    """
    
    def __init__(self):
        self.settings = Settings()
        super().__init__(
            name=self.settings.bot_name,
            api_id=self.settings.api_id,
            api_hash=self.settings.api_hash,
            bot_token=self.settings.bot_token,
            plugins=dict(root="pixbot/plugins/"),
            workdir="./sessions/",
            max_concurrent_transmissions=10,
        )
        self.me = None  # Será preenchido ao iniciar

    async def start(self):
        """Inicializa o bot e configura comandos"""
        # Configura o parser para usar o modo DEFAULT (combina Markdown e HTML)
        self.set_parse_mode(enums.ParseMode.DEFAULT)
        
        await super().start()
        self.me = await self.get_me()
        logger.info(f"Bot iniciado: @{self.me.username} ({self.me.id})")
        
        # Configura a lista de comandos que aparecerá no menu do bot
        commands = [
            BotCommand("start", "Iniciar o bot e ver menu principal"),
            BotCommand("payment", "Gerar novo pagamento PIX"),
            BotCommand("status", "Verificar status dos pagamentos recentes")
        ]
        
        await self.set_bot_commands(commands)
        logger.info("Comandos do bot configurados")


async def main():
    try:
        bot = PixBot()
        # Inicializa a biblioteca de conversas
        Conversation(bot)
        
        # Inicia o bot
        await bot.start()
        logger.info("Bot está em execução. Pressione CTRL+C para sair.")
        await idle()
    except Exception as e:
        logger.error(f"Erro ao iniciar o bot: {str(e)}")
        traceback.print_exc()
    finally:
        if 'bot' in locals() and hasattr(bot, 'is_connected') and bot.is_connected:
            await bot.stop()
            logger.info("Bot parou de executar")


if __name__ == "__main__":
    try:
        logger.success("Iniciando o Bot de Pagamentos PIX...")
        asyncio.run(main())
    except Exception as e:
        logger.error(f"Erro ao iniciar o bot: {e}")
        traceback.print_exc()
        exit(1)
    except KeyboardInterrupt:
        logger.warning("Bot finalizado pelo usuário!")
        exit(0)