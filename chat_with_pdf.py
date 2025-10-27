"""
INFO 5940 011
Assignment 1
Yuqing Sun
ys2434
"""

import streamlit as st
import os
from openai import OpenAI
from os import environ

from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain.schema import Document
from langchain_community.vectorstores import Chroma
from langchain_openai import OpenAIEmbeddings

client = OpenAI(
    api_key=os.environ["API_KEY"],
    base_url="https://api.ai.it.cornell.edu",
)
CHAT_MODEL = os.environ.get("OPENAI_CHAT_MODEL", "openai.gpt-4o")

# App setup
st.title("📝 File Q&A with OpenAI")

# Helper functions
def ensure_dir(path):
    if not os.path.exists(path):
        os.makedirs(path, exist_ok=True)

def save_uploaded_file(uploaded_file):
    ensure_dir("uploaded_files")
    temp_path = os.path.join("uploaded_files", uploaded_file.name)
    with open(temp_path, "wb") as f:
        f.write(uploaded_file.getbuffer())
    return temp_path

def load_documents(files):
    docs = []
    for f in files:
        name = f.name.lower()
        if name.endswith(".txt") or name.endswith(".md"):
            content = f.read().decode("utf-8", errors="ignore")
            docs.append(Document(page_content=content, metadata={"source": f.name}))
        elif name.endswith(".pdf"):
            tmp_path = save_uploaded_file(f)
            loader = PyPDFLoader(tmp_path)
            loaded = loader.load()
            for d in loaded:
                d.metadata["source"] = f.name
            docs.extend(loaded)
        else:
            st.warning(f"Unsupported file type: {f.name}")
    return docs

def split_documents(docs, chunk_size=1200, chunk_overlap=150):
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        separators=["\n\n", "\n", " ", ""]
    )
    return splitter.split_documents(docs)

def build_vectorstore(embed_model="openai.text-embedding-3-small", persist_dir=".chroma_store"):
    ensure_dir(persist_dir)
    # Force the embedding call to use Cornell’s base URL and API key
    embeddings = OpenAIEmbeddings(
        model=embed_model,
        openai_api_key=os.environ["API_KEY"],
        openai_api_base="https://api.ai.it.cornell.edu/v1",   # <- note the /v1
    )
    return Chroma(
        embedding_function=embeddings,
        persist_directory=persist_dir,
        collection_name="rag_docs",
    )

def add_to_vectorstore(vdb, chunks):
    if chunks:
        vdb.add_documents(chunks)
        vdb.persist()
    return len(chunks)

def retrieve_context(vdb, question, k=4):
    retriever = vdb.as_retriever(search_kwargs={"k": k})
    results = retriever.get_relevant_documents(question)
    context = "\n\n".join([d.page_content for d in results])
    return context, results

def format_sources(docs):
    refs = []
    for d in docs:
        src = d.metadata.get("source", "unknown")
        page = d.metadata.get("page")
        refs.append(f"{src} (page {page})" if page else src)
    return list(dict.fromkeys(refs))


# Streamlit interface
uploaded_files = st.file_uploader(
    "Upload your documents (.txt, .md, .pdf)", type=("txt", "md", "pdf"), accept_multiple_files=True
)

question = st.chat_input(
    "Ask something about the uploaded files",
    disabled=not uploaded_files,
)

if "messages" not in st.session_state:
    st.session_state["messages"] = [
        {"role": "assistant", "content": "Ask something about your uploaded files."}
    ]

# Display chat history
for msg in st.session_state.messages:
    st.chat_message(msg["role"]).write(msg["content"])

if question and uploaded_files:
    st.session_state.messages.append({"role": "user", "content": question})
    st.chat_message("user").write(question)

    # Build or load vector store
    vdb = build_vectorstore()
    if "indexed" not in st.session_state:
        with st.spinner("Indexing uploaded files..."):
            docs = load_documents(uploaded_files)
            chunks = split_documents(docs)
            add_to_vectorstore(vdb, chunks)
        st.session_state["indexed"] = True
        st.success(f"Indexed {len(chunks)} chunks from {len(uploaded_files)} file(s).")

    with st.spinner("Retrieving relevant chunks..."):
        context_text, retrieved = retrieve_context(vdb, question, k=4)

    # Retrieve context for the question
    with st.chat_message("assistant"):
        resp = client.chat.completions.create(
            model=CHAT_MODEL,
            messages=[
                {"role": "system", "content": f"Here are the relevant document chunks:\n\n{context_text}"},
                *st.session_state.messages
            ],
            stream=False,  # <— turn off streaming
        )
        response = resp.choices[0].message.content
        st.markdown(response)


    # Append assistant’s response
    st.session_state.messages.append({"role": "assistant", "content": response})

    # Display sources
    refs = format_sources(retrieved)
    if refs:
        st.caption("Sources:\n" + "\n".join(["- " + r for r in refs]))