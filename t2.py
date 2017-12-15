import requests
import ast
import sys
import codecs
import re
import boto3
import json
import matplotlib.pyplot as plt
from tqdm import tqdm
from bs4 import BeautifulSoup
from datetime import datetime
from dateutil.parser import parse

reload(sys)
sys.setdefaultencoding('utf8')

def get_app_coments(pagenum, appid):
    print("Baixando comentarios...")
    url = "https://play.google.com/store/getreviews"

    headers = {
        "Content-Type": "application/x-www-form-urlencoded;charset=ascii"
    }

    payload = "reviewType=0&pageNum=" + pagenum + "&id=" + appid + "&reviewSortOrder=2&xhr=1&hl=en"

    text = ast.literal_eval(requests.post(url, data=payload, headers=headers).text.replace(")]}'\n\n", ""))[0][2]
    text = text.replace("\u003c", "<").replace("\u003e", ">").replace("\u003a", ":").replace("\u003b", ";").replace("\u003d", "=")

    soup = BeautifulSoup(text, "lxml")

    dates = soup.findAll("span", { "class" : "review-date" })
    reviews = soup.findAll("div", { "class" : "review-body with-review-wrapper" })

    result = []

    for i in range(len(dates)):
        try:
            result.append([dates[i].contents[0] , reviews[i].contents[2].encode("utf-8")])
        except:
            continue


    print("Comentarios baixados.")
    return result

def get_sentiment(reviews):
    comprehend = boto3.client(service_name="comprehend")

    print("Analisando sentimentos...")
    for review in tqdm(reviews):
        review[1] = comprehend.detect_sentiment(Text=review[1], LanguageCode="en")["SentimentScore"]

    return reviews

def merge_equal_days(reviews):
    
    for i in range(len(reviews)-1):
        if reviews[i] != None:
            aux =  reviews[i][1]
            divisor = 1
            for j in range(i+1, len(reviews)):
                if reviews[j] != None and reviews[i][0] == reviews[j][0]:
                    aux = sum_scores(aux, reviews[j][1])
                    divisor += 1
                    reviews[j] = None
            reviews[i][1] = div_scores(aux, divisor)

    return [x for x in reviews if x != None]

def sum_scores(scores1, scores2):
    result = {}
    
    for key in scores1:
        result[key] = scores1[key] + scores2[key]
    
    return result

def div_scores(scores, divisor):
    result = {}

    for key in scores:
        result[key] = scores[key] / divisor

    return result

if __name__ == "__main__":

    print("Insira o ID do App:")
    id = raw_input(">")

    review_list = get_app_coments("1", id)
    sentiment_list = merge_equal_days(get_sentiment(review_list))

    for elem in sentiment_list:
        elem[0] = datetime.strptime(elem[0], "%B %d, %Y")

    sentiment_list = sorted(sentiment_list)
    
    mixed = [[],[]]
    for x in sentiment_list:
        mixed[0].append(x[0])
        mixed[1].append(x[1]["Mixed"])

    positive = [[],[]]
    for x in sentiment_list:
        positive[0].append(x[0])
        positive[1].append(x[1]["Positive"])

    neutral = [[],[]]
    for x in sentiment_list:
        neutral[0].append(x[0])
        neutral[1].append(x[1]["Neutral"])

    negative = [[],[]]
    for x in sentiment_list:
        negative[0].append(x[0])
        negative[1].append(x[1]["Negative"])

    
    plt.plot(mixed[0], mixed[1], "b-", label="Mixed")
    plt.plot(positive[0], positive[1], "g-", label="Positive")
    plt.plot(neutral[0], neutral[1], "y-", label="Neutral")
    plt.plot(negative[0], negative[1], "r-", label="Negative")

    plt.title("Analise de sentimentos " + id)
    plt.ylabel('Intensidade do sentimento')
    plt.xlabel('Datas')
    plt.legend()
    plt.show()
