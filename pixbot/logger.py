import logging
import sys
from logging.handlers import RotatingFileHandler

from loguru import logger as loguru_logger


class InterceptHandler(logging.Handler):
    def emit(self, record):
        # Get corresponding Loguru level if it exists
        try:
            level = loguru_logger.level(record.levelname).name
        except ValueError:
            level = record.levelno

        # Find caller from where originated the logged message
        frame, depth = logging.currentframe(), 2
        while frame.f_code.co_filename == logging.__file__:
            frame = frame.f_back
            depth += 1

        # Filtra logs indesejados do Pyrogram
        if 'pyrogram' in record.name.lower() and record.levelname == 'INFO':
            # Apenas permite logs específicos do Pyrogram
            allowed_messages = [
                "Bot iniciado:",
                "Bot está em execução",
                "Bot parou",
                "Comandos do bot configurados"
            ]
            
            # Verifica se a mensagem contém algum texto permitido
            should_log = any(allowed in record.getMessage() for allowed in allowed_messages)
            if not should_log:
                return  # Ignora mensagens que não são necessárias
        
        loguru_logger.opt(depth=depth, exception=record.exc_info).log(
            level, record.getMessage()
        )


# Remove manipuladores padrão do loguru
loguru_logger.remove()

# Adiciona saída para o console
loguru_logger.add(
    sys.stdout,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan> - <level>{message}</level>",
    level="INFO",
    colorize=True,
    filter=lambda record: "pyrogram.session" not in record["name"]  # Filtra logs de sessão
)

# Adiciona saída para arquivo com rotação
loguru_logger.add(
    "logs/pixbot.log",
    format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
    level="DEBUG",
    rotation="10 MB",
    compression="zip",
    retention="1 week",
)

# Configura pyrogram para usar níveis de log mais adequados
logging.getLogger("pyrogram").setLevel(logging.WARNING)
logging.getLogger("pyrogram.session").setLevel(logging.CRITICAL)
logging.getLogger("pyrogram.connection").setLevel(logging.CRITICAL)

# Configura o handler do sistema de logging do Python para usar loguru
logging.basicConfig(handlers=[InterceptHandler()], level=0, force=True)

# Referência para o logger
logger = loguru_logger