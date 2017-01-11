"""create init user management

Revision ID: fba2ed6ae503
Revises: None
Create Date: 2017-01-10 11:41:40.358558

"""

# revision identifiers, used by Alembic.
revision = 'fba2ed6ae503'
down_revision = None

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.create_table('role',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(length=80), nullable=True),
    sa.Column('description', sa.String(length=255), nullable=True),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('name')
    )
    op.create_table('user',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(length=255), nullable=True),
    sa.Column('email', sa.String(length=255), nullable=True),
    sa.Column('avatar', sa.String(length=200), nullable=True),
    sa.Column('password', sa.String(length=255), nullable=True),
    sa.Column('active', sa.Boolean(), nullable=True),
    sa.Column('confirm_at', sa.DateTime(), nullable=True),
    sa.Column('is_admin', sa.Boolean(), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.Column('auth_provider_id', sa.String(length=255), nullable=True),
    sa.Column('auth_provider_user_id', sa.String(length=255), nullable=True),
    sa.Column('auth_provider_profile_pic', sa.String(length=512), nullable=True),
    sa.Column('auth_provider_access_token', sa.String(length=255), nullable=True),
    sa.Column('auth_provider_secret', sa.String(length=255), nullable=True),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('email'),
    sa.UniqueConstraint('name')
    )
    op.create_table('users_roles',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=True),
    sa.Column('role_id', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['role_id'], ['role.id'], ),
    sa.ForeignKeyConstraint(['user_id'], ['user.id'], ),
    sa.PrimaryKeyConstraint('id')
    )


def downgrade():
    op.drop_table('users_roles')
    op.drop_table('user')
    op.drop_table('role')
