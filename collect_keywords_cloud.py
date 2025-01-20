import time
import requests
import json
import re
import os
from bs4 import BeautifulSoup
from dotenv import load_dotenv
import signaturehelper

class NaverShoppingCrawler:
    def __init__(self):
        """환경 변수 로드 (한 번만 실행)"""
        load_dotenv()
        self.client_id = os.getenv('CLIENT_ID')
        self.client_secret = os.getenv('CLIENT_SECRET')
        self.api_key = os.getenv('API_KEY')
        self.secret_key = os.getenv('SECRET_KEY')
        self.customer_id = os.getenv('CUSTOMER_ID')
        self.base_url = 'https://api.naver.com'
        self.shop_api_url = "https://openapi.naver.com/v1/search/shop.json"
        
    def get_shopping_trend(self, keyword):
        """네이버 쇼핑 인기 상품 키워드 가져오기 (API 연동)"""
        url = f"{self.shop_api_url}?query={keyword}&display=15&start=1&sort=sim"
        headers = {
            "X-Naver-Client-Id": self.client_id,
            "X-Naver-Client-Secret": self.client_secret
        }
        
        response = requests.get(url, headers=headers)
        data = response.json()

        top_keyword_list = []
        for item in data['items']:
            raw_title = item['title']
            clean_title = re.sub(r'<.*?>', '', raw_title)  # <b> 태그 제거
            top_keyword_list.extend(clean_title.split())  # 띄어쓰기 기준 리스트화

        return top_keyword_list
    
    def get_related_keywords(self, keyword):
        """네이버 검색에서 연관 키워드 가져오기"""
        search_url = f'https://search.naver.com/search.naver?query={keyword}'
        search_res = requests.get(search_url)
        search_soup = BeautifulSoup(search_res.text, 'html.parser')

        lis = search_soup.select('.keyword')
        related_keywords = [li.select_one('.tit').text.strip() for li in lis if li.select_one('.tit')]

        return related_keywords

    def get_trend_keywords(self, keyword):
        """네이버 광고 API에서 트렌드 키워드 가져오기"""
        def get_header(method, uri):
            timestamp = str(round(time.time() * 1000))  # 요청 시간
            signature = signaturehelper.Signature.generate(timestamp, method, uri, self.secret_key)
            return {
                'Content-Type': 'application/json; charset=UTF-8',
                'X-Timestamp': timestamp,
                'X-API-KEY': self.api_key,
                'X-Customer': str(self.customer_id),
                'X-Signature': signature
            }
        
        uri = '/keywordstool'
        method = 'GET'
        time.sleep(1)  # API 호출 제한 방지

        response = requests.get(
            self.base_url + uri,
            params={
                'siteId': None,
                'biztpId': None,
                'hintKeywords': keyword,
                'event': None,
                'month': None,
                'showDetail': '1'
            },
            headers=get_header(method, uri)
        )

        keyword_list = response.json().get('keywordList', [])

        keywords = []
        for item in keyword_list:
            monthly_search = int(item['monthlyPcQcCnt']) + int(item['monthlyMobileQcCnt'])
            keywords.append((item['relKeyword'], monthly_search))

        # 중복 제거 후 상위 100개 키워드 반환
        trends_keywords = sorted(set(keywords), key=lambda x: x[1], reverse=True)[:100]
        return [item[0] for item in trends_keywords]  # 키워드만 반환

    def get_total_keywords(self, keyword):
        """최종 키워드 리스트 반환 (쇼핑 트렌드 + 연관 키워드 + 트렌드 키워드)"""
        total_keywords_list = []
        total_keywords_list.extend(self.get_shopping_trend(keyword))
        total_keywords_list.extend(self.get_related_keywords(keyword))
        total_keywords_list.extend(self.get_trend_keywords(keyword))

        return total_keywords_list