# 🐍 Virtual Environment (venv) Setup Guide

## ✅ Current Status

**Python Version**: 3.14.6 ✅  
**Required Packages**: Already installed ✅

### Installed Packages Check
```
✅ pydantic 2.13.4
✅ pytest 9.1.1
✅ streamlit (ready)
```

---

## ❓ Do You Need venv?

### **Answer: NO - Not Required But Recommended**

#### You CAN Run Without venv:
✅ Your Python is already set up  
✅ All packages are installed globally  
✅ You can start immediately  

#### BUT venv Is Recommended Because:
✅ Keeps project dependencies isolated  
✅ Prevents conflicts with other projects  
✅ Best practice for Python development  
✅ Makes it portable (share with others)  
✅ Easy cleanup (delete folder to uninstall)  

---

## 🚀 Option 1: Run WITHOUT venv (Fastest - Right Now!)

```bash
cd d:\sem5\EDI

# Just run it immediately
python -m pytest tests/ -v
streamlit run app.py
```

**Pros**: Immediate, no setup needed  
**Cons**: Global packages, not isolated  

---

## 🔧 Option 2: Create venv (Recommended)

### Step 1: Create Virtual Environment

```bash
cd d:\sem5\EDI
python -m venv venv
```

This creates a `venv/` folder with isolated Python environment.

### Step 2: Activate venv

```bash
# Windows - PowerShell
.\venv\Scripts\Activate.ps1

# Windows - CMD
venv\Scripts\activate.bat

# After activation, your prompt will show:
# (venv) C:\sem5\EDI>
```

### Step 3: Install Dependencies

```bash
pip install -r requirements.txt
```

### Step 4: Run Project

```bash
# Tests
python -m pytest tests/ -v

# UI
streamlit run app.py

# Research
python research/run_evaluation.py
```

### Step 5: Deactivate When Done

```bash
deactivate

# Prompt returns to normal (no (venv) prefix)
```

---

## 📋 Quick Comparison

| Feature | Without venv | With venv |
|---------|------------|----------|
| Setup Time | 0 seconds | 30 seconds |
| Global Isolation | ❌ No | ✅ Yes |
| Easy Cleanup | ❌ No | ✅ Yes (delete folder) |
| Portability | ❌ Limited | ✅ Good |
| Current Status | ✅ Ready | ⚠️ Need setup |

---

## 📝 My Recommendation

### For Quick Testing
```bash
cd d:\sem5\EDI
streamlit run app.py
```
**No venv needed - start immediately!**

### For Regular Development
```bash
cd d:\sem5\EDI
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
streamlit run app.py
```
**Better practice - isolated environment**

---

## 🐛 Troubleshooting

### Issue: "venv cannot be imported"
```bash
python -m venv venv
```
(Should work with Python 3.14)

### Issue: "Activate.ps1 cannot be loaded"
**Solution**: Run PowerShell as Administrator or use:
```bash
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
.\venv\Scripts\Activate.ps1
```

### Issue: Package not found after venv activate
**Solution**: Install requirements in venv:
```bash
pip install -r requirements.txt
```

---

## ✨ What I Recommend

Since you **already have everything installed globally**, you have two paths:

### Path A: Start Immediately (0 seconds setup)
```bash
cd d:\sem5\EDI
streamlit run app.py
```
**Just run it - everything works!**

### Path B: Proper Setup (1 minute setup)
```bash
cd d:\sem5\EDI
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
streamlit run app.py
```
**Better for long-term development**

---

## 📚 Detailed venv Guide (If You Want It)

### Create venv
```bash
cd d:\sem5\EDI
python -m venv venv
```

### Activate (PowerShell)
```bash
.\venv\Scripts\Activate.ps1
```

### Install packages
```bash
pip install -r requirements.txt
```

### Verify installation
```bash
pip list
python -m pytest tests/ --co -q
```

### Run everything
```bash
# Tests
python -m pytest tests/ -v

# Research
python research/run_evaluation.py

# UI
streamlit run app.py
```

### Deactivate when done
```bash
deactivate
```

### Delete venv (to clean up)
```bash
deactivate
Remove-Item -Recurse venv
```

---

## 🎯 Bottom Line

**Your Python is ready to go right now!**

You have two options:

### ⚡ **Option 1: Fastest - Run Now**
```bash
cd d:\sem5\EDI && streamlit run app.py
```
Takes 0 seconds, works immediately.

### 🛠️ **Option 2: Best Practice - Setup venv**
```bash
cd d:\sem5\EDI
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
streamlit run app.py
```
Takes 1 minute, better for development.

---

**Which would you prefer?** Choose one and I'll guide you through it! 🚀
