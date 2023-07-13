"""empty message

Revision ID: 5362b84fd98f
Revises: a0d0eb93254e
Create Date: 2021-12-08 17:20:46.357524

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '5362b84fd98f'
down_revision = 'a0d0eb93254e'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('user_lists',
    sa.Column('database_id', sa.Integer(), nullable=False),
    sa.Column('date_created', sa.Date(), nullable=True),
    sa.Column('date_updated', sa.Date(), nullable=True),
    sa.Column('name', sa.String(), nullable=True),
    sa.Column('owner', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['owner'], ['users.database_id'], ),
    sa.PrimaryKeyConstraint('database_id')
    )
    op.create_table('user_list_items',
    sa.Column('database_id', sa.Integer(), nullable=False),
    sa.Column('real_item_id', sa.Integer(), nullable=True),
    sa.Column('user_list_id', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['real_item_id'], ['real_items.database_id'], ),
    sa.ForeignKeyConstraint(['user_list_id'], ['user_lists.database_id'], ),
    sa.PrimaryKeyConstraint('database_id')
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('user_list_items')
    op.drop_table('user_lists')
    # ### end Alembic commands ###
