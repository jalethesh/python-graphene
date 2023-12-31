"""empty message

Revision ID: 9194dc67f080
Revises: 5362b84fd98f
Create Date: 2021-12-09 12:59:31.689168

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '9194dc67f080'
down_revision = '5362b84fd98f'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('real_items', 'user_list')
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('real_items', sa.Column('user_list', sa.VARCHAR(), autoincrement=False, nullable=True))
    # ### end Alembic commands ###
