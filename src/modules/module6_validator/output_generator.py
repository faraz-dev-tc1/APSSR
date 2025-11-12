"""
Module 6: Validator and Output Generator - Output generation component
"""
import json
from pathlib import Path
from typing import Dict, Any, List
from datetime import datetime

from src.modules.module5_consolidator.rule_tree import RuleTree
from src.models.document import Amendment
from src.utils.logger import get_logger
from src.utils.config_loader import get_config


logger = get_logger("output_generator")


class OutputGenerator:
    """
    Generates output in multiple formats
    """

    def __init__(self):
        """Initialize output generator"""
        self.config = get_config()
        self.output_formats = self.config.get('output.formats', ['json', 'html'])

    def generate_all(
        self,
        consolidated_tree: RuleTree,
        amendments: List[Amendment],
        audit_report: Dict[str, Any],
        output_dir: str
    ) -> Dict[str, str]:
        """
        Generate all output formats

        Args:
            consolidated_tree: Consolidated rule tree
            amendments: List of amendments
            audit_report: Audit report
            output_dir: Output directory path

        Returns:
            Dictionary mapping format -> file path
        """
        logger.info(f"Generating outputs in formats: {self.output_formats}")

        output_dir_path = Path(output_dir)
        output_dir_path.mkdir(parents=True, exist_ok=True)

        generated_files = {}

        # JSON output
        if 'json' in self.output_formats:
            json_path = self._generate_json(
                consolidated_tree,
                amendments,
                output_dir_path
            )
            generated_files['json'] = str(json_path)

        # HTML output
        if 'html' in self.output_formats:
            html_path = self._generate_html(
                consolidated_tree,
                amendments,
                output_dir_path
            )
            generated_files['html'] = str(html_path)

        # Audit report
        audit_path = self._generate_audit_report(audit_report, output_dir_path)
        generated_files['audit'] = str(audit_path)

        logger.info(f"Generated {len(generated_files)} output files")
        return generated_files

    def _generate_json(
        self,
        tree: RuleTree,
        amendments: List[Amendment],
        output_dir: Path
    ) -> Path:
        """Generate JSON output"""
        logger.info("Generating JSON output...")

        all_rules = tree.get_all_rules()

        output = {
            'metadata': {
                'generated_at': datetime.now().isoformat(),
                'total_rules': len(all_rules),
                'total_amendments': len(amendments)
            },
            'rules': [
                {
                    'uuid': rule.uuid,
                    'display_number': rule.display_number,
                    'content': rule.content,
                    'level': rule.level,
                    'amendment_history': [
                        {
                            'go_id': a.go_id,
                            'date': a.date.isoformat() if a.date else None,
                            'action': a.action.value,
                            'target_path': a.target_path
                        }
                        for a in rule.amendment_history
                    ]
                }
                for rule in all_rules
            ],
            'amendments': [
                {
                    'uuid': a.uuid,
                    'go_id': a.go_id,
                    'date': a.date.isoformat() if a.date else None,
                    'action': a.action.value,
                    'target_path': a.target_path,
                    'confidence': a.confidence,
                    'flagged': a.flagged
                }
                for a in amendments
            ]
        }

        output_path = output_dir / 'consolidated_rulebook.json'
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(output, f, indent=2, ensure_ascii=False)

        logger.info(f"JSON output saved to {output_path}")
        return output_path

    def _generate_html(
        self,
        tree: RuleTree,
        amendments: List[Amendment],
        output_dir: Path
    ) -> Path:
        """Generate HTML output with change tracking"""
        logger.info("Generating HTML output...")

        all_rules = tree.get_all_rules()

        html_content = self._build_html_document(all_rules, amendments)

        output_path = output_dir / 'consolidated_rulebook.html'
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_content)

        logger.info(f"HTML output saved to {output_path}")
        return output_path

    def _build_html_document(
        self,
        rules: List,
        amendments: List[Amendment]
    ) -> str:
        """Build HTML document"""
        html = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Consolidated Rulebook</title>
    <style>
        body {
            font-family: 'Georgia', serif;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            line-height: 1.6;
        }
        h1 {
            color: #2c3e50;
            border-bottom: 3px solid #3498db;
            padding-bottom: 10px;
        }
        .metadata {
            background: #ecf0f1;
            padding: 15px;
            border-radius: 5px;
            margin-bottom: 30px;
        }
        .rule {
            margin-bottom: 30px;
            padding: 15px;
            border-left: 4px solid #3498db;
            background: #f9f9f9;
        }
        .rule-number {
            font-weight: bold;
            font-size: 1.2em;
            color: #2c3e50;
            margin-bottom: 10px;
        }
        .rule-content {
            margin-left: 20px;
            text-align: justify;
        }
        .amendment-badge {
            display: inline-block;
            background: #e74c3c;
            color: white;
            padding: 2px 8px;
            border-radius: 3px;
            font-size: 0.8em;
            margin-left: 10px;
        }
        .amendment-history {
            margin-top: 15px;
            padding: 10px;
            background: #fff;
            border-radius: 3px;
            font-size: 0.9em;
        }
        .amendment-item {
            padding: 5px 0;
            border-bottom: 1px solid #ecf0f1;
        }
        .substituted {
            text-decoration: line-through;
            color: #e74c3c;
        }
        .inserted {
            border-bottom: 2px solid #27ae60;
            color: #27ae60;
        }
    </style>
</head>
<body>
    <h1>Consolidated Rulebook</h1>

    <div class="metadata">
        <h3>Document Information</h3>
        <p><strong>Generated:</strong> {generated_time}</p>
        <p><strong>Total Rules:</strong> {total_rules}</p>
        <p><strong>Total Amendments Applied:</strong> {total_amendments}</p>
    </div>

    <div class="rules-container">
""".format(
            generated_time=datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            total_rules=len(rules),
            total_amendments=len(amendments)
        )

        # Add rules
        for rule in rules:
            has_amendments = len(rule.amendment_history) > 0
            amendment_badge = '<span class="amendment-badge">Modified</span>' if has_amendments else ''

            html += f"""
        <div class="rule">
            <div class="rule-number">
                Rule {rule.display_number}
                {amendment_badge}
            </div>
            <div class="rule-content">
                {self._escape_html(rule.content)}
            </div>
"""

            if has_amendments:
                html += """
            <div class="amendment-history">
                <strong>Amendment History:</strong>
"""
                for amend in rule.amendment_history:
                    date_str = amend.date.strftime('%Y-%m-%d') if amend.date else 'Unknown'
                    html += f"""
                <div class="amendment-item">
                    • {amend.action.value} per {amend.go_id} ({date_str})
                </div>
"""
                html += """
            </div>
"""

            html += """
        </div>
"""

        html += """
    </div>
</body>
</html>
"""

        return html

    def _escape_html(self, text: str) -> str:
        """Escape HTML special characters"""
        return (text
                .replace('&', '&amp;')
                .replace('<', '&lt;')
                .replace('>', '&gt;')
                .replace('"', '&quot;')
                .replace("'", '&#39;')
                .replace('\n', '<br>'))

    def _generate_audit_report(
        self,
        audit_report: Dict[str, Any],
        output_dir: Path
    ) -> Path:
        """Generate audit report"""
        logger.info("Generating audit report...")

        output_path = output_dir / 'audit_report.json'
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(audit_report, f, indent=2, ensure_ascii=False)

        logger.info(f"Audit report saved to {output_path}")
        return output_path


def main():
    """Test output generator"""
    # This would typically be called from the main pipeline
    pass


if __name__ == "__main__":
    main()
