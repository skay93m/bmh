from __future__ import annotations

import pytest
from bmh.core.models import NoteModel, SearchResult, normalize_notes_json


def test_note_model_defaults():
    note = NoteModel()
    assert note.title == "Untitled Note"
    assert note.content == ""
    assert note.entity is None
    assert note.external_id is None
    assert note.metadata == {}


def test_note_model_custom_values():
    note = NoteModel(
        title="My Custom Note",
        content="Some markdown body",
        entity="kancil/tasks/foo.md",
        external_id="uuid-123",
        file_path="tasks/foo.md",
        updated_at="2026-09-15T12:00:00Z",
        metadata={"category": "spec"},
    )
    assert note.title == "My Custom Note"
    assert note.content == "Some markdown body"
    assert note.entity == "kancil/tasks/foo.md"
    assert note.external_id == "uuid-123"
    assert note.metadata == {"category": "spec"}


def test_note_model_blank_title_and_none_content():
    note = NoteModel(title="   ", content=None)
    assert note.title == "Untitled Note"
    assert note.content == ""


def test_normalize_empty_and_whitespace():
    assert normalize_notes_json("") == []
    assert normalize_notes_json("   ") == []
    assert normalize_notes_json(None) == []


def test_normalize_plain_text():
    notes = normalize_notes_json("not valid json at all")
    assert len(notes) == 1
    assert notes[0].title == "Plain Text Output"
    assert notes[0].content == "not valid json at all"


def test_normalize_json_array_of_objects():
    raw_json = """
    [
        {"title": "Note 1", "content": "Body 1", "entity": "ent:1", "external_id": "id-1", "metadata": "not-a-dict"},
        {"name": "Note 2", "body": "Body 2", "permalink": "ent:2", "id": "id-2"}
    ]
    """
    notes = normalize_notes_json(raw_json)
    assert len(notes) == 2
    assert notes[0].title == "Note 1"
    assert notes[0].content == "Body 1"
    assert notes[0].entity == "ent:1"
    assert notes[0].external_id == "id-1"
    assert notes[0].metadata == {"raw": "not-a-dict"}

    assert notes[1].title == "Note 2"
    assert notes[1].content == "Body 2"
    assert notes[1].entity == "ent:2"
    assert notes[1].external_id == "id-2"


def test_normalize_json_wrapper_results():
    payload = {
        "results": [
            {
                "title": "Wrapped Note",
                "content": "Content inside wrapper",
                "entity": "project:wrapped",
                "external_id": "uuid-999",
                "metadata": {"note_type": "task"},
            }
        ],
        "total": 1,
        "current_page": 1,
    }
    notes = normalize_notes_json(payload)
    assert len(notes) == 1
    assert notes[0].title == "Wrapped Note"
    assert notes[0].content == "Content inside wrapper"
    assert notes[0].note_type == "task"


def test_normalize_single_object():
    payload = {
        "title": "Solo Note",
        "description": "Just one description",
        "external_id": "solo-id",
    }
    notes = normalize_notes_json(payload)
    assert len(notes) == 1
    assert notes[0].title == "Solo Note"
    assert notes[0].content == "Just one description"
    assert notes[0].external_id == "solo-id"


def test_normalize_primitive_elements():
    notes = normalize_notes_json(["item 1", "item 2"])
    assert len(notes) == 2
    assert notes[0].content == "item 1"
    assert notes[1].content == "item 2"


def test_normalize_primitive_single_value():
    notes = normalize_notes_json(12345)
    assert len(notes) == 1
    assert notes[0].content == "12345"
