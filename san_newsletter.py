import glob
import os
import re
import time

import requests
import schedule
from bs4 import BeautifulSoup
from decouple import config


def source_data():
    source = "https://lodz.san.edu.pl/strefa-studenta/plany-zajec/"
    return source


def data():
    payload = {
        "haslo_student": config("PASSWORD"),
        "indeks_student": config("USERNAME"),
        "zaloguj_studenta": "Zaloguj"
    }
    return payload


def request_html(payload, source):
    with requests.session() as s:
        r = s.post(source, data=payload)
        soup = BeautifulSoup(r.content, "html.parser")
    return soup


def send_to_telegram(file_location):
    bot_url = 'https://api.telegram.org/bot'
    send_document = bot_url + config("TOKEN") + '/sendDocument?'
    data = {
        'chat_id': config("CHAT_ID"),
        'parse_mode': 'HTML',
        'caption': 'Nowy plan lekcji!'
    }
    files = {
        'document': open(file_location, 'rb')
    }
    requests.post(send_document, data=data, files=files, stream=True)


def update_pdfs(soup):
    list = []
    for file in glob.glob("pdfs/*.pdf"):
        list.append(file.split("pdfs/", 1)[1])

    link = ""

    for i in soup.find_all("a"):
        if re.search("^" + config("PDF_PREFIX") + ".*", i["href"]):
            link = i["href"]
            print("Newest link on website:", link)
            break

    if link != "":
        newest_pdf = link.split("wgrane-pliki/", 1)[1]
        if newest_pdf not in list:
            pdf = requests.get(link)
            open("pdfs/" + newest_pdf, "wb").write(pdf.content)
            try:
                if os.path.exists("pdfs/" + list[0]):
                    os.remove("pdfs/" + list[0])
            except:
                pass
            send_to_telegram("pdfs/" + newest_pdf)
            return "New PDF downloaded"
    return "No updates"


def scrape():
    source = source_data()
    payload = data()
    soup = request_html(payload, source)
    print(update_pdfs(soup))


def main():
    newpath = r'pdfs/'
    if not os.path.exists(newpath):
        os.makedirs(newpath)
    scrape()
    schedule.every(60).minutes.do(scrape)
    while True:
        schedule.run_pending()
        time.sleep(60)


if __name__ == "__main__":
    main()
