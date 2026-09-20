"""
📸 Photo Finder Agent
Scans a directory and finds all photos containing a specific person
using face recognition (face_recognition + OpenCV).
"""

import os
import sys
import json
import argparse
from pathlib import Path
from datetime import datetime

# ── dependency check ────────────────────────────────────────────────────────
try:
    import face_recognition
    import cv2
    import numpy as np
    from PIL import Image
except ImportError as e:
    print(f"[ERROR] Missing dependency: {e}")
    print("Run:  pip install face_recognition opencv-python pillow")
    sys.exit(1)


# ── supported image extensions ───────────────────────────────────────────────
IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".bmp", ".webp", ".tiff", ".tif"}


# ╔══════════════════════════════════════════════════════╗
# ║              PHOTO FINDER AGENT                      ║
# ╚══════════════════════════════════════════════════════╝

class PhotoFinderAgent:
    """
    An agent that scans a directory for photos and identifies
    all images containing a specific person.
    """

    def __init__(self, tolerance: float = 0.55, verbose: bool = True):
        """
        Args:
            tolerance: Face match threshold (lower = stricter). Default 0.55.
            verbose:   Print progress to console.
        """
        self.tolerance = tolerance
        self.verbose = verbose
        self.reference_encodings: list = []
        self.results: dict = {
            "matched": [],
            "no_match": [],
            "no_face_detected": [],
            "errors": [],
        }

    # ── internal helpers ─────────────────────────────────────────────────────

    def _log(self, msg: str):
        if self.verbose:
            print(msg)

    def _load_image(self, path: str):
        """Load image via face_recognition (handles EXIF rotation via PIL)."""
        try:
            pil_img = Image.open(path).convert("RGB")
            return np.array(pil_img)
        except Exception as e:
            raise RuntimeError(f"Cannot open image: {e}")

    def _find_images(self, directory: str) -> list[Path]:
        """Recursively find all image files in a directory."""
        root = Path(directory)
        if not root.exists():
            raise FileNotFoundError(f"Directory not found: {directory}")
        images = [
            p for p in root.rglob("*")
            if p.suffix.lower() in IMAGE_EXTS and p.is_file()
        ]
        return sorted(images)

    # ── public API ───────────────────────────────────────────────────────────

    def load_reference(self, reference_photo: str) -> bool:
        """
        Load the reference photo and extract face encoding(s).

        Args:
            reference_photo: Path to a clear photo of the target person.

        Returns:
            True if at least one face was found, False otherwise.
        """
        self._log(f"\n[Agent] Loading reference photo: {reference_photo}")
        try:
            img = self._load_image(reference_photo)
            encodings = face_recognition.face_encodings(img)
            if not encodings:
                self._log("[Agent] ⚠️  No face detected in the reference photo.")
                self._log("       Make sure the photo is clear and well-lit.")
                return False
            self.reference_encodings = encodings
            self._log(f"[Agent] ✅ Reference loaded — {len(encodings)} face(s) encoded.")
            return True
        except Exception as e:
            self._log(f"[Agent] ❌ Error loading reference: {e}")
            return False

    def scan_directory(self, directory: str) -> dict:
        """
        Scan a directory and find photos containing the reference person.

        Args:
            directory: Path to the folder to search (scanned recursively).

        Returns:
            dict with keys: matched, no_match, no_face_detected, errors.
        """
        if not self.reference_encodings:
            raise RuntimeError("Call load_reference() before scan_directory().")

        images = self._find_images(directory)
        total = len(images)
        self._log(f"\n[Agent] 🔍 Found {total} image(s) in '{directory}'\n")

        for idx, img_path in enumerate(images, 1):
            label = f"[{idx}/{total}] {img_path.name}"
            try:
                img = self._load_image(str(img_path))
                # Detect all faces in the photo
                face_locations = face_recognition.face_locations(img, model="hog")

                if not face_locations:
                    self._log(f"  ⬜  {label}  → no faces detected")
                    self.results["no_face_detected"].append(str(img_path))
                    continue

                # Encode detected faces
                face_encodings = face_recognition.face_encodings(img, face_locations)

                # Compare each detected face against reference
                matched = False
                for enc in face_encodings:
                    distances = face_recognition.face_distance(
                        self.reference_encodings, enc
                    )
                    if any(distances <= self.tolerance):
                        matched = True
                        break

                if matched:
                    self._log(f"  ✅  {label}  → MATCH")
                    self.results["matched"].append(str(img_path))
                else:
                    self._log(f"  ❌  {label}  → no match ({len(face_locations)} face(s))")
                    self.results["no_match"].append(str(img_path))

            except Exception as e:
                self._log(f"  ⚠️  {label}  → error: {e}")
                self.results["errors"].append({"path": str(img_path), "error": str(e)})

        return self.results

    def save_report(self, output_path: str = "report.json") -> str:
        """Save a JSON report of the scan results."""
        report = {
            "timestamp": datetime.now().isoformat(),
            "tolerance": self.tolerance,
            "summary": {
                "matched": len(self.results["matched"]),
                "no_match": len(self.results["no_match"]),
                "no_face_detected": len(self.results["no_face_detected"]),
                "errors": len(self.results["errors"]),
            },
            "results": self.results,
        }
        with open(output_path, "w") as f:
            json.dump(report, f, indent=2)
        return output_path

    def print_summary(self):
        """Print a human-readable summary."""
        matched = self.results["matched"]
        print("\n" + "═" * 55)
        print("  📊  SCAN SUMMARY")
        print("═" * 55)
        print(f"  ✅  Matched photos   : {len(matched)}")
        print(f"  ❌  No match         : {len(self.results['no_match'])}")
        print(f"  ⬜  No face detected : {len(self.results['no_face_detected'])}")
        print(f"  ⚠️   Errors           : {len(self.results['errors'])}")
        print("═" * 55)

        if matched:
            print("\n  📁  Photos with the person:")
            for p in matched:
                print(f"     → {p}")
        else:
            print("\n  No matching photos found.")
        print()


# ── CLI entry point ───────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="📸 Photo Finder Agent — find all photos containing a specific person",
        formatter_class=argparse.RawTextHelpFormatter,
    )
    parser.add_argument(
        "reference",
        help="Path to a clear reference photo of the person to find",
    )
    parser.add_argument(
        "directory",
        help="Path to the photo directory to scan (searched recursively)",
    )
    parser.add_argument(
        "--tolerance",
        type=float,
        default=0.55,
        help="Face match tolerance (0.0–1.0). Lower = stricter. Default: 0.55",
    )
    parser.add_argument(
        "--save-report",
        metavar="FILE",
        default=None,
        help="Save results to a JSON report file",
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Suppress per-image output (only show summary)",
    )

    args = parser.parse_args()

    print("╔════════════════════════════════════════╗")
    print("║      📸  Photo Finder Agent  📸         ║")
    print("╚════════════════════════════════════════╝")

    agent = PhotoFinderAgent(tolerance=args.tolerance, verbose=not args.quiet)

    # Step 1: Load reference
    if not agent.load_reference(args.reference):
        sys.exit(1)

    # Step 2: Scan directory
    try:
        agent.scan_directory(args.directory)
    except FileNotFoundError as e:
        print(f"[ERROR] {e}")
        sys.exit(1)

    # Step 3: Print summary
    agent.print_summary()

    # Step 4: Optionally save report
    if args.save_report:
        path = agent.save_report(args.save_report)
        print(f"  💾  Report saved to: {path}\n")


if __name__ == "__main__":
    main()
