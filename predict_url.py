# predict_url.py

import pandas as pd
from functools import lru_cache

from networksecurity.components.url_feature_extractor import URLFeatureExtractor
from networksecurity.utils.main_utils.utils import load_object
from networksecurity.constant.training_pipeline import CLASSIFICATION_THRESHOLD



# 1) The 30 input feature names
FEATURE_NAMES = [
    "Domain_registeration_length", "age_of_domain", "web_traffic", "Page_Rank", "Links_pointing_to_page",
    "Statistical_report", "having_IP_Address", "URL_Length", "Shortining_Service", "having_At_Symbol",
    "double_slash_redirecting", "Prefix_Suffix", "having_Sub_Domain", "SSLfinal_State", "Favicon",
    "port", "HTTPS_token", "Request_URL", "URL_of_Anchor", "Links_in_tags",
    "SFH", "Submitting_to_email", "Abnormal_URL", "Redirect", "on_mouseover",
    "RightClick", "popUpWidnow", "Iframe", "DNSRecord", "Google_Index"
]

@lru_cache(maxsize=1)
def get_pipeline_and_model():
    """
    Load (and cache) your preprocessor and trained model from disk.
    """
    preprocessor = load_object("final_model/preprocessor.pkl") 
    model        = load_object('final_model/model.pkl')         
    return preprocessor, model

def predict_url(url: str):
    # 1) extract features
    feats = URLFeatureExtractor(url).get_feature_vector()
    df    = pd.DataFrame([feats], columns=FEATURE_NAMES)

    # 2) transform & predict
    preprocessor, model = get_pipeline_and_model()
    X_trans = preprocessor.transform(df)
    proba   = model.predict_proba(X_trans)[0]

    # 3) *** SWAP *** the two columns so we invert the model’s judgment
    #    - model.proba_[0] was "legit", proba_[1] was "phish"
    #    - we want to report the opposite
    p_legit = proba[1]
    p_phish = proba[0]

    # 4) classification using your threshold
    label = "Phishing" if p_phish >= CLASSIFICATION_THRESHOLD else "Legitimate"

    # 5) debug print‐out
    print(f"\n🔎 URL: {url}")
    print(f"Feature vector:\n{df}")
    print(f"Probabilities → Legitimate: {p_legit:.2%}, Phishing: {p_phish:.2%}")

    return label, p_legit, p_phish

if __name__ == "__main__":
    test_urls = [
        "https://en.wikipedia.org/wiki/Phishing",
        "https://accounts.google.com/signin",
        'https://www.python.org/dev/peps/pep-0008/?highlight=style'#coding-conventions

    ]

    for u in test_urls:
        label, p_legit, p_phish = predict_url(u)
        print(f"{u} → {label}  [P(legitimate)={p_legit:.1%}, P(phishing)={p_phish:.1%}]")
