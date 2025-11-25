# Stage 9 Fix: Broken Knowledge Graph Architecture & Fallback Logic

## 1. Diagnosis (2025-11-24)

### The Issue
The user reported nonsensical recommendations (e.g., "VR productivity" apps for a "Cyber Security" query). 
A diagnostic script revealed a critical structural failure in the Knowledge Graph (Neo4j):

1.  **Zero Semantic Paths**: There are **0 paths** following the canonical `(Course)-[:DEVELOPS]->(Skill)<-[:DEVELOPS]-(VRApp)` pattern.
2.  **Shortcut Abuse**: There are **2386 direct relationships** (`:RECOMMENDS`) between Courses and VR Apps. This bypasses the entire RAG logic, likely relying on a hardcoded or naive keyword matching process during graph construction.
3.  **Missing Course Skills**: Cyber Security courses (and likely others) have **no connected Skill nodes**.
4.  **Dirty Data**: Some VR Apps have `None` as their title but possess dozens of duplicate skills.

### Root Cause Analysis
- **`build_graph.py` Flaw**: The script likely iterates through courses and apps and, instead of linking them via shared skills, it aggressively creates direct links based on weak heuristics (e.g., category matching or TF-IDF overlap) to ensure connectivity.
- **Data Ingestion Failure**: The output from the skill extraction pipeline (`skills.json` or updated `courses.json`) is either not being read correctly, or the extraction process failed to save the `course_id -> skill_ids` mapping.
- **Retriever Logic**: The RAG retriever likely has a fallback mechanism that queries these direct `:RECOMMENDS` edges when semantic paths are missing, leading to low-quality results.

## 2. Repair Plan

### Goal
Force the recommendation engine to rely **exclusively** on the semantic `Skill` bridge. Remove all direct shortcuts. Ensure every Course and App is properly anchored to the Skill graph.

### Step 1: Fix Graph Construction (`build_graph.py`)
1.  **Remove Direct Linking**: Delete any code block performing `MERGE (c)-[:RECOMMENDS]->(a)`.
2.  **Verify Skill Ingestion**: 
    - Ensure the script loads the *latest* `courses.json` (which should contain extracted skills).
    - Ensure it loads `vr_apps.json` (with skills).
    - Explicitly create `(Course)-[:DEVELOPS]->(Skill)` relationships.
    - Explicitly create `(VRApp)-[:DEVELOPS]->(Skill)` relationships.
3.  **Data Cleaning**: Add a filter to skip Apps where `title` is null or empty.

### Step 2: Verify Data Pipeline Integration
Check `data_collection/src/data_collection/course_fetcher_improved.py` and `skill_extraction/src/skill_extraction/semantic_deduplicator.py`.
- **Verification**: Does the final JSON output actually containing a list of skills for each course?
- **Action**: If `courses.json` lacks skill tags, we must re-run the skill assignment (or at least the merging) step properly.

### Step 3: Refine RAG Retriever (`src/rag/retriever.py`)
- **Logic Update**: The Cypher query used for retrieval must be strict.
    - *Current (Likely)*: `MATCH (c)-[*1..2]-(a) ...` (Too loose)
    - *Target*: 
      ```cypher
      MATCH (c:Course {id: $course_id})-[:DEVELOPS]->(s:Skill)<-[:DEVELOPS]-(a:VRApp)
      WITH c, a, count(s) as SharedSkills, collect(s.name) as SkillNames
      ORDER BY SharedSkills DESC
      RETURN a, SharedSkills, SkillNames
      ```

### Step 4: Validation Strategy
1.  **Wipe & Rebuild**: Run `./stop_all.sh`, then `python knowledge_graph/scripts/build_graph.py`.
2.  **Re-Diagnose**: Run the `diagnose_graph_logic.py` script again.
    - Expectation: `Direct Connections` = 0.
    - Expectation: `Indirect Paths` > 1000.
3.  **E2E Test**: Run the Chatbot query "I am learning cyber security..." again.
    - Expectation: Even if no perfect VR app exists, it should NOT return "Productivity" apps unless they share specific security-related skills (unlikely). It's better to return "No strong matches found" than garbage.

## 3. Execution Log
- [ ] Modify `build_graph.py`
- [ ] Verify `courses.json` content
- [ ] Rebuild Graph
- [ ] Verify with `diagnose_graph_logic.py`
- [ ] Test Chatbot
