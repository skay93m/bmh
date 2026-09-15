from __future__ import annotations

import json
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


class SearchResult(BaseModel):
    """Pydantic model representing search-notes response envelope."""

    results: List[NoteModel] = Field(default_factory=list)
    total: int = 0
    current_page: int = 1
    page_size: int = 10
    has_more: bool = False


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
        
    note_type = item.get("type") or metadata.get("note_type")

    return NoteModel(
        title=str(title),
        content=str(content),
        entity=str(entity) if entity else None,
        external_id=str(external_id) if external_id else None,
        file_path=str(file_path) if file_path else None,
        permalink=str(permalink) if permalink else None,
        updated_at=str(updated_at) if updated_at else None,
        note_type=str(note_type) if note_type else None,
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
