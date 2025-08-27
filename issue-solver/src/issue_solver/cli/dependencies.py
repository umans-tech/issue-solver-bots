from issue_solver.agents.issue_resolving_agent import IssueResolvingAgent
from issue_solver.agents.supported_agents import SupportedAgent
from issue_solver.cli.solve_command_settings import SolveCommandSettings
from issue_solver.clock import UTCSystemClock, Clock
from issue_solver.events.event_store import EventStore
from issue_solver.factories import init_event_store, init_agent_message_store
from issue_solver.git_operations.git_helper import GitClient


class Dependencies:
    def __init__(
        self,
        event_store: EventStore,
        git_client: GitClient,
        coding_agent: IssueResolvingAgent,
        clock: Clock,
    ):
        self._event_store = event_store
        self.git_client = git_client
        self.coding_agent = coding_agent
        self.clock = clock

    @property
    def event_store(self) -> EventStore:
        return self._event_store


async def init_command_dependencies(settings: SolveCommandSettings) -> Dependencies:
    database_url = settings.database_url
    queue_url = settings.process_queue_url
    agent_message_store = await init_agent_message_store(
        database_url, settings.redis_url
    )
    agent = SupportedAgent.get(
        settings.agent,
        settings.model_settings,
        agent_messages=agent_message_store,
    )
    git_client = GitClient()
    clock = UTCSystemClock()
    event_store = await init_event_store(
        database_url=database_url,
        queue_url=queue_url,
        webhook_base_url=settings.webhook_base_url,
    )
    return Dependencies(
        coding_agent=agent,
        git_client=git_client,
        clock=clock,
        event_store=event_store,
    )
