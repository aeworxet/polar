"""organization.metadata

Revision ID: b392d94ec6bf
Revises: e3baa1506821
Create Date: 2023-06-19 14:27:19.523689

"""
from alembic import op
import sqlalchemy as sa


# Polar Custom Imports
from polar.kit.extensions.sqlalchemy import PostgresUUID

# revision identifiers, used by Alembic.
revision = 'b392d94ec6bf'
down_revision = 'e3baa1506821'
branch_labels: tuple[str] | None = None
depends_on: tuple[str] | None = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('organizations', sa.Column('bio', sa.String(), nullable=True))
    op.add_column('organizations', sa.Column('pretty_name', sa.String(), nullable=True))
    op.add_column('organizations', sa.Column('company', sa.String(), nullable=True))
    op.add_column('organizations', sa.Column('blog', sa.String(), nullable=True))
    op.add_column('organizations', sa.Column('location', sa.String(), nullable=True))
    op.add_column('organizations', sa.Column('email', sa.String(), nullable=True))
    op.add_column('organizations', sa.Column('twitter_username', sa.String(), nullable=True))
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('organizations', 'twitter_username')
    op.drop_column('organizations', 'email')
    op.drop_column('organizations', 'location')
    op.drop_column('organizations', 'blog')
    op.drop_column('organizations', 'company')
    op.drop_column('organizations', 'pretty_name')
    op.drop_column('organizations', 'bio')
    # ### end Alembic commands ###