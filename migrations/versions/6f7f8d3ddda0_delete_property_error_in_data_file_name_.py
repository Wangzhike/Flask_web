"""delete @property error in data_file_name of Task and TaskTemp models

Revision ID: 6f7f8d3ddda0
Revises: 69dc729a366a
Create Date: 2017-06-04 14:54:26.043941

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '6f7f8d3ddda0'
down_revision = '69dc729a366a'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('taskTemps', sa.Column('data_file_name', sa.String(), nullable=True))
    op.add_column('tasks', sa.Column('data_file_name', sa.String(), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('tasks', 'data_file_name')
    op.drop_column('taskTemps', 'data_file_name')
    # ### end Alembic commands ###
