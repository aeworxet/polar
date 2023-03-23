"""accounts columns nullable

Revision ID: 8db2ec8b80c7
Revises: cbca2a00e6e9
Create Date: 2023-03-21 12:36:37.927246

"""
from alembic import op
import sqlalchemy as sa


# Polar Custom Imports

# revision identifiers, used by Alembic.
revision = "8db2ec8b80c7"
down_revision = "cbca2a00e6e9"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column(
        "accounts", sa.Column("account_type", sa.String(length=10), nullable=False)
    )
    op.alter_column(
        "accounts",
        "type",
        new_column_name="business_type",
        nullable=True,
    )
    op.alter_column(
        "accounts", "email", existing_type=sa.VARCHAR(length=254), nullable=True
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column(
        "accounts", "email", existing_type=sa.VARCHAR(length=254), nullable=False
    )
    op.alter_column(
        "accounts",
        "business_type",
        new_column_name="type",
        nullable=False,
    )
    op.drop_column("accounts", "account_type")
    # ### end Alembic commands ###