import json
import requests
import threading
import time
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from update import update_lex


def get_request(url):
    header = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.77 Safari/537.36"}
    source = requests.get(url).text
    return source


def get_sentiment(name, ticker, page, sia, date_sentiments):
    html = get_request("https://www.nasdaq.com/symbol/{}/news-headlines?page={}".format(ticker, str(page)))
    soup = BeautifulSoup(html, features="html.parser")
    posts = soup.find("div", "news-headlines")
    urls = posts.find_all("a", target="_self")
    dates = posts.find_all("small")

    for i in range(len(urls)):
        time.sleep(1)
        url = urls[i]["href"].strip()
        date = dates[i].get_text().strip().split(" ")[0]

        link_page = get_request(url)
        link_soup = BeautifulSoup(link_page, features="html.parser")
        sentences = link_soup.find_all("p", attrs={"class": None})
        passage = ""
        for sentence in sentences:
            passage += sentence.text
        if passage.count(name) >= 5:
            print(date + "\t" + url.split("/")[4])
            passage = " ".join(passage.split())
            passage = passage[:len(passage) // 4]
            sentiment = sia.polarity_scores(passage)["compound"]
            date_sentiments.setdefault(date, []).append(sentiment)


def get_stock(name, ticker, pages):
    sia = update_lex()
    date_sentiments = {}
    threads = [None] * pages
    for i in range(1, pages):
        threads[i] = threading.Thread(target=get_sentiment, args=(name,ticker,i,sia,date_sentiments))
        threads[i].start()
    for i in range(1, pages):
        threads[i].join()

    date_sentiment = {}
    for k, v in date_sentiments.items():
        date_sentiment[datetime.strptime(k, "%m/%d/%Y").date() + timedelta(days=1)] = round(sum(v) / float(len(v)), 3)
    return date_sentiment
