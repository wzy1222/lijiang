"""empty message

Revision ID: 3114752ba610
Revises: d7e9609754a3
Create Date: 2020-01-28 11:35:05.784158

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '3114752ba610'
down_revision = 'd7e9609754a3'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('user', sa.Column('user_type', sa.Integer(), nullable=False))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('user', 'user_type')
    # ### end Alembic commands ###