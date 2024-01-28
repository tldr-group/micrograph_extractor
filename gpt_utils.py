import json
import re

def extract_json_from_response(response):
    # Try to parse response as normal JSON data
    try:
        json_data = json.loads(response)
        return json_data
    except json.JSONDecodeError:
        pass

    # Use regular expressions to find JSON data inside Markdown-formatted code blocks
    pattern = r'```json(.*?)```'
    matches = re.findall(pattern, response, re.DOTALL)

    if matches:
        # If matching Markdown-formatted JSON data is found, extract it from the first match
        json_data = matches[0].strip()
        
        try:
            # Try to parse the extracted JSON data
            parsed_json = json.loads(json_data)
            return parsed_json
        except json.JSONDecodeError as e:
            print(f"Error parsing Markdown-formatted JSON: {e}")

    # If it's neither normal JSON nor Markdown-formatted JSON, look for JSON-like structures in the text
    json_like_pattern = r'\{.*\}'
    json_like_matches = re.findall(json_like_pattern, response, re.DOTALL)

    if json_like_matches:
        # If matching JSON-like structure is found, extract and try to parse it
        json_like_data = json_like_matches[0].strip()
        
        try:
            parsed_json_like = json.loads(json_like_data)
            return parsed_json_like
        except json.JSONDecodeError as e:
            print(f"Error parsing JSON-like structure: {e}")

    return None  # If no JSON data is found, return None