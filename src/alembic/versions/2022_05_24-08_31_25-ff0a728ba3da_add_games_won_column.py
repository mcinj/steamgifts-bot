"""add games_won column

Revision ID: ff0a728ba3da
Revises: 15c028536ef5
Create Date: 2022-05-24 08:31:25.684099

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'ff0a728ba3da'
down_revision = '15c028536ef5'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('notification', sa.Column('games_won', sa.Integer(), nullable=True))
    # set a default for previous won notifications
    with op.get_context().autocommit_block():
        op.execute("UPDATE notification SET games_won=1 WHERE type='won';")


def downgrade():
    op.drop_column('notification', 'games_won')
