import time
import requests

OLLAMA_URL = "http://127.0.0.1:11434"
MODEL_NAME = "pierce-county-records-classifier-phi2:latest"


def check_model_loaded() -> bool:
    """Return True if the model appears in /api/tags."""
    try:
        r = requests.get(f"{OLLAMA_URL}/api/tags", timeout=5)
        tags = r.json()  # ['model1:latest', 'model2:latest', ...]
        return any(MODEL_NAME in tag for tag in tags)
    except Exception as exc:
        print(f"[ERROR] Ollama tag check failed: {exc}")
        return False


def warm_up_model() -> bool:
    """Send a warm-up prompt to load the model."""
    try:
        payload = {
            "model": MODEL_NAME,
            "prompt": "Respond with: READY",
            "stream": False,
        }
        print(f"[INFO] Warming up model: {MODEL_NAME}...")
        resp = requests.post(
            f"{OLLAMA_URL}/api/generate", json=payload, timeout=60
        )
        if "READY" in resp.text:
            print("[SUCCESS] Ollama model is warm and ready.")
            return True
        print(f"[WARNING] Unexpected warm-up response: {resp.text}")
        return False
    except Exception as exc:
        print(f"[ERROR] Ollama warm-up failed: {exc}")
        return False


def ensure_model_ready(max_retries: int = 3, delay: int = 10) -> bool:
    """Ensure the model is pulled and warmed before continuing."""
    for attempt in range(max_retries):
        print(
            f"[INFO] Checking model load status (Attempt {attempt + 1}/{max_retries})..."
        )
        if check_model_loaded() and warm_up_model():
            return True
        time.sleep(delay)
    print("[FAIL] Ollama model failed to load after retries.")
    return False
