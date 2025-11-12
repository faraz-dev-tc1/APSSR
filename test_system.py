"""
Test script for validating the Rulebook Consolidation System
Run this after uploading PDFs to test the complete pipeline
"""
import sys
import os
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.pipeline import RulebookConsolidationPipeline
from src.utils.logger import get_logger

logger = get_logger("test_pipeline")


def test_system():
    """Test the complete system with uploaded PDFs"""

    print("=" * 80)
    print("TESTING AUTOMATED RULEBOOK CONSOLIDATION SYSTEM")
    print("=" * 80)
    print()

    # Check for API key
    api_key = os.getenv('GOOGLE_API_KEY')
    if not api_key or api_key == 'your_google_api_key_here':
        print("❌ ERROR: GOOGLE_API_KEY not set!")
        print()
        print("To test the system, you need a Google API key:")
        print("1. Get a free key at: https://aistudio.google.com/app/apikey")
        print("2. Edit .env file and replace 'your_google_api_key_here' with your actual key")
        print("3. Run this test again")
        print()
        return False

    print("✓ Google API key found")
    print()

    # Check for input PDFs
    input_dir = Path("data/input")
    pdf_files = list(input_dir.glob("*.pdf"))

    if not pdf_files:
        print("❌ ERROR: No PDF files found in data/input/")
        print()
        print("Please upload PDF files to data/input/ directory")
        print()
        return False

    print(f"✓ Found {len(pdf_files)} PDF file(s):")
    for pdf in pdf_files:
        print(f"  - {pdf.name}")
    print()

    # Check for reference PDFs
    reference_dir = Path("data/reference")
    reference_files = list(reference_dir.glob("*.pdf"))

    if reference_files:
        print(f"✓ Found {len(reference_files)} reference PDF(s):")
        for pdf in reference_files:
            print(f"  - {pdf.name}")
        print()
    else:
        print("ℹ No reference PDFs found (validation will be skipped)")
        print()

    # Run tests
    print("=" * 80)
    print("RUNNING TESTS")
    print("=" * 80)
    print()

    test_results = []

    # Test 1: Module 1 - Preprocessor
    print("TEST 1: Module 1 - Document Preprocessor")
    print("-" * 80)
    try:
        from src.modules.module1_preprocessor import DocumentPreprocessor
        preprocessor = DocumentPreprocessor()

        test_pdf = pdf_files[0]
        print(f"Processing: {test_pdf.name}")

        fingerprint, pages, text_lines = preprocessor.process(str(test_pdf))

        print(f"✓ Extracted {len(pages)} pages")
        print(f"✓ Extracted {len(text_lines)} text lines")
        print(f"✓ Document type: {fingerprint.document_type.value}")

        test_results.append(("Module 1: Preprocessor", True, None))
        print()

    except Exception as e:
        print(f"❌ FAILED: {str(e)}")
        test_results.append(("Module 1: Preprocessor", False, str(e)))
        print()
        return False

    # Test 2: Module 2 - Reconstructor (uses Gemini)
    print("TEST 2: Module 2 - Logical Unit Reconstructor (Gemini AI)")
    print("-" * 80)
    try:
        from src.modules.module2_reconstructor import LogicalUnitReconstructor
        reconstructor = LogicalUnitReconstructor()

        rules, gos = reconstructor.reconstruct(text_lines)

        print(f"✓ Reconstructed {len(rules)} rules")
        print(f"✓ Reconstructed {len(gos)} Government Orders")

        test_results.append(("Module 2: Reconstructor", True, None))
        print()

    except Exception as e:
        print(f"❌ FAILED: {str(e)}")
        test_results.append(("Module 2: Reconstructor", False, str(e)))
        print()
        return False

    # Test 3: Module 3 - Segmenter
    print("TEST 3: Module 3 - Document Segmenter")
    print("-" * 80)
    try:
        from src.modules.module3_segmenter import DocumentSegmenter
        segmenter = DocumentSegmenter()

        base_rules, amendment_gos, metadata = segmenter.segment(rules, gos)

        print(f"✓ Segmented into {len(base_rules)} base rules")
        print(f"✓ Segmented into {len(amendment_gos)} amendment GOs")
        print(f"✓ Structure type: {metadata['structure']['type']}")

        test_results.append(("Module 3: Segmenter", True, None))
        print()

    except Exception as e:
        print(f"❌ FAILED: {str(e)}")
        test_results.append(("Module 3: Segmenter", False, str(e)))
        print()
        return False

    # Test 4: Module 4 - Extractor (uses Gemini)
    print("TEST 4: Module 4 - Amendment Extractor (ADK Agent)")
    print("-" * 80)
    try:
        from src.modules.module4_extractor import AmendmentExtractor
        extractor = AmendmentExtractor()

        amendments = extractor.extract(amendment_gos)

        print(f"✓ Extracted {len(amendments)} amendments")

        flagged = [a for a in amendments if a.flagged]
        if flagged:
            print(f"⚠ {len(flagged)} amendments flagged for review")

        test_results.append(("Module 4: Extractor", True, None))
        print()

    except Exception as e:
        print(f"❌ FAILED: {str(e)}")
        test_results.append(("Module 4: Extractor", False, str(e)))
        print()
        return False

    # Test 5: Module 5 - Consolidator
    print("TEST 5: Module 5 - Rulebook Consolidation Engine")
    print("-" * 80)
    try:
        from src.modules.module5_consolidator import RulebookConsolidator
        consolidator = RulebookConsolidator()

        consolidated_tree = consolidator.consolidate(base_rules, amendments)

        final_rules = consolidated_tree.get_all_rules()
        print(f"✓ Initial rules: {len(base_rules)}")
        print(f"✓ Amendments applied: {len(amendments)}")
        print(f"✓ Final rules: {len(final_rules)}")
        print(f"✓ Conflicts detected: {len(consolidator.conflicts)}")

        test_results.append(("Module 5: Consolidator", True, None))
        print()

    except Exception as e:
        print(f"❌ FAILED: {str(e)}")
        test_results.append(("Module 5: Consolidator", False, str(e)))
        print()
        return False

    # Test 6: Module 6 - Validator & Output
    print("TEST 6: Module 6 - Validator & Output Generator")
    print("-" * 80)
    try:
        from src.modules.module6_validator import RulebookValidator, OutputGenerator

        validator = RulebookValidator()
        output_generator = OutputGenerator()

        # Validate
        validation_result = validator.validate(consolidated_tree)
        print(f"✓ Validation completed")
        print(f"  Status: {'PASSED' if validation_result.passed else 'FAILED'}")

        # Generate outputs
        audit_report = validator.generate_audit_report(
            validation_result,
            consolidated_tree,
            len(amendments)
        )

        output_files = output_generator.generate_all(
            consolidated_tree,
            amendments,
            audit_report,
            "data/output/test_run"
        )

        print(f"✓ Generated {len(output_files)} output files:")
        for file_type, file_path in output_files.items():
            print(f"  - {file_type}: {file_path}")

        test_results.append(("Module 6: Validator", True, None))
        print()

    except Exception as e:
        print(f"❌ FAILED: {str(e)}")
        test_results.append(("Module 6: Validator", False, str(e)))
        print()
        return False

    # Test 7: Full Pipeline
    print("TEST 7: Complete Pipeline Integration")
    print("-" * 80)
    try:
        pipeline = RulebookConsolidationPipeline()

        # Run with reference if available
        if reference_files:
            print(f"Running with reference: {reference_files[0].name}")
            results = pipeline.process_with_reference(
                str(pdf_files[0]),
                str(reference_files[0]),
                "data/output/full_test"
            )
        else:
            print("Running without reference")
            results = pipeline.process(
                str(pdf_files[0]),
                "data/output/full_test"
            )

        if results['status'] == 'completed':
            print(f"✓ Pipeline completed successfully")
            print(f"  Duration: {results.get('duration_seconds', 0):.2f} seconds")
            if 'validation_passed' in results:
                print(f"  Validation: {'PASSED' if results['validation_passed'] else 'FAILED'}")

            test_results.append(("Full Pipeline", True, None))
        else:
            print(f"❌ Pipeline failed: {results.get('error', 'Unknown error')}")
            test_results.append(("Full Pipeline", False, results.get('error')))
            return False

        print()

    except Exception as e:
        print(f"❌ FAILED: {str(e)}")
        test_results.append(("Full Pipeline", False, str(e)))
        print()
        return False

    # Summary
    print("=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)
    print()

    passed = sum(1 for _, success, _ in test_results if success)
    total = len(test_results)

    for test_name, success, error in test_results:
        status = "✓ PASS" if success else "❌ FAIL"
        print(f"{status} - {test_name}")
        if error:
            print(f"         Error: {error}")

    print()
    print(f"Results: {passed}/{total} tests passed")
    print()

    if passed == total:
        print("🎉 ALL TESTS PASSED! System is working correctly.")
        print()
        print("Output files generated in:")
        print("  - data/output/test_run/")
        print("  - data/output/full_test/")
        print()
        return True
    else:
        print("⚠ Some tests failed. Please review the errors above.")
        print()
        return False


if __name__ == "__main__":
    success = test_system()
    sys.exit(0 if success else 1)
