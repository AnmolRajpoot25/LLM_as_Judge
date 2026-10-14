# -*- coding: utf-8 -*-
"""Initial migration

Revision ID: 001
Revises: 
Create Date: 2024-01-01 00:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '001'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'sessions',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('session_id', sa.String(100), nullable=False),
        sa.Column('mode', sa.Enum('GENERATE_AND_COMPARE', 'SINGLE_GENERATION', 'MANUAL_COMPARE', 'BATCH_EVALUATION', name='sessionmode'), nullable=False),
        sa.Column('status', sa.Enum('PENDING', 'GENERATING', 'EVALUATING', 'COMPLETED', 'COMPLETED_WITH_WARNINGS', 'FAILED', 'INSUFFICIENT_SUCCESSFUL_MODELS', name='sessionstatus'), nullable=False),
        sa.Column('prompt', sa.Text(), nullable=False),
        sa.Column('system_prompt', sa.Text(), nullable=True),
        sa.Column('selected_models', sa.JSON(), nullable=False, server_default='[]'),
        sa.Column('position_swap_check', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('session_id'),
    )
    op.create_index('ix_sessions_status', 'sessions', ['status'], unique=False)
    op.create_index('ix_sessions_created_at', 'sessions', ['created_at'], unique=False)

    op.create_table(
        'generation_models',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('session_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('model_id', sa.String(255), nullable=False),
        sa.Column('model_name', sa.String(255), nullable=True),
        sa.Column('provider', sa.String(100), nullable=False),
        sa.Column('answer', sa.Text(), nullable=True),
        sa.Column('latency_seconds', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('input_tokens', sa.Integer(), nullable=True),
        sa.Column('output_tokens', sa.Integer(), nullable=True),
        sa.Column('estimated_cost', sa.Float(), nullable=True),
        sa.Column('cost_source', sa.String(50), nullable=True),
        sa.Column('success', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('error_type', sa.String(100), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('raw_metadata', sa.JSON(), nullable=False, server_default='{}'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['session_id'], ['sessions.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_generation_models_session_id', 'generation_models', ['session_id'], unique=False)
    op.create_index('ix_generation_models_model_id', 'generation_models', ['model_id'], unique=False)

    op.create_table(
        'comparisons',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('session_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('comparison_id', sa.String(100), nullable=False),
        sa.Column('pair_number', sa.Integer(), nullable=False),
        sa.Column('model_a_id', sa.String(255), nullable=False),
        sa.Column('model_a_name', sa.String(255), nullable=False),
        sa.Column('model_b_id', sa.String(255), nullable=False),
        sa.Column('model_b_name', sa.String(255), nullable=False),
        sa.Column('winner_model_id', sa.String(255), nullable=True),
        sa.Column('success', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('judge_latency', sa.Float(), nullable=True),
        sa.Column('judge_result', sa.JSON(), nullable=True),
        sa.Column('raw_judge_response', sa.Text(), nullable=True),
        sa.Column('error_type', sa.String(100), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('position_swap_check', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['session_id'], ['sessions.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('comparison_id'),
    )
    op.create_index('ix_comparisons_session_id', 'comparisons', ['session_id'], unique=False)
    op.create_index('ix_comparisons_winner_model_id', 'comparisons', ['winner_model_id'], unique=False)

    op.create_table(
        'rankings',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('session_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('rank', sa.Integer(), nullable=False),
        sa.Column('model_id', sa.String(255), nullable=False),
        sa.Column('model_name', sa.String(255), nullable=False),
        sa.Column('wins', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('losses', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('ties', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('win_rate', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('score', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('total_matches', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['session_id'], ['sessions.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_rankings_session_id', 'rankings', ['session_id'], unique=False)
    op.create_index('ix_rankings_model_id', 'rankings', ['model_id'], unique=False)

    op.create_table(
        'metrics',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('session_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('total_models', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('successful_generations', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('failed_generations', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('total_comparisons', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('successful_comparisons', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('failed_comparisons', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('total_input_tokens', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('total_output_tokens', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('total_estimated_cost', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('avg_generation_latency', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('avg_judge_latency', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('session_wall_clock_seconds', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('position_swap_enabled', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('position_swap_executed', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('position_swap_consistent', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('position_swap_inconsistent', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['session_id'], ['sessions.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('session_id'),
    )


def downgrade() -> None:
    op.drop_table('metrics')
    op.drop_table('rankings')
    op.drop_table('comparisons')
    op.drop_table('generation_models')
    op.drop_table('sessions')
    op.execute("DROP TYPE IF EXISTS sessionmode")
    op.execute("DROP TYPE IF EXISTS sessionstatus")