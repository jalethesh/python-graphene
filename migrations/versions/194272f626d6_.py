"""empty message

Revision ID: 194272f626d6
Revises: 5b96d5b378b0
Create Date: 2021-08-23 13:50:51.021086

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '194272f626d6'
down_revision = '5b96d5b378b0'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('offers_history', 'scryfall_card_id')
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('offers_history', sa.Column('scryfall_card_id', sa.VARCHAR(), autoincrement=False, nullable=True))
    # ### end Alembic commands ###