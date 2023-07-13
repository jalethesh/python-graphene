"""empty message

Revision ID: 4bafa4d50b9d
Revises: 2918e91c4896
Create Date: 2022-01-21 20:43:53.752165

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '4bafa4d50b9d'
down_revision = '2918e91c4896'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column('ebay_listing', 'database_id',
               existing_type=sa.VARCHAR(),
               type_=sa.Integer(),
               existing_nullable=False,
               autoincrement=True)
    op.create_unique_constraint(None, 'ebay_listing', ['database_id'])
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint(None, 'ebay_listing', type_='unique')
    op.alter_column('ebay_listing', 'database_id',
               existing_type=sa.Integer(),
               type_=sa.VARCHAR(),
               existing_nullable=False,
               autoincrement=True)
    # ### end Alembic commands ###
