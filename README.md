# Retrieval-Augmented Generation (RAG) Application

### Course: INFO 5940 011
### Assignment 1 
### Author: *Yuqing Sun* 
### netID: *ys2434* 

---

## Project Overview

This project develop a Retrieval-Augmented Generation (RAG) application using LangChain and Streamlit on the platform of Codespace. 
The app allows users to upload multiple `.txt`, `.md`, and `.pdf` documents, chunk and embed them using ChromaDB, and then query their content via a conversational interface.
All queries are grounded in the retrieved document content, ensuring factually relevant responses.  

---

##  Features

~ Upload multiple files (`.txt`, `.md`, `.pdf`)  
~ Automatic document chunking and embedding via ChromaDB  
~ Retrieval-Augmented answers grounded in uploaded documents  
~ Conversational chat interface with multi-turn context  

---

##  Architecture

| Component | Description |
|------------|--------------|
| **Frontend** | Built in Streamlit, providing a simple chat UI for uploading files and asking questions. |
| **LLM Backend** | Powered by OpenAI-compatible models via the Cornell API Gateway. |
| **Retrieval Layer** | LangChain with Chroma as the vector database for storing and retrieving document embeddings. |
| **Chunking** | Uses `RecursiveCharacterTextSplitter` to break large documents into manageable text pieces for efficient retrieval. |

---

##  Setup Instructions (Codespace)

### 1. Clone or open the provided Codespace

```bash
git clone https://github.com/Yuqing-2434/INFO-5940-Codespace.git
cd <INFO-5940-Codespace>
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Export your API key

```bash
export API_KEY="your API key"
```

### 4. Run the Streamlit app

```bash
streamlit run chat_with_pdf.py
```

## How to Use

1. Upload one or more files (.txt, .md, .pdf).
2. The app will index and embed them automatically.
3. Type your question in the chat box.
4. The assistant responds based on retrieved document chunks.
5. Sources are displayed below each answer.

## Close the app:
```bash
Ctrl + C

```