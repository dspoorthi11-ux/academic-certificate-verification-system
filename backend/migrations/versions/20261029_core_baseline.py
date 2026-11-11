"""Create missing core tables while preserving existing installations.

Revision ID: 20261029_core
Revises:
Create Date: 2026-10-29
"""

from alembic import op

from app.models.base import Base
from app.models import certificate, user

revision = "20261029_core"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    core_tables = [
        user.Role.__table__,
        user.User.__table__,
        user.University.__table__,
        user.Student.__table__,
        user.Verifier.__table__,
        certificate.Certificate.__table__,
        certificate.CertificateDocument.__table__,
        certificate.BlockchainRecord.__table__,
        certificate.Verification.__table__,
        certificate.AuditLog.__table__,
        certificate.FraudAnalysis.__table__,
    ]
    Base.metadata.create_all(bind=op.get_bind(), tables=core_tables, checkfirst=True)


def downgrade() -> None:
    raise RuntimeError("The core baseline is intentionally irreversible to protect existing project data")