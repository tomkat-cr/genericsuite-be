"""
Tests for genericsuite/util/parse_multipart.py — download_file and helpers.
"""
import sys
import os
from unittest.mock import MagicMock, patch


def _ensure_mocks():
    # framework_abs_layer mock needs Request/Response to be real classes
    # (not MagicMock instances) so that typing.Callable type hints work.
    if "genericsuite.util.framework_abs_layer" not in sys.modules:
        fw_mock = MagicMock()
        fw_mock.Request = MagicMock
        fw_mock.Response = MagicMock
        fw_mock.BlueprintOne = MagicMock
        sys.modules["genericsuite.util.framework_abs_layer"] = fw_mock
    sys.modules.setdefault("genericsuite.util.app_logger", MagicMock())
    # Mock app_context to avoid pulling in the full jwt chain
    sys.modules.setdefault("genericsuite.util.app_context", MagicMock())
    sys.modules.setdefault("requests_toolbelt", MagicMock())
    sys.modules.setdefault("requests_toolbelt.multipart", MagicMock())
    sys.modules.setdefault("requests_toolbelt.multipart.decoder", MagicMock())


def _fresh_parse_multipart():
    _ensure_mocks()
    for mod in list(sys.modules):
        if mod == "genericsuite.util.parse_multipart":
            del sys.modules[mod]
    import genericsuite.util.parse_multipart as m
    return m


# ---- download_file ----

def test_download_file_creates_file_with_content(tmp_path):
    m = _fresh_parse_multipart()
    with patch("genericsuite.util.parse_multipart.temp_filename",
               return_value=str(tmp_path / "upload.txt")):
        file_path = m.download_file(b"hello world", "txt")
    assert os.path.exists(file_path)
    with open(file_path, "rb") as f:
        content = f.read()
    assert content == b"hello world"


def test_download_file_returns_file_path(tmp_path):
    m = _fresh_parse_multipart()
    expected_path = str(tmp_path / "myfile.jpg")
    with patch("genericsuite.util.parse_multipart.temp_filename",
               return_value=expected_path):
        result = m.download_file(b"\xff\xd8\xff", "jpg")
    assert result == expected_path


def test_download_file_empty_bytes(tmp_path):
    m = _fresh_parse_multipart()
    with patch("genericsuite.util.parse_multipart.temp_filename",
               return_value=str(tmp_path / "empty.bin")):
        file_path = m.download_file(b"", "bin")
    assert os.path.exists(file_path)
    assert os.path.getsize(file_path) == 0


def test_download_file_no_extension(tmp_path):
    m = _fresh_parse_multipart()
    with patch("genericsuite.util.parse_multipart.temp_filename",
               return_value=str(tmp_path / "noext")):
        file_path = m.download_file(b"data", None)
    assert os.path.exists(file_path)


# ---- parse_multipart (basic) ----

def test_parse_multipart_calls_decoder():
    m = _fresh_parse_multipart()
    MultipartDecoder = MagicMock()
    fake_part = MagicMock()
    fake_part.headers = {
        b"Content-Disposition": b'form-data; name="file"; filename="test.txt"'
    }
    fake_part.content = b"test content"
    fake_part.encoding = "utf-8"
    MultipartDecoder.return_value.parts = [fake_part]
    with patch("genericsuite.util.parse_multipart.MultipartDecoder", MultipartDecoder):
        result = m.parse_multipart(b"raw_body", {"content-type": "multipart/form-data"})
    assert "parts" in result
    assert len(result["parts"]) == 1


def test_parse_multipart_injects_boundary_for_bare_multipart():
    m = _fresh_parse_multipart()
    MultipartDecoder = MagicMock()
    MultipartDecoder.return_value.parts = []
    with patch("genericsuite.util.parse_multipart.MultipartDecoder", MultipartDecoder):
        m.parse_multipart(b"body", {"content-type": "multipart/form-data"})
    # Verify boundary was appended
    call_args = MultipartDecoder.call_args
    assert "boundary" in call_args[0][1]


def test_parse_multipart_part_without_content_type():
    m = _fresh_parse_multipart()
    fake_part = MagicMock()
    fake_part.headers = {
        b"Content-Disposition": b'form-data; name="field"'
    }
    fake_part.content = b"value"
    fake_part.encoding = "utf-8"
    MultipartDecoder = MagicMock()
    MultipartDecoder.return_value.parts = [fake_part]
    with patch("genericsuite.util.parse_multipart.MultipartDecoder", MultipartDecoder):
        result = m.parse_multipart(b"body", {"content-type": "text/plain"})
    assert result["parts"][0]["type"] is None
