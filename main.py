#!/usr/bin/env python3
"""
Main entry point for Automated Rulebook Consolidation System
"""
import argparse
import sys
from pathlib import Path

from src.pipeline import RulebookConsolidationPipeline
from src.utils.logger import get_logger


logger = get_logger("main")


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Automated Rulebook Consolidation System",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Process a single PDF
  python main.py input.pdf

  # Process with reference document for validation
  python main.py input.pdf --reference reference.pdf

  # Specify output directory
  python main.py input.pdf --output ./output

  # Process with all options
  python main.py input.pdf --reference ref.pdf --output ./results
        """
    )

    parser.add_argument(
        'input_pdf',
        type=str,
        help='Path to input PDF file containing rulebook and amendments'
    )

    parser.add_argument(
        '--reference',
        '-r',
        type=str,
        help='Path to reference consolidated PDF for validation',
        default=None
    )

    parser.add_argument(
        '--output',
        '-o',
        type=str,
        help='Output directory for results (default: data/output)',
        default='data/output'
    )

    parser.add_argument(
        '--version',
        '-v',
        action='version',
        version='Rulebook Consolidation System v1.0.0'
    )

    args = parser.parse_args()

    # Validate input file
    input_path = Path(args.input_pdf)
    if not input_path.exists():
        logger.error(f"Input file not found: {args.input_pdf}")
        sys.exit(1)

    # Validate reference file if provided
    if args.reference:
        ref_path = Path(args.reference)
        if not ref_path.exists():
            logger.error(f"Reference file not found: {args.reference}")
            sys.exit(1)

    # Create output directory
    output_path = Path(args.output)
    output_path.mkdir(parents=True, exist_ok=True)

    try:
        # Initialize pipeline
        logger.info("Initializing Rulebook Consolidation Pipeline...")
        pipeline = RulebookConsolidationPipeline()

        # Process
        if args.reference:
            logger.info("Processing with reference document...")
            results = pipeline.process_with_reference(
                str(input_path),
                args.reference,
                str(output_path)
            )
        else:
            logger.info("Processing without reference document...")
            results = pipeline.process(
                str(input_path),
                str(output_path)
            )

        # Display results
        print("\n" + "=" * 80)
        print("PROCESSING COMPLETE")
        print("=" * 80)

        if results['status'] == 'completed':
            print(f"\n✓ Status: SUCCESS")
            print(f"✓ Duration: {results.get('duration_seconds', 0):.2f} seconds")

            if 'validation_passed' in results:
                validation_icon = "✓" if results['validation_passed'] else "✗"
                validation_text = "PASSED" if results['validation_passed'] else "FAILED"
                print(f"{validation_icon} Validation: {validation_text}")

            print("\nOutput Files:")
            for file_type, file_path in results.get('output_files', {}).items():
                print(f"  • {file_type}: {file_path}")

            print("\nStage Summary:")
            for stage_name, stage_data in results.get('stages', {}).items():
                icon = "✓" if stage_data.get('status') == 'completed' else "✗"
                print(f"  {icon} {stage_name.replace('_', ' ').title()}")

            sys.exit(0)
        else:
            print(f"\n✗ Status: FAILED")
            print(f"✗ Error: {results.get('error', 'Unknown error')}")
            sys.exit(1)

    except KeyboardInterrupt:
        logger.info("\nProcessing interrupted by user")
        sys.exit(130)
    except Exception as e:
        logger.error(f"Fatal error: {str(e)}", exc_info=True)
        print(f"\n✗ Fatal Error: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
