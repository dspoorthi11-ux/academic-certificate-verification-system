import os
import re
from io import BytesIO
from pathlib import Path
from typing import Any

from PIL import Image


class FraudDetectionService:
    def __init__(self, model_path: str | None = None) -> None:
        self.model_path = Path(model_path or os.getenv("AI_MODEL_PATH", "./ai-service/models"))
        self.model_path.mkdir(parents=True, exist_ok=True)

    def analyze_document(
        self,
        document_hash: str,
        text: str | None = None,
        metadata: dict[str, Any] | None = None,
        document_bytes: bytes | None = None,
        mime_type: str | None = None,
    ) -> dict[str, Any]:
        metadata = metadata or {}
        if not document_bytes:
            return {
                "analysis_status": "NOT_ASSESSED",
                "authenticity_score": None,
                "fraud_probability": None,
                "risk_level": "NOT_ASSESSED",
                "detected_anomalies": ["No certificate file was uploaded; document analysis was not run"],
                "extracted_text": "",
                "explanation": "Document parsing, OCR, metadata, and layout checks require an uploaded file. AI analysis cannot authenticate a certificate.",
                "recommended_action": "Upload the document; rely on approved issuer and hash matching for the authenticity decision.",
            }

        anomalies: list[str] = []
        score = 100.0
        extracted_text = text or ""
        analysis_status = "COMPLETED"
        detected_mime = self._detect_mime(document_bytes)
        if detected_mime is None:
            anomalies.append("File signature is not recognized as a PDF, JPEG, or PNG")
            score -= 35
        elif mime_type and detected_mime != mime_type:
            anomalies.append("Declared file type does not match the file signature")
            score -= 25

        if len(document_hash) != 64 or not re.fullmatch(r"[a-fA-F0-9]{64}", document_hash):
            anomalies.append("Document hash is missing or is not a SHA-256 digest")
            score -= 20

        if detected_mime == "application/pdf":
            extracted_text, pdf_anomalies, pdf_score, partial = self._analyze_pdf(document_bytes)
            anomalies.extend(pdf_anomalies)
            score -= pdf_score
            if partial:
                analysis_status = "PARTIAL"
        elif detected_mime in {"image/jpeg", "image/png"}:
            extracted_text, image_anomalies, image_score, partial = self._analyze_image(document_bytes)
            anomalies.extend(image_anomalies)
            score -= image_score
            if partial:
                analysis_status = "PARTIAL"

        expected_issuer = str(metadata.get("expected_issuer") or "").strip()
        if not expected_issuer:
            anomalies.append("Approved issuer metadata was unavailable to the risk analysis")
            score -= 5
        elif extracted_text and expected_issuer.casefold() not in extracted_text.casefold():
            anomalies.append("Extracted text did not contain the expected issuer name")
            score -= 10

        if len(extracted_text.strip()) < 30:
            anomalies.append("Extracted text is sparse or unavailable; manual review may be required")
            score -= 8

        score = max(0.0, min(100.0, score))
        fraud_probability = round((100.0 - score) / 100.0, 3)
        risk = self._risk_category(fraud_probability)
        if not anomalies:
            anomalies.append("No material heuristic anomalies detected; issuer and hash checks remain authoritative")

        return {
            "analysis_status": analysis_status,
            "authenticity_score": round(score, 2),
            "fraud_probability": fraud_probability,
            "risk_level": risk,
            "detected_anomalies": anomalies,
            "extracted_text": extracted_text,
            "explanation": "Deterministic baseline heuristics using file signatures, text extraction/OCR availability, issuer-name consistency, and basic document structure. This is not a trained forensic model and does not determine authenticity.",
            "recommended_action": "Manual issuer review" if risk in {"HIGH", "CRITICAL"} else "Use issuer confirmation and document hash comparison; AI cues are supporting evidence only",
        }

    @staticmethod
    def _detect_mime(content: bytes) -> str | None:
        if content.startswith(b"%PDF-"):
            return "application/pdf"
        if content.startswith(b"\xff\xd8\xff"):
            return "image/jpeg"
        if content.startswith(b"\x89PNG\r\n\x1a\n"):
            return "image/png"
        return None

    @staticmethod
    def _risk_category(fraud_probability: float) -> str:
        if fraud_probability > 0.7:
            return "CRITICAL"
        if fraud_probability > 0.45:
            return "HIGH"
        if fraud_probability > 0.2:
            return "MEDIUM"
        return "LOW"

    @staticmethod
    def _analyze_pdf(content: bytes) -> tuple[str, list[str], float, bool]:
        anomalies: list[str] = []
        try:
            from pypdf import PdfReader

            reader = PdfReader(BytesIO(content), strict=False)
            if len(reader.pages) == 0:
                return "", ["PDF contains no pages"], 30.0, False
            if len(reader.pages) > 50:
                anomalies.append("PDF page count is unusually high")
                score_penalty = 8.0
            else:
                score_penalty = 0.0
            page_text = [page.extract_text() or "" for page in reader.pages]
            text = "\n".join(page_text)
            sizes = {
                (round(float(page.mediabox.width)), round(float(page.mediabox.height)))
                for page in reader.pages
            }
            if len(sizes) > 2:
                anomalies.append("PDF pages use multiple inconsistent page dimensions")
                score_penalty += 6.0
            metadata = reader.metadata
            if metadata and metadata.creation_date and metadata.modification_date:
                if metadata.modification_date < metadata.creation_date:
                    anomalies.append("PDF modification metadata predates creation metadata")
                    score_penalty += 8.0
            partial = not text.strip()
            if partial:
                anomalies.append("No selectable PDF text was found; OCR was not available for embedded scans")
            return text, anomalies, score_penalty, partial
        except Exception:
            return "", ["PDF structure could not be parsed safely"], 25.0, True

    @staticmethod
    def _analyze_image(content: bytes) -> tuple[str, list[str], float, bool]:
        anomalies: list[str] = []
        try:
            image = Image.open(BytesIO(content))
            image.verify()
            image = Image.open(BytesIO(content))
            width, height = image.size
            if width < 400 or height < 250:
                anomalies.append("Image resolution may be insufficient for reliable credential review")
                score_penalty = 8.0
            else:
                score_penalty = 0.0
            try:
                import pytesseract

                tesseract_path = os.getenv("TESSERACT_PATH")
                if tesseract_path:
                    pytesseract.pytesseract.tesseract_cmd = tesseract_path
                text = pytesseract.image_to_string(image, timeout=5)
                return text, anomalies, score_penalty, not text.strip()
            except Exception:
                anomalies.append("OCR engine unavailable; image text was not extracted")
                return "", anomalies, score_penalty, True
        except Exception:
            return "", ["Image structure could not be decoded safely"], 25.0, True


def get_fraud_service() -> FraudDetectionService:
    return FraudDetectionService()
