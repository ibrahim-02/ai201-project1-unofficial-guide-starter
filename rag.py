"""
Grounded generation pipeline.

query() — the main entry point:
  1. Retrieves top-4 chunks from ChromaDB using embed.retrieve()
  2. Builds a context block from the chunks
  3. Sends a strictly grounded prompt to Groq (llama-3.3-70b-versatile)
  4. Returns the answer text and deduplicated list of source filenames

Grounding mechanism: the system prompt explicitly forbids the model from
using outside knowledge and requires it to say "I don't have enough
information" when the context is insufficient. Source attribution is
required in every response.
"""

import os
from groq import Groq
from dotenv import load_dotenv
from embed import retrieve

load_dotenv()

LLM_MODEL = "llama-3.3-70b-versatile"
TOP_K = 4

SYSTEM_PROMPT = """You are an unofficial student guide assistant for Boston University (BU) and Northeastern University (NEU).

STRICT RULES:
1. Answer ONLY using the information provided in the CONTEXT sections below.
2. Do NOT use your general training knowledge. If the answer is not in the context, say exactly: "I don't have enough information in my documents to answer that."
3. Do not speculate, infer beyond the context, or fill in gaps from outside knowledge.
4. Every response MUST end with a Sources line listing the filenames the answer draws from.

Format your Sources line exactly like this:
Sources: [filename1.txt, filename2.txt]"""


def build_context(chunks: list[dict]) -> str:
    parts = []
    for i, chunk in enumerate(chunks, 1):
        parts.append(f"--- CONTEXT {i} (source: {chunk['source']}) ---\n{chunk['text']}")
    return "\n\n".join(parts)


def query(user_question: str) -> tuple[str, list[str]]:
    """
    Run the full RAG pipeline for a user question.
    Returns (answer_text, list_of_source_filenames).
    """
    chunks = retrieve(user_question, k=TOP_K)
    context = build_context(chunks)
    sources = list(dict.fromkeys(c["source"] for c in chunks))  # deduplicated, order-preserved

    user_message = f"{context}\n\nQuestion: {user_question}"

    client = Groq(api_key=os.environ["GROQ_API_KEY"])
    response = client.chat.completions.create(
        model=LLM_MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_message},
        ],
        temperature=0.2,
        max_tokens=1024,
    )

    answer = response.choices[0].message.content.strip()
    return answer, sources


if __name__ == "__main__":
    test_questions = [
        "What is the best dining hall at Boston University?",
        "How does Northeastern's co-op program work?",
        "Which MBTA line serves Northeastern University?",
        "What neighborhoods do BU students typically live off-campus?",
        "What makes the malloc lab in CS 3650 at Northeastern so difficult?",
    ]

    for q in test_questions:
        print(f"\nQ: {q}")
        print("-" * 60)
        answer, sources = query(q)
        print(answer)
        print()
