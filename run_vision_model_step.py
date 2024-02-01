import openai
import os
import base64
import requests
import json
import re
from gpt_utils import *

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


def process_json(doi_path):
    # 读取combined_output.json文件
    json_file_path = os.path.join(doi_path, "combined_output.json")
    with open(json_file_path, "r") as file:
        data = json.load(file)

    # 定义output_file的路径
    output_file = os.path.join(doi_path, "llm_labeling_subfigure.json")

    # 检查文件是否存在，如果存在，则删除
    if os.path.exists(output_file):
        os.remove(output_file)

    new_data = []
    for item in data:
        try:
            img_paths = item.get('img_path', [])# img_paths
            figure = item.get('figure',[]) # figure
            abstract = item.get('abstract', []) # abstract
            captions = item.get('captions', []) # captions

            abstract_escaped = repr(abstract)
            captions_escaped = repr(captions)
            paper_information = f""" The abstract is: {abstract_escaped}, and the captions are: {captions_escaped}"""

            user_message_1 = """
                You are an expert materials scientist specializing in micrographs, images captured using microscopes such as SEM, TEM, or AFM. 
                Typically, these are greyscale and might include annotations like scale bars or arrows, although not always. 
                Your task is to determine whether an image is a micrograph or a different type of figure, like a graph or diagram from a scientific paper.
                If it is a micrograph, respond with a single 'yes', otherwise respond with a single 'no'. 
                """
            system_message_user2 = """
            You are an expert materials scientist working on micrographs. The first image is a main image is taken from a research paper. The second image is a subfigure cropped from the main image. It is might be a micrograph. 

            Focus on the abstract of the paper, captions, and the content of these images. Answer the questions below in JSON entries without additional text. 
            1.Do you think the cropped image is a micrograph? Answer with a single 'true' or 'false'.
            2.What technique (e.g., SEM, TEM) was used to create the micrograph in the cropped image? Provide a brief answer, such as 'SEM' or 'Optical Microscopy'.
            3.What material is shown in the micrograph? Provide the full name e.g., 'Lithium Nickel-Manganese-Cobalt (NMC) 811 cathode' or 'Insulin aggregates'.
            4.If there are any interesting things about the micrograph, like specific processing conditions or anomalies, please put these in a list of single phrases (e.g ['heat-treated, 'cracked', 'sintered']). 
            5.Which part of the caption of the mainfigure does this subfigure correspond to? Extract the caption of the subfigure, and its label e.g (a), (b) if possible.

            Here's an example of the JSON output format. 

            {
            "isMicrograph": "true",
            "instrument": "Technique",
            "material": "Description",
            "comments": ["comment1", "comment2", "comment3"]
            "subfigure_caption": "(label): caption of subfigure"
                }

            IMPORTANT: The answer should only contain pure JSON data.
            """
            
            user_message_2 = system_message_user2 + paper_information

            system_message_user3 = """
                You are an expert materials scientist. You study micrographs, 
                which are images taken using a microscope. 

                Focus on the abstract of the paper, captions, and the content of these images, answer these questions in a JSON format:
                1.Is there a micrograph in this figure? Respond with 'true' or 'false'
                2.If a micrograph is present, identify all the techniques used (e.g., SEM, TEM, Optical Microscopy) of the micrograph
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
            user_message_3 = system_message_user3 + paper_information

            # 处理img_paths列表
            
            if len(img_paths) > 1:
                for img_path in img_paths[1:]:
                    response_1 = get_completion_single_image(img_path, user_message_1)

                    # 根据response_1的值处理
                    if re.search(r'\bno\b', response_1, re.IGNORECASE):
                        new_fields = {
                            'figure': figure,
                            'subfigure': get_subfigure(img_path),
                            'isMicrograph': 'false'
                        }
                        if new_fields:
                            new_data.append(new_fields)

                    elif re.search(r'\byes\b', response_1, re.IGNORECASE):
                        response_2 = get_completion_multiple_images([img_paths[0], img_path], user_message_2)
                        response_json = extract_json_from_response(response_2)

                        new_fields = {
                            'figure': figure,
                            'subfigure': get_subfigure(img_path)
                        }

                        new_fields.update(response_json)
                        if new_fields:
                            new_data.append(new_fields) 

            else:

                response_mainfigure = get_completion_single_image(img_paths[0], user_message_3)
                response_mainfigure_json = extract_json_from_response(response_mainfigure)

                new_fields = {
                    'figure': figure,
                    'subfigure': []
                }
                
                new_fields.update(response_mainfigure_json)
                if new_fields:
                    new_data.append(new_fields) 
  

        except Exception as e:
            # if there is an error processing the item, write the error message to the error file
            error_log_path = os.path.join(doi_path, 'error_log.txt')
            with open(error_log_path, 'a') as error_file:
                error_message = f"Error processing item in {doi_path}: {e}\n{traceback.format_exc()}"
                error_file.write(error_message)                       

    if new_data:
        with open(output_file, 'w') as file:
            json.dump(new_data, file, indent=4)


import os
import traceback


def process_all_doi_folders(train_folder):
    error_log_path = os.path.join(train_folder, "error_log.txt")
    items = [item for item in os.listdir(train_folder) if os.path.isdir(os.path.join(train_folder, item))]
    total_items = len(items)
    for index, item in enumerate(items):
        item_path = os.path.join(train_folder, item)

        if os.path.isdir(item_path):
            print(f"Starting processing folder: {item_path}")
            try:
                process_json(item_path)
            except Exception as e:
                # write error message to error_log.txt
                with open(error_log_path, "a") as error_file:
                    error_message = (
                        f"Error processing {item_path}: {e}\n{traceback.format_exc()}"
                    )
                    error_file.write(error_message)
            print(f"Finished processing folder: {item_path}")
            
            # Print progress
            progress = ((index + 1) / total_items) * 100
            print(f"Completed: {progress:.2f}%")



train_folder = "./train_ismicrograph_true"  
process_all_doi_folders(train_folder)
