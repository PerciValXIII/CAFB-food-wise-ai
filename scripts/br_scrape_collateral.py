import os
import json
import fitz  # PyMuPDF
import datetime
import numpy as np
import cv2
import pytesseract
from pathlib import Path
from pdf2image import convert_from_path
from ultralytics import YOLO  # AI-based infographic extraction
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

class ScrapeCollateral:
    def __init__(self, source_dir, output_file, image_dir, stats_file, collateral_images_file, model_path="yolov8_custom.pt"):
        """Initialize scraper with source directory and output paths."""
        self.source_dir = Path(source_dir).resolve()
        self.output_file = Path(output_file).resolve()
        self.image_dir = Path(image_dir).resolve()
        self.stats_file = Path(stats_file).resolve()
        self.collateral_images_file = Path(collateral_images_file).resolve()

        # Load AI Model for infographic detection
        self.model = model = YOLO("yolov8x.pt")  # This will automatically download the latest version

        # Ensure output directories exist
        self.output_file.parent.mkdir(parents=True, exist_ok=True)
        self.image_dir.mkdir(parents=True, exist_ok=True)
        self.stats_file.parent.mkdir(parents=True, exist_ok=True)

        print(f"[INFO] Initialized ScrapeCollateral for directory: {self.source_dir}")

    def extract_metadata(self, pdf_path):
        """Extract metadata from the PDF file."""
        try:
            doc = fitz.open(pdf_path)
            metadata = doc.metadata
            return {
                "Title": metadata.get("title", "Unknown"),
                "Author": metadata.get("author", "Unknown"),
                "Subject": metadata.get("subject", "Unknown"),
                "CreationDate": metadata.get("creationDate", "Unknown"),
                "ModificationDate": metadata.get("modDate", "Unknown"),
            }
        except Exception as e:
            print(f"[ERROR] Failed to extract metadata for {pdf_path}: {e}")
            return {}

    def extract_text(self, pdf_path):
        """Extract text along with its page and paragraph location."""
        collateral = []
        word_count = 0
        try:
            doc = fitz.open(pdf_path)
            for page_num, page in enumerate(doc, start=1):
                text = page.get_text("text")
                paragraphs = text.split("\n\n")
                for para_index, paragraph in enumerate(paragraphs, start=1):
                    words = paragraph.strip().split()
                    word_count += len(words)
                    collateral.append({
                        "page": page_num,
                        "paragraph": para_index,
                        "text": paragraph.strip()
                    })
        except Exception as e:
            print(f"[ERROR] Failed to extract text from {pdf_path}: {e}")
        return collateral, word_count

    def extract_images(self, pdf_path, pdf_index):
        """Converts each page to an image and extracts smaller infographics using AI."""
        base_images = []
        extracted_images = []
        image_metadata = []

        try:
            pages = convert_from_path(pdf_path, dpi=300)
            for page_index, page in enumerate(pages):
                base_filename = f"col_{pdf_index:03}.png"
                base_filepath = self.image_dir / base_filename

                # Save full-page image
                page.save(base_filepath, "PNG")
                base_images.append(base_filename)
                image_metadata.append({
                    "image_name": base_filename,
                    "source_pdf": pdf_path.name,
                    "page_number": page_index + 1,
                    "type": "full-page"
                })

                # Convert image to OpenCV format
                img_cv = np.array(page)
                img_cv = cv2.cvtColor(img_cv, cv2.COLOR_RGB2BGR)

                # Use AI model for infographic detection
                results = self.model(img_cv)

                for obj_index, obj in enumerate(results[0].boxes.xyxy):
                    x1, y1, x2, y2 = map(int, obj)
                    cropped_infographic = img_cv[y1:y2, x1:x2]

                    # Save extracted infographic
                    infographic_filename = f"col_{pdf_index:03}-{obj_index:03}.png"
                    infographic_filepath = self.image_dir / infographic_filename
                    cv2.imwrite(str(infographic_filepath), cropped_infographic)
                    extracted_images.append(infographic_filename)
                    
                    image_metadata.append({
                        "image_name": infographic_filename,
                        "source_pdf": pdf_path.name,
                        "page_number": page_index + 1,
                        "type": "infographic"
                    })

        except Exception as e:
            print(f"[ERROR] Failed to extract images from {pdf_path}: {e}")

        self.save_to_jsonl(image_metadata, self.collateral_images_file, append=True)
        return base_images, extracted_images

    def process_pdfs(self):
        """Process all PDFs and save structured data."""
        pdf_files = sorted(self.source_dir.glob("*.pdf"))  # Sort alphanumerically
        all_data = []
        text_data = []
        image_counts = {}

        if not pdf_files:
            print("[WARNING] No PDF files found in the source directory.")
            return

        print(f"[INFO] Found {len(pdf_files)} PDF files. Processing...")

        for idx, pdf_file in enumerate(pdf_files, start=1):
            print(f"[INFO] Processing: {pdf_file.name}")

            metadata = self.extract_metadata(pdf_file)
            text_entries, word_count = self.extract_text(pdf_file)
            base_images, extracted_images = self.extract_images(pdf_file, idx)

            file_link = f"./{pdf_file.relative_to(self.source_dir.parent)}"

            pdf_entry = {
                "file_name": pdf_file.name,
                "file_path": file_link,
                "metadata": metadata,
                "word_count": word_count,
                "base_images": base_images,
                "extracted_infographics": extracted_images,
                "text_data": text_entries,
            }

            all_data.append(pdf_entry)
            text_data.append(" ".join([entry["text"] for entry in text_entries]))
            image_counts[pdf_file.name] = len(extracted_images)

        self.save_to_jsonl(all_data, self.output_file)
        self.compute_text_similarity(text_data, pdf_files, image_counts)

    def compute_text_similarity(self, text_data, pdf_files, image_counts):
        """Computes textual similarity across all documents and saves stats."""
        print("\n[INFO] Running similarity analysis...")

        if len(text_data) < 2:
            print("[WARNING] Not enough documents for similarity comparison.")
            return

        vectorizer = TfidfVectorizer(stop_words="english")
        tfidf_matrix = vectorizer.fit_transform(text_data)
        similarity_matrix = cosine_similarity(tfidf_matrix)

        stats = []
        for i, pdf1 in enumerate(pdf_files):
            for j, pdf2 in enumerate(pdf_files):
                if i < j:
                    stats.append({
                        "file1": pdf1.name,
                        "file2": pdf2.name,
                        "similarity": round(similarity_matrix[i][j], 4),
                        "image_count1": image_counts.get(pdf1.name, 0),
                        "image_count2": image_counts.get(pdf2.name, 0),
                    })

        self.save_to_json(stats, self.stats_file)

    def save_to_jsonl(self, data, file_path, append=False):
        """Saves data to a JSONL file, appending if required."""
        try:
            mode = "a" if append else "w"
            with open(file_path, mode, encoding="utf-8") as file:
                for entry in data:
                    file.write(json.dumps(entry, ensure_ascii=False) + "\n")
            print(f"[INFO] Saved {len(data)} records to {file_path}")
        except Exception as e:
            print(f"[ERROR] Failed to save data: {e}")


    def save_to_json(self, data, file_path):
        """Saves data to a JSON file."""
        try:
            with open(file_path, "w", encoding="utf-8") as file:
                json.dump(data, file, ensure_ascii=False, indent=4)
            print(f"[INFO] Saved statistics to {file_path}")
        except Exception as e:
            print(f"[ERROR] Failed to save statistics: {e}")

# Example Usage
if __name__ == "__main__":
    base_path = Path(__file__).resolve().parent
    source_directory = base_path / "../source"
    output_jsonl = base_path / "collateral.jsonl"
    image_directory = base_path / "images"
    stats_file = base_path / "collateral_stats.jsonl"
    collateral_images_file = image_directory / "collateral-images.jsonl"

    scraper = ScrapeCollateral(source_directory, output_jsonl, image_directory, stats_file, collateral_images_file)
    scraper.process_pdfs()
