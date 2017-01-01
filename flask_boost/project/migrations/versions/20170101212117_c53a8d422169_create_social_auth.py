"""create social auth

Revision ID: c53a8d422169
Revises: c75c62f168f2
Create Date: 2017-01-01 21:21:17.622345

"""

# revision identifiers, used by Alembic.
revision = 'c53a8d422169'
down_revision = '3d8f34e83d23'

from alembic import op
import sqlalchemy as sa


def downgrade():
    op.drop_table('social_auth_association')
    op.drop_table('social_auth_usersocialauth')
    op.drop_table('social_auth_code')
    op.drop_table('social_auth_nonce')


def upgrade():
    op.create_table('social_auth_nonce',
    sa.Column('id', sa.INTEGER(), nullable=False),
    sa.Column('server_url', sa.VARCHAR(length=255), autoincrement=False, nullable=True),
    sa.Column('timestamp', sa.INTEGER(), autoincrement=False, nullable=True),
    sa.Column('salt', sa.VARCHAR(length=40), autoincrement=False, nullable=True),
    sa.PrimaryKeyConstraint('id', name=u'social_auth_nonce_pkey'),
    sa.UniqueConstraint('server_url', 'timestamp', 'salt', name=u'social_auth_nonce_server_url_timestamp_salt_key')
    )
    op.create_table('social_auth_code',
    sa.Column('id', sa.INTEGER(), nullable=False),
    sa.Column('email', sa.VARCHAR(length=200), autoincrement=False, nullable=True),
    sa.Column('code', sa.VARCHAR(length=32), autoincrement=False, nullable=True),
    sa.PrimaryKeyConstraint('id', name=u'social_auth_code_pkey'),
    sa.UniqueConstraint('code', 'email', name=u'social_auth_code_code_email_key')
    )
    op.create_table('social_auth_usersocialauth',
    sa.Column('id', sa.INTEGER(), nullable=False),
    sa.Column('provider', sa.VARCHAR(length=32), autoincrement=False, nullable=True),
    sa.Column('extra_data', sa.TEXT(), autoincrement=False, nullable=True),
    sa.PrimaryKeyConstraint('id', name=u'social_auth_usersocialauth_pkey')
    )
    op.create_table('social_auth_association',
    sa.Column('id', sa.INTEGER(), nullable=False),
    sa.Column('server_url', sa.VARCHAR(length=255), autoincrement=False, nullable=True),
    sa.Column('handle', sa.VARCHAR(length=255), autoincrement=False, nullable=True),
    sa.Column('secret', sa.VARCHAR(length=255), autoincrement=False, nullable=True),
    sa.Column('issued', sa.INTEGER(), autoincrement=False, nullable=True),
    sa.Column('lifetime', sa.INTEGER(), autoincrement=False, nullable=True),
    sa.Column('assoc_type', sa.VARCHAR(length=64), autoincrement=False, nullable=True),
    sa.PrimaryKeyConstraint('id', name=u'social_auth_association_pkey'),
    sa.UniqueConstraint('server_url', 'handle', name=u'social_auth_association_server_url_handle_key')
    )
