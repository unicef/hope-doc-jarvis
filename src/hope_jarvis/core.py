"""Core module for HOPE Bot - maintains compatibility with existing tests."""

from typing import List


class DocumentationSource:
    """Base class for documentation sources."""

    def __init__(self, name: str, url: str):
        self.name = name
        self.url = url

    def query(self, text: str) -> str:
        """Query the documentation source."""
        raise NotImplementedError


class HopeBot:
    """Main bot class that manages documentation sources."""

    def __init__(self):
        self.sources: List[DocumentationSource] = []

    def register_source(self, source: DocumentationSource) -> None:
        """Register a documentation source."""
        self.sources.append(source)

    def query_all(self, text: str) -> List[str]:
        """Query all registered sources."""
        return [source.query(text) for source in self.sources]
