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

    def get_header(self, method, uri):
        """네이버 광고 API 호출을 위한 헤더 생성"""
        timestamp = str(round(time.time() * 1000))
        signature = signaturehelper.Signature.generate(timestamp, method, uri, self.secret_key)
        return {
            "Content-Type": "application/json; charset=UTF-8",
            "X-Timestamp": timestamp,
            "X-API-KEY": self.api_key,
            "X-Customer": str(self.customer_id),
            "X-Signature": signature
        }

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
        print(f"🔍 트렌드 키워드 요청: {keyword}")

        response = requests.get(
            self.base_url + "/keywordstool",
            params={
                "hintKeywords": keyword,
                "showDetail": "1"
            },
            headers=self.get_header("GET", "/keywordstool")
        )

        try:
            data = response.json()
            print(f"✅ API 응답 데이터: {data}")  # API 응답 확인
        except Exception as e:
            print(f"❌ API 응답 파싱 오류: {e}")
            return []

        keyword_list = data.get('keywordList', [])
        if not keyword_list:
            print("⚠️ 트렌드 키워드가 비어 있음!")
            return []  # 빈 리스트 반환

        return [item["relKeyword"] for item in keyword_list]



    def get_total_keywords(self, keyword):
        """최종 키워드 리스트 반환 (쇼핑 트렌드 + 연관 키워드 + 트렌드 키워드 + 브랜드 목록)"""
        print(f"🔍 검색 키워드: {keyword}")

        total_keywords_list, top_category = self.get_shopping_trend(keyword)
        print(f"✅ 쇼핑 트렌드 키워드: {total_keywords_list}")
        print(f"✅ 대표 카테고리: {top_category}")

        related_keywords = self.get_related_keywords(keyword)
        print(f"✅ 연관 키워드: {related_keywords}")

        trend_keywords = self.get_trend_keywords(keyword)
        print(f"✅ 트렌드 키워드: {trend_keywords}")

        brands = self.get_brand_lists(keyword)
        print(f"✅ 브랜드 리스트: {brands}")

        # 빈 값이 있는지 확인
        if total_keywords_list is None or related_keywords is None or trend_keywords is None or brands is None:
            print("❌ 키워드 수집 중 일부 데이터가 None입니다.")
            return [], [], "카테고리 없음"

        # 리스트가 비었을 경우 오류 방지
        total_keywords_list.extend(related_keywords)
        total_keywords_list.extend(trend_keywords)

        return total_keywords_list, brands, top_category


if __name__ == "__main__":
    keyword = st.text_input("키워드를 입력하세요:")
    if keyword:
        crawler = NaverShoppingCrawler()
        total_keywords, brands, top_category = crawler.get_total_keywords(keyword)
        st.write("**키워드 리스트:**", total_keywords)
        st.write("**브랜드 리스트:**", brands)
        st.write("**가장 많이 등장한 카테고리:**", top_category)
