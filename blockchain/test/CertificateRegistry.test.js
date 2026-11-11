const { expect } = require("chai");
const { ethers } = require("hardhat");

describe("CertificateRegistry", function () {
  let registry;
  let owner;
  let other;

  beforeEach(async function () {
    [owner, other] = await ethers.getSigners();
    const CertificateRegistry = await ethers.getContractFactory("CertificateRegistry");
    registry = await CertificateRegistry.deploy();
    await registry.waitForDeployment();
  });

  it("registers a certificate", async function () {
    const certId = "CERT-1001";
    const hash = ethers.encodeBytes32String("document-hash");
    await registry.registerCertificate(certId, hash);
    expect(await registry.certificateExists(certId)).to.equal(true);
  });

  it("verifies a certificate hash", async function () {
    const certId = "CERT-1002";
    const hash = ethers.encodeBytes32String("document-hash");
    await registry.registerCertificate(certId, hash);
    expect(await registry.verifyCertificate(certId, hash)).to.equal(true);
  });

  it("revokes a certificate", async function () {
    const certId = "CERT-1003";
    const hash = ethers.encodeBytes32String("document-hash");
    await registry.registerCertificate(certId, hash);
    await registry.revokeCertificate(certId);
    expect(await registry.certificateExists(certId)).to.equal(true);
  });
});
