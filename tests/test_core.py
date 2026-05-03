from hope_jarvis.core import DocumentationSource, HopeBot


class MockSource(DocumentationSource):
    def query(self, text: str) -> str:
        return f"Results for '{text}' from {self.name}"


def test_bot_can_register_source():
    bot = HopeBot()
    source = MockSource(name="App1", url="https://docs.app1.hope.org")
    bot.register_source(source)
    assert len(bot.sources) == 1
    assert bot.sources[0].name == "App1"


def test_bot_queries_sources():
    bot = HopeBot()
    source1 = MockSource(name="App1", url="https://docs.app1.hope.org")
    source2 = MockSource(name="App2", url="https://docs.app2.hope.org")
    bot.register_source(source1)
    bot.register_source(source2)

    responses = bot.query_all("how to login")
    assert "Results for 'how to login' from App1" in responses
    assert "Results for 'how to login' from App2" in responses
