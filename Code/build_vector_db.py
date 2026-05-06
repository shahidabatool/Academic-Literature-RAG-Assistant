import os
import shutil
import re
from langchain_community.document_loaders import PyPDFDirectoryLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings

os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"

# Paths based on the script's actual location
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_PATH = os.path.join(SCRIPT_DIR, "../Text")
CHROMA_PATH = os.path.join(SCRIPT_DIR, "../Text/chroma_db")

# --- BPA Topic Classifier ---
# Maps keyword patterns to forensic sub-topics for richer metadata filtering
BPA_TOPICS = {
    "Pattern Classification": [
        "passive", "active", "projected", "transfer", "contact", "expirated",
        "pool", "flow", "drip trail", "saturation", "classification", "categoriz"
    ],
    "Spatter Analysis": [
        "spatter", "impact spatter", "cast-off", "arterial", "expiratory",
        "mist", "splash", "satellite", "parent drop"
    ],
    "Directionality & Angle": [
        "directionality", "angle of impact", "point of convergence", "area of origin",
        "trajectory", "string method", "tangent", "elliptical", "sine"
    ],
    "Crime Scene Procedure": [
        "crime scene", "documentation", "photography", "collection", "evidence",
        "chain of custody", "swab", "preservation", "courtroom"
    ],
    "Machine Learning & Computational": [
        "machine learning", "deep learning", "neural network", "cnn", "random forest",
        "xgboost", "svm", "classification model", "accuracy", "precision", "recall",
        "mobilenet", "resnet", "image processing", "computational", "algorithm"
    ],
    "Fluid Dynamics": [
        "viscosity", "surface tension", "fluid dynamics", "velocity", "volume",
        "weber number", "reynolds", "newtonian", "non-newtonian", "oscillation"
    ],
    "Bloodstain Morphology": [
        "shape", "size", "diameter", "elongat", "spine", "scallop", "tail",
        "directionality", "edge characteristic", "morpholog"
    ],
    "Anatomy & Physiology": [
        "blood cell", "plasma", "hemoglobin", "coagulation", "clotting",
        "hematocrit", "cardiovascular", "wound", "artery", "vein", "anatomy"
    ],
    "Experimental Methods": [
        "experiment", "laboratory", "controlled", "apparatus", "methodology",
        "test surface", "substrate", "drop height", "pipette", "syringe"
    ],
    "Legal & Forensic Standards": [
        "daubert", "frye", "testimony", "expert witness", "standard", "swgstain",
        "iabpa", "terminology", "working group", "quality assurance"
    ]
}

def classify_bpa_topic(text):
    """Classifies a text chunk into the most relevant BPA sub-topic using keyword matching."""
    text_lower = text.lower()
    scores = {}
    for topic, keywords in BPA_TOPICS.items():
        score = sum(1 for kw in keywords if kw in text_lower)
        if score > 0:
            scores[topic] = score
    
    if scores:
        return max(scores, key=scores.get)
    return "Bloodstain Pattern Analysis"  # default fallback

def extract_metadata(document):
    """
    Extracts custom metadata from the document based on filename and content analysis.
    Schema: source, author, page, topic, year, section_type
    """
    filename = os.path.basename(document.metadata.get("source", ""))
    text = document.page_content
    
    # Simple heuristic to extract year (looking for 4 digits starting with 19 or 20)
    year_match = re.search(r'(19\d{2}|20\d{2})', filename)
    year = int(year_match.group(1)) if year_match else 2025
    
    # Extract author and source based on basic split (e.g. 'Liu_et_al_2020.pdf')
    parts = filename.replace('.pdf', '').split('_')
    author = "Unknown"
    source = filename
    if len(parts) >= 2:
        author = f"{parts[0]} et al." if "et_al" in filename else parts[0]
        source = "_".join(parts)
    
    # Classify topic using content-based BPA topic modeling
    topic = classify_bpa_topic(text)
    
    # Detect section type from content patterns
    section_type = "body"
    text_lower = text.lower()[:200]
    if any(w in text_lower for w in ["abstract", "summary"]):
        section_type = "abstract"
    elif any(w in text_lower for w in ["introduction", "background"]):
        section_type = "introduction"
    elif any(w in text_lower for w in ["method", "material", "experimental"]):
        section_type = "methods"
    elif any(w in text_lower for w in ["result", "finding", "performance"]):
        section_type = "results"
    elif any(w in text_lower for w in ["discussion", "implication"]):
        section_type = "discussion"
    elif any(w in text_lower for w in ["conclusion", "future work"]):
        section_type = "conclusion"
    elif any(w in text_lower for w in ["reference", "bibliography"]):
        section_type = "references"
        
    document.metadata["source"] = source
    document.metadata["author"] = author
    document.metadata["year"] = year
    document.metadata["topic"] = topic
    document.metadata["section_type"] = section_type
    # 'page' is usually populated by PyPDFDirectoryLoader automatically
    if "page" not in document.metadata:
        document.metadata["page"] = 0
        
    return document

def main():
    print(f"Loading PDF documents from {DATA_PATH}...")
    loader = PyPDFDirectoryLoader(DATA_PATH)
    documents = loader.load()
    print(f"Loaded {len(documents)} pages from PDFs.")

    # --- UPGRADED: chunk_size 500 → 1500, overlap 50 → 200 ---
    print("Adding metadata and splitting text into chunks (size=1500, overlap=200)...")
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1500,
        chunk_overlap=200,
        length_function=len,
        is_separator_regex=False,
    )
    
    # Pre-process metadata on raw pages BEFORE splitting
    for doc in documents:
        doc = extract_metadata(doc)
        
    chunks = text_splitter.split_documents(documents)
    
    # Re-classify topics on the final chunks (more accurate than page-level)
    for chunk in chunks:
        chunk.metadata["topic"] = classify_bpa_topic(chunk.page_content)
    
    # Print topic distribution
    topic_counts = {}
    for chunk in chunks:
        t = chunk.metadata["topic"]
        topic_counts[t] = topic_counts.get(t, 0) + 1
    print(f"Split into {len(chunks)} chunks with topic distribution:")
    for t, c in sorted(topic_counts.items(), key=lambda x: -x[1]):
        print(f"  {t}: {c} chunks")

    # Clear out existing DB if it exists
    if os.path.exists(CHROMA_PATH):
        print("Clearing existing database...")
        shutil.rmtree(CHROMA_PATH)

    print("Initializing local HuggingFace embeddings (nomic-ai/nomic-embed-text-v1.5)...")
    embeddings = HuggingFaceEmbeddings(
        model_name="nomic-ai/nomic-embed-text-v1.5",
        model_kwargs={"trust_remote_code": True}
    )

    print(f"Building Chroma vector database. This may take a few minutes...")
    db = Chroma.from_documents(
        chunks, embeddings, persist_directory=CHROMA_PATH
    )
    print(f"Database successfully saved to {CHROMA_PATH}! Ready for RAG.")

    # --- NEW: Extract and Embed Images with CLIP ---
    print("\n--- Starting Multimodal Image Extraction ---")
    try:
        import multimodal_processor
        multimodal_processor.process_pdfs()
        print("Multimodal processing complete.")
    except Exception as e:
        print(f"Multimodal processing failed: {e}")

if __name__ == "__main__":
    main()
