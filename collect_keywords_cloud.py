import time
import requests
import json
import re
import streamlit as st
import pandas as pd
from bs4 import BeautifulSoup
import signaturehelper
from collections import Counter

class NaverShoppingCrawler:
    def __init__(self):
        """네이버 쇼핑 API 크롤러 초기화"""
        self.client_id = st.secrets["CLIENT_ID"]
        self.client_secret = st.secrets["CLIENT_SECRET"]
        self.api_key = st.secrets["API_KEY"]
        self.secret_key = st.secrets["SECRET_KEY"]
        self.customer_id = st.secrets["CUSTOMER_ID"]
        self.api_url = "https://openapi.naver.com/v1/search/shop.json"
        self.base_url = 'https://api.naver.com'
        self.csv_file = "brand_list.csv"

    def get_shopping_trend(self, keyword):
        """네이버 쇼핑 인기 상품 키워드 및 대표 카테고리 가져오기"""
        url = f"{self.api_url}?query={keyword}&display=15&start=1&sort=sim"
        headers = {
            "X-Naver-Client-Id": self.client_id,
            "X-Naver-Client-Secret": self.client_secret
        }
        response = requests.get(url, headers=headers)
        data = response.json()

        top_keyword_list = []
        category_list = []
        for item in data['items']:
            raw_title = item['title']
            clean_title = re.sub(r'<.*?>', '', raw_title)
            top_keyword_list.extend(clean_title.split())
            category = " > ".join(filter(None, [
                item.get('category1'), item.get('category2'), item.get('category3'), item.get('category4')
            ]))
            if category:
                category_list.append(category)
        
        category_counter = Counter(category_list)
        top_category = category_counter.most_common(1)[0][0] if category_counter else None
        
        return top_keyword_list, top_category

    def get_related_keywords(self, keyword):
        """네이버 검색에서 연관 키워드 가져오기"""
        search_url = f'https://search.naver.com/search.naver?query={keyword}'
        search_res = requests.get(search_url)
        search_soup = BeautifulSoup(search_res.text, 'html.parser')

        lis = search_soup.select('.keyword')
        related_keywords = [li.select_one('.tit').text.strip() for li in lis if li.select_one('.tit')]
        return related_keywords

    def get_brand_lists(self, keyword):
        """네이버 쇼핑 API에서 브랜드 정보 추출 후 CSV 파일에 저장"""
        url = f"{self.api_url}?query={keyword}&display=100&start=1&sort=sim"
        headers = {
            "X-Naver-Client-Id": self.client_id,
            "X-Naver-Client-Secret": self.client_secret
        }
        response = requests.get(url, headers=headers)
        data = response.json()
        brands = {item.get("brand", "Unknown") for item in data['items'] if item.get("brand")}
        
        if brands:
            df = pd.DataFrame({"Brand": list(brands)})
            df.to_csv(self.csv_file, mode="a", header=not pd.io.common.file_exists(self.csv_file), index=False)
        return list(brands)

    def get_trend_keywords(self, keyword):
        """네이버 광고 API에서 트렌드 키워드 가져오기"""
        
        debug_logs = [f"🔍 트렌드 키워드 요청: {keyword}"]

        uri = "/keywordstool"
        headers = self.get_header("GET", uri)

        response = requests.get(
            self.base_url + uri,
            params={
                "hintKeywords": keyword,
                "showDetail": "1"
            },
            headers=headers
        )

        try:
            data = response.json()
            debug_logs.append(f"✅ API 응답 데이터: {data}")  # API 응답 확인
        except Exception as e:
            debug_logs.append(f"❌ API 응답 파싱 오류: {e}")
            return [], debug_logs  # ✅ `st.text_area()`를 마지막에 한 번만 실행하기 위해 변경

        keyword_list = data.get("keywordList", [])
        if not keyword_list:
            debug_logs.append("⚠️ 트렌드 키워드가 비어 있음!")

        return [item["relKeyword"] for item in keyword_list], debug_logs  # ✅ 로그를 함께 반환



    def get_total_keywords(self, keyword):
        """최종 키워드 리스트 반환 (쇼핑 트렌드 + 연관 키워드 + 트렌드 키워드 + 브랜드 목록)"""
        total_keywords_list, top_category = self.get_shopping_trend(keyword)
        total_keywords_list.extend(self.get_related_keywords(keyword))
        total_keywords_list.extend(self.get_trend_keywords(keyword))
        brands = self.get_brand_lists(keyword)
        return total_keywords_list, brands, top_category
