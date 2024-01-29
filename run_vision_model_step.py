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

    for item in data:
        img_paths = item.get("img_path", [])  # img_paths
        figure = item.get("figure", [])  # figure
        abstract = item.get("abstract", [])  # abstract
        captions = item.get("captions", [])  # captions

        abstract_escaped = repr(abstract)
        captions_escaped = repr(captions)
        user_message_1 = """
        You are an expert materials scientist working on micrographs, which are images taken with a microscope (like an SEM, TEM or AFM etc). 
        They tend to be greyscale and may have annotations on them like scale bars or arrows (but not always). Your
        job is work out if an image is a micrograph or if it is a different figure from a paper like a graph or diagram.

        If if is a micrograph, respond with a single 'yes', otherwise respond 'no'. 
        """
        system_message = """
        You are an expert materials scientist working on micrographs. The first image is a main image is taken from a research paper. The second image is a micrograph cropped from the main image. 

        Focus on the abstract of the paper, captions, and the content of these images. Answer the questions below in JSON entries without additional text. 
        1.Do you think there is a micrograph present in this figure? Answer with a single 'true' or 'false'.
        2.What technique (e.g., SEM, TEM) was used to create the micrograph in the cropped image? Provide a brief answer, such as 'SEM' or 'Optical Microscopy'.
        3.What material is shown in the micrograph? Provide a short description, like 'NMC 811 cathode'.
        4.If there are any interesting things about the micrograph, like specific processing conditions or anomalies, please put these in a list of single phrases (e.g ['heat-treated, 'cracked', 'sintered']). 

        Here's an example of the JSON output format. 

        {
        "isMicrograph": "true",
        "instrument": "Technique",
        "material": "Description",
        "comments": ["comment1", "comment2", "comment3"]
            }

        IMPORTANT: The answer should only contain pure JSON data.
        """
        paper_information = f""" The abstract is: {abstract_escaped}, and the captions are: {captions_escaped}"""
        user_message_2 = system_message + paper_information

        # 处理img_paths列表
        for img_path in img_paths[1:]:
            response_1 = get_completion_single_image(img_path, user_message_1)
            new_data = []

            # 根据response_1的值处理
            if re.search(r"\bno\b", response_1, re.IGNORECASE):
                new_data = {
                    "figure": figure,
                    "subfigure": get_subfigure(img_path),
                    "isMicrograph": "false",
                }
            elif re.search(r"\byes\b", response_1, re.IGNORECASE):
                response_2 = get_completion_multiple_images(
                    [img_paths[0], img_path], user_message_2
                )
                response_json = extract_json_from_response(response_2)

                # 先创建一个新的字典，包含你想要放在前面的字段
                new_fields = {"figure": figure, "subfigure": get_subfigure(img_path)}

                # 然后更新这个新字典与response_json的内容
                new_fields.update(response_json)

                # 将更新后的字典添加到new_data
                new_data.append(new_fields)

            if new_data:
                # If the file already exists, read and update the data; if not, create a new list
                if os.path.exists(output_file):
                    with open(output_file, "r") as file:
                        try:
                            data = json.load(file)
                        except json.JSONDecodeError:
                            data = []
                else:
                    data = []

                # Append the new data to the list
                data.append(new_data)

                # Write the updated data back to the file
                with open(output_file, "w") as file:
                    json.dump(data, file, indent=4)


import os
import traceback


def process_all_doi_folders(train_folder):
    error_log_path = os.path.join(train_folder, "error_log.txt")
    for item in os.listdir(train_folder):
        item_path = os.path.join(train_folder, item)
        if os.path.isdir(item_path):
            try:
                process_json(item_path)
            except Exception as e:
                # 将错误信息写入error_log.txt
                with open(error_log_path, "a") as error_file:
                    error_message = (
                        f"Error processing {item_path}: {e}\n{traceback.format_exc()}"
                    )
                    error_file.write(error_message)


# 示例使用
train_folder = "micrograph_test/train"  # 这里设置你的train文件夹路径
process_all_doi_folders(train_folder)
