import sys
import os
import streamlit as st
import pandas as pd
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from collect_keywords import NaverShoppingCrawler
from compare_keywords import calculator

st.title("스마트스토어 상품명 키워드 봇")
st.write("내 상품이 상위노출되려면, 어떤 키워드를 써야할까?")

# input section
keyword = st.text_input("키워드를 입력하세요:")

if st.button("검색"):
    crawler = NaverShoppingCrawler()
    keywords = crawler.get_nobrand_keywords(keyword)  # 크롤링된 키워드 가져오기
    sorted_scores = calculator(keyword, crawler)
    crawler.quit()  # 크롤러 종료

    # 검색 결과 저장
    st.session_state["keyword"] = keyword
    st.session_state["sorted_scores"] = sorted_scores

# 기존 검색 결과 유지
if "sorted_scores" in st.session_state:
    keyword = st.session_state["keyword"]
    sorted_scores = st.session_state["sorted_scores"]

    st.subheader(f"'{keyword}'에 해당하는 추천 키워드는 다음과 같습니다:")

    if sorted_scores:
        st.write(f"1순위: {sorted_scores[0]['키워드']} / 2순위: {sorted_scores[1]['키워드']} / 3순위: {sorted_scores[2]['키워드']}")

        # 키워드 점수 테이블
        st.write("키워드별 상세 점수:")
        score_df = pd.DataFrame(sorted_scores)
        score_df.index = [f"{i+1}위" for i in range(len(score_df))]
        st.table(score_df)

        # 추가 키워드 버튼 및 결과 표시
        if st.button("사람들이 많이 검색한 추가 키워드를 보고 싶다면? 클릭!"):
            crawler = NaverShoppingCrawler()
            additional_keywords = crawler.get_trend_keywords(keyword)
            crawler.quit()

            # 검색 결과를 session_state에 저장
            st.session_state["additional_keywords"] = additional_keywords

    # 기존 검색 결과가 존재하면 추가 키워드 표 유지
    if "additional_keywords" in st.session_state:
        st.write("📢 추가 트렌드 키워드:")
        additional_df = pd.DataFrame({"추가 키워드": st.session_state["additional_keywords"]})
        st.table(additional_df)
