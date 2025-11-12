"""
Data models for document representation
"""
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any
from datetime import datetime
from enum import Enum
import uuid


class DocumentType(Enum):
    """Document type classification"""
    BASE_RULEBOOK = "base_rulebook"
    AMENDMENT_COLLECTION = "amendment_collection"
    MIXED_DOCUMENT = "mixed_document"
    CONSOLIDATED_RULEBOOK = "consolidated_rulebook"


class AmendmentAction(Enum):
    """Amendment action types"""
    SUBSTITUTE = "SUBSTITUTE"
    OMIT = "OMIT"
    INSERT = "INSERT"
    RENUMBER = "RENUMBER"


@dataclass
class TextLine:
    """Represents a single line of text with metadata"""
    content: str
    page_number: int
    x: float
    y: float
    font_size: float
    font_name: str
    line_height: float
    indentation: float
    is_bold: bool = False
    is_italic: bool = False


@dataclass
class PageMetadata:
    """Metadata for a document page"""
    page_number: int
    width: float
    height: float
    has_header: bool = False
    has_footer: bool = False
    text_density: float = 0.0


@dataclass
class DocumentFingerprint:
    """Unique identifier for a document"""
    first_100_chars: str
    font_size_distribution: Dict[float, int]
    structure_hash: str
    document_type: DocumentType
    total_pages: int
    creation_date: Optional[datetime] = None


@dataclass
class Rule:
    """Represents a complete rule with metadata"""
    uuid: str = field(default_factory=lambda: str(uuid.uuid4()))
    display_number: str = ""
    content: str = ""
    start_page: int = 0
    end_page: int = 0
    children: List['Rule'] = field(default_factory=list)
    parent_uuid: Optional[str] = None
    level: int = 0  # 0=Rule, 1=Sub-rule, 2=Clause, etc.
    amendment_history: List['Amendment'] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert rule to dictionary"""
        return {
            "uuid": self.uuid,
            "display_number": self.display_number,
            "content": self.content,
            "start_page": self.start_page,
            "end_page": self.end_page,
            "level": self.level,
            "children": [child.to_dict() for child in self.children],
            "amendment_history": [
                {
                    "go_id": a.go_id,
                    "date": a.date.isoformat() if a.date else None,
                    "action": a.action.value
                }
                for a in self.amendment_history
            ]
        }


@dataclass
class GovernmentOrder:
    """Represents a Government Order (GO)"""
    uuid: str = field(default_factory=lambda: str(uuid.uuid4()))
    go_id: str = ""
    date: Optional[datetime] = None
    effective_date: Optional[datetime] = None
    department: str = ""
    file_number: str = ""
    content: str = ""
    start_page: int = 0
    end_page: int = 0
    header_hash: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """Convert GO to dictionary"""
        return {
            "uuid": self.uuid,
            "go_id": self.go_id,
            "date": self.date.isoformat() if self.date else None,
            "effective_date": self.effective_date.isoformat() if self.effective_date else None,
            "department": self.department,
            "file_number": self.file_number,
            "content": self.content,
            "start_page": self.start_page,
            "end_page": self.end_page
        }


@dataclass
class Amendment:
    """Represents a structured amendment instruction"""
    uuid: str = field(default_factory=lambda: str(uuid.uuid4()))
    go_id: str = ""
    go_uuid: str = ""
    date: Optional[datetime] = None
    effective_date: Optional[datetime] = None
    action: AmendmentAction = AmendmentAction.SUBSTITUTE
    target_path: List[str] = field(default_factory=list)
    target_uuid: Optional[str] = None
    old_text: Optional[str] = None
    new_text: Optional[str] = None
    position: Optional[str] = None  # "before", "after", "replace"
    confidence: float = 1.0
    flagged: bool = False
    flag_reason: Optional[str] = None
    context: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert amendment to dictionary"""
        return {
            "uuid": self.uuid,
            "go_id": self.go_id,
            "go_uuid": self.go_uuid,
            "date": self.date.isoformat() if self.date else None,
            "effective_date": self.effective_date.isoformat() if self.effective_date else None,
            "action": self.action.value,
            "target_path": self.target_path,
            "target_uuid": self.target_uuid,
            "old_text": self.old_text,
            "new_text": self.new_text,
            "position": self.position,
            "confidence": self.confidence,
            "flagged": self.flagged,
            "flag_reason": self.flag_reason
        }


@dataclass
class ProcessedDocument:
    """Container for processed document data"""
    fingerprint: DocumentFingerprint
    pages: List[PageMetadata]
    text_lines: List[TextLine]
    rules: List[Rule] = field(default_factory=list)
    government_orders: List[GovernmentOrder] = field(default_factory=list)
    amendments: List[Amendment] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert document to dictionary"""
        return {
            "fingerprint": {
                "document_type": self.fingerprint.document_type.value,
                "total_pages": self.fingerprint.total_pages,
                "structure_hash": self.fingerprint.structure_hash
            },
            "total_rules": len(self.rules),
            "total_gos": len(self.government_orders),
            "total_amendments": len(self.amendments),
            "rules": [rule.to_dict() for rule in self.rules],
            "government_orders": [go.to_dict() for go in self.government_orders],
            "amendments": [amend.to_dict() for amend in self.amendments]
        }


@dataclass
class ValidationResult:
    """Results from validation process"""
    structural_match_score: float = 0.0
    content_fidelity_score: float = 0.0
    rule_alignment_percentage: float = 0.0
    anomalies: List[str] = field(default_factory=list)
    passed: bool = False
    details: Dict[str, Any] = field(default_factory=dict)
