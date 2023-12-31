"""empty message

Revision ID: 9d53704d1f14
Revises: b6347bb32cfa
Create Date: 2021-12-06 12:37:59.954354

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '9d53704d1f14'
down_revision = 'b6347bb32cfa'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('trades', sa.Column('paypal_costs', sa.Float(), nullable=True))
    op.add_column('trades', sa.Column('shipping_and_handling_costs', sa.Float(), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('trades', 'shipping_and_handling_costs')
    op.drop_column('trades', 'paypal_costs')
    # ### end Alembic commands ###
