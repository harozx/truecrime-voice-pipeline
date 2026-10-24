"""Test các phần không cần mạng: cấu hình, xoay vòng API key, xử lý SRT"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import config  # noqa: E402
from api_key_manager import APIKeyManager  # noqa: E402


def test_relative_paths_resolve_from_project_dir():
    assert os.path.isabs(config.OUTPUT_DIR)
    assert config.TRUYEN_INPUT_DIR.endswith(os.path.join('data', 'input_mp3'))
    assert config.PROCESSED_STORIES_DIR.startswith(config.TRUYEN_DIR)


def test_key_manager_reads_file_skips_comments_and_rotates(tmp_path, monkeypatch):
    monkeypatch.delenv('GEMINI_API_KEY', raising=False)
    keys_file = tmp_path / 'api_keys.txt'
    keys_file.write_text('# comment\nAIzaFIRST\n\nnot-a-key\nAIzaSECOND.\n', encoding='utf-8')

    manager = APIKeyManager(str(keys_file))

    assert manager.keys == ['AIzaFIRST', 'AIzaSECOND']
    assert [manager.get_next_key() for _ in range(3)] == ['AIzaFIRST', 'AIzaSECOND', 'AIzaFIRST']


def test_key_manager_uses_env_keys_without_duplicates(tmp_path, monkeypatch):
    monkeypatch.setenv('GEMINI_API_KEY', 'AIzaENV1, AIzaENV2')
    keys_file = tmp_path / 'api_keys.txt'
    keys_file.write_text('AIzaENV1\nAIzaFILE\n', encoding='utf-8')

    manager = APIKeyManager(str(keys_file))

    assert manager.keys == ['AIzaENV1', 'AIzaENV2', 'AIzaFILE']


def test_key_manager_without_keys_returns_none(tmp_path, monkeypatch):
    monkeypatch.delenv('GEMINI_API_KEY', raising=False)
    manager = APIKeyManager(str(tmp_path / 'missing.txt'))
    assert manager.get_next_key() is None


def test_srt_helpers():
    from auto_processor import format_time, split_srt_content

    assert format_time(3725.5) == '01:02:05,500'

    srt = '\n\n'.join(f'{i}\n00:00:0{i},000 --> 00:00:0{i},500\nline {i}' for i in range(1, 6))
    chunks = split_srt_content(srt, max_lines=2)
    assert len(chunks) == 3
    assert chunks[-1].startswith('5\n')
