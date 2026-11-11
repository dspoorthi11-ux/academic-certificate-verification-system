# AI Fraud Detection

The current service is a deterministic heuristic baseline, not a trained forensic model. It accepts actual uploaded bytes and reports an explicit `NOT_ASSESSED` or `PARTIAL` state when a file or parser is unavailable.

It checks:
- PDF/JPEG/PNG file signatures and declared MIME consistency.
- PDF text extraction, page count, page dimensions, and available creation/modification metadata.
- Image decoding and basic resolution cues.
- Optional OCR through pytesseract when the Tesseract executable is installed.
- Extracted issuer-name presence and sparse/unavailable text cues.
- Hash shape and document metadata supplied by the approved issuer registry.

Outputs include a risk score, fraud-probability estimate, category, anomalies, explanation, analysis state, and recommended action. These scores are supporting review cues only; they never establish authenticity. Authentic results require an approved issuer and a server-calculated hash match against the issuer record. The heuristic score is not a calibrated probability and should not be used as an automated adverse decision.

Set `TESSERACT_PATH` to the OCR executable where it is not on `PATH`. If unavailable, the response explicitly notes that OCR did not run.
