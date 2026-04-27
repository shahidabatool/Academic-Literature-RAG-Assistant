import streamlit as st
import os
import io
import re
import sys
import contextlib
import pandas as pd
import base64
import streamlit.components.v1 as components
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_groq import ChatGroq
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_openai import ChatOpenAI
from langchain_mistralai import ChatMistralAI
from langchain_anthropic import ChatAnthropic
from langchain_core.messages import HumanMessage, SystemMessage

os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

# Ensure output directory exists for file generation
OUTPUT_DIR = os.path.join(SCRIPT_DIR, "../outputs")
if not os.path.exists(OUTPUT_DIR):
    os.makedirs(OUTPUT_DIR)

# Page Configuration
st.set_page_config(page_title="Academic Literature RAG Assistant", page_icon="🩸", layout="wide")

# --- Custom CSS Theme ---
st.markdown("""
<style>


/* Header styling */
.main-header {
    text-align: center;
    padding: 20px 0 10px;
}
.main-header h1 {
    font-size: 2.2em;
    font-weight: 800;
    margin-bottom: 4px;
    letter-spacing: -0.5px;
}
.main-header .subtitle {
    font-size: 1em;
    font-weight: 400;
    opacity: 0.8;
}
.main-header .badge {
    display: inline-block;
    margin-top: 8px;
    padding: 4px 14px;
    background: rgba(239, 68, 68, 0.15);
    border: 1px solid rgba(239, 68, 68, 0.3);
    border-radius: 20px;
    color: #fca5a5;
    font-size: 0.75em;
    font-weight: 600;
    letter-spacing: 1px;
}

/* Skill chips */
.skill-chips {
    display: flex;
    flex-wrap: wrap;
    gap: 6px;
    justify-content: center;
    margin: 12px 0 20px;
}
.skill-chip {
    padding: 5px 12px;
    border-radius: 20px;
    font-size: 0.72em;
    font-weight: 600;
    border: 1px solid var(--secondary-background-color);
    background: var(--secondary-background-color);
}





/* Button styling */
.stDownloadButton button {
    background: linear-gradient(135deg, #3b82f6, #2563eb) !important;
    color: white !important;
    border: none !important;
    border-radius: 8px !important;
    font-weight: 600 !important;
}

/* Spinner */
.stSpinner > div {
    border-color: #3b82f6 !important;
}
</style>
""", unsafe_allow_html=True)

# --- Header ---
st.markdown("""
<div class="main-header">
    <h1>🩸 Academic Literature RAG Assistant</h1>
    <div class="subtitle">AI-Powered Forensic Literature Engine</div>
    <div class="badge">RAG + CROSS-ENCODER RERANKING</div>
</div>
<div class="skill-chips">
    <span class="skill-chip">📊 Infographics</span>
    <span class="skill-chip">📑 Excel Sheets</span>
    <span class="skill-chip">📝 Word Reports</span>
    <span class="skill-chip">📋 Presentations</span>
    <span class="skill-chip">📄 Paper Summaries</span>
    <span class="skill-chip">🔬 Q&A</span>
</div>
""", unsafe_allow_html=True)

# --- Sidebar ---
st.sidebar.markdown("## 🔑 API Keys")
st.sidebar.caption("Enter at least one key. The system auto-switches on failure.")
groq_key = st.sidebar.text_input("Groq", type="password", placeholder="gsk_...")
gemini_key = st.sidebar.text_input("Gemini", type="password", placeholder="AI...")
openai_key = st.sidebar.text_input("OpenAI", type="password", placeholder="sk-...")
mistral_key = st.sidebar.text_input("Mistral", type="password", placeholder="...")
claude_key = st.sidebar.text_input("Claude", type="password", placeholder="sk-ant-...")

st.sidebar.divider()
st.sidebar.markdown("## 💡 Quick Prompts")
quick_prompts = {
    "📊 Infographic": "Create an infographic for all 10 topics",
    "📑 Excel Sheet": "Create an Excel sheet of all topics",
    "📄 Summarize": "Summarize all papers on bloodstain pattern analysis",
    "📝 Word Report": "Create a detailed Word report on BPA classification",
}

# Store selected quick prompt
selected_prompt = None
for label, prompt_text in quick_prompts.items():
    if st.sidebar.button(label, use_container_width=True):
        selected_prompt = prompt_text

st.sidebar.divider()
st.sidebar.markdown("## 📈 Session Info")

# --- Step 6: Retrieval Function with Metadata Filtering ---
@st.cache_resource
def load_db():
    CHROMA_PATH = os.path.join(SCRIPT_DIR, "../Text/chroma_db")
    if not os.path.exists(CHROMA_PATH):
        return None
    embeddings = HuggingFaceEmbeddings(
        model_name="nomic-ai/nomic-embed-text-v1.5",
        model_kwargs={"trust_remote_code": True}
    )
    db = Chroma(persist_directory=CHROMA_PATH, embedding_function=embeddings)
    return db

db = load_db()
if db:
    try:
        count = db._collection.count()
        st.sidebar.metric("Vector DB Chunks", f"{count:,}")
    except:
        st.sidebar.caption("✅ Vector DB loaded")

st.sidebar.divider()
st.sidebar.markdown("## 💾 Export")

def get_chat_history_text():
    chat_text = "# Academic Literature RAG Assistant - Chat History\n\n"
    if "messages" in st.session_state:
        for msg in st.session_state["messages"]:
            role = "👤 USER" if msg["role"] == "user" else "🤖 ASSISTANT"
            # Remove any markdown code blocks that might interfere with the export's readability
            content = msg['content'].replace("```echarts", "```json") # ensure it shows as json in markdown editors
            chat_text += f"## {role}\n{content}\n\n---\n\n"
    return chat_text

if "messages" in st.session_state and len(st.session_state["messages"]) > 1:
    st.sidebar.download_button(
        label="📥 Download Chat History (.md)",
        data=get_chat_history_text(),
        file_name="bpa_chat_history.md",
        mime="text/markdown",
        use_container_width=True
    )
else:
    st.sidebar.info("Chat history will appear here once you start a conversation.")

# --- Domain-Specific SVG Diagram Injector ---
def get_topic_svg(heading):
    """Returns an inline SVG diagram based on topic keywords in the heading."""
    h = heading.lower()
    
    if any(w in h for w in ["classification", "types", "pattern", "category"]):
        return '''<svg width="100%" height="120" viewBox="0 0 400 120" xmlns="http://www.w3.org/2000/svg" style="margin-top:15px;">
          <circle cx="70" cy="50" r="30" fill="#FFCDD2" stroke="#E53935" stroke-width="2"/>
          <text x="70" y="55" text-anchor="middle" font-size="10" fill="#333" font-weight="bold">Passive</text>
          <text x="70" y="100" text-anchor="middle" font-size="9" fill="#888">Round</text>
          <text x="140" y="50" font-size="16" fill="#999">➔</text>
          <ellipse cx="200" cy="50" rx="35" ry="25" fill="#C8E6C9" stroke="#43A047" stroke-width="2"/>
          <text x="200" y="55" text-anchor="middle" font-size="10" fill="#333" font-weight="bold">Active</text>
          <text x="200" y="100" text-anchor="middle" font-size="9" fill="#888">Irregular</text>
          <text x="270" y="50" font-size="16" fill="#999">➔</text>
          <ellipse cx="340" cy="50" rx="40" ry="20" fill="#BBDEFB" stroke="#1E88E5" stroke-width="2"/>
          <text x="340" y="55" text-anchor="middle" font-size="10" fill="#333" font-weight="bold">Projected</text>
          <text x="340" y="100" text-anchor="middle" font-size="9" fill="#888">Elongated</text>
        </svg>'''
    
    elif any(w in h for w in ["ml", "model", "machine", "learning", "deep", "cnn", "accuracy"]):
        return '''<svg width="100%" height="120" viewBox="0 0 400 120" xmlns="http://www.w3.org/2000/svg" style="margin-top:15px;">
          <text x="5" y="20" font-size="11" fill="#555">Random Forest</text>
          <rect x="120" y="8" width="240" height="18" rx="9" fill="#C8E6C9" stroke="#43A047" stroke-width="1"/>
          <text x="5" y="48" font-size="11" fill="#555">XGBoost</text>
          <rect x="120" y="36" width="220" height="18" rx="9" fill="#BBDEFB" stroke="#1E88E5" stroke-width="1"/>
          <text x="5" y="76" font-size="11" fill="#555">CNN</text>
          <rect x="120" y="64" width="200" height="18" rx="9" fill="#FFE0B2" stroke="#FB8C00" stroke-width="1"/>
          <text x="5" y="104" font-size="11" fill="#555">MobileNet</text>
          <rect x="120" y="92" width="180" height="18" rx="9" fill="#F3E5F5" stroke="#8E24AA" stroke-width="1"/>
        </svg>'''
    
    elif any(w in h for w in ["crime scene", "investigation", "collection", "procedure", "process", "workflow"]):
        return '''<svg width="100%" height="120" viewBox="0 0 420 80" xmlns="http://www.w3.org/2000/svg" style="margin-top:15px;">
          <rect x="0" y="20" width="80" height="40" rx="10" fill="#FFCDD2" stroke="#E53935" stroke-width="2"/>
          <text x="40" y="45" text-anchor="middle" font-size="10" fill="#333" font-weight="bold">Scene</text>
          <text x="95" y="43" font-size="14" fill="#999">➔</text>
          <rect x="110" y="20" width="80" height="40" rx="10" fill="#C8E6C9" stroke="#43A047" stroke-width="2"/>
          <text x="150" y="45" text-anchor="middle" font-size="10" fill="#333" font-weight="bold">Evidence</text>
          <text x="205" y="43" font-size="14" fill="#999">➔</text>
          <rect x="220" y="20" width="80" height="40" rx="10" fill="#BBDEFB" stroke="#1E88E5" stroke-width="2"/>
          <text x="260" y="45" text-anchor="middle" font-size="10" fill="#333" font-weight="bold">Lab</text>
          <text x="315" y="43" font-size="14" fill="#999">➔</text>
          <rect x="330" y="20" width="80" height="40" rx="10" fill="#FFF9C4" stroke="#F9A825" stroke-width="2"/>
          <text x="370" y="45" text-anchor="middle" font-size="10" fill="#333" font-weight="bold">Report</text>
        </svg>'''
    
    elif any(w in h for w in ["anatomy", "anatomical", "blood", "physiology", "characteristic"]):
        return '''<svg width="100%" height="120" viewBox="0 0 300 120" xmlns="http://www.w3.org/2000/svg" style="margin-top:15px;">
          <circle cx="150" cy="60" r="40" fill="none" stroke="#E53935" stroke-width="2.5" stroke-dasharray="8 4"/>
          <circle cx="150" cy="60" r="8" fill="#E53935"/>
          <text x="150" y="10" text-anchor="middle" font-size="11" fill="#555" font-weight="bold">📐 Size</text>
          <line x1="150" y1="15" x2="150" y2="20" stroke="#ccc" stroke-width="1"/>
          <text x="260" y="65" text-anchor="middle" font-size="11" fill="#555" font-weight="bold">🔍 Shape</text>
          <line x1="190" y1="60" x2="240" y2="60" stroke="#ccc" stroke-width="1"/>
          <text x="150" y="118" text-anchor="middle" font-size="11" fill="#555" font-weight="bold">🩸 Distribution</text>
          <line x1="150" y1="100" x2="150" y2="108" stroke="#ccc" stroke-width="1"/>
          <text x="40" y="65" text-anchor="middle" font-size="11" fill="#555" font-weight="bold">➔ Direction</text>
          <line x1="70" y1="60" x2="110" y2="60" stroke="#ccc" stroke-width="1"/>
        </svg>'''
    
    return ""

def get_topic_svg_with_type(heading):
    """Returns (svg_type, svg_html) based on topic keywords in the heading."""
    h = heading.lower()
    
    if any(w in h for w in ["classification", "types", "pattern", "category"]):
        return "classification", get_topic_svg(heading)
    elif any(w in h for w in ["ml", "model", "machine", "learning", "deep", "cnn", "accuracy"]):
        return "ml", get_topic_svg(heading)
    elif any(w in h for w in ["crime scene", "investigation", "collection", "procedure", "process", "workflow"]):
        return "crimescene", get_topic_svg(heading)
    elif any(w in h for w in ["anatomy", "anatomical", "blood", "physiology", "characteristic"]):
        return "anatomy", get_topic_svg(heading)
    return None, ""

def inject_topic_svgs(html_content):
    """Post-process LLM HTML to inject domain-specific SVG diagrams into matching cards. Each SVG type injected only once."""
    import re as _re
    headings = _re.findall(r'<(?:h[2-4]|div)[^>]*>([^<]{5,80})</(?:h[2-4]|div)>', html_content)
    injected_types = set()  # track by SVG category, not heading
    for heading_text in headings:
        svg_type, svg = get_topic_svg_with_type(heading_text)
        if svg_type and svg and svg_type not in injected_types:
            injected_types.add(svg_type)
            target = heading_text + "<"
            if target in html_content:
                idx = html_content.find(target)
                ul_end = html_content.find("</ul>", idx)
                if ul_end != -1:
                    insert_pos = ul_end + len("</ul>")
                    html_content = html_content[:insert_pos] + "\n" + svg + "\n" + html_content[insert_pos:]
    return html_content

# --- Step 7: Skill Loader Function ---
SKILLS = {
    "pdf": "You are a forensic expert. Your task is to extract, read, and summarize information from the provided PDF literature. Be highly accurate.",
    "pptx": "You are an expert presentation designer. The user wants a PowerPoint presentation. You MUST respond with ONLY valid Python code using the `python-pptx` library to create a presentation. Ensure you save the presentation to '" + os.path.join(OUTPUT_DIR, "presentation.pptx") + "'. Write python code wrapped in ```python ... ```.",
    "docx": "You are an expert report writer. The user wants a Word document. You MUST respond with ONLY valid Python code using the `python-docx` library to create a document based on the context. Ensure you save the document to '" + os.path.join(OUTPUT_DIR, "report.docx") + "'. Write python code wrapped in ```python ... ```.",
    "xlsx": """You are a data analyst. The user wants an Excel spreadsheet. You MUST respond with ONLY valid Python code using the `openpyxl` library.

RULES:
1. Extract ALL relevant data from the provided context into a well-structured spreadsheet.
2. Include these columns at minimum: Topic, Sub-Topic, Key Finding, Method/Technique, Source Paper, Year.
3. Fill every row with specific facts from the context — never leave cells empty or use generic placeholders.
4. Add column headers with bold formatting and auto-adjusted column widths.
5. If the context mentions statistics, percentages, or numerical data, add a separate 'Statistics' sheet.
6. Save to '""" + os.path.join(OUTPUT_DIR, "data.xlsx") + """'.
7. Write python code wrapped in ```python ... ```.
""",
    "canvas-design": """You are a data extraction expert. Extract structured content from the provided BPA context and return ONLY valid JSON wrapped in ```json ... ```.

JSON SCHEMA — follow this EXACTLY:
```json
{
  "title": "exact paper title from context",
  "authors": "exact author names from context",
  "hero_steps": ["Step 1", "Step 2", "Step 3", "Step 4"],
  "sections": [
    {
      "heading": "section title",
      "points": ["concise point 1 (max 12 words)", "point 2", "point 3"],
      "stat": "94%",
      "stat_label": "Model Accuracy"
    }
  ],
  "bottom_stats": [
    {"value": "94%", "label": "Accuracy"},
    {"value": "6", "label": "Pattern Types"},
    {"value": "2020", "label": "Year"}
  ]
}
```

RULES:
1. Extract minimum 4 sections, maximum 10. Each section needs 3-5 concise bullet points.
2. hero_steps: Extract the main process/pipeline from the paper (4-6 steps).
3. CRITICAL: Every stat value must be copied WORD-FOR-WORD from the context. If no explicit stat exists, set stat to null.
4. bottom_stats: Extract 3 key numbers from the paper. If fewer than 3 exist, only include what you find.
5. Keep bullet points SHORT (max 12 words). No filler phrases like 'it is important to note'.
6. Copy paper title and author names EXACTLY as written in the context.
7. Return ONLY the JSON. No explanations before or after.
""",
    "doc-coauthoring": "You are a co-author for a forensic science paper. Help draft the literature review or paper sections in a highly academic tone.",
    "theme-factory": "You are a styling expert. Ensure outputs have a highly professional forensic theme, using deep reds, grays, and formal typography.",
    "paper-summary": """You are an expert academic research analyst specializing in forensic science. Generate a comprehensive, structured summary of the paper(s) from the provided context.

FORMAT — Use this exact structure with markdown headers:

## 📄 Paper Title
**Authors:** [exact names from context]
**Year:** [year]
**Source:** [journal/conference if available]

### 🎯 Research Objective
One clear paragraph explaining what the paper aims to achieve.

### 🔬 Methodology
- Bullet points describing the methods, datasets, and techniques used
- Include specific tools, sample sizes, and experimental setups mentioned

### 📊 Key Findings
- Numbered list of the most important results
- Include specific numbers, percentages, and metrics verbatim from the text
- Do NOT invent any statistics

### 💡 Contributions & Significance
- What new knowledge does this paper add to BPA?
- How does it compare to prior work?

### ⚠️ Limitations
- Any limitations or gaps mentioned by the authors

### 🔮 Future Work
- Suggested directions for future research

RULES:
1. Extract information ONLY from the provided context. Never invent facts.
2. If summarizing multiple papers, create a separate section for each paper.
3. Copy author names, paper titles, and statistics EXACTLY as written.
4. If a section has no relevant information in the context, write "Not available in the provided context."
5. Be thorough — include all key details, not just surface-level overview.
""",
    "data-viz": """You are an expert data visualization engineer. The user wants to see data, statistics, or a comparison visualized as an interactive chart.
Extract relevant numerical data from the context and generate a valid JSON configuration for Apache ECharts.

RULES:
1. You MUST wrap your JSON output in ```echarts ... ```
2. Return ONLY the ECharts configuration object (the 'options' dict).
3. The JSON must be perfectly valid (use double quotes, no trailing commas).
4. Do not invent data. Only use stats, accuracies, or numbers mentioned in the context.
5. Provide a short, one-sentence markdown summary of the chart BEFORE the ```echarts block.

Example Output format:
Here is a comparison of the model accuracies found in the literature.
```echarts
{
  "title": {"text": "Model Accuracies in BPA"},
  "tooltip": {"trigger": "axis"},
  "xAxis": {"type": "category", "data": ["Random Forest", "CNN", "XGBoost"]},
  "yAxis": {"type": "value", "max": 100},
  "series": [{"type": "bar", "data": [94.2, 96.1, 91.8]}]
}
```
"""
}

def load_skill(user_query):
    query = user_query.lower()
    if any(word in query for word in ["slide", "presentation", "ppt", "powerpoint"]):
        return SKILLS["pptx"], "pptx"
    elif any(word in query for word in ["report", "word", "doc", "summary document"]):
        return SKILLS["docx"], "docx"
    elif any(word in query for word in ["summarize", "summary of", "summarise", "sum up", "overview of paper", "what is this paper about"]):
        return SKILLS["paper-summary"], "paper-summary"
    elif any(word in query for word in ["extract", "pdf", "read paper"]):
        return SKILLS["pdf"], "pdf"
    elif any(word in query for word in ["table", "excel", "spreadsheet", "xlsx"]):
        return SKILLS["xlsx"], "xlsx"
    elif any(word in query for word in ["chart", "graph", "plot", "visualize", "visualization", "compare accuracy", "show stats"]):
        return SKILLS["data-viz"], "data-viz"
    elif any(word in query for word in ["poster", "figure", "visual", "infographic", "design"]):
        return SKILLS["canvas-design"], "canvas-design"
    elif any(word in query for word in ["co-write", "literature review", "draft section"]):
        return SKILLS["doc-coauthoring"], "doc-coauthoring"
    else:
        return "You are a helpful Forensic Science AI assistant answering questions based strictly on the provided literature context.", "none"

# --- Step 8: Model-agnostic LLM switcher ---
def get_llm():
    # Try Groq Primary
    if groq_key:
        try:
            return ChatGroq(api_key=groq_key, model="llama-3.3-70b-versatile"), "Groq (llama-3.3-70b-versatile)"
        except Exception as e:
            st.sidebar.warning(f"Groq failed: {e}")
    # Try Gemini
    if gemini_key:
        try:
            return ChatGoogleGenerativeAI(google_api_key=gemini_key, model="gemini-2.0-flash"), "Gemini (gemini-2.0-flash)"
        except Exception as e:
            st.sidebar.warning(f"Gemini failed: {e}")
    # Try OpenAI
    if openai_key:
        try:
            return ChatOpenAI(api_key=openai_key, model="gpt-4o-mini"), "OpenAI (gpt-4o-mini)"
        except Exception as e:
            st.sidebar.warning(f"OpenAI failed: {e}")
    # Try Mistral
    if mistral_key:
        try:
            return ChatMistralAI(api_key=mistral_key, model="mistral-large-latest"), "Mistral (mistral-large-latest)"
        except Exception as e:
            st.sidebar.warning(f"Mistral failed: {e}")
    # Try Claude (Anthropic)
    if claude_key:
        try:
            return ChatAnthropic(api_key=claude_key, model="claude-sonnet-4-20250514"), "Claude (claude-sonnet-4-20250514)"
        except Exception as e:
            st.sidebar.warning(f"Claude failed: {e}")
            
    return None, "No valid LLM available"

# --- Step 10: Code executor for file generation ---
def execute_python_code(response_text):
    # Extract python code block
    match = re.search(r"```python\n(.*?)```", response_text, re.DOTALL)
    if not match:
        return False, "No valid Python code found in the response."
    
    code = match.group(1)
    
    # Safe execution context
    f = io.StringIO()
    try:
        with contextlib.redirect_stdout(f), contextlib.redirect_stderr(f):
            exec(code, {})
        return True, f.getvalue()
    except Exception as e:
        return False, str(e)

# --- Step 9 & 11: RAG chain and Streamlit UI ---
if "messages" not in st.session_state:
    st.session_state["messages"] = [{
        "role": "assistant", 
        "content": "👋 **Welcome to the BPA Research Assistant!**\n\nI can help you with:\n- 🔬 **Ask questions** about bloodstain pattern analysis\n- 📊 **Generate infographics** — *\"Create an infographic for all 10 topics\"*\n- 📑 **Create Excel sheets** — *\"Create an Excel sheet of all topics\"*\n- 📝 **Write Word reports** — *\"Create a report on BPA classification\"*\n- 📋 **Build presentations** — *\"Make a presentation on spatter analysis\"*\n- 📄 **Summarize papers** — *\"Summarize the paper on machine learning in BPA\"*\n\nType your question below or use the **Quick Prompts** in the sidebar! 👈"
    }]

if db is None:
    st.warning("⚠️ Vector Database not found! Please build the database to begin.")
    if st.button("🔨 Build Vector Database Now", use_container_width=True):
        with st.spinner("Building database from PDF documents... This may take a few minutes."):
            import build_vector_db
            build_vector_db.main()
            st.success("✅ Database built successfully! Refreshing...")
            st.rerun()
else:
    for msg in st.session_state.messages:
        st.chat_message(msg["role"]).write(msg["content"])

    # Handle quick prompt from sidebar or manual input
    prompt = st.chat_input("Ask about BPA, or request an infographic, report, or summary...")
    if selected_prompt:
        prompt = selected_prompt
    
    if prompt:
        st.session_state.messages.append({"role": "user", "content": prompt})
        st.chat_message("user").write(prompt)

        with st.spinner("🔍 Retrieving & analyzing..."):
            llm, model_name = get_llm()
            if not llm:
                st.error("Please provide an API key for Groq, Gemini, OpenAI, Mistral, or Claude.")
                st.stop()
                
            st.sidebar.success(f"✅ Engine: {model_name}")

            # 1. Detect Intent & Load Skill
            skill_instruction, skill_name = load_skill(prompt)
            st.sidebar.info(f"Active Skill: {skill_name.upper()}")

            # 2. Retrieval (increase k for infographic generation)
            k_value = 15 if skill_name in ["canvas-design", "xlsx", "paper-summary"] else 5
            
            # 2a. Smart query enhancement for vague prompts
            search_query = prompt
            all_topics_mode = False
            BPA_TOPIC_QUERIES = [
                "bloodstain pattern classification passive active projected transfer",
                "spatter analysis impact cast-off arterial expiratory",
                "directionality angle of impact trajectory convergence",
                "crime scene investigation evidence collection documentation",
                "machine learning deep learning CNN classification model accuracy",
                "fluid dynamics viscosity surface tension velocity",
                "bloodstain morphology shape size diameter elongation",
                "anatomy physiology blood cells coagulation wound",
                "experimental methods laboratory controlled apparatus methodology",
                "legal forensic standards daubert testimony expert witness"
            ]
            
            vague_patterns = ["all the topics", "all topics", "all 10", "everything", "overview", "summary of all"]
            if any(v in prompt.lower() for v in vague_patterns):
                all_topics_mode = True
            
            if all_topics_mode:
                # Multi-topic retrieval: 2 chunks per topic = 20 diverse chunks
                docs = []
                for topic_query in BPA_TOPIC_QUERIES:
                    topic_retriever = db.as_retriever(search_kwargs={"k": 2})
                    topic_docs = topic_retriever.invoke(topic_query)
                    docs.extend(topic_docs)
                k_value = len(docs)  # keep all
            else:
                retriever = db.as_retriever(search_kwargs={"k": k_value + 10})  # over-retrieve for reranking
                docs = retriever.invoke(search_query)
            
            # 2b. Cross-encoder reranking (local, no API cost) — skip for all-topics mode
            if not all_topics_mode:
                try:
                    from sentence_transformers import CrossEncoder
                    reranker = CrossEncoder("cross-encoder/ms-marco-MiniLM-L-6-v2")
                    pairs = [(prompt, d.page_content) for d in docs]
                    scores = reranker.predict(pairs)
                    ranked = sorted(zip(scores, docs), key=lambda x: -x[0])
                    docs = [d for _, d in ranked[:k_value]]
                    st.sidebar.caption(f"Reranked {len(ranked)} → top {k_value} chunks")
                except Exception as e:
                    st.sidebar.caption(f"Reranker skipped: {e}")
                    docs = docs[:k_value]
            
            # 2c. Deduplicate chunks with similar content
            seen_content = set()
            unique_docs = []
            for d in docs:
                content_key = d.page_content[:200]
                if content_key not in seen_content:
                    seen_content.add(content_key)
                    unique_docs.append(d)
            docs = unique_docs
            
            context_blocks = []
            for d in docs:
                source = d.metadata.get('source', 'Unknown')
                page = d.metadata.get('page', 'N/A')
                topic = d.metadata.get('topic', 'N/A')
                year = d.metadata.get('year', 'N/A')
                section = d.metadata.get('section_type', 'N/A')
                context_blocks.append(f"--- SOURCE: {source} (Page {page}, Topic: {topic}, Section: {section}, Year: {year}) ---\n{d.page_content}")
            
            context = "\n\n".join(context_blocks)

            # 3. Build Skill-Aware Prompt
            topics_instruction = ""
            if all_topics_mode and skill_name == "canvas-design":
                topics_instruction = """
IMPORTANT: The user requested ALL 10 BPA topics. You MUST include a section in your JSON for EACH of these 10 topics:
1. Pattern Classification (passive, active, projected, transfer)
2. Spatter Analysis (impact, cast-off, arterial)
3. Directionality & Angle of Impact
4. Crime Scene Investigation & Evidence Collection
5. Machine Learning & Computational Methods
6. Fluid Dynamics of Blood
7. Bloodstain Morphology (shape, size, features)
8. Anatomy & Physiology of Blood
9. Experimental Methods & Laboratory Techniques
10. Legal & Forensic Standards (Daubert, expert testimony)
Your sections array MUST have exactly 10 items — one per topic.
"""
            full_system_prompt = f"""{skill_instruction}
{topics_instruction}
Use the following context from Bloodstain Pattern Analysis (BPA) literature to fulfill the user's query:
{context}

If the context does not contain the answer, explicitly state that.
"""
            messages = [
                SystemMessage(content=full_system_prompt),
                HumanMessage(content=prompt)
            ]

            # 4. Invoke LLM Switcher
            try:
                response = llm.invoke(messages)
                msg_content = response.content
                
                if skill_name == "canvas-design":
                    st.info("🎨 Extracting content & building infographic...")
                    
                    from infographic_builder import build_infographic_html, parse_llm_json
                    
                    # Parse the structured JSON from LLM
                    data = parse_llm_json(msg_content)
                    
                    if not data:
                        msg_content = f"❌ **Failed to extract infographic data.**\n\nModel did not return valid JSON.\n\nRaw Output:\n{msg_content}"
                    else:
                        # Build premium HTML from template
                        html_content = build_infographic_html(data)
                        
                        # Inject domain-specific SVG diagrams
                        html_content = inject_topic_svgs(html_content)
                        
                        png_path = os.path.join(OUTPUT_DIR, "infographic.png")
                        
                        # Save temp HTML for Playwright
                        tmp_html_path = os.path.join(OUTPUT_DIR, "_temp_infographic.html")
                        with open(tmp_html_path, "w", encoding="utf-8") as f:
                            f.write(html_content)
                        
                        # Convert HTML to PNG using Playwright
                        try:
                            from playwright.sync_api import sync_playwright
                            with sync_playwright() as p:
                                browser = p.chromium.launch()
                                page = browser.new_page()
                                page.goto(f"file://{tmp_html_path}")
                                page.wait_for_load_state("networkidle")
                                
                                height = page.evaluate("document.body.scrollHeight + 300")
                                page.set_viewport_size({"width": 1400, "height": int(height)})
                                page.screenshot(path=png_path, full_page=True)
                                browser.close()
                            
                            os.remove(tmp_html_path)
                            st.image(png_path)
                            msg_content = f"✅ **Infographic generated!** ({len(data.get('sections', []))} sections extracted)\n\nSaved to `outputs/infographic.png`."
                        except Exception as e:
                            st.warning(f"PNG export failed ({e}). Showing HTML version instead.")
                            msg_content = "✅ **Infographic generated as HTML!**"
                            components.html(html_content, height=1200, scrolling=True)
                        
                        # Download button
                        if os.path.exists(png_path):
                            with open(png_path, "rb") as f:
                                st.download_button("🖼️ Download Infographic (.png)", f, file_name="infographic.png", mime="image/png")

                # Check if we need to execute code for file generation
                elif skill_name in ["pptx", "docx", "xlsx"]:
                    st.info(f"Skill `{skill_name}` detected. Executing generated code...")
                    success, output = execute_python_code(msg_content)
                    if success:
                        msg_content = f"✅ **File successfully generated!**\n\nThe file has been saved to the `outputs` directory.\n\n*(Code execution output: {output})*"
                    else:
                        msg_content = f"❌ **Failed to generate file.**\n\nError:\n```\n{output}\n```\n\nModel provided code:\n{msg_content}"
                
                # Check if we need to render an EChart
                st.session_state.messages.append({"role": "assistant", "content": msg_content})
                
                with st.chat_message("assistant"):
                    echarts_match = re.search(r"```echarts\n(.*?)\n```", msg_content, re.DOTALL)
                    if echarts_match:
                        # Print the text before the chart
                        text_part = msg_content.split("```echarts")[0].strip()
                        if text_part:
                            st.write(text_part)
                            
                        # Render the chart using native HTML/JS to avoid plugin errors
                        try:
                            import json
                            import streamlit.components.v1 as components
                            
                            chart_json = echarts_match.group(1)
                            # Validate JSON
                            json.loads(chart_json) 
                            
                            html_code = f"""
                            <!DOCTYPE html>
                            <html>
                            <head>
                                <meta charset="utf-8">
                                <script src="https://cdn.jsdelivr.net/npm/echarts@5.5.0/dist/echarts.min.js"></script>
                            </head>
                            <body style="margin:0; padding:0; background: transparent;">
                                <div id="chart" style="width: 100%; height: 450px;"></div>
                                <script>
                                    var chartDom = document.getElementById('chart');
                                    var myChart = echarts.init(chartDom, 'dark'); // Use dark theme
                                    var option = {chart_json};
                                    
                                    // Make background transparent to match Streamlit
                                    option.backgroundColor = 'transparent';
                                    
                                    myChart.setOption(option);
                                    window.addEventListener('resize', function() {{
                                        myChart.resize();
                                    }});
                                </script>
                            </body>
                            </html>
                            """
                            components.html(html_code, height=470)
                        except Exception as e:
                            st.error(f"Failed to render chart: {e}")
                            st.code(echarts_match.group(1), language="json")
                    else:
                        st.write(msg_content)

            except Exception as e:
                st.error(f"Error during LLM inference: {str(e)}")
