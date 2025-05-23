"""update scheduled tasks model

Revision ID: 5ef0a009832d
Revises: 032f69bc6cf3
Create Date: 2025-01-02 10:56:34.170148

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '5ef0a009832d'
down_revision = '032f69bc6cf3'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('scheduled_tasks', schema=None) as batch_op:
        batch_op.add_column(sa.Column('name', sa.String(length=100), nullable=False))
        batch_op.add_column(sa.Column('cron', sa.String(length=100), nullable=False))
        batch_op.add_column(sa.Column('enabled', sa.Boolean(), nullable=True))
        batch_op.add_column(sa.Column('created_at', sa.DateTime(), nullable=True))
        batch_op.add_column(sa.Column('updated_at', sa.DateTime(), nullable=True))
        batch_op.drop_column('is_active')
        batch_op.drop_column('schedule_type')
        batch_op.drop_column('cron_expression')

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('scheduled_tasks', schema=None) as batch_op:
        batch_op.add_column(sa.Column('cron_expression', sa.VARCHAR(length=100), autoincrement=False, nullable=False))
        batch_op.add_column(sa.Column('schedule_type', sa.VARCHAR(length=20), autoincrement=False, nullable=False))
        batch_op.add_column(sa.Column('is_active', sa.BOOLEAN(), autoincrement=False, nullable=True))
        batch_op.drop_column('updated_at')
        batch_op.drop_column('created_at')
        batch_op.drop_column('enabled')
        batch_op.drop_column('cron')
        batch_op.drop_column('name')

    # ### end Alembic commands ###
