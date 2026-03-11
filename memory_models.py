from pydantic import BaseModel, Field, field_validator
from datetime import datetime
from typing import Literal, Optional, Any, Union
from uuid import UUID, uuid4
import hashlib


class MemorySource(BaseModel):
    """Who / what / where this memory came from — critical for provenance."""
    agent_id: str = Field(..., description="Unique ID of the agent instance")
    session_id: Optional[str] = Field(None, description="Conversation/thread/session ID")
    user_id: Optional[str] = Field(None, description="End-user identifier if applicable")
    tool_name: Optional[str] = Field(None, description="Tool/function that produced this")
    external_source: Optional[str] = Field(
        None, description="e.g. URL, API name, file path, human input"
    )


class MemoryEntry(BaseModel):
    """
    Core immutable memory unit.
    Every write creates a new entry → enables full audit trail & versioning.
    """
    id: UUID = Field(default_factory=uuid4)
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    # Core classification
    type: Literal[
        "fact",           # verifiable statement
        "preference",     # user stated or inferred preference
        "event",          # something that happened
        "reasoning_step", # agent's internal thought
        "tool_result",    # output from a tool call
        "user_instruction",
        "correction",     # agent/user corrected prior memory
        "summary"         # compressed recap of session
    ]
    
    content: Union[str, dict, list, float, int, bool, None] = Field(
        ..., description="The actual payload — keep simple types for serialization"
    )
    
    source: MemorySource
    
    # Integrity & audit fields
    content_hash: str = Field(
        default=None, 
        description="SHA-256 of content (JSON serialized) for tamper detection"
    )
    version: int = Field(1, ge=1, description="Increment on logical updates")
    previous_entry_id: Optional[UUID] = Field(
        None, description="Links to prior version if this supersedes it"
    )
    
    # Optional rich metadata
    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="e.g. confidence score, TTL, tags, context window refs"
    )

    @field_validator("content_hash", mode="before")
    @classmethod
    def compute_hash_if_missing(cls, v: Optional[str], info) -> str:
        if v is not None:
            return v
        # Auto-compute hash from content if not provided
        content_data = info.data.get("content")
        if content_data is None:
            return ""
        # Deterministic JSON serialization for hash stability
        import json
        serialized = json.dumps(
            content_data, sort_keys=True, separators=(",", ":"), default=str
        )
        return hashlib.sha256(serialized.encode("utf-8")).hexdigest()

    class Config:
        json_encoders = {
            datetime: lambda dt: dt.isoformat(),
            UUID: str,
        }
        # Optional: populate_by_name = True  (if you want alias support later)

    def model_dump_for_logging(self) -> dict:
        """Helper to get a Loki/Promtail-friendly dict (flat, no complex nesting)."""
        data = self.model_dump(mode="json")
        # Flatten source for easier querying in logs
        source_flat = {f"source_{k}": v for k, v in data.pop("source", {}).items()}
        return {**data, **source_flat}


# ────────────────────────────────────────────────
# Quick usage example
# ────────────────────────────────────────────────

if __name__ == "__main__":
    entry = MemoryEntry(
        type="preference",
        content="User prefers dark mode, metric units, and concise answers",
        source=MemorySource(
            agent_id="openclaw-ny-001",
            user_id="@devin_shinkle",
            session_id="sess_20260310_2304_est",
            external_source="direct user message"
        ),
        metadata={
            "confidence": 0.98,
            "expires_at": "2027-03-10",
            "tags": ["ui", "units"]
        }
    )

    print(entry.model_dump_json(indent=2))
    print("\nContent hash (auto-computed):", entry.content_hash)
    print("\nLogging-friendly version:")
    print(entry.model_dump_for_logging())
