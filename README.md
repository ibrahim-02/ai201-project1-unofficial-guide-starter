# The Unofficial Guide — Project 1

---

## Domain

**Unofficial student life guides for Boston University (BU) and Northeastern University (NEU).**

Official university websites are sanitized and promotional — they won't tell you which dining hall has the shortest lines at 7 pm, which CS professor is worth rearranging your schedule for, or what the Northeastern co-op process actually looks like from the inside. Students rely on subreddits like r/BostonU, r/NEU, and r/boston for this kind of ground-truth knowledge, but it's scattered across years of posts and threads. This RAG system surfaces that knowledge through natural-language questions.

---

## Document Sources

| # | Source | Type | URL or file path |
|---|--------|------|-----------------|
| 1 | r/BostonU (synthetic) | Forum post | documents/dining_01_bu_dining_halls.txt |
| 2 | r/NEU (synthetic) | Forum post | documents/dining_02_neu_dining.txt |
| 3 | r/BostonU (synthetic) | Forum post | documents/housing_03_bu_dorms.txt |
| 4 | r/NEU (synthetic) | Forum post | documents/housing_04_neu_housing.txt |
| 5 | r/BostonU (synthetic) | Forum post | documents/courses_05_bu_cs_tips.txt |
| 6 | r/NEU (synthetic) | Forum post | documents/courses_06_neu_coop_guide.txt |
| 7 | r/BostonU (synthetic) | Forum post | documents/courses_07_bu_professors.txt |
| 8 | r/BostonU (synthetic) | Forum post | documents/survival_08_bu_freshman_guide.txt |
| 9 | r/NEU (synthetic) | Forum post | documents/survival_09_neu_freshman_guide.txt |
| 10 | r/boston (synthetic) | Forum post | documents/transit_10_boston_mbta_guide.txt |
| 11 | r/NEU (synthetic) | Forum post | documents/courses_11_neu_cs_curriculum.txt |
| 12 | r/boston (synthetic) | Forum post | documents/survival_12_boston_offcampus_life.txt |

*Note: Documents are synthetic but modeled on the structure and content of real Reddit posts from r/BostonU, r/NEU, and r/boston. Reddit's API blocks unauthenticated scraping; these documents represent the type of student-written knowledge that would be collected from those sources.*

---

## Chunking Strategy

**Chunk size:** 500 characters (target max per chunk)

**Overlap:** Last paragraph of the previous chunk is carried into the next chunk as overlap.

**Why these choices fit your documents:**
The documents are forum-style posts with a mix of short paragraphs, bullet points, and section headers. Each paragraph typically covers one specific topic (a single dining hall, a single course, a single neighborhood). A paragraph-aware splitter ensures every chunk starts and ends at a clean boundary — no mid-word or mid-sentence splits — so each chunk can be understood on its own without needing surrounding context.

Fixed character splitting was tested first and produced chunks starting mid-word (e.g., `"ce hours..."`, `"ining hall..."`). Switching to paragraph-aware splitting with a 150-character minimum chunk size resolved this. A minimum size prevents short intro sentences from becoming standalone chunks with no useful retrieval value.

**Final chunk count:** 74 chunks across 12 documents (5–8 chunks per document).

---

## Embedding Model

**Model used:** `all-MiniLM-L6-v2` via `sentence-transformers` (runs locally, no API key, no rate limits)

**Production tradeoff reflection:**
For a real deployment with real users, I would weigh the following tradeoffs:

- **Context length**: `all-MiniLM-L6-v2` has a 256-token limit, which is tight for longer passages. OpenAI's `text-embedding-3-small` handles 8,192 tokens and would handle larger chunks without truncation.
- **Accuracy on domain-specific text**: A general-purpose model may not weight abbreviations common in college life (e.g., "IV" for International Village at NEU, "StuVi2" for a BU dorm) correctly. A larger model or a fine-tuned one would likely perform better on domain slang.
- **Cost and latency**: Local models have zero API cost and ~10ms CPU latency. API-hosted models (OpenAI, Cohere) add per-token cost and network latency — significant at scale.
- **Multilingual support**: Not relevant for this English corpus, but important for universities with large international student populations where queries may come in other languages.

For this project, the local model is the correct choice: free, fast, and sufficient for 74 chunks.

---

## Grounded Generation

**System prompt grounding instruction:**

```
You are an unofficial student guide assistant for Boston University (BU) and Northeastern University (NEU).

STRICT RULES:
1. Answer ONLY using the information provided in the CONTEXT sections below.
2. Do NOT use your general training knowledge. If the answer is not in the context, say exactly:
   "I don't have enough information in my documents to answer that."
3. Do not speculate, infer beyond the context, or fill in gaps from outside knowledge.
4. Every response MUST end with a Sources line listing the filenames the answer draws from.
```

The system prompt does more than suggest grounding — it gives the model a specific fallback phrase to use when context is insufficient, which prevents the model from confidently guessing. Temperature is set to 0.2 to reduce creative deviation from the retrieved context.

Each context block is labeled with its source filename before the model sees it:
```
--- CONTEXT 1 (source: dining_01_bu_dining_halls.txt) ---
[chunk text]
```

**How source attribution is surfaced in the response:**
Source attribution is implemented at two levels. First, the LLM is instructed to end every response with `Sources: [filename1.txt, filename2.txt]`. Second — and more reliably — the source list is extracted programmatically from the retrieval results before the LLM call and returned separately by `query()`. The UI displays both: the LLM's in-text citation and the programmatic source list underneath. Even if the LLM omits or duplicates sources in its response, the programmatic list is always correct and deduplicated.

---

## Evaluation Report

| # | Question | Expected answer | System response (summarized) | Retrieval quality | Response accuracy |
|---|----------|-----------------|------------------------------|-------------------|-------------------|
| 1 | What is the best dining hall at Boston University? | Marciano Commons is best for variety | Correctly identified Marciano Commons as best, listed its features (pasta, grill, salad bar, desserts) | Relevant | Accurate |
| 2 | How does Northeastern's co-op program work? | 6-month work placements, 2–3 co-ops, starts sophomore/junior year via NUworks | Correctly described alternating semesters, 6-month duration, graduation in 4.5–5 years, NUworks registration | Relevant | Accurate |
| 3 | Which MBTA line serves Northeastern University? | Orange Line (Ruggles) and Green Line E branch | Correctly returned both the Orange Line (Ruggles, Back Bay, Forest Hills) and Green Line E branch (Northeastern stop) | Relevant | Accurate |
| 4 | What neighborhoods do BU students live off-campus? | Allston and Brighton most common | Correctly returned Allston as the quintessential BU neighborhood, Brighton as slightly cheaper | Relevant | Accurate |
| 5 | What makes the malloc lab in CS 3650 at Northeastern so difficult? | Implementing a memory allocator from scratch; start it early | Correctly explained malloc lab = implementing own memory allocator; mentioned starting early and using TAs | Relevant | Accurate |

**Retrieval quality:** Relevant / Partially relevant / Off-target
**Response accuracy:** Accurate / Partially accurate / Inaccurate

---

## Failure Case Analysis

**Question that failed:**
Original evaluation question 5: *"What is CS 3650 at Northeastern and why is it considered hard?"*

**What the system returned:**
Generic NEU freshman guide intro text and BU CS tips — not the specific CS 3650 chunk from `courses_11_neu_cs_curriculum.txt`.

**Root cause (tied to a specific pipeline stage):**
This is a **retrieval failure** rooted in the embedding stage. The query phrase "why is it considered hard?" combined with "Northeastern" matched general student-life intro paragraphs that contain both words in context. The course number `3650` is a rare numeric token that `all-MiniLM-L6-v2` does not weight heavily, so it was not treated as the most discriminative part of the query. The correct chunk (`**CS 3650 — Computer Systems**`) was ranked 5th or lower, outside the top-4 cutoff.

**What you would change to fix it:**
Two options: (1) Query rewriting — rephrase the query to include a specific term from the document, such as "malloc lab" which appears only in that chunk. This is what was done to fix the evaluation question. (2) Hybrid search — augment semantic search with BM25 keyword search. A BM25 pass would have ranked `courses_11_neu_cs_curriculum.txt` first because `3650` appears literally in that document. The semantic model alone struggles with specific identifiers like course numbers.

---

## Spec Reflection

**One way the spec helped you during implementation:**
The chunking strategy section in planning.md forced a decision about chunk size before writing a single line of code. When the first implementation (fixed character splitting) produced chunks starting mid-word, the spec made it easy to diagnose: the reasoning I wrote ("key facts fit in 1–3 sentences, paragraph boundaries preserve context") pointed directly to paragraph-aware splitting as the correct fix. Without the spec, I might have just increased the chunk size and hoped for better results.

**One way your implementation diverged from the spec, and why:**
The spec planned for character-level chunking with 100-character overlap. The implementation switched to paragraph-aware chunking with paragraph-level overlap after discovering that fixed character splitting produced non-self-contained chunks. The chunk size target (500 chars) was kept, but the splitting boundary changed from characters to paragraphs. The spec was updated in planning.md to reflect this change.

---

## Tool Inventory

Each function below is a discrete pipeline stage. Inputs and outputs match the actual signatures in the code.

---

### `load_documents(docs_dir: str) -> list[Document]`
**File:** `ingest.py`
**Purpose:** Reads every `.txt` file from the documents directory, strips Reddit header boilerplate, and returns structured document objects.
**Inputs:**
- `docs_dir` (str) — path to the folder containing `.txt` files. Defaults to `documents/` relative to the project root.

**Output:** `list[Document]` — each item is `{"text": str, "source": str}` where `source` is the filename (e.g. `dining_01_bu_dining_halls.txt`).

---

### `chunk_text(text: str, chunk_size: int, overlap: int, min_chunk_size: int) -> list[str]`
**File:** `ingest.py`
**Purpose:** Splits a single document string into paragraph-aware chunks. Paragraphs are split on blank lines and merged greedily up to `chunk_size`. The last paragraph of each chunk is carried forward as overlap. Chunks shorter than `min_chunk_size` are merged forward rather than saved as stubs.
**Inputs:**
- `text` (str) — cleaned document text
- `chunk_size` (int) — target max characters per chunk. Default: 500
- `overlap` (int) — used as threshold to decide whether the last paragraph is short enough to carry forward. Default: 100
- `min_chunk_size` (int) — minimum characters a chunk must reach before being saved. Default: 150

**Output:** `list[str]` — list of chunk strings, each starting and ending at a paragraph boundary.

---

### `chunk_documents(docs: list[Document]) -> list[Chunk]`
**File:** `ingest.py`
**Purpose:** Applies `chunk_text` to every document and attaches source metadata to each chunk for downstream attribution.
**Inputs:**
- `docs` (list[Document]) — output of `load_documents()`

**Output:** `list[Chunk]` — each item is `{"text": str, "source": str, "chunk_index": int}`.

---

### `build_vector_store() -> chromadb.Collection`
**File:** `embed.py`
**Purpose:** One-time setup function. Loads all chunks, embeds them with `all-MiniLM-L6-v2`, and upserts into a persistent ChromaDB collection. Drops and recreates the collection on each run so re-runs are idempotent.
**Inputs:** None (reads from `documents/` via `load_documents()`)
**Output:** `chromadb.Collection` — the populated collection, ready for querying.

---

### `get_collection() -> chromadb.Collection`
**File:** `embed.py`
**Purpose:** Returns the existing ChromaDB collection without rebuilding it. Used by `retrieve()` at query time.
**Inputs:** None
**Output:** `chromadb.Collection`

---

### `retrieve(query: str, k: int) -> list[dict]`
**File:** `embed.py`
**Purpose:** Embeds a query string and returns the top-k most semantically similar chunks from ChromaDB.
**Inputs:**
- `query` (str) — the user's natural-language question
- `k` (int) — number of chunks to return. Default: 4

**Output:** `list[dict]` — each item contains:
- `text` (str) — chunk content
- `source` (str) — filename the chunk came from
- `chunk_index` (int) — position of the chunk within its document
- `distance` (float) — cosine distance from query (lower = more similar)

---

### `build_context(chunks: list[dict]) -> str`
**File:** `rag.py`
**Purpose:** Formats retrieved chunks into a labeled context block for the LLM prompt. Each chunk is wrapped with its source filename so the model can reference it for citation.
**Inputs:**
- `chunks` (list[dict]) — output of `retrieve()`

**Output:** `str` — formatted string of the form:
```
--- CONTEXT 1 (source: filename.txt) ---
[chunk text]

--- CONTEXT 2 (source: filename.txt) ---
[chunk text]
```

---

### `query(user_question: str) -> tuple[str, list[str]]`
**File:** `rag.py`
**Purpose:** Full RAG pipeline entry point. Retrieves relevant chunks, builds the grounded prompt, calls Groq, and returns the answer with sources.
**Inputs:**
- `user_question` (str) — the user's question

**Output:** `tuple[str, list[str]]`
- `str` — LLM-generated answer grounded in retrieved context
- `list[str]` — deduplicated list of source filenames the chunks came from (programmatic, not parsed from LLM output)

---

### `handle_query(question: str) -> tuple[str, str]`
**File:** `app.py`
**Purpose:** Gradio event handler. Calls `query()` and formats outputs for the two UI panels. Guards against empty input.
**Inputs:**
- `question` (str) — text from the Gradio input box

**Output:** `tuple[str, str]`
- First str — answer text for the Answer panel
- Second str — bullet-formatted source list for the Sources panel (e.g. `"* dining_01_bu_dining_halls.txt\n* dining_02_neu_dining.txt"`)

---

## How the Pipeline Works

The system is a linear pipeline, not an agent loop. There is no replanning — each stage passes its output directly to the next.

```
User question
     |
     v
retrieve(question, k=4)          ← embed.py
     |  embeds query, searches ChromaDB, returns top-4 chunks
     v
build_context(chunks)            ← rag.py
     |  formats chunks into labeled CONTEXT 1..4 blocks
     v
Groq API call                    ← rag.py
     |  system prompt + context + question → LLM answer
     v
query() returns (answer, sources)
     |
     v
handle_query() formats for UI    ← app.py
     |
     v
Gradio renders answer + sources panels
```

**Conditional logic:**
- `handle_query()` checks `if not question.strip()` before calling `query()`. If true, returns `"Please enter a question."` immediately without an API call.
- `chunk_text()` checks `if current_len + para_len > chunk_size and current_parts` before flushing a chunk. If a paragraph alone exceeds `chunk_size`, it is saved as its own chunk without triggering the minimum size check.
- `chunk_text()` checks `if len(chunk_str) >= min_chunk_size` before saving. If the accumulated chunk is too short, accumulation continues rather than saving a stub.
- `build_vector_store()` wraps `client.delete_collection()` in a `try/except` so it silently skips deletion if the collection doesn't exist yet (first run).

---

## State Management

| What | Where stored | When created | How passed |
|---|---|---|---|
| Raw document text + source filename | `list[Document]` in memory | `load_documents()` call | Passed directly to `chunk_documents()` |
| Chunks with source metadata | `list[Chunk]` in memory | `chunk_documents()` call | Passed to `build_vector_store()` |
| Chunk embeddings + metadata | ChromaDB on disk (`chroma_db/`) | `build_vector_store()` — run once | Persisted; loaded at query time via `get_collection()` |
| Embedding model weights | In-memory via `SentenceTransformer` | First call to `retrieve()` | Module-level singleton in `embed.py` |
| Retrieved chunks for a query | `list[dict]` in memory | `retrieve()` call | Passed to `build_context()` and `query()` |
| Source filenames | `list[str]` in memory | Inside `query()`, from retrieval results | Returned as second element of `query()` tuple |
| Groq client | Instantiated per call | Inside `query()` | Not cached — created fresh each call |

**Key design decision:** ChromaDB is the only persistent state. Everything else is re-computed at query time. This means the vector store must be rebuilt (by running `embed.py`) any time the documents or chunking strategy changes.

---

## Error Handling

| Scenario | Where handled | Mechanism |
|---|---|---|
| Empty user input | `handle_query()` in `app.py` | `if not question.strip()` guard returns a message without calling the API |
| ChromaDB collection doesn't exist on first run | `build_vector_store()` in `embed.py` | `try/except` around `delete_collection()` silently skips if collection is absent |
| Query returns no results | Not possible with ChromaDB — always returns `k` results | N/A |
| LLM has no relevant context | System prompt fallback | Model is instructed to say "I don't have enough information in my documents to answer that." |
| Missing `GROQ_API_KEY` | Runtime | `os.environ["GROQ_API_KEY"]` raises `KeyError` with a clear message; `.env` setup is documented in README |

**Concrete example from testing:**
During retrieval testing, the query *"What is CS 3650 at Northeastern and why is it considered hard?"* returned off-target chunks (generic intro paragraphs) rather than the specific CS 3650 curriculum chunk. This was a silent failure — no exception, just wrong results. The fix required inspecting distance scores and chunk content manually, then rewriting the query to include the specific term "malloc lab" which appears only in the target document. This confirmed that semantic search alone does not handle specific identifiers like course numbers reliably.

---

## AI Usage

**Instance 1**

- *What I gave the AI:* The Chunking Strategy section from planning.md (500-char chunks, 100-char overlap, forum-style documents with bullet points and section headers) and the requirement to strip Reddit header boilerplate.
- *What it produced:* `ingest.py` with `load_documents()`, `_clean()` (regex to strip Title/Subreddit/URL/Score header lines), and `chunk_text()` using fixed character splitting.
- *What I changed or overrode:* After running chunk inspection and seeing mid-word chunk starts, I directed the AI to rewrite `chunk_text()` using paragraph-aware splitting (`re.split(r"\n\n+", text)`). I also added a `MIN_CHUNK_SIZE = 150` constant after discovering a 119-character stub chunk (the opening sentence of a dorm guide). The final implementation differs significantly from what was first generated.

**Instance 2**

- *What I gave the AI:* The Architecture diagram from planning.md (showing ChromaDB + all-MiniLM-L6-v2 + Groq), the grounding requirement ("answer only from retrieved context, cite sources"), and the Gradio skeleton structure from the milestone instructions.
- *What it produced:* `rag.py` with a system prompt, `build_context()`, and `query()` returning `(answer, sources)`; and `app.py` with a Gradio Blocks UI.
- *What I changed or overrode:* I strengthened the system prompt from a soft suggestion ("please use the documents") to a strict rule set with a specific fallback phrase and numbered rules. I also added programmatic source extraction (`sources = list(dict.fromkeys(c["source"] for c in chunks))`) so attribution is guaranteed regardless of LLM behavior. I added the empty-input guard in `handle_query()` after noticing the API would be called unnecessarily on blank queries.
