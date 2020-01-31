"""empty message

Revision ID: fbcaaf02d7f7
Revises: 81e9fffaa1a7
Create Date: 2020-01-29 15:09:42.301052

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'fbcaaf02d7f7'
down_revision = '81e9fffaa1a7'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('admin_command',
    sa.Column('id', sa.BIGINT(), nullable=False),
    sa.Column('command', sa.INTEGER(), nullable=False),
    sa.Column('reason', sa.VARCHAR(length=255), nullable=False),
    sa.Column('extra', sa.TEXT(), nullable=True),
    sa.Column('create_time', sa.DATETIME(), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('admin_command')
    # ### end Alembic commands ###