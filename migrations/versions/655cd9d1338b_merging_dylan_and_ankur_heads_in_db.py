"""Merging Dylan and Ankur heads in db

Revision ID: 655cd9d1338b
Revises: 36ad6d6f61b0, 6b72eb301a97
Create Date: 2021-09-11 09:09:47.711155

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '655cd9d1338b'
down_revision = ('36ad6d6f61b0', '6b72eb301a97')
branch_labels = None
depends_on = None


def upgrade():
    pass


def downgrade():
    pass
