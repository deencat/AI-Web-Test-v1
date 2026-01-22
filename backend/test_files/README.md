# Test Files Repository

This directory contains sample files used for testing file upload functionality in the AI Web Test v1.0 system.

## Available Test Files

### 1. hkid_sample.pdf
- **Type:** PDF Document
- **Purpose:** Sample HKID (Hong Kong Identity Card) document for identity verification tests
- **Size:** ~50KB
- **Use Case:** Testing document upload flows for identity verification

### 2. passport_sample.jpg
- **Type:** JPEG Image
- **Purpose:** Sample passport photo for identity verification tests
- **Size:** ~100KB
- **Use Case:** Testing image upload flows for passport verification

### 3. address_proof.pdf
- **Type:** PDF Document
- **Purpose:** Sample address proof document (utility bill, bank statement, etc.)
- **Size:** ~75KB
- **Use Case:** Testing document upload flows for address verification

## Usage in Test Cases

Test steps can reference these files using absolute paths:

```json
{
  "action": "upload_file",
  "selector": "input[type='file']",
  "file_path": "/app/test_files/hkid_sample.pdf",
  "instruction": "Upload HKID document"
}
```

## File Path Resolution

The system supports both absolute and relative paths:
- Absolute: `/app/test_files/hkid_sample.pdf`
- Relative: `test_files/hkid_sample.pdf` (relative to backend directory)

## Adding New Test Files

To add new test files:
1. Place the file in this directory
2. Update this README with file details
3. Use descriptive filenames that indicate the file's purpose
4. Keep file sizes reasonable (<1MB recommended)

## Security Note

These are **sample/mock files only** and contain no real personal data. They are for testing purposes only and should not be used with production data.

## Supported File Types

The system supports all common file types:
- **Documents:** PDF, DOC, DOCX, TXT
- **Images:** JPG, JPEG, PNG, GIF, BMP
- **Spreadsheets:** XLS, XLSX, CSV
- **Archives:** ZIP, RAR, 7Z

## File Upload Flow

1. Test generation AI detects file upload requirement
2. Generates `upload_file` action with appropriate test file
3. Tier 1 (Playwright): Direct file input using `set_input_files()`
4. Tier 2 (Hybrid): XPath extraction + Playwright upload
5. Tier 3 (Stagehand): AI-driven upload with fallback
