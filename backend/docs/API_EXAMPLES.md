# API Usage Examples

## Contract Review (File Upload)

### Using cURL

```bash
# Review a PDF contract
curl -X POST "http://localhost:8000/api/review" \
  -F "file=@employment_contract.pdf" \
  -F "contract_type=employment"

# Review a DOCX contract
curl -X POST "http://localhost:8000/api/review" \
  -F "file=@vendor_agreement.docx" \
  -F "contract_type=vendor"

# Review a scanned contract (image)
curl -X POST "http://localhost:8000/api/review" \
  -F "file=@scanned_contract.jpg" \
  -F "contract_type=employment"
```

### Using Python requests

```python
import requests

# Review a contract
with open("contract.pdf", "rb") as f:
    response = requests.post(
        "http://localhost:8000/api/review",
        files={"file": f},
        data={"contract_type": "employment"}
    )

result = response.json()
print(f"Safety Score: {result['safety_score']}/100")
print(f"Total Findings: {result['total_findings']}")

# Critical issues
for issue in result['critical_points']:
    print(f"⚠️ CRITICAL: {issue['advice']}")
    if issue['quote']:
        print(f"   Quote: {issue['quote']}")
```

### Using JavaScript fetch

```javascript
const formData = new FormData();
formData.append('file', fileInput.files[0]);
formData.append('contract_type', 'employment');

const response = await fetch('http://localhost:8000/api/review', {
    method: 'POST',
    body: formData
});

const result = await response.json();
console.log('Safety Score:', result.safety_score);
console.log('Critical Issues:', result.critical_points.length);
```

---

## Export Review Results

### Export as Word Redline

```bash
# Get review ID from review response
REVIEW_ID="rev_abc123"

# Export as Word document
curl -X POST "http://localhost:8000/api/reviews/${REVIEW_ID}/export/docx" \
  --output "${REVIEW_ID}_redline.docx"
```

### Export as PDF Report

```bash
# Export as PDF summary
curl -X POST "http://localhost:8000/api/reviews/${REVIEW_ID}/export/pdf" \
  --output "${REVIEW_ID}_report.pdf"
```

---

## Upload Legal Documents (for RAG)

```bash
# Upload Indian Labour Law PDFs for context
curl -X POST "http://localhost:8000/api/legal-docs/upload" \
  -F "file=@Industrial_Disputes_Act.pdf" \
  -F "namespace=labour_law"

# Upload company policies (DOCX)
curl -X POST "http://localhost:8000/api/legal-docs/upload" \
  -F "file=@HR_Policy.docx" \
  -F "namespace=company_policies"

# Upload scanned legal documents (images)
curl -X POST "http://localhost:8000/api/legal-docs/upload" \
  -F "file=@legal_notice.png" \
  -F "namespace=legal_notices"
```

---

## Complete Workflow Example

```python
import requests
import time

# 1. Upload legal reference documents
print("Uploading legal documents...")
with open("labour_law.pdf", "rb") as f:
    upload_response = requests.post(
        "http://localhost:8000/api/legal-docs/upload",
        files={"file": f},
        data={"namespace": "labour_law"}
    )
print(f"✅ Uploaded {upload_response.json()['chunks_uploaded']} chunks")

# Give time for vectorization
time.sleep(2)

# 2. Review a contract
print("\nReviewing contract...")
with open("employment_contract.pdf", "rb") as f:
    review_response = requests.post(
        "http://localhost:8000/api/review",
        files={"file": f},
        data={"contract_type": "employment"}
    )

review = review_response.json()
review_id = review['review_id']

print(f"\n📊 Review Results:")
print(f"   Review ID: {review_id}")
print(f"   Safety Score: {review['safety_score']}/100")
print(f"   Total Findings: {review['total_findings']}")
print(f"   - Critical: {len(review['critical_points'])}")
print(f"   - Missing: {len(review['missing_points'])}")
print(f"   - Negotiable: {len(review['negotiable_points'])}")
print(f"   - Good: {len(review['good_points'])}")

# 3. Export as Word redline
print("\nExporting Word redline...")
word_response = requests.post(
    f"http://localhost:8000/api/reviews/{review_id}/export/docx"
)
with open(f"{review_id}_redline.docx", "wb") as f:
    f.write(word_response.content)
print(f"✅ Saved {review_id}_redline.docx")

# 4. Export as PDF report
print("Exporting PDF report...")
pdf_response = requests.post(
    f"http://localhost:8000/api/reviews/{review_id}/export/pdf"
)
with open(f"{review_id}_report.pdf", "wb") as f:
    f.write(pdf_response.content)
print(f"✅ Saved {review_id}_report.pdf")

# 5. Submit feedback (RLHF)
print("\nSubmitting feedback...")
feedback_response = requests.post(
    "http://localhost:8000/api/feedback",
    json={
        "review_id": review_id,
        "point_index": 0,
        "point_category": "CRITICAL",
        "action": "accepted",
        "user_comment": "Valid concern about termination clause"
    }
)
print(f"✅ Feedback: {feedback_response.json()['message']}")
```

---

## Response Format Example

```json
{
  "review_id": "rev_abc123",
  "safety_score": 65,
  "critical_points": [
    {
      "category": "CRITICAL",
      "quote": "Employer may terminate without notice during probation",
      "advice": "This violates Indian labour law. Minimum 30-day notice required even during probation per Industrial Disputes Act.",
      "agent_source": "skeptic",
      "confidence": 1.0,
      "legal_reference": "[Industrial Disputes Act 1947] Section 25F requires notice or payment in lieu"
    }
  ],
  "missing_points": [
    {
      "category": "MISSING",
      "quote": null,
      "advice": "Contract doesn't mention Provident Fund (PF). PF is mandatory for companies with 20+ employees per EPF Act 1952.",
      "agent_source": "strategist",
      "confidence": 0.95,
      "legal_reference": "[Employees' Provident Funds Act 1952] Applicability to establishments"
    }
  ],
  "negotiable_points": [ /* ... */ ],
  "good_points": [ /* ... */ ],
  "total_findings": 12,
  "created_at": "2024-01-10T12:30:00Z"
}
```

---

## Supported File Formats

| Format | Extension | Notes |
|--------|-----------|-------|
| PDF | `.pdf` | With page number tracking |
| Word | `.docx` | Heading detection enabled |
| Images | `.png`, `.jpg`, `.jpeg` | Gemini Vision OCR |
| TIFF | `.tif`, `.tiff` | Gemini Vision OCR |
| BMP | `.bmp` | Gemini Vision OCR |
| WebP | `.webp` | Gemini Vision OCR |

---

## Error Handling

```python
try:
    with open("contract.pdf", "rb") as f:
        response = requests.post(
            "http://localhost:8000/api/review",
            files={"file": f},
            data={"contract_type": "employment"}
        )
    response.raise_for_status()
    result = response.json()
    
except requests.exceptions.HTTPError as e:
    if e.response.status_code == 400:
        print(f"Bad Request: {e.response.json()['detail']}")
        # File type not supported or text extraction failed
    elif e.response.status_code == 500:
        print(f"Server Error: {e.response.json()['detail']}")
        # Internal error during processing
    else:
        print(f"HTTP Error: {e}")
        
except FileNotFoundError:
    print("Contract file not found")
    
except Exception as e:
    print(f"Unexpected error: {e}")
```
