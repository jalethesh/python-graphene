"""empty message

Revision ID: c3a8535e925a
Revises: a9997bd34fd9
Create Date: 2021-08-28 14:16:17.947884

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'c3a8535e925a'
down_revision = 'a9997bd34fd9'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('merchants',
    sa.Column('database_id', sa.Integer(), nullable=False),
    sa.Column('short_code', sa.String(), nullable=True),
    sa.Column('name', sa.String(), nullable=True),
    sa.PrimaryKeyConstraint('database_id'),
    sa.UniqueConstraint('database_id')
    )
    op.create_table('users',
    sa.Column('database_id', sa.Integer(), nullable=False),
    sa.Column('username', sa.String(), nullable=True),
    sa.Column('password_hash', sa.String(), nullable=True),
    sa.Column('security_role', sa.String(), nullable=True),
    sa.PrimaryKeyConstraint('database_id'),
    sa.UniqueConstraint('database_id'),
    sa.UniqueConstraint('username')
    )
    op.create_table('generic_items',
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
    op.create_table('item_collections',
    sa.Column('database_id', sa.Integer(), nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=True),
    sa.Column('name', sa.String(), nullable=True),
    sa.Column('public', sa.Boolean(), nullable=True),
    sa.Column('date_created', sa.Date(), nullable=True),
    sa.Column('date_updated', sa.Date(), nullable=True),
    sa.Column('trashed', sa.Boolean(), nullable=True),
    sa.Column('order_status', sa.String(), nullable=True),
    sa.Column('admin_approved', sa.Boolean(), nullable=True),
    sa.Column('admin_comment', sa.String(), nullable=True),
    sa.ForeignKeyConstraint(['user_id'], ['users.database_id'], ),
    sa.PrimaryKeyConstraint('database_id'),
    sa.UniqueConstraint('database_id'),
    sa.UniqueConstraint('name')
    )
    op.create_table('real_items',
    sa.Column('database_id', sa.Integer(), nullable=False),
    sa.Column('item_collections_id', sa.Integer(), nullable=True),
    sa.Column('item_id', sa.Integer(), nullable=True),
    sa.Column('sku', sa.String(), nullable=True),
    sa.Column('condition_id', sa.Integer(), nullable=True),
    sa.Column('date_created', sa.Date(), nullable=True),
    sa.Column('date_updated', sa.Date(), nullable=True),
    sa.ForeignKeyConstraint(['condition_id'], ['conditions.database_id'], ),
    sa.ForeignKeyConstraint(['item_collections_id'], ['item_collections.database_id'], ),
    sa.ForeignKeyConstraint(['item_id'], ['generic_items.id'], ),
    sa.PrimaryKeyConstraint('database_id'),
    sa.UniqueConstraint('database_id')
    )
    op.drop_table('items')
    op.add_column('conditions', sa.Column('database_id', sa.Integer(), nullable=False))
    op.drop_constraint('conditions_id_key', 'conditions', type_='unique')
    op.create_unique_constraint(None, 'conditions', ['database_id'])
    op.drop_column('conditions', 'id')
    op.drop_constraint('offers_item_id_fkey', 'offers', type_='foreignkey')
    op.create_foreign_key(None, 'offers', 'generic_items', ['item_id'], ['id'])
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint(None, 'offers', type_='foreignkey')
    op.create_foreign_key('offers_item_id_fkey', 'offers', 'items', ['item_id'], ['id'])
    op.add_column('conditions', sa.Column('id', sa.INTEGER(), autoincrement=True, nullable=False))
    op.drop_constraint(None, 'conditions', type_='unique')
    op.create_unique_constraint('conditions_id_key', 'conditions', ['id'])
    op.drop_column('conditions', 'database_id')
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
    sa.UniqueConstraint('id', name='items_id_key'),
    sa.UniqueConstraint('item_index', name='items_item_index_key')
    )
    op.drop_table('real_items')
    op.drop_table('item_collections')
    op.drop_table('generic_items')
    op.drop_table('users')
    op.drop_table('merchants')
    # ### end Alembic commands ###
