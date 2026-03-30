"""session expiry and activity streak state"""

from alembic import op
import sqlalchemy as sa


revision = "0004_session_expiry_and_activity_streak"
down_revision = "0003_claimed_challenges"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("users", sa.Column("last_activity_on", sa.Date(), nullable=True))
    op.add_column("session_tokens", sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True))
    op.execute("UPDATE session_tokens SET expires_at = created_at + interval '30 days' WHERE expires_at IS NULL")
    op.alter_column("session_tokens", "expires_at", nullable=False)
    op.create_index("ix_session_tokens_expires_at", "session_tokens", ["expires_at"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_session_tokens_expires_at", table_name="session_tokens")
    op.drop_column("session_tokens", "expires_at")
    op.drop_column("users", "last_activity_on")
