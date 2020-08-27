import time
from selenium.common.exceptions import NoSuchElementException
import json
from datetime import datetime
from selenium.webdriver.common.keys import Keys
from config import (
    get_web_driver_options,
    get_chrome_web_driver,
    set_ignore_certificate_error,
    set_browser_as_incognito,
    set_automation_as_head_less,
    NAME,
    CURRENCY,
    FILTERS,
    BASE_URL,
    DIRECTORY
)


class GenerateReport:
    def __init__(self, file_name, filters, base_link, currency, data):
        self.data = data
        self.file_name = file_name
        self.filters = filters
        self.base_link = base_link
        self.currency = currency
        report = {
            'title': self.file_name,
            'date': self.get_now(),
            'currency': self.currency,
            'filters': self.filters,
            'base_link': self.base_link,
            'products': self.data
        }
        print("Creating report...")
        with open(f'{DIRECTORY}/{file_name}.json', 'w') as f:
            json.dump(report, f)
        print("Done...")

    @staticmethod
    def get_now():
        now = datetime.now()
        return now.strftime("%d/%m/%Y %H:%M:%S")



class EmagAPI:
    def __init__(self, search_term, filters, base_url, currency):
        self.base_url = base_url
        self.search_term = search_term
        options = get_web_driver_options()
        set_ignore_certificate_error(options)
        set_browser_as_incognito(options)
        self.driver = get_chrome_web_driver(options)
        self.currency = currency
        self.price_filter = f"pret,intre-{filters['min']}-si-{filters['max']}"

    def run(self):
        print("Starting Script...")
        print(f"Looking for {self.search_term} products...")
        links = self.get_products_links()
        if not links:
            print("Stopped script.")
            return
        print(f"Got {len(links)} links to products...")
        print("Getting info about products...")
        products = self.get_products_info(links)
        print(f"Got info about {len(products)} products...")
        self.driver.quit()
        return products

    def get_single_product_info(self, asin):
        ID = self.get_ID(asin)
        print(f"Product ID: {ID} - getting data...")
        product_short_url = self.shorten_url(asin)
        self.driver.get(f'{product_short_url}')
        time.sleep(2)
        title = self.get_title()
        seller = self.get_seller()
        price = self.get_price()
        if title and seller and price:
            product_info = {
                'asin': asin,
                'url': product_short_url,
                'title': title,
                'seller': seller,
                'price': price
            }
            return product_info
        return None

    def get_title(self):
        try:
            return self.driver.find_element_by_class_name('page-title').text
        except Exception as e:
            print(e)
            print(f"Can't get title of a product - {self.driver.current_url}")
            return None

    def get_products_info(self,links):
        asins = self.get_asins(links)
        products = []
        for asin in asins:
            product = self.get_single_product_info(asin)
            if product:
                products.append(product)
        return products
    
    def get_seller(self):
        try:
            return self.driver.find_element_by_class_name('inline-block').text
        except Exception as e:
            print(e)
            print(f"Can't get seller of a product - {self.driver.current_url}")
            return None

    def get_price(self):
        price = None
        try:
            price = self.driver.find_element_by_css_selector("div.w-50.mrg-rgt-xs p.product-new-price").text;
            price = self.convert_price(price)
        except NoSuchElementException:
            try:
                availability = self.driver.find_element_by_class_name('label.label-in_stock').text
                if 'În stoc' in availability:
                    price = self.driver.find_element_by_class_name('product-new-price').text
            except Exception as e:
                print(e)
                print(f"Can't get price of a product - {self.driver.current_url}")
                return None
        except Exception as e:
            print(e)
            print(f"Can't get price of a product - {self.driver.current_url}")
            return None
        #print(price)
        return price

    def convert_price(self,price):
        return(price[:len(price)-6] + ',' + price[len(price)-6:len(price)-4] + " " + price[len(price)-3:])

    def get_asins(self,links):
        return [self.get_asin(link) for link in links]

    @staticmethod
    def get_asin(product_link):
        #print(product_link[product_link.find('.ro/') + 4:product_link.find('/?X')])
        return product_link[product_link.find('.ro/') + 4:product_link.find('/?X')]
        
#https://www.emag.ro/casti-bluetooth-samsung-galaxy-buds-silver-sm-r170nzsarom/pd/DXD415BBM/?path=casti-bluetooth-samsung-galaxy-buds-silver-sm-r170nzsarom/pd/DXD415BBM
#https://www.emag.ro/casti-bluetooth-samsung-galaxy-buds-silver-sm-r170nzsarom/pd/DXD415BBM/?X-Search-Id=2024b344bc2ccf785507&X-Product-Id=5877319&X-Search-Page=1&X-Search-Position=0&X-Section=search&X-MB=0&X-Search-Action=view
    
    @staticmethod   
    def get_ID(asin):
        return asin[asin.find('/pd/') + 4: ]

    def shorten_url(self, asin):
        return self.base_url + asin
    
    def get_products_links(self):
        self.driver.get(self.base_url)
        element = self.driver.find_element_by_xpath('//*[@id="searchboxTrigger"]')
        element.send_keys(self.search_term)
        element.send_keys(Keys.ENTER)
        time.sleep(2) 
        self.driver.get(f'{self.driver.current_url}{self.price_filter}')
        print(f"Our url: {self.driver.current_url}")
        time.sleep(2)
        links = []
        try:
            result_list  = self.driver.find_elements_by_class_name("thumbnail-wrapper.js-product-url")
            for elem in result_list:
                links.append(elem.get_attribute('href'))
            return links
        except Exception as e:
            print("Didn't get any products...")
            print(e)
            return links
        

if __name__ == '__main__':
    emag = EmagAPI(NAME, FILTERS, BASE_URL, CURRENCY)
    data = emag.run()
    GenerateReport(NAME, FILTERS, BASE_URL, CURRENCY, data)