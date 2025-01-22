import os
import streamlit as st
import matplotlib.pyplot as plt
import matplotlib as mpl
import matplotlib.font_manager as fm
import urllib.request
import numpy as np
import pandas as pd
from compare_keywords_cloud import calculator

# import 지연 로딩 (순환 참조 방지)
def get_crawler():
    from collect_keywords_cloud import NaverShoppingCrawler  # 함수 내부에서 import
    return NaverShoppingCrawler()

# 폰트를 저장할 Streamlit 전용 디렉토리 설정
font_dir = os.path.join(os.getcwd(), ".streamlit/fonts")
font_path = os.path.join(font_dir, "NanumGothic.ttf")

# 폰트가 없으면 다운로드
if not os.path.exists(font_path):
    os.makedirs(font_dir, exist_ok=True)  # 앱 디렉토리에 저장
    font_url = "https://github.com/naver/nanumfont/releases/latest/download/NanumGothic.ttf"
    urllib.request.urlretrieve(font_url, font_path)

# Matplotlib에 폰트 추가 및 설정
fm.fontManager.addfont(font_path)
mpl.rc("font", family="NanumGothic")
mpl.rcParams["axes.unicode_minus"] = False  # 마이너스(-) 기호 깨짐 방지

# Streamlit UI 설정
st.title("스마트스토어 상품명 키워드 분석")
st.write("내 상품이 상위노출되려면, 어떤 키워드를 써야할까?")

# 사용자 입력
keyword = st.text_input("키워드를 입력하세요:")

if st.button("검색"):
    st.session_state.clear()
    crawler = get_crawler()
    sorted_scores = calculator(keyword, crawler)
    
    # 검색 결과 저장
    st.session_state["keyword"] = keyword
    st.session_state["sorted_scores"] = sorted_scores

# 기존 검색 결과 유지
if "sorted_scores" in st.session_state:
    keyword = st.session_state["keyword"]
    sorted_scores = st.session_state["sorted_scores"]

    st.subheader(f"'{keyword}'에 대한 추천 키워드")
    
    if sorted_scores:
        st.write(f"1순위: {sorted_scores[0]['키워드']} / 2순위: {sorted_scores[1]['키워드']} / 3순위: {sorted_scores[2]['키워드']}")
        
        # 키워드 점수 데이터프레임 생성
        score_df = pd.DataFrame(sorted_scores)
        score_df.index = [f"{i+1}위" for i in range(len(score_df))]
        st.table(score_df)
        
        # 그래프 시각화 (막대 그래프)
        fig, ax = plt.subplots()
        keywords = score_df["키워드"]
        total_scores = score_df["총점"]

        ax.barh(keywords[::-1], total_scores[::-1], color='skyblue')
        ax.set_xlabel("총점")
        ax.set_ylabel("키워드")
        ax.set_title("추천 키워드 점수 분석")

        st.pyplot(fig)