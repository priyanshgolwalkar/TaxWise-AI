from typing import Protocol

class KnowledgeRetriever(Protocol):
    def retrieve(self, query: str, user_id: int) -> list[dict]: ...

class EmptyKnowledgeRetriever:
    def retrieve(self, _query: str, _user_id: int) -> list[dict]:
        return []
