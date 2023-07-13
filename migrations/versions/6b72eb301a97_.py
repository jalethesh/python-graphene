"""empty message

Revision ID: 6b72eb301a97
Revises: e374a8bd66cb
Create Date: 2021-09-09 13:31:36.931504

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '6b72eb301a97'
down_revision = 'e374a8bd66cb'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint('real_items_item_collections_id_fkey', 'real_items', type_='foreignkey')
    op.create_foreign_key(None, 'real_items', 'item_collections', ['item_collections_id'], ['database_id'], ondelete='CASCADE')
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint(None, 'real_items', type_='foreignkey')
    op.create_foreign_key('real_items_item_collections_id_fkey', 'real_items', 'item_collections', ['item_collections_id'], ['database_id'])
    # ### end Alembic commands ###