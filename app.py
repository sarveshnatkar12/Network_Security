import sys
import os
import re
import certifi
import pymongo
import pandas as pd

from dotenv import load_dotenv
from fastapi import FastAPI, Request, File, UploadFile, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response, RedirectResponse
from fastapi.templating import Jinja2Templates
from uvicorn import run as app_run

from networksecurity.exception.exception import NetworkSecurityException
from networksecurity.pipeline.training_pipeline import TrainingPipeline
from networksecurity.components.url_feature_extractor import URLFeatureExtractor
from networksecurity.constant.training_pipeline import CLASSIFICATION_THRESHOLD
from networksecurity.utils.main_utils.utils import load_object
from networksecurity.utils.ml_utils.model.estimator import NetworkModel

# ========== Load Environment ========== #
load_dotenv()
ca = certifi.where()
mongo_db_url = os.getenv("MONGODB_URL_KEY")

# ========== Mongo Setup ========== #
client = pymongo.MongoClient(mongo_db_url, tlsCAFile=ca)
from networksecurity.constant.training_pipeline import (
    DATA_INGESTION_DATABASE_NAME,
    DATA_INGESTION_COLLECTION_NAME
)
database = client[DATA_INGESTION_DATABASE_NAME]
collection = database[DATA_INGESTION_COLLECTION_NAME]

# ========== App Setup ========== #
app = FastAPI()
templates = Jinja2Templates(directory="./templates")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ========== Feature List ========== #
FEATURE_NAMES = [
    "Domain_registeration_length", "age_of_domain", "web_traffic", "Page_Rank", "Links_pointing_to_page",
    "Statistical_report", "having_IP_Address", "URL_Length", "Shortining_Service", "having_At_Symbol",
    "double_slash_redirecting", "Prefix_Suffix", "having_Sub_Domain", "SSLfinal_State", "Favicon",
    "port", "HTTPS_token", "Request_URL", "URL_of_Anchor", "Links_in_tags",
    "SFH", "Submitting_to_email", "Abnormal_URL", "Redirect", "on_mouseover",
    "RightClick", "popUpWidnow", "Iframe", "DNSRecord", "Google_Index"
]

# ========== Load Preprocessor and Model Once ========== #
preprocessor = load_object("final_model/preprocessor.pkl")
model = load_object("final_model/model.pkl")
network_model = NetworkModel(preprocessor=preprocessor, model=model)

# ====================== ROUTES ====================== #

@app.get("/", tags=["Landing"])
async def landing_page(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/check-url", tags=["Prediction UI"])
async def render_url_form(request: Request):
    return templates.TemplateResponse("url_form.html", {"request": request})

@app.get("/train", tags=["Training"])
async def train_route():
    try:
        tp = TrainingPipeline()
        tp.run_pipeline()
        return Response("Training is successful")
    except Exception as e:
        raise NetworkSecurityException(e, sys)

@app.post("/predict", tags=["CSV Upload Prediction"])
async def predict_file_route(request: Request, file: UploadFile = File(...)):
    try:
        df = pd.read_csv(file.file)
        y_pred = network_model.predict(df)
        df["predicted_column"] = y_pred
        df.to_csv("prediction_output/output.csv", index=False)

        table_html = df.to_html(classes="table table-striped", index=False)
        return templates.TemplateResponse(
            "table.html",
            {"request": request, "table": table_html}
        )
    except Exception as e:
        raise NetworkSecurityException(e, sys)
    

@app.get("/check-url-form")
async def check_url_form(request: Request):
    return templates.TemplateResponse("url_form.html", {"request": request})


@app.post("/predict-url", tags=["URL Prediction"])
async def post_url_form(request: Request, url: str = Form(...)):
    try:
        url_list = [u.strip() for u in re.split(r"[,\n]+", url) if u.strip()]
        results = []

        for u in url_list:
            feats = URLFeatureExtractor(u).get_feature_vector()
            df = pd.DataFrame([feats], columns=FEATURE_NAMES)

            X_trans = preprocessor.transform(df)
            proba = model.predict_proba(X_trans)[0]

            # Reverse class probabilities (as discussed earlier)
            p_legit = proba[1]
            p_phish = proba[0]
            label = "Phishing" if p_phish >= CLASSIFICATION_THRESHOLD else "Legitimate"

            results.append({
                "url": u,
                "label": label,
                "P_legit": f"{p_legit:.1%}",
                "P_phish": f"{p_phish:.1%}"
            })

        return templates.TemplateResponse(
            "url_form.html",
            {"request": request, "results": results}
        )
    except Exception as e:
        raise NetworkSecurityException(e, sys)

# ====================== START APP ====================== #
if __name__ == "__main__":
    app_run(app, host='0.0.0.0', port=8120)
