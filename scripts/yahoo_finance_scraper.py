#  Importing the WebDriver class for automated web browsing.
from selenium import webdriver

# Importing the Keys class for simulating keyboard inputs.
from selenium.webdriver.common.keys import Keys

# Importing the By class for locating elements on web pages.
from selenium.webdriver.common.by import By

# Importing the requests module for sending HTTP requests.
import requests

# Importing the BeautifulSoup class for parsing HTML and XML documents.
from bs4 import BeautifulSoup

# Importing the pandas library for data manipulation with the alias pd.
import pandas as pd

# Concurrent task execution in python.
import concurrent.futures

# For sentiment analysis:
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

url="https://finance.yahoo.com/quote/AAPL/news"

"""
Setting up a user-agent header to mimic a request coming from a specific web browser.
This can help in scenarios where websites need to indentify the client's browser type,
for compatibility or access purposes.
"""
headers={
    'User-Agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36 OPR/107.0.0.0'
}

# Global list allNews that will contain all the data about each article:
allNews=[]

def openWebPage(url):
    """
    Opens a web page specified by the URL using a WebDriver instance.

    The WebDriver instance returned, allows you to automate interactions with the web page.
    """
    driver=webdriver.Chrome()
    driver.get(url)
    driver.implicitly_wait(3)
    return driver

def extractNews(driver):
    """
    Scraping n number of news from the web page using the WebDriver instance.

    It returns a list of article elements found while scrolling through the page.
    """
    articlesList=[]
    # Finding the <body> element to enable scrolling:
    element=driver.find_element(By.TAG_NAME,'body')

    while len(articlesList)<100:
        # Scrolling down the web page by sending PAGE_DOWN key.
        element.send_keys(Keys.PAGE_DOWN)

        # Extracting the page source and parsing it with BeautifulSoup:
        page_source = driver.page_source
        soup = BeautifulSoup(page_source, 'html.parser')

        # The list of article elements:
        articlesList=soup.find('ul',{'class':'My(0) P(0) Wow(bw) Ov(h)'}).find_all('h3',{'class':'Mb(5px)'})

        # for debugging:
        print(len(articlesList))

        driver.implicitly_wait(3)
    driver.quit()
    return articlesList

def fetchNewsInfo(article):
    """
    Fetching the data of each article that we get from 'extractNews' function.
    Getting the date, title, context, source_namme and link of each article.
    """
    # Printing the article's title for debugging
    print(article.find('a').text)

    # Full URL of the articles:
    link = 'https://finance.yahoo.com/quote/AAPL' + article.find('a')['href']
    
    r = requests.get(link, headers=headers)

    # Parsing the HTML content of the article page:
    soup = BeautifulSoup(r.text, 'html.parser')

    # Finding all the paragraphs of the article and concatenating them:
    articles = soup.find('div', {'class': 'caas-body'}).find_all('p')
    paragraph = ''
    for p in articles:
        paragraph += p.text

    # Dictionary containing all the data we want:
    news = {
        'Date': soup.find('time')['datetime'],
        'article_title': article.find('a').text,  
        'article': paragraph,
        'source_name': 'Yahoo Finance',
        'source_link': link
    }

    # Global list allNews containing all the data about each article:
    allNews.append(news)
    return 

def sentimentsScores(df):
    # SentimentIntensityAnalyzer object:
    sentiments = SentimentIntensityAnalyzer()

    # Empty lists to store sentiment scores:
    positive_scores = []
    negative_scores = []
    neutral_scores = []
    compound_scores = []

    # Calculating the sentiment scores for each article in the df
    for article in df["article"]:
        scores = sentiments.polarity_scores(article)
        positive_scores.append(scores["pos"])
        negative_scores.append(scores["neg"])
        neutral_scores.append(scores["neu"])
        compound_scores.append(scores["compound"])

    # Assigning the lists to the df columns:
    df["Positive"] = positive_scores
    df["Negative"] = negative_scores
    df["Neutral"] = neutral_scores
    df["Compound"] = compound_scores

    # Labeling the sentiment (positive, neutral or negative) based on the compound score:
    score = df["Compound"].values
    sentiment = []
    for i in score:
        if i >= 0.05 :
            sentiment.append('Positive')
        elif i <= -0.05 :
            sentiment.append('Negative')
        else:
            sentiment.append('Neutral')
    df["Sentiment"] = sentiment
    return df


def preProcess(df):
    # Removing duplicates based on article title
    df.drop_duplicates(subset='article_title', keep='first', inplace=True)

    # Sorting DataFrame based on the 'Date' column in reverse order
    df= df.sort_values(by='Date', ascending=False)

    # Converting the 'Date' column to datetime format because errors='coerce' will turn invalid parsing to NaT
    df['Date'] = pd.to_datetime(df['Date'], errors='coerce')

    # Filtering out rows with valid dates (non-NaT)
    df= df.dropna(subset=['Date'])
    
    return df

def turnToCSV():
    """
    Converting the collected news data into a dataframe and then into a csv file,
    while handling duplicates and cleaning the data.
    """
    try:
        existing_data = pd.read_csv("News.csv")
    except FileNotFoundError:
        existing_data = pd.DataFrame()

    # Getting the sentiments score of the new extracted data
    new_data=sentimentsScores(pd.DataFrame(allNews))

    # Appending new data to existing DataFrame
    df = pd.concat([existing_data, new_data])

    # handling duplicates and cleaning the data:
    df=preProcess(df)

    # Turning the df into a csv file:
    df.to_csv("News.csv", index=False)

def main():
    """
    Making the program run x100 faster by using concurrent execution,
    to make the code fetch information from multiple news articles in parallel.
    """
    with concurrent.futures.ThreadPoolExecutor() as executor:
        executor.map(fetchNewsInfo,extractNews(openWebPage(url)))
    turnToCSV()
main()
