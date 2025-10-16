# evo-ai-agents-wiki-integration-webinar

Корпоративная вики с AI - интеграция агентов для поиска и ответов на вопросы с использованием Model Context Protocol (MCP) и LLM.

## Обзор

Этот проект представляет собой комплексное решение для создания корпоративного ассистента, который отвечает на вопросы, используя внутреннюю вики через MCP-сервер и LLM. Система состоит из двух основных компонентов:

1. **MCP-сервер** - сервер Model Context Protocol для интеграции с Outline Wiki
2. **AI-агент** - корпоративный ассистент, работающий на поисковом сервере MCP и LLM

## Архитектура

```
Вопрос → Извлечение ключевых слов → Поиск MCP → Сбор контекста → Ответ LLM
```

### Компоненты системы

- **MCP-сервер**: Предоставляет поисковые возможности через MCP-совместимые эндпоинты
- **AI-агент**: Обрабатывает вопросы пользователей и генерирует ответы на основе данных из вики
- **Outline Wiki**: Внешняя система вики для хранения корпоративных знаний

## Возможности

### MCP-сервер

- **MCP-совместимый поисковый инструмент**: Интеграция с Outline Wiki для поиска контента
- **Двойная поддержка транспортов**:
  - Современный Streamable HTTP транспорт (рекомендуется)
  - Устаревший SSE транспорт для обратной совместимости
- **Управление сессиями**: Поддержка множественных MCP-сессий
- **Docker-готовность**: Простое развертывание в контейнерах

### AI-агент

- Поиск по вики через MCP (инструмент: `search`)
- Улучшенная выдача за счёт ключевых слов
- Надёжная обработка ошибок и повторные попытки
- Отслеживание истории диалога

## Структура проекта

```
├── agent/                    # AI-агент (Python)
│   ├── assistant/           # Основной код ассистента
│   ├── Dockerfile           # Docker конфигурация для агента
│   ├── requirements.txt     # Python зависимости
│   └── README.md           # Документация агента
├── mcp-server/             # MCP-сервер (TypeScript/Node.js)
│   ├── src/                # Исходный код сервера
│   ├── dockerfile          # Docker конфигурация для сервера
│   ├── package.json        # Node.js зависимости
│   └── README.md           # Документация сервера
└── README.md               # Общая документация проекта
```

## Быстрый старт

### Предварительные требования

- **Python 3.8+** - для AI-агента
- **Node.js 20+** - для MCP-сервера
- **Outline Wiki** - настроенный экземпляр с API доступом
- **Docker** - для контейнеризации (опционально)

### Установка и запуск

#### 1. MCP-сервер

```bash
cd mcp-server

# Установка зависимостей
yarn install

# Создание файла конфигурации
cp .env.example .env
# Отредактируйте .env файл с вашими настройками Outline

# Запуск в режиме разработки
yarn dev

# Или сборка и запуск production версии
yarn build
yarn start
```

#### 2. AI-агент

```bash
cd agent

# Создание виртуального окружения
python -m venv .venv

# Активация виртуального окружения
# Linux/macOS:
source .venv/bin/activate
# Windows:
.venv\Scripts\activate

# Установка зависимостей
pip install -r requirements.txt

# Создание файла конфигурации
cp env.example .env
# Отредактируйте .env файл с вашими настройками

# Запуск агента
python -m assistant.start_a2a
```

### Docker развертывание

#### MCP-сервер

```bash
cd mcp-server

# Сборка образа
yarn docker:build

# Запуск контейнера
yarn docker:run
```

#### AI-агент

```bash
cd agent

# Сборка образа
docker build -t evo-ai-agents-outline-agent .

# Запуск контейнера
docker run --rm --name wiki-assistant \
  --env-file .env \
  -p 10000:10000 \
  evo-ai-agents-outline-agent
```

## Конфигурация

### MCP-сервер (.env)

```env
# Порт сервера (по умолчанию: 8080)
PORT=8080

# URL вашего Outline API (обязательно)
OUTLINE_BASE_URL=https://your-outline-instance.com

# Bearer токен для аутентификации в Outline API (обязательно)
OUTLINE_TOKEN=your-outline-api-token
```

### AI-агент (.env)

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

## API и инструменты

### MCP инструменты

Сервер предоставляет следующий MCP инструмент:

#### `search` - Поиск в Outline Wiki

**Описание**: Выполняет полнотекстовый поиск в Outline Wiki по заданному запросу.

**Входные параметры**:

```json
{
  "query": "строка поиска", // Обязательно: поисковый запрос
  "limit": 20, // Опционально: максимум результатов (1-100, по умолчанию: 20)
  "offset": 0 // Опционально: смещение для пагинации (по умолчанию: 0)
}
```

### Эндпоинты

#### Streamable HTTP (рекомендуется)

- `POST /` - Основной MCP эндпоинт для современных клиентов
- `GET /` - Получение информации о сессии
- `DELETE /` - Закрытие сессии

#### SSE (обратная совместимость)

- `GET /sse` - Установка SSE соединения для устаревших клиентов
- `POST /messages` - Отправка сообщений через SSE транспорт

## Использование

### Программное использование AI-агента

```python
from assistant.wiki_assistant import WikiAssistant

assistant = WikiAssistant(mcp_server_url="http://localhost:3001")
answer = assistant.answer("Какова наша политика удалённой работы?")
print(answer)

# При необходимости корректно закрыть асинхронные ресурсы
import asyncio
asyncio.run(assistant.close())
```

## Технологический стек

### MCP-сервер

- **Node.js 20+** - Runtime окружение
- **TypeScript** - Язык программирования
- **Express.js** - Web фреймворк
- **@modelcontextprotocol/sdk** - MCP SDK
- **Axios** - HTTP клиент для Outline API
- **Zod** - Валидация схем

### AI-агент

- **Python 3.8+** - Runtime окружение
- **LiteLLM** - LLM интеграция
- **a2a-sdk** - Фреймворк для агентов
- **Starlette** - ASGI фреймворк
- **asyncio** - Асинхронное программирование

## Разработка

### Доступные команды

#### MCP-сервер

```bash
yarn dev          # Запуск в режиме разработки
yarn build        # Сборка проекта
yarn start        # Запуск production версии
yarn lint         # Проверка кода линтером
yarn lint:fix     # Автоматическое исправление ошибок линтера
yarn format       # Форматирование кода
yarn inspect      # Инспектор MCP для отладки
```

#### AI-агент

```bash
# Запуск в режиме разработки
python -m assistant.start_a2a

# Запуск с отладкой
DEBUG=true python -m assistant.start_a2a
```

## Устранение неполадок

- Убедитесь, что задан `MCP_URL`, первый URL доступен и предоставляет инструмент `search`
- Проверьте учётные данные и конфигурацию модели LLM
- Установите `DEBUG=true` для подробных логов
- Убедитесь, что Outline Wiki доступен и API токен действителен

## Лицензия

MIT License

## Развертывание

### Container Registry

Для публикации в Container Registry:

1. **MCP-сервер**:

   ```bash
   cd mcp-server
   yarn deploy
   ```

2. **AI-агент**:
   ```bash
   cd agent
   docker build -t evo-ai-agents-outline-agent .
   docker tag evo-ai-agents-outline-agent as-konstantinov.cr.cloud.ru/evo-ai-agents-outline-agent:latest
   docker push as-konstantinov.cr.cloud.ru/evo-ai-agents-outline-agent:latest
   ```

## Поддержка

Для получения помощи и поддержки обращайтесь к документации соответствующих компонентов:

- [MCP-сервер](mcp-server/README.md)
- [AI-агент](agent/README.md)
