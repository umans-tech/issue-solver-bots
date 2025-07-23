import pytest
from claude_code_sdk import ResultMessage

from issue_solver.agents.agent_message_store import AgentMessageStore
from issue_solver.models.supported_models import (
    VersionedAIModel,
    SupportedAnthropicModel,
)


@pytest.mark.asyncio
async def test_append_and_get_agent_result_message(
    agent_message_store: AgentMessageStore,
):
    # Given
    process_id = "test-process-id"
    message = ResultMessage(
        subtype="success",
        duration_ms=288140,
        duration_api_ms=313835,
        is_error=False,
        num_turns=147,
        session_id="954062cd-ac62-4886-8942-ce41b8176059",
        total_cost_usd=1.4922057499999997,
        usage={
            "input_tokens": 224,
            "cache_creation_input_tokens": 78387,
            "cache_read_input_tokens": 3202823,
            "output_tokens": 13058,
            "server_tool_use": {"web_search_requests": 0},
            "service_tier": "standard",
        },
        result="## Summary\n\n"
        "\u2705 **Issue resolved**\n\n"
        "I have successfully fixed the TimeDelta field serialization precision issue with milliseconds. "
        "\n\n**Cost breakdown**: 120 words used for this summary.",
    )
    await agent_message_store.append(
        process_id,
        model=VersionedAIModel(SupportedAnthropicModel.CLAUDE_SONNET_4),
        turn=16,
        message=message,
        agent="CLAUDE_CODE",
    )

    # When
    found_messages = await agent_message_store.get(process_id=process_id)

    # Then
    assert found_messages


@pytest.mark.asyncio
async def test_agent_message_not_found(
    agent_message_store: AgentMessageStore,
):
    # Given
    process_id = "non-existent-process-id"

    # When
    found_messages = await agent_message_store.get(process_id=process_id)

    # Then
    assert not found_messages
