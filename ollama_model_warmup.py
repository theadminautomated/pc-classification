import time
from pathlib import Path
import requests

OLLAMA_URL = "http://127.0.0.1:11434"
MODEL_NAME = "pierce-county-records-classifier-phi2:latest"


def warm_up_model() -> bool:
    """Send a warm-up prompt to load the model."""
    try:
        payload = {
            "model": MODEL_NAME,
            "prompt": "Respond with: READY",
            "stream": False,
        }
        print(f"[INFO] Warming up model: {MODEL_NAME}...")
        resp = requests.post(f"{OLLAMA_URL}/api/generate", json=payload, timeout=60)
        if "READY" in resp.text:
            print("[SUCCESS] Ollama model is warm and ready.")
            return True
        print(f"[WARNING] Unexpected warm-up response: {resp.text}")
        return False
    except Exception as exc:
        print(f"[ERROR] Ollama warm-up failed: {exc}")
        return False


def create_model() -> bool:
    """Attempt to create the model from the local Modelfile."""
    try:
        modelfile = Path("Modelfile-phi2")
        if not modelfile.exists():
            print(f"[ERROR] Modelfile not found: {modelfile}")
            return False
        payload = {
            "name": MODEL_NAME.split(":")[0],
            "modelfile": modelfile.read_text(encoding="utf-8"),
        }
        print(f"[INFO] Creating model {MODEL_NAME}...")
        resp = requests.post(f"{OLLAMA_URL}/api/create", json=payload, timeout=300)
        if resp.status_code == 200:
            print("[SUCCESS] Model created successfully.")
            return True
        print(f"[ERROR] Model creation failed: {resp.text}")
        return False
    except Exception as exc:
        print(f"[ERROR] Model creation exception: {exc}")
        return False


def ensure_model_ready(max_retries: int = 3, delay: int = 10) -> bool:
    """Create (if needed) and warm the model before continuing."""
    for attempt in range(max_retries):
        print(f"[INFO] Warming model (attempt {attempt + 1}/{max_retries})...")
        if warm_up_model():
            return True
        print("[INFO] Warm-up failed, attempting to create model...")
        create_model()
        time.sleep(delay)
    print("[FAIL] Ollama model failed to load after retries.")
    return False
