import streamlit as st
import urllib.request
import json
import time
from datetime import datetime, timedelta
from collections import Counter
import pandas as pd
import re
from concurrent.futures import ThreadPoolExecutor
from collect_keywords import NaverShoppingCrawler

# Streamlit secrets에서 API 키 가져오기
CLIENT_ID = st.secrets["CLIENT_ID"]
CLIENT_SECRET = st.secrets["CLIENT_SECRET"]

# 브랜드 리스트 로드 함수
def load_brands(csv_file="brand_list.csv"):
    """CSV 파일에서 브랜드 리스트를 로드"""
    if csv_file in st.secrets:
        brands = st.secrets[csv_file].split("\n")
        return set(brands)
    return set()

# 대표 키워드 사전 생성 함수
def generate_representative_keywords(keywords):
    representative_keywords = {}
    for keyword in keywords:
        base_word = re.sub(r'[^가-힣a-zA-Z]', '', keyword)
        if len(base_word) > 1:
            category = base_word
            if category not in representative_keywords:
                representative_keywords[category] = []
            representative_keywords[category].append(keyword)
    return representative_keywords

# 빈도 점수 계산 함수
def calculate_frequency_score(keywords):
    category_keywords = generate_representative_keywords(keywords)
    pattern_dict = {category: re.compile('|'.join(map(re.escape, keywords))) for category, keywords in category_keywords.items()}
    category_counts = Counter()
    for keyword in keywords:
        for category, pattern in pattern_dict.items():
            if pattern.search(keyword):
                category_counts[category] += 1
    max_freq = max(category_counts.values()) if category_counts else 1
    return {word: freq / max_freq for word, freq in category_counts.items()}

# 네이버 데이터랩 API를 이용한 트렌드 점수 계산 함수
def fetch_trend_score(chunk, start_date, end_date):
    url = "https://openapi.naver.com/v1/datalab/search"
    keyword_groups = [{"groupName": kw[:19].strip(), "keywords": [kw.strip()]} for kw in chunk if kw and kw.strip()]
    body = json.dumps({
        "startDate": start_date,
        "endDate": end_date,
        "timeUnit": "date",
        "keywordGroups": keyword_groups
    }, ensure_ascii=False).encode("utf-8")

    request = urllib.request.Request(url)
    request.add_header("X-Naver-Client-Id", CLIENT_ID)
    request.add_header("X-Naver-Client-Secret", CLIENT_SECRET)
    request.add_header("Content-Type", "application/json")

    response = urllib.request.urlopen(request, data=body)
    result = json.loads(response.read().decode("utf-8"))

    scores = {}
    for item in result.get("results", []):
        keyword = item["title"]
        data = item.get("data", [])
        if len(data) < 2:
            scores[keyword] = {"30일": 0, "7일": 0}
        else:
            recent_30 = data[-1]["ratio"]
            previous_avg_30 = sum(d["ratio"] for d in data[:-1]) / max(len(data) - 1, 1)
            
            recent_7_data = data[-7:] if len(data) >= 7 else data
            recent_avg_7 = sum(d["ratio"] for d in recent_7_data) / max(len(recent_7_data), 1)
            
            scores[keyword] = {
                "30일": recent_30 / previous_avg_30 if previous_avg_30 != 0 else 0,
                "7일": recent_avg_7 / previous_avg_30 if previous_avg_30 != 0 else 0
            }
    return scores

# 키워드 트렌드 점수 계산 함수
def calculate_trend_scores(keywords):
    end_date = datetime.today().strftime("%Y-%m-%d")
    start_date = (datetime.today() - timedelta(days=30)).strftime("%Y-%m-%d")
    chunk_size = 5
    scores = {}
    with ThreadPoolExecutor(max_workers=4) as executor:
        futures = [executor.submit(fetch_trend_score, keywords[i:i + chunk_size], start_date, end_date) for i in range(0, len(keywords), chunk_size)]
        for future in futures:
            scores.update(future.result())
    return scores

# 키워드 점수 계산 함수
def calculator(keyword, crawler, max_keywords=15):
    keywords, brands = crawler.get_total_keywords(keyword)
    brands = load_brands()
    
    # 브랜드명을 포함하는 키워드 제거
    filtered_keywords = [kw for kw in keywords if not any(brand in kw for brand in brands if isinstance(brand, str))]
    
    frequency_scores = calculate_frequency_score(filtered_keywords)
    trend_scores = calculate_trend_scores(list(frequency_scores.keys()))
    
    scores = []
    for kw in frequency_scores.keys():
        trend_score_30 = trend_scores.get(kw, {}).get("30일", 0)
        trend_score_7 = trend_scores.get(kw, {}).get("7일", 0)
        final_trend_score = (trend_score_30 * 0.7) + (trend_score_7 * 0.3)

        scores.append({
            "키워드": kw,
            "빈도 점수": frequency_scores.get(kw, 0),
            "유행성 점수": final_trend_score,
            "총점": frequency_scores.get(kw, 0) + final_trend_score,
        })

    return sorted(scores, key=lambda x: x["총점"], reverse=True)[:max_keywords]

# Streamlit UI
st.title("키워드 비교 분석")
keyword = st.text_input("키워드를 입력하세요:")
if st.button("분석 시작"):
    crawler = NaverShoppingCrawler()
    sorted_scores = calculator(keyword, crawler)
    df = pd.DataFrame(sorted_scores)
    st.write(df)
