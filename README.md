GITHUB_TOKEN=______
GITHUB_OWNER=SasiNikhil
GITHUB_REPO=issues-gw-demo
WEBHOOK_SECRET=mysecret123 
PORT=8080
LOG_LEVEL=INFO

# run locally non-docker
python -m venv .venv
# Win: .\.venv\Scripts\Activate.ps1  |  Mac/Linux: source .venv/bin/activate
pip install -r requirements.txt
python -m uvicorn app.main:app --host 0.0.0.0 --port 8080 --reload

# run using docker
# start Docker Desktop
Start-Process "C:\Program Files\Docker\Docker\Docker Desktop.exe"
docker version          # should show both Client and Server
wsl -l -v               # should include 'docker-desktop' and 'docker-desktop-data' (VERSION 2)
Set-Location "C:\Users\SASI NIKHIL\Downloads\issues-gw-full\issues-gw"
docker build -t issues-gw:latest .
docker run --rm -p 8080:8080 --env-file .\.env issues-gw:latest
 
Links: http://127.0.0.1:8080/healthz,  http://127.0.0.1:8080/docs

HTTPie commands
Healthz - http GET :8080/healthz
Create issue - http POST :8080/issues Content-Type:application/json \
  "{ \"title\": \"Bug: crash on save\", \"body\": \"Steps to reproduce...\", \"labels\": [\"bug\",\"p1\"] }"
List Issues - http GET :8080/issues state==open page==1 per_page==2
Get issue by number - Get issue by number
Update issue (close / reopen) - Update issue (close / reopen)
Add a comment - http POST :8080/issues/NUMBER/comments body="Thanks for reporting this!"




