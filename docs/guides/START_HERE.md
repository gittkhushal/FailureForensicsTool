# 🚀 START HERE - FailureForensicsTool Quick Start

**Everything is ready to run!** Choose your preferred option below.

---

## ⚡ **Option 1: Start Immediately (No Setup)**

```bash
cd d:\sem5\EDI
streamlit run app.py
```

✅ Opens UI at `http://localhost:8501`  
✅ No venv needed  
✅ All packages already installed  
✅ Takes 5 seconds to start

**This is the recommended way to get started!**

---

## 🧪 **Option 2: Run Tests First (Verify Everything)**

```bash
cd d:\sem5\EDI
python -m pytest tests/ -v
```

✅ Runs all 178 tests  
✅ Takes ~2 seconds  
✅ Confirms system is working

**Expected Output**: `178 passed`

---

## 📊 **Option 3: Run Research Evaluation**

```bash
cd d:\sem5\EDI
python research/run_evaluation.py
```

✅ Analyzes 5 failure scenarios  
✅ Generates JSON metrics  
✅ Takes ~5 seconds  
✅ Results saved to `research/results/`

---

## 🔧 **Option 4: Setup venv (Recommended for Development)**

If you want a clean, isolated environment:

```bash
cd d:\sem5\EDI

# Create venv
python -m venv venv

# Activate
.\venv\Scripts\Activate.ps1

# Install dependencies
pip install -r requirements.txt

# Run UI
streamlit run app.py
```

Takes ~1 minute but better for long-term development.

---

## 📋 **All Available Commands**

### Run the UI
```bash
cd d:\sem5\EDI
streamlit run app.py
```

### Run Tests
```bash
python -m pytest tests/ -v              # All tests with details
python -m pytest tests/ -q              # Quick output
python -m pytest tests/test_pipeline.py # Single file
```

### Run Research Evaluation
```bash
python research/run_evaluation.py
```

### Interactive Python
```bash
python
# Then run examples from RUN_LOCALLY.md
```

---

## 🎨 **UI Features (After Running `streamlit run app.py`)**

| Page | What It Does |
|------|-------------|
| **Dashboard** | System overview & statistics |
| **Run Pipeline** | Execute pipelines with tracing |
| **Trace Explorer** | Browse past executions |
| **Failure Analysis** | Detect & classify failures |
| **Propagation Analysis** | Analyze failure spread |
| **Feedback & Evaluation** | Manage evaluation cases |
| **Analytics** | Performance metrics |

---

## 📚 **Documentation**

- **RUN_LOCALLY.md** - Complete execution guide with examples
- **VENV_SETUP.md** - Virtual environment setup (with/without venv)
- **README.md** - Project overview
- **QUICKSTART.md** - Quick reference
- **docs/METHODOLOGY.md** - Technical methodology
- **docs/architecture.md** - System architecture

---

## ✅ **Status Check**

| Component | Status |
|-----------|--------|
| Python 3.14 | ✅ Ready |
| All packages | ✅ Installed |
| Tests | ✅ 178/178 passing |
| UI | ✅ Ready to launch |
| Database | ✅ Auto-creates on first run |
| Research framework | ✅ Ready |

---

## 🎯 **Recommended Starting Path**

### Path 1: Visual Demo (Easiest)
```bash
cd d:\sem5\EDI
streamlit run app.py
```
→ See the UI in action immediately

### Path 2: Verify Everything (Safest)
```bash
cd d:\sem5\EDI
python -m pytest tests/ -v
```
→ Confirm all 178 tests pass  
→ Then run: `streamlit run app.py`

### Path 3: Full Experience (Complete)
```bash
cd d:\sem5\EDI
python -m pytest tests/ -q           # Verify
python research/run_evaluation.py    # Analyze
streamlit run app.py                 # Explore UI
```

---

## 🚀 **I Recommend: Start with Option 1**

```bash
cd d:\sem5\EDI
streamlit run app.py
```

**Then explore the 7 UI pages to understand the system!**

---

## 🐛 **Troubleshooting**

### "Module not found" error
```bash
cd d:\sem5\EDI  # Make sure you're in the right directory
```

### Need to install packages
```bash
pip install -r requirements.txt
```

### Want to use venv
See VENV_SETUP.md for detailed instructions

### Database issues
```bash
del failure_forensics.db  # Delete and it will recreate
```

---

## 📞 **Quick Help**

| Question | Answer |
|----------|--------|
| Do I need venv? | No, but recommended. See VENV_SETUP.md |
| Which command to start? | `streamlit run app.py` |
| Are tests passing? | Yes! 178/178 ✅ |
| Where's the UI? | `localhost:8501` after running streamlit |
| How do I use it? | See 7 pages in the UI or RUN_LOCALLY.md |
| Can I run without Ollama? | Yes! System has fallback methods |

---

## 🎊 **You're All Set!**

Pick an option above and get started:

1. **Want instant UI?** → `streamlit run app.py`
2. **Want to verify?** → `python -m pytest tests/ -v`
3. **Want full analysis?** → `python research/run_evaluation.py`

**Let's go!** 🚀

---

*For detailed information, see RUN_LOCALLY.md, VENV_SETUP.md, or the docs/ folder.*
