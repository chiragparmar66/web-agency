"""add deployment and client approval

Revision ID: f71be392a823
Revises: e52ac3d91b41
Create Date: 2026-10-03 21:30:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'f71be392a823'
down_revision = 'e52ac3d91b41'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1. Update website_builds with client approval columns
    with op.batch_alter_table('website_builds', schema=None) as batch_op:
        batch_op.add_column(
            sa.Column(
                'client_approved',
                sa.Boolean(),
                nullable=False,
                server_default=sa.text('0'),
            )
        )
        batch_op.add_column(sa.Column('client_approved_at', sa.DateTime(timezone=True), nullable=True))
        batch_op.add_column(sa.Column('client_feedback', sa.Text(), nullable=True))

    # 2. Create deployments table
    op.create_table(
        'deployments',
        sa.Column('id', sa.String(length=36), primary_key=True, nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('project_id', sa.String(length=36), sa.ForeignKey('projects.id', ondelete='CASCADE'), nullable=False),
        sa.Column('build_id', sa.String(length=36), sa.ForeignKey('website_builds.id', ondelete='CASCADE'), nullable=False),
        sa.Column('version_number', sa.Integer(), nullable=False),
        sa.Column(
            'status',
            sa.Enum(
                'NOT_READY',
                'READY',
                'QUEUED',
                'DEPLOYING',
                'DEPLOYED',
                'FAILED',
                'ROLLED_BACK',
                name='deployment_status_enum',
                native_enum=False,
            ),
            nullable=False,
            server_default='READY',
        ),
        sa.Column('provider', sa.String(length=50), nullable=False),
        sa.Column('provider_deployment_id', sa.String(length=255), nullable=True),
        sa.Column('live_url', sa.String(length=500), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('deployed_by_user_id', sa.String(length=36), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('deployed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('deployment_metadata', sa.JSON(), nullable=True),
        sa.Column('smoke_test_status', sa.String(length=50), server_default='NOT_RUN', nullable=True),
        sa.Column('smoke_test_details', sa.JSON(), nullable=True),
    )
    with op.batch_alter_table('deployments', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_deployments_project_id'), ['project_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_deployments_build_id'), ['build_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_deployments_status'), ['status'], unique=False)


def downgrade() -> None:
    with op.batch_alter_table('deployments', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_deployments_status'))
        batch_op.drop_index(batch_op.f('ix_deployments_build_id'))
        batch_op.drop_index(batch_op.f('ix_deployments_project_id'))

    op.drop_table('deployments')

    with op.batch_alter_table('website_builds', schema=None) as batch_op:
        batch_op.drop_column('client_feedback')
        batch_op.drop_column('client_approved_at')
        batch_op.drop_column('client_approved')
