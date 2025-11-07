# 🎬 Quick Demo Summary

## 🎯 **What to Demo (5-7 minutes)**

### **1. Q&A - Ambiguous Query** ⭐ **MOST IMPRESSIVE** (2 min)
**Show**: Student asks "I don't get this" → System asks for clarification with context-aware suggestions

**Why it's impressive**: Most AI systems guess or give generic answers. This one intelligently asks for clarification.

**Endpoint**: `POST /api/v1/qa/query`
```json
{
  "student_id": "...",
  "query": "I don't get this",
  "context": {"recent_sessions": ["Algebra"]}
}
```

---

### **2. Practice - Bank Items Unavailable** (2 min)
**Show**: Request practice for niche topic → System generates practice on-the-fly

**Why it's impressive**: System never fails. Always provides value, even when data is missing.

**Endpoint**: `POST /api/v1/practice/assign`
```json
{
  "student_id": "...",
  "subject": "Advanced Quantum Physics",
  "num_items": 5
}
```

---

### **3. Progress Dashboard - Completed Goal** (1-2 min)
**Show**: Student completes goal → System celebrates and suggests related subjects

**Why it's impressive**: Keeps engagement high, guides next steps, shows cross-subject awareness.

**Endpoint**: `GET /api/v1/progress/{student_id}`

---

## 🚀 **Quick Setup**

1. **Start server**: `python run_server.py`
2. **Open API docs**: http://localhost:8000/docs
3. **Use demo examples**: See `scripts/demo_examples.http`

---

## 📊 **Key Talking Points**

- ✅ **45+ tests passing** - Production quality
- ✅ **Edge cases handled** - Real-world ready
- ✅ **Intelligent responses** - Context-aware
- ✅ **Never fails silently** - Always provides value
- ✅ **Tutor oversight** - Built-in control

---

## 🎯 **Full Demo Guide**

See `DEMO_GUIDE.md` for:
- Complete 15-20 minute demo
- All edge cases
- Talking points
- Q&A preparation

