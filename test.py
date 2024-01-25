import os

def rename_files_in_folders(base_path):
    for folder in os.listdir(base_path):
        folder_path = os.path.join(base_path, folder)
        if os.path.isdir(folder_path):
            old_file_path = os.path.join(folder_path, 'llm_label_gpt4.json')
            new_file_path = os.path.join(folder_path, 'llm_label_gpt3-5.json')
            if os.path.exists(old_file_path):
                os.rename(old_file_path, new_file_path)
                # print(f"Renamed file in {folder}")

# 设置您要处理的顶级文件夹的路径
base_folder_path = './micrograph_dataset/train'
rename_files_in_folders(base_folder_path)