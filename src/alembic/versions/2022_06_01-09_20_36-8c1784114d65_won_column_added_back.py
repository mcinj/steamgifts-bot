"""won column added backed

Revision ID: 8c1784114d65
Revises: ff0a728ba3da
Create Date: 2022-06-01 09:20:36.762279

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = '8c1784114d65'
down_revision = 'ff0a728ba3da'
branch_labels = None
depends_on = None


def upgrade():
    # add columns as nullable as existing records don't have that column value set
    op.add_column('giveaway', sa.Column('won', sa.Boolean(), nullable=True))
    # set value on new columns for all records
    with op.get_context().autocommit_block():
        op.execute("UPDATE giveaway SET won=false WHERE won is null;")
    # SQLite doesn't support ALTERs so alembic uses a batch mode
    # Set columns to non-nullable now that all records have a value
    with op.batch_alter_table('giveaway') as batch_op:
        batch_op.alter_column('won', nullable=False)


def downgrade():
    op.drop_column('giveaway', 'won')
