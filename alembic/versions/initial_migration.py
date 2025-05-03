"""Initial migration

Revision ID: 5d4b3a1c4f2e
Revises:
Create Date: 2025-04-30 15:29:00

"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSON


# revision identifiers, used by Alembic.
revision = "5d4b3a1c4f2e"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # Create users table
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("username", sa.String(), nullable=False),
        sa.Column("github_id", sa.String(), nullable=True),
        sa.Column("email", sa.String(), nullable=True),
        sa.Column("avatar_url", sa.String(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.Column("installation_id", sa.Integer(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_users_github_id"), "users", ["github_id"], unique=True)
    op.create_index(op.f("ix_users_email"), "users", ["email"], unique=True)
    op.create_index(op.f("ix_users_id"), "users", ["id"], unique=False)
    op.create_index(op.f("ix_users_username"), "users", ["username"], unique=True)

    # Create readme_generations table
    op.create_table(
        "readme_generations",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("repository_name", sa.String(), nullable=False),
        sa.Column("repository_id", sa.String(), nullable=False),
        sa.Column("content", sa.Text(), nullable=True),
        sa.Column("metadata", JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.Column("version", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_readme_generations_id"), "readme_generations", ["id"], unique=False
    )

    # Create readme_sections table
    op.create_table(
        "readme_sections",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("readme_generation_id", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(), nullable=False),
        sa.Column("content", sa.Text(), nullable=True),
        sa.Column("order", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(
            ["readme_generation_id"],
            ["readme_generations.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_readme_sections_id"), "readme_sections", ["id"], unique=False
    )

    # Create user_preferences table
    op.create_table(
        "user_preferences",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("section_preferences", JSON(), nullable=True),
        sa.Column("style_preferences", JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id"),
    )
    op.create_index(
        op.f("ix_user_preferences_id"), "user_preferences", ["id"], unique=False
    )


def downgrade():
    op.drop_index(op.f("ix_user_preferences_id"), table_name="user_preferences")
    op.drop_table("user_preferences")
    op.drop_index(op.f("ix_readme_sections_id"), table_name="readme_sections")
    op.drop_table("readme_sections")
    op.drop_index(op.f("ix_readme_generations_id"), table_name="readme_generations")
    op.drop_table("readme_generations")
    op.drop_index(op.f("ix_users_username"), table_name="users")
    op.drop_index(op.f("ix_users_id"), table_name="users")
    op.drop_index(op.f("ix_users_email"), table_name="users")
    op.drop_index(op.f("ix_users_github_id"), table_name="users")
    op.drop_table("users")
