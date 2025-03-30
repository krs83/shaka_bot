from bs4 import BeautifulSoup


def parsing(html_string):
    soup = BeautifulSoup(html_string, 'html.parser')

    fights = []

    # Находим все строки с информацией о боях
    for row in soup.find_all('tr', style="line-height: 30px"):
        time_element = row.find('td', class_='schedule_cat_title')

        if not time_element:
            continue

        time = time_element.text.split('|')[0].strip()

        fighters = []
        for fighter_element in row.find_all('td', class_='schedule_comp_name'):
            fighters.append(fighter_element.text.strip())

        if len(fighters) == 2:
            fights.append({
                "time": time,
                "red_fighter": fighters[0],
                "blue_fighter": fighters[1]
            })
    return fights



def find_matching_fights(text, fighters):
    for fights in fighters:
        for keys, values in fights.items():
            if text in values:
                print(f"""Время: {fights['time']}
Спортсмен в красном: {fights['red_fighter']}
Спортсмен в синем: {fights['blue_fighter']}
                    """)
