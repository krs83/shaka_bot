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
            soup = BeautifulSoup(res, "lxml")

            # Парсинг общей таблицы с Академиями
            af_results = []
            async for result in div_parsing(soup, "rate-stat", "rate-stat-table"):
                af_results.append(result)

            # Парсинг AF спортсменов
            async for result in div_parsing(
                soup, "rate-stat-leaders", "rate-stat-table"
            ):
                af_results.append(result)
            return af_results


def check_af(text) -> bool:
    """
    Функция для проверки, содержит ли переданный текст какое-либо из названий академий AF из словаря academy_titles.

    Args:
        text (str): Текст, который нужно проверить.

    Returns:
        bool: True, если текст содержит одно из названий академий, иначе False.
    """

    return any(title in text for title in academy_titles.values())


async def div_parsing(soup, find_all_class, rows_class):
    """
    Асинхронный генератор для парсинга div элементов.
    """
    box = soup.find_all("div", class_=find_all_class)

    for b in box:
        table_rows = b.find("div", class_=rows_class)
        if check_af(table_rows.text):
            yield str(b.text.replace("\n\n\n", " "))
