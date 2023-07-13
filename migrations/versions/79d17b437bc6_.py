"""empty message

Revision ID: 79d17b437bc6
Revises: acdd305e17e2
Create Date: 2022-02-03 21:21:16.477736

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '79d17b437bc6'
down_revision = 'acdd305e17e2'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('real_items', sa.Column('last_transaction', sa.Integer(), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('real_items', 'last_transaction')
    # ### end Alembic commands ###