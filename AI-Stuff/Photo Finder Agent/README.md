# 📸 Photo Finder Agent

A Python agent that scans a directory and finds **all photos containing a specific person** using face recognition.

---

## ⚙️ Installation

```bash
# 1. Install dependencies (CMake required for dlib)
pip install -r requirements.txt

# macOS shortcut for dlib/cmake:
# brew install cmake

# Ubuntu shortcut:
# sudo apt-get install build-essential cmake libopenblas-dev
```

---

## 🚀 Usage

### Command Line

```bash
python agent.py <reference_photo> <directory_to_scan> [options]
```

**Examples:**

```bash
# Basic scan
python agent.py john.jpg ~/Photos/

# Stricter matching (fewer false positives)
python agent.py john.jpg ~/Photos/ --tolerance 0.45

# Save results to JSON report
python agent.py john.jpg ~/Photos/ --save-report results.json

# Quiet mode (summary only)
python agent.py john.jpg ~/Photos/ --quiet
```

### In Python

```python
from agent import PhotoFinderAgent

agent = PhotoFinderAgent(tolerance=0.55)

# Load reference photo of the person
agent.load_reference("john.jpg")

# Scan a directory (recursive)
results = agent.scan_directory("/path/to/photos")

# Print summary
agent.print_summary()

# Save JSON report
agent.save_report("report.json")

# Access matched files
print(results["matched"])   # list of matching photo paths
```

---

## 🎛️ Options

| Option | Default | Description |
|--------|---------|-------------|
| `--tolerance` | `0.55` | Match threshold (0.0–1.0). Lower = stricter. |
| `--save-report` | None | Save JSON results to a file. |
| `--quiet` | False | Suppress per-image logs. |

---

## 📂 Output Structure

```
matched             → photos where the person was found
no_match            → photos with faces, but not the person
no_face_detected    → photos with no faces at all
errors              → photos that couldn't be processed
```

---

## 💡 Tips

- Use a **clear, front-facing** photo as the reference for best accuracy.
- If you get too many false positives → lower the tolerance (e.g. `0.45`).
- If the person is being missed → raise tolerance slightly (e.g. `0.60`).
- The agent scans **recursively**, so nested folders are included.
- Supported formats: JPG, JPEG, PNG, BMP, WEBP, TIFF.
