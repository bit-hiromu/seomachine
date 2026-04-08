#!/usr/bin/env python3
"""
generate_article.py
Groq API (OpenAI互換) を使って SEO 最適化された日本語記事を生成し、
drafts/ フォルダに Markdown + YAMLフロントマター形式で保存する。
"""

import os
import re
import time
import logging
from datetime import datetime
from pathlib import Path

from openai import OpenAI, RateLimitError, APIError

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

ROOT = Path(__file__).parent.parent
CONTEXT_DIR = ROOT / "context"
DRAFTS_DIR = ROOT / "drafts"
TOPICS_FILE = ROOT / "topics" / "current-topic.txt"

GROQ_MODEL = "llama-3.3-70b-versatile"  # TPD 100K（1日1記事=約20Kトークンで問題なし）
MAX_RETRIES = 3
RETRY_DELAY = 5  # 秒


MAX_CONTEXT_CHARS = 1500  # システムプロンプトのトークン超過を防ぐ上限


def load_context_file(filename: str) -> str:
    """context/ フォルダからファイルを読み込む（1500文字に制限）。"""
    filepath = CONTEXT_DIR / filename
    if not filepath.exists():
        logger.warning(f"コンテキストファイルが見つかりません: {filepath}")
        return ""
    with open(filepath, encoding="utf-8") as f:
        content = f.read()
    if len(content) > MAX_CONTEXT_CHARS:
        content = content[:MAX_CONTEXT_CHARS] + "\n...(省略)"
    return content


def load_current_topic() -> dict:
    """topics/current-topic.txt から選択済みトピックを読み込む。"""
    if not TOPICS_FILE.exists():
        raise FileNotFoundError(f"トピックファイルが見つかりません: {TOPICS_FILE}")
    topic = {}
    with open(TOPICS_FILE, encoding="utf-8") as f:
        for line in f:
            if ": " in line:
                key, value = line.strip().split(": ", 1)
                topic[key.strip()] = value.strip()
    return topic


CLUSTER_CATEGORY_MAP = {
    "Claude Code": "claude-code",
    "AIツール":    "ai-tools",
    "ワークフロー": "ai-workflow",
    "トレンド":    "ai-news",
}


def cluster_to_category(cluster: str) -> str:
    """クラスター名からはてなブログカテゴリを返す。"""
    for key, cat in CLUSTER_CATEGORY_MAP.items():
        if key in cluster:
            return cat
    return "ai-tools"


def build_system_prompt(brand_voice: str, style_guide: str, seo_guidelines: str, category: str = "claude-code") -> str:
    """システムプロンプトを構築する。"""
    return f"""あなたは日本語の技術ブログ記事を執筆するSEOエキスパートです。
以下のブランドボイス、スタイルガイド、SEOガイドラインに従って記事を作成してください。

---
{brand_voice}
---
{style_guide}
---
{seo_guidelines}
---

記事は必ず以下の形式で出力してください。
コードブロックで囲まずに、そのまま出力してください:

---
title: "記事タイトル（32文字以内）"
description: "メタディスクリプション（120文字以内）"
category: "{category}"
keywords: ["キーワード1", "キーワード2"]
date: "{datetime.now().strftime('%Y-%m-%d')}"
---

# 記事タイトル

本文をここに書く...

重要: フロントマター（---で囲まれた部分）はコードブロックに入れないでください。
本文中のコードブロックは必ず言語を指定し、実際に動作するコード例を含めてください。"""


CLAUDE_CODE_FACTS = """
## Claude Code に関する正確な情報

Claude Code は Anthropic が開発した CLI ツール（コマンドラインインターフェース）です。
IDE ではなく、ターミナルから使う AI コーディングエージェントです。

### インストール方法
```bash
npm install -g @anthropic-ai/claude-code
```

### 基本的な起動方法
```bash
# プロジェクトディレクトリに移動して起動
cd your-project
claude
```

### 主なコマンド・使い方
```bash
# ファイルを読み込んで質問
claude "このコードのバグを直して"

# 特定ファイルを指定
claude --file src/app.py "この関数を最適化して"

# 会話を続ける（--continue）
claude --continue

# 非対話モード（スクリプト用）
claude -p "テストを書いて" --output-format json
```

### 料金（2026年4月時点）
- Claude Pro サブスクリプション（$20/月）に含まれる
- API 従量課金での利用も可能
- 入力: $3 / 1M トークン、出力: $15 / 1M トークン（Claude 3.5 Sonnet）
- 1 日の使用量目安: コード補完・質問で 50〜200K トークン程度

### Claude Code の特徴
- ファイルの読み書き、コマンド実行、Git 操作まで自律的に行う
- MCP（Model Context Protocol）でツール拡張が可能
- `.claude/` ディレクトリで設定・カスタムコマンドを管理
- CLAUDE.md でプロジェクト固有のルールを定義できる

### GitHub Copilot / Cursor との違い
- GitHub Copilot: エディタ補完中心。コード補完の精度が高い
- Cursor: VS Code ベースの AI エディタ。GUI 操作が快適
- Claude Code: CLI ベース。自律的なタスク実行が得意。ファイル操作・コマンド実行まで一貫して行える
"""


def build_user_prompt(topic: dict, section: str = "full") -> str:
    """記事生成用のユーザープロンプトを構築する。"""
    keyword = topic.get("keyword", "")
    cluster = topic.get("cluster", "")
    is_pillar = topic.get("is_pillar", "False").lower() == "true"

    word_count = "5000〜7000文字" if is_pillar else "3000〜5000文字"

    # Claude Code クラスターの記事には正確な情報を注入する
    facts_section = ""
    if "Claude Code" in cluster or "Claude Code" in keyword:
        facts_section = f"\n\n以下の情報を参考にして、正確な内容を書いてください:\n{CLAUDE_CODE_FACTS}\n"

    if section == "full":
        return f"""以下のキーワードで日本語の技術ブログ記事を書いてください。
{facts_section}
【メインキーワード】{keyword}
【トピッククラスター】{cluster}
【目標文字数】{word_count}
【記事タイプ】{"ピラーページ（包括的ガイド）" if is_pillar else "サポート記事（具体的なハウツー）"}

要件:
- YAMLフロントマター付きMarkdown形式で出力
- 実際のコマンド例（コピーしてそのまま動くもの）を必ず含める
- 具体的な数値（コスト、トークン数、実行時間など）を示す
- H2/H3で構造化し、各セクション300〜600文字
- メリットとデメリット・注意点の両方を記載
- 内部リンクのURLは `/entry/` で始まる仮URLを使用
- 日本語で書いてください"""
    elif section == "intro":
        return f"""以下のキーワードで日本語記事のイントロダクション部分を書いてください。
{facts_section}
【メインキーワード】{keyword}
【トピッククラスター】{cluster}

出力内容:
- YAMLフロントマター（title, description, category, keywords, date）
- H1タイトル
- リード文（3〜5文、要点とメリットを簡潔に）
- 目次（H2見出しのリスト）

日本語で書いてください。"""
    elif section == "body":
        return f"""以下のキーワードで日本語記事の本文を書いてください。
{facts_section}
【メインキーワード】{keyword}
【トピッククラスター】{cluster}
【目標文字数】{word_count}

出力内容:
- H2/H3で構造化された本文
- 各セクション300〜600文字
- 実際のコマンド例（言語指定必須、コピーしてそのまま動くもの）
- 具体的な数値データ（コスト・時間など）
- デメリット・注意点のセクションを含める

日本語で書いてください。"""
    elif section == "conclusion":
        return f"""以下のキーワードで日本語記事のまとめ部分を書いてください。

【メインキーワード】{keyword}

出力内容:
- ## まとめ セクション（箇条書きでポイントを整理）
- 関連記事への内部リンク（URLは /entry/ で始まる仮URLを使用）

日本語で書いてください。"""
    return ""


def call_groq_api(client: OpenAI, system_prompt: str, user_prompt: str) -> str:
    """Groq API を呼び出す。レート制限時はリトライする。"""
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            logger.info(f"API呼び出し (試行 {attempt}/{MAX_RETRIES})")
            response = client.chat.completions.create(
                model=GROQ_MODEL,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=0.7,
                max_tokens=4096,
            )
            content = response.choices[0].message.content
            logger.info(f"API呼び出し成功 ({len(content)} 文字)")
            return content
        except RateLimitError as e:
            wait = RETRY_DELAY * (2 ** (attempt - 1))
            logger.warning(f"レート制限エラー: {e}. {wait}秒後にリトライします")
            time.sleep(wait)
        except APIError as e:
            wait = RETRY_DELAY * attempt
            logger.warning(f"APIエラー: {e}. {wait}秒後にリトライします")
            time.sleep(wait)
    raise RuntimeError(f"API呼び出しが {MAX_RETRIES} 回失敗しました")


def generate_article(client: OpenAI, topic: dict, system_prompt: str) -> str:
    """
    記事を生成する。
    ピラー・通常記事ともに intro → body → conclusion の3分割で生成し結合する。
    max_tokens=2048 でも合計6,000文字以上を確保するため。
    """
    logger.info("3分割生成を開始します (intro → body → conclusion)")

    intro = call_groq_api(client, system_prompt, build_user_prompt(topic, "intro"))
    time.sleep(3)  # レート制限対策

    body = call_groq_api(client, system_prompt, build_user_prompt(topic, "body"))
    time.sleep(3)

    conclusion = call_groq_api(client, system_prompt, build_user_prompt(topic, "conclusion"))

    return _merge_sections(intro, body, conclusion)


def _merge_sections(intro: str, body: str, conclusion: str) -> str:
    """
    イントロ・本文・まとめを結合する。
    フロントマターは intro から取り、body/conclusion の余分なフロントマターを除去する。
    """
    def strip_frontmatter(text: str) -> str:
        """YAMLフロントマターを除去する。"""
        stripped = re.sub(r"^---[\s\S]*?---\s*", "", text, count=1)
        return stripped.strip()

    body_clean = strip_frontmatter(body)
    conclusion_clean = strip_frontmatter(conclusion)

    return f"{intro.strip()}\n\n{body_clean}\n\n{conclusion_clean}"


def save_draft(content: str, keyword: str) -> Path:
    """生成した記事を drafts/ に保存する。"""
    DRAFTS_DIR.mkdir(parents=True, exist_ok=True)
    date_str = datetime.now().strftime("%Y-%m-%d")
    # ファイル名用にキーワードをサニタイズ
    safe_keyword = re.sub(r"[^\w\u3040-\u9FFF\u30A0-\u30FF]", "-", keyword)
    safe_keyword = re.sub(r"-+", "-", safe_keyword).strip("-")[:50]
    filename = f"{date_str}-{safe_keyword}.md"
    filepath = DRAFTS_DIR / filename

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)

    logger.info(f"記事を保存しました: {filepath}")
    return filepath


def main():
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        raise EnvironmentError("GROQ_API_KEY 環境変数が設定されていません")

    logger.info("記事生成を開始します")

    # コンテキスト読み込み
    brand_voice = load_context_file("brand-voice.md")
    style_guide = load_context_file("style-guide.md")
    seo_guidelines = load_context_file("seo-guidelines.md")

    # トピック読み込み
    topic = load_current_topic()
    logger.info(f"トピック: {topic.get('keyword')} ({topic.get('cluster')})")

    # Groq クライアント初期化
    client = OpenAI(
        api_key=api_key,
        base_url="https://api.groq.com/openai/v1",
    )

    # クラスターからカテゴリを決定
    category = cluster_to_category(topic.get("cluster", ""))
    logger.info(f"カテゴリ: {category}")

    # システムプロンプト構築
    system_prompt = build_system_prompt(brand_voice, style_guide, seo_guidelines, category)

    # 記事生成
    article = generate_article(client, topic, system_prompt)

    # 保存
    filepath = save_draft(article, topic.get("keyword", "article"))
    print(f"DRAFT_FILE={filepath}")
    logger.info("記事生成完了")


if __name__ == "__main__":
    main()
