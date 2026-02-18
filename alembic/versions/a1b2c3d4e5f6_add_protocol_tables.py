"""add protocol_state and protocol_blocks tables

Revision ID: a1b2c3d4e5f6
Revises: c8d4e5f6a789
Create Date: 2026-02-18

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, Sequence[str], None] = 'c8d4e5f6a789'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()
    dialect = conn.dialect.name
    # Handle partially applied migration: if tables exist, skip create
    inspector = sa.inspect(conn)
    tables = inspector.get_table_names()
    if 'protocol_state' in tables and 'protocol_blocks' in tables:
        # Ensure protocol_state has a row
        row = conn.execute(sa.text("SELECT COUNT(*) FROM protocol_state")).scalar()
        if row == 0:
            import uuid
            uid = str(uuid.uuid4())
            if dialect == 'sqlite':
                conn.execute(sa.text(
                    "INSERT INTO protocol_state (id, deferred_rewards, updated_at) VALUES (:id, 0, datetime('now'))"
                ).bindparams(id=uid))
            else:
                conn.execute(sa.text(
                    "INSERT INTO protocol_state (id, deferred_rewards, updated_at) VALUES (:id, 0, NOW())"
                ).bindparams(id=uid))
        return

    op.create_table(
        'protocol_state',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('last_processed_ts', sa.DateTime(), nullable=True),
        sa.Column('last_emitted_block_id', sa.BigInteger(), nullable=True),
        sa.Column('deferred_rewards', sa.Numeric(24, 6), nullable=False, server_default='0'),
        sa.Column('utilization_window', sa.JSON(), nullable=True),
        sa.Column('saturated_days', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_table(
        'protocol_blocks',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('block_id', sa.BigInteger(), nullable=False),
        sa.Column('emitted_at', sa.DateTime(), nullable=True),
        sa.Column('reward_total', sa.Numeric(24, 6), nullable=False),
        sa.Column('splits_applied', sa.JSON(), nullable=True),
        sa.Column('processed_tx_count', sa.Integer(), nullable=False, server_default='0'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_protocol_blocks_block_id'), 'protocol_blocks', ['block_id'], unique=False)

    # Insert single protocol_state row
    import uuid
    uid = str(uuid.uuid4())
    dialect = op.get_bind().dialect.name
    if dialect == 'sqlite':
        op.execute(
            sa.text(
                "INSERT INTO protocol_state (id, last_processed_ts, last_emitted_block_id, deferred_rewards, updated_at) "
                "VALUES (:id, NULL, NULL, 0, datetime('now'))"
            ).bindparams(id=uid)
        )
    else:
        op.execute(
            sa.text(
                "INSERT INTO protocol_state (id, last_processed_ts, last_emitted_block_id, deferred_rewards, updated_at) "
                "VALUES (:id, NULL, NULL, 0, NOW())"
            ).bindparams(id=uid)
        )


def downgrade() -> None:
    op.drop_index(op.f('ix_protocol_blocks_block_id'), table_name='protocol_blocks')
    op.drop_table('protocol_blocks')
    op.drop_table('protocol_state')
