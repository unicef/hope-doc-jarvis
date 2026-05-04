"""Response generation module."""

from typing import Any

from hope_jarvis.config import (
    get_ollama_base_url,
    get_ollama_model,
    get_ollama_streaming,
    get_ollama_temperature,
)


def _build_ollama_config():
    return {
        "base_url": get_ollama_base_url(),
        "model": get_ollama_model(),
        "temperature": get_ollama_temperature(),
        "streaming": get_ollama_streaming(),
    }


def create_llm_chain(config: dict):
    """Create LangChain LLM chain with Ollama."""
    from langchain_core.output_parsers import StrOutputParser
    from langchain_core.prompts import ChatPromptTemplate
    from langchain_ollama import ChatOllama

    ollama_config = config["ollama"]

    llm = ChatOllama(
        base_url=ollama_config["base_url"],
        model=ollama_config["model"],
        temperature=ollama_config["temperature"],
        streaming=ollama_config["streaming"],
    )

    # Prompt template with instruction to cite rendered HTML URLs
    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                """You are a helpful assistant for the HOPE ecosystem.
The HOPE ecosystem includes multiple applications: HOPE, Country Report, Country Workspace, and Aurora.

Use the following context from HOPE documentation to answer the user's question.
Each context entry includes an "App:" field indicating which application the content belongs to.

When citing sources, ALWAYS use this format: **[App Name](url)**
Example: **[Aurora](https://aurora.docs.example.com/guide/)** or **[HOPE](https://hope.docs.example.com/setup/)**

Never use generic "[Source: url]" format. Always include the app name in bold before the link.
If you don't have enough information in the context, say so.

Context:
{context}

User question: {question}""",
            ),
            ("human", "{question}"),
        ]
    )

    return prompt | llm | StrOutputParser()


def generate_response(query: str, relevant_chunks: list[dict[str, Any]], config: dict = None) -> str:
    """Generate response using LLM with context."""
    if config is None:
        config = {"ollama": _build_ollama_config()}

    chain = create_llm_chain(config)

    # Prepare context from chunks
    context_parts = []
    for chunk in relevant_chunks:
        app_name = chunk["metadata"].get("repo_name", "Unknown")
        context_part = f"App: {app_name}\nContent: {chunk['content']}\nSource: {chunk['metadata']['rendered_html_url']}"
        context_parts.append(context_part)

    context = "\n\n---\n\n".join(context_parts)

    # Generate response
    return chain.invoke({"context": context, "question": query})


def generate_response_stream(query: str, relevant_chunks: list[dict[str, Any]], config: dict = None):
    """Generate streaming response using LLM with context."""
    if config is None:
        config = {"ollama": _build_ollama_config()}

    chain = create_llm_chain(config)

    # Prepare context from chunks
    context_parts = []
    for chunk in relevant_chunks:
        app_name = chunk["metadata"].get("repo_name", "Unknown")
        context_part = f"App: {app_name}\nContent: {chunk['content']}\nSource: {chunk['metadata']['rendered_html_url']}"
        context_parts.append(context_part)

    context = "\n\n---\n\n".join(context_parts)

    # Stream response
    yield from chain.stream({"context": context, "question": query})
