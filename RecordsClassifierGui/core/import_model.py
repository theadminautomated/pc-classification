"""
core.import_model - Model import logic for Records Classifier
"""

import os
import sys
import time
from pathlib import Path
from typing import Optional, Tuple
import ollama

def verify_model(m: str) -> Tuple[bool, str]:
    """Verify model is available locally."""
    try:
        # Check if model exists in local storage first
        models = ollama.list()
        models_data = models.get('models', [])
        model_names = [model.get('name', '') for model in models_data]
        if any(m in name for name in model_names):
            return True, "Model found in local storage"

        # Model not found, look for model files
        # Get base directory
        if getattr(sys, 'frozen', False):
            # Running as EXE
            base_dir = Path(sys.executable).parent
        else:
            # Running as script
            base_dir = Path(__file__).parent.parent.parent
            
        # Check bundled model directory
        bundled_dir = base_dir / "models"
        if bundled_dir.exists():
            modelfile = bundled_dir / "Modelfile-phi2"
            if modelfile.exists():
                try:
                    with open(modelfile, 'r') as f:
                        modelfile_content = f.read()
                    ollama.create(model=m, modelfile=modelfile_content)
                    return True, "Model created successfully from bundled files"
                except Exception as e:
                    return False, f"Failed to create model: {str(e)}"
                    
        # Model files not found
        return False, "Model not found and model files not available"
    except Exception as e:
        return False, str(e)

def import_model(m: str = "pierce-county-records-classifier-phi2:latest") -> bool:
    """Import model from bundled files if needed."""
    success, _ = verify_model(m)
    if success:
        return True
        
    # Model not available, check user dir
    user_home = Path.home()
    ollama_dir = user_home / ".ollama" / "models"
    
    if (ollama_dir / "Modelfile-phi2").exists():
        try:
            with open(ollama_dir / "Modelfile-phi2", 'r') as f:
                modelfile_content = f.read()
            ollama.create(model=m, modelfile=modelfile_content)
            return True
        except Exception:
            pass
            
    # Try one more time with verify_model to handle any race conditions
    success, _ = verify_model(m)
    return success

if __name__ == '__main__':
    model = sys.argv[1] if len(sys.argv) > 1 else "pierce-county-records-classifier-phi2:latest"
    sys.exit(0 if import_model(model) else 1)
