import sqlite3
import numpy as np
import os
from embeddings import get_embedding, cosine_similarity

DB_PATH = os.path.join(os.path.dirname(__file__), 'results.db')

# Ensure table exists
def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS results (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        query TEXT,
        embedding BLOB,
        summary TEXT
    )''')
    conn.commit()
    conn.close()

init_db()

def save_result(query: str, embedding: np.ndarray, summary: str):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('INSERT INTO results (query, embedding, summary) VALUES (?, ?, ?)',
              (query, embedding.tobytes(), summary))
    conn.commit()
    conn.close()

def get_similar(query: str, embedding: np.ndarray, threshold: float = 0.8):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('SELECT query, embedding, summary FROM results')
    rows = c.fetchall()
    conn.close()
    for q, emb_blob, summary in rows:
        emb = np.frombuffer(emb_blob, dtype=np.float32)
        sim = cosine_similarity(embedding, emb)
        if sim >= threshold:
            return q, summary, sim
    return None 