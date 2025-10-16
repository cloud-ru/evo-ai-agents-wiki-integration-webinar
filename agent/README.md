# evo-ai-agents-wiki-assistant

Корпоративный ассистент для вики, работающий на поисковом сервере MCP (Model Context Protocol) и LLM.

## Обзор

Ассистент отвечает на вопросы, используя вашу внутреннюю вики:

1. Извлечение ключевых слов с помощью LLM для формирования эффективных поисковых запросов
2. Вызов инструмента на MCP-сервере для поиска по вики
3. Ответ LLM, основанный на результатах MCP

## Архитектура

```
Вопрос → Извлечение ключевых слов → Поиск MCP → Сбор контекста → Ответ LLM
```

## Возможности

- Поиск по вики через MCP (инструмент: `search`)
- Улучшенная выдача за счёт ключевых слов
- Надёжная обработка ошибок и повторные попытки
- Отслеживание истории диалога

## Установка

### Предварительные требования

- Python 3.8+
- Запущенный MCP-сервер, предоставляющий инструмент `search`
- Совместимая с OpenAI конечная точка LLM (или OpenAI API)

### Установка зависимостей

```bash
# Установка Python-зависимостей
pip install -r requirements.txt
```

### Переменные окружения

Создайте файл `.env` со следующим содержимым:

```env
# MCP-сервера (SSE-URL через запятую)
MCP_URL=http://localhost:3001

# LLM / Foundation Model через API, совместимый с LiteLLM
LLM_MODEL=hosted_vllm/Qwen/Qwen3-Coder-480B-A35B-Instruct
LLM_API_BASE=https://foundation-models.api.cloud.ru/v1
LLM_API_KEY=your-api-key

# Сервер a2a-sdk / Starlette
PORT=10000
LOG_LEVEL=INFO

# Метаданные агента
AGENT_NAME=Wiki Assistant
AGENT_DESCRIPTION=Отвечает на вопросы, используя корпоративную вики через MCP и LLM
AGENT_VERSION=v1.0.0
```

## Использование

### Запуск локально (без Docker)

```bash
# 1) Скопируйте шаблон окружения и заполните значения
cp env.example .env

# Обязательно укажите рабочий MCP-сервер и LLM-провайдера в .env
# MCP_URL=http://localhost:3001
# LLM_MODEL=...
# LLM_API_BASE=...
# LLM_API_KEY=...

# 2) Создайте и активируйте виртуальное окружение (venv)
python -m venv .venv

# Linux / macOS / Git Bash (Windows)
source .venv/bin/activate 2>/dev/null || source .venv/Scripts/activate

# Windows PowerShell (альтернатива)
# .\.venv\Scripts\Activate.ps1

# Windows CMD (альтернатива)
# .\.venv\Scripts\activate.bat

# 3) Установите зависимости
pip install -r requirements.txt

# 4) Запустите сервер A2A
python -m assistant.start_a2a

# По умолчанию сервер слушает порт 10000.
# Изменить можно переменной окружения PORT, например:
# PORT=11000 python -m assistant.start_a2a
```

После запуска сервер будет доступен на `http://localhost:10000` (или на порту из `PORT`).

### Программно

```python
from assistant.wiki_assistant import WikiAssistant

assistant = WikiAssistant(mcp_server_url="http://localhost:3001")
answer = assistant.answer("Какова наша политика удалённой работы?")
print(answer)

# При необходимости корректно закрыть асинхронные ресурсы
import asyncio
asyncio.run(assistant.close())
```

### Сервер A2A (a2a-sdk / Starlette)

Запуск нового сервера на базе a2a-sdk (Starlette):

```bash
python -m assistant.start_a2a
```

По умолчанию сервер слушает на `0.0.0.0:PORT` (по умолчанию `PORT=10000`).

## Справочник API

### WikiAssistant

Конструктор:

```python
WikiAssistant(mcp_server_url: str)
```

Методы:

- `answer(question: str) -> str`
- `chat_history -> list`
- `close() -> Awaitable[None]`

## Интеграция с MCP

- Вызываемый инструмент: `search`
- Протокол: JSON-RPC поверх HTTP (см. `assistant/mcp_client.py`)
- Результаты приводятся к лёгким объектам `RetrievedDocument` (см. `assistant/retrievers.py`)

## Структура проекта

```
assistant/
├── __init__.py
├── agent.py             # google-adk: LiteLlm + McpToolset (не используется рантаймом)
├── a2a_agent.py         # Обёртка агента для a2a-sdk, вызывает WikiAssistant
├── agent_task_manager.py# Исполнитель для a2a-sdk, мапит события задач
├── start_a2a.py         # Точка входа Starlette + a2a-sdk
├── mcp_client.py        # Клиент MCP-сервера
├── prompts.py           # Строковые шаблоны промптов (без LangChain)
├── retrievers.py        # Ретривер без LangChain, использует LiteLLM для ключевых слов
└── wiki_assistant.py    # Основная реализация ассистента (LiteLLM + MCP)
```

## Устранение неполадок

- Убедитесь, что задан `MCP_URL`, первый URL доступен и предоставляет инструмент `search`
- Проверьте учётные данные и конфигурацию модели LLM
- Установите `DEBUG=true` для подробных логов

## Лицензия

MIT License

## Развёртывание

Ниже приведены команды для сборки, тегирования, публикации и запуска Docker-образа без использования npm. Имя пакета/образа обновлено на `evo-ai-agents-outline-agent`.

### Сборка и публикация образа

```bash
# Сборка локального образа
docker build -t evo-ai-agents-outline-agent .

# Тегирование для реестра
docker tag evo-ai-agents-outline-agent <package-name>.cr.cloud.ru/evo-ai-agents-outline-agent:latest

# Публикация в реестр
docker push <package-name>.cr.cloud.ru/evo-ai-agents-outline-agent:latest
```

### Запуск локально

```bash
# Используя локально собранный образ
docker run --rm --name wiki-assistant \
  --env-file .env \
  -p 10000:10000 \
  evo-ai-agents-outline-agent
```
