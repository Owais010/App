Step 1: Navigate to ML Service Directory
cd c:\Users\anilr\pathfinder-learn\ml-service
Step 2: Create Virtual Environment
python -m venv venv
Step 3: Activate Virtual Environment
.\venv\Scripts\Activate.ps1
You should see (venv) appear in your terminal prompt
Step 4: Install Dependencies
pip install -r requirements.txt
Step 5: Verify Models Exist
Get-ChildItem .\models\*.pkl
Should show 3 model files: difficulty_model.pkl, ranking_model.pkl, skill_gap_model.pkl

If models are missing, train them:
python training/generate_data.py
python training/train_all.py
Step 6: Start the ML Service
uvicorn app.main:app --host 0.0.0.0 --port 8000
Keep this terminal open - the service runs here
Step 7: Test the Service (Open New Terminal)
Health Check:
Invoke-RestMethod -Uri "http://localhost:8000/health"
Expected output:
status        models_loaded version
------        ------------- -------
healthy       True          1.0.0
Test Prediction:
$json = '{"user_id":"test","topic_id":"math","attempt_count":10,"correct_attempts":7,"avg_response_time":20,"self_confidence_rating":0.7,"difficulty_feedback":3,"session_duration":30,"previous_mastery_score":0.5,"time_since_last_attempt":24}'

Invoke-RestMethod -Uri "http://localhost:8000/predict" -Method Post -Body $json -ContentType "application/json"
Step 8: Access API Documentation
Open browser and go to:

Swagger UI: http://localhost:8000/docs
ReDoc: http://localhost:8000/redoc
Step 9: Stop the Service
Press Ctrl + C in the terminal running uvicorn

Quick Copy-Paste (All Commands)
# Run these in sequence
cd c:\Users\anilr\pathfinder-learn\ml-service
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8000
API Endpoints Summary
Endpoint	Method	Description
/health	GET	Check if service is running
/predict	POST	Get ML predictions
/metrics	GET	Prometheus metrics
/docs	GET	Interactive API docs
Troubleshooting
Issue	Solution
ModuleNotFoundError	Make sure you're in ml-service folder and venv is activated
Port 8000 in use	Use --port 8001 instead
Models not found	Run python training/train_all.py