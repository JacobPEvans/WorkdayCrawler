import concurrent.futures
import json
import requests
import sys
import time

from bs4 import BeautifulSoup
from selenium import webdriver

HTML_PARSER = "html.parser"
GOOGLE_URL = 'https://www.google.com/search?q=myworkdayjobs.com'


class WorkdayCrawler(object):

    def get_by_company(self, company_name):
        response = requests.get(GOOGLE_URL + '+' + company_name)
        if response.status_code == requests.codes.ok:
            soup = BeautifulSoup(response.content, HTML_PARSER)
            workday_raw_urls = soup.find_all('h3')

            raw_url = None
            for company_link in workday_raw_urls:
                temp = str(company_link.a['href'])
                if self.is_googled_url_legit(temp):
                        raw_url = temp
                        break

            if not raw_url:
                print('Company not found in workday')
                return

            position_list = self.hack_a_company(raw_url)

            company_object  = {}
            company_object[company_name] = position_list
            json_output = json.dumps(company_object)
            self.save_to_file(json_output, company_name)

        else:
            print(response.status_code)
            print('Unable to reach google')

    def is_googled_url_legit(self, url):
        return url and 'https' in url and 'myworkdayjobs.com' in url

    # get the companies in the first google search page
    def get(self):
        company_object = {}

        list_req = requests.get(GOOGLE_URL)
        if list_req.status_code == requests.codes.ok:
            soup = BeautifulSoup(list_req.content, HTML_PARSER)
            workday_raw_urls = soup.find_all('h3')

            for company_link in workday_raw_urls:
                raw_url = str(company_link.a['href'])
                if self.is_googled_url_legit(raw_url):

                    company_name = raw_url[raw_url.index('https:')+8:raw_url.index('.')]
                    if company_name in company_object:
                        # done this before
                        continue
                    position_list = self.hack_a_company(raw_url)
                    company_object[company_name] = position_list

            json_output = json.dumps(company_object)
            self.save_to_file(json_output)

        else:
            print (list_req.status_code)
            print ('Unable to reach google')

    def hack_a_company(self, raw_url):
        # url: company's career landing page
        url = raw_url[raw_url.index('https'): raw_url.index('&')]

        position_url_list = self.get_list_of_position_url(url)

        base_url = url[:url.index('/', 10)]

        position_list = []

        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            funture_positions = []
            for position_url in position_url_list:
                complete_url = base_url + position_url
                future_position = executor.submit(self.get_position_detail, complete_url)
                funture_positions.append(future_position)

        for future in concurrent.futures.as_completed(funture_positions):
            try:
                position = future.result()
            except Exception as exc:
                print (exc)
            else:
            	position_list.append(position)

        return position_list

    # get list of positions from the company's career landing page
    def get_list_of_position_url(self, landing_page_url):
        
        # PhantomJs - need to use your own phantom path
        browser = webdriver.PhantomJS(executable_path=r'/usr/local/bin/phantomjs')  
        browser.get(landing_page_url)
        # wait until the url change
        time.sleep(5)
        current_url = browser.current_url
        browser.close()
        
        # first url example
        # https://cornell.wd1.myworkdayjobs.com/CornellCareerPage/2/refreshFacet/318c8bb6f553100021d223d9780d30be
        # next urls example
        # https://cornell.wd1.myworkdayjobs.com/CornellCareerPage/3/searchPagination/318c8bb6f553100021d223d9780d30be/50

        position_list = self.parse_position_url_list(current_url)
        all_position_urls = []
        pagination_count = 0
        pagination_url = current_url.replace('refreshFacet', 'searchPagination')

        # while there's still something in the list, if not, meaning there's no more
        while position_list:
            all_position_urls.extend(position_list)
            pagination_count += 50
            position_list = self.parse_position_url_list(pagination_url, pagination_count)

        return all_position_urls

    # get url for each position 
    def parse_position_url_list(self, url, count=None):
        url_list = []
        if count:
            url = url + '/' + str(count)
        print (url)
        response = requests.get(url, headers={"Accept":"application/json"})
        if not response or response.status_code == requests.codes.not_found:
            return url_list

        dict_response = json.loads(response.text)
        for first_child in dict_response.get('body').get('children'):
            if first_child.get('widget') == 'facetSearchResult':
                second_children = first_child.get('children')
                if not second_children:
                    continue
                for second_child in second_children:
                    if second_child.get('widget') == 'facetSearchResultList':
                        list_items = second_child.get('listItems')
                        if not list_items:
                            break
                        for list_item in list_items:
                            command_link = list_item.get('title').get('commandLink')
                            if command_link:
                                url_list.append(command_link)
        return url_list

    def get_position_detail(self, url):
        print (url)
        response = requests.get(url, headers={"Accept":"application/json"})
        dict_response = json.loads(response.text)
        all_detail = dict_response.get('openGraphAttributes')
        # pop unwanted info
        all_detail.pop('imageUrl')
        all_detail.pop('type')
        all_detail.pop('description')
        return all_detail

    def save_to_file(self, content, company_name='wordday_jobs'):
        f = open(company_name + '.json', 'wb')
        f.write(content.encode('utf8'))
        f.close()

if __name__ == '__main__':
    companies = sys.argv[1:]
    workday = WorkdayCrawler()
    for c in companies:
        workday.get_by_company(c)
