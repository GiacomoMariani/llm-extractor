import os
from typing import Any

import requests
import streamlit as st
from dotenv import load_dotenv


load_dotenv()

API_URL = os.getenv("API_BASE_URL", "http://localhost:8000").rstrip("/")
API_KEY = os.getenv("APP_API_KEY", "")
HEADERS = {"X-API-Key": API_KEY} if API_KEY else {}


SAMPLE_QUESTIONS = [
    "Which customer orders are ready to ship?",
    "Who coordinates invoice and order follow-up?",
    "Who reviews citation quality and fallback cases?",
    "How many remote work days are allowed each week?",
    "Who approves expenses above 500 euros?",
    "Which package includes monthly reporting?",
    "Is custom integration included in the starter plan?",
    "What support options are available for delivery questions?",
    "What are the main steps in the chatbot workflow?",
    "Which information is not included in the demo documents?",
]


st.set_page_config(
    page_title="Business RAG Chatbot",
    page_icon="💬",
    layout="wide",
)

st.title("Business RAG Chatbot")

st.info(
    "Demo environment: this page is for testing only. "
    "Do not upload confidential, personal, financial, legal, or sensitive business data."
)


def api_request(
    method: str,
    path: str,
    *,
    timeout: int = 15,
    **kwargs: Any,
) -> dict[str, Any]:
    if not API_KEY:
        raise RuntimeError("Missing APP_API_KEY in .env")

    response = requests.request(
        method=method,
        url=f"{API_URL}{path}",
        headers=HEADERS,
        timeout=timeout,
        **kwargs,
    )

    if response.status_code == 401:
        raise RuntimeError("Unauthorized. Check APP_API_KEY in .env.")

    if response.status_code == 403:
        try:
            detail = response.json().get("detail", "Action not allowed.")
        except ValueError:
            detail = "Action not allowed."
        raise RuntimeError(detail)

    response.raise_for_status()

    if not response.content:
        return {}

    return response.json()


def get_docs() -> list[dict[str, Any]]:
    return api_request("GET", "/documents")["documents"]


def ask_docs(question: str) -> dict[str, Any]:
    return api_request(
        "POST",
        "/documents/ask",
        json={
            "question": question,
            "top_k": 3,
        },
        timeout=30,
    )


def upload_doc(uploaded_file) -> dict[str, Any]:
    files = {
        "file": (
            uploaded_file.name,
            uploaded_file.getvalue(),
            uploaded_file.type or "application/octet-stream",
        )
    }

    return api_request(
        "POST",
        "/documents/upload",
        files=files,
        timeout=60,
    )


def reindex_doc(doc_id: str) -> dict[str, Any]:
    return api_request(
        "POST",
        f"/documents/{doc_id}/reindex",
        timeout=15,
    )


def delete_doc(doc_id: str) -> dict[str, Any]:
    return api_request(
        "DELETE",
        f"/documents/{doc_id}",
        timeout=15,
    )


def get_logs(limit: int = 10) -> list[dict[str, Any]]:
    return api_request(
        "GET",
        "/admin/document-query-logs",
        params={"limit": limit},
        timeout=15,
    )["logs"]


def submit_question(question: str) -> None:
    cleaned_question = question.strip()

    if not cleaned_question:
        return

    try:
        result = ask_docs(cleaned_question)

        answer_item = {
            "question": cleaned_question,
            "answer": result.get("answer", ""),
            "was_fallback": result.get("was_fallback", False),
            "citations": result.get("citations", []),
        }

        st.session_state["latest_answer"] = answer_item
        st.session_state["chat"].append(answer_item)
        st.session_state.pop("logs", None)

    except (requests.RequestException, RuntimeError) as exc:
        st.error(f"Could not get an answer: {exc}")


def show_sources(citations: list[dict[str, Any]]) -> None:
    if not citations:
        return

    st.markdown("#### Sources")

    for cite in citations:
        page = cite.get("page_number")
        page_text = f", page {page}" if page else ""
        title = f"{cite.get('filename', 'Unknown source')}{page_text}"

        with st.expander(title):
            st.write(cite.get("snippet", "No snippet available."))

            score = cite.get("hybrid_score")
            if score is not None:
                st.caption(f"Retrieval score: {score:.3f}")


def render_doc_rows(
    docs: list[dict[str, Any]],
    *,
    allow_delete: bool,
) -> None:
    if not docs:
        st.info("No documents in this layer.")
        return

    for doc in docs:
        info_col, action_col = st.columns([5, 2])

        with info_col:
            page_count = doc.get("page_count")
            page_text = f" — {page_count} pages" if page_count else ""

            st.write(
                f"**{doc['filename']}** — "
                f"{doc['status']} — "
                f"{doc['chunk_count']} chunks"
                f"{page_text}"
            )

        with action_col:
            if st.button("Re-index", key=f"reindex-{doc['document_id']}"):
                try:
                    reindex_doc(doc["document_id"])
                    st.session_state.pop("docs", None)
                    st.success(f"Queued re-index for {doc['filename']}")
                    st.rerun()
                except (requests.RequestException, RuntimeError) as exc:
                    st.error(f"Could not re-index document: {exc}")

            if allow_delete:
                if st.button("Delete", key=f"delete-{doc['document_id']}"):
                    try:
                        delete_doc(doc["document_id"])
                        st.session_state.pop("docs", None)
                        st.success(f"Deleted {doc['filename']}")
                        st.rerun()
                    except (requests.RequestException, RuntimeError) as exc:
                        st.error(f"Could not delete document: {exc}")
            else:
                st.caption("Protected demo document")


if not API_KEY:
    st.error("Missing APP_API_KEY in .env")
    st.stop()


if "chat" not in st.session_state:
    st.session_state["chat"] = []

if "latest_answer" not in st.session_state:
    st.session_state["latest_answer"] = None


# ---------------------------------------------------------------------
# Chat
# ---------------------------------------------------------------------

st.markdown("## Chat with the knowledge base")

st.caption(
    "Ask a question here. The chatbot searches across both document layers: "
    "the preloaded demo knowledge base and your temporary uploaded documents."
)

with st.form("chat-form", clear_on_submit=True):
    question = st.text_input(
        "Your question",
        placeholder="Example: Which invoice is overdue?",
    )
    submitted = st.form_submit_button("Ask the chatbot")

if submitted:
    submit_question(question)

if st.session_state["latest_answer"]:
    latest = st.session_state["latest_answer"]

    st.markdown("### Chatbot answer")
    st.markdown(f"**Question:** {latest['question']}")

    if latest["was_fallback"]:
        st.warning(latest["answer"])
    else:
        st.success("Answer found in the knowledge base.")
        st.write(latest["answer"])

    show_sources(latest["citations"])


st.markdown("### Suggested demo questions")
st.caption(
    "Use these to quickly test citations, fallback behavior, "
    "and retrieval across different documents."
)

for index, sample_question in enumerate(SAMPLE_QUESTIONS, start=1):
    question_col, button_col = st.columns([6, 1])

    with question_col:
        st.write(f"{index}. {sample_question}")

    with button_col:
        if st.button("Ask", key=f"sample-question-{index}"):
            submit_question(sample_question)
            st.rerun()


if len(st.session_state["chat"]) > 1:
    st.markdown("### Previous conversation")

    if st.button("Clear chat"):
        st.session_state["chat"] = []
        st.session_state["latest_answer"] = None
        st.rerun()

    for item in reversed(st.session_state["chat"][:-1]):
        st.markdown(f"**Question:** {item['question']}")

        if item["was_fallback"]:
            st.warning(item["answer"])
        else:
            st.write(item["answer"])

        show_sources(item["citations"])
        st.divider()


# ---------------------------------------------------------------------
# Document layers
# ---------------------------------------------------------------------

st.markdown("## Document sources")

st.caption(
    "This environment has two document layers: "
    "preloaded demo documents that are always available, "
    "and temporary user-uploaded documents for local testing."
)

if st.button("Refresh documents"):
    st.session_state.pop("docs", None)

try:
    if "docs" not in st.session_state:
        st.session_state["docs"] = get_docs()

    docs = st.session_state["docs"]

    demo_docs = [doc for doc in docs if doc.get("is_demo")]
    user_docs = [doc for doc in docs if not doc.get("is_demo")]

    st.markdown("### Layer 1: Preloaded demo knowledge base")
    st.caption(
        "These fictional demo documents are bundled with the app, "
        "loaded automatically from the demo folder, and protected from deletion."
    )
    render_doc_rows(demo_docs, allow_delete=False)

    st.markdown("### Layer 2: Temporary user uploads")
    st.caption(
        "These are documents uploaded during local testing. "
        "They can be re-indexed or deleted."
    )

    uploaded_file = st.file_uploader(
        "Upload a temporary test document",
        type=["txt", "md", "pdf"],
    )

    if uploaded_file and st.button("Upload temporary document"):
        try:
            upload_doc(uploaded_file)
            st.session_state.pop("docs", None)
            st.success("Temporary document uploaded successfully.")
            st.rerun()
        except (requests.RequestException, RuntimeError) as exc:
            st.error(f"Could not upload document: {exc}")

    render_doc_rows(user_docs, allow_delete=True)

except (requests.RequestException, RuntimeError) as exc:
    st.error(f"Could not load documents: {exc}")


# ---------------------------------------------------------------------
# Admin query logs
# ---------------------------------------------------------------------

st.markdown("## Recent query logs")

if st.button("Refresh logs"):
    st.session_state.pop("logs", None)

try:
    if "logs" not in st.session_state:
        st.session_state["logs"] = get_logs()

    logs = st.session_state["logs"]

    if not logs:
        st.info("No query logs yet.")
    else:
        for log in logs:
            status = "Fallback" if log["was_fallback"] else "Answered"

            with st.expander(f"{status} — {log['question']}"):
                st.write(f"**Answer:** {log['answer']}")
                st.write(f"**Citations:** {log['citation_count']}")
                st.write(f"**Latency:** {log['latency_ms']:.2f} ms")

                sources = log.get("retrieved_sources", [])

                if sources:
                    st.markdown("**Retrieved sources**")

                    for source in sources:
                        page = source.get("page_number")
                        page_text = f", page {page}" if page else ""
                        score = source.get("hybrid_score")
                        filename = source.get("filename", "Unknown source")

                        if score is None:
                            st.write(f"- {filename}{page_text}")
                        else:
                            st.write(
                                f"- {filename}{page_text} "
                                f"(score: {score:.3f})"
                            )

except (requests.RequestException, RuntimeError) as exc:
    st.error(f"Could not load query logs: {exc}")