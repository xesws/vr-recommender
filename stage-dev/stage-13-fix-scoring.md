# Stage 13 Complete: Confidence Scoring Fix

**Date:** 2025-11-24
**Focus:** Correcting misleading confidence scores for inferred recommendations.

## 1. The Issue
User testing revealed a logical contradiction in the UI:
- The system correctly identified that no direct apps existed for "Machine Learning" and used a Semantic Bridge to recommend "VR Fitness".
- However, it displayed these bridged results as **"100% match"** because the scoring logic normalized the top result to 1.0, regardless of its absolute quality.
- This misled users into thinking "VR Fitness" was a perfect tool for Machine Learning.

## 2. The Fix
- **Logic Update (`vr_recommender.py`):**
    - Modified the `likeliness_score` calculation.
    - Introduced a **Confidence Cap** for bridged results.
    - **Rule:** If `retrieval_source == "semantic_bridge"`, the normalized score is capped at **0.49** (49%).
- **Result:**
    - Direct matches (e.g., "Maths" -> "GeoGebra") can still reach 100%.
    - Inferred matches (e.g., "ML" -> "Fitness") are now honestly presented as < 50% matches, aligning with the "related to" explanation.

## 3. Verification
- **Query:** "Machine Learning"
- **Before:** "VR Fitness (100% match)"
- **After:** "VR Fitness (**49% match**)"

## 4. Conclusion
The system's scoring is now semantically consistent with its retrieval logic. It successfully manages user expectations by visually distinguishing between high-confidence direct hits and lower-confidence inferred suggestions.
