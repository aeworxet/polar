"""organization.billing_email

Revision ID: 366887033e1c
Revises: 4490b9736177
Create Date: 2023-05-09 09:29:13.974934

"""
from alembic import op
import sqlalchemy as sa


# Polar Custom Imports

# revision identifiers, used by Alembic.
revision = "366887033e1c"
down_revision = "4490b9736177"
branch_labels: tuple[str] | None = None
depends_on: tuple[str] | None = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column(
        "organizations",
        sa.Column("billing_email", sa.String(length=120), nullable=True),
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column("organizations", "billing_email")
    # ### end Alembic commands ###
