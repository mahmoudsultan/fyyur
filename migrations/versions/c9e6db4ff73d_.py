"""empty message

Revision ID: c9e6db4ff73d
Revises: 6bf32bc2f9da
Create Date: 2020-07-17 19:48:31.539796

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'c9e6db4ff73d'
down_revision = '6bf32bc2f9da'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('Show', sa.Column('artist_id', sa.Integer(), nullable=False))
    op.add_column('Show', sa.Column('venue_id', sa.Integer(), nullable=False))
    op.create_foreign_key(None, 'Show', 'Artist', ['artist_id'], ['id'])
    op.create_foreign_key(None, 'Show', 'Venue', ['venue_id'], ['id'])
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint(None, 'Show', type_='foreignkey')
    op.drop_constraint(None, 'Show', type_='foreignkey')
    op.drop_column('Show', 'venue_id')
    op.drop_column('Show', 'artist_id')
    # ### end Alembic commands ###
