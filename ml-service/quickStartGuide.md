# Quick Start Guide: AdaptiQ ML Service & Web Setup

This guide provides step-by-step instructions to get the platform (both the React Frontend and the ML Service) up and running after cloning the repository.

---

## 🏗️ 1. Setup the ML Backend Service

Open a new terminal window and navigate to the ML service folder:
```powershell
cd ml-service
```

### A. Create and Activate Virtual Environment
Create a clean Python environment to avoid dependency conflicts:
```powershell
python -m venv venv
```
Activate it:
* **Windows (PowerShell):** `.\venv\Scripts\Activate.ps1`
* **Windows (Command Prompt):** `.\venv\Scripts\activate.bat`
* **Mac/Linux:** `source venv/bin/activate`

*(You should see `(venv)` appear in your terminal prompt)*

### B. Install Dependencies
```powershell
pip install -r requirements.txt
```

### C. Verify / Train Models
Check if models exist in the `models/` directory:
```powershell
Get-ChildItem .\models\*.pkl   # Windows
# or
ls ./models/*.pkl              # Mac/Linux
```
If you don't see `difficulty_model.pkl`, `ranking_model.pkl`, and `skill_gap_model.pkl`, you need to train them first:
```powershell
python training/generate_data.py
python training/train_all.py
```

### D. Start the ML Service
```powershell
uvicorn app.main:app --host 0.0.0.0 --port 8000
```
> **Leave this terminal open!** The ML service must stay running in the background.

---

## 🎨 2. Setup the React Frontend

Open a **second** new terminal window and navigate to the project root (where `package.json` is located - typically one folder up from `ml-service`):

### A. Install Node Dependencies
```powershell
npm install
```

### B. Start the Development Server
```powershell
npm run dev
```

The terminal will provide a local URL (usually `http://localhost:5173/`). Hold `Ctrl` and click the link to open the app in your browser.

---

## 🧪 3. Testing the Integration

To verify everything is connected correctly:
1. Go to the `Quiz` section on the website.
2. Complete a quiz session.
3. At the end, you'll see a Feedback modal. Fill it out and submit.
4. On the `Results` dashboard, look for the **AdaptiQ Engine Insights 🧠** panel. If it loads with personalized AI metrics (Skill Gap, Recommended Action), the integration is successful!

---

## 🔧 Troubleshooting

| Issue | Solution |
| :--- | :--- |
| `uvicorn: The term 'uvicorn' is not recognized` | Ensure you have activated your virtual environment (`.\venv\Scripts\Activate.ps1`) before running the command. |
| `ModuleNotFoundError` | Make sure you're in the `ml-service` folder and `venv` is activated before running python files. |
| `Port 8000 in use` | Change the backend port: `uvicorn app.main:app --port 8001`, and update `VITE_ML_API_URL` in your frontend `.env` file. |
| ML Insights fail to load on frontend | Ensure the FastAPI terminal (running `uvicorn`) is still open and running without errors. Check the Network tab in your browser's Developer Tools. |