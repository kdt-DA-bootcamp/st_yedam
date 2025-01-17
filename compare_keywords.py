import os
import pandas as pd
from datetime import datetime, timedelta
import urllib.request
import json
import time
from collect_keywords import NaverShoppingCrawler
from collections import Counter

# 환경 변수 로드

CLIENT_ID = st.secrets['CLIENT_ID']
CLIENT_SECRET = st.secrets['CLIENT_SECRET']

if not CLIENT_ID or not CLIENT_SECRET:
    raise ValueError("🚨 환경 변수 CLIENT_ID 또는 CLIENT_SECRET이 설정되지 않았습니다.")

# 빈도 점수 계산 (NaN 방지)
def calculate_frequency_score(keywords):
    keyword_counts = pd.Series(keywords).value_counts()

    if keyword_counts.empty:
        return {kw: 0 for kw in keywords}

    total_count = keyword_counts.sum()  # 전체 키워드 개수
    keyword_scores = keyword_counts / total_count  # 각 키워드의 빈도를 전체 개수로 나눠 정규화

    return keyword_scores.to_dict()

# 유행성 점수 계산 (한 번에 5개씩 요청)
def calculate_trend_scores(keywords):
    end_date = datetime.today().strftime("%Y-%m-%d")
    start_date = (datetime.today() - timedelta(days=30)).strftime("%Y-%m-%d")

    url = "https://openapi.naver.com/v1/datalab/search"
    chunk_size = 5  # 5개씩 요청
    scores = {}

    for i in range(0, len(keywords), chunk_size):
        keyword_chunk = keywords[i:i + chunk_size]

        keyword_groups = [{"groupName": kw[:19].strip(), "keywords": [kw.strip()]} for kw in keyword_chunk if kw and kw.strip()]

        body = {
            "startDate": start_date,
            "endDate": end_date,
            "timeUnit": "date",
            "keywordGroups": keyword_groups
        }

        body = json.dumps(body, ensure_ascii=False).encode("utf-8")

        request = urllib.request.Request(url)
        request.add_header("X-Naver-Client-Id", CLIENT_ID)
        request.add_header("X-Naver-Client-Secret", CLIENT_SECRET)
        request.add_header("Content-Type", "application/json")

        try:
            response = urllib.request.urlopen(request, data=body)
            if response.getcode() == 200:
                result = json.loads(response.read().decode("utf-8"))

                for item in result.get("results", []):
                    keyword = item["title"]
                    data = item.get("data", [])
                    if len(data) < 2:
                        scores[keyword] = 0
                    else:
                        recent = data[-1]["ratio"]
                        previous_avg = sum(d["ratio"] for d in data[:-1]) / max(len(data) - 1, 1)
                        scores[keyword] = recent / previous_avg if previous_avg != 0 else 0

            time.sleep(1.5)  # 요청 간격 조정

        except urllib.error.HTTPError as e:
            error_response = e.read().decode("utf-8")
            print(f"❌ HTTPError: {e}\n🛑 API 에러 응답: {error_response}")

    return scores

# 키워드 점수 계산 함수 추가
def calculator(keyword, crawler, max_keywords=15):
    """각 항목의 점수 계산기"""
    raw_keywords = set(crawler.get_nobrand_keywords(keyword))

    # 키워드 검색량 기준 정렬 (트렌드 키워드와 교집합 필터링)
    keywords_with_trend = set(crawler.get_trend_keywords(keyword))
    filtered_keywords = list(raw_keywords & keywords_with_trend)[:max_keywords]

    # 점수 계산
    trend_scores = calculate_trend_scores(filtered_keywords)
    frequency_scores = calculate_frequency_score(filtered_keywords)

    # 결과 합산 및 저장
    scores = []
    for kw in filtered_keywords:
        frequency_score = frequency_scores.get(kw, 0)
        trend_score = trend_scores.get(kw, 0)
        total_score = frequency_score + trend_score

        scores.append({
            "키워드": kw,
            "빈도 점수": frequency_score,
            "유행성 점수": trend_score,
            "총점": total_score,
        })

    # 점수 총합 기준 정렬 및 상위 10개 항목 선택
    sorted_scores = sorted(scores, key=lambda x: x["총점"], reverse=True)[:10]

    return sorted_scores

# 실행
if __name__ == "__main__":
    keyword = input("키워드를 입력하세요: ")
    crawler = NaverShoppingCrawler()
    sorted_scores = calculator(keyword, crawler)

    # 🔥 크롤러 종료 (메모리 절약)
    crawler.quit()

    # 점수 출력
    print("📢 상품명에 적합한 키워드:")
    for idx, score in enumerate(sorted_scores, start=1):
        print(f"""{idx}. 키워드: {score['키워드']}, 
        빈도 점수: {score['빈도 점수']:.2f}, 
        유행성 점수: {score['유행성 점수']:.2f}, 
        총합 점수: {score['총점']:.2f}""")
