# Security

Implemented controls:
- bcrypt password hashing and JWT authentication; missing credentials return 401.
- Role-gated institution review, issuer record creation/revocation, and admin audit access.
- Admin accounts cannot self-register; bootstrap via `BOOTSTRAP_ADMIN_EMAIL` and `BOOTSTRAP_ADMIN_PASSWORD`.
- Institution trust is not granted by registration or email-domain matching alone. Approval requires real evidence files and reviewed evidence IDs.
- Certificate bytes are hashed server-side; caller-supplied digests are not accepted as document proof.
- MIME allowlists, content-signature checks in the analysis layer, and bounded upload size.
- Ed25519 platform attestations with canonical JSON payloads; public pages validate the persisted signature.
- Private signing key path is environment-configured, excluded from source control, and production refuses to generate a missing key.
- Public checks omit student name/email fields.

Production gaps to close:
- Add distributed rate limiting, bot/abuse controls, and security monitoring before public exposure.
- Use a secret manager/HSM, key rotation runbook, and backup/recovery for signing keys.
- Add encrypted archive backups, retention/consent policies, access logging for document reads, and periodic integrity audits.
- Configure HTTPS, production CORS, PostgreSQL, secure cookie/token policy, and external institutional evidence verification.
- A platform Ed25519 seal is not a CCA-licensed DSC, PAdES signature, or trusted timestamp.

Never commit secrets, private keys, uploaded evidence, or production data.
