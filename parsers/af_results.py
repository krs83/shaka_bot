from bs4 import BeautifulSoup
import aiohttp

from config import academy_titles


async def results_af_parser(results_url):
    """
   Асинхронная функция для парсинга результатов с веб-страницы и поиска информации об AF Academy.
   """
    async with aiohttp.ClientSession() as session:
        async with session.get(results_url) as results:
            res = await results.text()
            soup = BeautifulSoup(res, 'lxml')
            box = soup.find_all('div', class_='box')

            for b in box:
                box_body = b.find('div', class_='box-body')
                if check_af(box_body.text):
                    yield str(b.text)


def check_af(text) -> bool:
    """
    Функция для проверки, содержит ли переданный текст какое-либо из названий академий AF из словаря academy_titles.

    Args:
        text (str): Текст, который нужно проверить.

    Returns:
        bool: True, если текст содержит одно из названий академий, иначе False.
    """

    return any(title in text for title in academy_titles.values())




