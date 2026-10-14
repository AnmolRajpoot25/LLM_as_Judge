# -*- coding: utf-8 -*-
"""Add UserApiKey table

Revision ID: 003
Revises: 002
Create Date: 2024-01-03 00:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '003'
down_revision: Union[str, None] = '002'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'user_api_keys',
        sa.Column('id', sa.String(64), nullable=False),
        sa.Column('user_id', sa.String(50), nullable=False),
        sa.Column('provider', sa.String(32), nullable=False),
        sa.Column('api_key', sa.Text(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_user_api_keys_user_id', 'user_api_keys', ['user_id'], unique=False)
    op.create_index('ix_user_api_keys_id', 'user_api_keys', ['id'], unique=False)


def downgrade() -> None:
    op.drop_table('user_api_keys')
