from pathlib import Path
from pypdf import PdfReader
import chromadb
from chromadb.utils import embedding_functions

PAPERS_DIR = Path("papers")
CHROMA_PATH = "./chroma_db"
CHUNK_SIZE = 800
CHUNK_OVERLAP = 100


def extract_pages(pdf_path):
    """Yield (page_number, text) for every page that has real text."""
    reader = PdfReader(pdf_path)
    for page_num, page in enumerate(reader.pages, start=1):
        text = page.extract_text() or ""
        if text.strip():
            yield page_num, text


def chunk_text(text, chunk_size=CHUNK_SIZE, overlap=CHUNK_OVERLAP):
    """Split text into overlapping chunks so meaning isn't lost at boundaries."""
    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunks.append(text[start:end])
        start += chunk_size - overlap
    return chunks


def main():
    # all-MiniLM-L6-v2: small (~80MB), fast, the standard starting embedding model.
    # Chroma calls this automatically whenever we add or query text, we never
    # touch the raw vectors ourselves.
    embedding_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
        model_name="all-MiniLM-L6-v2"
    )
    client = chromadb.PersistentClient(path=CHROMA_PATH)
    collection = client.get_or_create_collection(
        name="climate_papers",
        embedding_function=embedding_fn,
    )

    pdf_files = list(PAPERS_DIR.glob("*.pdf"))
    if not pdf_files:
        print(f"No PDFs found in {PAPERS_DIR}/. Add some and re-run.")
        return

    all_ids, all_docs, all_metadatas = [], [], []
    chunk_counter = 0

    for pdf_path in pdf_files:
        print(f"Processing {pdf_path.name}...")
        for page_num, page_text in extract_pages(pdf_path):
            for chunk in chunk_text(page_text):
                chunk_counter += 1
                # Metadata is what lets us cite a real source and page later,
                # not just return text with no attribution.
                all_ids.append(f"{pdf_path.stem}-p{page_num}-c{chunk_counter}")
                all_docs.append(chunk)
                all_metadatas.append({"source": pdf_path.name, "page": page_num})

    BATCH_SIZE = 1000
    for i in range(0, len(all_ids), BATCH_SIZE):
        collection.add(
            ids=all_ids[i:i + BATCH_SIZE],
            documents=all_docs[i:i + BATCH_SIZE],
            metadatas=all_metadatas[i:i + BATCH_SIZE],
        )
        print(f"  Added batch {i // BATCH_SIZE + 1} ({min(i + BATCH_SIZE, len(all_ids))}/{len(all_ids)} chunks)")
    print(f"Stored {chunk_counter} chunks from {len(pdf_files)} PDF(s) in {CHROMA_PATH}")
    
    #collection.add(ids=all_ids, documents=all_docs, metadatas=all_metadatas)
    #print(f"Stored {chunk_counter} chunks from {len(pdf_files)} PDF(s) in {CHROMA_PATH}")


if __name__ == "__main__":
    main()
