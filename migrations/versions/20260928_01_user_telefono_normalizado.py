"""Expand user with a nullable normalized phone field.

Revision ID: 20260928_01
Revises:
Create Date: 2026-09-28
"""
from alembic import op
import sqlalchemy as sa


revision = '20260928_01'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        'user',
        sa.Column('telefono_normalizado', sa.String(length=20), nullable=True),
    )


def downgrade():
    op.drop_column('user', 'telefono_normalizado')