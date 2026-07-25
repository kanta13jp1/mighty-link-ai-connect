# -*- coding: utf-8 -*-
"""
tests/test_training_modal_ui.py
WBS: T919
役割別研修・オンボーディングインタラクティブガイドUIの自動テスト
index.html および src/index.html の構造、リンク、言語キー、ミラー同一性を検証する。
"""

import os
import pytest

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INDEX_PATH = os.path.join(REPO_ROOT, "index.html")
SRC_INDEX_PATH = os.path.join(REPO_ROOT, "src", "index.html")


def read_file(path: str) -> str:
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def test_index_and_src_index_mirror_identity():
    """index.html と src/index.html が完全に一致することを確認"""
    content_root = read_file(INDEX_PATH)
    content_src = read_file(SRC_INDEX_PATH)
    assert content_root == content_src, "index.html and src/index.html must be identical"


def test_training_modal_structure():
    """研修ガイドモーダルのHTML要素・構造が存在することを確認"""
    content = read_file(INDEX_PATH)
    assert 'id="training-modal"' in content
    assert 'id="training-modal-title"' in content
    assert 'id="training-tab-1"' in content
    assert 'id="training-tab-2"' in content
    assert 'id="training-tab-3"' in content
    assert 'id="training-course-1"' in content
    assert 'id="training-course-2"' in content
    assert 'id="training-course-3"' in content
    assert 'openTrainingModal' in content
    assert 'closeTrainingModal' in content
    assert 'switchTrainingTab' in content
    assert 'toggleTrainingCourseProgress' in content


def test_training_handbook_links_in_modal():
    """研修ハンドブック（docs/training/）へのリンクが存在することを確認"""
    content = read_file(INDEX_PATH)
    assert 'FOUNDATION_TRAINING_HANDBOOK.md' in content
    assert 'SALES_HR_TRAINING_HANDBOOK.md' in content
    assert 'ADMIN_MANAGEMENT_TRAINING_HANDBOOK.md' in content


def test_training_i18n_keys():
    """研修ガイド用i18n辞書キー（nav_training, training_modal_title等）が存在することを確認"""
    content = read_file(INDEX_PATH)
    assert 'nav_training:' in content
    assert 'training_modal_title:' in content
    assert 'training_modal_subtitle:' in content
    assert 'data-i18n="nav_training"' in content
