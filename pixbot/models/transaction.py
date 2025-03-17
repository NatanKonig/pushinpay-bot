"""
Modelo para representar transações de pagamento
"""
from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Dict, Any, List

from pixbot.logger import logger


@dataclass
class Transaction:
    """Classe para armazenar informações de uma transação de pagamento"""
    
    id: str
    user_id: int  # ID do usuário no Telegram
    amount: float  # Valor em reais
    qr_code: str  # Código PIX copia e cola
    created_at: datetime
    status: str = "pending"  # pending, paid, expired, canceled, failed
    description: Optional[str] = None
    message_id: Optional[int] = None  # ID da mensagem no Telegram
    
    @classmethod
    def from_api_response(cls, api_data: Dict[str, Any], user_id: int, message_id: Optional[int] = None) -> 'Transaction':
        """
        Cria uma instância de Transaction a partir da resposta da API
        
        Args:
            api_data: Resposta da API de pagamentos
            user_id: ID do usuário no Telegram
            message_id: ID da mensagem no Telegram (opcional)
            
        Returns:
            Nova instância de Transaction
        """
        return cls(
            id=api_data.get('id'),
            user_id=user_id,
            amount=api_data.get('value', 0) / 100,  # Converte de centavos para reais
            qr_code=api_data.get('qr_code', ''),
            created_at=datetime.now(),
            status=api_data.get('status', 'pending'),
            description=api_data.get('description'),
            message_id=message_id
        )
    
    def update_from_api(self, api_data: Dict[str, Any]) -> None:
        """
        Atualiza os dados da transação a partir da resposta da API
        
        Args:
            api_data: Resposta da API de pagamentos
        """
        self.status = api_data.get('status', self.status)
        
    def is_paid(self) -> bool:
        """Verifica se o pagamento foi confirmado"""
        return self.status == "paid"
    
    def is_pending(self) -> bool:
        """Verifica se o pagamento está pendente"""
        return self.status == "pending"
    
    def is_expired(self) -> bool:
        """Verifica se o pagamento expirou"""
        return self.status == "expired"


# Gerenciador global de transações em memória
class TransactionManager:
    """Gerencia as transações do bot em memória"""
    
    _transactions = {}  # Dict[transaction_id, Transaction]
    
    @classmethod
    def add_transaction(cls, transaction: Transaction) -> None:
        """
        Adiciona uma nova transação
        
        Args:
            transaction: Instância de Transaction
        """
        cls._transactions[transaction.id] = transaction
        logger.debug(f"Nova transação adicionada: {transaction.id} para usuário {transaction.user_id}")
    
    @classmethod
    def get_transaction(cls, transaction_id: str) -> Optional[Transaction]:
        """
        Obtém uma transação pelo ID
        
        Args:
            transaction_id: ID da transação
            
        Returns:
            Instância de Transaction ou None se não encontrada
        """
        transaction = cls._transactions.get(transaction_id)
        if not transaction:
            logger.warning(f"Transação não encontrada: {transaction_id}")
        return transaction
    
    @classmethod
    def update_transaction(cls, transaction_id: str, api_data: Dict[str, Any]) -> Optional[Transaction]:
        """
        Atualiza uma transação com dados da API
        
        Args:
            transaction_id: ID da transação
            api_data: Resposta da API de pagamentos
            
        Returns:
            Instância atualizada de Transaction ou None se não encontrada
        """
        transaction = cls.get_transaction(transaction_id)
        if transaction:
            old_status = transaction.status
            transaction.update_from_api(api_data)
            logger.info(f"Transação {transaction_id} atualizada: status {old_status} -> {transaction.status}")
            return transaction
        return None