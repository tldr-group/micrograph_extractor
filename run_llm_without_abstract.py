import re
import openai
import os
import json
from gpt_utils import *

openai.api_key = os.getenv("OPENAI_API_KEY")
client = openai.OpenAI(api_key=openai.api_key)

def assistant(caption):
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
    You are an expert on micrographs, images captured using microscopes such as SEM, TEM, or AFM, etc.

    Given caption of a figure from an academic paper, answer the question:
    Is there a micrograph in this figure? Respond with 'true' or 'false'
    
    IMPORTANT: The anwer should only contain pure JSON format only with the fields "isMicrograph"

    Here's an example of output:

    {
    "isMicrograph": "true or false"
    }
    

    """
    caption_escaped = repr(caption)
    user_message = f""" Caption: {caption_escaped}"""

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

                llm_label_data = []

                for item in captions_data:
                    caption = item['caption']
                    name = item['name']
                    figure_type = item['figType']

                    if figure_type == 'Figure':
                        response = assistant(caption)
                        response_data = extract_json_from_response(response)
                        response_data['figure'] = name
                        llm_label_data.append(response_data)

                with open(os.path.join(folder_path, 'labels_3-5.json'), 'w') as file:
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
train_directory_path = './micrograph_dataset_new/train'
process_folder(train_directory_path)
                





