# Quick Start Guide

## 5-Minute Setup

### 1. Install Dependencies

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install packages
pip install -r requirements.txt
```

### 2. Set Up Google API Key

```bash
# Copy environment template
cp .env.example .env

# Edit .env and add your key:
# GOOGLE_API_KEY=your_actual_key_here
```

**Get your API key**: https://aistudio.google.com/app/apikey

### 3. Run the System

```bash
# Place your PDF in data/input/
# Then run:
python main.py data/input/your_rulebook.pdf
```

### 4. Check Results

Results will be in `data/output/`:
- `consolidated_rulebook.json` - Structured data
- `consolidated_rulebook.html` - Human-readable version
- `audit_report.json` - Validation metrics

## Example Workflow

```bash
# 1. Process a 1996 rulebook with amendments
python main.py data/input/rulebook_1996.pdf --output results/1996_consolidated

# 2. Validate against 2008 reference
python main.py data/input/rulebook_1996.pdf \
  --reference data/reference/rulebook_2008.pdf \
  --output results/validated

# 3. View results
open results/validated/consolidated_rulebook.html
```

## Testing Individual Modules

```bash
# Test just the preprocessor
python -m src.modules.module1_preprocessor.preprocessor data/input/test.pdf

# Test reconstruction
python -m src.modules.module2_reconstructor.reconstructor data/input/test.pdf

# Test full pipeline
python -m src.pipeline data/input/test.pdf
```

## Troubleshooting

**Problem**: "No module named 'src'"
- **Solution**: Run from project root directory

**Problem**: "GOOGLE_API_KEY not set"
- **Solution**: Check `.env` file exists and has valid key

**Problem**: "pdfplumber error"
- **Solution**: Ensure PDF is not encrypted or image-only

## Next Steps

- Read full [README.md](README.md) for detailed documentation
- Check [config/config.yaml](config/config.yaml) for customization
- See example outputs in `data/output/`

## Support

- 📚 Documentation: See README.md
- 🐛 Issues: Create a GitHub issue
- 💬 Questions: Check troubleshooting section
