# Financial News Sentiment Analysis
A Python-based project that analyzes financial news headlines and predicts the overall sentiment for companies using NLP models.

[Live Demo](https://sentiment-analysis-eight-gamma.vercel.app/)

Try it out:
```
pip install -r requirements.txt
python run_analysis.py
```

## Motivation
In today’s fast-paced world, staying updated on financial news is crucial. Stock prices are heavily influenced by company headlines, but manually tracking this information is challenging

Years ago, I had the idea to use models to predict stock prices, but it didn’t work. I realized that a key factor influencing stock prices is the news headlines of the company.

That’s exactly why this project came to be – to give a clear picture of market sentiment by analyzing financial news headlines.

> You cannot predict the future.  -Stephen Hawking (*A Brief History of Time*)

## Features
- Automatically scrapes financial news articles.
- Stores articles and sentiment in a PostgreSQL database
- Use a pretrained model to classify headlines as positive, negative or neutral
- Use a custom model to do Named-entity recognition (NER) on companies

## Structure
- [scraper.py](https://github.com/KOlCIqwq/Sentiment-Analysis/blob/master/scraper.py): Scrapes news articles, inserts them into a PostgreSQL database, and triggers the Kaggle notebook.
- [financial-news-analyzer.ipynb](https://github.com/KOlCIqwq/Sentiment-Analysis/blob/master/financial-news-analyzer.ipynb): Runs the models on Kaggle and inserts the results into the same PostgreSQL database.
- [kaggle.ipynb](https://github.com/KOlCIqwq/Sentiment-Analysis/blob/master/kaggle.ipynb): File used to fine-tune the model
- [api/index.py](https://github.com/KOlCIqwq/Sentiment-Analysis/blob/master/api/index.py): Flask web application that serves the demo website and exposes API endpoints for retrieving articles and sentiment summaries from the database
- [public/index.html](https://github.com/KOlCIqwq/Sentiment-Analysis/blob/master/public/index.html): HTML page for the demo site.

## Models
- Based on DistilBERT, fine-tuned for financial news sentiment classification.
- You can find the sentiment model [here](https://huggingface.co/KOlCi/distilbert-financial-sentiment)

