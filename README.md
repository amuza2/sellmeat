# SellMeat

Meat ordering mobile app for a business that sells chicken, turkey, and other meats to restaurants, retailers, and hotels.

## Tech Stack

- **Mobile App**: Python Flet (MVVM architecture)
- **Backend**: FastAPI
- **Database**: PostgreSQL
- **Env Management**: uv

## Project Structure

```
sellmeat/
├── backend/    # FastAPI API server
└── mobile/     # Flet mobile app (MVVM)
```

## Quick Start

### Backend

```bash
cd backend
uv venv && uv pip install -e .
cp .env.example .env  # Edit with your DB credentials
alembic upgrade head
python seed.py
uvicorn app.main:app --reload
```

### Mobile App

```bash
cd mobile
uv venv && uv pip install -e .
python main.py
```

## Default Accounts

- **Seller**: seller@sellmeat.com / password123
- **Customer**: customer@example.com / password123

## Features

- Customer: Browse products, place orders by weight (kg) or unit, track order status, view history
- Seller: Manage meat types & categories, products & prices, delivery slots, delivery fee, orders status & payment
- Order flow: pending → preparation → delivering → delivered (or cancelled)
- Payment tracking: paid / unpaid per order
