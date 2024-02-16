import openai
import os
import base64
import requests
import json
import re
from gpt_utils import *
import traceback


openai.api_key = os.getenv("OPENAI_API_KEY")
client = openai.OpenAI(api_key=openai.api_key)


def get_completion_single_image(image_path, user_message):
    def encode_image(image_path):
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode("utf-8")

    # Getting the base64 string
    base64_image = encode_image(image_path)

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {openai.api_key}",
    }

    payload = {
        "model": "gpt-4-vision-preview",
        "messages": [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": user_message},
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"},
                    },
                ],
            }
        ],
        "max_tokens": 300,
    }

    response = requests.post(
        "https://api.openai.com/v1/chat/completions", headers=headers, json=payload
    )
    print(image_path)
    print(response.json()["choices"][0]["message"]["content"])
    return response.json()["choices"][0]["message"]["content"]


def get_completion_multiple_images(image_paths, user_message):
    # Function to encode images
    def encode_images(image_paths):
        base64_images = []
        for path in image_paths:
            with open(path, "rb") as image_file:
                base64_images.append(
                    base64.b64encode(image_file.read()).decode("utf-8")
                )
        return base64_images

    # Getting the base64 strings for all images
    base64_images = encode_images(image_paths)

    # Preparing the payload with dynamic image content
    messages_content = [{"type": "text", "text": user_message}]

    for image in base64_images:
        messages_content.append(
            {
                "type": "image_url",
                "image_url": {"url": f"data:image/jpeg;base64,{image}"},
            }
        )

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {openai.api_key}",
    }

    payload = {
        "model": "gpt-4-vision-preview",
        "messages": [{"role": "user", "content": messages_content}],
        "max_tokens": 1000,
    }

    response = requests.post(
        "https://api.openai.com/v1/chat/completions", headers=headers, json=payload
    )
    print(response.json().get("choices", [{}])[0].get("message", {}).get("content", ""))

    return response.json().get("choices", [{}])[0].get("message", {}).get("content", "")


def get_subfigure(img_path):
    # Use regular expression to match the pattern in image file name
    match = re.search(r"fig_(\d+)(?:_(\d+))?\.jpg", img_path)
    if match:
        # Return the subfigure number if it exists, otherwise return an empty string
        return match.group(2) if match.group(2) else ""
    else:
        return ""


def save_to_file(output_file, data):
    # Saves data to a file
    with open(output_file, 'w') as file:
        json.dump(data, file, indent=4)

def process_json(doi_path, user_message_1, system_message_user2):
    json_file_path = os.path.join(doi_path, "combined_output.json")
    with open(json_file_path, "r") as file:
        data = json.load(file)

    output_file = os.path.join(doi_path, "labels_gpt4_vision_subfigure.json")

    if os.path.exists(output_file):
        with open(output_file, "r") as file:
            new_data = json.load(file)
    else:
        new_data = []

    processed_img_paths = {item['subfigure']: item for item in new_data}

    for item in data:
        img_paths = item.get('img_path', [])
        figure = item.get('figure', [])
        abstract = item.get('abstract', [])
        captions = item.get('captions', [])

        # Prepare paper information for processing
        abstract_escaped = repr(abstract)
        captions_escaped = repr(captions)
        paper_information = f"The abstract is: {abstract_escaped}, and the captions are: {captions_escaped}"
        user_message_2 = system_message_user2 + paper_information

        # Iterate over img_paths, skipping already processed images
        for img_path in img_paths[1:]:
            if get_subfigure(img_path) in processed_img_paths:
                continue

            try:
                # Simulated functions for demonstration purposes
                response_1 = get_completion_single_image(img_path, user_message_1)
                if re.search(r'\bfalse\b', response_1, re.IGNORECASE):
                    new_fields = {
                        'figure': figure,
                        'subfigure': get_subfigure(img_path),
                        'isMicrograph': False,
                    }
                elif re.search(r'\btrue\b', response_1, re.IGNORECASE):
                    response_2 = get_completion_multiple_images([img_paths[0], img_path], user_message_2)
                    response_json = extract_json_from_response(response_2)

                    new_fields = {
                        'figure': figure,
                        'subfigure': get_subfigure(img_path)
                    }
                    new_fields.update(response_json)
                else:
                    # Handle case where response_1 is neither 'true' nor 'false'
                    new_fields = {
                        "figure": figure,
                        "subfigure": get_subfigure(img_path),
                        "isMicrograph": False,
                        "comments": "Ambiguous response for micrograph check"
                    }
            except Exception as e:
                new_fields = {
                    "figure": figure,
                    "subfigure": get_subfigure(img_path),
                    "isMicrograph": False,
                    "comments": f"Error processing image: {str(e)}"
                }

            new_data.append(new_fields)
            processed_img_paths[img_path] = new_fields

            # Save the processing result immediately after each image to preserve progress
            with open(output_file, "w") as file:
                json.dump(new_data, file, indent=4)

def process_all_doi_folders(train_folder, user_message_1, system_message_user2):
    error_log_path = os.path.join(train_folder, "error_log.txt")
    items = [item for item in os.listdir(train_folder) if os.path.isdir(os.path.join(train_folder, item))]
    total_items = len(items)

    for index, item in enumerate(items):
        item_path = os.path.join(train_folder, item)

        print(f"Processing folder: {item_path}")
        try:
            process_json(item_path, user_message_1, system_message_user2)
        except Exception as e:
            # Write error message to error_log.txt in the main folder
            with open(error_log_path, "a") as error_file:
                error_message = f"Error processing {item_path}: {e}\n{traceback.format_exc()}"
                error_file.write(error_message)
        print(f"Finished processing folder: {item_path}")

        # Print progress
        progress = ((index + 1) / total_items) * 100
        print(f"Progress: {progress:.2f}%")


user_message_1 = """
            You are an expert materials scientist specializing in micrographs. 
            Typically, these are greyscale and might include annotations like scale bars or arrows, although not always. 

            Your task:Given a subfigure image from a research paper,
            1. check if it is a micrograph or another type of figure, such as a graph or diagram, 
            2. check if it includes sub-subfigures.

            If the image is solely a micrograph without any sub-subfigures, you should respond with 'TRUE'; 
            otherwise,  respond with 'FALSE'. 

            Here is an example of output:
            "Reason: The image is a micrograph with 2 sub-subfigures.
            Answer: FALSE"
            """
system_message_user2 = """
            You are an expert materials scientist working on micrographs. The first image is a main image is taken from a research paper. The second image is a subfigure cropped from the main image. It is might be a micrograph. 

            Focus on the abstract of the paper, captions, and the content of these images. Answer the questions below: 
            1.Is the cropped image a micrograph? Answer with a single 'true' or 'false'.
            2.What technique (e.g., SEM, TEM) was used to create the micrograph in the cropped image? Provide a brief answer, such as 'SEM' or 'Optical Microscopy'.
            3.What material is shown in the micrograph? Provide the full name e.g., 'Lithium Nickel-Manganese-Cobalt (NMC) 811 cathode' or 'Insulin aggregates'.
            4.If there are any interesting things about the micrograph, like specific processing conditions or anomalies, put these in a list of single phrases (e.g ['heat-treated, 'cracked', 'sintered']). 
            5.Which part of the caption of the mainfigure does this subfigure correspond to? Extract the caption of the subfigure, and its label e.g (a), (b) if possible.

            Here's an example of the JSON output format:

            {
            "isMicrograph": True,
            "instrument": "Technique",
            "material": "Description",
            "comments": ["comment1", "comment2", "comment3"]
            "subfigure_caption": "(label): caption of subfigure"
                }

            IMPORTANT: The answer should only contain pure JSON data matching the fields provided in the examples.
            """
        
train_folder = "./micrograph_interesting/train"  
process_all_doi_folders(train_folder, user_message_1, system_message_user2)
