"""empty message

Revision ID: 9684df3a88ff
Revises: bf4f581da222
Create Date: 2021-08-22 15:02:06.634112

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '9684df3a88ff'
down_revision = 'bf4f581da222'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('items',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('oracle_id', sa.String(), nullable=True),
    sa.Column('multiverse_ids', sa.String(), nullable=True),
    sa.Column('mtgo_id', sa.String(), nullable=True),
    sa.Column('produced_mana', sa.String(), nullable=True),
    sa.Column('mtgo_foil_id', sa.String(), nullable=True),
    sa.Column('scryfall_card_id', sa.String(), nullable=True),
    sa.Column('legalities', sa.String(), nullable=True),
    sa.Column('full_art', sa.Boolean(), nullable=True),
    sa.Column('textless', sa.Boolean(), nullable=True),
    sa.Column('loyalty', sa.String(), nullable=True),
    sa.Column('oversized', sa.Boolean(), nullable=True),
    sa.Column('card_back_id', sa.String(), nullable=True),
    sa.Column('games', sa.String(), nullable=True),
    sa.Column('lang', sa.String(), nullable=True),
    sa.Column('name', sa.String(), nullable=True),
    sa.Column('uri', sa.String(), nullable=True),
    sa.Column('rarity', sa.String(), nullable=True),
    sa.Column('variation', sa.String(), nullable=True),
    sa.Column('variation_of', sa.String(), nullable=True),
    sa.Column('layout', sa.String(), nullable=True),
    sa.Column('scryfall_uri', sa.String(), nullable=True),
    sa.Column('cmc', sa.Float(), nullable=True),
    sa.Column('cardmarket_id', sa.String(), nullable=True),
    sa.Column('tcgplayer_id', sa.String(), nullable=True),
    sa.Column('color_identity', sa.String(), nullable=True),
    sa.Column('colors', sa.String(), nullable=True),
    sa.Column('keywords', sa.String(), nullable=True),
    sa.Column('image_uris', sa.String(), nullable=True),
    sa.Column('foil', sa.Boolean(), nullable=True),
    sa.Column('nonfoil', sa.Boolean(), nullable=True),
    sa.Column('etchedfoil', sa.Boolean(), nullable=True),
    sa.Column('mana_cost', sa.String(), nullable=True),
    sa.Column('oracle_text', sa.String(), nullable=True),
    sa.Column('power', sa.String(), nullable=True),
    sa.Column('reserved', sa.Boolean(), nullable=True),
    sa.Column('toughness', sa.String(), nullable=True),
    sa.Column('type_line', sa.String(), nullable=True),
    sa.Column('artist', sa.String(), nullable=True),
    sa.Column('booster', sa.String(), nullable=True),
    sa.Column('border_color', sa.String(), nullable=True),
    sa.Column('collector_number', sa.String(), nullable=True),
    sa.Column('flavor_name', sa.String(), nullable=True),
    sa.Column('flavor_text', sa.String(), nullable=True),
    sa.Column('frame', sa.String(), nullable=True),
    sa.Column('printed_name', sa.String(), nullable=True),
    sa.Column('printed_text', sa.String(), nullable=True),
    sa.Column('printed_type_line', sa.String(), nullable=True),
    sa.Column('illustration_id', sa.String(), nullable=True),
    sa.Column('promo', sa.Boolean(), nullable=True),
    sa.Column('purchase_uris', sa.String(), nullable=True),
    sa.Column('released_at', sa.Date(), nullable=True),
    sa.Column('scryfall_set_uri', sa.String(), nullable=True),
    sa.Column('set_name', sa.String(), nullable=True),
    sa.Column('set_search_uri', sa.String(), nullable=True),
    sa.Column('set_type', sa.String(), nullable=True),
    sa.Column('set_uri', sa.String(), nullable=True),
    sa.Column('set', sa.String(), nullable=True),
    sa.Column('image_uri_small', sa.String(), nullable=True),
    sa.Column('image_uri_normal', sa.String(), nullable=True),
    sa.Column('image_uri_large', sa.String(), nullable=True),
    sa.Column('image_uri_png', sa.String(), nullable=True),
    sa.Column('item_index', sa.String(), nullable=True),
    sa.Column('scryfall_set_id', sa.String(), nullable=False),
    sa.ForeignKeyConstraint(['scryfall_set_id'], ['sets.scryfall_set_id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('id'),
    sa.UniqueConstraint('item_index')
    )
    op.create_table('offers',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('scryfall_card_id', sa.String(), nullable=True),
    sa.Column('item_index', sa.String(), nullable=True),
    sa.Column('last_updated', sa.Date(), nullable=True),
    sa.Column('item_id', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['item_id'], ['items.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('id'),
    sa.UniqueConstraint('item_index'),
    sa.UniqueConstraint('scryfall_card_id')
    )
    op.create_table('offers_history',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('scryfall_card_id', sa.String(), nullable=True),
    sa.Column('item_index', sa.String(), nullable=True),
    sa.Column('last_updated', sa.Date(), nullable=True),
    sa.Column('source', sa.String(), nullable=True),
    sa.Column('merchant', sa.String(), nullable=True),
    sa.Column('amount', sa.Float(), nullable=True),
    sa.Column('card_type', sa.String(), nullable=True),
    sa.Column('condition', sa.String(), nullable=True),
    sa.Column('offer_id', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['offer_id'], ['offers.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('id'),
    sa.UniqueConstraint('item_index')
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('offers_history')
    op.drop_table('offers')
    op.drop_table('items')
    # ### end Alembic commands ###