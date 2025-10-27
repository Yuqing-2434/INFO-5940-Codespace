# Reference Log (ref-log.md)

### Course: INFO 5940 011
### Assignment 1 
### Author: *Yuqing Sun* 
### netID: *ys2434* 

This file logs all **external sources**, **documentation**, and **AI-assisted tools** that contributed to the completion of this assignment.  

### External Libraries and Frameworks

| Library / Framework | Purpose | Reference / Documentation |
|----------------------|----------|----------------------------|
| **Streamlit** | Web-based chat interface, file uploader, and chat history management | [https://docs.streamlit.io](https://docs.streamlit.io) |
| **LangChain** | Core RAG pipeline components: `Document`, `RecursiveCharacterTextSplitter`, `Chroma` | [https://python.langchain.com](https://python.langchain.com) |
| **ChromaDB** | Vector database for storing and retrieving embeddings | [https://docs.trychroma.com](https://docs.trychroma.com) |
| **PyPDF2 / LangChain PyPDFLoader** | PDF parsing and text extraction | [https://pypi.org/project/pypdf2/](https://pypi.org/project/pypdf2/) |
| **OpenAI Python SDK** | Connects to the Cornell AI Gateway for embeddings and chat completions | [https://platform.openai.com/docs/api-reference](https://platform.openai.com/docs/api-reference) |
| **NumPy / Pandas** | Dependency packages required by Streamlit and Chroma | [https://numpy.org/doc](https://numpy.org/doc), [https://pandas.pydata.org](https://pandas.pydata.org) |

---

## Online References

| Source | Usage |
|--------|-------|
| LangChain official examples | Used to understand document chunking and retriever setup |
| GitHub Codespace template repository (`assignment1` branch) | Used as base development environment with provided `requirements.txt`， `.devcontainer`, and templates |
| Stack Overflow | Resolved dependency conflict errors between NumPy 2.x and Pandas 2.x |

---

## GenAI Usage

| Tool | Use Case | Description / Rationale |
|------|-----------|--------------------------|
| **OpenAI ChatGPT** | Code debugging | Used to debug LangChain + Chroma integration and resolve model name errors. |
| **OpenAI ChatGPT** | Documentation drafting | Used to generate the initial draft of `README.md` and `INSTRUCTIONS.md`; all code and wording were verified and edited by the author. |

### Why GenAI was used:
- To speed up error resolution and clarify API usage across LangChain modules.  
- To improve documentation clarity and create better formatting.  
