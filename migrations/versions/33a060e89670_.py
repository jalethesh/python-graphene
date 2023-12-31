"""empty message

Revision ID: 33a060e89670
Revises: fb10a19b7d1d
Create Date: 2021-08-20 11:54:05.435268

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '33a060e89670'
down_revision = 'fb10a19b7d1d'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('cards', 'scryfall_set_id')
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('cards', sa.Column('scryfall_set_id', sa.VARCHAR(), autoincrement=False, nullable=True))
    # ### end Alembic commands ###
