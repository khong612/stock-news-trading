import csv
import pandas as pd
from nltk.sentiment.vader import SentimentIntensityAnalyzer
# nltk.download("vader_lexicon")


def update_lex():
    sia = SentimentIntensityAnalyzer()

    stock_lex = pd.read_csv("data/stock_lex.csv")
    stock_lex["sentiment"] = (stock_lex["Aff_Score"] + stock_lex["Neg_Score"]) / 2
    stock_lex = dict(zip(stock_lex.Item, stock_lex.sentiment))
    stock_lex = {k: v for k, v in stock_lex.items() if len(k.split(" ")) == 1}
    stock_lex_scaled = {}
    for k, v in stock_lex.items():
        if v > 0:
            stock_lex_scaled[k] = v / max(stock_lex.values()) * 4
        else:
            stock_lex_scaled[k] = v / min(stock_lex.values()) * -4

    positive = []
    with open("data/positive.csv", "r") as f:
        reader = csv.reader(f)
        for row in reader:
            positive.append(row[0].strip())

    negative = []
    with open("data/negative.csv", "r") as f:
        reader = csv.reader(f)
        for row in reader:
            negative.append(row[0].strip())

    final_lex = {}
    final_lex.update(stock_lex_scaled)
    final_lex.update({word.lower(): 2.0 for word in positive if word.lower() not in final_lex})
    final_lex.update({word.lower(): -2.0 for word in negative if word.lower() not in final_lex})
    sia.lexicon = final_lex
    return sia
