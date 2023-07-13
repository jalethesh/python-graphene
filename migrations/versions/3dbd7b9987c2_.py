"""empty message

Revision ID: 3dbd7b9987c2
Revises: 59b2f7f3e3b2
Create Date: 2021-08-22 11:22:24.615674

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '3dbd7b9987c2'
down_revision = '59b2f7f3e3b2'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('offers',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('scryfall_card_id', sa.String(), nullable=True),
    sa.Column('item_index', sa.String(), nullable=True),
    sa.Column('last_updated', sa.Date(), nullable=True),
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
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('id'),
    sa.UniqueConstraint('item_index')
    )
    op.create_unique_constraint(None, 'cards', ['id'])
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint(None, 'cards', type_='unique')
    op.drop_table('offers_history')
    op.drop_table('offers')
    # ### end Alembic commands ###