"""Main Chainlit application."""

import logging
import os
import re
from pathlib import Path

import chainlit as cl
import sentry_sdk

from hope_jarvis.config import (
    get_all_repo_names,
    get_ingestion_chunk_overlap,
    get_ingestion_chunk_size,
    get_ollama_base_url,
    get_ollama_model,
    get_ollama_streaming,
    get_ollama_temperature,
    get_qdrant_collection_name,
    get_qdrant_url,
    get_retrieval_score_threshold,
    get_retrieval_top_k,
)
from hope_jarvis.ingestion import (
    chunk_markdown_file,
    store_chunks_in_qdrant,
    sync_all_repos,
)
from hope_jarvis.query import retrieve_relevant_chunks

# Prompt files directory
PROMPTS_DIR = Path(__file__).parent / "prompts"


sentry_dsn = os.environ.get("SENTRY_DSN")
if sentry_dsn:
    sentry_sdk.init(
        dsn=sentry_dsn,
        environment=os.environ.get("ENVIRONMENT", "production"),
        send_default_pii=False,
    )

logger = logging.getLogger(__name__)


def load_prompts():
    """Load all prompt files from the prompts directory."""
    prompts = {}
    if not PROMPTS_DIR.exists():
        return prompts

    for md_file in sorted(PROMPTS_DIR.glob("*.md")):
        with open(md_file, encoding="utf-8") as f:
            prompts[md_file.stem] = f.read()

    return prompts


# Identity response patterns (Italian and English)
IDENTITY_PATTERNS = [
    r"chi sei\??",
    r"chi sei tu\??",
    r"cos'è jarvis\??",
    r"cos'e jarvis\??",
    r"che cosa sei\??",
    r"what are you\??",
    r"who are you\??",
    r"tell me about (yourself|jarvis)",
]


def is_identity_question(text: str) -> bool:
    """Check if the user question is about Jarvis identity."""
    text_lower = text.lower().strip()
    return any(re.search(pattern, text_lower) for pattern in IDENTITY_PATTERNS)


def get_identity_response() -> str:
    """Return the exact identity response from persona.md or fallback."""
    prompts = load_prompts()
    persona = prompts.get("persona", "")

    # Extract the exact response from persona.md (blockquote line)
    match = re.search(r"^> (I\'m Jarvis[^\n]+)", persona, re.MULTILINE)
    if match:
        return match.group(1).strip()

    # Fallback to the requested response
    return "I'm Jarvis a personal assistant for the HOPE ecosystem documentation"


def _build_config():
    return {
        "ollama": {
            "base_url": get_ollama_base_url(),
            "model": get_ollama_model(),
            "temperature": get_ollama_temperature(),
            "streaming": get_ollama_streaming(),
        },
        "qdrant": {
            "url": get_qdrant_url(),
            "collection_name": get_qdrant_collection_name(),
        },
        "retrieval": {
            "top_k": get_retrieval_top_k(),
            "score_threshold": get_retrieval_score_threshold(),
        },
        "ingestion": {
            "chunk_size": get_ingestion_chunk_size(),
            "chunk_overlap": get_ingestion_chunk_overlap(),
        },
    }


def _check_env():
    required = [
        "OLLAMA_HOST",
        "QDRANT_HOST",
        "QDRANT_COLLECTION_NAME",
        "EMBEDDING_MODEL_NAME",
        "CONFIG_PATH",
        "DATA_DIR",
    ]
    missing = [v for v in required if not os.environ.get(v)]
    if missing:
        raise RuntimeError(f"Missing env vars: {', '.join(missing)}")


# Store config in user session
@cl.on_chat_start
async def start():
    _check_env()
    cl.user_session.set("config", _build_config())
    cl.user_session.set("prompts", load_prompts())
    await cl.Message(content="Hey, I'm ready.").send()


@cl.on_message
async def main(message: cl.Message):
    import time

    try:
        config = cl.user_session.get("config")
        if config is None:
            _check_env()
            config = _build_config()
            cl.user_session.set("config", config)

        # Check for identity questions
        if is_identity_question(message.content):
            await cl.Message(content=get_identity_response()).send()
            return

        prompts = load_prompts()

        # Retrieve relevant chunks
        t0 = time.time()
        chunks = retrieve_relevant_chunks(
            query=message.content,
            qdrant_url=config["qdrant"]["url"],
            collection_name=config["qdrant"]["collection_name"],
            top_k=config["retrieval"]["top_k"],
            score_threshold=config["retrieval"]["score_threshold"],
        )
        t1 = time.time()
        logger.info(f"[TIMING] Retrieval: {t1 - t0:.2f}s | Chunks: {len(chunks)}")

        if not chunks:
            await cl.Message(content="Sorry, I cannot help you on this topic.").send()
            return

        # Prepare context for LLM
        context_parts = []
        sources = []

        for chunk in chunks:
            app_name = chunk["metadata"]["repo_name"]
            rendered_url = chunk["metadata"]["rendered_html_url"]
            content = chunk["content"]
            context_parts.append(f"App: {app_name}\nContent: {content}\nSource: {rendered_url}")
            source_info = {
                "app": app_name,
                "url": chunk["metadata"]["rendered_html_url"],
                "score": round(chunk["metadata"]["score"], 3),
            }
            if source_info not in sources:
                sources.append(source_info)

        context = "\n\n---\n\n".join(context_parts)

        # Create LLM chain
        from langchain_core.output_parsers import StrOutputParser
        from langchain_core.prompts import ChatPromptTemplate
        from langchain_ollama import ChatOllama

        llm = ChatOllama(
            base_url=config["ollama"]["base_url"],
            model=config["ollama"]["model"],
            temperature=config["ollama"]["temperature"],
            streaming=True,
        )

        repos_list = "\n".join(f"- {r}" for r in get_all_repo_names())

        common = "\n\n".join(prompts.values())

        system_prompt = """%(common)s

The HOPE ecosystem includes:
%(repos_list)s

IMPORTANT: You MUST ONLY answer questions related to the HOPE ecosystem documentation.
If a question is not about HOPE, its applications or their documentation, you MUST respond EXACTLY with:

"Sorry, I cannot help you on this topic."

Context:
{context}""" % {"common": common, "repos_list": repos_list}

        prompt = ChatPromptTemplate.from_messages(
            [
                ("system", system_prompt),
                ("human", "{question}"),
            ]
        )

        chain = prompt | llm | StrOutputParser()

        # Stream response
        msg = cl.Message(content="")
        await msg.send()

        response_text = ""
        t2 = time.time()
        async for token in chain.astream({"context": context, "question": message.content}):
            response_text += token
            await msg.stream_token(token)
        t3 = time.time()
        logger.info(f"[TIMING] LLM generation: {t3 - t2:.2f}s")

        # Store Q&A in session for feedback handling
        cl.user_session.set("last_question", message.content)
        cl.user_session.set("last_answer", response_text)
        cl.user_session.set("last_sources", sources)

        # Add sources as separate message
        if sources:
            sources_parts = []
            for s in sources:
                text = f"- **{s['app']}**: [{s['url']}]({s['url']}) (score: {s['score']})"
                sources_parts.append(text)
            sources_text = "**Sources:**\n" + "\n".join(sources_parts)
            await cl.Message(content=sources_text).send()

        # Add feedback buttons to the response message
        msg.actions = [
            cl.Action(name="satisfied", label="👍 Soddisfatto", payload={"value": "satisfied"}),
            cl.Action(name="not_satisfied", label="👎 Non soddisfatto", payload={"value": "not_satisfied"}),
        ]
        await msg.update()

    except Exception as e:
        import traceback

        error_type = type(e).__name__
        error_msg = str(e)
        logger.info(f"[ERROR] {error_type}: {error_msg}")
        logger.info(traceback.format_exc())

        # Send to Sentry (no-op if not configured)
        sentry_sdk.capture_exception(e)

        # User-friendly messages for connection errors
        if "ConnectError" in error_type or "Connection" in error_type or "HTTPConnection" in error_msg:
            await cl.Message(
                content="⚠️ Unable to connect to a required service. Please check that Ollama and Qdrant are running."
            ).send()
        else:
            await cl.Message(content="⚠️ An unexpected error occurred. The team has been notified.").send()


@cl.action_callback("satisfied")
async def on_satisfied(action: cl.Action):
    """Handle satisfied feedback - save Q&A to knowledge base."""
    from hope_jarvis.knowledge import save_qa_to_markdown

    question = cl.user_session.get("last_question", "")
    answer = cl.user_session.get("last_answer", "")
    sources = cl.user_session.get("last_sources", [])

    if question and answer:
        try:
            save_qa_to_markdown(question, answer, sources)
            await cl.Message(content="✅ Grazie! La risposta è stata salvata.").send()
        except Exception as e:
            logger.error(f"Failed to save Q&A: {e}")
            await cl.Message(content="Si è verificato un errore nel salvataggio.").send()
    else:
        await cl.Message(content="Errore: impossibile recuperare la domanda o la risposta.").send()

    await action.remove()


@cl.action_callback("not_satisfied")
async def on_not_satisfied(action: cl.Action):
    """Handle not satisfied feedback."""
    await cl.Message(content="Mi dispiace. Come posso aiutarti meglio?").send()
    await action.remove()


@cl.on_chat_end
def end():
    pass


# Ingestion command (can be triggered via Chainlit action if needed)
async def run_ingestion():
    """Run full ingestion pipeline."""
    config = cl.user_session.get("config")

    # Get chunk size and overlap from config
    from hope_jarvis.config import get_ingestion_chunk_overlap, get_ingestion_chunk_size

    chunk_size = get_ingestion_chunk_size()
    chunk_overlap = get_ingestion_chunk_overlap()

    # Sync repos
    changed_files = sync_all_repos()

    if not changed_files:
        return "Nessun file aggiornato."

    # Process each changed file
    all_chunks = []
    for file_info in changed_files:
        chunks = chunk_markdown_file(
            file_path=file_info["full_path"],
            relative_file_path=file_info["file_path"],
            repo_name=file_info["repo_name"],
            github_url=file_info["github_url"],
            rendered_base_url=file_info["rendered_base_url"],
            docs_dir=file_info["docs_dir"],
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
        )
        all_chunks.extend(chunks)

    # Store in Qdrant
    store_chunks_in_qdrant(
        chunks=all_chunks,
        qdrant_url=config["qdrant"]["url"],
        collection_name=config["qdrant"]["collection_name"],
    )

    n_chunks = len(all_chunks)
    n_files = len(changed_files)
    return f"Ingestion completata: {n_chunks} chunks da {n_files} file."
