"""empty message

Revision ID: acdd305e17e2
Revises: 1f76cf92c119
Create Date: 2022-02-03 20:28:49.028364

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'acdd305e17e2'
down_revision = '1f76cf92c119'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('real_items', sa.Column('last_transaction', sa.Integer(), nullable=True))
    op.create_foreign_key(None, 'real_items', 'transactions', ['last_transaction'], ['database_id'])
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint(None, 'real_items', type_='foreignkey')
    op.drop_column('real_items', 'last_transaction')
    # ### end Alembic commands ###
