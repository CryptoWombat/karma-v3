"""add validator_api_keys table

Revision ID: c8d4e5f6a789
Revises: b73c8ce24283
Create Date: 2026-02-18

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'c8d4e5f6a789'
down_revision: Union[str, Sequence[str], None] = 'b73c8ce24283'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'validator_api_keys',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('key_hash', sa.String(length=64), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('revoked_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_validator_api_keys_key_hash'), 'validator_api_keys', ['key_hash'], unique=True)


def downgrade() -> None:
    op.drop_index(op.f('ix_validator_api_keys_key_hash'), table_name='validator_api_keys')
    op.drop_table('validator_api_keys')
