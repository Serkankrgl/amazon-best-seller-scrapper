from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
import xlsxwriter
import time
from datetime import date

# region Selenium Setup

options = webdriver.ChromeOptions()
options.add_argument("start-maximized")
options.add_experimental_option("excludeSwitches", ["enable-automation"])
options.add_experimental_option('useAutomationExtension', False)

# endregion

# region URLS
AMAZON_EU = 'https://www.amazon.com'
AMAZON_JP = 'https://www.amazon.co.jp'

Amazon_Search = 'www.amazon.com/s?k={}&i={}'

# endregion

# region Variables

delay = 5


# endregion

# region Functions
class AmazonScrapper:
    urls = {'Best Sellers':'https://www.amazon.co.jp/-/en/gp/bestsellers/ref=zg_bs_tab',
            'Hot New Releases':'https://www.amazon.co.jp/-/en/gp/new-releases/ref=zg_bs_tab',
            'Movers & Shakers':'https://www.amazon.co.jp/-/en/gp/movers-and-shakers/ref=zg_bsnr_tab',
            'Most Wished For':'https://www.amazon.co.jp/-/en/gp/most-wished-for/ref=zg_bsms_tab',
            'Most Gifted':'https://www.amazon.co.jp/-/en/gp/most-gifted/ref=zg_mw_tab'}
    def __init__(self, url):
        self.driver = webdriver.Chrome(options=options, executable_path='./bin/chromedriver.exe')
        self.url = self.urls[url]
        self.url_name = url
        self.categories = self.get_categories()

    def get_categories(self):
        black_list = []
        file = open("blacklist.txt", "r")
        for line in file:
            black_list.append(line.strip())

        categories = []
        self.driver.get(self.url)
        myElem = WebDriverWait(self.driver, delay).until(EC.presence_of_element_located((By.ID, 'a-page')))
        soup = BeautifulSoup(self.driver.page_source, 'html.parser')
        raw_categories = soup.find_all('div', {'role': 'treeitem'})

        for category in raw_categories:
            try:
                a_tag = category.a
                href = a_tag.get('href').replace('/ref=zg_bs_nav_0', '')
                category_name = a_tag.text
            except AttributeError:
                # TODO Tag Bulunamaz ise hata fırlat
                continue

            if not black_list.__contains__(category_name):
                categories.append((category_name, href))

        return categories

    def get_product_info(self):
        workbook = xlsxwriter.Workbook(self.url_name.replace(' ','_')+str(date.today())+'.xlsx')
        worksheet = workbook.add_worksheet()
        SCROLL_PAUSE_TIME = 0.5
        for category in self.categories:
            grid_index = 0
            for page_number in range(1,3):
                active_url = AMAZON_JP + category[1].strip()+'?pg='+str(page_number)
                self.driver.get(active_url.strip())
                time.sleep(delay)
                last_height = self.driver.execute_script("return document.body.scrollHeight")

                while True:
                    # Scroll down to bottom
                    self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")

                    # Wait to load page
                    time.sleep(SCROLL_PAUSE_TIME)

                    # Calculate new scroll height and compare with last scroll height
                    new_height = self.driver.execute_script("return document.body.scrollHeight")
                    if new_height == last_height:
                        break
                    last_height = new_height


                soup = BeautifulSoup(self.driver.page_source, 'html.parser')
                grid_items = soup.find_all('div', {'id': 'gridItemRoot'})

                row = 0
                for grid_item in grid_items:
                    grid_index = grid_index+1
                    product_code = grid_item.find('div', {'class': 'zg-grid-general-faceout'}).findChild('div',recursive=False).get('id')

                    product_url_eu = AMAZON_EU + '/dp/' + product_code
                    product_url_jp = AMAZON_JP + '/dp/' + product_code
                    self.driver.get(product_url_jp)
                    time.sleep(delay)
                    try:
                        soup = BeautifulSoup(self.driver.page_source, 'html.parser')
                        breadcrum_coiner = soup.find('div', {'id': 'wayfinding-breadcrumbs_feature_div'})
                        breadcrums = breadcrum_coiner.find_all('a', {'class': 'a-link-normal'})
                        innerCat = breadcrums[len(breadcrums) - 1].text
                        outerCat = breadcrums[0].text
                        bestsellercatss = soup.find('table', {'id': 'productDetails_detailBullets_sections1'})
                        if not bestsellercatss is None:
                            bestsellercatss = soup.find('table', {'id': 'productDetails_detailBullets_sections1'})

                            table = bestsellercatss.tbody
                            tr = table.find_all('tr')
                            index = 0
                            try:
                                for i in tr:
                                    th = i.th
                                    if th.text.strip() == 'Amazon Bestseller':
                                        break
                                    index = index + 1
                                aTag2 = tr[index].td.find_all('a')
                                text3 = aTag2[len(aTag2) - 1].text
                            except IndexError:
                                continue
                            search_url = Amazon_Search.format(text3.strip().replace(' ', '+'), outerCat.strip())

                        else:
                            search_url = Amazon_Search.format(innerCat.strip().replace(' ', '+'), outerCat.strip())

                        worksheet.write(row, 0, search_url)
                        worksheet.write(row, 1, product_url_eu)
                        worksheet.write(row, 2, product_url_jp)
                        worksheet.write(row, 3, innerCat.strip())
                        worksheet.write(row, 4, outerCat.strip())
                        worksheet.write(row, 5, product_code.strip())

                        row = row + 1
                        print(' {0} , {1} , {2} , {3} , {4} ,{5},{6}'.format(grid_index,product_code.strip(), innerCat.strip(), outerCat.strip(), search_url,product_url_eu, product_url_jp))
                        print(
                            '******************************************************************************************')

                    except AttributeError:
                        continue
        workbook.close()
    def terminate_driver(self):
        self.driver.close()
# endregion
