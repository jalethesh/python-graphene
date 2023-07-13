"""empty message

Revision ID: dc0b04d88ea0
Revises: d7c36626d575
Create Date: 2021-08-20 11:52:49.668294

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'dc0b04d88ea0'
down_revision = 'd7c36626d575'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_unique_constraint(None, 'sets', ['scryfall_set_id'])
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint(None, 'sets', type_='unique')
    # ### end Alembic commands ###
