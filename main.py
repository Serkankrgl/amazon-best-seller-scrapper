import scrapper as scr
import time

AMAZON_BEST_SELLER = 'https://www.amazon.co.jp/-/en/gp/bestsellers/ref=zg_bs_tab'

if __name__ == '__main__':
    pages = ['Best Sellers',
             'Hot New Releases',
             'Movers & Shakers',
             'Most Wished For',
             'Most Gifted']
    index = 0
    for text in pages:
        index = index + 1
        print(index,' - ',text)
    selection = input()
    s = scr.AmazonScrapper(pages[int(selection)-1])
    s.get_product_info()
    s.terminate_driver()
