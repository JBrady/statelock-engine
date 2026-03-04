from __future__ import annotations

from app.db.init_db import init_db
from app.db.session import SessionLocal
from app.db.models import Conversation, Turn


def main() -> None:
    init_db()
    db = SessionLocal()
    try:
        c = Conversation(title="Demo conversation")
        db.add(c)
        db.flush()

        db.add_all(
            [
                Turn(conversation_id=c.conversation_id, speaker="user", text="How do I debug packet loss in my home network?", thread_hint="networking"),
                Turn(conversation_id=c.conversation_id, speaker="assistant", text="Start with ping and traceroute baselines.", thread_hint="networking"),
                Turn(conversation_id=c.conversation_id, speaker="user", text="Explain cosmic microwave background anisotropy.", thread_hint="cosmology"),
                Turn(conversation_id=c.conversation_id, speaker="assistant", text="It encodes early universe density fluctuations.", thread_hint="cosmology"),
            ]
        )
        db.commit()
        print(c.conversation_id)
    finally:
        db.close()


if __name__ == "__main__":
    main()
