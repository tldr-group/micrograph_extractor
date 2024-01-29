import os
import json
import glob
import re

def process_folder(doi_folder):
    # Paths to the required files
    extraction_file = os.path.join(doi_folder, "llm_label_gpt3-5_extract.json")
    captions_file = os.path.join(doi_folder, "captions.json")
    paper_data_file = os.path.join(doi_folder, "paper_data.json")
    imgs_folder = os.path.join(doi_folder, "imgs")

    # Loading the files
    with open(extraction_file, 'r') as file:
        extraction_data = json.load(file)

    with open(captions_file, 'r') as file:
        captions_data = json.load(file)

    with open(paper_data_file, 'r') as file:
        paper_data = json.load(file)
    abstract = paper_data.get("abstract", "")

    # Process each figure in extraction_data
    output = []
    for figure_info in extraction_data:
        figure_number = figure_info['figure']
        
        # Find matching caption
        caption = next((item['caption'] for item in captions_data if item['name'] == figure_number), None)

        # Correctly formulating the regex pattern
        pattern = re.compile(f"captions_fig_{figure_number}(_\\d+)?\\.jpg")

        # Gathering and sorting image paths
        figure_img_paths = sorted(
            [path for path in glob.glob(os.path.join(imgs_folder, f"captions_fig_{figure_number}*.jpg")) if pattern.match(os.path.basename(path))],
            key=lambda x: (len(x), x)
        )

        # Build the JSON structure
        figure_data = {
            "figure": figure_number,
            "captions": caption,
            "abstract": abstract,
            "img_path": figure_img_paths,
            "gpt3_5_response": figure_info,
        }
        output.append(figure_data)

    return output



def traverse_and_process(base_folder):
    doi_folders = [os.path.join(base_folder, f) for f in os.listdir(base_folder) if os.path.isdir(os.path.join(base_folder, f))]

    for folder in doi_folders:
        result = process_folder(folder)
        output_file = os.path.join(folder, "combined_output.json")

        # Writing the result to a new JSON file
        with open(output_file, 'w') as file:
            json.dump(result, file, indent=4)

# Example usage
traverse_and_process("./micrograph_test/train")
