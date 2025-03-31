import os
import pandas as pd


def fill_filenames_by_order(
    csv_relative_path="../data/annotated_data/text_content_annotation.csv",
    ppt_dir_relative="../data/sources/powerpoints/",
    pdf_dir_relative="../data/sources/collateral/"
):
    """
    Fills the 'File Name' column in the annotation CSV by assigning PowerPoint and PDF filenames
    based on row order and source type.
    
    Parameters:
        csv_relative_path (str): Relative path to the annotation CSV file.
        ppt_dir_relative (str): Relative path to the PowerPoint files directory.
        pdf_dir_relative (str): Relative path to the PDF collateral files directory.
    """
    base_dir = os.path.dirname(os.path.abspath(__file__))
    csv_path = os.path.join(base_dir, csv_relative_path)
    ppt_dir = os.path.join(base_dir, ppt_dir_relative)
    pdf_dir = os.path.join(base_dir, pdf_dir_relative)

    # Load the CSV
    df = pd.read_csv(csv_path)

    # List files
    ppt_files = sorted([f for f in os.listdir(ppt_dir) if f.lower().endswith('.pptx')])
    pdf_files = sorted([f for f in os.listdir(pdf_dir) if f.lower().endswith('.pdf')])

    # Initialize indices and output list
    ppt_index, pdf_index = 0, 0
    file_names = []

    # Iterate through each row and assign file names
    for _, row in df.iterrows():
        source_type = str(row['Source Type']).strip().lower()

        if 'powerpoint' in source_type and ppt_index < len(ppt_files):
            file_names.append(ppt_files[ppt_index])
            ppt_index += 1
        elif ('pdf' in source_type or 'collateral' in source_type) and pdf_index < len(pdf_files):
            file_names.append(pdf_files[pdf_index])
            pdf_index += 1
        else:
            file_names.append(None)  # Fallback if no match

    # Update and save the CSV
    df['File Name'] = file_names
    df.to_csv(csv_path, index=False)
    print("File Name column successfully updated.")

# Example usage (can be called from another script or main)
if __name__ == "__main__":
    fill_filenames_by_order()