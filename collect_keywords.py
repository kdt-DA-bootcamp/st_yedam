import streamlit as st
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
import time
import requests
import os
from bs4 import BeautifulSoup
import signaturehelper

class NaverShoppingCrawler:
    def __init__(self):
        # Chrome 옵션 설정
        chrome_options = Options()
        chrome_options.add_argument("--headless")  # GUI 없이 실행
        chrome_options.add_argument("--no-sandbox")  # 샌드박스 비활성화
        chrome_options.add_argument("--disable-dev-shm-usage")  # 메모리 사용 최적화
        chrome_options.add_argument("--disable-gpu")  # GPU 가속 비활성화
        chrome_options.add_argument("--remote-debugging-port=9222")  # 디버깅 포트 설정

        # Selenium 드라이버 초기화
        self.driver = webdriver.Chrome(
            service=Service(ChromeDriverManager().install()),
            options=chrome_options
        )

    def get_brand_list(self, keyword):
        """
        입력한 키워드의 브랜드 리스트를 가져오며, 브랜드가 없을 경우 제조사 리스트를 가져옵니다.
        """
        self.driver.get(f'https://search.shopping.naver.com/search/all?query={keyword}')
        brand_list = []
        
        # 브랜드 확장 버튼 클릭 및 크롤링
        try:
            button = self.driver.find_element(By.CSS_SELECTOR, "button[title='브랜드']")
            button.click()
            time.sleep(2)  # 버튼 클릭 후 로딩 대기

            main_brands = self.driver.find_elements(By.CSS_SELECTOR, "ul[class*='basicTypeFilter_finder_tit_list'] li button")
            for m_brand in main_brands:
                text = m_brand.text.strip()
                if text:
                    brand_list.append(text)
        except Exception as e:
            print(f"브랜드 확장 버튼을 찾을 수 없습니다: {e}")

        # 브랜드가 없을 경우 제조사 리스트 가져오기
        if not brand_list:
            try:
                button = self.driver.find_element(By.CSS_SELECTOR, "button[title='제조사']")
                button.click()
                time.sleep(2)  # 버튼 클릭 후 로딩 대기

                manufacturers = self.driver.find_elements(By.CSS_SELECTOR, "ul[class*='basicTypeFilter_finder_tit_list'] li button")
                for mfr in manufacturers:
                    text = mfr.text.strip()
                    if text:
                        brand_list.append(text)
            except Exception as e:
                print(f"제조사 확장 버튼을 찾을 수 없습니다: {e}")
        
        return brand_list

    def get_top_keywords(self, keyword):
        """
        입력한 키워드의 검색 상위 노출 상품 키워드를 가져옵니다.
        """
        self.driver.get(f'https://search.shopping.naver.com/search/all?where=all&frm=NVSCTAB&query={keyword}')

        # 광고 제외 상품명 크롤링
        top_titles = []
        try:
            self.driver.execute_script("window.scrollTo(0,document.body.scrollHeight);")
            time.sleep(0.5)  # 스크롤 후 로딩 대기
            titles = self.driver.find_elements(By.CSS_SELECTOR, '.product_title__Mmw2K')
            for title in titles:
                top_titles.append(title.text.strip())
        except Exception as e:
            print(f"상품명 크롤링 중 오류 발생: {e}")

        # 중복 제거 및 키워드 분리
        keywords = set()
        for title in top_titles:
            keywords.update(title.split())

        return sorted(list(keywords))

    def get_related_keywords(self, keyword):
        """
        연관 키워드를 가져옵니다.
        """
        search_url = f'https://search.naver.com/search.naver?query={keyword}'
        search_res = requests.get(search_url)
        search_soup = BeautifulSoup(search_res.text, 'html.parser')

        lis = search_soup.select('.keyword')

        related_keywords = []
        for li in lis:
            keyword_tag = li.select_one('.tit')
            if keyword_tag:
                related_keywords.append(keyword_tag.text.strip())
            else:
                additionals = search_soup.select('.fds-keyword-text')
                for add in additionals:
                    related_keywords.append(add.text.strip())

        return related_keywords

    def get_trend_keywords(self, keyword):
        """
        트렌드 키워드를 가져옵니다 (API 연동).
        """
        def get_header(method, uri, api_key, secret_key, customer_id):
            timestamp = str(round(time.time() * 1000))  # 요청 시간
            signature = signaturehelper.Signature.generate(timestamp, method, uri, secret_key)
            return {
                'Content-Type': 'application/json; charset=UTF-8',
                'X-Timestamp': timestamp,
                'X-API-KEY': api_key,
                'X-Customer': str(customer_id),
                'X-Signature': signature
            }
        
        API_KEY = st.secrets['API_KEY']
        SECRET_KEY = st.secrets['SECRET_KEY']
        CUSTOMER_ID = st.secrets['CUSTOMER_ID']
        BASE_URL = 'https://api.naver.com'

        uri = '/keywordstool'
        method = 'GET'

        # API 요청
        time.sleep(1)

        response = requests.get(
            BASE_URL + uri,
            params={
                'siteId': None,
                'biztpId': None,
                'hintKeywords': keyword,
                'event': None,
                'month': None,
                'showDetail': '1'
            },
            headers=get_header(method, uri, API_KEY, SECRET_KEY, CUSTOMER_ID)
        )

        keyword_list = response.json().get('keywordList', [])

        keywords = [
            {
                '키워드': item['relKeyword'],
                '월간 검색량': int(item['monthlyPcQcCnt']) + int(item['monthlyMobileQcCnt'])
            }
            for item in keyword_list
            if item['monthlyPcQcCnt'] != '< 10' and item['monthlyMobileQcCnt'] != '< 10'
        ]

        trends_keywords = sorted(keywords, key=lambda x: x['월간 검색량'], reverse=True)[:100]
        return [item['키워드'] for item in trends_keywords]

    def get_nobrand_keywords(self, keyword):
        """
        브랜드에 포함되지 않은 키워드 리스트를 반환합니다.
        """
        total_keywords_list = []
        total_keywords_list.extend(self.get_related_keywords(keyword))
        total_keywords_list.extend(self.get_top_keywords(keyword))
        total_keywords_list.extend(self.get_trend_keywords(keyword))

        brand_list = self.get_brand_list(keyword)

        # 브랜드 이름이 키워드에 포함된 경우 제외
        nobrand_keywords_list = []
        for kw in total_keywords_list:
            if not any(brand in kw for brand in brand_list):
                nobrand_keywords_list.append(kw)

        return nobrand_keywords_list

    def quit(self):
        # 드라이버 종료
        self.driver.quit()

# 실행
if __name__ == "__main__":
    keyword = input("키워드를 입력하세요: ")
    crawler = NaverShoppingCrawler()
    Total_keywords_list = crawler.get_nobrand_keywords(keyword)
    print(Total_keywords_list)