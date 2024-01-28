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
        "max_tokens": 1000
    }
    
    response = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload)
    print(response.json().get('choices', [{}])[0].get('message', {}).get('content', ''))

    return response.json().get('choices', [{}])[0].get('message', {}).get('content', '')

# def get_completion_vision(image_paths, user_message):
#     return f"test_result:{image_paths}"

def get_subfigure(img_path):
    # Use regular expression to match the pattern in image file name
    match = re.search(r'fig_(\d+)(?:_(\d+))?\.jpg', img_path)
    if match:
        # Return the subfigure number if it exists, otherwise return an empty string
        return match.group(2) if match.group(2) else ''
    else:
        return ''

def save_results(figure, subfigure, response, doi_path):
    # Define the output file path
    output_file = os.path.join(doi_path, 'gpt4_labeling_subfigure.json')

    # Prepare the data to be saved
    new_data = {
        "figure": figure,
        "subfigure": subfigure,
        "response": response
    }

    # If the file already exists, read and update the data; if not, create a new list
    if os.path.exists(output_file):
        with open(output_file, 'r') as file:
            try:
                data = json.load(file)
            except json.JSONDecodeError:
                data = []
    else:
        data = []

    # Append the new data to the list
    data.append(new_data)

    # Write the updated data back to the file
    with open(output_file, 'w') as file:
        json.dump(data, file, indent=4)

def process_json(json_data, doi_path):
    # Process each item in the json list
    for item in json_data:
        img_paths = item.get('img_path', [])
        captions = item.get('captions', [])
        figure = item.get('figure', '')
        abstract = item.get('abstract', '')
        user_message = """You are an expert materials scientist. You study micrographs, which are images taken using a microscope. 
The first image is a main image is taken from a research paper, and the remaining images are subfigures cropped from this main image. 
Please focus on the abstract of the paper, captions, and the content of these images.

Questions:

1.What's the length of the output json entries? The length of JSON entries should match the number of input figures. 
2.Does the main image contain a micrograph? Answer with either 'true' or 'false'.
3.If yes, does the cropped subfigure contain a micrograph? Answer with either 'true' or 'false'.
4.What technique (e.g., SEM, TEM) was used to create the micrograph in the cropped image? Provide a brief answer, such as 'SEM' or 'Optical Microscopy'.
5.What material is shown in the micrograph? Provide a short description, like 'NMC 811 cathode'.

Answer the questions below in JSON entries. Here's an example of the JSON output format. 

For the main image with a micrograph and its cropped images, create a separate JSON format for the main image and each cropped image.
This example assumes the main image contains a micrograph and has two cropped images (three images in total), so the lenth of json entries is 3. 
'Subfigure' indicates the sequence of the cropped images, starting from 0:


[{
"subfigure": "none",
"isMicrograph": "true"
},

{
"subfigure": "0",
"isMicrograph": "true",
"instrument": "Technique",
"material": "Description",
"comments": ["comment1", "comment2", "comment3"]
},

{
"subfigure": "1",
"isMicrograph": "false",
"instrument": "none",
"material": "none",
"comments": "none"
}]


Abstract: Hydrogen bonded organic frameworks (HOFs) with enzymes incorporated during their bottom-up synthesis represent functional biocomposites with promising applications in catalysis and sensing. High enzyme loading while preserving high specific activity is fundamental for development, but to combine these biospecific features with a porous carrier is an unmet challenge. Here, we explored synthetic incorporation of D-amino acid oxidase (DAAO) with metal-free tetraamidine/tetracarboxylate-based BioHOF-1. Comparison of different DAAO forms in BioHOF-1 incorporation revealed that N-terminal enzyme fusion with the positively charged module Zbasic2 (Z-DAAO) promotes the loading (2.5-fold; ~500 mg g-1) and strongly boosts the activity (6.5-fold). To benchmark the HOF composite with metal-organic framework (MOF) composites, Z-DAAO was immobilized into the zeolitic imidazolate framework-8 (ZIF-8), the relatively more hydrophilic analogue metal azolate framework-7 (MAF-7). While sensitivity to the framework environment limited the activity of DAAO@MAF-7 (3.2 U mg-1) and DAAO@ZIF-8 (≤ 0.5 U mg-1), the activity of DAAO@BioHOF-1 was comparable (~45%) to that of soluble DAAO (50.1 U mg-1) and independent of the enzyme loading (100 – 500 mg g-1). The DAAO@BioHOF-1 composites showed superior activity with respect to every reported carrier for the same enzyme and excellent stability during solid catalyst recycling. Collectively, our results show that the fusion of the enzyme with a positively charged protein module enables the synthesis of highly active HOF biocomposites suggesting the use of genetic engineering for the preparation of biohybrid systems with unprecedented properties.
Figure caption:Figure 3. Material characterization of Z-DAAO@BioHOF-1, Z-DAAO@ZIF-8, and Z-DAAO@MAF-7 with an initial Z-DAAO concentration of 1 mg mL-1 during synthesis after optimization of the synthesis to obtain each material at the correct topology. (a-c) PXRD patterns including simulated PXRD patterns of each material (red), each material without biocatalyst (grey), and Z-DAAO@HOF/MOF. (d-f) ATR-FTIR spectra of each material with/without biocatalyst. (g-i) SEM images of the obtained biocomposites with inset zoom of Z-DAAO@ZIF-8

IMPORTANT: 
When the main image contains a micrograph, the length of JSON entries should match the number of figures. 
For each subfigure, use its original sequence order from the user's input; do not assign new numbers.
"""
        # Call your custom function get_completion_vision
        response = get_completion_vision(img_paths, user_message)

        # Get subfigure value for each image path and save results
        for img_path in img_paths:
            subfigure = get_subfigure(img_path)
            save_results(figure, subfigure, response, doi_path)


def process_folder(folder_path):
    # Iterate through each subfolder in the specified folder
    for doi_folder in os.listdir(folder_path):
        doi_path = os.path.join(folder_path, doi_folder)
        if os.path.isdir(doi_path):
            json_file = os.path.join(doi_path, 'combined_output.json')
            if os.path.exists(json_file):
                with open(json_file, 'r') as file:
                    data = json.load(file)
                    process_json(data, doi_path)
        
        
process_folder('micrograph_test/train')








# print(response.json()['choices'][0]['message']['content'])

# Path to your image
# image_path = "train_ismicrograph_true/chemrxiv_10_26434_14481855_v1/imgs/captions_fig_2_1.jpg"
# Example usage
# user_message = ""
# img_paths = ["path/to/image1.jpg", "path/to/image2.jpg"]
# result = get_completion_vision(img_paths, user_message)
# print(result)