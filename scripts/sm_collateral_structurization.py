import os
import json
import pandas as pd
import fitz  # PyMuPDF


class CollateralPDFParser:
    def __init__(self, pdf_path):
        self.pdf_path = pdf_path
        self.file_name = os.path.basename(pdf_path)
        self.file_type = "collateral"

    def parse_pdf(self, file_id):
        content_blocks = []

        doc = fitz.open(self.pdf_path)
        for page_num, page in enumerate(doc, start=1):
            text = page.get_text("text")  # Extract full page text
            if not text.strip():
                continue

            # Split on double newlines or paragraph-like blocks
            paragraphs = [p.strip() for p in text.split('\n\n') if p.strip()]
            for para_num, para_text in enumerate(paragraphs, start=1):
                clean_text = para_text.replace("\u00a0", " ")
                content_blocks.append({
                    "page": page_num,
                    "paragraph": para_num,
                    "text": clean_text
                })

        content_json = {
            "file_id": file_id,
            "filename": self.file_name,
            "content": content_blocks
        }

        return {
            "file_id": file_id,
            "file_name": self.file_name,
            "content_json": json.dumps(content_json),
            "file_type": self.file_type
        }



if __name__ == "__main__":
    root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    pdf_dir = os.path.join(root_dir, "data", "sources", "collateral")
    output_csv = os.path.join(root_dir, "data", "supabase_structured_data", "parsed_collaterals.csv")

    all_records = []
    pdf_files = [f for f in os.listdir(pdf_dir) if f.endswith(".pdf")]

    for i, pdf_file in enumerate(sorted(pdf_files), start=1):
        file_id = f"col_{i:03d}"
        pdf_path = os.path.join(pdf_dir, pdf_file)
        parser = CollateralPDFParser(pdf_path)
        parsed_data = parser.parse_pdf(file_id)
        all_records.append(parsed_data)

    df = pd.DataFrame(all_records)
    df.to_csv(output_csv, index=False)
    print(f"Parsed {len(pdf_files)} PDFs using PyMuPDF. Data saved to: {output_csv}")
