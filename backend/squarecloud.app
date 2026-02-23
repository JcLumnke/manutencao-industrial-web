{
  "name": "manutencao-backend",
  "platform": "python",
  "python_version": "3.11",
  "build_command": "pip install -r backend/requirements.txt",
  "start_command": "uvicorn backend.main:app --host 0.0.0.0 --port $PORT",
  "env": {
    "PYTHONUNBUFFERED": "1"
  }
}
