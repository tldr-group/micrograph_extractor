import os
import json

def evaluate_labels(train_folder, label_type):
    for doi_folder in os.listdir(train_folder):
        doi_path = os.path.join(train_folder, doi_folder)
        if os.path.isdir(doi_path):
            label_file = os.path.join(doi_path, 'labels.json')
            if os.path.isfile(label_file):
                with open(label_file, 'r', encoding='utf-8') as file:
                    labels = json.load(file)

                # Check if 'human' field exists, if not, skip
                if 'human' not in labels:
                    print(f"Skipping {doi_folder}, 'human' field not found.")
                    continue
                
                llm_eval = []
                
                human_labels = labels.get('human', [])
                llm_labels = labels.get(label_type, [])
                
                llm_dict = {item['figure']: item for item in llm_labels}
                
                for human_item in human_labels:
                    figure = human_item['figure']
                    # compare with llm
                    llm_item = llm_dict.get(figure)
                    if llm_item:
                        isMicrograph_correct = llm_item['isMicrograph'] == human_item['isMicrograph']
                    else:
                        print(f"No {label_type} item for figure: {figure}")
                        isMicrograph_correct = False
                    llm_eval.append({
                        'figure': figure,
                        'isMicrograph_correct': isMicrograph_correct
                    })
                
                # update evaluated labels and save
                labels[f'{label_type}_eval_auto'] = llm_eval
                with open(label_file, 'w', encoding='utf-8') as file:
                    json.dump(labels, file, ensure_ascii=False, indent=4)

if __name__ == "__main__":
    train_folder = './train'
    evaluate_labels(train_folder, "gpt4_without_abstract")
