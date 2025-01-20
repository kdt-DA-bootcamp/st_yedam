import streamlit as st
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from compare_keywords_cloud import calculator

# import 지연 로딩 (순환 참조 방지)
def get_crawler():
    from collect_keywords_cloud import NaverShoppingCrawler  # 함수 내부에서 import
    return NaverShoppingCrawler()

# font 설정
import matplotlib as mpl
import matplotlib.font_manager as fm
mpl.rcParams['axes.unicode_minus'] = False
plt.rcParams["font.family"] = 'NanumGothic'
plt.rc('font', family='Malgun Gothic')  # Windows용

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