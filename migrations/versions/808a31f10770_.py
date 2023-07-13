"""empty message

Revision ID: 808a31f10770
Revises: ec0cedba96f5
Create Date: 2021-08-22 11:28:26.431853

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '808a31f10770'
down_revision = 'ec0cedba96f5'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('offers_history', sa.Column('offer', sa.Integer(), nullable=True))
    op.create_foreign_key(None, 'offers_history', 'offers', ['offer'], ['id'])
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint(None, 'offers_history', type_='foreignkey')
    op.drop_column('offers_history', 'offer')
    # ### end Alembic commands ###