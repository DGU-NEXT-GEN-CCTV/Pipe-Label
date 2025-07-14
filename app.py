import os
import streamlit as st
from func import load_dropdown_list, load_label_map, load_label_list, update_label

LABEL_MAP = load_label_map()

# --- 페이지 설정 ---
st.set_page_config(
    page_title="NGC | Pipeline Labeling",
    page_icon="🏷️",
    layout="wide"
)

# --- 제목 및 설명 ---
st.title("Pipeline Labeling")
st.write("이 저장소는 동영상을 입력으로 받아 행동 라벨링을 도와주는 파이프라인입니다. [GitHub](https://github.com/DGU-NEXT-GEN-CCTV/Pipe-Label)")

# --- 드롭다운으로 폴더 선택 ---
video_list, clip_list = load_dropdown_list()
st.session_state.label_list = load_label_list(video_list[0]) if video_list else []
if not clip_list:
    st.warning("GIF를 포함한 폴더를 찾을 수 없습니다. 'data' 폴더에 데이터를 추가해주세요.")
    st.stop()

# 사용자가 선택한 폴더를 세션 상태에 저장하여 새로고침해도 유지되도록 합니다.
if 'selected_folder' not in st.session_state:
    st.session_state.selected_folder = clip_list[0]

st.subheader("클립 디렉토리 선택")

dir_path = st.selectbox(
    "클립 디렉토리 선택",
    options=clip_list,
    index=clip_list.index(st.session_state.selected_folder) if st.session_state.selected_folder in clip_list else 0
)

# 선택된 폴더를 세션 상태에 저장합니다.
st.session_state.selected_folder = dir_path

# --- GIF 파일 검색 및 시각화 ---
if dir_path:
    # 입력된 경로가 유효한 디렉토리인지 확인합니다.
    if os.path.isdir(dir_path):

        gif_files = []
        # 디렉토리 내 모든 파일을 확인하며 .gif로 끝나는 파일을 찾습니다.
        for filename in os.listdir(dir_path):
            if filename.lower().endswith(".gif"):
                full_path = os.path.join(dir_path, filename)
                gif_files.append(full_path)
            gif_files.sort()  # 파일 이름 순서대로 정렬

        if not gif_files:
            st.info("해당 폴더에 GIF 파일이 없습니다.")
        else:
            st.subheader(f"총 {len(gif_files)}개의 클립")

            # 갤러리 형태로 이미지를 보여주기 위해 열(column)을 설정합니다.
            # 4개의 열을 사용하고, 더 많은 이미지가 있으면 새로운 행을 만듭니다.
            col_n = 3
            cols = st.columns(col_n)
            for idx, gif_path in enumerate(gif_files):
                with cols[idx % col_n]:
                    try:
                        with st.container(border=True):
                            st.image(
                                gif_path,
                                use_container_width=True,
                            )
                            
                            def on_label_change(gif_path):
                                video_name = os.path.basename(video_list[clip_list.index(dir_path)])
                                clip_idx = int(os.path.basename(gif_path).split('.')[0])
                                selected_label = st.session_state[f"selectbox_{gif_path}"]
                                selected_label_index = LABEL_MAP.get(selected_label, None)
                                st.session_state.label_list[idx] = selected_label_index
                                update_label(video_name, LABEL_MAP, selected_label, clip_idx)

                            st.selectbox(
                                "행동 라벨",
                                tuple(LABEL_MAP.keys()),
                                key=f"selectbox_{gif_path}",
                                index=st.session_state.label_list[idx],
                                on_change=on_label_change,
                                args=(gif_path,)
                            )
                    except Exception as e:
                        st.error(f"{os.path.basename(gif_path)} 로드 실패: {e}")

    else:
        st.error("유효하지 않은 폴더 경로입니다. 다시 확인해주세요.")