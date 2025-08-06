import spacy
from transformers import pipeline
import torch

NER_MODEL_PATH = "output/model-best"

SENTIMENT_MODEL_NAME = "KOlCi/distilbert-financial-sentiment"

print("Loading models... This might take a moment.")

# Load the custom SpaCy NER model
try:
    nlp_ner = spacy.load(NER_MODEL_PATH)
    print(f"NER model loaded")
except OSError:
    print(f"Could not load SpaCy model.")
    exit()

device = 0 if torch.cuda.is_available() else -1 # Use GPU if available, otherwise CPU
try:
    sentiment_pipeline = pipeline(
        "sentiment-analysis",
        model=SENTIMENT_MODEL_NAME,
        device=device
    )
    print(f"sentiment model loaded")
except Exception as e:
    print(f"Could not load model.")
    print(f"e")
    exit()


def analyze_text(text: str):
    """
    Runs a line of text through both the NER and sentiment models.
    """
    print("\n" + "="*50)
    print(f"Analyzing text: '{text}'")

    ner_doc = nlp_ner(text)
    companies = [ent.text for ent in ner_doc.ents]
    sentiment_result = sentiment_pipeline(text)
    sentiment = sentiment_result[0]['label'].upper()
    score = sentiment_result[0]['score']

    # Display the results
    print("-" * 20)
    print(f"Sentiment: {sentiment} (Score: {score:.4f})")
    #print(companies)
    
    if companies:
        print(f"Companies Found: {', '.join(companies)}")
    else:
        print("Companies Found: None")
    print("="*50)


if __name__ == "__main__":
    # Test sentences to analyze
    test_sentences = [
        "Apple announced a record-breaking quarter, with iPhone sales surging past expectations.",
        "Regulators are launching a full-scale investigation into a data breach at Meta Platforms.",
        "Despite market volatility, Microsoft's cloud division showed steady growth.",
        "The new electric vehicle from Tesla received mixed reviews from early testers.",
        "HSBC will close another 25 branches by the end of the year.",
        "Trump to put additional 25% import taxes on India, bringing combined tariffs to 50%",
        "Trump will highlight Apple’s plans to invest $100 billion more in US, raising total to $600 billion",
        "Wall Street holds steady following mixed profit reports from McDonald’s, Disney and Shopify",
        "AMD stock slumps 5% on earnings miss, China AI chip concerns",
        "Gold News: Treasury Yields Pressure Gold, but Fed Rate Cut Bets Offer Support",
        "DIS: Disney Stock Slides Despite Earnings Beat, Doubled Profit — It’s the TV and Theatrical Units"
    ]

    for sentence in test_sentences:
        analyze_text(sentence)