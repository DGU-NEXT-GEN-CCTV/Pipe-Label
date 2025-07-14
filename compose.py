import os
import json
import csv
import shutil
from argparse import ArgumentParser
from utils.logger import Logger

logger = Logger()

def parse_args():
    logger.log("[bold] ‣ Initializing... [/bold]")
    parser = ArgumentParser()
    parser.add_argument("--output_dir", type=str, default="data/output")
    parser.add_argument("--label_map", type=str, default="data/label_map.txt")
    parser.add_argument("--label", type=str, default="data/output_data.json")
    args = parser.parse_args()
    
    logger.console_args(vars(args))
    
    return args


def load_label_map(label_map_path: str = "data/label_map.txt"):
    if not os.path.exists(label_map_path):
        raise FileNotFoundError(f"Label map file '{label_map_path}' does not exist.")
    
    label_map = {}
    with open(label_map_path, 'r') as f:
        for idx, line in enumerate(f):
            label = line.strip()
            label_map[label] = idx
    
    return label_map


def main():
    logger.console_banner()
    
    args = parse_args()
    
    label_map = load_label_map(args.label_map)
    shutil.copy(args.label_map, os.path.join(args.output_dir, 'label_map.txt'))
    
    logger.log(f"[bold] ‣ Loading label list from {args.label}... [/bold]")
    label = json.load(open(args.label, 'r'))
    label_list = label['label_list']
    
    data = []
    
    for l in label_list:
        for idx, c in enumerate(l['label']):
            video_name = l['video_name'].split('.')[0]
            clip_idx = idx
            clip_name = f"{video_name}_{clip_idx}.mp4"
            label_name = list(label_map.keys())[c]
            data.append([clip_name, label_name])
            
    output_csv_path = os.path.join(args.output_dir, 'label.csv')
    os.makedirs(args.output_dir, exist_ok=True)
    
    with open(output_csv_path, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerows(data)
        
    logger.log(f"[bold green] ∙ Labels saved to {output_csv_path} [/bold green]")
    
    
if __name__ == "__main__":
    main()
    
    
    