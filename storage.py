from pathlib import Path
from typing import List, Optional
import json
from datetime import datetime
from uuid import UUID

from .models import MemoryEntry  # relative import from same package


class JsonlMemoryStore:
    """
    Simple append-only JSONL storage for MemoryEntry objects.
    Each line = one JSON-serialized MemoryEntry.
    
    Designed to be:
    - Cheap & local
    - Promtail-friendly (structured JSON lines)
    - Easy to tail / index / query later
    """

    def __init__(
        self,
        directory: str | Path = "./memory_logs",
        filename_prefix: str = "agent-memory",
    ):
        self.directory = Path(directory)
        self.directory.mkdir(parents=True, exist_ok=True)
        
        # One file per day keeps things manageable
        today_str = datetime.utcnow().strftime("%Y-%m-%d")
        self.file_path = self.directory / f"{filename_prefix}-{today_str}.jsonl"
        
        # We'll keep an in-memory cache of recent entries for fast read-back during a session
        # (not persisted across restarts — that's fine for most agent use-cases)
        self._session_cache: List[MemoryEntry] = []

    def append(self, entry: MemoryEntry) -> None:
        """
        Append a new memory entry (immutable — never modify existing ones).
        Writes to JSONL + keeps in lightweight session cache.
        """
        line_dict = entry.model_dump(mode="json")
        
        # Ensure deterministic serialization for reproducibility
        json_line = json.dumps(line_dict, sort_keys=True, separators=(",", ":")) + "\n"
        
        # Atomic append
        with self.file_path.open("a", encoding="utf-8") as f:
            f.write(json_line)
        
        # Keep in session memory for quick lookup during this run
        self._session_cache.append(entry)

    def get_recent(self, n: int = 50) -> List[MemoryEntry]:
        """Quick in-memory access to the most recent entries (session lifetime)."""
        return self._session_cache[-n:]

    def search_by_type(self, type_name: str, limit: int = 20) -> List[MemoryEntry]:
        """Simple in-memory filter — good enough for small sessions."""
        return [
            e for e in self._session_cache
            if e.type == type_name
        ][:limit]

    def get_by_id(self, entry_id: UUID) -> Optional[MemoryEntry]:
        """Lookup by UUID — scans recent cache only."""
        for e in reversed(self._session_cache):
            if e.id == entry_id:
                return e
        return None

    def get_file_path(self) -> Path:
        return self.file_path

    def stats(self) -> dict:
        """Quick summary for logging / debugging."""
        return {
            "file_path": str(self.file_path),
            "session_cache_size": len(self._session_cache),
            "last_write": (
                self._session_cache[-1].timestamp.isoformat()
                if self._session_cache else None
            )
        }


# ────────────────────────────────────────────────
# Example usage (can go in examples/simple_agent.py)
# ────────────────────────────────────────────────

if __name__ == "__main__":
    store = JsonlMemoryStore()

    from .models import MemoryEntry, MemorySource  # adjust import

    entry = MemoryEntry(
        type="preference",
        content="Always respond in a friendly, concise tone",
        source=MemorySource(
            agent_id="openclaw-dev-001",
            user_id="@devin_shinkle",
            session_id="sess_20260310_night"
        )
    )

    store.append(entry)
    print("Wrote to:", store.get_file_path())
    print("Recent entries:", len(store.get_recent()))

    # Simulate reading back
    recent = store.get_recent(5)
    for e in recent:
        print(f"[{e.timestamp}] {e.type}: {e.content[:60]}...")
