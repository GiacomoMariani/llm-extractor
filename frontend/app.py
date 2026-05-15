import os

import requests
import streamlit as st
from dotenv import load_dotenv


load_dotenv()

API_URL = os.getenv("API_BASE_URL", "http://localhost:8000")
API_KEY = os.getenv("APP_API_KEY", "")

HEADERS = {"X-API-Key": API_KEY} if API_KEY else {}


st.set_page_config(page_title="Business RAG Chatbot", page_icon="💬")

st.title("Business RAG Chatbot")
st.info(
    "Demo environment: this page is for testing only. "
    "Do not upload confidential, personal, financial, legal, or sensitive business data."
)


def get_docs():
    res = requests.get(
        f"{API_URL}/documents",
        headers=HEADERS,
        timeout=10,
    )
    res.raise_for_status()
    return res.json()["documents"]


def ask_docs(question: str):
    res = requests.post(
        f"{API_URL}/documents/ask",
        headers=HEADERS,
        json={
            "question": question,
            "top_k": 3,
        },
        timeout=30,
    )
    res.raise_for_status()
    return res.json()

def delete_doc(doc_id: str):
    res = requests.delete(
        f"{API_URL}/documents/{doc_id}",
        headers=HEADERS,
        timeout=10,
    )
    res.raise_for_status()
    return res.json()

def reindex_doc(doc_id: str):
    res = requests.post(
        f"{API_URL}/documents/{doc_id}/reindex",
        headers=HEADERS,
        timeout=10,
    )
    res.raise_for_status()
    return res.json()

def get_logs(limit: int = 10):
    res = requests.get(
        f"{API_URL}/admin/document-query-logs",
        headers=HEADERS,
        params={"limit": limit},
        timeout=10,
    )
    res.raise_for_status()
    return res.json()["logs"]

if not API_KEY:
    st.error("Missing APP_API_KEY in .env")
    st.stop()

st.subheader("Upload document")

uploaded_file = st.file_uploader(
    "Choose a document",
    type=["txt", "md", "pdf"],
)

if uploaded_file and st.button("Upload"):
    try:
        files = {
            "file": (
                uploaded_file.name,
                uploaded_file.getvalue(),
                uploaded_file.type or "application/octet-stream",
            )
        }

        res = requests.post(
            f"{API_URL}/documents/upload",
            headers=HEADERS,
            files=files,
            timeout=60,
        )
        res.raise_for_status()

        st.session_state["docs"] = get_docs()
        st.success("Document uploaded successfully.")

    except requests.RequestException as exc:
        st.error(f"Could not upload document: {exc}")

st.subheader("Indexed documents")

if st.button("Refresh documents"):
    st.session_state.pop("docs", None)

try:
    if "docs" not in st.session_state:
        st.session_state["docs"] = get_docs()

    docs = st.session_state["docs"]

    if not docs:
        st.info("No documents indexed yet.")
    else:
        for doc in docs:
            info_col, action_col = st.columns([4, 1])

            with info_col:
                st.write(
                    f"**{doc['filename']}** — "
                    f"{doc['status']} — "
                    f"{doc['chunk_count']} chunks"
                )

            with action_col:
                if st.button("Re-index", key=f"reindex-{doc['document_id']}"):
                    try:
                        reindex_doc(doc["document_id"])
                        st.session_state["docs"] = get_docs()
                        st.success(f"Queued re-index for {doc['filename']}")
                        st.rerun()
                    except requests.RequestException as exc:
                        st.error(f"Could not re-index document: {exc}")

                if st.button("Delete", key=f"delete-{doc['document_id']}"):
                    try:
                        delete_doc(doc["document_id"])
                        st.session_state["docs"] = get_docs()
                        st.success(f"Deleted {doc['filename']}")
                        st.rerun()
                    except requests.RequestException as exc:
                        st.error(f"Could not delete document: {exc}")

except requests.RequestException as exc:
    st.error(f"Could not load documents: {exc}")


st.divider()

st.subheader("Ask a question")

st.info(
    """
    Try asking:
    - Which invoice is overdue?
    - Who handles invoice disputes?
    - Who reviews citation quality and fallback cases?
    - How many remote work days are allowed each week?
    - Who approves expenses above 500 euros?
    - Which package includes monthly reporting?
    - Is custom integration included in the starter plan?
    - What should a customer do if an item arrives damaged?
    - What are the main steps in the chatbot workflow?
    - What is the real company bank account?
    """
)

question = st.text_input(
    "Question",
    placeholder="You my write the question here and then click the button below",
)

if st.button("Ask") and question.strip():
    try:
        result = ask_docs(question.strip())

        st.markdown("### Answer")
        st.write(result["answer"])

        if result.get("was_fallback"):
            st.warning("The answer was not found in the uploaded documents.")

        citations = result.get("citations", [])

        if citations:
            st.markdown("### Sources")

            for cite in citations:
                page = cite.get("page_number")
                page_text = f", page {page}" if page else ""

                with st.expander(f"{cite['filename']}{page_text}"):
                    st.write(cite["snippet"])

    except requests.RequestException as exc:
        st.error(f"Could not get an answer: {exc}")

st.divider()

st.subheader("Recent query logs")

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
                st.write(f"**Latency:** {log['latency_ms']} ms")

                sources = log.get("retrieved_sources", [])

                if sources:
                    st.markdown("**Retrieved sources**")

                    for source in sources:
                        page = source.get("page_number")
                        page_text = f", page {page}" if page else ""

                        st.write(
                            f"- {source['filename']}{page_text} "
                            f"(score: {source['hybrid_score']:.3f})"
                        )

except requests.RequestException as exc:
    st.error(f"Could not load query logs: {exc}")