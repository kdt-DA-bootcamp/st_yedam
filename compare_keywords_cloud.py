import streamlit as st
import urllib.request
import json
import time
from datetime import datetime, timedelta
from collections import Counter
import pandas as pd
import re
import threading
from concurrent.futures import ThreadPoolExecutor
import collect_keywords_cloud

# 대표 키워드 사전 자동 생성 함수
def generate_category_keywords(keywords):
    category_keywords = {}
    for keyword in keywords:
        base_word = re.sub(r'[^가-힣a-zA-Z]', '', keyword)  # 특수문자 제거
        if len(base_word) > 1:
            category = base_word  # 단순화하여 대표 키워드 설정
            if category not in category_keywords:
                category_keywords[category] = []
            category_keywords[category].append(keyword)
    return category_keywords

# 빈도 점수 계산
def calculate_frequency_score(keywords):
    category_keywords = generate_category_keywords(keywords)
    pattern_dict = {category: re.compile('|'.join(map(re.escape, keywords))) for category, keywords in category_keywords.items()}
    category_counts = Counter()
    for keyword in keywords:
        for category, pattern in pattern_dict.items():
            if pattern.search(keyword):
                category_counts[category] += 1
    max_freq = max(category_counts.values()) if category_counts else 1
    return {word: freq / max_freq for word, freq in category_counts.items()}

# 유행성 점수 계산 (멀티스레딩 적용)
def fetch_trend_score(chunk, start_date, end_date):
    """네이버 데이터랩 API를 이용한 트렌드 점수 계산"""
    url = "https://openapi.naver.com/v1/datalab/search"
    keyword_groups = [{"groupName": kw[:19].strip(), "keywords": [kw.strip()]} for kw in chunk if kw and kw.strip()]
    body = json.dumps({
        "startDate": start_date,
        "endDate": end_date,
        "timeUnit": "date",
        "keywordGroups": keyword_groups
    }, ensure_ascii=False).encode("utf-8")

    # 함수 내부에서 환경 변수 로드 (Streamlit 실행 시 오류 방지)
    client_id = st.secrets["CLIENT_ID"]
    client_secret = st.secrets["CLIENT_SECRET"]

    request = urllib.request.Request(url)
    request.add_header("X-Naver-Client-Id", client_id)
    request.add_header("X-Naver-Client-Secret", client_secret)
    request.add_header("Content-Type", "application/json")

    response = urllib.request.urlopen(request, data=body)
    result = json.loads(response.read().decode("utf-8"))

    scores = {}
    for item in result.get("results", []):
        keyword = item["title"]
        data = item.get("data", [])
        if len(data) < 2:
            scores[keyword] = 0
        else:
            recent = data[-1]["ratio"]
            previous_avg = sum(d["ratio"] for d in data[:-1]) / max(len(data) - 1, 1)
            scores[keyword] = recent / previous_avg if previous_avg != 0 else 0
    return scores

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
    keywords = crawler.get_total_keywords(keyword)
    frequency_scores = calculate_frequency_score(keywords)
    trend_scores = calculate_trend_scores(list(frequency_scores.keys()))
    scores = []
    for kw in frequency_scores.keys():
        scores.append({
            "키워드": kw,
            "빈도 점수": frequency_scores.get(kw, 0),
            "유행성 점수": trend_scores.get(kw, 0),
            "총점": frequency_scores.get(kw, 0) + trend_scores.get(kw, 0),
        })
    return sorted(scores, key=lambda x: x["총점"], reverse=True)[:max_keywords]
