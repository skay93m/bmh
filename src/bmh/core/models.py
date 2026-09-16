from __future__ import annotations

import json
import re
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, field_validator


class NoteModel(BaseModel):
    """Normalized schema for a Basic Memory note or search result item."""

    title: str = Field(default="Untitled Note")
    content: str = Field(default="")
    entity: Optional[str] = None
    external_id: Optional[str] = None
    file_path: Optional[str] = None
    permalink: Optional[str] = None
    updated_at: Optional[str] = None
    note_type: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    status: Optional[str] = None
    priority: Optional[str] = None
    assigned_to: Optional[str] = None
    steps: List[str] = Field(default_factory=list)
    frontmatter: Dict[str, Any] = Field(default_factory=dict)
    metadata: Dict[str, Any] = Field(default_factory=dict)

    @field_validator("title", mode="before")
    @classmethod
    def extract_title(cls, v: Any, info: Any) -> str:
        if v is not None and str(v).strip():
            return str(v).strip()
        return "Untitled Note"

    @field_validator("content", mode="before")
    @classmethod
    def extract_content(cls, v: Any) -> str:
        if v is None:
            return ""
        return str(v)

    @field_validator("tags", mode="before")
    @classmethod
    def coerce_tags(cls, v: Any) -> List[str]:
        if v is None:
            return []
        if isinstance(v, str):
            return [t.strip() for t in v.split(",") if t.strip()]
        if isinstance(v, (list, tuple, set)):
            return [str(t).strip() for t in v if str(t).strip()]
        return [str(v).strip()]

    def __getitem__(self, key: str) -> Any:
        if hasattr(self, key):
            return getattr(self, key)
        if key in self.metadata:
            return self.metadata[key]
        raise KeyError(key)

    def get(self, key: str, default: Any = None) -> Any:
        try:
            return self[key]
        except KeyError:
            return default

    def __contains__(self, key: str) -> bool:
        return hasattr(self, key) or (key in self.metadata)

    def keys(self) -> List[str]:
        base_keys = list(self.__class__.model_fields.keys())
        return base_keys + [k for k in self.metadata.keys() if k not in base_keys]


class SearchResult(BaseModel):
    """Pydantic model representing search-notes response envelope."""

    results: List[NoteModel] = Field(default_factory=list)
    total: int = 0
    current_page: int = 1
    page_size: int = 10
    has_more: bool = False


class TaskItem(BaseModel):
    """Represents a checklist task item within a note."""

    index: int
    text: str
    completed: bool = False
    raw_line: str = ""


def extract_task_items(content: str) -> List[TaskItem]:
    """Extract checklist items from markdown content."""
    items: List[TaskItem] = []
    pattern = re.compile(r"^(?:(?:\d+\.)|[-*])\s+\[([ xX])\]\s+(.*)$")
    idx = 1
    for line in content.splitlines():
        match = pattern.match(line.strip())
        if match:
            status_char, step_text = match.groups()
            completed = status_char.lower() == "x"
            items.append(
                TaskItem(
                    index=idx,
                    text=step_text.strip(),
                    completed=completed,
                    raw_line=line.strip(),
                )
            )
            idx += 1
    return items


class FieldValidationResult(BaseModel):
    """Validation result for an individual schema field."""

    field_name: str
    field_type: Optional[str] = None
    required: bool = False
    status: str = "present"  # "present", "missing", "invalid"
    values: List[Any] = Field(default_factory=list)
    message: Optional[str] = None


class NoteValidationResult(BaseModel):
    """Validation result for an individual note."""

    note_identifier: str
    schema_entity: Optional[str] = None
    passed: bool = True
    field_results: List[FieldValidationResult] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    errors: List[str] = Field(default_factory=list)


class SchemaValidationReport(BaseModel):
    """Overall report returned by schema-validate."""

    total_notes: int = 0
    total_entities: int = 0
    valid_count: int = 0
    warning_count: int = 0
    error_count: int = 0
    results: List[NoteValidationResult] = Field(default_factory=list)
    type_summaries: List[Dict[str, Any]] = Field(default_factory=list)
    error: Optional[str] = None


class OrphanEntity(BaseModel):
    """Entity without relations in the knowledge graph."""

    external_id: Optional[str] = None
    title: str = "Untitled"
    note_type: Optional[str] = None
    file_path: Optional[str] = None


class DoctorReport(BaseModel):
    """Parsed result of bm doctor execution."""

    status: str = "passed"  # "passed" | "failed"
    passed: bool = True
    output: str = ""
    steps: List[str] = Field(default_factory=list)


class SchemaDriftField(BaseModel):
    """Drifting schema field item."""

    name: str
    source: Optional[str] = "observation"
    count: int = 0
    total: int = 0
    percentage: float = 0.0


class SchemaDiffReport(BaseModel):
    """Report returned by schema-diff."""

    note_type: str = ""
    schema_found: bool = True
    new_fields: List[SchemaDriftField] = Field(default_factory=list)
    dropped_fields: List[SchemaDriftField] = Field(default_factory=list)
    cardinality_changes: List[Dict[str, Any]] = Field(default_factory=list)
    error: Optional[str] = None


class LintAllSummary(BaseModel):
    """Aggregated health score and summary for Lint All dashboard."""

    health_score: int = 100
    grade: str = "A"
    doctor_passed: bool = True
    total_notes: int = 0
    valid_schemas: int = 0
    schema_warnings: int = 0
    schema_errors: int = 0
    orphan_count: int = 0
    drift_count: int = 0
    action_items: List[str] = Field(default_factory=list)


class NoteTemplate(BaseModel):
    """Note template definition for Ingest wizards."""

    name: str
    folder: str
    note_type: str
    description: str
    default_tags: List[str] = Field(default_factory=list)


def _dict_to_note(item: Dict[str, Any]) -> NoteModel:
    """Safely convert a raw dictionary into a NoteModel."""
    title = (
        item.get("title")
        or item.get("name")
        or item.get("header")
        or "Untitled Note"
    )
    content = (
        item.get("content")
        or item.get("body")
        or item.get("description")
        or item.get("text")
        or ""
    )
    entity = item.get("entity") or item.get("permalink") or item.get("entity_name")
    external_id = item.get("external_id") or item.get("id") or item.get("uuid")
    file_path = item.get("file_path") or item.get("path")
    permalink = item.get("permalink")
    updated_at = item.get("updated_at") or item.get("timestamp") or item.get("date")

    metadata = item.get("metadata") or {}
    if not isinstance(metadata, dict):
        metadata = {"raw": metadata}

    frontmatter = item.get("frontmatter") or {}
    if not isinstance(frontmatter, dict):
        frontmatter = {}

    note_type = (
        item.get("type")
        or metadata.get("note_type")
        or frontmatter.get("type")
    )

    tags_raw = item.get("tags") or metadata.get("tags") or frontmatter.get("tags") or []
    if isinstance(tags_raw, str):
        tags = [t.strip() for t in tags_raw.split(",") if t.strip()]
    elif isinstance(tags_raw, (list, tuple, set)):
        tags = [str(t).strip() for t in tags_raw if str(t).strip()]
    elif tags_raw is not None:
        tags = [str(tags_raw).strip()]
    else:
        tags = []

    status = item.get("status") or metadata.get("status") or frontmatter.get("status")
    priority = item.get("priority") or metadata.get("priority") or frontmatter.get("priority")
    assigned_to = item.get("assigned_to") or metadata.get("assigned_to") or frontmatter.get("assigned_to")

    steps_raw = item.get("steps") or metadata.get("steps") or frontmatter.get("steps") or []
    steps: List[str] = []
    if isinstance(steps_raw, list):
        steps = [str(s) for s in steps_raw]
    elif steps_raw:
        steps = [str(steps_raw)]

    return NoteModel(
        title=str(title),
        content=str(content),
        entity=str(entity) if entity else None,
        external_id=str(external_id) if external_id else None,
        file_path=str(file_path) if file_path else None,
        permalink=str(permalink) if permalink else None,
        updated_at=str(updated_at) if updated_at else None,
        note_type=str(note_type) if note_type else None,
        tags=tags,
        status=str(status) if status else None,
        priority=str(priority) if priority else None,
        assigned_to=str(assigned_to) if assigned_to else None,
        steps=steps,
        frontmatter=frontmatter,
        metadata=metadata,
    )


def normalize_notes_json(data: Any) -> List[NoteModel]:
    """Normalize raw JSON data (string, dict, or list) into a list of NoteModel instances."""
    if isinstance(data, str):
        data = data.strip()
        if not data:
            return []
        try:
            parsed = json.loads(data)
        except json.JSONDecodeError:
            # Fallback for plain text or malformed JSON
            return [NoteModel(title="Plain Text Output", content=data)]
    else:
        parsed = data

    if isinstance(parsed, list):
        notes = []
        for item in parsed:
            if isinstance(item, dict):
                notes.append(_dict_to_note(item))
            else:
                notes.append(NoteModel(content=str(item)))
        return notes

    if isinstance(parsed, dict):
        # Look for standard wrapper keys
        for key in ("results", "items", "notes", "data", "rows"):
            if key in parsed and isinstance(parsed[key], list):
                return normalize_notes_json(parsed[key])

        # Single object
        return [_dict_to_note(parsed)]

    if parsed is not None:
        return [NoteModel(content=str(parsed))]

    return []

