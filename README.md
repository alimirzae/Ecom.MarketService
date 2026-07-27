# Ecom.MarketService

## Overview

Ecom.MarketService is a FastAPI microservice responsible for collecting,
storing and serving market data for the Ecom ERP platform.

Current providers:

- Navasan (Widget)
- Future:
  - TGJU
  - Bonbast
  - Crypto Exchanges
  - Product Price Crawlers

---

## Technology Stack

- Python 3.12+
- FastAPI
- SQLAlchemy 2.x
- MySQL 8
- Alembic
- APScheduler
- uv
- httpx
- BeautifulSoup

---

## Project Structure

app/

    api/

    core/

    database/

    dto/

    entities/

    providers/

    repository/

    services/

    scheduler/

    utils/

scripts/

tests/

---

## Run

Create virtual environment

uv sync

Run service

uv run uvicorn app.main:app --reload

Run tests

uv run pytest

---

## Database

Database Name

ecom_market

---

## Coding Rules

- SQLAlchemy 2 style
- Repository Pattern
- Provider Plugin Architecture
- DTO between layers
- Stateless Services
- Type Hints Required
- Black Formatting

---

## Current Status

Version 0.1

Implemented

- Project Structure
- MySQL
- SQLAlchemy
- Navasan Provider
- Database Entities

Next

- Repository
- Market Service
- API
- Scheduler

---

## License

Private
Ecom ERP