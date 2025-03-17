# Bot de Pagamentos PIX para Telegram

Este projeto é um bot para Telegram que permite aos usuários gerar e gerenciar pagamentos via PIX diretamente através do chat. O bot é desenvolvido com Pyrogram/Kurigram e segue uma arquitetura modular baseada em princípios de Programação Orientada a Objetos (POO).

## Funcionalidades

* 💰 Geração de QR Codes e links de pagamento PIX
* 🔄 Verificação automática de status de pagamentos
* 📱 Interface interativa com botões (InlineKeyboard)
* 💼 Suporte a valores pré-definidos e personalizados
* 📊 Histórico de transações para os usuários

## Estrutura do Projeto

```
/
├── main.py                    # Ponto de entrada principal
├── bot.py                     # Configuração do bot e inicialização
├── settings.py                # Configurações usando Pydantic
├── requirements.txt           # Dependências do projeto
├── .env.example               # Modelo para configurações de ambiente
├── pixbot/                    # Pacote principal do bot
│   ├── __init__.py
│   ├── logger.py              # Configuração de logs com Loguru
│   ├── models/                # Modelos de dados
│   │   ├── __init__.py
│   │   └── transaction.py     # Modelo para transações
│   ├── plugins/               # Handlers para comandos e callbacks
│   │   ├── __init__.py
│   │   ├── start.py           # Comando /start
│   │   ├── payment.py         # Funções de pagamento
│   │   ├── callbacks.py       # Callbacks para botões
│   │   └── custom_filters.py  # Filtros personalizados
│   └── utils/                 # Funções utilitárias
│       ├── __init__.py
│       ├── payment_api.py     # Integração com API de pagamentos
│       └── helpers.py         # Funções auxiliares
```

## Requisitos

* Python 3.10 ou superior
* API ID e API Hash do Telegram (obtenha em [my.telegram.org](https://my.telegram.org))
* Token de bot do Telegram (obtenha através do [@BotFather](https://t.me/BotFather))
* Conta e token de API da [PushinPay](https://www.pushinpay.com.br/) para processar pagamentos PIX

## Instalação

1. Clone o repositório:
   ```bash
   git clone https://github.com/NatanKonig/pushinpay-bot.git
   cd pushinpay-bot
   ```
2. Instale as dependências:
   ```bash
   pip install -r requirements.txt
   ```
3. Configure as variáveis de ambiente:
   ```bash
   cp .env.example .env
   # Edite o arquivo .env com suas credenciais
   ```
4. Execute o bot:
   ```bash
   python main.py
   ```

## Comandos do Bot

* `/start` - Inicia o bot e exibe o menu principal
* `/payment` - Atalho para iniciar um novo pagamento
* `/status` - Verifica o status dos pagamentos recentes

## Integração com API de Pagamentos

O bot utiliza a [API PushinPay](https://www.pushinpay.com.br/) para gerar e gerenciar pagamentos PIX. É necessário ter uma conta e um token de API válido.

## Personalização

Você pode personalizar o bot editando os seguintes arquivos:

* `settings.py` - Altere configurações e valores padrão
* `pixbot/plugins/start.py` - Modifique as mensagens de boas-vindas
* `pixbot/utils/helpers.py` - Personalize a formatação das mensagens

## Características Técnicas

* Usa `uvloop` para melhor performance
* Configuração baseada em Pydantic para validação e flexibilidade
* Logs avançados com Loguru
* Sistema de transações em memória para rastreamento de pagamentos

## Contribuições

Contribuições são bem-vindas! Sinta-se à vontade para abrir issues ou enviar pull requests.

## Licença

Este projeto está licenciado sob a licença MIT - veja o arquivo [LICENSE]() para mais detalhes.
