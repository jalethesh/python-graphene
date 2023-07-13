"""empty message

Revision ID: cc474ea32333
Revises: 9c6e590ac645
Create Date: 2021-11-03 16:32:38.097991

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'cc474ea32333'
down_revision = '9c6e590ac645'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('trades', sa.Column('left_close', sa.Boolean(), nullable=True))
    op.add_column('trades', sa.Column('right_close', sa.Boolean(), nullable=True))
    op.add_column('trades', sa.Column('half_closed_side', sa.Boolean(), nullable=True))
    op.add_column('users', sa.Column('credit', sa.Float(), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('users', 'credit')
    op.drop_column('trades', 'half_closed_side')
    op.drop_column('trades', 'right_close')
    op.drop_column('trades', 'left_close')
    # ### end Alembic commands ###
