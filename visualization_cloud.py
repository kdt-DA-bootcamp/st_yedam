import streamlit as st
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import time

from collect_keywords import NaverShoppingCrawler
from compare_keywords import calculator

# Streamlit UI 설정

# 사이드바 이미지 추가
st.sidebar.image("Neyo.webp", 
                 caption="🧚‍♂️ 키워드 요정 네요 (Neyo)", use_container_width=True)

# 메인 소개글
st.title("🛍️ 안녕하세요! 네요(Neyo)에요! 🧚‍♂️")
st.write("네이버 키워드 요정✨ 그래서 저는 네요! ")  
st.write("상품명을 고민 중이신가요? 🤔 네요가 딱 맞는 키워드를 찾아드릴게요!")  
st.write("상위 노출을 위한 똑똑한 키워드를 함께 찾아봐요! 🚀")  

# 확장형 상품명 가이드
with st.expander("상품명 가이드 by 네요 🧚‍♂️"):
    st.write("""
    스마트스토어에서 상품을 **상위 노출**시키려면 어떤 상품명을 써야 할까요?  
    **네요의 꿀팁!** 상품명을 정할 때는 아래 세 가지를 꼭 기억하세요!
    """)

    st.subheader("🔍 1. 키워드 검색량이 중요해요!")
    st.write("""
    - 많은 사람들이 검색하는 키워드를 포함하면 **노출될 확률**이 올라가요. 📈  
    - 하지만 너무 인기 있는 키워드는 **경쟁이 치열**해서 상위 노출이 어렵답니다. 🤯  
    - **꿀팁!** 이미 상위에 노출된 상품들의 키워드를 참고해 보세요.
    (소곤소곤) 네요는 이미 상위 노출된 상품명을 함께 분석하고 있답니다...!
    - **검색량이 많으면서도 경쟁이 적은 키워드**를 찾는 게 가장 중요해요!
    """)

    st.subheader("🔥 2. 유행을 타는 키워드를 활용해요!")
    st.write("""
    - 계절, 명절, 휴일마다 인기 키워드가 바뀐다는 사실, 알고 계셨나요? 🗓️  
    - 상품명을 등록할 때 **최신 트렌드를 반영**하는 게 필수! 🚀  
    """)

    st.subheader("🛒 3. 카테고리 적합성을 꼭 체크하세요!")
    st.write("""
    - 검색이 잘된다고 아무 키워드나 마구 넣으면? ❌ 효과가 없어요!  
    - 키워드마다 등록되는 **카테고리**가 따로 정해져 있어요.  
    - 네이버의 검색 알고리즘이 **상품과 키워드의 적합성**을 판단하니,  
      카테고리에 맞는 키워드를 잘 골라야 해요! 🎯  
    """)

    st.write("📢 **네요의 한마디!** 좋은 키워드가 곧 상위 노출의 비결이에요! 지금 바로 **최적의 상품명**을 만들어볼까요?")

# 사용자 입력
keyword = st.text_input("키워드를 입력하세요:")

# 검색 버튼 생성
if st.button("검색"):

    with st.spinner("네요가 열심히 분석 중이에요... 잠시만 기다려 주세요!"):

        st.session_state.clear()
        crawler = NaverShoppingCrawler()
        
        sorted_scores = calculator(keyword, crawler)
        _, top_category = crawler.get_shopping_trend(keyword)

    st.success("분석 완료!")
    
    # 검색 결과 저장
    st.session_state["keyword"] = keyword
    st.session_state["sorted_scores"] = sorted_scores
    st.session_state["top_category"] = top_category

# 기존 검색 결과 유지
if "sorted_scores" in st.session_state:
    keyword = st.session_state["keyword"]
    sorted_scores = st.session_state["sorted_scores"]
    top_category = st.session_state.get("top_category", "카테고리 정보 없음")

    st.subheader(f"'{keyword}'에 대한 추천 카테고리")
    st.write(f"가장 많이 등록된 카테고리: **{top_category}**")

    st.subheader(f"'{keyword}'에 대한 추천 키워드")
    
    if sorted_scores:
        st.write(f"1순위: **{sorted_scores[0]['키워드']}** / 2순위: **{sorted_scores[1]['키워드']}** / 3순위: **{sorted_scores[2]['키워드']}**")
        
        # 키워드 점수 데이터프레임 생성
        score_df = pd.DataFrame(sorted_scores)
        score_df.index = [f"{i+1}위" for i in range(len(score_df))]
        
        with st.container():
            st.dataframe(score_df, use_container_width=True)
        
        # 추가 트렌드 키워드 버튼
        if st.button("추가 트렌드 키워드 보기"):
            crawler = NaverShoppingCrawler()
            additional_keywords = crawler.get_trend_keywords(keyword)
            
            # 검색 결과 저장
            st.session_state["additional_keywords"] = additional_keywords
    
    # 추가 키워드 표시
    if "additional_keywords" in st.session_state:
        st.subheader("📢 추가 트렌드 키워드")
        additional_df = pd.DataFrame({"추가 키워드": st.session_state["additional_keywords"]})
        st.table(additional_df)