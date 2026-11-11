# Blockchain

The blockchain layer uses Hardhat and a Solidity smart contract registry. The contract is not deployed or connected to API transaction signing by default.

## Contract responsibilities
- registerCertificate
- verifyCertificate
- revokeCertificate
- certificateExists
- getCertificate
- addIssuer / removeIssuer (owner only)
- isAuthorizedIssuer
- original-issuer-only revocation

## Local dev

```bash
cd blockchain
npm install
npx hardhat test
npx hardhat node
npx hardhat run scripts/deploy.js --network localhost
```

The backend exposes RPC health and transaction lookup. Contract writes and certificate verification return `not_configured` until a deployed contract address, ABI adapter, authorized signer, and chain-specific monitoring are installed. No synthetic transaction ID or confirmation is generated. Only certificate hashes/minimal references should be published on-chain; never student PII or document files.
