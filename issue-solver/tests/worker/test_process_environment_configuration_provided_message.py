from unittest.mock import Mock

import pytest
from morphcloud.api import MorphCloudClient

from tests.controllable_clock import ControllableClock
from tests.examples.happy_path_persona import BriceDeNice
from issue_solver.events.domain import EnvironmentConfigurationValidated
from issue_solver.events.event_store import EventStore
from issue_solver.worker.messages_processing import process_event_message
from issue_solver.worker.solving.process_issue_resolution_request import Dependencies


@pytest.mark.asyncio
async def test_process_environment_configuration_provided_message_should_produce_environment_configuration_validated_event(
    event_store: EventStore, time_under_control: ControllableClock
):
    # Given
    microvm_client = Mock(spec=MorphCloudClient)
    config_provided = BriceDeNice.got_his_environment_configuration_provided()
    config_process_id = config_provided.process_id
    await event_store.append(config_process_id, config_provided)

    # When
    await process_event_message(
        config_provided,
        dependencies=Dependencies(
            event_store,
            Mock(),
            Mock(),
            time_under_control,
            microvm_client,
            is_dev_environment_service_enabled=True,
        ),
    )

    # Then
    produced_events = await event_store.get(config_process_id)

    assert produced_events == [
        config_provided,
        EnvironmentConfigurationValidated(
            process_id=config_process_id,
            occurred_at=time_under_control.now(),
            snapshot_id="brice-env-001-snap-001",
            stdout="environment setup completed successfully",
            stderr="no errors",
            return_code=0,
        ),
    ]
