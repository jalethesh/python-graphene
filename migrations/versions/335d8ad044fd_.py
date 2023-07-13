"""empty message

Revision ID: 335d8ad044fd
Revises: 8426a24efcb2
Create Date: 2021-10-20 11:32:20.392890

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '335d8ad044fd'
down_revision = '8426a24efcb2'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('latest_offers',
    sa.Column('database_id', sa.Integer(), nullable=False),
    sa.Column('scryfall_card_id', sa.String(), nullable=True),
    sa.Column('item_index', sa.String(), nullable=True),
    sa.Column('last_updated', sa.Date(), nullable=True),
    sa.Column('item_id', sa.Integer(), nullable=True),
    sa.Column('condition', sa.String(), nullable=True),
    sa.ForeignKeyConstraint(['condition'], ['conditions.us_code'], ),
    sa.ForeignKeyConstraint(['item_id'], ['generic_items.id'], ),
    sa.PrimaryKeyConstraint('database_id'),
    sa.UniqueConstraint('database_id')
    )
    op.create_table('latest_offers_history',
    sa.Column('databaseId', sa.Integer(), nullable=False),
    sa.Column('scryfall_card_id', sa.String(), nullable=True),
    sa.Column('last_updated', sa.DateTime(), nullable=True),
    sa.Column('source', sa.String(), nullable=True),
    sa.Column('merchant', sa.String(), nullable=True),
    sa.Column('amount', sa.Float(), nullable=True),
    sa.Column('card_type', sa.String(), nullable=True),
    sa.Column('condition', sa.String(), nullable=True),
    sa.Column('offers_id', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['condition'], ['conditions.us_code'], ),
    sa.ForeignKeyConstraint(['merchant'], ['merchants.shortcode'], ),
    sa.ForeignKeyConstraint(['offers_id'], ['latest_offers.database_id'], ),
    sa.PrimaryKeyConstraint('databaseId'),
    sa.UniqueConstraint('databaseId')
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('latest_offers_history')
    op.drop_table('latest_offers')
    # ### end Alembic commands ###
