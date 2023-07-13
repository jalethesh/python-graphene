"""empty message

Revision ID: 9c6e590ac645
Revises: 5faf63e4c192
Create Date: 2021-10-28 15:34:38.537051

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '9c6e590ac645'
down_revision = '5faf63e4c192'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('notifications',
    sa.Column('database_id', sa.Integer(), nullable=False),
    sa.Column('date_created', sa.Date(), nullable=True),
    sa.Column('date_updated', sa.Date(), nullable=True),
    sa.Column('read', sa.Boolean(), nullable=True),
    sa.Column('message', sa.String(), nullable=True),
    sa.Column('user_id', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['user_id'], ['users.database_id'], ),
    sa.PrimaryKeyConstraint('database_id')
    )
    op.add_column('trades', sa.Column('left_confirm', sa.Boolean(), nullable=True))
    op.add_column('trades', sa.Column('right_confirm', sa.Boolean(), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('trades', 'right_confirm')
    op.drop_column('trades', 'left_confirm')
    op.drop_table('notifications')
    # ### end Alembic commands ###