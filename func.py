import os
import cv2
import json
import imageio
from tqdm import tqdm
from argparse import ArgumentParser
from utils.logger import Logger

logger = Logger()

def parse_args():
    logger.log("[bold] ‣ Initializing... [/bold]")
    parser = ArgumentParser()
    parser.add_argument("--data_dir", type=str, default="data")
    parser.add_argument("--video_dir", type=str, default="data/videos")
    parser.add_argument("--clip_dir", type=str, default="data/clips")
    parser.add_argument("--output_dir", type=str, default="data/output")
    parser.add_argument("--label_map_path", type=str, default="data/label_map.txt")
    parser.add_argument("--clip_size", type=int, default=30)
    args = parser.parse_args()
    
    logger.console_args(vars(args))
    
    return args

def load_video_list(input_dir: str = "data/videos"):
    logger.log(f"[bold] ‣ Loading video list from {input_dir}... [/bold]")
    
    if not os.path.exists(input_dir):
        raise FileNotFoundError(f"Input directory '{input_dir}' does not exist.")
    
    video_files = [f for f in os.listdir(input_dir) if f.lower().endswith(('.mp4', '.avi', '.mov'))]
    video_files = sorted(video_files)
    if not video_files:
        raise ValueError(f"No video files found in the input directory '{input_dir}'.")
    
    logger.log(f"[bold green] ∙ Found {len(video_files)} video files. [/bold green]")
    
    return [os.path.join(input_dir, f) for f in video_files]


def load_clip(clip_dir: str, video_name: str, clip_idx: int):
    # 불러올 클립 경로의 확장자를 .gif로 변경
    clip_path = os.path.join(clip_dir, video_name, f"{clip_idx}.gif")
    if not os.path.exists(clip_path):
        raise FileNotFoundError(f"Clip '{clip_path}' does not exist.")
    return clip_path


def load_label_map(label_map_path: str = "data/label_map.txt"):
    if not os.path.exists(label_map_path):
        raise FileNotFoundError(f"Label map file '{label_map_path}' does not exist.")
    
    label_map = {}
    with open(label_map_path, 'r') as f:
        for idx, line in enumerate(f):
            label = line.strip()
            label_map[label] = idx
    
    return label_map


def load_label_list(video_path: str, json_path: str = "data/output_data.json"):
    with open(json_path, 'r') as f:
        data = json.load(f)
        
    video_name = os.path.basename(video_path)
    label_index = data['video_list'].index(video_name)
    label_list = data['label_list'][label_index]['label']
    return label_list


def load_dropdown_list(video_dir: str = "data/videos", clip_dir: str = "data/clips"):
    video_list = load_video_list(video_dir)
    clip_list = [os.path.join(clip_dir, os.path.basename(video).split('.')[0]) for video in video_list]
    return video_list, clip_list


def initialize(video_list: list, clip_size: int, data_dir: str):
    logger.log("[bold] ‣ Initializing data structure... [/bold]")
    
    output_data = {
        'video_list': [os.path.basename(video) for video in video_list],
        'clip_size': clip_size,
        'label_list': []
    }
    
    for video_path in video_list:
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            raise ValueError(f"Could not open video file '{video_path}'.")
        
        video_name = os.path.basename(video_path)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        label = [0 for _ in range(0, total_frames, clip_size)]
        
        output_data['label_list'].append({
            'video_name': video_name,
            'total_frames': total_frames,
            'label': label
        })
        
        cap.release()
    
    output_path = os.path.join(data_dir, 'output_data.json')
    with open(output_path, 'w') as f:
        json.dump(output_data, f, indent=4)
        
    logger.log(f"[bold green] ∙ Data structure initialized and saved to {output_path}. [/bold green]")
        
    return output_path


def cutting_video_to_clips(video_list: list, clip_size: int, clip_dir: str, output_dir: str = "data/output"):
    logger.log(f"[bold] ‣ Cutting videos into clips of size {clip_size}... [/bold]")
    
    if not os.path.exists(clip_dir):
        os.makedirs(clip_dir)
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    for video_path in video_list:
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            raise ValueError(f"Could not open video file '{video_path}'.")

        video_name = os.path.basename(video_path).split('.')[0]
        cur_clip_dir = os.path.join(clip_dir, video_name)
        
        os.makedirs(cur_clip_dir, exist_ok=True)

        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        fps = cap.get(cv2.CAP_PROP_FPS)
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        clip_count = total_frames // clip_size
        
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')

        for i in tqdm(range(clip_count), desc=f"Processing {video_name}({video_path}) to clips"):
            start_frame = i * clip_size
            cap.set(cv2.CAP_PROP_POS_FRAMES, start_frame)
            
            frames_for_gif = []
            
            output_mp4_path = os.path.join(output_dir, f"{video_name}_{i}.mp4")
            out_mp4 = cv2.VideoWriter(output_mp4_path, fourcc, fps, (width, height))

            for _ in range(clip_size):
                ret, frame = cap.read()
                if not ret:
                    break
                
                # MP4 저장을 위해 원본 프레임 사용
                out_mp4.write(frame)
                
                # GIF 저장을 위해 RGB로 변환하여 저장
                rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                frames_for_gif.append(rgb_frame)

            out_mp4.release()

            if frames_for_gif:
                output_gif_path = os.path.join(cur_clip_dir, f"{i}.gif")
                imageio.mimsave(output_gif_path, frames_for_gif, fps=fps, loop=0)

        cap.release()
        
    logger.log(f"[bold green] ∙ Video clips saved to {clip_dir}. [/bold green]")

def update_label(video_name: str, label_map: dict, label: list, clip_idx: int, json_path: str = "data/output_data.json"):
    if not os.path.exists(json_path):
        raise FileNotFoundError(f"JSON file '{json_path}' does not exist.")
    
    with open(json_path, 'r') as f:
        data = json.load(f)
    
    video_name_flag = video_name in data['video_list']
    if not video_name_flag:
        raise ValueError(f"Video '{video_name}' not found in the JSON data.")
    video_index = data['video_list'].index(video_name)
    
    clip_index_flag = clip_idx < len(data['label_list'])
    if not clip_index_flag:
        raise ValueError(f"Clip index {clip_idx} is out of range for video '{video_name}'.")
    
    label_flag = label in label_map
    if not label_flag:
        raise ValueError(f"Label '{label}' not found in the label map.")
    
    data['label_list'][video_index]['label'][clip_idx] = label_map.get(label, -1)
    
    with open(json_path, 'w') as f:
        json.dump(data, f, indent=4)
        

def main():
    logger.console_banner()
    args = parse_args()
    
    video_list = load_video_list(args.video_dir)
    cutting_video_to_clips(video_list, args.clip_size, args.clip_dir)
    output = initialize(video_list, args.clip_size, args.data_dir)
    
if __name__ == "__main__":
    main()