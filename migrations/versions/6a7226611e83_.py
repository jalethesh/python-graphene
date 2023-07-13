"""empty message

Revision ID: 6a7226611e83
Revises: 69f2a2b74075
Create Date: 2022-02-11 15:17:22.671269

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '6a7226611e83'
down_revision = '69f2a2b74075'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('transaction_logs',
    sa.Column('database_id', sa.Integer(), nullable=False),
    sa.Column('transaction_id', sa.Integer(), nullable=True),
    sa.Column('date_created', sa.Date(), nullable=True),
    sa.Column('message', sa.String(), nullable=True),
    sa.ForeignKeyConstraint(['transaction_id'], ['transactions.database_id'], ),
    sa.PrimaryKeyConstraint('database_id')
    )
    op.add_column('transactions', sa.Column('web_admin_approved', sa.Boolean(), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('transactions', 'web_admin_approved')
    op.drop_table('transaction_logs')
    # ### end Alembic commands ###