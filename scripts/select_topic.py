#!/usr/bin/env python3
"""
select_topic.py
context/target-keywords.md からまだ記事化していないキーワードを選択し、
topics/selected-topics.log に記録する。
"""

import os
import re
import logging
from datetime import datetime
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

ROOT = Path(__file__).parent.parent
KEYWORDS_FILE = ROOT / "context" / "target-keywords.md"
PUBLISHED_DIR = ROOT / "published"
LOG_FILE = ROOT / "topics" / "selected-topics.log"
SELECTED_TOPIC_FILE = ROOT / "topics" / "current-topic.txt"


def load_keywords(filepath: Path) -> list[dict]:
    """target-keywords.md からキーワードとクラスターを抽出する。"""
    keywords = []
    current_cluster = ""
    priority_map = {"最優先": 1, "中優先": 2, "低優先": 3}
    keyword_priority = 2  # デフォルト

    with open(filepath, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            # クラスター名を検出
            cluster_match = re.match(r"^## (クラスター \d+: .+)$", line)
            if cluster_match:
                current_cluster = cluster_match.group(1)
                continue
            # 優先度セクション
            priority_match = re.match(r"^\d+\. (最優先|中優先|低優先): (.+)$", line)
            if priority_match:
                continue
            # キーワード行
            kw_match = re.match(r"^- (.+?)（ピラー）?$", line)
            if kw_match and current_cluster:
                kw = kw_match.group(1).replace("（ピラー）", "").strip()
                is_pillar = "（ピラー）" in line
                # クラスターから優先度を推定
                if "Claude Code" in current_cluster:
                    keyword_priority = 1
                elif "AIツール" in current_cluster or "ワークフロー" in current_cluster:
                    keyword_priority = 2
                else:
                    keyword_priority = 3
                keywords.append({
                    "keyword": kw,
                    "cluster": current_cluster,
                    "is_pillar": is_pillar,
                    "priority": keyword_priority,
                })
    return keywords


def load_used_topics(log_file: Path) -> set[str]:
    """ログファイルから使用済みキーワードを読み込む。"""
    used = set()
    if log_file.exists():
        with open(log_file, encoding="utf-8") as f:
            for line in f:
                # 形式: 2026-04-08 | keyword | cluster
                parts = line.strip().split(" | ")
                if len(parts) >= 2:
                    used.add(parts[1].strip())
    return used


def load_published_titles(published_dir: Path) -> set[str]:
    """published/ フォルダの Markdown タイトルを収集する。"""
    titles = set()
    if not published_dir.exists():
        return titles
    for md_file in published_dir.glob("**/*.md"):
        with open(md_file, encoding="utf-8") as f:
            for line in f:
                title_match = re.match(r"^title:\s*[\"']?(.+?)[\"']?\s*$", line)
                if title_match:
                    titles.add(title_match.group(1))
                    break
    return titles


def select_next_topic(keywords: list[dict], used: set[str], published: set[str]) -> dict | None:
    """優先度順に未使用・未公開のキーワードを選択する。"""
    available = [
        kw for kw in keywords
        if kw["keyword"] not in used and kw["keyword"] not in published
    ]
    if not available:
        logger.warning("利用可能なキーワードがありません。使用済みリストをリセットします。")
        available = keywords  # フォールバック: 全キーワードから選択

    # 優先度でソート（ピラーページを先に）
    available.sort(key=lambda x: (x["priority"], 0 if x["is_pillar"] else 1))
    return available[0] if available else None


def record_selection(log_file: Path, topic: dict) -> None:
    """選択したキーワードをログに記録する。"""
    log_file.parent.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    entry = f"{timestamp} | {topic['keyword']} | {topic['cluster']}\n"
    with open(log_file, "a", encoding="utf-8") as f:
        f.write(entry)
    logger.info(f"ログに記録: {entry.strip()}")


def save_current_topic(filepath: Path, topic: dict) -> None:
    """次のスクリプトが読み込むために選択済みトピックを保存する。"""
    filepath.parent.mkdir(parents=True, exist_ok=True)
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(f"keyword: {topic['keyword']}\n")
        f.write(f"cluster: {topic['cluster']}\n")
        f.write(f"is_pillar: {topic['is_pillar']}\n")
        f.write(f"priority: {topic['priority']}\n")
    logger.info(f"選択トピックを保存: {filepath}")


def main():
    logger.info("トピック選択を開始します")

    keywords = load_keywords(KEYWORDS_FILE)
    logger.info(f"キーワード総数: {len(keywords)}")

    used_topics = load_used_topics(LOG_FILE)
    logger.info(f"使用済みキーワード数: {len(used_topics)}")

    published_titles = load_published_titles(PUBLISHED_DIR)
    logger.info(f"公開済み記事数: {len(published_titles)}")

    topic = select_next_topic(keywords, used_topics, published_titles)
    if not topic:
        logger.error("選択できるトピックがありません")
        raise SystemExit(1)

    logger.info(f"選択されたキーワード: {topic['keyword']} ({topic['cluster']})")
    record_selection(LOG_FILE, topic)
    save_current_topic(SELECTED_TOPIC_FILE, topic)
    print(f"SELECTED_TOPIC={topic['keyword']}")


if __name__ == "__main__":
    main()
