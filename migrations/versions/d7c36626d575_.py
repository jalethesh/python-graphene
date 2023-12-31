"""empty message

Revision ID: d7c36626d575
Revises: de6eb862bd6f
Create Date: 2021-08-20 11:43:36.396616

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'd7c36626d575'
down_revision = 'de6eb862bd6f'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column('cards', 'scryfall_set_id',
               existing_type=sa.VARCHAR(),
               nullable=False)
    op.create_foreign_key(None, 'cards', 'sets', ['scryfall_set_id'], ['scryfall_set_id'])
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint(None, 'cards', type_='foreignkey')
    op.alter_column('cards', 'scryfall_set_id',
               existing_type=sa.VARCHAR(),
               nullable=True)
    # ### end Alembic commands ###
