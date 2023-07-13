"""empty message

Revision ID: f7e45febf019
Revises: 1ac58a1af63f
Create Date: 2021-08-23 13:31:38.653858

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'f7e45febf019'
down_revision = '1ac58a1af63f'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column('offers', 'scryfall_card_id',
               existing_type=sa.VARCHAR(),
               type_=sa.Integer(),
               existing_nullable=True)
    op.create_foreign_key(None, 'offers', 'items', ['scryfall_card_id'], ['scryfall_card_id'])
    op.drop_column('offers', 'item_index')
    op.add_column('offers_history', sa.Column('offers_id', sa.Integer(), nullable=False))
    op.drop_constraint('offers_history_offer_fkey', 'offers_history', type_='foreignkey')
    op.create_foreign_key(None, 'offers_history', 'offers', ['offers_id'], ['id'])
    op.drop_column('offers_history', 'offer')
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('offers_history', sa.Column('offer', sa.INTEGER(), autoincrement=False, nullable=False))
    op.drop_constraint(None, 'offers_history', type_='foreignkey')
    op.create_foreign_key('offers_history_offer_fkey', 'offers_history', 'offers', ['offer'], ['id'])
    op.drop_column('offers_history', 'offers_id')
    op.add_column('offers', sa.Column('item_index', sa.VARCHAR(), autoincrement=False, nullable=True))
    op.drop_constraint(None, 'offers', type_='foreignkey')
    op.alter_column('offers', 'scryfall_card_id',
               existing_type=sa.Integer(),
               type_=sa.VARCHAR(),
               existing_nullable=True)
    # ### end Alembic commands ###
