# Automated Rulebook Consolidation System (APSSR)

A sophisticated AI-powered system for processing government rulebooks and their amendments to generate consolidated, up-to-date versions using **Google ADK** and **Gemini API**.

## 🎯 Overview

This system processes complex government documents where rules and amendments span multiple pages with inconsistent formatting. It intelligently reconstructs logical units, extracts structured amendments, and dynamically applies them to produce validated consolidated rulebooks.

## ✨ Features

- **PDF Text Extraction**: Advanced extraction preserving spatial coordinates and metadata
- **Intelligent Reconstruction**: Uses Gemini AI to rebuild multi-page rules and Government Orders
- **Smart Segmentation**: Automatically separates base rulebook from amendments
- **AI-Powered Extraction**: ADK agents extract structured amendments from natural language
- **Dynamic Consolidation**: Applies amendments while handling structural evolution
- **Comprehensive Validation**: Cross-validates against reference documents
- **Multiple Output Formats**: Generates JSON, HTML, and audit reports

## 🏗️ System Architecture

The system consists of **6 core modules** working sequentially:

```
┌─────────────────────────────────────────────────────────────┐
│                    INPUT: PDF Document                       │
│           (Rulebook + Amendments + GOs)                      │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│  MODULE 1: Document Preprocessor                             │
│  • PDF text extraction with spatial metadata                 │
│  • Content normalization & noise filtering                   │
│  • Document fingerprinting                                    │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│  MODULE 2: Logical Unit Reconstructor (Gemini AI)            │
│  • Rebuild multi-page rules                                  │
│  • Reconstruct Government Orders                             │
│  • Build hierarchical structure                              │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│  MODULE 3: Document Segmenter                                │
│  • Separate base rulebook from amendments                    │
│  • Detect transition points                                  │
│  • Sort GOs chronologically                                  │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│  MODULE 4: Amendment Extractor (ADK Agents)                  │
│  • Extract structured amendments from GOs                    │
│  • Classify action types (SUBSTITUTE/OMIT/INSERT)            │
│  • Resolve ambiguous references                              │
│  • Detect conflicts                                          │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│  MODULE 5: Rulebook Consolidation Engine                     │
│  • Build hierarchical rule tree                              │
│  • Apply amendments dynamically                              │
│  • Handle structural evolution                               │
│  • Track amendment history                                   │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│  MODULE 6: Validator & Output Generator                      │
│  • Validate against reference documents                      │
│  • Generate consolidated rulebook (JSON/HTML)                │
│  • Create audit reports                                      │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│              OUTPUT: Consolidated Rulebook                    │
│      + Amendment History + Validation Report                  │
└─────────────────────────────────────────────────────────────┘
```

## 🚀 Quick Start

### Prerequisites

- Python 3.9+
- Google API Key (for Gemini)

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd APSSR
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Download spaCy model** (optional, for advanced NLP)
   ```bash
   python -m spacy download en_core_web_sm
   ```

5. **Configure environment**
   ```bash
   cp .env.example .env
   # Edit .env and add your GOOGLE_API_KEY
   ```

### Configuration

Edit `.env` file:

```env
GOOGLE_API_KEY=your_google_api_key_here
GEMINI_MODEL=gemini-2.0-flash-exp
MAX_WORKERS=4
ENABLE_VALIDATION=true
```

## 📖 Usage

### Basic Usage

Process a rulebook PDF:

```bash
python main.py input.pdf
```

### With Reference Document

Process and validate against a reference consolidated rulebook:

```bash
python main.py input.pdf --reference reference_2008.pdf
```

### Custom Output Directory

```bash
python main.py input.pdf --output ./results
```

### Complete Example

```bash
python main.py rulebook_1996_with_amendments.pdf \
  --reference rulebook_2008_consolidated.pdf \
  --output ./output/consolidated_2024
```

## 📂 Project Structure

```
APSSR/
├── src/
│   ├── modules/
│   │   ├── module1_preprocessor/        # PDF extraction & normalization
│   │   │   ├── pdf_extractor.py
│   │   │   ├── content_normalizer.py
│   │   │   ├── noise_filter.py
│   │   │   └── preprocessor.py
│   │   ├── module2_reconstructor/       # Logical unit reconstruction
│   │   │   ├── gemini_client.py
│   │   │   ├── rule_reconstructor.py
│   │   │   ├── go_reconstructor.py
│   │   │   └── reconstructor.py
│   │   ├── module3_segmenter/           # Document segmentation
│   │   │   └── segmenter.py
│   │   ├── module4_extractor/           # Amendment extraction
│   │   │   ├── adk_agent.py
│   │   │   └── extractor.py
│   │   ├── module5_consolidator/        # Rule consolidation
│   │   │   ├── rule_tree.py
│   │   │   └── consolidator.py
│   │   └── module6_validator/           # Validation & output
│   │       ├── validator.py
│   │       └── output_generator.py
│   ├── models/
│   │   └── document.py                  # Data models
│   ├── utils/
│   │   ├── config_loader.py
│   │   └── logger.py
│   ├── pipeline.py                      # Main pipeline orchestrator
│   └── __init__.py
├── config/
│   └── config.yaml                      # System configuration
├── data/
│   ├── input/                           # Input PDFs
│   ├── output/                          # Generated outputs
│   └── reference/                       # Reference documents
├── tests/                               # Unit tests
├── logs/                                # Application logs
├── main.py                              # Entry point
├── requirements.txt                     # Python dependencies
├── .env.example                         # Environment template
└── README.md                            # This file
```

## 🔧 Configuration

Edit `config/config.yaml` to customize:

```yaml
gemini:
  model: "gemini-2.0-flash-exp"
  temperature: 0.1
  max_tokens: 8000

preprocessing:
  min_text_length: 10
  header_footer_threshold: 0.9

extraction:
  action_types:
    - "SUBSTITUTE"
    - "OMIT"
    - "INSERT"

consolidation:
  numbering_conventions:
    after_rule: ["A", "B", "C"]
    conflict_resolution: "chronological"

validation:
  structural_match_threshold: 0.95
  content_fidelity_threshold: 0.95
```

## 📊 Output Files

The system generates:

1. **`consolidated_rulebook.json`** - Complete structured data
   ```json
   {
     "metadata": {...},
     "rules": [
       {
         "uuid": "...",
         "display_number": "22",
         "content": "...",
         "amendment_history": [...]
       }
     ]
   }
   ```

2. **`consolidated_rulebook.html`** - Human-readable version with change tracking

3. **`audit_report.json`** - Validation metrics and amendment statistics

## 🧪 Testing Individual Modules

Each module can be tested independently:

```bash
# Test Module 1: Preprocessor
python -m src.modules.module1_preprocessor.preprocessor input.pdf

# Test Module 2: Reconstructor
python -m src.modules.module2_reconstructor.reconstructor input.pdf

# Test Module 3: Segmenter
python -m src.modules.module3_segmenter.segmenter input.pdf

# Test Module 4: Extractor
python -m src.modules.module4_extractor.extractor input.pdf

# Test Module 5: Consolidator
python -m src.modules.module5_consolidator.consolidator input.pdf
```

## 🤖 Google ADK Integration

This system uses **Google ADK** principles:

- **Code-First Approach**: All logic defined in Python
- **Gemini Integration**: Advanced text understanding and extraction
- **Agent Pattern**: Specialized agents for different tasks
- **Model-Agnostic**: Can be adapted to other LLMs

### Key ADK Components

1. **GeminiClient** - Direct Gemini API integration
2. **AmendmentExtractionAgent** - Specialized agent for amendment parsing
3. **Pipeline Orchestrator** - Multi-agent coordination

## 🎓 Use Cases

- **Government Agencies**: Consolidate rulebooks automatically
- **Legal Teams**: Track regulatory changes over time
- **Compliance**: Maintain up-to-date policy documents
- **Research**: Analyze regulatory evolution

## 🔍 Advanced Features

### Handling Edge Cases

The system handles:

- **Multi-page rules** spanning 6+ pages
- **Partial page rules** with varying positioning
- **GO header separation** across pages
- **Temporal dependencies** in amendments
- **Interspersed content** (rules mixed with GOs)

### Amendment Conflict Detection

Automatically detects:

- Same-date modifications to same rule
- Missing target references
- Overlapping amendments

### Validation Metrics

- Structural match score (≥95% threshold)
- Content fidelity score (≥95% threshold)
- Rule alignment percentage
- Anomaly detection

## 📝 API Reference

### Pipeline Class

```python
from src.pipeline import RulebookConsolidationPipeline

pipeline = RulebookConsolidationPipeline()

# Process document
results = pipeline.process(
    pdf_path="input.pdf",
    output_dir="./output"
)

# Process with reference
results = pipeline.process_with_reference(
    pdf_path="input.pdf",
    reference_pdf_path="reference.pdf",
    output_dir="./output"
)
```

## 🐛 Troubleshooting

### Common Issues

1. **"GOOGLE_API_KEY not set"**
   - Ensure `.env` file exists with valid API key
   - Run: `export GOOGLE_API_KEY=your_key`

2. **PDF extraction errors**
   - Check PDF is not encrypted
   - Ensure PDF contains extractable text (not scanned images)

3. **Low confidence amendments**
   - Review flagged amendments in audit report
   - Adjust Gemini temperature in config

4. **Memory issues**
   - Reduce `max_tokens` in config
   - Process smaller document sections

## 🤝 Contributing

Contributions welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## 📄 License

[MIT License](LICENSE)

## 🙏 Acknowledgments

- Built with [Google ADK](https://github.com/google/adk-python)
- Powered by [Gemini API](https://ai.google.dev/)
- PDF processing by [pdfplumber](https://github.com/jsvine/pdfplumber)

## 📧 Support

For issues and questions:

- GitHub Issues: [Create an issue]
- Documentation: See `/docs` folder
- Email: support@example.com

---

**Made with ❤️ using Google ADK and Gemini AI**
