"""
Integração com a API de pagamentos PIX
"""

import json
import re
from typing import Any, Dict, Optional

import requests

from pixbot.logger import logger
from pixbot.settings import Settings

settings = Settings()


class PIXApiError(Exception):
    """Exceção base para erros da API PIX"""

    pass


class PIXValueExceededError(PIXApiError):
    """Exceção para quando o valor excede o limite permitido"""

    def __init__(self, message="O valor excede o limite máximo permitido", limit=150.0):
        self.limit = limit
        super().__init__(message)


class PaymentAPI:
    """Classe para interagir com a API de pagamentos PIX"""

    @staticmethod
    def get_headers() -> Dict[str, str]:
        """Retorna os cabeçalhos para a requisição API"""
        return {
            "Authorization": f"Bearer {settings.pix_api_token}",
            "Content-Type": "application/json",
        }

    @classmethod
    async def generate_pix(cls, value: float, description: str = "") -> Dict[str, Any]:
        """
        Gera um QR Code PIX para pagamento

        Args:
            value: Valor em reais (será convertido para centavos)
            description: Descrição opcional do pagamento

        Returns:
            Dicionário com os dados do PIX gerado

        Raises:
            PIXValueExceededError: Quando o valor excede o limite máximo
            Exception: Para outros erros na API
        """
        value_in_cents = int(value * 100)

        payload = {"value": value_in_cents, "webhook_url": settings.webhook_url}

        if description:
            payload["description"] = description

        logger.info(f"Gerando PIX no valor de R$ {value:.2f}")

        try:
            response = requests.post(
                settings.pix_api_url, headers=cls.get_headers(), json=payload
            )
            response.raise_for_status()

            pix_data = response.json()
            logger.info(f"PIX gerado com sucesso. ID: {pix_data.get('id', 'N/A')}")

            return pix_data

        except requests.RequestException as e:
            logger.error(f"Erro ao gerar PIX: {str(e)}")
            error_msg = ""
            if "solicitar aumento" in e.response.text:
                response_text = e.response.text
                logger.error(f"Resposta da API: {response_text}")

                # Tenta extrair a mensagem de erro
                try:
                    error_data = json.loads(response_text)
                    error_msg = error_data.get("error", "")

                    # Verifica se é um erro de valor excedido, independente da formatação exata
                    if (
                        "valor máximo" in error_msg.lower()
                        or "limite" in error_msg.lower()
                    ) and any(limite in error_msg for limite in ["150", "R$"]):
                        # Tenta extrair o valor limite da mensagem
                        limit_match = re.search(r"R\$\s*(\d+)[,.](\d+)", error_msg)
                        limit = 150.0  # valor padrão
                        if limit_match:
                            try:
                                limit = float(
                                    f"{limit_match.group(1)}.{limit_match.group(2)}"
                                )
                            except (ValueError, IndexError):
                                pass

                        raise PIXValueExceededError(message=error_msg, limit=limit)
                except (json.JSONDecodeError, AttributeError):
                    # Se não conseguir extrair a mensagem de erro como JSON, verificamos o texto bruto
                    if (
                        "valor máximo" in response_text.lower()
                        and "150" in response_text
                    ):
                        raise PIXValueExceededError(
                            message="Valor excede o limite máximo permitido de R$ 150,00",
                            limit=150.0,
                        )

            # Se chegamos aqui, é porque não identificamos como erro de limite
            raise Exception(f"Falha ao gerar pagamento PIX: {str(e)}")

    @classmethod
    async def check_payment_status(cls, transaction_id: str) -> Dict[str, Any]:
        """
        Verifica o status de um pagamento PIX

        Args:
            transaction_id: ID da transação PIX

        Returns:
            Dicionário com os dados atualizados da transação
        """
        url = f"{settings.pix_status_url}{transaction_id}"

        logger.info(f"Verificando status do PIX ID: {transaction_id}")

        try:
            response = requests.get(url, headers=cls.get_headers())
            response.raise_for_status()

            status_data = response.json()
            logger.info(
                f"Status do PIX ID {transaction_id}: {status_data.get('status', 'N/A')}"
            )

            return status_data

        except requests.RequestException as e:
            logger.error(f"Erro ao verificar status do PIX: {str(e)}")
            if hasattr(e, "response") and e.response:
                logger.error(f"Resposta da API: {e.response.text}")

            raise Exception(f"Falha ao verificar status do pagamento: {str(e)}")
