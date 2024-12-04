"""Add result_dir to TestResult

Revision ID: 3382dd1b72b1
Revises: 26aba17bc1c6
Create Date: 2024-12-04 05:46:39.641374

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '3382dd1b72b1'
down_revision = '26aba17bc1c6'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('test_results', schema=None) as batch_op:
        batch_op.add_column(sa.Column('result_dir', sa.Text(), nullable=True))

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('test_results', schema=None) as batch_op:
        batch_op.drop_column('result_dir')

    # ### end Alembic commands ###