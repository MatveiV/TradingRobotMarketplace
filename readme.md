# Trading Robot Marketplace

**Copy Trading Platform** — создание, публикация и подключение торговых роботов для MetaTrader 4 и MetaTrader 5.

Два типа пользователей:
- **Money Manager (Управляющий)** — создаёт стратегию, загружает робота (`.ex4`/`.ex5` + `.set`), настраивает комиссии (Performance/Subscription/Entry fee + Agent Reward), управляет подключениями инвесторов
- **Инвестор** — просматривает стратегии с фильтрацией, изучает торговую историю и показатели, подключается для копирования сделок

## Быстрый старт

```bash
# Backend
cd backend
pip install -r requirements.txt
python -m uvicorn app.main:app --reload --port 8000
# API docs: http://localhost:8000/docs

# Frontend
cd frontend/artifacts/trading-marketplace
pnpm install
pnpm dev
# UI: http://localhost:5173

# Генерация демо-стратегий
curl -X POST http://localhost:8000/api/strategies/seed
```

## Возможности

| Возможность | Описание |
|------------|----------|
| **Создание стратегии** | Название, описание, логотип, Withdrawal Policy, Availability, Trades History From, Password Protection |
| **Комиссии** | Performance Fee % + Agent Reward %, Subscription Fee (Daily/Weekly/Monthly/Annual) + Agent Reward %, Entry Fee % + Agent Reward % |
| **Загрузка робота** | Файлы `.ex4`/`.ex5` (робот) + `.set` (настройки) для MT4/MT5 через upload или URL |
| **Подключение к счёту** | Логин, пароль, сервер; выбор MT версии, настроек графика, таймфрейма |
| **Deploy-процесс** | Upload → Apply settings → Launch terminal → Full deploy pipeline |
| **Торговая история** | Пагинированная таблица сделок, AreaChart Profit/Loss, Drawdown, Win Rate |
| **MetaTrader управление** | Disconnect инвестора, удаление стратегии |
| **Стратегия инвестора** | Просмотр деталей, подключение через DeployDialog, MM controls (disconnect/delete) |

## Архитектура

```
┌──────────────────┐     ┌──────────────────┐     ┌──────────────────┐
│  Frontend        │────▶│  Backend API     │────▶│  MT4 / MT5       │
│  React + TS      │     │  FastAPI         │     │  Adapter (mock)  │
│  Vite + shadcn/ui│     │                  │     └──────────────────┘
└──────────────────┘     └──────┬───────────┘
                                │
                         ┌──────┴───────────┐
                         │  SQLite /        │
                         │  SQLAlchemy ORM  │
                         └──────────────────┘
```

## Технологии

| Компонент | Технология |
|-----------|-----------|
| Frontend | React 19, TypeScript, Vite 7, Tailwind CSS 4, shadcn/ui |
| Routing | wouter |
| Data fetching | TanStack Query (React Query 5) |
| Forms | react-hook-form + zod |
| Charts | recharts (AreaChart) |
| UI Icons | lucide-react |
| Backend | Python 3.14, FastAPI, SQLAlchemy, Pydantic |
| База данных | SQLite (dev) / PostgreSQL (prod) |
| Документация | Swagger (`/docs`), Mermaid-диаграммы |

## Структура проекта

```
backend/
  app/
    api/strategies.py       — API endpoints (25+ методов)
    models.py               — SQLAlchemy модели (Strategy, InvestorConnection)
    schemas.py              — Pydantic схемы (v2 + legacy)
    main.py                 — Точка входа FastAPI
    config.py               — Конфигурация
    utils/file_storage.py   — Файловое хранилище
    robot_manager/manager.py— Менеджер роботов (MT4/MT5)
    adapters/               — MT4 / MT5 адаптеры
  requirements.txt

frontend/artifacts/trading-marketplace/
  src/
    pages/                  — Home, StrategyDetail
    components/             — StrategiesTab, StrategyCreateTab, DeployDialog
    components/ui/          — shadcn/ui компоненты
    lib/api-client/         — Generated API client (orval)
    hooks/                  — use-toast
  vite.config.ts
  package.json

TRM_SRS.md                  — Системный документ требований (SRS)
```

## API Endpoints

### Стратегии

| Метод | Endpoint | Описание |
|-------|----------|----------|
| POST | `/api/strategies/` | Создание стратегии |
| GET | `/api/strategies/` | Список стратегий |
| GET | `/api/strategies/{id}` | Детали стратегии |
| DELETE | `/api/strategies/{id}` | Удаление стратегии |
| POST | `/api/strategies/seed` | Генерация демо-стратегий |
| GET | `/api/strategies/{id}/performance` | Trading Performance (график) |
| GET | `/api/strategies/{id}/trades` | Пагинированная история сделок |

### Deploy / Connect

| Метод | Endpoint | Описание |
|-------|----------|----------|
| POST | `/api/strategies/{id}/connect-account` | Подключение инвестора к MT счёту |
| POST | `/api/strategies/{id}/disconnect-investor` | Отключение инвестора (MM) |
| POST | `/api/strategies/{id}/deploy/upload` | Загрузка .ex4/.ex5/.set файлов |
| POST | `/api/strategies/{id}/deploy/url` | Загрузка из URL |
| POST | `/api/strategies/{id}/deploy/launch` | Запуск терминала |
| POST | `/api/strategies/{id}/deploy` | Full deploy pipeline |

### Управление

| Метод | Endpoint | Описание |
|-------|----------|----------|
| POST | `/api/strategies/{id}/connect` | Подключение к MT4/MT5 |
| POST | `/api/strategies/{id}/start` | Запуск робота |
| POST | `/api/strategies/{id}/stop` | Остановка робота |
| GET | `/api/strategies/{id}/status` | Статус робота |
| POST | `/api/strategies/{id}/replace-robot` | Проверка замены |
| POST | `/api/strategies/{id}/confirm-replace` | Подтверждение замены |
| PUT | `/api/strategies/{id}/submit` | Отправка на модерацию |
| PUT | `/api/strategies/{id}/approve` | Одобрение стратегии |
| PUT | `/api/strategies/{id}/reject` | Отклонение стратегии |

### Marketplace

| Метод | Endpoint | Описание |
|-------|----------|----------|
| GET | `/api/strategies/marketplace` | Marketplace с фильтрацией |
| POST | `/api/strategies/investor/connect` | Подключение инвестора |
| POST | `/api/strategies/investor/disconnect/{id}` | Отписка инвестора |

### System

| Метод | Endpoint | Описание |
|-------|----------|----------|
| GET | `/api/healthz` | Health check |
| GET | `/api/stats` | Статистика платформы |

## Комиссии (Fee System)

Каждая стратегия поддерживает три типа комиссии:

| Тип | Описание | MM доля | Agent доля |
|-----|----------|---------|------------|
| **Performance Fee** | % от прибыли инвестора | `performanceFee` | `performanceAgentFee` |
| **Subscription Fee** | Фиксированная плата (Daily/Weekly/Monthly/Annual) | `subscriptionFee` | `subscriptionAgentFee` |
| **Entry Fee** | % от суммы входа инвестора | `entryFee` | `entryAgentFee` |

## Модель данных

**Strategy** — стратегия со статусами:
`draft → pending_moderation → approved → rejected → published` + `running`, `stopped`, `error`

**InvestorConnection** — связь инвестора со стратегией (макс. 5 на одного MM)

## Документация

Полный SRS с BPMN, Sequence, C4 и State диаграммами: [`TRM_SRS.md`](TRM_SRS.md)

---

*Статус: Реализовано. Версия 4.0 — новый frontend, расширенные схемы, deploy pipeline, fee system.*
