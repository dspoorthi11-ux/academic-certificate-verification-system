"""Add institution trust registry and verification evidence tables.

Revision ID: 20261030_trust
Revises:
Create Date: 2026-10-30
"""

from alembic import op
import sqlalchemy as sa

revision = "20261030_trust"
down_revision = "20261029_core"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "institution_registry",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("user_id", sa.String(length=36), nullable=False),
        sa.Column("university_id", sa.String(length=36), nullable=True),
        sa.Column("institution_name", sa.String(length=255), nullable=False),
        sa.Column("institution_type", sa.String(length=100), nullable=False),
        sa.Column("official_email", sa.String(length=255), nullable=False),
        sa.Column("website", sa.String(length=255), nullable=False),
        sa.Column("country", sa.String(length=120), nullable=False),
        sa.Column("state", sa.String(length=120), nullable=True),
        sa.Column("address", sa.Text(), nullable=False),
        sa.Column("accreditation", sa.Text(), nullable=False),
        sa.Column("representative_name", sa.String(length=255), nullable=False),
        sa.Column("representative_designation", sa.String(length=255), nullable=False),
        sa.Column("contact_number", sa.String(length=80), nullable=False),
        sa.Column("supporting_documents", sa.Text(), nullable=False),
        sa.Column("domain_candidate", sa.String(length=255), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("institution_public_key", sa.Text(), nullable=True),
        sa.Column("approved_by", sa.String(length=36), nullable=True),
        sa.Column("approved_at", sa.DateTime(), nullable=True),
        sa.Column("decision_notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["university_id"], ["universities.id"]),
        sa.ForeignKeyConstraint(["approved_by"], ["users.id"]),
        sa.UniqueConstraint("official_email", name="uq_institution_registry_email"),
    )
    op.create_index("ix_institution_registry_user_id", "institution_registry", ["user_id"])
    op.create_index("ix_institution_registry_status", "institution_registry", ["status"])

    op.create_table(
        "institution_verifications",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("institution_id", sa.String(length=36), nullable=False),
        sa.Column("admin_user_id", sa.String(length=36), nullable=False),
        sa.Column("previous_status", sa.String(length=32), nullable=False),
        sa.Column("new_status", sa.String(length=32), nullable=False),
        sa.Column("evidence_reviewed", sa.Text(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["institution_id"], ["institution_registry.id"]),
        sa.ForeignKeyConstraint(["admin_user_id"], ["users.id"]),
    )
    op.create_index("ix_institution_verifications_institution_id", "institution_verifications", ["institution_id"])
    op.create_index("ix_institution_verifications_institution_created", "institution_verifications", ["institution_id", "created_at"])

    op.create_table(
        "verification_attestations",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("public_id", sa.String(length=40), nullable=False),
        sa.Column("verification_id", sa.String(length=36), nullable=False),
        sa.Column("certificate_id", sa.String(length=100), nullable=False),
        sa.Column("document_hash", sa.String(length=128), nullable=False),
        sa.Column("institution_name", sa.String(length=255), nullable=False),
        sa.Column("result", sa.String(length=32), nullable=False),
        sa.Column("verified_at", sa.DateTime(), nullable=False),
        sa.Column("methodology", sa.Text(), nullable=False),
        sa.Column("issuer_confirmation_reference", sa.String(length=255), nullable=False),
        sa.Column("blockchain_reference", sa.String(length=255), nullable=True),
        sa.Column("platform_identity", sa.String(length=255), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("key_id", sa.String(length=128), nullable=False),
        sa.Column("public_key", sa.Text(), nullable=False),
        sa.Column("signature", sa.Text(), nullable=False),
        sa.Column("payload", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["verification_id"], ["verifications.id"]),
        sa.UniqueConstraint("public_id"),
        sa.UniqueConstraint("verification_id", "version", name="uq_attestation_verification_version"),
    )
    op.create_index("ix_verification_attestations_public_id", "verification_attestations", ["public_id"])
    op.create_index("ix_verification_attestations_verification_id", "verification_attestations", ["verification_id"])
    op.create_index("ix_verification_attestations_certificate_id", "verification_attestations", ["certificate_id"])

    op.create_table(
        "digital_signatures",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("attestation_id", sa.String(length=36), nullable=False),
        sa.Column("algorithm", sa.String(length=50), nullable=False),
        sa.Column("key_id", sa.String(length=128), nullable=False),
        sa.Column("public_key", sa.Text(), nullable=False),
        sa.Column("signature", sa.Text(), nullable=False),
        sa.Column("signed_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["attestation_id"], ["verification_attestations.id"]),
    )
    op.create_index("ix_digital_signatures_attestation_id", "digital_signatures", ["attestation_id"])

    op.create_table(
        "verification_archives",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("attestation_id", sa.String(length=36), nullable=False),
        sa.Column("document_hash", sa.String(length=128), nullable=False),
        sa.Column("original_document_path", sa.String(length=500), nullable=True),
        sa.Column("evidence_json", sa.Text(), nullable=False),
        sa.Column("archived_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["attestation_id"], ["verification_attestations.id"]),
        sa.UniqueConstraint("attestation_id"),
    )
    op.create_index("ix_verification_archives_document_hash", "verification_archives", ["document_hash"])

    op.create_table(
        "blockchain_transactions",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("certificate_id", sa.String(length=100), nullable=False),
        sa.Column("transaction_hash", sa.String(length=128), nullable=True),
        sa.Column("network", sa.String(length=100), nullable=False),
        sa.Column("operation", sa.String(length=50), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("details", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.UniqueConstraint("transaction_hash"),
    )
    op.create_index("ix_blockchain_transactions_certificate_id", "blockchain_transactions", ["certificate_id"])

    op.create_table(
        "verification_requests",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("certificate_id", sa.String(length=100), nullable=False),
        sa.Column("requester_id", sa.String(length=36), nullable=True),
        sa.Column("institution_id", sa.String(length=36), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("request_reference", sa.String(length=255), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["requester_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["institution_id"], ["institution_registry.id"]),
    )
    op.create_index("ix_verification_requests_certificate_id", "verification_requests", ["certificate_id"])


def downgrade() -> None:
    op.drop_index("ix_verification_requests_certificate_id", table_name="verification_requests")
    op.drop_table("verification_requests")
    op.drop_index("ix_blockchain_transactions_certificate_id", table_name="blockchain_transactions")
    op.drop_table("blockchain_transactions")
    op.drop_index("ix_verification_archives_document_hash", table_name="verification_archives")
    op.drop_table("verification_archives")
    op.drop_index("ix_digital_signatures_attestation_id", table_name="digital_signatures")
    op.drop_table("digital_signatures")
    op.drop_index("ix_verification_attestations_certificate_id", table_name="verification_attestations")
    op.drop_index("ix_verification_attestations_verification_id", table_name="verification_attestations")
    op.drop_index("ix_verification_attestations_public_id", table_name="verification_attestations")
    op.drop_table("verification_attestations")
    op.drop_index("ix_institution_verifications_institution_created", table_name="institution_verifications")
    op.drop_index("ix_institution_verifications_institution_id", table_name="institution_verifications")
    op.drop_table("institution_verifications")
    op.drop_index("ix_institution_registry_status", table_name="institution_registry")
    op.drop_index("ix_institution_registry_user_id", table_name="institution_registry")
    op.drop_table("institution_registry")