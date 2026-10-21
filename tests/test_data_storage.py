import json
import pytest
from storage import read_json, write_json

def test_atomic_json_roundtrip(tmp_path):
    p=tmp_path/'records.json';write_json(p,[{'id':'one'},{'id':'two'}])
    assert read_json(p)==[{'id':'one'},{'id':'two'}]

def test_malformed_json_is_reported(tmp_path):
    p=tmp_path/'bad.json';p.write_text('{oops',encoding='utf-8')
    with pytest.raises(ValueError,match='Invalid JSON'):read_json(p)
