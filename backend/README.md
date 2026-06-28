# SellMeat Backend

FastAPI backend for the SellMeat meat ordering app.

## Setup

```bash
# Create virtual environment and install dependencies
uv venv
uv pip install -e .

# Copy env file
cp .env.example .env
# Edit .env with your PostgreSQL credentials

# Run migrations
alembic revision --autogenerate -m "initial"
alembic upgrade head

# Seed sample data
python seed.py

# Start server
uvicorn app.main:app --reload
```

## API Docs

Once running, visit:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Default Seed Accounts

- **Seller**: seller@sellmeat.com / password123
- **Customer**: customer@example.com / password123
