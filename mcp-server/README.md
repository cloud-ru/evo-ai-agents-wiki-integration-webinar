# evo-ai-agents-outline-mcp-server

Сервер Model Context Protocol (MCP) для интеграции с Outline Wiki. Предоставляет поисковые возможности через MCP-совместимые эндпоинты, поддерживает как современные Streamable HTTP, так и устаревшие SSE транспорты для обеспечения обратной совместимости.

## Возможности

- **MCP-совместимый поисковый инструмент**: Интеграция с Outline Wiki для поиска контента
- **Двойная поддержка транспортов**:
  - Современный Streamable HTTP транспорт (рекомендуется)
  - Устаревший SSE транспорт для обратной совместимости
- **Управление сессиями**: Поддержка множественных MCP-сессий
- **Docker-готовность**: Простое развертывание в контейнерах
- **TypeScript**: Полная типизация для надежности разработки
- **CORS поддержка**: Настроенная для веб-приложений

## Архитектура

Сервер построен на Express.js с поддержкой двух типов транспортов MCP:

### Транспорты

- **Streamable HTTP** (`/mcp`): Современный транспорт для новых клиентов

### Структура проекта

```
.
├── src/
│   ├── config.ts              # Конфигурация и переменные окружения
│   ├── endpoints.ts           # Регистрация Express эндпоинтов для MCP
│   ├── mcp.server.ts          # Определение MCP сервера и поискового инструмента
│   ├── mcp.ts                 # Главная точка входа, настройка Express приложения
│   ├── transport.manager.ts   # Управление MCP сессиями и транспортами
│   └── outline-search.service.ts # Сервис для работы с Outline API
├── dist/                      # Скомпилированные JavaScript файлы
├── dockerfile                 # Многоэтапная Docker сборка
├── package.json               # Метаданные проекта и скрипты
├── tsconfig.json              # Конфигурация TypeScript
└── README.md                  # Документация проекта
```

## Быстрый старт

### Предварительные требования

- **Node.js 20+**: Для запуска сервера
- **Outline Wiki**: Настроенный экземпляр с API доступом
- **Yarn**: Менеджер пакетов (рекомендуется)

### Установка

1. Клонируйте репозиторий:

```bash
git clone <repository-url>
cd evo-ai-agents-outline-mcp-server
```

2. Установите зависимости:

```bash
yarn install
```

### Конфигурация

Создайте файл `.env` в корне проекта:

```bash
# Порт сервера (по умолчанию: 8080)
PORT=8080

# URL вашего Outline API (обязательно)
OUTLINE_BASE_URL=https://your-outline-instance.com

# Bearer токен для аутентификации в Outline API (обязательно)
OUTLINE_TOKEN=your-outline-api-token
```

> **Важно**: Получите API токен в настройках Outline Wiki в разделе "API Tokens"

## Запуск

### Режим разработки

```bash
yarn dev
```

Команда автоматически собирает проект и запускает сервер с hot-reload.

### Сборка

```bash
yarn build
```

Компилирует TypeScript код в JavaScript в папку `dist/`.

### Production запуск

```bash
yarn start
```

Запускает собранную версию сервера.

### Docker

#### Сборка и запуск в Docker

```bash
# Сборка образа
yarn docker:build

# Запуск контейнера
yarn docker:run
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

**Выходные данные**:

- Форматированный список результатов с заголовками
- URL документов
- ID коллекций
- Рейтинги релевантности
- Полное содержимое документов в JSON формате

### Эндпоинты

#### Streamable HTTP (рекомендуется)

- `POST /mcp` - Основной MCP эндпоинт для современных клиентов


## Развертывание

### Container Registry

Для публикации в Container Registry:

1. **Сборка образа**:

   ```bash
   yarn docker:build
   ```

2. **Тегирование** (замените `<REGISTRY-NAME>` на имя вашего реестра):

   ```bash
   yarn docker:tag
   ```

3. **Публикация**:

   ```bash
   yarn docker:push
   ```

4. **Автоматизация всех шагов**:
   ```bash
   yarn deploy
   ```

> **Важно**: Замените `<REGISTRY-NAME>` на фактическое имя вашего Container Registry (например: `crp12345`).

### Инструкции по Container Registry

Подробная документация: [cloud.ru/docs/labs/services/topics/container-apps\_\_before-work](https://cloud.ru/docs/labs/services/topics/container-apps__before-work?source-platform=Evolution)

## Разработка

### Доступные команды

```bash
yarn dev          # Запуск в режиме разработки
yarn build        # Сборка проекта
yarn start        # Запуск production версии
yarn lint         # Проверка кода линтером
yarn lint:fix     # Автоматическое исправление ошибок линтера
yarn format       # Форматирование кода
yarn inspect      # Инспектор MCP для отладки
```

### Технологический стек

- **Node.js 20+** - Runtime окружение
- **TypeScript** - Язык программирования
- **Express.js** - Web фреймворк
- **@modelcontextprotocol/sdk** - MCP SDK
- **Axios** - HTTP клиент для Outline API
- **Zod** - Валидация схем
- **Docker** - Контейнеризация

## Лицензия

MIT License
