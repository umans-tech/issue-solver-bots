from dataclasses import dataclass


@dataclass(frozen=True)
class CodeRepositoryConnected:
    url: str
    access_token: str
    user_id: str
    knowledge_base_id: str
    process_id: str
