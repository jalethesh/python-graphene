"""empty message

Revision ID: 5289763224f9
Revises: 31a1968413e0
Create Date: 2022-01-24 16:43:28.985424

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '5289763224f9'
down_revision = '31a1968413e0'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('listing_feedback',
    sa.Column('database_id', sa.Integer(), nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=True),
    sa.Column('listing_id', sa.Integer(), nullable=True),
    sa.Column('user_comment', sa.String(), nullable=True),
    sa.Column('user_selected_generic_id', sa.Integer(), nullable=True),
    sa.Column('date_created', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['listing_id'], ['ebay_listing.database_id'], ),
    sa.ForeignKeyConstraint(['user_id'], ['users.database_id'], ),
    sa.ForeignKeyConstraint(['user_selected_generic_id'], ['generic_items.id'], ),
    sa.PrimaryKeyConstraint('database_id'),
    sa.UniqueConstraint('database_id')
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('listing_feedback')
    # ### end Alembic commands ###
