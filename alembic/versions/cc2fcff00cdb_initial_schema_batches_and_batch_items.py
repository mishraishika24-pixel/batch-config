"""initial schema: batches and batch_items

Revision ID: cc2fcff00cdb
Revises: 
Create Date: 2026-07-03 22:46:59.303042

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = 'cc2fcff00cdb'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# Native Postgres ENUM types are created independently of the tables that
# use them, so we manage their lifecycle explicitly (create_type=False on
# the columns) instead of relying on create_table/drop_table to do it
# implicitly. Without this, `downgrade` leaves the type behind and a
# subsequent `upgrade` fails with "type already exists".
batch_status_enum = postgresql.ENUM(
    "PENDING", "PROCESSING", "COMPLETED", "COMPLETED_WITH_ERRORS", "FAILED",
    name="batch_status",
    create_type=False,
)
item_status_enum = postgresql.ENUM(
    "PENDING", "PROCESSING", "COMPLETED", "FAILED",
    name="item_status",
    create_type=False,
)


def upgrade() -> None:
    """Upgrade schema."""
    bind = op.get_bind()
    batch_status_enum.create(bind, checkfirst=True)
    item_status_enum.create(bind, checkfirst=True)

    op.create_table('batches',
    sa.Column('id', sa.Uuid(), nullable=False),
    sa.Column('status', batch_status_enum, nullable=False),
    sa.Column('total_items', sa.Integer(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_batches_status'), 'batches', ['status'], unique=False)
    op.create_table('batch_items',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('batch_id', sa.Uuid(), nullable=False),
    sa.Column('payload', sa.JSON(), nullable=False),
    sa.Column('status', item_status_enum, nullable=False),
    sa.Column('result', sa.JSON(), nullable=True),
    sa.Column('error_message', sa.Text(), nullable=True),
    sa.Column('attempts', sa.Integer(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['batch_id'], ['batches.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_batch_items_batch_id_status', 'batch_items', ['batch_id', 'status'], unique=False)
    op.create_index('ix_batch_items_status', 'batch_items', ['status'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index('ix_batch_items_status', table_name='batch_items')
    op.drop_index('ix_batch_items_batch_id_status', table_name='batch_items')
    op.drop_table('batch_items')
    op.drop_index(op.f('ix_batches_status'), table_name='batches')
    op.drop_table('batches')

    bind = op.get_bind()
    item_status_enum.drop(bind, checkfirst=True)
    batch_status_enum.drop(bind, checkfirst=True)
