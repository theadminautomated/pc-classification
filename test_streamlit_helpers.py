from pathlib import Path
import tempfile
from streamlit_helpers import sanitize_filename, load_file_content

class DummyUpload:
    def __init__(self, name: str, data: bytes):
        self.name = name
        self._data = data
    def read(self):
        return self._data


def test_sanitize_filename():
    assert sanitize_filename('..\\evil.txt') == 'evil.txt'


def test_load_file_content(tmp_path: Path):
    dummy = DummyUpload('demo.txt', b'hi')
    # simulate session state
    import streamlit as st
    st.session_state['temp_dir'] = str(tmp_path)
    path = load_file_content(dummy)
    assert path is not None
    assert path.read_bytes() == b'hi'
