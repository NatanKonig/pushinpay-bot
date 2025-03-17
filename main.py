"""
Ponto de entrada principal do bot
"""

import asyncio
import os
import traceback

from pixbot.bot import main
from pixbot.logger import logger

if __name__ == "__main__":
    try:
        logger.success("Bot de Pagamentos PIX iniciando...")
        asyncio.run(main())
    except Exception as e:
        logger.error(f"Erro ao iniciar o bot: {e}")
        traceback.print_exc()
        exit(1)
    except KeyboardInterrupt:
        logger.warning("Bot finalizado pelo usuário!")
        exit(0)
