import re
import time
from datetime import datetime

import requests
from bs4 import BeautifulSoup

import schedule


url = 'https://fix-price.kz/'
headers = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/94.0.4606.71 Safari/537.36 RuxitSynthetic/1.0 v3975717906 t6703941201591042144 athfa3c3975 altpub cvcv=2 smf=0"
}


def get_data():
    req = requests.get(url=url, headers=headers)
    req.encoding = 'UTF8'
    src = req.text
    soup = BeautifulSoup(src, 'lxml')

    # with open('home_page.html', 'w', encoding='utf-8') as file:
    #     file.write(src)

    # Сбор всех ссылок на каталоги
    dict_catalog = []
    categories = soup.find('div', class_='catalog-dropdown collapse').find('nav', class_='catalog-nav').find_all('a')
    for a in categories:
        url_cat = f"https://fix-price.kz{a.get('href')}"
        dict_catalog.append(url_cat)

    link_cards_page = []
    for url_catalog in dict_catalog:
        page = 1
        while True:
            print(f'{url_catalog}?PAGEN_1={page}')
            req1 = requests.get(url=f'{url_catalog}?PAGEN_1={page}', headers=headers)
            req1.encoding = 'UTF8'
            src1 = req1.text
            soup1 = BeautifulSoup(src1, 'lxml')

            # with open('home_page.html', 'w', encoding='utf-8') as file:
            #     file.write(src1)

            all_url_cards_page = soup1.find('div', class_='main-list-item')\
                .find_all('div', itemprop='itemListElement')
            for url_card in all_url_cards_page:
                link = url_card.find('link').get('href')
                link_cards_page.append(link)
                # print(link)

            page += 1
            if len(soup1.find_all('div', class_='btn-container')) == 0:
                break

    list_products = [['Каталог', 'Артикул', 'Название', 'Бренд', 'Цена', 'Ссылка']]
    max_product = len(link_cards_page)
    count = 0
    for link_cards in link_cards_page:
        try:
            url_product = f'https://fix-price.kz{link_cards}'
            req2 = requests.get(url=f'https://fix-price.kz{link_cards}', headers=headers)
            req2.encoding = 'UTF8'
            src2 = req2.text
            soup2 = BeautifulSoup(src2, 'lxml')

            # with open('home_page.html', 'w', encoding='utf-8') as file:
            #     file.write(src2)

            categories = soup2.find('div', class_='container container--full container--gray')\
                .find('div', class_='container').find_all('div', class_='breadcrumb__item')
            if len(categories) == 3:
                categories = f'{categories[1].text.strip()}'
            elif len(categories) > 3:
                categories = f'{categories[1].text.strip()}/{categories[-2].text.strip()}'
            else:
                categories = 'не указан'
            # print(categories)

            article = soup2.find('div', class_='product-detail-card-info')\
                .find_all('div', class_='product-detail-card-info__brand')[0].find('span').text.strip()
            # print(article)

            name = soup2.find('div', class_='page-header__title').text.strip()
            # print(name)

            if len(soup2.find_all('div', class_='product-detail__item')[0].find('div', class_='product-detail-card-info').find_all('div', class_='product-detail-card-info__brand')) > 1:
                brand = soup2.find_all('div', class_='product-detail__item')[0].find('div', class_='product-detail-card-info')\
                    .find_all('div', class_='product-detail-card-info__brand')[-1]\
                    .find('span', class_='product-detail-card-info__brand-value').find('a').text
            else:
                brand = 'не указан'
            # print(brand)

            if len(soup2.find_all('div', class_='product-detail__item')[1].find_all('div', class_=re.compile('product-detail-aside__badge-price product-card__badge-price--'))) == 1:
                price = soup2.find_all('div', class_='product-detail__item')[1]\
                    .find('div', class_=re.compile('product-detail-aside__badge-price product-card__badge-price--'))\
                    .text.replace(' ', '').replace('теңге', '').strip()
            else:
                price = 'не указана'
            # print(price)

            list_products.append(
                [
                    categories, article, name, brand, price, url_product
                ]
            )
            count += 1
            print(f'{count}/{max_product}')
            # print(categories, article, name, brand, price, link_cards)

        except Exception as ex:
            print(ex)
            print(f'Ошибка в товаре: https://fix-price.kz{link_cards}')
            count += 1
            print(f'{count}/{max_product}')
            continue

    google_table(dict_cards=list_products)


def google_table(dict_cards):
    import os.path

    from googleapiclient.discovery import build
    from googleapiclient.errors import HttpError
    from google.oauth2 import service_account

    SCOPES = ['https://www.googleapis.com/auth/spreadsheets']

    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    SERVICE_ACCOUNT_FILE = os.path.join(BASE_DIR, 'credentials.json')

    credentials = service_account.Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE, scopes=SCOPES)

    # mail bot 'parsers@parsers-372008.iam.gserviceaccount.com'
    SAMPLE_SPREADSHEET_ID = '107SdHe8_dV6npe_dKE-7xA2QJgxz6ZOywOy-GZyrZX0'
    SAMPLE_RANGE_NAME = 'fix-price.kz!A1:F'

    try:
        service = build('sheets', 'v4', credentials=credentials).spreadsheets().values()

        # Чистим(удаляет) весь лист
        array_clear = {}
        clear_table = service.clear(spreadsheetId=SAMPLE_SPREADSHEET_ID,
                                    range=SAMPLE_RANGE_NAME,
                                    body=array_clear).execute()

        # добавляет информации
        array = {'values': dict_cards}
        response = service.append(spreadsheetId=SAMPLE_SPREADSHEET_ID,
                                  range=SAMPLE_RANGE_NAME,
                                  valueInputOption='USER_ENTERED',
                                  insertDataOption='OVERWRITE',
                                  body=array).execute()

    except HttpError as err:
        print(err)


def main():
    start_time = datetime.now()

    schedule.every(35).minutes.do(get_data)
    while True:
        schedule.run_pending()

    finish_time = datetime.now()
    spent_time = finish_time - start_time
    print(spent_time)


if __name__ == '__main__':
    main()
