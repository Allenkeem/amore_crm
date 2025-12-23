# Amore Agent Project

AI-powered CRM Message Builder using FastAPI and Streamlit.

## 🚀 Quick Start (Docker)

You can run the entire system (Frontend + Backend) with a single command using Docker.

### Prerequisites
- Docker & Docker Compose installed

### How to Run
1. Open your terminal in this directory.
2. Run the following command:
   ```bash
   docker-compose up --build
   ```
   *(Add `-d` to run in background: `docker-compose up --build -d`)*

3. Docker will build the images and start the services.
   - **Frontend**: [http://localhost:8501](http://localhost:8501)
   - **Backend**: [http://localhost:8000/docs](http://localhost:8000/docs) (Swagger UI)

### How to Stop
Press `Ctrl+C` in the terminal (if running in foreground) or run:
```bash
docker-compose down
```

## 🛠 Manual Run (Without Docker)

If you prefer running services individually:

1. **Backend**:
   ```bash
   cd backend
   pip install -r requirements.txt
   python main.py
   ```

2. **Frontend**:
   ```bash
   cd frontend
   pip install -r requirements.txt
   streamlit run app.py
   ```
