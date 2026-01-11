# 📈 Investment Portfolio Tracker (Backend)

A robust, asynchronous backend system for tracking investment portfolios, monitoring real-time crypto asset prices, and managing price alerts. Built with modern Python, FastAPI, and Modular Architecture. The project was built with a strong emphasis on **Code Quality**, **Test-Driven Development (TDD)**, and **Performance**.

![Python](https://img.shields.io/badge/Python-3.12-blue?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.124.2-009688?logo=fastapi&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-17-336791?logo=postgresql&logoColor=white)
![Redis](https://img.shields.io/badge/Redis-Cache-DC382D?logo=redis&logoColor=white)
![Celery](https://img.shields.io/badge/Celery-Distributed%20Tasks-37814A?logo=celery&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?logo=docker&logoColor=white)

## 🚀 Key Features

* **Portfolio Management**: Create multiple portfolios, add/remove assets, and track weighted average buy prices.
* **Real-time Market Data**: Fetches live crypto prices via CoinGecko API with caching strategies using **Redis**.
* **Background Workers**: **Celery** & **Redis** powered workers for scheduled tasks (price updates every 5 min).
* **Smart Alerts**: System monitors prices in the background and sends email notifications (mocked) when targets are hit.
* **Analytics & History**: Daily snapshots of portfolio performance - Total Value and PnL (profit and loss in percentage) stored for historical charting.
* **Secure Auth**: JWT Authentication with secure password hashing.
* **High Performance**: Fully asynchronous database drivers (`asyncpg`) and endpoints.

## 🛠️ Tech Stack

* **Language**: Python 3.12
* **Framework**: FastAPI
* **Database**: PostgreSQL (SQLAlchemy Async ORM + Alembic Migrations)
* **Task Queue**: Celery + Redis (Message Broker)
* **Caching**: Redis
* **Dependency Management**: `uv` (modern, fast Python package manager)
* **Testing**: Pytest + Testcontainers logic (separate test DB)
* **Containerization**: Docker & Docker Compose

## 🏗️ Architecture

The system is composed of 5 main services managed via Docker Compose:

1.  **Web**: FastAPI application serving the REST API.
2.  **Worker**: Celery worker processing background jobs (alerts, price updates).
3.  **Beat**: Celery beat scheduler for periodic tasks (cron jobs).
4.  **Database**: PostgreSQL for persistent data storage.
5.  **Redis**: For caching and Celery message broker.

## 📏 Quality Standards
* **TDD (Test-Driven Development):** Code written in the Red-Green-Refactor cycle using `pytest`.
* **Type Hinting:** Full static typing checked by `mypy`.
* **Linting & Formatting:** Code formatted and checked by `ruff`.
* **Pre-commit hooks:** Automatic quality verification before every commit.

## ⚙️ Installation & Setup

### Prerequisites
* Docker & Docker Compose installed.

### 1. Clone the repository
```bash
git clone https://github.com/RadomirNiewiadomski/investment-tracker.git
cd investment-tracker
```

### 2. Environment Configuration

Create a `.env` file in the root directory using the provided `.env.example` as a template.

### 3. Run with Docker

Build and start the services:

```bash
docker compose up --build
```

**The API will be available at `http://localhost:8000`.**

Note: Database migrations are applied automatically on container startup.

### 4. Seed the database (optional)

To populate the database with a sample data (demo user, portfolio, assets, and alerts) run:

```bash
docker compose run --rm web uv run python -m src.scripts.seed_db
```

## 📚 API Documentation

Once the app is running, access the interactive Swagger UI:

👉 **[http://localhost:8000/docs]**

### Core Endpoints:

* `POST /api/v1/auth/register` - Create account
* `POST /api/v1/auth/token` - Login
* `GET /api/v1/portfolios` - List user portfolios
* `POST /api/v1/portfolios/{id}/assets` - Add asset (e.g., BTC, ETH)
* `GET /api/v1/portfolios/{id}/history` - Get historical chart data (for frontend developers to build charts)
* `POST /api/v1/alerts` - Set price alert

## 🧪 Testing and Code Quality

The project uses `pytest` for Unit and Integration testing. It spins up a separate test database to ensure data isolation.

**Run all tests:**

```bash
docker compose run --rm web uv run pytest
```

**Check static typing (mypy):**

```bash
docker compose run --rm web uv run mypy .
```

**Check code style (ruff):**

```bash
docker compose run --rm web uv run ruff check .
```

## 🔄 Background Tasks

* **Price Updates**: Runs every 5 minutes to refresh asset prices in Redis.
* **Alert Processing**: Checks triggered alerts immediately after price updates and sends email notifications (mocked for now).
* **Daily Snapshot**: Runs every day at 00:00 UTC to record portfolio history.

-----

## Created by:
Radomir Niewiadomski
