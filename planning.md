# Project 1 Planning: The Unofficial Guide

> Write this document before you write any pipeline code.
> Your spec and architecture diagram are what you'll use to direct AI tools (Claude, Copilot, etc.) to generate your implementation — the more specific they are, the more useful the generated code will be.
> Update the Retrieval Approach and Chunking Strategy sections if you change your approach during implementation.
> Update this file before starting any stretch features.

---

## Domain

**Unofficial student life guides for Boston University (BU) and Northeastern University (NEU).**

This knowledge is valuable because official university websites and orientation packets are sanitized, promotional, and incomplete. They won't tell you which dining hall has the shortest lines at 7 pm, which CS professor is worth rearranging your schedule for, which neighborhood has the best rent-to-commute ratio, or what the Northeastern co-op process actually looks like from the inside. Students rely on r/BostonU, r/NEU, and r/boston for this kind of ground-truth knowledge — but it's scattered across years of posts and threads. A RAG system over curated student-written documents can surface this knowledge through natural-language questions.

---

## Documents

| # | Source | Description | URL or location |
|---|--------|-------------|-----------------|
| 1 | r/BostonU (synthetic) | BU dining halls ranked — Marciano, Warren, Towers | documents/dining_01_bu_dining_halls.txt |
| 2 | r/NEU (synthetic) | Northeastern dining guide — IV, Stetson, Outtakes | documents/dining_02_neu_dining.txt |
| 3 | r/BostonU (synthetic) | BU dorm tier list — Warren, West Campus, StuVi2 | documents/housing_03_bu_dorms.txt |
| 4 | r/NEU (synthetic) | NEU housing guide — dorms, co-op housing, Mission Hill | documents/housing_04_neu_housing.txt |
| 5 | r/BostonU (synthetic) | BU CS curriculum tips — CS 111, 210, 330 | documents/courses_05_bu_cs_tips.txt |
| 6 | r/NEU (synthetic) | Northeastern co-op complete guide — NUworks, compensation, housing | documents/courses_06_neu_coop_guide.txt |
| 7 | r/BostonU (synthetic) | BU professor recommendations — CS, Math, Engineering | documents/courses_07_bu_professors.txt |
| 8 | r/BostonU (synthetic) | BU freshman survival guide — academics, transit, Boston tips | documents/survival_08_bu_freshman_guide.txt |
| 9 | r/NEU (synthetic) | NEU freshman survival guide — co-op culture, campus geography | documents/survival_09_neu_freshman_guide.txt |
| 10 | r/boston (synthetic) | MBTA guide for BU and NEU students — Green Line, Orange Line | documents/transit_10_boston_mbta_guide.txt |
| 11 | r/NEU (synthetic) | NEU CS curriculum — Fundies, OOD, Systems, Algorithms | documents/courses_11_neu_cs_curriculum.txt |
| 12 | r/boston (synthetic) | Off-campus life — Allston, Mission Hill, groceries, wellness | documents/survival_12_boston_offcampus_life.txt |

*Note: Documents are synthetic but modeled closely on real Reddit post structures and content common in r/BostonU, r/NEU, and r/boston. Reddit's current API blocks unauthenticated scraping; these documents represent the type and quality of student-written knowledge that would be collected from those sources.*

---

## Chunking Strategy

**Chunk size:** 500 characters

**Overlap:** 100 characters

**Reasoning:**
The documents are forum-style posts with a mix of short paragraphs, bullet points, and section headers. Key facts (e.g., "Ruggles is the main Orange Line stop for Northeastern" or "Dining dollars don't roll over to the following fall") are often contained within 1–3 sentences. A 500-character chunk captures roughly 2–4 sentences, which is enough context to answer a specific factual question without pulling in unrelated information. A chunk size much larger (e.g., 1500 characters) would conflate multiple topics within one post into a single chunk, hurting retrieval precision. The 100-character overlap ensures that sentences split across chunk boundaries are still represented in at least one chunk.

---

## Retrieval Approach

**Embedding model:** `all-MiniLM-L6-v2` via sentence-transformers (runs locally, no API key required)

**Top-k:** 4 chunks per query

**Production tradeoff reflection:**
For a real deployment, I would consider `text-embedding-3-small` from OpenAI or `embed-english-v3.0` from Cohere. The tradeoffs to weigh:
- *Context length*: all-MiniLM-L6-v2 has a 256-token limit, which is tight for long passages; OpenAI's models handle 8k+ tokens.
- *Accuracy on domain-specific text*: a general-purpose model may miss slang or abbreviations specific to college life (e.g., "IV" for International Village at NEU). A fine-tuned or larger model would likely perform better.
- *Cost and latency*: local models like all-MiniLM-L6-v2 have zero API cost and ~10ms latency on CPU; API-hosted models add cost and network latency.
- *Multilingual support*: not relevant for this English-only corpus, but important for universities with international student populations.
For this project, the local model is the right choice: free, fast, and sufficient for the scale of 12 documents.

---

## Evaluation Plan

| # | Question | Expected answer |
|---|----------|-----------------|
| 1 | What is the best dining hall at Boston University? | Marciano Commons is ranked best for variety; Café 3 equivalent is Towers for calm atmosphere. |
| 2 | How does Northeastern's co-op program work? | Students alternate between full-time academic semesters and 6-month paid work placements, typically 2–3 co-ops total, starting sophomore/junior year via NUworks. |
| 3 | Which MBTA line serves Northeastern University? | The Orange Line (Ruggles stop) and the Green Line E branch (Northeastern stop) both serve NEU. |
| 4 | What neighborhoods do BU students typically live off-campus? | Allston and Brighton are most common; Fenway/Kenmore for those willing to pay more. |
| 5 | What makes the malloc lab in CS 3650 at Northeastern so difficult? | CS 3650 is Computer Systems (C programming, memory management, processes); the malloc lab (implementing your own memory allocator) is famously hard — start it the week it's assigned. |

---

## Anticipated Challenges

1. **Chunk boundary splits**: A fact like "The Ruggles stop is on the Orange Line" could be split across a chunk boundary, leaving each half without enough context. The 100-character overlap mitigates this but doesn't eliminate it.

2. **Cross-document ambiguity**: Some topics (transit, off-campus housing) appear in multiple documents with different levels of detail. If a query about "Orange Line" returns chunks from both the MBTA guide and the NEU freshman guide, the retrieved context may be slightly redundant rather than complementary. The LLM needs to handle this gracefully.

---

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                     INGESTION                           │
│  documents/*.txt  →  ingest.py  →  raw text + metadata  │
└───────────────────────────┬─────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────┐
│                     CHUNKING                            │
│  chunk_text()  →  500-char chunks, 100-char overlap     │
│  Library: Python string slicing (no external lib)       │
└───────────────────────────┬─────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────┐
│              EMBEDDING + VECTOR STORE                   │
│  sentence-transformers all-MiniLM-L6-v2  →  embeddings  │
│  ChromaDB (local)  →  persisted vector store            │
│  Script: embed.py                                       │
└───────────────────────────┬─────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────┐
│                     RETRIEVAL                           │
│  User query  →  embed query  →  ChromaDB top-4 search   │
└───────────────────────────┬─────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────┐
│                   GENERATION                            │
│  Retrieved chunks + system prompt  →  Groq API          │
│  Model: llama-3.3-70b-versatile                         │
│  Output: grounded answer + source citations             │
└───────────────────────────┬─────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────┐
│                  QUERY INTERFACE                        │
│  Streamlit web UI (app.py)  →  localhost:8501           │
└─────────────────────────────────────────────────────────┘
```

---

## AI Tool Plan

**Milestone 2 — Ingestion and chunking:**
Give Claude the Chunking Strategy section above and ask it to implement `ingest.py` with a `load_documents()` function that reads all `.txt` files from `documents/` and returns a list of `{text, source}` dicts, and a `chunk_text()` function using the 500-char / 100-overlap spec. Verify by checking that chunk count matches expectations and no chunk exceeds 500 characters.

**Milestone 3 — Embedding and retrieval:**
Give Claude the Retrieval Approach section and ask it to implement `embed.py` that loads chunks from `ingest.py`, embeds them with `all-MiniLM-L6-v2`, and upserts them into a ChromaDB collection with source metadata. Verify by querying ChromaDB directly and checking that top results match the expected document for a known query.

**Milestone 4 — Generation and interface:**
Give Claude the Architecture diagram and the Grounded Generation requirements and ask it to implement `rag.py` (query pipeline) and `app.py` (Streamlit UI). Verify by running the 5 evaluation questions and checking that every response includes a source citation.
