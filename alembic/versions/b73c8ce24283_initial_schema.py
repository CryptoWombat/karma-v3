"""initial_schema

Revision ID: b73c8ce24283
Revises: 
Create Date: 2026-02-18 00:04:48.030440

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b73c8ce24283'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema: create users, wallets, transactions, referrals."""
    op.create_table(
        'users',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('telegram_user_id', sa.BigInteger(), nullable=False),
        sa.Column('username', sa.String(length=255), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.Column('is_system_wallet', sa.Boolean(), nullable=True),
        sa.Column('is_event_wallet', sa.Boolean(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('telegram_user_id'),
    )
    op.create_index(op.f('ix_users_telegram_user_id'), 'users', ['telegram_user_id'], unique=True)

    op.create_table(
        'wallets',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('user_id', sa.UUID(), nullable=False),
        sa.Column('karma_balance', sa.Numeric(precision=24, scale=6), nullable=False),
        sa.Column('chiliz_balance', sa.Numeric(precision=24, scale=6), nullable=False),
        sa.Column('staked_amount', sa.Numeric(precision=24, scale=6), nullable=False),
        sa.Column('rewards_earned', sa.Numeric(precision=24, scale=6), nullable=False),
        sa.Column('next_unlock_ts', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id'),
    )

    op.create_table(
        'transactions',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('type', sa.Enum('mint', 'send', 'receive', 'stake_deposit', 'unstake_withdraw',
            'stake_reward', 'referral_invite', 'referral_bonus', 'protocol_emission',
            'stakers_distributed', 'swap', 'event_wallet_created', name='transactiontype'),
            nullable=False),
        sa.Column('actor_user_id', sa.UUID(), nullable=True),
        sa.Column('from_user_id', sa.UUID(), nullable=True),
        sa.Column('to_user_id', sa.UUID(), nullable=True),
        sa.Column('amount_karma', sa.Numeric(precision=24, scale=6), nullable=True),
        sa.Column('amount_chiliz', sa.Numeric(precision=24, scale=6), nullable=True),
        sa.Column('metadata', sa.JSON(), nullable=True),
        sa.Column('block_id', sa.BigInteger(), nullable=True),
        sa.ForeignKeyConstraint(['actor_user_id'], ['users.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['from_user_id'], ['users.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['to_user_id'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_transactions_block_id'), 'transactions', ['block_id'], unique=False)
    op.create_index(op.f('ix_transactions_type'), 'transactions', ['type'], unique=False)

    op.create_table(
        'referrals',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('invitee_user_id', sa.UUID(), nullable=False),
        sa.Column('inviter_user_id', sa.UUID(), nullable=False),
        sa.Column('rewarded', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['invitee_user_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['inviter_user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
    )


def downgrade() -> None:
    """Downgrade schema: drop tables."""
    op.drop_table('referrals')
    op.drop_index(op.f('ix_transactions_type'), table_name='transactions')
    op.drop_index(op.f('ix_transactions_block_id'), table_name='transactions')
    op.drop_table('transactions')
    op.drop_table('wallets')
    op.drop_index(op.f('ix_users_telegram_user_id'), table_name='users')
    op.drop_table('users')
