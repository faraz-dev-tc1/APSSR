"""
Main Pipeline Orchestrator
Coordinates all modules to process rulebooks
"""
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime

from src.modules.module1_preprocessor import DocumentPreprocessor
from src.modules.module2_reconstructor import LogicalUnitReconstructor
from src.modules.module3_segmenter import DocumentSegmenter
from src.modules.module4_extractor import AmendmentExtractor
from src.modules.module5_consolidator import RulebookConsolidator
from src.modules.module6_validator import RulebookValidator, OutputGenerator
from src.models.document import ProcessedDocument, Rule
from src.utils.logger import get_logger
from src.utils.config_loader import get_config


logger = get_logger("pipeline")


class RulebookConsolidationPipeline:
    """
    Main pipeline orchestrator using ADK-style multi-agent pattern
    Coordinates all six modules to process government rulebooks
    """

    def __init__(self):
        """Initialize pipeline with all modules"""
        logger.info("Initializing Rulebook Consolidation Pipeline...")

        self.config = get_config()

        # Initialize all modules
        self.preprocessor = DocumentPreprocessor()
        self.reconstructor = LogicalUnitReconstructor()
        self.segmenter = DocumentSegmenter()
        self.extractor = AmendmentExtractor()
        self.consolidator = RulebookConsolidator()
        self.validator = RulebookValidator()
        self.output_generator = OutputGenerator()

        logger.info("Pipeline initialized successfully")

    def process(
        self,
        pdf_path: str,
        output_dir: str = "data/output",
        reference_rules: Optional[list[Rule]] = None
    ) -> Dict[str, Any]:
        """
        Process a rulebook PDF through the complete pipeline

        Args:
            pdf_path: Path to PDF file
            output_dir: Output directory for results
            reference_rules: Optional reference rules for validation

        Returns:
            Dictionary containing processing results and file paths
        """
        start_time = datetime.now()
        logger.info("=" * 80)
        logger.info("STARTING RULEBOOK CONSOLIDATION PIPELINE")
        logger.info(f"Input: {pdf_path}")
        logger.info(f"Output: {output_dir}")
        logger.info("=" * 80)

        results = {
            'status': 'processing',
            'stages': {}
        }

        try:
            # Stage 1: Document Preprocessing
            logger.info("\n" + "=" * 80)
            logger.info("STAGE 1: DOCUMENT PREPROCESSING")
            logger.info("=" * 80)

            fingerprint, pages, text_lines = self.preprocessor.process(pdf_path)

            results['stages']['preprocessing'] = {
                'status': 'completed',
                'pages': len(pages),
                'text_lines': len(text_lines),
                'document_type': fingerprint.document_type.value
            }

            # Stage 2: Logical Unit Reconstruction
            logger.info("\n" + "=" * 80)
            logger.info("STAGE 2: LOGICAL UNIT RECONSTRUCTION")
            logger.info("=" * 80)

            rules, gos = self.reconstructor.reconstruct(text_lines)

            results['stages']['reconstruction'] = {
                'status': 'completed',
                'rules': len(rules),
                'government_orders': len(gos)
            }

            # Stage 3: Document Segmentation
            logger.info("\n" + "=" * 80)
            logger.info("STAGE 3: DOCUMENT SEGMENTATION")
            logger.info("=" * 80)

            base_rules, amendment_gos, seg_metadata = self.segmenter.segment(rules, gos)

            results['stages']['segmentation'] = {
                'status': 'completed',
                'base_rules': len(base_rules),
                'amendment_gos': len(amendment_gos),
                'structure': seg_metadata['structure']['type']
            }

            # Stage 4: Amendment Extraction
            logger.info("\n" + "=" * 80)
            logger.info("STAGE 4: AMENDMENT EXTRACTION")
            logger.info("=" * 80)

            amendments = self.extractor.extract(amendment_gos)

            # Resolve ambiguous references
            available_rule_numbers = [rule.display_number for rule in base_rules]
            amendments = self.extractor.resolve_ambiguous_references(
                amendments,
                available_rule_numbers
            )

            # Detect conflicts
            conflicts = self.extractor.detect_conflicts(amendments)

            flagged_amendments = [a for a in amendments if a.flagged]

            results['stages']['extraction'] = {
                'status': 'completed',
                'total_amendments': len(amendments),
                'flagged_amendments': len(flagged_amendments),
                'conflicts': len(conflicts)
            }

            # Stage 5: Rulebook Consolidation
            logger.info("\n" + "=" * 80)
            logger.info("STAGE 5: RULEBOOK CONSOLIDATION")
            logger.info("=" * 80)

            consolidated_tree = self.consolidator.consolidate(base_rules, amendments)

            results['stages']['consolidation'] = {
                'status': 'completed',
                'initial_rules': len(base_rules),
                'amendments_applied': len(amendments),
                'final_rules': len(consolidated_tree.get_all_rules()),
                'conflicts': len(self.consolidator.conflicts)
            }

            # Stage 6: Validation and Output Generation
            logger.info("\n" + "=" * 80)
            logger.info("STAGE 6: VALIDATION AND OUTPUT GENERATION")
            logger.info("=" * 80)

            # Validate
            validation_result = self.validator.validate(
                consolidated_tree,
                reference_rules
            )

            # Generate audit report
            audit_report = self.validator.generate_audit_report(
                validation_result,
                consolidated_tree,
                len(amendments)
            )

            # Generate outputs
            output_files = self.output_generator.generate_all(
                consolidated_tree,
                amendments,
                audit_report,
                output_dir
            )

            results['stages']['validation_output'] = {
                'status': 'completed',
                'validation_passed': validation_result.passed,
                'output_files': output_files
            }

            # Final results
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()

            results['status'] = 'completed'
            results['validation_passed'] = validation_result.passed
            results['output_files'] = output_files
            results['duration_seconds'] = duration

            logger.info("\n" + "=" * 80)
            logger.info("PIPELINE COMPLETED SUCCESSFULLY")
            logger.info(f"Duration: {duration:.2f} seconds")
            logger.info(f"Validation: {'PASSED' if validation_result.passed else 'FAILED'}")
            logger.info("=" * 80)

            return results

        except Exception as e:
            logger.error(f"Pipeline failed: {str(e)}", exc_info=True)
            results['status'] = 'failed'
            results['error'] = str(e)
            return results

    def process_with_reference(
        self,
        pdf_path: str,
        reference_pdf_path: str,
        output_dir: str = "data/output"
    ) -> Dict[str, Any]:
        """
        Process with reference document for validation

        Args:
            pdf_path: Path to PDF to consolidate
            reference_pdf_path: Path to reference consolidated PDF
            output_dir: Output directory

        Returns:
            Processing results
        """
        logger.info("Processing with reference document for validation...")

        # Extract reference rules
        ref_fingerprint, ref_pages, ref_text_lines = self.preprocessor.process(reference_pdf_path)
        ref_rules, _ = self.reconstructor.reconstruct(ref_text_lines)

        # Process main document with reference
        return self.process(pdf_path, output_dir, ref_rules)


def main():
    """Main entry point for testing"""
    import sys

    if len(sys.argv) < 2:
        print("Usage: python pipeline.py <pdf_path> [reference_pdf_path] [output_dir]")
        sys.exit(1)

    pdf_path = sys.argv[1]
    reference_pdf_path = sys.argv[2] if len(sys.argv) > 2 else None
    output_dir = sys.argv[3] if len(sys.argv) > 3 else "data/output"

    # Initialize pipeline
    pipeline = RulebookConsolidationPipeline()

    # Process
    if reference_pdf_path:
        results = pipeline.process_with_reference(pdf_path, reference_pdf_path, output_dir)
    else:
        results = pipeline.process(pdf_path, output_dir)

    # Print summary
    print("\n" + "=" * 80)
    print("PIPELINE RESULTS")
    print("=" * 80)
    print(f"Status: {results['status']}")

    if results['status'] == 'completed':
        print(f"\nValidation: {'PASSED' if results.get('validation_passed') else 'FAILED'}")
        print(f"Duration: {results.get('duration_seconds', 0):.2f} seconds")

        print("\nStages:")
        for stage_name, stage_data in results.get('stages', {}).items():
            print(f"  {stage_name}: {stage_data.get('status', 'unknown')}")

        print("\nOutput Files:")
        for file_type, file_path in results.get('output_files', {}).items():
            print(f"  {file_type}: {file_path}")
    else:
        print(f"\nError: {results.get('error', 'Unknown error')}")


if __name__ == "__main__":
    main()
