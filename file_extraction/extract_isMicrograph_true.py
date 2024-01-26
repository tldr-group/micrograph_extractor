import os
import json
import shutil
import glob
import re

import os
import shutil

import os
import shutil

def copy_json_files(source_folder_path, target_folder_path):
    """
    Copy JSON files from a source folder to a target folder while preserving the directory structure.

    Args:
        source_folder_path (str): The path to the source folder containing JSON files.
        target_folder_path (str): The path to the target folder where JSON files will be copied.

    Returns:
        None
    """
    # Traverse all subfolders in the source folder
    for subdir in os.listdir(source_folder_path):
        source_subdir_path = os.path.join(source_folder_path, subdir)
        target_subdir_path = os.path.join(target_folder_path, subdir)

        # Check if the target subfolder exists, create it if it doesn't
        if not os.path.exists(target_subdir_path):
            os.makedirs(target_subdir_path)

        # Build the full paths for source and target files
        source_file_path = os.path.join(source_subdir_path, 'llm_label_gpt3-5.json')
        target_file_path = os.path.join(target_subdir_path, 'llm_label_gpt3-5.json')

        # If the source file exists, copy it to the target path
        if os.path.exists(source_file_path):
            shutil.copy(source_file_path, target_file_path)
            print(f"File copied: {source_file_path} -> {target_file_path}")



def process_micrograph_images(target_folder_base, train_folder, is_micrograph="true"):

    # iterate through all DOIs
    for doi in os.listdir(train_folder):
        doi_folder = os.path.join(train_folder, doi)
        imgs_folder = os.path.join(doi_folder, "imgs")  

        # ignore if not a folder
        if not os.path.isdir(doi_folder):
            continue

        # JSON file path
        json_file_path = os.path.join(doi_folder, "llm_label_gpt3-5.json")
        captions_json_path = os.path.join(doi_folder, "captions.json")
        paper_data_json_path = os.path.join(doi_folder, "paper_data.json")

        # check if JSON file exists
        if os.path.exists(json_file_path):
            with open(json_file_path, 'r') as json_file:
                data = json.load(json_file)

                # iterate through all items in JSON file
                extracted_data = [] 
                for item in data:
                    # check if item is a micrograph
                    if item.get("isMicrograph") == is_micrograph:
                        extracted_data.append(item)

                        # extract figure images
                        figure_number = item.get("figure")
                        if figure_number:
                            pattern = os.path.join(imgs_folder, f"captions_fig_{figure_number}(_\\d+)?\\.jpg")
                            figure_img_paths = [path for path in glob.glob(os.path.join(imgs_folder, "captions_fig_*.jpg")) if re.match(pattern, path)]

                            target_imgs_folder = os.path.join(target_folder_base, doi, "imgs")
                            os.makedirs(target_imgs_folder, exist_ok=True)
                            for img_path in figure_img_paths:
                                shutil.copy(img_path, target_imgs_folder)

                # only save json file if there is at least one item
                if extracted_data:
                    target_doi_folder = os.path.join(target_folder_base, doi)
                    os.makedirs(target_doi_folder, exist_ok=True)
                    
                    # save extracted data to json file
                    target_json_folder = os.path.join(target_doi_folder, "llm_label_gpt3-5_extract.json")
                    with open(target_json_folder, 'w') as target_json_file:
                        json.dump(extracted_data, target_json_file, indent=4)

                    # copy captions.json and paper_data.json
                    if os.path.exists(captions_json_path):
                        shutil.copy(captions_json_path, target_doi_folder)
                    if os.path.exists(paper_data_json_path):
                        shutil.copy(paper_data_json_path, target_doi_folder)


# source_folder = './micrograph_dataset/train'  # Source folder path
# target_folder = './train'  # Target folder path
# copy_json_files(source_folder, target_folder)

is_micrograph = "false"    
target_folder_base = "./train_ismicrograph_false"             
train_folder = './micrograph_dataset/train' 
process_micrograph_images(target_folder_base,train_folder,is_micrograph)

