"""add build review status to website builds

Revision ID: e52ac3d91b41
Revises: d14eb2f45735
Create Date: 2026-10-03 21:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'e52ac3d91b41'
down_revision = 'd14eb2f45735'
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table('website_builds', schema=None) as batch_op:
        batch_op.add_column(
            sa.Column(
                'review_status',
                sa.Enum('PENDING_REVIEW', 'APPROVED', 'REJECTED', name='build_review_status_enum', native_enum=False),
                nullable=False,
                server_default='PENDING_REVIEW',
            )
        )
        batch_op.add_column(sa.Column('review_notes', sa.Text(), nullable=True))
        batch_op.add_column(sa.Column('reviewed_by_user_id', sa.String(length=36), nullable=True))
        batch_op.add_column(sa.Column('reviewed_at', sa.DateTime(timezone=True), nullable=True))
        batch_op.create_foreign_key(
            'fk_website_builds_reviewed_by_user_id',
            'users',
            ['reviewed_by_user_id'],
            ['id'],
            ondelete='SET NULL',
        )
        batch_op.create_index(batch_op.f('ix_website_builds_review_status'), ['review_status'], unique=False)


def downgrade() -> None:
    with op.batch_alter_table('website_builds', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_website_builds_review_status'))
        batch_op.drop_constraint('fk_website_builds_reviewed_by_user_id', type_='foreignkey')
        batch_op.drop_column('reviewed_at')
        batch_op.drop_column('reviewed_by_user_id')
        batch_op.drop_column('review_notes')
        batch_op.drop_column('review_status')
