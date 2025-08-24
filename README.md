# Financial News Sentiment Analysis
A Python-based project that analyzes financial news headlines and predicts the overall sentiment for companies using NLP models.

[Live Demo](https://sentiment-analysis-jzlt.onrender.com/)

Try it out:
```
pip install -r requirements.txt
python run_analysis.py
```

## Motivation
In today’s fast-paced world, staying updated on financial news is crucial. Stock prices are heavily influenced by company headlines, but manually tracking this information is challenging.

Years ago, I had the idea to use models to predict stock prices, but it didn’t work. I realized that a key factor influencing stock prices is the news headlines of the company.

This project was born to provide an overall sentiment of the market based on its financial news headlines.

## Features
- Automatically scrapes financial news articles.
- Stores articles and sentiment in a PostfreSQL database
- Use a pretrained model to classify headlines as positive, negative or neutral
- Use a custom model to do Named-entity recognition (NER) on companies

## Structure
- [scraper.py](https://github.com/KOlCIqwq/Sentiment-Analysis/blob/master/scraper.py): Scrapes news articles, inserts them into a PostgreSQL database, and triggers the Kaggle notebook.
- [kaggle.ipynb](https://github.com/KOlCIqwq/Sentiment-Analysis/blob/master/kaggle.ipynb): Runs the models on Kaggle and inserts the results into the same PostgreSQL database.
- [app.py](https://github.com/KOlCIqwq/Sentiment-Analysis/blob/master/app.py): Flask web application that serves the demo website and exposes API endpoints for retrieving articles and sentiment summaries from the database
- [templates/index.html](https://github.com/KOlCIqwq/Sentiment-Analysis/blob/master/templates/index.html): HTML page for the demo site.

## Models
- Based on DistilBERT, fine-tuned for financial news sentiment classification.
- You can find the sentiment model [here](https://huggingface.co/KOlCi/distilbert-financial-sentiment)

