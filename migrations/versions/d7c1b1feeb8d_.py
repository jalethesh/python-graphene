"""empty message

Revision ID: d7c1b1feeb8d
Revises: 5e07c88263dd
Create Date: 2021-09-25 08:39:48.274717

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'd7c1b1feeb8d'
down_revision = '5e07c88263dd'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('real_item_defects',
    sa.Column('database_id', sa.Integer(), nullable=False),
    sa.Column('defect_name', sa.Boolean(), nullable=True),
    sa.Column('realitem_id', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['realitem_id'], ['real_items.database_id'], ),
    sa.PrimaryKeyConstraint('database_id'),
    sa.UniqueConstraint('database_id')
    )
    op.drop_column('real_items', 'defect_roller_lines')
    op.drop_column('real_items', 'defect_bend')
    op.drop_column('real_items', 'defect_scratched')
    op.drop_column('real_items', 'defect_clouding')
    op.drop_column('real_items', 'defect_curled')
    op.drop_column('real_items', 'defect_inked')
    op.drop_column('real_items', 'defect_signed')
    op.drop_column('real_items', 'defect_crease')
    op.drop_column('real_items', 'defect_smudges')
    op.drop_column('real_items', 'defect_dented')
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('real_items', sa.Column('defect_dented', sa.BOOLEAN(), autoincrement=False, nullable=True))
    op.add_column('real_items', sa.Column('defect_smudges', sa.BOOLEAN(), autoincrement=False, nullable=True))
    op.add_column('real_items', sa.Column('defect_crease', sa.BOOLEAN(), autoincrement=False, nullable=True))
    op.add_column('real_items', sa.Column('defect_signed', sa.BOOLEAN(), autoincrement=False, nullable=True))
    op.add_column('real_items', sa.Column('defect_inked', sa.BOOLEAN(), autoincrement=False, nullable=True))
    op.add_column('real_items', sa.Column('defect_curled', sa.BOOLEAN(), autoincrement=False, nullable=True))
    op.add_column('real_items', sa.Column('defect_clouding', sa.BOOLEAN(), autoincrement=False, nullable=True))
    op.add_column('real_items', sa.Column('defect_scratched', sa.BOOLEAN(), autoincrement=False, nullable=True))
    op.add_column('real_items', sa.Column('defect_bend', sa.BOOLEAN(), autoincrement=False, nullable=True))
    op.add_column('real_items', sa.Column('defect_roller_lines', sa.BOOLEAN(), autoincrement=False, nullable=True))
    op.drop_table('real_item_defects')
    # ### end Alembic commands ###