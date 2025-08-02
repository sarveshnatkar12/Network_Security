# 🌐 Network Security: Phishing URL Detection using Machine Learning  
[🚀 Deployed App](https://phishingapp.duckdns.org/)

---

## 🔒 Project Overview

Phishing attacks trick users into revealing sensitive information by disguising malicious websites as trustworthy ones. This project uses Machine Learning to detect phishing URLs based on 30+ extracted features. The goal is to classify URLs as **Legitimate** or **Phishing** using a trained ML model.

Users can:
- Upload a CSV of URLs for bulk predictions.
- Trigger model training directly from the web UI.
- Deploy the pipeline via CI/CD to AWS EC2 with Docker + GitHub Actions.

---

## ✅ Features

- 📥 **MongoDB-based data ingestion**
- 🧪 **Validation**: Schema checks + Data drift detection
- 🔁 **Transformation**: Missing value imputation with KNN
- 🤖 **Modeling**: Random Forest (F1 ≈ 0.97), GridSearchCV + CalibratedClassifierCV
- 📈 **Evaluation**: Precision, Recall, F1 Score
- 📦 **MLflow + DagsHub tracking**
- 🧪 **FastAPI backend** with `/train` and `/predict`
- 🚢 **Dockerized**, deployed to **EC2** via **GitHub Actions**
- 🌍 **Free custom domain** via [DuckDNS](https://duckdns.org)

---

## ⚙️ Tech Stack

| Tool/Tech          | Purpose                          |
|--------------------|----------------------------------|
| Python 3.10        | Core Programming Language        |
| FastAPI            | Web Framework                    |
| Docker             | Containerization                 |
| GitHub Actions     | CI/CD Pipeline                   |
| AWS EC2, ECR, S3   | Cloud Hosting & Deployment       |
| MongoDB Atlas      | Cloud Database                   |
| Scikit-learn       | ML Modeling & Preprocessing      |
| MLflow + DagsHub   | Experiment Tracking              |
| DuckDNS            | Free HTTPS domain for EC2        |

---

## 🧪 How It Works

### 🧬 Pipeline Steps:
1. **Ingestion**: Pull data from MongoDB Atlas → Store locally → Split train/test
2. **Validation**: Schema check + Drift detection (KS-Test)
3. **Transformation**: KNNImputer for missing values → Save `.npy` and preprocessor
4. **Model Training**: Train/tune models → Pick best → Save + Log to MLflow/DagsHub
5. **Sync to S3**: Artifacts + final model are pushed to an S3 bucket
6. **Serve with FastAPI**: `/train` and `/predict` endpoints
7. **Deploy with GitHub Actions**: Builds + pushes Docker image → Pulls & runs on EC2

---

## 🔁 Web App Endpoints

| Endpoint      | Method | Description                     |
|---------------|--------|---------------------------------|
| `/`           | GET    | Homepage with UI buttons        |
| `/train`      | GET    | Triggers full ML pipeline       |
| `/predict`    | POST   | Accepts CSV of URLs and predicts |
| `/ping`       | GET    | Health check (optional)         |

---

## 🚀 Deployment

### 🔧 Local Docker Build & Run
```bash
docker build -t phishingapp-local .
docker run -d -p 8120:8120 --name phishingapp-local phishingapp-local:latest

☁️ Cloud Deployment (CI/CD)
Create AWS EC2 instance + ECR + S3

Configure GitHub Secrets:

AWS_ACCESS_KEY_ID

AWS_SECRET_ACCESS_KEY

AWS_REGION

ECR_REPOSITORY_NAME

AWS_ECR_REPOSITORY_URL

Push code to GitHub and manually trigger the workflow.

App will be auto-deployed to EC2.

🌐 Free Domain (HTTPS Optional)
Using DuckDNS:

Chose: phishingapp.duckdns.org (linked to EC2 public IP)

Configured via NGINX for proxy to port 8120

🔍 Example Prediction Flow
Go to phishingapp.duckdns.org

Upload phisingData.csv

Click Predict

Get results in styled table with output saved

📊 Sample Input Features
30 features like:

having_IP_Address, URL_Length, Shortining_Service

SSLfinal_State, Domain_registeration_length

Google_Index, Links_pointing_to_page

and more...

Target: Result (1 = Phishing, -1 = Legitimate)

🙋‍♂️ Author
Sarvesh Natkar
📫 LinkedIn
🧠 Passionate about ML, cloud, and secure web deployments.

🧠 Final Note
This project showcases an end-to-end ML pipeline that connects data collection, processing, modeling, and real-time deployment into a single, scalable solution — built for interviews, portfolios, and real-world ML applications.


