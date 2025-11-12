# System Architecture

## Overview

The Automated Rulebook Consolidation System follows a **modular pipeline architecture** with six specialized processing stages, powered by **Google ADK** and **Gemini AI**.

## Design Principles

1. **Modularity**: Each module is independent and testable
2. **Code-First**: All logic defined in Python (ADK principle)
3. **AI-Powered**: Leverages Gemini for intelligent text understanding
4. **Traceable**: Complete audit trail of all modifications
5. **Validatable**: Cross-validation against reference documents

## Module Details

### Module 1: Document Preprocessor

**Purpose**: Transform raw PDF into structured, normalized content

**Components**:
- `PDFExtractor`: Extracts text with spatial metadata using pdfplumber
- `ContentNormalizer`: Fixes broken words, standardizes formatting
- `NoiseFilter`: Removes headers, footers, page numbers

**Input**: Raw PDF file
**Output**: Cleaned, normalized text lines with metadata

**Key Technologies**:
- pdfplumber for PDF extraction
- Regex for pattern matching
- Spatial analysis for layout detection

### Module 2: Logical Unit Reconstructor

**Purpose**: Rebuild multi-page rules and GOs into coherent units

**Components**:
- `GeminiClient`: Interface to Gemini API
- `RuleReconstructor`: Rebuilds rules across page boundaries
- `GOReconstructor`: Reconstructs Government Orders

**Input**: Normalized text lines
**Output**: Complete Rule and GO objects

**Key Technologies**:
- **Gemini AI** for continuation analysis
- Pattern matching for rule/GO detection
- Semantic analysis for content classification

**AI Usage**:
```python
# Gemini analyzes if content continues across pages
analysis = gemini.analyze_continuation(
    current_page_end,
    next_page_start,
    context_type="rule"
)
# Returns: {continues: true/false, confidence: 0.0-1.0, reason: "..."}
```

### Module 3: Document Segmenter

**Purpose**: Separate base rulebook from amendments

**Components**:
- `DocumentSegmenter`: Detects transition points, classifies content

**Input**: Rules and GOs
**Output**: Base rules + Amendment GOs (chronologically sorted)

**Key Technologies**:
- Structural analysis
- Content classification
- Temporal ordering

### Module 4: Amendment Extractor

**Purpose**: Convert GO text into structured amendments

**Components**:
- `AmendmentExtractionAgent`: **ADK-style agent** using Gemini
- `AmendmentExtractor`: Orchestrates extraction and validation

**Input**: Government Orders
**Output**: Structured Amendment objects

**Key Technologies**:
- **Google ADK agent pattern**
- **Gemini API** for natural language understanding
- JSON-based structured extraction

**AI Usage**:
```python
# Agent extracts structured amendments from natural language
amendments = agent.extract_amendments_from_go(
    go_content=go.content,
    go_id=go.go_id,
    go_date=go.date
)
# Returns: [{action, target_path, old_text, new_text, confidence}, ...]
```

**Example Transformation**:

Input (Natural Language):
```
"In Rule 22, sub-rule (2), clause (e), for the words '14-Backward Class (Group-C)-Women'
substitute '14-Backward Class(Group-C)- In every third cycle of 100 point roster...'"
```

Output (Structured):
```json
{
  "action": "SUBSTITUTE",
  "target_path": ["rule-22", "sub-rule-2", "clause-e"],
  "old_text": "14-Backward Class (Group-C)-Women",
  "new_text": "14-Backward Class(Group-C)- In every third cycle...",
  "confidence": 0.95
}
```

### Module 5: Rulebook Consolidation Engine

**Purpose**: Apply amendments dynamically to base rulebook

**Components**:
- `RuleTree`: Hierarchical tree structure with UUID-based addressing
- `RulebookConsolidator`: Applies amendments, handles renumbering

**Input**: Base rules + Amendments
**Output**: Consolidated RuleTree

**Key Technologies**:
- Tree data structure with dynamic addressing
- UUID-based tracking (immutable)
- Display number mapping (mutable)
- Snapshot system for rollback

**Data Structure**:
```
RuleTree
├── Rule 1 (uuid: abc123, display: "1")
├── Rule 2 (uuid: def456, display: "2")
│   ├── Sub-rule 2(1) (uuid: ghi789)
│   └── Sub-rule 2(2) (uuid: jkl012)
├── Rule 2A (uuid: mno345, display: "2A") ← Inserted
└── Rule 3 (uuid: pqr678, display: "3")
```

**Amendment Application**:
1. **SUBSTITUTE**: Replace content, preserve structure
2. **OMIT**: Remove node and descendants, renumber
3. **INSERT**: Create new node, insert at position, renumber
4. **RENUMBER**: Update display number mapping

### Module 6: Validator & Output Generator

**Purpose**: Validate and generate outputs

**Components**:
- `RulebookValidator`: Cross-validates against reference
- `OutputGenerator`: Produces JSON, HTML, audit reports

**Input**: Consolidated tree + Reference (optional)
**Output**: Validated rulebook + Multiple formats

**Key Technologies**:
- Levenshtein distance for text similarity
- HTML generation with change tracking
- JSON serialization

**Validation Metrics**:
- Structural match: ≥95% rule numbering alignment
- Content fidelity: ≥95% text similarity
- Anomaly detection: Missing/extra rules, content differences

## Data Flow

```
PDF File
  ↓
[Module 1] → Normalized Text Lines
  ↓
[Module 2] → Rules + GOs
  ↓
[Module 3] → Base Rules + Amendment GOs
  ↓
[Module 4] → Structured Amendments
  ↓
[Module 5] → Consolidated Rule Tree
  ↓
[Module 6] → Validated Outputs (JSON/HTML/Audit)
```

## Google ADK Integration

### ADK Principles Applied

1. **Code-First Development**
   - All logic in Python
   - No complex configuration files
   - Direct API calls

2. **Agent Pattern**
   - `AmendmentExtractionAgent`: Specialized for parsing GOs
   - `GeminiClient`: Reusable interface to Gemini
   - Modular, composable agents

3. **Model Integration**
   - Optimized for Gemini 2.0 Flash
   - Model-agnostic design (can swap LLMs)
   - Configurable parameters (temperature, max_tokens)

### Gemini API Usage

**Primary Use Cases**:

1. **Continuation Analysis** (Module 2)
   ```python
   gemini.analyze_continuation(text1, text2, context_type)
   ```

2. **Content Classification** (Module 2)
   ```python
   gemini.classify_content_type(content)
   ```

3. **Amendment Extraction** (Module 4)
   ```python
   gemini.generate(prompt, system_instruction)
   ```

4. **Ambiguity Resolution** (Module 4)
   ```python
   gemini.resolve_ambiguous_target(reference, context, rules)
   ```

## Error Handling

### Confidence Thresholds

- Amendments with confidence < 0.7 are **flagged** for review
- Low-confidence operations logged for audit

### Conflict Detection

- Same-date modifications to same rule
- Missing target references
- Overlapping amendments

### Validation Gates

- Internal consistency checks
- Cross-document validation (if reference provided)
- Anomaly detection and reporting

## Performance Considerations

### Optimization Strategies

1. **Batching**: Process multiple amendments in single API call when possible
2. **Caching**: Reuse Gemini responses for similar queries
3. **Parallel Processing**: Independent modules can run concurrently
4. **Snapshot System**: Periodic snapshots avoid full reprocessing

### Scalability

- **Small documents** (< 50 pages): < 2 minutes
- **Medium documents** (50-200 pages): 2-10 minutes
- **Large documents** (200+ pages): 10-30 minutes

(Times depend on API latency and document complexity)

## Extension Points

### Adding New Amendment Actions

1. Add to `AmendmentAction` enum in `models/document.py`
2. Implement handler in `RulebookConsolidator._apply_single_amendment()`
3. Update agent extraction patterns in `AmendmentExtractionAgent`

### Supporting New Output Formats

1. Add format to `config/config.yaml`
2. Implement generator method in `OutputGenerator`
3. Register in `OutputGenerator.generate_all()`

### Custom Validation Rules

1. Extend `RulebookValidator._check_internal_consistency()`
2. Add custom metrics to `ValidationResult`
3. Update audit report generation

## Technology Stack

- **Python 3.9+**: Core language
- **Google ADK**: Agent framework principles
- **Gemini API**: AI-powered text understanding
- **pdfplumber**: PDF text extraction
- **python-Levenshtein**: Text similarity
- **pydantic**: Data validation
- **PyYAML**: Configuration management

## Security Considerations

- API keys stored in `.env` (not in repo)
- No sensitive data logged
- PDF processing sandboxed
- Input validation on all user inputs

## Future Enhancements

1. **Batch Processing**: Process multiple documents in parallel
2. **Web Interface**: Browser-based UI for document upload
3. **Advanced Validation**: Machine learning for anomaly detection
4. **Real-time Processing**: Stream-based processing for large documents
5. **Multi-language Support**: Extend beyond English documents
