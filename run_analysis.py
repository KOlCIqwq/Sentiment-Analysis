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
    score = str(f"{score:.4f}")
    sentiment = sentiment + "Confidence: " + score

    # Display the results
    print("-" * 20)
    #print(f"Sentiment: {sentiment} (Score: {score:.4f})")
    print(sentiment)
    
    if companies:
        print(f"Companies Found: {', '.join(companies)}")
    else:
        print("Companies Found: None")
    print("="*50)


if __name__ == "__main__":

    headline = input("Insert the headline to analyze:")
    analyze_text(headline)

    """ # Test sentences to analyze
    test_sentences = [
    ]

    for sentence in test_sentences:
        analyze_text(sentence) """


