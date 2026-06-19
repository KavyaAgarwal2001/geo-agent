import chromadb
from chromadb.utils import embedding_functions
import pytest

CHROMA_PATH = "./chroma_db"

# A real test query set: each pair is (question, a keyword/phrase we'd expect
# in a genuinely relevant answer). This is what makes the test objective
# instead of "I read the output and it seemed fine."
RETRIEVAL_CASES = [
    ("How much will sea levels rise by 2100?", "sea level"),
    ("What are the impacts of global warming on coral reefs?", "coral"),
    ("What is the carbon budget for limiting warming to 1.5 degrees?", "carbon budget"),
    ("How does climate change affect food security?", "food security"),
    ("What adaptation strategies are recommended for climate change?", "adaptation"),
]


@pytest.fixture(scope="module")
def collection():
    embedding_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
        model_name="all-MiniLM-L6-v2"
    )
    client = chromadb.PersistentClient(path=CHROMA_PATH)
    return client.get_collection(name="climate_papers", embedding_function=embedding_fn)


@pytest.mark.parametrize("query,expected_keyword", RETRIEVAL_CASES)
def test_retrieval_returns_relevant_chunk(collection, query, expected_keyword):
    results = collection.query(query_texts=[query], n_results=3)
    retrieved_text = " ".join(results["documents"][0]).lower()
    assert expected_keyword.lower() in retrieved_text, (
        f"None of the top 3 chunks for {query!r} mention {expected_keyword!r}"
    )
