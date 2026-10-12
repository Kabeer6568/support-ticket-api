"""Backfill missing user roles and constrain valid values.

Revision ID: 0002_normalize_user_roles
Revises: 0001_initial_schema
"""
from alembic import op
import sqlalchemy as sa

revision = "0002_normalize_user_roles"
down_revision = "0001_initial_schema"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        "UPDATE users SET role = 'user' "
        "WHERE role IS NULL OR trim(role) = ''"
    )
    with op.batch_alter_table("users") as batch_op:
        batch_op.alter_column(
            "role",
            existing_type=sa.String(length=20),
            nullable=False,
            server_default=sa.text("'user'"),
        )
        batch_op.create_check_constraint(
            "ck_users_role_valid",
            "role IN ('user', 'support_agent', 'admin')",
        )


def downgrade() -> None:
    with op.batch_alter_table("users") as batch_op:
        batch_op.drop_constraint("ck_users_role_valid", type_="check")
        batch_op.alter_column(
            "role",
            existing_type=sa.String(length=20),
            nullable=True,
            server_default=None,
        )
