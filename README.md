# JusticeGraph API ⚖️

A minimal, production-ready ML API for predicting court backlogs and case duration.

## 🚀 How to Run Locally

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Start the Server
```bash
uvicorn justice_graph.api.main:app --reload
```
The API will be live at `http://127.0.0.1:8000`.

## 📡 Endpoints

| Endpoint | Method | Description |
|---|---|---|
| `/predict/backlog` | POST | Predicts risk level based on court stats. |
| `/predict/duration` | POST | Estimates case duration based on case details. |
| `/predict/district-backlog` | POST | Returns estimated duration for a specific district (Karnataka). |

## ☁️ How to Deploy on Render

This project is configured for easy deployment on [Render](https://render.com).

### Option 1: Automatic (Recommended)
1. Push this code to a GitHub/GitLab repository.
2. In Render dashboard, click **"New + "** -> **"Blueprint"**.
3. Connect your repository.
4. Render will automatically detect `render.yaml` and configure the service.
5. Click **Apply**.

### Option 2: Manual Setup
1. Create a new **Web Service** on Render.
2. Connect your repository.
3. Use the following settings:
   - **Runtime**: Python 3
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn justice_graph.api.main:app --host 0.0.0.0 --port 10000`
4. Click **Create Web Service**.

That's it! Your API will be live in minutes.
