// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

contract CertificateRegistry {
    struct CertificateEntry {
        string certificateId;
        bytes32 documentHash;
        address issuer;
        uint256 timestamp;
        bool active;
        bool revoked;
    }

    mapping(string => CertificateEntry) private certificates;
    mapping(address => bool) private authorizedIssuers;
    address public immutable owner;

    event CertificateRegistered(string certificateId, bytes32 documentHash, address issuer, uint256 timestamp);
    event CertificateRevoked(string certificateId, address issuer, uint256 timestamp);
    event IssuerAuthorizationChanged(address issuer, bool authorized);

    constructor() {
        owner = msg.sender;
        authorizedIssuers[msg.sender] = true;
    }

    modifier onlyAuthorizedIssuer() {
        require(authorizedIssuers[msg.sender], "Unauthorized issuer");
        _;
    }

    modifier onlyOwner() {
        require(msg.sender == owner, "Only owner");
        _;
    }

    function addIssuer(address issuer) external onlyOwner {
        require(issuer != address(0), "Invalid issuer");
        authorizedIssuers[issuer] = true;
        emit IssuerAuthorizationChanged(issuer, true);
    }

    function removeIssuer(address issuer) external onlyOwner {
        require(issuer != owner, "Cannot remove owner");
        authorizedIssuers[issuer] = false;
        emit IssuerAuthorizationChanged(issuer, false);
    }

    function isAuthorizedIssuer(address issuer) external view returns (bool) {
        return authorizedIssuers[issuer];
    }

    function registerCertificate(string memory certificateId, bytes32 documentHash) external onlyAuthorizedIssuer {
        require(!certificates[certificateId].active, "Certificate already exists");
        certificates[certificateId] = CertificateEntry({
            certificateId: certificateId,
            documentHash: documentHash,
            issuer: msg.sender,
            timestamp: block.timestamp,
            active: true,
            revoked: false
        });
        emit CertificateRegistered(certificateId, documentHash, msg.sender, block.timestamp);
    }

    function verifyCertificate(string memory certificateId, bytes32 documentHash) external view returns (bool) {
        CertificateEntry memory cert = certificates[certificateId];
        return cert.active && !cert.revoked && cert.documentHash == documentHash;
    }

    function revokeCertificate(string memory certificateId) external onlyAuthorizedIssuer {
        CertificateEntry storage cert = certificates[certificateId];
        require(cert.active, "Certificate not found");
        require(cert.issuer == msg.sender, "Only original issuer");
        cert.revoked = true;
        cert.active = false;
        emit CertificateRevoked(certificateId, msg.sender, block.timestamp);
    }

    function certificateExists(string memory certificateId) external view returns (bool) {
        return certificates[certificateId].active || certificates[certificateId].revoked;
    }

    function getCertificate(string memory certificateId) external view returns (string memory, bytes32, address, uint256, bool, bool) {
        CertificateEntry memory cert = certificates[certificateId];
        return (cert.certificateId, cert.documentHash, cert.issuer, cert.timestamp, cert.active, cert.revoked);
    }
}
