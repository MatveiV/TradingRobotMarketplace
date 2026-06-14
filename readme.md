# Trading Robot Marketplace

**Copy Trading Platform** — создание, публикация и подключение торговых роботов для MetaTrader 4 и MetaTrader 5.

Два типа пользователей:
- **Money Manager (Управляющий)** — создаёт стратегию, загружает робота (`.ex4`/`.ex5` + `.set`), подключается к торговому счёту, устанавливает комиссию и публикует стратегию в Marketplace
- **Инвестор** — просматривает стратегии, фильтрует по доходности/риску/платформе, подключается и копирует сделки

## Быстрый старт

```bash
# Backend
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
# API docs: http://localhost:8000/docs

# Frontend
cd frontend
npm install
npm run dev
# UI: http://localhost:5173
```

## Возможности

| Возможность | Описание |
|------------|----------|
| **Создание стратегии** | Название, описание, логотип, подписка (daily/weekly/monthly), цена |
| **Загрузка робота** | Файлы `.ex4`/`.ex5` + `.set` для MT4/MT5 |
| **Подключение к счёту** | Логин, пароль, сервер для MT4 или MT5 |
| **Замена робота** | Если другой робот запущен — диалог подтверждения замены |
| **Торговая история** | Загрузка сделок, расчёт Trading Performance (PnL, win rate) |
| **Модерация** | Стратегия проходит проверку перед публикацией в Marketplace |
| **Marketplace** | Список стратегий с фильтрацией по платформе, риску, сортировкой по доходности |
| **Copy Trading** | Подключение инвестора к стратегии (до 5 подключений на одного MM), комиссия % от прибыли, отписка в любой момент |

## Архитектура

```
┌──────────────┐     ┌──────────────┐     ┌──────────────────┐
│  Frontend    │────▶│  Backend API │────▶│  MT4 / MT5       │
│  React + TS  │     │  FastAPI     │     │  Adapter (mock)  │
└──────────────┘     └──────┬───────┘     └──────────────────┘
                            │
                     ┌──────┴───────┐
                     │  SQLite/DB   │
                     └──────────────┘
```

## Технологии

| Компонент | Технология |
|-----------|-----------|
| Frontend | React 18, TypeScript, Tailwind CSS, Vite, React Router, Axios |
| Backend | Python, FastAPI, SQLAlchemy, Pydantic |
| База данных | SQLite (dev) / PostgreSQL (prod) |
| Документация | Swagger (`/docs`), Mermaid-диаграммы |

## Структура проекта

```
backend/
  app/
    api/strategies.py    — API endpoints (16 методов)
    models.py            — SQLAlchemy модели (Strategy, InvestorConnection)
    schemas.py           — Pydantic схемы
    main.py              — Точка входа FastAPI
    adapters/            — MT4 / MT5 адаптеры
    robot_manager/       — Менеджер роботов
    config.py            — Конфигурация
  requirements.txt

frontend/
  src/
    pages/               — Marketplace, StrategyDetails, StrategiesPage, CreateStrategy
    components/          — StrategyForm, ReplaceRobotDialog
    services/api.ts      — API клиент (Axios)
    types/index.ts       — TypeScript типы
  package.json

TRM_SRS.md               — Системный документ требований (SRS)
Task4BA.docx             — Исходное задание
```

## API Endpoints

| Метод | Endpoint | Описание |
|-------|----------|----------|
| POST | `/api/strategies/` | Создание стратегии |
| GET | `/api/strategies/` | Список стратегий |
| GET | `/api/strategies/{id}` | Детали стратегии |
| POST | `/api/strategies/{id}/connect` | Подключение к MT4/MT5 |
| POST | `/api/strategies/{id}/start` | Запуск робота |
| POST | `/api/strategies/{id}/stop` | Остановка робота |
| GET | `/api/strategies/{id}/status` | Статус робота |
| GET | `/api/strategies/{id}/performance` | Trading Performance |
| POST | `/api/strategies/{id}/replace-robot` | Проверка замены |
| POST | `/api/strategies/{id}/confirm-replace` | Подтверждение замены |
| PUT | `/api/strategies/{id}/submit` | Отправка на модерацию |
| PUT | `/api/strategies/{id}/approve` | Одобрение стратегии |
| PUT | `/api/strategies/{id}/reject` | Отклонение стратегии |
| GET | `/api/strategies/marketplace` | Marketplace с фильтрацией |
| POST | `/api/strategies/investor/connect` | Подключение инвестора |
| POST | `/api/strategies/investor/disconnect/{id}` | Отписка инвестора |

## Модель данных

- **Strategy** — стратегия со статусами: `draft → pending_moderation → approved → rejected → published` + `running`, `stopped`, `error`
- **InvestorConnection** — связь инвестора со стратегией (макс. 5 на одного MM)

## Документация

Полный SRS с BPMN, Sequence, C4 и State диаграммами: [`TRM_SRS.md`](TRM_SRS.md)

---

*Статус: Реализовано. Все требования Task4BA.docx выполнены.*
