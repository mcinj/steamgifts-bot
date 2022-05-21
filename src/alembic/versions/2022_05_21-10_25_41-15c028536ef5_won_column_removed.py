"""won column removed

Revision ID: 15c028536ef5
Revises: 1da33402b659
Create Date: 2022-05-21 10:25:41.647723

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = '15c028536ef5'
down_revision = '1da33402b659'
branch_labels = None
depends_on = None


def upgrade():
    op.drop_column('giveaway', 'won')


def downgrade():
    # add columns as nullable as existing records don't have that column value set
    op.add_column('giveaway', sa.Column('won', sa.Boolean(), nullable=True))
    # set value on new columns for all records
    with op.get_context().autocommit_block():
        op.execute("UPDATE giveaway SET won=false WHERE won is null;")
    # SQLite doesn't support ALTERs so alembic uses a batch mode
    # Set columns to non-nullable now that all records have a value
    with op.batch_alter_table('giveaway') as batch_op:
        batch_op.alter_column('won', nullable=False)
