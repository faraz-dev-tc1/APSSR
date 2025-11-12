# Testing Instructions

## Quick Test

Once you've uploaded PDFs and set up your API key:

```bash
# Run the complete test suite
python test_system.py
```

This will:
1. ✅ Verify all dependencies are installed
2. ✅ Check for API key
3. ✅ Find PDF files in data/input/
4. ✅ Test each module individually
5. ✅ Run the complete pipeline
6. ✅ Generate all outputs
7. ✅ Show summary report

## Expected Output

```
================================================================================
TESTING AUTOMATED RULEBOOK CONSOLIDATION SYSTEM
================================================================================

✓ Google API key found
✓ Found 1 PDF file(s):
  - rulebook_1996.pdf

TEST 1: Module 1 - Document Preprocessor
✓ Extracted 150 pages
✓ Extracted 3500 text lines
✓ Document type: mixed_document

TEST 2: Module 2 - Logical Unit Reconstructor (Gemini AI)
✓ Reconstructed 45 rules
✓ Reconstructed 23 Government Orders

...

🎉 ALL TESTS PASSED! System is working correctly.
```

## What Gets Generated

After testing, you'll find:

```
data/output/
├── test_run/
│   ├── consolidated_rulebook.json    # Structured data
│   ├── consolidated_rulebook.html    # Human-readable
│   └── audit_report.json             # Validation metrics
└── full_test/
    └── (same files from full pipeline run)
```

## Manual Testing (Step by Step)

If you want to test modules individually:

```bash
# Test Module 1 only
python -m src.modules.module1_preprocessor.preprocessor data/input/your_file.pdf

# Test Module 2 only
python -m src.modules.module2_reconstructor.reconstructor data/input/your_file.pdf

# Test full pipeline
python main.py data/input/your_file.pdf --output data/output/manual_test
```

## Troubleshooting

### "GOOGLE_API_KEY not set"
Edit `.env` and add your key:
```
GOOGLE_API_KEY=your_actual_key_here
```

### "No PDF files found"
Upload PDFs to `data/input/` directory

### "Module import error"
Run from project root: `python test_system.py`

### Gemini API errors
- Check API key is valid
- Ensure you have API quota
- Try with smaller PDF first
