"""empty message

Revision ID: 13a102a2f756
Revises: cc474ea32333
Create Date: 2021-11-04 12:20:53.457722

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '13a102a2f756'
down_revision = 'cc474ea32333'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column('trades', 'half_closed_side',
               existing_type=sa.BOOLEAN(),
               type_=sa.String(),
               existing_nullable=True)
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column('trades', 'half_closed_side',
               existing_type=sa.String(),
               type_=sa.BOOLEAN(),
               existing_nullable=True)
    # ### end Alembic commands ###
