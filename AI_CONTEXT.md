# AI_CONTEXT.md

This file is the authoritative reference for all AI agents working on this project.

Any AI assistant MUST read this file before generating code.

------------------------------------------------------------

PROJECT

------------------------------------------------------------

Name

Ecom.MarketService

Purpose

Market Data Platform for Ecom ERP.

This service collects market data from external providers,
stores them inside MySQL,
and exposes them through REST APIs.

Current supported data

- Currency
- Gold
- Coin

Future

- Cryptocurrency
- Commodity Prices
- Weather
- AI Predictions
- OCR Services

------------------------------------------------------------

ARCHITECTURE

------------------------------------------------------------

FastAPI

↓

Market API

↓

Market Service

↓

Repository

↓

Provider Registry

↓

Provider Plugins

↓

Remote Providers

↓

MySQL

------------------------------------------------------------

ARCHITECTURE RULES

------------------------------------------------------------

DO NOT CHANGE WITHOUT EXPLICIT APPROVAL.

Repository Pattern

Provider Plugin Pattern

DTO between layers

Stateless Services

SQLAlchemy 2.x

MySQL

FastAPI

Alembic

uv package manager

------------------------------------------------------------

DIRECTORY STRUCTURE

------------------------------------------------------------

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

------------------------------------------------------------

PROVIDER RULES

------------------------------------------------------------

Every provider is a plugin.

Example

providers/

navasan/

provider.py

parser.py

Future

providers/

tgju/

provider.py

parser.py

Provider responsibilities

- HTTP Request

- Parse Response

- Return DTO

Provider MUST NOT

- Access Database

- Use SQLAlchemy

- Know Repository

------------------------------------------------------------

REPOSITORY RULES

------------------------------------------------------------

Repository owns

Database

Transactions

Caching

History

Latest Prices

Repository MUST NOT

Call HTTP

Parse HTML

Know FastAPI

------------------------------------------------------------

SERVICE RULES

------------------------------------------------------------

Business logic only.

Service MUST NOT

Know SQLAlchemy Models

Know HTML

Know HTTP

------------------------------------------------------------

API RULES

------------------------------------------------------------

REST API only.

API MUST NOT

Contain Business Logic.

------------------------------------------------------------

DATABASE

------------------------------------------------------------

Database

ecom_market

Main Tables

market_provider

market_item

market_price_latest

market_price_history

------------------------------------------------------------

ROADMAP

------------------------------------------------------------

Phase 1

✔ Structure

✔ Database

✔ Provider

Phase 2

Repository

Market Service

REST API

Phase 3

Scheduler

Logging

Retry

Caching

Phase 4

Additional Providers

Crawler

AI

OCR

------------------------------------------------------------

IMPORTANT

------------------------------------------------------------

Before changing architecture

Update this file first.

This file is the Single Source of Truth.
