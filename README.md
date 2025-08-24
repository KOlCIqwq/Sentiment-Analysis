# Financial News Sentiment Analysis
This project leverages several models to give a sentiment on financial news articles

[Demo Site](https://sentiment-analysis-jzlt.onrender.com/)
Try it out:
```
pip install -r requirements.txt
python run_analysis.py
```

## Motivation
Living in a fast track society, there's gonna be things that you'll be missing. One of them is, and very important one, is about the financials
Years ago I had the idea to use models to predict the stock prices, but it failed miserably. But I realized a key factor that influence the price
and that is the news headlines of the company. 
Then this project is born, to give an overall sentiment of the company based on the financial news headlines.

## Structure
- [scraper.py](https://github.com/KOlCIqwq/Sentiment-Analysis/blob/master/scraper.py): Scrapes the news, insert them into postgres database, and trigger the kaggle notebook
- [kaggle.py](https://github.com/KOlCIqwq/Sentiment-Analysis/blob/master/kaggle.ipynb): Runs the models on Kaggle, and insert the results on the same postgres
- [app.py](https://github.com/KOlCIqwq/Sentiment-Analysis/blob/master/app.py): Provides functions to render on site
- [templates/index.html](https://github.com/KOlCIqwq/Sentiment-Analysis/blob/master/templates/index.html): Html page for the demo site

## Models
You can find the sentiment model [here](https://huggingface.co/KOlCi/distilbert-financial-sentiment)

