import re
import openai
import os
import json
from gpt_utils import *

# TODO: only accept "figType": "Figure", add "llm" field

openai.api_key = os.getenv("OPENAI_API_KEY")
client = openai.OpenAI(api_key=openai.api_key)

def assistant(abstract, captions):
    """
    Given an abstract and a caption, generate a JSON output with the following fields:
    1. IsMicrographPresent: Whether a micrograph is present in the figure.
    2. MicroscopyTechniqueUsed: The microscopy technique used to produce the micrograph.
    3. MaterialShown: The material shown in the micrograph."""
    
    def get_completion(messages, model="gpt-3.5-turbo-1106", 
                        temperature=0, max_tokens=500):

            completion = client.chat.completions.create(
                model= model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens
            )
            return completion.choices[0].message.content

    system_message ="""
    You are an expert materials scientist. You study micrographs, 
    which are images taken using a microscope. 
    A variety of instruments can produce micrographs, including but not limited to:
    SEM: Scanning Electron Microscopy,
    TEM: Transmission Electron Microscopy,
    STEM: Scanning Transmission Electron Microscopy,
    OM: Optical Microscopy,
    RLM: Reflected Light Microscopy,
    XCT: X-ray Tomography,
    AFM: Atomic Force Microscopy,
    ConfocalMicroscopy: Confocal Microscopy,
    Nanomicroscopy: Nanomicroscopy
    ...


    Given abstract and caption of the figure from an academic paper, answer these questions in a JSON format:
    1.Is there a micrograph in this figure? Respond with 'true' or 'false'
    2.If a micrograph is present, identify all the techniques used (e.g., SEM, TEM, Optical Microscopy) of the micrograph(s)
    3.If a micrograph is present, list all materials featured in the micrographs (e.g., 'NMC 811 cathode' or 'Insulin aggregates', 'Cobalt')
    4.If there are any interesting things about the micrograph, like specific processing conditions or anomalies, please put these in a list of single phrases (e.g ['heat-treated, 'cracked', 'sintered']). 
    
    If there is a micrograph in the figure, ensure that the output is in JSON format with the fields "isMicrograph", "instrument", "material" and 'comments'. 
    If there is no micrograph in the figure, ensure that the output is in JSON format only with the fields "isMicrograph".
    
    IMPORTANT: It should only contain pure JSON data and should not include any other non-JSON content.

    Here's an example of how the JSON output should look with micrograph present:

    {
  "isMicrograph": "true",
  "instrument": "Technique",
  "material": "Description",
  "comments": ["comment1", "comment2", "comment3"]
    }

    Here's an example of how the JSON output should look without micrograph present:
        {
    "isMicrograph": "false"
    }
    

    """
    abstract_escaped = repr(abstract)
    captions_escaped = repr(captions)
    user_message = f""" The abstract is: {abstract_escaped}, and the captions are: {captions_escaped}"""

    messages =  [  
    {'role':'system', 
    'content': system_message},    
    {'role':'user', 
    'content': f"{user_message}"},  
    ] 

    response = get_completion(messages)
    return response


def process_folder(base_path):
    error_log_path = os.path.join(base_path, 'error_log.txt')
    folders = [f for f in os.listdir(base_path) if os.path.isdir(os.path.join(base_path, f))]
    total_folders = len(folders)

    for i, folder in enumerate(folders):
        folder_path = os.path.join(base_path, folder)
        if os.path.isdir(folder_path):
            print(f"Start processing: {folder}")
            try:
                # Process the folder contents
                with open(os.path.join(folder_path, 'captions.json'), 'r') as file:
                    captions_data = json.load(file)

                with open(os.path.join(folder_path, 'paper_data.json'), 'r') as file:
                    paper_data = json.load(file)

                abstract = paper_data.get('abstract', '')
                llm_label_data = []

                for item in captions_data:
                    caption = item['caption']
                    name = item['name']

                    response = assistant(abstract, caption)
                    response_data = extract_json_from_response(response)
                    response_data['figure'] = name
                    llm_label_data.append(response_data)

                with open(os.path.join(folder_path, 'labels.json'), 'w') as file:
                    json.dump(llm_label_data, file, indent=4)
                print(f"Finished processing the folder: {folder}")

            except Exception as e:
                # Write the error to the error log
                with open(error_log_path, 'a') as error_file:
                    error_message = f"Error processing folder {folder}: {e}\n"
                    error_file.write(error_message)
                print(f"An error occurred while processing the folder {folder}. Please check the error log for details.")
            
            # Print progress
            progress_percentage = (i + 1) / total_folders * 100
            print(f"Processing... {progress_percentage:.2f}% complete")

# Process each DOI-named folder in the 'train' directory
train_directory_path = './micrograph_dataset/train'
process_folder(train_directory_path)
                





