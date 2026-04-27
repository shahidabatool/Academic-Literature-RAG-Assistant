# 🩸 BPA Research Assistant

[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![Streamlit](https://img.shields.io/badge/Streamlit-FF4B4B?style=flat&logo=Streamlit&logoColor=white)](https://streamlit.io/)
[![LangChain](https://img.shields.io/badge/LangChain-121212?style=flat&logo=Chainlink&logoColor=white)](https://langchain.com/)
[![ChromaDB](https://img.shields.io/badge/ChromaDB-00D1B2?style=flat)](https://www.trychroma.com/)

![BPA Research Assistant Header](docs/header.png)

> [!NOTE]
> 🚧 **Work in Progress** — This system is being actively developed as part of **MRP Research at Toronto Metropolitan University**.

## 📚 Multi-Provider Literature RAG Chatbot

The **BPA Research Assistant** is a flexible Retrieval-Augmented Generation (RAG) engine that allows researchers to choose their preferred LLM provider — **OpenAI, Google Gemini, Anthropic Claude, Mistral, or Groq (Llama 3.3-70b)** — all from a single interface. 

Built with **LangChain**, **ChromaDB**, and **HuggingFace Embeddings (Nomic-AI)**, it provides a robust framework for querying complex forensic literature. The system supports multiple document formats (PDF, DOCX, XLSX, and PPTX) and features an interactive Streamlit interface for seamless document analysis and conversational Q&A.

### 🌟 Key Features

- **🧠 Multi-Engine RAG**: Seamlessly switch between top-tier LLMs including **Groq (Llama 3)**, **Gemini 2.0**, **GPT-4o**, **Mistral**, and **Claude** to compare reasoning and outputs.
- **📄 Research Automation & Synthesis**: Beyond simple Q&A, the system synthesizes data across multiple papers to provide comprehensive overviews and thematic summaries.
- **🛠️ Multi-Format Export Suite**: Convert literature insights directly into professional assets:
    - **📑 Excel Sheets**: Structured data extraction for meta-analyses.
    - **📝 Word Reports**: Detailed academic or investigative reports.
    - **📋 PowerPoint Presentations**: Automated slide generation for research briefings.
    - **📊 Interactive Infographics**: High-fidelity visual summaries of forensic topics.
- **📈 Real-time Data Visualization**: Automatic extraction of experimental metrics and statistics rendered as interactive **Apache ECharts**.
- **🔎 Advanced Forensic Retrieval**: Hyper-accurate search utilizing **Cross-Encoder Reranking** and **Metadata Filtering** to find the needle in the haystack.

---

## 🛠️ Project Structure

```text
Task_3_RAG_System/
├── Code/
│   ├── streamlit_app.py        # Main UI and RAG logic
│   ├── build_vector_db.py      # PDF ingestion & ChromaDB builder
│   └── infographic_builder.py  # Infographic rendering engine
├── Text/
│   ├── *.pdf                   # Source forensic literature
│   └── chroma_db/              # Persistent vector store
├── outputs/                    # Generated reports & infographics
├── docs/                       # Project documentation & assets
└── requirements.txt            # Python dependencies
```

---

## 🚀 Getting Started

### 1. Clone the Repository
```bash
git clone https://github.com/your-username/bpa-research-assistant.git
cd bpa-research-assistant
```

### 2. Install Dependencies
Ensure you have Python 3.9+ installed.
```bash
pip install -r requirements.txt
playwright install chromium
```

### 3. Ingest Literature
Place your forensic PDF papers in the `Text/` directory, then build the vector database:
```bash
python Code/build_vector_db.py
```

### 4. Launch the App
```bash
streamlit run Code/streamlit_app.py
```

---

## 💡 How to Use

1. **Enter API Keys**: Provide your Groq, Gemini, or OpenAI keys in the sidebar.
2. **Ask Questions**: Use the chat interface to query the literature (e.g., *"What are the latest CNN models for blood spatter classification?"*).
3. **Generate Assets**: Use "Quick Prompts" to:
    - **Create Infographics**: *"Generate an infographic for all topics."*
    - **Export Data**: *"Create an Excel sheet of all findings."*
    - **Draft Reports**: *"Write a Word report on experimental methodology."*

---

## 🏗️ Technical Architecture

- **Vector Store**: [ChromaDB](https://www.trychroma.com/) for efficient similarity search.
- **Embeddings**: `nomic-ai/nomic-embed-text-v1.5` for high-dimensional text representation.
- **Reranker**: `cross-encoder/ms-marco-MiniLM-L-6-v2` for optimizing retrieval relevance.
- **Frontend**: [Streamlit](https://streamlit.io/) for a responsive, forensic-themed dashboard.
- **Execution**: Dynamic Python code execution for on-the-fly file generation.

---

## 📜 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

---

*Developed for Advanced Forensic Research in Bloodstain Pattern Analysis.*
