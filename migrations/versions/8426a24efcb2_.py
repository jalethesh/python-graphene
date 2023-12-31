"""empty message

Revision ID: 8426a24efcb2
Revises: f85bafa9e6a8
Create Date: 2021-10-19 10:39:57.109661

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '8426a24efcb2'
down_revision = 'f85bafa9e6a8'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('offers', sa.Column('condition', sa.String(), nullable=True))
    op.create_foreign_key(None, 'offers', 'conditions', ['condition'], ['us_code'])
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint(None, 'offers', type_='foreignkey')
    op.drop_column('offers', 'condition')
    # ### end Alembic commands ###
