"""empty message

Revision ID: bf61ace8de7e
Revises: 9d53704d1f14
Create Date: 2021-12-06 14:16:33.200353

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'bf61ace8de7e'
down_revision = '9d53704d1f14'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('users', sa.Column('address_line_one', sa.String(), nullable=True))
    op.add_column('users', sa.Column('address_line_two', sa.String(), nullable=True))
    op.add_column('users', sa.Column('address_state', sa.String(), nullable=True))
    op.add_column('users', sa.Column('address_city', sa.String(), nullable=True))
    op.add_column('users', sa.Column('address_country', sa.String(), nullable=True))
    op.add_column('users', sa.Column('address_zipcode', sa.String(), nullable=True))
    op.add_column('users', sa.Column('phone_number', sa.String(), nullable=True))
    op.add_column('users', sa.Column('real_name', sa.String(), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('users', 'real_name')
    op.drop_column('users', 'phone_number')
    op.drop_column('users', 'address_zipcode')
    op.drop_column('users', 'address_country')
    op.drop_column('users', 'address_city')
    op.drop_column('users', 'address_state')
    op.drop_column('users', 'address_line_two')
    op.drop_column('users', 'address_line_one')
    # ### end Alembic commands ###
