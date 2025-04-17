import os
import re
import pickle
from typing import List
from sentence_transformers import SentenceTransformer

# ———————————————————————————————————————————————
TRANSCRIPT_PATH = "transcript_punctuated.txt"
CHUNK_SIZE = 100  
EMBEDDING_MODEL_NAME = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
EMBEDDINGS_OUTPUT = "embeddings.pkl"

# ———————————————————————————————————————————————
def read_transcript(path: str) -> str:
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def split_into_chunks(text: str, chunk_size: int) -> List[str]:
    words = text.split()
    chunks = []

    for i in range(0, len(words), chunk_size):
        chunk = " ".join(words[i:i + chunk_size])
        chunks.append(chunk)

    return chunks


def generate_embeddings(chunks: List[str], model_name: str) -> List[List[float]]:
    model = SentenceTransformer(model_name)
    return model.encode(chunks, show_progress_bar=True)


def save_embeddings(chunks: List[str], embeddings: List[List[float]], path: str):
    with open(path, "wb") as f:
        pickle.dump({"chunks": chunks, "embeddings": embeddings}, f)


# ———————————————————————————————————————————————
def run_embedding_pipeline():
    if not os.path.exists(TRANSCRIPT_PATH):
        return

    text = read_transcript(TRANSCRIPT_PATH)

    chunks = split_into_chunks(text, CHUNK_SIZE)

    embeddings = generate_embeddings(chunks, EMBEDDING_MODEL_NAME)

    save_embeddings(chunks, embeddings, EMBEDDINGS_OUTPUT)


# ———————————————————————————————————————————————
if __name__ == "__main__":
    run_embedding_pipeline()
