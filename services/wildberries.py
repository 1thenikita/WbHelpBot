import requests

def get_photo_image(id):
    """
    Получение картинки продукта.

    :param id:
    :return: Ссылка
    """

    id = int(id)

    url = f'https://basket-13.wbbasket.ru/vol{int(id/100000)}/part{int(id/1000)}/{id}/info/ru/rich_v1.json'
    headers = {
        'Accept': '*/*',
        'Accept-Language': 'ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7',
        'Connection': 'keep-alive',
        'DNT': '1',
        'Origin': 'https://www.wildberries.ru',
        'Referer': 'https://www.wildberries.ru/catalog/elektronika/igry-i-razvlecheniya/aksessuary/garnitury',
        'Sec-Fetch-Dest': 'empty',
        'Sec-Fetch-Mode': 'cors',
        'Sec-Fetch-Site': 'cross-site',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36',
        'sec-ch-ua': '"Not)A;Brand";v="99", "Google Chrome";v="127", "Chromium";v="127"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"',
    }

    try:
        response = requests.get(url=url, headers=headers)

        json = response.json()
        return json.get('content')[0].get('blocks')[0].get('image').get('src') + '.webp'
    except:
        return None

def get_category(id):
    """
    Получение продукта, а также его размеров с ценами.

    :param id: ID продукта
    :return: JSON продукта с ценами.
    """

    url = f'https://card.wb.ru/cards/v2/detail?appType=1&curr=rub&dest=-2603384&spp=30&hide_dtype=10&ab_testing=false&nm={id}'.format(id=id)

    headers = {
        'Accept': '*/*',
        'Accept-Language': 'ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7',
        'Connection': 'keep-alive',
        'DNT': '1',
        'Origin': 'https://www.wildberries.ru',
        'Referer': 'https://www.wildberries.ru/catalog/elektronika/igry-i-razvlecheniya/aksessuary/garnitury',
        'Sec-Fetch-Dest': 'empty',
        'Sec-Fetch-Mode': 'cors',
        'Sec-Fetch-Site': 'cross-site',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36',
        'sec-ch-ua': '"Not)A;Brand";v="99", "Google Chrome";v="127", "Chromium";v="127"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"',
    }

    response = requests.get(url=url, headers=headers)

    return response.json()


def format_items(response):
    """
    Обработчик информации по работе с списком продуктов.

    :param response: Response
    :return: Список продуктов
    """
    products = []

    products_raw = response.get('data', {}).get('products', None)

    if products_raw != None and len(products_raw) > 0:
        for product in products_raw:
            products.append({
                'brand': product.get('brand', None),
                'name': product.get('name', None),
                'id': product.get('id', None),
                'reviewRating': product.get('reviewRating', None),
                'feedbacks': product.get('feedbacks', None),
                'price': next(iter(product.get('sizes')), None).get('price', None).get('product', None)
            })

    return products

def get_product(id):
    """
    Получает продукт через его ID.

    Формат возвращения - json.

    :param id: ID продукта
    :return:
    """
    products = get_category(id)
    return (format_items(products)[0])


def get_product_price(id):
    """
    Получает цену продукта через его ID.

    Формат возвращения - float.

    :param id: ID продукта
    :return: Float - стоимость
    """
    products = get_category(id)
    return (float(format_items(products)[0].get('price', None)) / 100)-10

if __name__ == "__main__":
    category = get_category()
    print(format_items(category))
