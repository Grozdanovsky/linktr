import pprint
from bs4 import BeautifulSoup
import csv
import json
import time
import random
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
import datetime
import threading
from proxy_list import LST_STATIC_PROXIES
from proxy_manager import proxy_manager

lock = threading.Lock() 


class Linktree:

    def __init__(self):
        self.counter = 0
        self.notFound = 0
        self.MAX_THREADS = 30

    def download_users(self, flat_list):
        threads = min(self.MAX_THREADS, len(flat_list))

        with ThreadPoolExecutor(max_workers=threads) as executor:
            executor.map(self.transform, flat_list)

    def transform(self, username=""):
        proxies = LST_STATIC_PROXIES
        print(self.counter)
        print(proxies[self.counter])
        if not username:
            return None

        error_count = 0
        url = f"https://linktr.ee/{username}"
        r = None
        while True:
            
            if error_count > 3:
                self.counter += 1
                
            try:
                dict_proxies = {
                    "http": proxies[self.counter],
                    "https": proxies[self.counter]
                }
                r = requests.post(url,  timeout=3)
                # proxy = random.randint(0, len(LST_STATIC_PROXIES) - 1)
                # r = requests.post(url, proxies={'http': proxies[proxy], 'https': proxies[proxy]}, timeout=3)

                # if self.counter == 1000:
                #     # time.sleep(60)
                #     self.counter = 0
                #     change_proxy = True
                if r.status_code == 404:
                    print('Error user not found!', username)
                    # self.notFound += 1
                    # time.sleep(2)
                    # if self.notFound == 20:
                    #     time.sleep(15)
                    #     self.notFound = 0

                    break

                if r.status_code == 429:
                    print("Too many requests", username)
                    # Change proxy
                    self.counter += 1
                    time.sleep(2)

                    if self.counter == len(proxies)-1:
                        self.counter = 0

                    break

                if r.status_code == 200:
                    html = r.content.decode("utf-8")
                    soup = BeautifulSoup(html, "html.parser")
                    everything = soup.find('script', {"id": "__NEXT_DATA__"})
                    data = json.loads(everything.text)

                    print("User found!", username)
                    other_links = []
                    social_media_links = []
                    user = (data.get('props', {}).get('pageProps', {}).get(
                        'account', {}).get('username'))

                    description = data.get('props', {}).get('pageProps', {}).get('description')

                    links = data.get('props', {}).get(
                        'pageProps', {}).get('account', {}).get("links")

                    for username in range(len(links)):
                        dict1 = {}
                        key = links[username - 1].get('title')
                        value = links[username - 1].get('url')
                        dict1[key] = value
                        other_links.append(dict1)

                    social_links = data.get('props', {}).get(
                        'pageProps', {}).get('account', {}).get("socialLinks", [])

                    for username in range(len(social_links)):
                        social_media_links.append(social_links[username - 1].get('url'))

                    tier = data.get('props', {}).get(
                        'pageProps', {}).get('account', {}).get('tier')

                    sensitive_content = data.get('props', {}).get(
                        'pageProps', {}).get('hasSensitiveContent')

                    result = [user, description, other_links,
                              social_media_links, tier, sensitive_content]
                    writer = csv.writer(file_)
                    writer.writerow(result)
                    # self.write_to_csv(result)
                    # update proxy counter
                    # check proxy capacity / totals
                    return result

            except Exception as err:
                print(err)
                error_count += 1
                if r and r.status_code == 200:
                    break
        return None


if __name__ == '__main__':

    with open('users_test.csv', 'r') as users:  # this is the file that you read from

        csv_reader = csv.reader(users)
        list_of_users = list(csv_reader)
        flat_list = [item for sublist in list_of_users for item in sublist]

    # flat_list = ['StarkvillePony']
    # download_users(flat_list)
    notFound = 0

    start = time.time()
    linktr = Linktree()

    file_path = f"results-{datetime.datetime.now():%Y%m%d%H%M%S}.csv"
    file_=  open(file_path, 'a', newline="", encoding='utf-8')
    writer = csv.DictWriter(file_, fieldnames=['user', 'description', 'other_links', 'social_links', 'tier',
                                                'sensitive_content'])
    writer.writeheader()
    writer = csv.writer(file_)

    for username_ in flat_list:
        record = linktr.transform(username=username_)

    file_.close()

    # file_ = open(file_path, 'a', newline="", encoding='utf-8')
    # writer = csv.DictWriter(file_, fieldnames=['user', 'description', 'other_links', 'social_links', 'tier',
    #                                        'sensitive_content'])
    # writer.writeheader()
    #
    # with ThreadPoolExecutor(max_workers=10) as pool:
    #     futures = []
    #     for username_ in flat_list:
    #         futures.append(pool.submit(linktr.transform,
    #                                    username=username_
    #                                    ))
    #
    #     for future_ in as_completed(futures):
    #         record = future_.result()
    #         with lock:
    #             writer.writerow(record)
    #
    # file_.close()

    end = time.time()
    print(f'time it took  {end - start}')
