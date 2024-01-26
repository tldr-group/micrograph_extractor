import openai
import os
import base64
import requests
import json
import re


openai.api_key = os.getenv("OPENAI_API_KEY")
client = openai.OpenAI(api_key=openai.api_key)

import base64
import requests
import openai  # Ensure you have imported openai

def get_completion_vision(image_paths, user_message):
    # Function to encode images
    def encode_images(image_paths):
        base64_images = []
        for path in image_paths:
            with open(path, "rb") as image_file:
                base64_images.append(base64.b64encode(image_file.read()).decode('utf-8'))
        return base64_images

    # Getting the base64 strings for all images
    base64_images = encode_images(image_paths)

    # Preparing the payload with dynamic image content
    messages_content = [
        {"type": "text", "text": user_message}
    ]

    for image in base64_images:
        messages_content.append(
            {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image}"}}
        )

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {openai.api_key}"
    }

    payload = {
        "model": "gpt-4-vision-preview",
        "messages": [{"role": "user", "content": messages_content}],
        "max_tokens": 300
    }
    print(payload)

    response = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload)
    print(response.json().get('choices', [{}])[0].get('message', {}).get('content', ''))

    return response.json().get('choices', [{}])[0].get('message', {}).get('content', '')



def get_subfigure(img_path):
    # Use regular expression to match the pattern in image file name
    match = re.search(r'fig_(\d+)(?:_(\d+))?\.jpg', img_path)
    if match:
        # Return the subfigure number if it exists, otherwise return an empty string
        return match.group(2) if match.group(2) else ''
    else:
        return ''
    
def process_json(json_data, doi_folder, doi_path):
    # Process each item in the json list
    for item in json_data:
        img_paths = item.get('img_paths', [])
        captions = item.get('captions', [])
        figure = item.get('figure', '')
        abstract = item.get('abstract', '')
        user_message = "Do you think there is a micrograph in this figure?"
        # Call your custom function get_completion_vision
        response = get_completion_vision(img_paths, user_message)

        # Get subfigure value for each image path and save results
        for img_path in img_paths:
            subfigure = get_subfigure(img_path)
            save_results(figure, subfigure, response, doi_path, doi_folder)

def save_results(figure, subfigure, response, doi_path, doi_folder):
    # Define the output file path within the original train/<doi> folder
    output_file = os.path.join(doi_path, doi_folder + '_result.json')

    # Prepare the data to be saved in JSON format
    output_data = {
        "figure": figure,
        "subfigure": subfigure,
        "response": response
    }

    # Write the data to a JSON file
    with open(output_file, 'w') as file:
        json.dump(output_data, file, indent=4)

# Example usage
def process_folder(folder_path):
    # Iterate through each subfolder in the specified folder
    for doi_folder in os.listdir(folder_path):
        doi_path = os.path.join(folder_path, doi_folder)
        if os.path.isdir(doi_path):
            json_file = os.path.join(doi_path, 'combined_output.json')
            if os.path.exists(json_file):
                with open(json_file, 'r') as file:
                    data = json.load(file)
                    process_json(data, doi_folder, doi_path)
        
        
process_folder('micrograph_test/train')








# print(response.json()['choices'][0]['message']['content'])

# Path to your image
# image_path = "train_ismicrograph_true/chemrxiv_10_26434_14481855_v1/imgs/captions_fig_2_1.jpg"
# Example usage
# user_message = ""
# img_paths = ["path/to/image1.jpg", "path/to/image2.jpg"]
# result = get_completion_vision(img_paths, user_message)
# print(result)