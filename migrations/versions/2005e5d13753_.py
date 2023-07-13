"""empty message

Revision ID: 2005e5d13753
Revises: 2ee02c39dd7d
Create Date: 2021-08-22 11:15:52.360087

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '2005e5d13753'
down_revision = '2ee02c39dd7d'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('offers_active',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('scryfall_card_id', sa.String(), nullable=True),
    sa.Column('item_index', sa.String(), nullable=True),
    sa.Column('last_updated', sa.Date(), nullable=True),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('id'),
    sa.UniqueConstraint('item_index'),
    sa.UniqueConstraint('scryfall_card_id')
    )
    op.create_table('cards',
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
    op.drop_table('offers')
    op.drop_table('items')
    op.add_column('offers_history', sa.Column('offers_active_id', sa.Integer(), nullable=False))
    op.drop_constraint('offers_history_offers_id_fkey', 'offers_history', type_='foreignkey')
    op.create_foreign_key(None, 'offers_history', 'offers_active', ['offers_active_id'], ['id'])
    op.drop_column('offers_history', 'offers_id')
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('offers_history', sa.Column('offers_id', sa.INTEGER(), autoincrement=False, nullable=False))
    op.drop_constraint(None, 'offers_history', type_='foreignkey')
    op.create_foreign_key('offers_history_offers_id_fkey', 'offers_history', 'offers', ['offers_id'], ['id'])
    op.drop_column('offers_history', 'offers_active_id')
    op.create_table('items',
    sa.Column('id', sa.INTEGER(), autoincrement=True, nullable=False),
    sa.Column('oracle_id', sa.VARCHAR(), autoincrement=False, nullable=True),
    sa.Column('multiverse_ids', sa.VARCHAR(), autoincrement=False, nullable=True),
    sa.Column('mtgo_id', sa.VARCHAR(), autoincrement=False, nullable=True),
    sa.Column('produced_mana', sa.VARCHAR(), autoincrement=False, nullable=True),
    sa.Column('mtgo_foil_id', sa.VARCHAR(), autoincrement=False, nullable=True),
    sa.Column('scryfall_card_id', sa.VARCHAR(), autoincrement=False, nullable=True),
    sa.Column('legalities', sa.VARCHAR(), autoincrement=False, nullable=True),
    sa.Column('full_art', sa.BOOLEAN(), autoincrement=False, nullable=True),
    sa.Column('textless', sa.BOOLEAN(), autoincrement=False, nullable=True),
    sa.Column('loyalty', sa.VARCHAR(), autoincrement=False, nullable=True),
    sa.Column('oversized', sa.BOOLEAN(), autoincrement=False, nullable=True),
    sa.Column('card_back_id', sa.VARCHAR(), autoincrement=False, nullable=True),
    sa.Column('games', sa.VARCHAR(), autoincrement=False, nullable=True),
    sa.Column('lang', sa.VARCHAR(), autoincrement=False, nullable=True),
    sa.Column('name', sa.VARCHAR(), autoincrement=False, nullable=True),
    sa.Column('uri', sa.VARCHAR(), autoincrement=False, nullable=True),
    sa.Column('rarity', sa.VARCHAR(), autoincrement=False, nullable=True),
    sa.Column('variation', sa.VARCHAR(), autoincrement=False, nullable=True),
    sa.Column('variation_of', sa.VARCHAR(), autoincrement=False, nullable=True),
    sa.Column('layout', sa.VARCHAR(), autoincrement=False, nullable=True),
    sa.Column('scryfall_uri', sa.VARCHAR(), autoincrement=False, nullable=True),
    sa.Column('cmc', postgresql.DOUBLE_PRECISION(precision=53), autoincrement=False, nullable=True),
    sa.Column('cardmarket_id', sa.VARCHAR(), autoincrement=False, nullable=True),
    sa.Column('tcgplayer_id', sa.VARCHAR(), autoincrement=False, nullable=True),
    sa.Column('color_identity', sa.VARCHAR(), autoincrement=False, nullable=True),
    sa.Column('colors', sa.VARCHAR(), autoincrement=False, nullable=True),
    sa.Column('keywords', sa.VARCHAR(), autoincrement=False, nullable=True),
    sa.Column('image_uris', sa.VARCHAR(), autoincrement=False, nullable=True),
    sa.Column('foil', sa.BOOLEAN(), autoincrement=False, nullable=True),
    sa.Column('nonfoil', sa.BOOLEAN(), autoincrement=False, nullable=True),
    sa.Column('etchedfoil', sa.BOOLEAN(), autoincrement=False, nullable=True),
    sa.Column('mana_cost', sa.VARCHAR(), autoincrement=False, nullable=True),
    sa.Column('oracle_text', sa.VARCHAR(), autoincrement=False, nullable=True),
    sa.Column('power', sa.VARCHAR(), autoincrement=False, nullable=True),
    sa.Column('reserved', sa.BOOLEAN(), autoincrement=False, nullable=True),
    sa.Column('toughness', sa.VARCHAR(), autoincrement=False, nullable=True),
    sa.Column('type_line', sa.VARCHAR(), autoincrement=False, nullable=True),
    sa.Column('artist', sa.VARCHAR(), autoincrement=False, nullable=True),
    sa.Column('booster', sa.VARCHAR(), autoincrement=False, nullable=True),
    sa.Column('border_color', sa.VARCHAR(), autoincrement=False, nullable=True),
    sa.Column('collector_number', sa.VARCHAR(), autoincrement=False, nullable=True),
    sa.Column('flavor_name', sa.VARCHAR(), autoincrement=False, nullable=True),
    sa.Column('flavor_text', sa.VARCHAR(), autoincrement=False, nullable=True),
    sa.Column('frame', sa.VARCHAR(), autoincrement=False, nullable=True),
    sa.Column('printed_name', sa.VARCHAR(), autoincrement=False, nullable=True),
    sa.Column('printed_text', sa.VARCHAR(), autoincrement=False, nullable=True),
    sa.Column('printed_type_line', sa.VARCHAR(), autoincrement=False, nullable=True),
    sa.Column('illustration_id', sa.VARCHAR(), autoincrement=False, nullable=True),
    sa.Column('promo', sa.BOOLEAN(), autoincrement=False, nullable=True),
    sa.Column('purchase_uris', sa.VARCHAR(), autoincrement=False, nullable=True),
    sa.Column('released_at', sa.DATE(), autoincrement=False, nullable=True),
    sa.Column('scryfall_set_uri', sa.VARCHAR(), autoincrement=False, nullable=True),
    sa.Column('set_name', sa.VARCHAR(), autoincrement=False, nullable=True),
    sa.Column('set_search_uri', sa.VARCHAR(), autoincrement=False, nullable=True),
    sa.Column('set_type', sa.VARCHAR(), autoincrement=False, nullable=True),
    sa.Column('set_uri', sa.VARCHAR(), autoincrement=False, nullable=True),
    sa.Column('set', sa.VARCHAR(), autoincrement=False, nullable=True),
    sa.Column('image_uri_small', sa.VARCHAR(), autoincrement=False, nullable=True),
    sa.Column('image_uri_normal', sa.VARCHAR(), autoincrement=False, nullable=True),
    sa.Column('image_uri_large', sa.VARCHAR(), autoincrement=False, nullable=True),
    sa.Column('image_uri_png', sa.VARCHAR(), autoincrement=False, nullable=True),
    sa.Column('item_index', sa.VARCHAR(), autoincrement=False, nullable=True),
    sa.Column('scryfall_set_id', sa.VARCHAR(), autoincrement=False, nullable=False),
    sa.ForeignKeyConstraint(['scryfall_set_id'], ['sets.scryfall_set_id'], name='items_scryfall_set_id_fkey'),
    sa.PrimaryKeyConstraint('id', name='items_pkey'),
    sa.UniqueConstraint('item_index', name='items_item_index_key')
    )
    op.create_table('offers',
    sa.Column('id', sa.INTEGER(), autoincrement=True, nullable=False),
    sa.Column('scryfall_card_id', sa.VARCHAR(), autoincrement=False, nullable=True),
    sa.Column('item_index', sa.VARCHAR(), autoincrement=False, nullable=True),
    sa.Column('last_updated', sa.DATE(), autoincrement=False, nullable=True),
    sa.PrimaryKeyConstraint('id', name='offers_pkey'),
    sa.UniqueConstraint('id', name='offers_id_key'),
    sa.UniqueConstraint('item_index', name='offers_item_index_key'),
    sa.UniqueConstraint('scryfall_card_id', name='offers_scryfall_card_id_key')
    )
    op.drop_table('cards')
    op.drop_table('offers_active')
    # ### end Alembic commands ###
