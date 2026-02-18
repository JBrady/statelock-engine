from app.services.automation_policy import (
    build_confidence_signal,
    derive_session_id,
    should_save_memory,
)


def test_session_id_mapping_and_fallback():
    assert (
        derive_session_id("telegram", "chat_123", "user_9")
        == "telegram:chat_123:user_9"
    )
    assert derive_session_id("", "", "") == "agent:chat:main"


def test_save_policy_triggers_and_skips():
    assert should_save_memory(
        user_input="We made a decision about fallback",
        model_output="Policy is local-first.",
        always_save=False,
    )
    assert not should_save_memory(
        user_input="hi",
        model_output="hello there",
        always_save=False,
    )


def test_confidence_signal():
    low = build_confidence_signal("I think maybe this could work")
    assert low["confidence_low"] is True

    ok = build_confidence_signal(
        "Use local models for standard tasks and escalate only when correctness is critical."
    )
    assert ok["confidence_low"] is False
