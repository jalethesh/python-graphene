"""empty message

Revision ID: 11648da597a8
Revises: b3dce92b6a61
Create Date: 2021-09-11 15:47:45.406167

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '11648da597a8'
down_revision = 'b3dce92b6a61'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_unique_constraint(None, 'merchants', ['shortcode'])
    op.create_foreign_key(None, 'merchants_condition_multiplier', 'merchants', ['merchant'], ['shortcode'])
    op.add_column('offers_history', sa.Column('merchant', sa.String(), nullable=True))
    op.create_foreign_key(None, 'offers_history', 'merchants', ['merchant'], ['shortcode'])
    op.drop_column('offers_history', 'merchant_string')
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('offers_history', sa.Column('merchant_string', sa.VARCHAR(), autoincrement=False, nullable=True))
    op.drop_constraint(None, 'offers_history', type_='foreignkey')
    op.drop_column('offers_history', 'merchant')
    op.drop_constraint(None, 'merchants_condition_multiplier', type_='foreignkey')
    op.drop_constraint(None, 'merchants', type_='unique')
    # ### end Alembic commands ###