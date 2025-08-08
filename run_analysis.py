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
        "AAPL stock raises by 5%"
        ,"AAPL stock surges by 5%"
        ,"Cicciogamer Ltd. gained 10% of its portofolio value"
        ,"Bitcoin hits 118k, a new all time high!"
        ,"U.S. startup Lyten acquires most of bankrupt Northvolt, including projects in Sweden, Germany & Poland. Backed by Stellantis & FedEx, Lyten plans to restart Northvolt's Skelleftea plant & resume battery deliveries by 2026. Ex-Northvolt execs join Lyten, excluding the founder."
        ,"Firefly Aerospace's IPO priced at $45/share, valuing it at $6.32B, with shares set to open up to 22% higher. The company raised $868.3M, surpassing competitors, & eyes a role in missile defense. Despite past challenges, Firefly has expanded into spacecraft & lunar services."
        ,"Bitcoin & crypto assets may soon be included in 401(k) plans as President Trump plans to sign an executive order, boosting market sentiment. Bitcoin rose 1% to $116K, Ether up 4%. Crypto stocks surged premarket. Fidelity explores bitcoin 401(k) options amid low employer adoption."
        ,"Intel CEO Lip-Bu Tan is addressing concerns with the U.S. administration after President Trump demanded his resignation due to alleged conflicts tied to Chinese firms, casting doubt on Intel's turnaround plans. Tan is working to ensure the administration receives accurate information."
        ,"METAMeta partners with PIMCO & Blue Owl Capital for a $29B financing to expand data centers in Louisiana, with PIMCO managing $26B in debt & Blue Owl contributing $3B equity. Part of Meta's AI strategy, the plan includes offloading $2B in assets & major spending on AI facilities."
        ,"AKAMAkamai Technologies raises its annual revenue & profit forecast due to strong demand for cloud services & security solutions. New revenue expectations are $4.14B-$4.21B, with adjusted EPS of $6.60-$6.80. Q2 revenue hit $1.04B, beating analysts' $1.02B estimate."
        ,"OpenAI launches GPT-5 for 700M ChatGPT users, targeting enterprise needs in software, finance, writing & health. Despite scaling challenges, GPT-5 offers test-time compute for complex tasks. OpenAI eyes $500B valuation amid major tech investments. Reviewers see modest upgrade."
    ]

    for sentence in test_sentences:
        analyze_text(sentence)
