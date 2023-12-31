"""empty message

Revision ID: 894e4c50f1fc
Revises: 0f2da3392995
Create Date: 2021-09-11 12:41:26.250964

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '894e4c50f1fc'
down_revision = '0f2da3392995'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('offers_history', sa.Column('condition_id', sa.Integer(), nullable=True))
    op.create_foreign_key(None, 'offers_history', 'conditions', ['condition_id'], ['database_id'])
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint(None, 'offers_history', type_='foreignkey')
    op.drop_column('offers_history', 'condition_id')
    # ### end Alembic commands ###
