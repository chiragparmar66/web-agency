"""add inquiry subject and read_at and optional phone

Revision ID: 8b4c2e61a901
Revises: f71be392a823
Create Date: 2026-10-03 22:08:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '8b4c2e61a901'
down_revision: Union[str, None] = 'f71be392a823'
branch_labels: Union[Sequence[str], None] = None
depends_on: Union[Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table('inquiries', schema=None) as batch_op:
        batch_op.add_column(sa.Column('subject', sa.String(length=255), nullable=True))
        batch_op.add_column(sa.Column('read_at', sa.DateTime(timezone=True), nullable=True))
        batch_op.alter_column('phone', existing_type=sa.String(length=50), nullable=True)


def downgrade() -> None:
    with op.batch_alter_table('inquiries', schema=None) as batch_op:
        batch_op.alter_column('phone', existing_type=sa.String(length=50), nullable=False)
        batch_op.drop_column('read_at')
        batch_op.drop_column('subject')
