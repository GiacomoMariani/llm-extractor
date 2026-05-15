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


if not API_KEY:
    st.error("Missing APP_API_KEY in .env")
    st.stop()


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
            st.write(
                f"**{doc['filename']}** — "
                f"{doc['status']} — "
                f"{doc['chunk_count']} chunks"
            )

except requests.RequestException as exc:
    st.error(f"Could not load documents: {exc}")


st.divider()

st.subheader("Ask a question")

question = st.text_input(
    "Question",
    placeholder="Ask something from the uploaded documents",
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
