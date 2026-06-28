"""add is_archived to orders

Revision ID: b3f2a1c8e9d4
Revises: a271db64341b
Create Date: 2025-06-28

"""
from alembic import op
import sqlalchemy as sa


revision = "b3f2a1c8e9d4"
down_revision = "a271db64341b"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("orders", sa.Column("is_archived", sa.Boolean(), nullable=False, server_default=sa.text("false")))


def downgrade():
    op.drop_column("orders", "is_archived")
