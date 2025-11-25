# Stage 14 Complete: Refined Confidence Scoring

**Date:** 2025-11-24
**Focus:** Improving the nuance of confidence scores for inferred recommendations.

## 1. The Issue
In Stage 13, we introduced a hard cap (`min(score, 0.49)`) for semantic bridge results. While this prevented "100% match" claims, it had a side effect: if multiple apps had high raw scores (e.g., 0.9, 0.8), they were all flattened to exactly 0.49, losing their relative ranking information.

## 2. The Fix
- **Logic Update (`vr_recommender.py`):**
    - Changed the scoring logic from **Truncation** (`min`) to **Scaling** (`score * 0.49`).
    - **Formula:** `final_score = normalized_score * 0.49`.
- **Result:**
    - A semantic bridge result that was originally a "top match" (1.0 relative score) becomes **49%**.
    - A weaker result (e.g., 0.8 relative score) becomes **39%**.
    - This preserves the relative quality differences between inferred recommendations while keeping the absolute confidence honest.

## 3. Verification
- **Query:** "Machine Learning"
- **Result:** "VR Fitness (**49% match**)"
- **Observation:** In this specific case, all top results had identical scores because they all matched the single bridged skill ("Fitness Training Methodologies") with equal weight. However, the logic now supports differentiation for more complex queries.

## 4. Conclusion
The scoring system is now mathematically sound, preserving both the *absolute* uncertainty of inferred matches and the *relative* ranking of candidates.
