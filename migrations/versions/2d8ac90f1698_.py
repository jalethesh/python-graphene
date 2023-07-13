"""empty message

Revision ID: 2d8ac90f1698
Revises: 1a82639c87ee
Create Date: 2021-08-23 13:22:36.114298

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '2d8ac90f1698'
down_revision = '1a82639c87ee'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column('offers_history', 'offer_id',
               existing_type=sa.INTEGER(),
               nullable=False)
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column('offers_history', 'offer_id',
               existing_type=sa.INTEGER(),
               nullable=True)
    # ### end Alembic commands ###