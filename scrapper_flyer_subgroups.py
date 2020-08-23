import asyncio
import random
import re

import save_excel_flyer

import aiofiles

import aiohttp
import requests
from lxml.html import fromstring

from urllib.parse import urljoin

DOMAIN = 'https://www.wir-machen-druck.de/'
GROUP_URL = \
    'https://www.wir-machen-druck.de/extrem-guenstig-bedruckte-zeitschriften-drucken,category,13309.html'


async def make_request(client, url, method="GET", **kwargs):
    async with aiofiles.open('./logs.log', "a") as out:
        log = f'[make_request]  url: {url}  data:{kwargs} + \n'
        await out.write(log)
        await out.flush()
        print(log)
    try:
        response = await client.request(method=method, url=url, **kwargs)
    except Exception as exc:
        print(exc)
        await asyncio.sleep(random.uniform(3.0, 7.0))
        response = await client.request(method=method, url=url, **kwargs)
    response = await response.text()
    return fromstring(response)


async def get_group(group_url):
    response = requests.get(group_url).text
    html = fromstring(response)
    category_titles = html.xpath('.//a[@class="navSmall"]/text()')
    category_urls = html.xpath('.//a[@class="navSmall"]/@href')
    del category_titles[1:4], category_titles[2:4], category_titles[3:5], category_titles[4:]
    del category_urls[1:4], category_urls[2:4], category_urls[3:5], category_urls[4:]

    titles_urls_list = list()
    for category_title, category_urls in zip(category_titles, category_urls):
        titles_urls_list.append([category_title, category_urls])
    loop = asyncio.get_running_loop()
    info_about_group_list = ['Broschüren']
    async with aiohttp.ClientSession(loop=loop, connector=aiohttp.TCPConnector(verify_ssl=False)) as client:
        category = await asyncio.gather(
            *[get_subcategories(client, category[0], urljoin(DOMAIN, category[1])) for category in
              titles_urls_list])
        info_about_group_list.append(category)
    save_excel_flyer.insert_word_into_excel(info_about_group_list)


async def get_subcategories(client, title, category_url):
    html = await make_request(client, category_url)
    subcategories = html.xpath('.//a[@class="navSmall"]/@href')
    info_about_category_list = [title]

    subcategories = await asyncio.gather(
        *[get_products(client, urljoin(DOMAIN, subcategory)) for subcategory in subcategories])
    info_about_category_list.append(subcategories)
    return info_about_category_list


async def get_products(client, subcategory_url):
    products = []
    try:
        html = await make_request(client, subcategory_url)
        products_url = html.xpath('.//a[@name="Submit2"]/@href')
        products_title = await asyncio.gather(
            *[get_product(client, product_url=urljoin(DOMAIN, product)) for product in products_url])
        products.append(products_title)
    except Exception as exc:
        print('******** ERROR')
        print(exc)

    return products  # {'subcategory': [[product_price1, link], [product_price2], link]}


async def get_product(client, product_url):
    html = await make_request(client, product_url)
    product_options = html.xpath('.//select[@name="sorten"]//option')
    product_name = html.xpath('.//h1[@class="product-title"]/strong/text()')[0]

    product_data = [product_name, product_url]
    for product_option in product_options:
        product_option_value = product_option.attrib['value']
        product_option_name = product_option.attrib['label']
        # {'Naturpapier 90g':
        #   [
        #       {'without_delivery': ['25 stuck 6.50 EURO, 50 stuck 7.80 EURO']}
        #       {'24h-Express-Produktion': ['6.30', '7.50']}
        #   ]
        # }
        data = {'sorten': product_option_value}
        l_ = await get_options(client, product_url, data=data)
        # {'24h-Express-Produktion': ['6.30', '7.50']}
        product_data.append([product_option_name, l_])
        break  # -----------------------
    return product_data  # {'product': [deliveries], 'link': product_url}


async def get_options(client, product_url, data):
    html = await make_request(client, product_url, method="POST", data=data)
    price_dict = ['kostenlosem Versand', html.xpath('.//select[@name="auflage"]//option/@label')]
    del price_dict[1][0]
    # price
    # for amount in amount_list:
    #     delivery_prices = await get_delivery_type(client,
    #                                               product_url,
    #                                               {**data, "auflage": amount.attrib['value']})
    #     if delivery_prices is False:
    #         break
    #
    #      price in delivery_prices:
    #         updated_price = input_delivery_price_instead_netto(amount.attrib['label'],
    #                                                            price)
    #         delivery_price_list.append(updated_price)
    #     break #-------------------

    return [price_dict]
    # Price_list [['24h-Express-Produktion', ['6.30', '7.50']], ['kostenlosem', ['5.32','4.23']]]


def input_delivery_price_instead_netto(amount, price):
    replacement = re.sub(r'(\d{1,4}\.){0,3}\d{1,10},\d{0,2}', price, amount)
    return replacement


async def get_delivery_type(client, product_url, data):
    price_delivery_list = []
    html = await make_request(client, product_url, method="POST", data=data)
    try:
        delivery_type = \
            html.xpath('//div[@class="card-text delivery-container"]//input[@id="feld_23"]/@name')[0]
        data[delivery_type] = 123
        price_delivery_list.append(
            await visit_delivery_option(client, product_url, data=data))
        return price_delivery_list  # PRICE(['6.30'])
    except IndexError:
        return False


async def visit_delivery_option(client, product_url, data):
    html = await make_request(client, product_url, method="POST", data=data)
    delivery_price = html.xpath(
        './/strong[@id="net-price"]/text()')[0].strip()
    return delivery_price  # Price '6.30'


if __name__ == '__main__':
    from datetime import datetime

    n = datetime.now()
    asyncio.run(get_group(GROUP_URL))
    print(datetime.now() - n)
