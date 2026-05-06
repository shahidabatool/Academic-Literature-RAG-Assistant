import os
import fitz # PyMuPDF
import io
from PIL import Image
import torch
from transformers import CLIPProcessor, CLIPModel
from langchain_chroma import Chroma
from langchain_core.documents import Document
import numpy as np

# Configuration
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PDF_DIR = os.path.join(SCRIPT_DIR, "../Text")
IMAGE_OUT_DIR = os.path.join(SCRIPT_DIR, "../Data/extracted_images")
CHROMA_IMAGE_PATH = os.path.join(SCRIPT_DIR, "../Text/chroma_image_db")

os.makedirs(IMAGE_OUT_DIR, exist_ok=True)

# Initialize CLIP
print("Loading CLIP model (openai/clip-vit-base-patch32)...")
device = "cpu" # Default to CPU for stability in this environment
model = CLIPModel.from_pretrained("openai/clip-vit-base-patch32").to(device)
processor = CLIPProcessor.from_pretrained("openai/clip-vit-base-patch32")

class CLIPEmbeddingFunction:
    """Custom embedding function for Chroma to use CLIP, following LangChain interface."""
    def embed_documents(self, texts):
        # We don't really use this for batch embedding texts in this script, 
        # but Chroma requires it.
        embeddings = []
        for text in texts:
            inputs = processor(text=text, return_tensors="pt", padding=True).to(device)
            with torch.no_grad():
                text_features = model.get_text_features(**inputs)
            emb = text_features[0].cpu().numpy()
            emb = emb / np.linalg.norm(emb)
            embeddings.append(emb.tolist())
        return embeddings

    def embed_query(self, text):
        return self.embed_documents([text])[0]

def process_pdfs():
    # Initialize Chroma for images
    embedding_func = CLIPEmbeddingFunction()
    db = Chroma(collection_name="bpa_images", persist_directory=CHROMA_IMAGE_PATH, embedding_function=embedding_func)
    
    pdf_files = [f for f in os.listdir(PDF_DIR) if f.lower().endswith(".pdf")]
    
    for pdf_name in pdf_files:
        print(f"\nProcessing {pdf_name}...")
        pdf_path = os.path.join(PDF_DIR, pdf_name)
        doc = fitz.open(pdf_path)
        
        for page_num in range(len(doc)):
            page = doc[page_num]
            image_list = page.get_images(full=True)
            
            for img_index, img_info in enumerate(image_list):
                xref = img_info[0]
                base_image = doc.extract_image(xref)
                image_bytes = base_image["image"]
                
                # Load with PIL to check size
                try:
                    image = Image.open(io.BytesIO(image_bytes))
                    if image.width < 150 or image.height < 150:
                        continue # Skip small icons/logos
                        
                    # Save image
                    image_filename = f"{pdf_name}_p{page_num+1}_i{img_index}.jpg"
                    image_path = os.path.join(IMAGE_OUT_DIR, image_filename)
                    image.convert("RGB").save(image_path, "JPEG")
                    
                    # Generate CLIP embedding for the image
                    inputs = processor(images=image, return_tensors="pt").to(device)
                    with torch.no_grad():
                        # get_image_features returns the projected visual features (512-dim)
                        image_features = model.get_image_features(**inputs)
                    
                    # Normalize manually to ensure it works on any tensor-like output
                    embedding = image_features[0].cpu().numpy()
                    embedding = embedding / np.linalg.norm(embedding)
                    embedding = embedding.tolist()
                    
                    # Add to Chroma
                    # Note: We use a placeholder text but the embedding is the IMAGE embedding
                    db.add_texts(
                        texts=[f"Image from {pdf_name} page {page_num+1}"],
                        metadatas=[{
                            "source": pdf_name,
                            "page": page_num + 1,
                            "image_path": image_path,
                            "type": "figure"
                        }],
                        embeddings=[embedding]
                    )
                    print(f"  Extracted and embedded figure: {image_filename}")
                    
                except Exception as e:
                    print(f"  Error processing image {img_index} on page {page_num}: {e}")

if __name__ == "__main__":
    process_pdfs()
