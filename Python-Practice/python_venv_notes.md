# Python Virtual Environments — Complete Notes

---

## What is a Virtual Environment?

A **virtual environment** is an isolated Python installation that has its own packages, dependencies, and interpreter — separate from your system-wide Python installation.

> Think of it like this: your system Python is a **shared kitchen**, and a virtual environment is your own **private kitchen** where you can cook however you want without affecting anyone else.

---

## The Problem Without Virtual Environments

Imagine you have two projects:

- **Project A** needs `Django 3.2`
- **Project B** needs `Django 4.2`

Without virtual environments, both projects share the same global Python installation. You **can't install both versions simultaneously**, so one project will always break.

---

## Virtual Environment vs. Global Python

| Feature             | Global Python                         | Virtual Environment                    |
| ------------------- | ------------------------------------- | -------------------------------------- |
| Package isolation   | ❌ Shared across all projects          | ✅ Per-project packages                 |
| Version conflicts   | ❌ Common problem                      | ✅ No conflicts                         |
| Dependency tracking | ❌ Hard to know what belongs where     | ✅ Clean `requirements.txt` per project |
| System safety       | ❌ Bad installs can break system tools | ✅ System Python untouched              |
| Reproducibility     | ❌ Hard to replicate environment       | ✅ Easy to share exact setup            |
| Clean uninstall     | ❌ Leftovers everywhere                | ✅ Just delete the folder               |

---

## Quick Usage

```bash
# Create a virtual environment
python -m venv myenv

# Activate it
source myenv/bin/activate        # macOS/Linux
myenv\Scripts\activate           # Windows

# Install packages (only affects this environment)
pip install django requests

# Save dependencies
pip freeze > requirements.txt

# Deactivate when done
deactivate
```

---

## Key Benefits

1. **Conflict-free** — different projects can use different library versions
2. **Reproducible** — `requirements.txt` lets anyone recreate your exact environment
3. **Safe** — you can't accidentally break system Python or other projects
4. **Clean** — easy to delete and start fresh
5. **Professional standard** — expected in all real-world Python projects

---

## Can You Ship a venv to Others?

**Short answer: You technically can, but you really shouldn't.**

### Why Shipping a venv Directly is a Bad Idea

A virtual environment contains **hardcoded absolute paths** baked into it at creation time.

For example, inside `myenv/bin/activate`:
```bash
VIRTUAL_ENV="/home/yourname/projects/myapp/myenv"  # hardcoded!
```

Problems when sharing:
- Their username is different → path breaks
- Their OS may be different (Windows vs Linux) → completely incompatible
- Their Python version may differ → binary mismatches
- The venv folder **must** sit at the exact same path → practically impossible

### The Right Way: Ship `requirements.txt` Instead

**You do this:**
```bash
pip freeze > requirements.txt
```

**They do this:**
```bash
python -m venv myenv
source myenv/bin/activate
pip install -r requirements.txt
```

They get an **identical set of packages**, built fresh for their own machine. ✅

### Rule of Thumb

> Ship the **recipe** (`requirements.txt`), not the **kitchen** (`venv` folder).

### Modern Alternatives

| Tool                       | File Used                  | What it Does                                         |
| -------------------------- | -------------------------- | ---------------------------------------------------- |
| `pip` + `requirements.txt` | `requirements.txt`         | Simple, universally understood                       |
| `pipenv`                   | `Pipfile` + `Pipfile.lock` | Manages venv + deps together                         |
| `poetry`                   | `pyproject.toml`           | Modern dep management + packaging                    |
| `conda`                    | `environment.yml`          | Popular in data science, handles non-Python deps too |

### What You Actually Ship

```
myproject/
├── main.py
├── utils.py
├── requirements.txt   ✅ ship this
├── README.md
└── .gitignore         ← should include /myenv/
```

Your `.gitignore` should always exclude the venv folder:
```
myenv/
venv/
.venv/
```

---

## Does venv Have Its Own Python Interpreter?

**Sort of — it symlinks/copies, not a full separate installation.**

### Folder Structure of a venv

```
myenv/
├── bin/                    (Scripts/ on Windows)
│   ├── python              ← symlink to system Python
│   ├── python3             ← symlink to system Python
│   ├── pip                 ← its OWN pip (isolated)
│   └── activate
├── lib/
│   └── python3.x/
│       └── site-packages/  ← its OWN packages folder
└── pyvenv.cfg              ← config pointing to base Python
```

### Python Interpreter — Symlink, Not a Copy

- On **macOS/Linux**: `python` inside venv is a **symlink** to your system Python
- On **Windows**: a small **copy** of the interpreter is made (Windows doesn't support symlinks well)

The actual Python binary is **shared** — venv doesn't install a new Python.

### What's Shared vs Isolated

| Component                 | Shared with System?     | Isolated?           |
| ------------------------- | ----------------------- | ------------------- |
| Python interpreter binary | ✅ Shared (symlinked)    | ❌                   |
| Python version            | ✅ Same as system Python | ❌                   |
| `pip`                     | ❌                       | ✅ Own copy          |
| Installed packages        | ❌                       | ✅ Own site-packages |
| Environment variables     | ❌                       | ✅ Scoped to venv    |

### Practical Implication

Because the interpreter is symlinked, the Python version inside venv is the **same as system Python**:

```bash
python --version          # system: Python 3.11.2
source myenv/bin/activate
python --version          # venv:   Python 3.11.2  ← same!
```

You **cannot change the Python version** inside a venv. Create the venv using a specific interpreter to target a version:

```bash
python3.10 -m venv myenv-310   # uses Python 3.10
python3.11 -m venv myenv-311   # uses Python 3.11
```

---

## If You Need True Python Version Isolation — Use `pyenv`

`pyenv` lets you install and switch between multiple Python versions on the same machine, and pairs perfectly with venv:

```bash
pyenv install 3.10.12
pyenv local 3.10.12        # sets Python version for this folder
python -m venv myenv       # now uses Python 3.10.12
```

---

## Summary

| Concept                        | Key Point                                     |
| ------------------------------ | --------------------------------------------- |
| What is venv?                  | Isolated environment with its own packages    |
| Why use it?                    | Avoid dependency conflicts between projects   |
| Ship venv to others?           | ❌ No — use `requirements.txt` instead         |
| Python interpreter             | Symlinked from system, not a new installation |
| `pip` inside venv              | Fully isolated ✅                              |
| Need different Python version? | Use `pyenv` alongside venv                    |
