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

## AI Usage

**Instance 1**

- *What I gave the AI:* The Chunking Strategy section from planning.md (500-char chunks, 100-char overlap, forum-style documents with bullet points and section headers) and the requirement to strip Reddit header boilerplate.
- *What it produced:* `ingest.py` with `load_documents()`, `_clean()` (regex to strip Title/Subreddit/URL/Score header lines), and `chunk_text()` using fixed character splitting.
- *What I changed or overrode:* After running chunk inspection and seeing mid-word chunk starts, I directed the AI to rewrite `chunk_text()` using paragraph-aware splitting (`re.split(r"\n\n+", text)`). I also added a `MIN_CHUNK_SIZE = 150` constant after discovering a 119-character stub chunk (the opening sentence of a dorm guide). The final implementation differs significantly from what was first generated.

**Instance 2**

- *What I gave the AI:* The Architecture diagram from planning.md (showing ChromaDB + all-MiniLM-L6-v2 + Groq), the grounding requirement ("answer only from retrieved context, cite sources"), and the Gradio skeleton structure from the milestone instructions.
- *What it produced:* `rag.py` with a system prompt, `build_context()`, and `query()` returning `(answer, sources)`; and `app.py` with a Gradio Blocks UI.
- *What I changed or overrode:* I strengthened the system prompt from a soft suggestion ("please use the documents") to a strict rule set with a specific fallback phrase and numbered rules. I also added programmatic source extraction (`sources = list(dict.fromkeys(c["source"] for c in chunks))`) so attribution is guaranteed regardless of LLM behavior. I added the empty-input guard in `handle_query()` after noticing the API would be called unnecessarily on blank queries.
