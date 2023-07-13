"""empty message

Revision ID: 75e8efc46a3f
Revises: 0dacc95d1d08
Create Date: 2021-08-25 17:48:11.487364

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '75e8efc46a3f'
down_revision = '0dacc95d1d08'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('conditions', sa.Column('database_id', sa.Integer(), nullable=False))
    op.drop_constraint('conditions_id_key', 'conditions', type_='unique')
    op.create_unique_constraint(None, 'conditions', ['database_id'])
    op.drop_column('conditions', 'id')
    op.add_column('items', sa.Column('database_id', sa.Integer(), nullable=False))
    op.drop_constraint('items_id_key', 'items', type_='unique')
    op.create_unique_constraint(None, 'items', ['database_id'])
    op.drop_column('items', 'id')
    op.add_column('offers', sa.Column('database_id', sa.Integer(), nullable=False))
    op.drop_constraint('offers_id_key', 'offers', type_='unique')
    op.create_unique_constraint(None, 'offers', ['database_id'])
    op.drop_constraint('offers_item_id_fkey', 'offers', type_='foreignkey')
    op.create_foreign_key(None, 'offers', 'items', ['item_id'], ['database_id'])
    op.drop_column('offers', 'id')
    op.add_column('offers_history', sa.Column('database_id', sa.Integer(), nullable=False))
    op.drop_constraint('offers_history_id_key', 'offers_history', type_='unique')
    op.create_unique_constraint(None, 'offers_history', ['database_id'])
    op.drop_constraint('offers_history_offers_id_fkey', 'offers_history', type_='foreignkey')
    op.create_foreign_key(None, 'offers_history', 'offers', ['offers_id'], ['database_id'])
    op.drop_column('offers_history', 'id')
    op.add_column('sets', sa.Column('database_id', sa.Integer(), nullable=False))
    op.drop_constraint('sets_id_key', 'sets', type_='unique')
    op.create_unique_constraint(None, 'sets', ['database_id'])
    op.drop_column('sets', 'id')
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('sets', sa.Column('id', sa.INTEGER(), server_default=sa.text("nextval('sets_id_seq'::regclass)"), autoincrement=True, nullable=False))
    op.drop_constraint(None, 'sets', type_='unique')
    op.create_unique_constraint('sets_id_key', 'sets', ['id'])
    op.drop_column('sets', 'database_id')
    op.add_column('offers_history', sa.Column('id', sa.INTEGER(), autoincrement=True, nullable=False))
    op.drop_constraint(None, 'offers_history', type_='foreignkey')
    op.create_foreign_key('offers_history_offers_id_fkey', 'offers_history', 'offers', ['offers_id'], ['id'])
    op.drop_constraint(None, 'offers_history', type_='unique')
    op.create_unique_constraint('offers_history_id_key', 'offers_history', ['id'])
    op.drop_column('offers_history', 'database_id')
    op.add_column('offers', sa.Column('id', sa.INTEGER(), server_default=sa.text("nextval('offers_id_seq'::regclass)"), autoincrement=True, nullable=False))
    op.drop_constraint(None, 'offers', type_='foreignkey')
    op.create_foreign_key('offers_item_id_fkey', 'offers', 'items', ['item_id'], ['id'])
    op.drop_constraint(None, 'offers', type_='unique')
    op.create_unique_constraint('offers_id_key', 'offers', ['id'])
    op.drop_column('offers', 'database_id')
    op.add_column('items', sa.Column('id', sa.INTEGER(), server_default=sa.text("nextval('items_id_seq'::regclass)"), autoincrement=True, nullable=False))
    op.drop_constraint(None, 'items', type_='unique')
    op.create_unique_constraint('items_id_key', 'items', ['id'])
    op.drop_column('items', 'database_id')
    op.add_column('conditions', sa.Column('id', sa.INTEGER(), autoincrement=True, nullable=False))
    op.drop_constraint(None, 'conditions', type_='unique')
    op.create_unique_constraint('conditions_id_key', 'conditions', ['id'])
    op.drop_column('conditions', 'database_id')
    # ### end Alembic commands ###
