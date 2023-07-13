"""empty message

Revision ID: 2a8d6b8c5431
Revises: 0cf3daa4fb41
Create Date: 2021-09-11 15:18:36.291167

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '2a8d6b8c5431'
down_revision = '0cf3daa4fb41'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('merchants', sa.Column('database_id', sa.Integer(), nullable=True))
    op.create_unique_constraint(None, 'merchants', ['short_code'])
    op.create_foreign_key(None, 'merchants_condition_multiplier', 'merchants', ['merchant_id'], ['database_id'])
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint(None, 'merchants_condition_multiplier', type_='foreignkey')
    op.drop_constraint(None, 'merchants', type_='unique')
    op.drop_column('merchants', 'database_id')
    # ### end Alembic commands ###
