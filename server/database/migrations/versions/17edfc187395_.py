"""empty message

Revision ID: 17edfc187395
Revises: 448013955f6d
Create Date: 2024-05-17 19:52:46.578414

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "17edfc187395"
down_revision: Union[str, None] = "448013955f6d"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column("service", sa.Column("api_key", sa.String(), nullable=False))
    op.drop_column("service", "api")
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column(
        "service", sa.Column("api", sa.VARCHAR(), autoincrement=False, nullable=False)
    )
    op.drop_column("service", "api_key")
    # ### end Alembic commands ###
