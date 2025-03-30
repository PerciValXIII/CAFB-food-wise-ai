import os
import pandas as pd

# Set base paths
base_dir = os.path.dirname(os.path.abspath(__file__))
csv_path = os.path.join(base_dir, "../data/annotated_data/text_content_annotation.csv")
ppt_dir = os.path.join(base_dir, "../data/sources/powerpoints/")
pdf_dir = os.path.join(base_dir, "../data/sources/collateral/")

# Load CSV
df = pd.read_csv(csv_path)

# Get sorted file lists
ppt_files = sorted([f for f in os.listdir(ppt_dir) if f.lower().endswith('.pptx')])
pdf_files = sorted([f for f in os.listdir(pdf_dir) if f.lower().endswith('.pdf')])

# Fill 'File Name' based on row order within each type
ppt_index, pdf_index = 0, 0
file_names = []

for _, row in df.iterrows():
    source_type = row['Source Type'].strip().lower()
    if source_type == 'powerpoint' and ppt_index < len(ppt_files):
        file_names.append(ppt_files[ppt_index])
        ppt_index += 1
    elif ('pdf' in source_type or 'collateral' in source_type) and pdf_index < len(pdf_files):
        file_names.append(pdf_files[pdf_index])
        pdf_index += 1
    else:
        file_names.append(None)  # In case of mismatch

# Assign and save
df['File Name'] = file_names
df.to_csv(csv_path, index=False)
print("CSV updated with file names based on row order.")
