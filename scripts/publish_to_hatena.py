#!/usr/bin/env python3
"""
publish_to_hatena.py
drafts/ から最新の Markdown ファイルを読み込み、
はてなブログ AtomPub API に下書きとして投稿する。
"""

import os
import re
import logging
import requests
from datetime import datetime
from pathlib import Path

import yaml

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

ROOT = Path(__file__).parent.parent
DRAFTS_DIR = ROOT / "drafts"


def load_latest_draft() -> tuple[Path, dict, str]:
    """
    drafts/ から最新の Markdown ファイルを読み込み、
    (filepath, frontmatter, body) を返す。
    """
    md_files = sorted(DRAFTS_DIR.glob("*.md"), key=lambda p: p.stat().st_mtime, reverse=True)
    if not md_files:
        raise FileNotFoundError(f"drafts/ に Markdown ファイルが見つかりません: {DRAFTS_DIR}")

    latest = md_files[0]
    logger.info(f"最新の下書き: {latest}")

    with open(latest, encoding="utf-8") as f:
        content = f.read()

    frontmatter, body = parse_frontmatter(content)
    return latest, frontmatter, body


def parse_frontmatter(content: str) -> tuple[dict, str]:
    """YAMLフロントマターを解析し (frontmatter_dict, body) を返す。

    以下の形式に対応:
    1. 通常のフロントマター: --- ... ---
    2. コードブロック内フロントマター: ```yaml\n--- ... ---\n```
    """
    # パターン1: ```yaml\n---...---\n``` 形式（LLMがコードブロックで出力した場合）
    cb_match = re.match(
        r"^```(?:yaml)?\s*\n---\s*\n([\s\S]*?)\n---\s*\n```\s*\n?([\s\S]*)$",
        content.strip(),
        re.MULTILINE,
    )
    if cb_match:
        try:
            fm = yaml.safe_load(cb_match.group(1))
            body = cb_match.group(2).strip()
            logger.info("コードブロック形式のフロントマターを検出・除去しました")
            return fm or {}, body
        except yaml.YAMLError as e:
            logger.warning(f"YAMLパースエラー（コードブロック形式）: {e}")

    # パターン2: 通常のフロントマター --- ... ---
    match = re.match(r"^---\s*\n([\s\S]*?)\n---\s*\n?([\s\S]*)$", content.strip(), re.MULTILINE)
    if match:
        try:
            fm = yaml.safe_load(match.group(1))
            body = match.group(2).strip()
            return fm or {}, body
        except yaml.YAMLError as e:
            logger.warning(f"YAMLパースエラー: {e}")

    # フロントマターが見つからない場合: タイトルを本文先頭から抽出を試みる
    logger.warning("フロントマターが見つかりませんでした。本文をそのまま使用します。")
    return {}, content.strip()


def build_atom_entry(title: str, content: str, category: str, hatena_id: str) -> str:
    """はてなブログ AtomPub 用の XML エントリを構築する。"""
    # XML特殊文字をエスケープ（タイトルのみ; contentはCDATAで保護）
    title_escaped = (
        title.replace("&", "&amp;")
             .replace("<", "&lt;")
             .replace(">", "&gt;")
             .replace('"', "&quot;")
    )

    return f"""<?xml version="1.0" encoding="utf-8"?>
<entry xmlns="http://www.w3.org/2005/Atom"
       xmlns:app="http://www.w3.org/2007/app">
  <title>{title_escaped}</title>
  <author><name>{hatena_id}</name></author>
  <content type="text/x-markdown"><![CDATA[{content}]]></content>
  <category term="{category}" />
  <app:control>
    <app:draft>yes</app:draft>
  </app:control>
</entry>"""


def post_to_hatena(
    atom_entry: str,
    hatena_id: str,
    blog_id: str,
    api_key: str,
) -> dict:
    """はてなブログ AtomPub API に POST する。"""
    endpoint = f"https://blog.hatena.ne.jp/{hatena_id}/{blog_id}/atom/entry"
    headers = {"Content-Type": "application/atom+xml; charset=utf-8"}

    logger.info(f"投稿先: {endpoint}")
    response = requests.post(
        endpoint,
        data=atom_entry.encode("utf-8"),
        headers=headers,
        auth=(hatena_id, api_key),
        timeout=30,
    )

    if response.status_code in (200, 201):
        logger.info(f"投稿成功: ステータス {response.status_code}")
        # レスポンスから記事 URL を抽出
        url_match = re.search(r"<link[^>]+href=[\"']([^\"']+)[\"'][^>]+rel=[\"']alternate[\"']", response.text)
        if not url_match:
            url_match = re.search(r"<id>([^<]+)</id>", response.text)
        url = url_match.group(1) if url_match else "（URLを取得できませんでした）"
        return {"success": True, "url": url, "status_code": response.status_code}
    else:
        logger.error(f"投稿失敗: ステータス {response.status_code}")
        logger.error(f"レスポンス: {response.text[:500]}")
        response.raise_for_status()
        return {"success": False}


def main():
    hatena_id = os.environ.get("HATENA_ID")
    blog_id = os.environ.get("HATENA_BLOG_ID")
    api_key = os.environ.get("HATENA_API_KEY")

    if not all([hatena_id, blog_id, api_key]):
        raise EnvironmentError(
            "環境変数が不足しています。HATENA_ID, HATENA_BLOG_ID, HATENA_API_KEY を設定してください。"
        )

    logger.info("はてなブログへの投稿を開始します")

    filepath, frontmatter, body = load_latest_draft()

    title = frontmatter.get("title", filepath.stem)
    category = frontmatter.get("category", "ai-tools")
    description = frontmatter.get("description", "")

    logger.info(f"タイトル: {title}")
    logger.info(f"カテゴリ: {category}")

    # 本文の先頭にメタディスクリプションをコメントとして追加（任意）
    full_content = body

    atom_entry = build_atom_entry(title, full_content, category, hatena_id)
    result = post_to_hatena(atom_entry, hatena_id, blog_id, api_key)

    if result["success"]:
        logger.info(f"投稿完了 - URL: {result['url']}")
        print(f"POSTED_URL={result['url']}")
    else:
        raise RuntimeError("投稿に失敗しました")


if __name__ == "__main__":
    main()
