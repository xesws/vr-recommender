
## 5. Chatbot Logic Fix (2025-11-24)

### The Issue
User reported that typing "Machine Learning" triggered the "Welcome/Greeting" message instead of a recommendation search.

### Root Cause
Naive substring matching in `parse_user_intent`:
```python
if any(g in msg_lower for g in ["hello", "hi", "hey"]):
    return "greeting"
```
The string "Mac**hi**ne Learning" contains "hi", causing a false positive.

### The Fix
Updated `flask_api.py` to use Regex with word boundaries:
```python
if re.search(r'\b(hello|hi|hey)\b', msg_lower):
    return "greeting"
```

### Verification
- Input: "Machine Learning" -> Intent: "recommendation" (Correct)
- Input: "Hi there" -> Intent: "greeting" (Correct)
