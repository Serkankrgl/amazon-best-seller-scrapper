import csv
from bs4 import BeautifulSoup
from selenium import webdriver
import xlsxwriter
import time
from datetime import date
today = date.today()
name = 'new_release {} .xlsx'
name = name.format(today).strip()
workbook = xlsxwriter.Workbook(name)
worksheet = workbook.add_worksheet()
options = webdriver.ChromeOptions()
options.add_argument("start-maximized")
options.add_experimental_option("excludeSwitches", ["enable-automation"])
options.add_experimental_option('useAutomationExtension', False)
driver = webdriver.Chrome(options=options,executable_path='./bin/chromedriver.exe')

baseUrlEU = 'https://www.amazon.com'
baseUrlJP = 'https://www.amazon.co.jp'
#bestSellerUrl = 'https://www.amazon.co.jp/Best-Sellers/zgbs'
bestSellerUrl = 'https://www.amazon.co.jp/-/en/gp/new-releases/ref=zg_bs_tab'
sleepSec = 5
searchUrl = 'www.amazon.com/s?k={}&i={}'

worksheet.write(0, 0, 'finalSearchUrl')
worksheet.write(0, 1, 'UrlEU')
worksheet.write(0, 2, 'UrlJP')
worksheet.write(0, 3, 'İç Kategori')
worksheet.write(0, 4, 'Dış Kategori')
worksheet.write(0, 5, 'ASIN')

def getBestSellerCategories(categories):
    blackList = []


    bestSellerCategories = []
    file = open("blacklist.txt", "r")
    for line in file:
        blackList.append(line.strip())

    for category in categories:

        try:
            aTag = category.a
            href = aTag.get('href').replace('/ref=zg_bs_nav_0','')
        except AttributeError:
            continue

        url = baseUrlJP + href
        title = aTag.text
        result = (title, url)

        if blackList.__contains__(title) == False:
            bestSellerCategories.append(result)

    return bestSellerCategories


if __name__ == '__main__':

    driver.get(bestSellerUrl)
    soup = BeautifulSoup(driver.page_source, 'html.parser')
    categories = soup.find_all('div', {'role': 'treeitem'})
    time.sleep(sleepSec)

    for page in getBestSellerCategories(categories):
        gridindex = 0
        for index in range(1,2):

            PageUrl = page[1].strip()+'?pg='+str(index)
            driver.get(PageUrl.strip())
            SCROLL_PAUSE_TIME = 0.5

            # Get scroll height
            last_height = driver.execute_script("return document.body.scrollHeight")

            while True:
                # Scroll down to bottom
                driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")

                # Wait to load page
                time.sleep(SCROLL_PAUSE_TIME)

                # Calculate new scroll height and compare with last scroll height
                new_height = driver.execute_script("return document.body.scrollHeight")
                if new_height == last_height:
                    break
                last_height = new_height

            time.sleep(sleepSec)#waiting 5 sec for the html render
            soup = BeautifulSoup(driver.page_source, 'html.parser')

            gridItems = soup.find_all('div', {'id' : 'gridItemRoot'})
            row=1
            for gridItem in gridItems:
                col=0
                gridindex = gridindex + 1
                if gridindex < 50:
                    continue
                productCode = gridItem.find('div', {'class': 'zg-grid-general-faceout'}).findChild('div',recursive=False).get('id')
                EUURL= baseUrlEU +'/dp/'+productCode
                JPURL = baseUrlJP +'/dp/'+productCode

                driver.get(JPURL)
                try:
                    soup = BeautifulSoup(driver.page_source, 'html.parser')
                    breadcrumCoiner = soup.find('div',{'id': 'wayfinding-breadcrumbs_feature_div'})
                    finalBreadcrum = breadcrumCoiner.find_all('a',{'class': 'a-link-normal'})
                    bestsellercatss = soup.find('table',{'id': 'productDetails_detailBullets_sections1'})
                    checkgrid = False
                    try:
                        table = bestsellercatss.tbody
                        tr = table.find_all('tr')
                        index = 0
                        for i in tr:
                            th = i.th
                            if th.text.strip() == 'Amazon Bestseller':
                                break
                            index = index+1
                        aTag2 = tr[index].td.find_all('a')
                        text3 =aTag2[len(aTag2)-1].text
                        checkgrid = True
                    except AttributeError:
                        test = soup.find_all('Amazon Bestseller')
                        print(test)
                    innerCat = finalBreadcrum[len(finalBreadcrum)-1].text
                    outerCat = finalBreadcrum[0].text
                    if checkgrid :
                        finalSearchUrl = searchUrl.format(text3.strip().replace(' ', '+'), outerCat.strip())

                    else:
                        finalSearchUrl = searchUrl.format(innerCat.strip().replace(' ','+'),outerCat.strip())

                    worksheet.write(row, col, finalSearchUrl)
                    worksheet.write(row, col+1, EUURL)
                    worksheet.write(row, col+2, JPURL)
                    worksheet.write(row, col+3, innerCat)
                    worksheet.write(row, col+4, outerCat)
                    worksheet.write(row, col+5, productCode)

                    row= row+1

                    print(gridindex,productCode,EUURL, JPURL,innerCat,outerCat,finalSearchUrl)
                    print('******************************************************************************************')
                except AttributeError:
                    continue
                time.sleep(sleepSec)



            time.sleep(sleepSec)
            #quick actions causes crush. Solutions: sleep
        break
    workbook.close()
    driver.close()
