"""empty message

Revision ID: 24d10322d366
Revises: 7d9bdb5e8ce0
Create Date: 2021-09-11 13:33:28.188439

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '24d10322d366'
down_revision = '7d9bdb5e8ce0'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('merchants', sa.Column('city', sa.String(), nullable=True))
    op.add_column('merchants', sa.Column('state', sa.String(), nullable=True))
    op.add_column('merchants', sa.Column('country', sa.String(), nullable=True))
    op.add_column('merchants', sa.Column('date_created', sa.Date(), nullable=True))
    op.drop_column('merchants', 'location')
    op.drop_column('merchants', 'last_updated')
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('merchants', sa.Column('last_updated', sa.DATE(), autoincrement=False, nullable=True))
    op.add_column('merchants', sa.Column('location', sa.VARCHAR(), autoincrement=False, nullable=True))
    op.drop_column('merchants', 'date_created')
    op.drop_column('merchants', 'country')
    op.drop_column('merchants', 'state')
    op.drop_column('merchants', 'city')
    # ### end Alembic commands ###