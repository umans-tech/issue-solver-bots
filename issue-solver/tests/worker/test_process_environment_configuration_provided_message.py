from unittest.mock import Mock

import pytest
from morphcloud.api import MorphCloudClient, Snapshot

from tests.controllable_clock import ControllableClock
from tests.examples.happy_path_persona import BriceDeNice
from tests.worker.test_process_issue_resolution_requested_message import to_script
from issue_solver.events.domain import (
    EnvironmentConfigurationValidated,
    EnvironmentValidationFailed,
)
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
    repo_connected = BriceDeNice.got_his_first_repo_connected()
    await event_store.append(
        repo_connected.process_id,
        repo_connected,
    )
    await event_store.append(config_process_id, config_provided)

    base_snapshot = Mock(spec=Snapshot)
    microvm_client.snapshots.list.return_value = [base_snapshot]
    prepared_snapshot = Mock()
    prepared_snapshot.id = "brice-env-001-snap-001"
    base_snapshot.exec.return_value = prepared_snapshot

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
    microvm_client.snapshots.list.assert_called_with(
        metadata={
            "type": "base",
        }
    )

    prepare_settings = f"""
export PROCESS_ID=\'{config_provided.process_id}\'
export REPO_PATH=\'nice-repo\'
export URL=\'{repo_connected.url}\'
export ACCESS_TOKEN=\'{repo_connected.access_token}\'
export INSTALL_SCRIPT=\'{config_provided.project_setup}\'
"""

    base_snapshot.exec.assert_called_once_with(
        to_script(
            command="cudu prepare",
            dotenv_settings=prepare_settings,
            global_setup_script=config_provided.global_setup,
        )
    )
    prepared_snapshot.set_metadata.assert_called_once_with(
        {
            "type": "dev",
            "knowledge_base_id": repo_connected.knowledge_base_id,
            "environment_id": config_provided.environment_id,
        }
    )


@pytest.mark.asyncio
async def test_process_environment_configuration_provided_message_should_produce_environment_configuration_validation_failed(
    event_store: EventStore, time_under_control: ControllableClock
):
    # Given
    microvm_client = Mock(spec=MorphCloudClient)
    config_provided = BriceDeNice.got_his_environment_configuration_provided()
    config_process_id = config_provided.process_id
    repo_connected = BriceDeNice.got_his_first_repo_connected()
    await event_store.append(
        repo_connected.process_id,
        repo_connected,
    )
    await event_store.append(config_process_id, config_provided)

    base_snapshot = Mock(spec=Snapshot)
    microvm_client.snapshots.list.return_value = [base_snapshot]
    prepared_snapshot = Mock()
    prepared_snapshot.id = "brice-env-001-snap-001"
    base_snapshot.exec.side_effect = Exception("VM crashed")

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
        EnvironmentValidationFailed(
            process_id=config_process_id,
            occurred_at=time_under_control.now(),
            stdout="",
            stderr="VM crashed",
            return_code=1,
        ),
    ]
    microvm_client.snapshots.list.assert_called_with(
        metadata={
            "type": "base",
        }
    )

    prepare_settings = f"""
export PROCESS_ID=\'{config_provided.process_id}\'
export REPO_PATH=\'nice-repo\'
export URL=\'{repo_connected.url}\'
export ACCESS_TOKEN=\'{repo_connected.access_token}\'
export INSTALL_SCRIPT=\'{config_provided.project_setup}\'
"""

    base_snapshot.exec.assert_called_once_with(
        to_script(
            command="cudu prepare",
            dotenv_settings=prepare_settings,
            global_setup_script=config_provided.global_setup,
        )
    )
