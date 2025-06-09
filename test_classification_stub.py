import tempfile
import os
import datetime
from pathlib import Path
from RecordsClassifierGui.logic.classification_engine_fixed import ClassificationEngine

def test_classify_file_stub():
    engine = ClassificationEngine(timeout_seconds=1)
    with tempfile.NamedTemporaryFile('w', suffix='.txt', delete=False) as tf:
        tf.write('sample text')
        path = Path(tf.name)
    try:
        result = engine.classify_file(path)
        assert result.model_determination in {'TRANSITORY', 'DESTROY', 'KEEP'}
        assert result.status
    finally:
        path.unlink(missing_ok=True)


def test_last_modified_mode_auto_destroy(tmp_path):
    engine = ClassificationEngine(timeout_seconds=1)
    file_path = tmp_path / "old.txt"
    file_path.write_text("old content")
    old_time = (datetime.datetime.now() - datetime.timedelta(days=6 * 365 + 1)).timestamp()
    os.utime(file_path, (old_time, old_time))
    result = engine.classify_file(file_path, run_mode="Last Modified")
    assert result.model_determination == "DESTROY"
