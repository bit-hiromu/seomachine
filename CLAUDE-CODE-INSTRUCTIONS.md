# SEO Machine 自動化セットアップ — Claude Code 指示設計書

## 概要

このドキュメントは、SEO MachineをフォークしてGroq API + GitHub Actions + はてなブログAPIによる
記事自動生成・投稿パイプラインを構築するための、Claude Codeへの指示設計書です。

VS Code上でClaude Codeを使い、以下の指示を順番に実行してください。

---

## 前提条件（事前に自分で準備するもの）

以下のアカウント・情報を事前に取得してください:

1. **GitHubアカウント** — フォーク・リポジトリ管理用
2. **Groq APIキー** — https://console.groq.com で無料取得（クレカ不要）
3. **はてなブログアカウント** — https://hatenablog.com で開設
4. **はてなブログAPIキー** — はてなブログ管理画面 > 設定 > 詳細設定 > AtomPub で確認
5. **はてなID** — はてなのユーザーID
6. **ブログID** — はてなブログのドメイン（例: your-blog.hatenablog.com）

---

## Phase 1: リポジトリのフォークとクローン

### 指示 1-1: フォークとクローン

```
GitHubで https://github.com/TheCraigHewitt/seomachine をフォークしてください。

フォーク後、ローカルにクローンします:
git clone https://github.com/[あなたのGitHubユーザー名]/seomachine.git
cd seomachine
```

> ※ フォークはGitHub WebUIで行い、クローン以降をClaude Codeで実行

### 指示 1-2: ディレクトリ構成の確認

Claude Codeに以下を入力:

```
プロジェクトのディレクトリ構成を確認して、主要なファイルの役割を教えて
```

---

## Phase 2: Contextファイルの設定

### 指示 2-1: brand-voice.md の作成

Claude Codeに以下を入力:

```
context/brand-voice.md を以下の内容で上書きしてください:

# Brand Voice Guide

## ブランド概要
- ブログ名: [あなたのブログ名]
- ポジショニング: エンジニア・開発者向けのAI活用実践ブログ
- 言語: 日本語
- プラットフォーム: はてなブログ

## ターゲットオーディエンス
- 日本のソフトウェアエンジニア・開発者（25〜45歳）
- AI/LLMツールを業務に取り入れたい中級以上のエンジニア
- Claude Code、ChatGPT、GitHub Copilotなどに関心がある層

## ブランドボイス
- 実践的: 理論だけでなく、実際に手を動かして試した結果を伝える
- 率直: 良い点も悪い点も正直に書く。過度な煽りはしない
- 技術的かつ親しみやすい: 専門用語は使うが、必要に応じて補足する
- 一人称は「自分」または省略

## やること
- 実際のコード例やコマンド例を必ず含める
- 具体的な数値（実行時間、トークン数、コスト）を示す
- メリットだけでなくデメリットや注意点も書く

## やらないこと
- 「革命的」「神ツール」などの誇大表現
- 根拠のない主観だけの評価
- 初心者向けの過度に丁寧な説明

## 差別化ポイント
- Claude Codeのヘビーユーザー視点
- 日本語での深い技術情報
- 開発者の実務に直結する具体的なワークフロー紹介
```

### 指示 2-2: style-guide.md の作成

Claude Codeに以下を入力:

```
context/style-guide.md を以下の内容で上書きしてください:

# Style Guide

## 記事フォーマット
1. タイトル（H1）: 32文字以内、検索意図に合致
2. リード文: 3〜5文で要点とメリット
3. 目次: H2ベースで自動生成
4. 本文: H2/H3で構造化、1セクション300〜600文字
5. まとめ: ポイントの箇条書き
6. 関連記事リンク: 内部リンク2〜3本

## 文体
- ハウツー記事: 「〜です/〜ます」調
- レビュー・考察記事: 「〜だ/〜である」調
- 1文は60文字以内を目安
- 段落は3〜4文で区切る

## コード記載ルール
- コードブロックには必ず言語を指定
- コマンドには実行環境を明記
- コピー＆ペーストでそのまま動くことを目指す

## 数値・単位
- 半角数字を使用
- 英数字と日本語の間にスペースを入れる
- 日付は YYYY年MM月 形式
```

### 指示 2-3: target-keywords.md の作成

Claude Codeに以下を入力:

```
context/target-keywords.md を以下の内容で上書きしてください:

# Target Keywords

## キーワード戦略
ロングテールキーワード中心。競合の少ないニッチから攻める。

## クラスター 1: Claude Code
- Claude Code 使い方 完全ガイド（ピラー）
- Claude Code インストール 方法
- Claude Code 料金 プラン 比較
- Claude Code vs GitHub Copilot 比較
- Claude Code vs Cursor 違い
- Claude Code MCP サーバー 設定
- Claude Code エラー 対処法

## クラスター 2: AIツール比較
- AIコーディングツール 比較（ピラー）
- GitHub Copilot 最新機能 レビュー
- Cursor エディタ 使い方
- AIコーディング 無料ツール まとめ

## クラスター 3: AI活用ワークフロー
- エンジニア AI 業務効率化 ガイド（ピラー）
- AI コードレビュー 自動化
- AI テスト自動生成 方法
- プロンプトエンジニアリング エンジニア向け

## クラスター 4: AI最新トレンド
- Claude 新機能 まとめ
- AI エージェント 最新動向
- ローカルLLM 実行 方法

## 優先度
1. 最優先: Claude Code + 具体的操作キーワード
2. 中優先: AIツール比較、ワークフロー系
3. 低優先: AI一般ニュース
```

### 指示 2-4: 残りのcontextファイルを作成

Claude Codeに以下を入力:

```
以下の3つのcontextファイルも作成してください:

1. context/features.md — ブログの提供価値として:
   - Claude Code実践レポート（毎日使用するヘビーユーザー視点）
   - AIツール比較・レビュー（コード例付き）
   - 開発ワークフロー改善（ビフォーアフター付き）
   - アフィリエイト候補: Claude Pro, GitHub Copilot, Cursor Pro, AWS, プログラミング書籍

2. context/competitor-analysis.md — 競合分析として:
   - Qiita/Zenn: 記事数膨大だが個人の深い検証記事は少ない
   - 大手メディア: ニュース速報型、深い実践レビューは少ない
   - 個人ブログ: Claude Code系の日本語ブログはまだ少ない
   - コンテンツギャップ: Claude Code詳細ガイド、MCP実践、日本語環境での比較検証

3. context/internal-links-map.md — 内部リンクマップとして:
   - カテゴリ: claude-code, ai-tools, ai-workflow, ai-news
   - ピラーページ3つ（Claude Code完全ガイド、AIツール比較、AI活用ガイド）
   - ルール: 各記事から最低2本の内部リンク、相互リンク必須

seo-guidelines.md と writing-examples.md はテンプレートのままでOKです。
```

---

## Phase 3: 自動化パイプラインの構築

### 指示 3-1: 自動化用のディレクトリとファイルを作成

Claude Codeに以下を入力:

```
以下の自動化パイプラインを構築してください:

## 要件
- GitHub Actionsで毎日1回（日本時間9:00）自動実行
- Groq API（無料枠）でLlama 3.3 70Bを使って記事を生成
- はてなブログのAtomPub APIで「下書き」として投稿
- context/ フォルダの設定を記事生成のプロンプトに反映

## 作成するファイル

### 1. scripts/generate_article.py
Pythonスクリプト。以下の処理を行う:
- context/ フォルダからbrand-voice.md、style-guide.md、target-keywords.mdを読み込む
- target-keywords.md からランダムまたは順番にキーワードを選択
- Groq APIを呼び出してSEO最適化された日本語記事を生成
- モデルは llama-3.3-70b-versatile を使用
- OpenAI互換のAPIエンドポイント https://api.groq.com/openai/v1 を使用
- 生成された記事をMarkdown形式で drafts/ フォルダに保存
- メタ情報（タイトル、メタディスクリプション、カテゴリ、キーワード）もYAMLフロントマターとして含める
- レート制限を考慮し、複数回のAPI呼び出し間にsleepを入れる

Groq APIの呼び出し例:
```python
from openai import OpenAI

client = OpenAI(
    api_key=os.environ["GROQ_API_KEY"],
    base_url="https://api.groq.com/openai/v1"
)

response = client.chat.completions.create(
    model="llama-3.3-70b-versatile",
    messages=[
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt}
    ],
    temperature=0.7,
    max_tokens=4096
)
```

### 2. scripts/publish_to_hatena.py
Pythonスクリプト。以下の処理を行う:
- drafts/ フォルダから最新の記事を読み込む
- YAMLフロントマターからタイトル、カテゴリを取得
- はてなブログのAtomPub APIに下書きとして投稿
- 認証はBASIC認証（はてなID + APIキー）を使用
- エンドポイント: https://blog.hatena.ne.jp/{はてなID}/{ブログID}/atom/entry
- content typeは text/x-markdown を指定
- app:draft を yes に設定（下書き状態）

投稿XMLの形式:
```xml
<?xml version="1.0" encoding="utf-8"?>
<entry xmlns="http://www.w3.org/2005/Atom"
       xmlns:app="http://www.w3.org/2007/app">
  <title>{タイトル}</title>
  <author><name>{はてなID}</name></author>
  <content type="text/x-markdown">{Markdown本文}</content>
  <category term="{カテゴリ}" />
  <app:control>
    <app:draft>yes</app:draft>
  </app:control>
</entry>
```

### 3. scripts/select_topic.py
Pythonスクリプト。以下の処理を行う:
- context/target-keywords.md を読み込み
- published/ フォルダの既存記事タイトルと照合して、まだ書いていないキーワードを特定
- 優先度順に次のトピックを選択して返す
- 選択したキーワードを topics/selected-topics.log に記録

### 4. .github/workflows/daily-article.yml
GitHub Actionsワークフロー:
```yaml
name: Daily Article Generation

on:
  schedule:
    - cron: '0 0 * * *'  # UTC 0:00 = JST 9:00
  workflow_dispatch:  # 手動実行も可能

jobs:
  generate-and-publish:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Setup Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.12'
      
      - name: Install dependencies
        run: pip install openai requests pyyaml
      
      - name: Select topic
        run: python scripts/select_topic.py
        env:
          GROQ_API_KEY: ${{ secrets.GROQ_API_KEY }}
      
      - name: Generate article
        run: python scripts/generate_article.py
        env:
          GROQ_API_KEY: ${{ secrets.GROQ_API_KEY }}
      
      - name: Publish to Hatena Blog (draft)
        run: python scripts/publish_to_hatena.py
        env:
          HATENA_ID: ${{ secrets.HATENA_ID }}
          HATENA_BLOG_ID: ${{ secrets.HATENA_BLOG_ID }}
          HATENA_API_KEY: ${{ secrets.HATENA_API_KEY }}
      
      - name: Commit generated files
        run: |
          git config user.name "github-actions[bot]"
          git config user.email "github-actions[bot]@users.noreply.github.com"
          git add drafts/ published/ topics/
          git diff --staged --quiet || git commit -m "Auto-generate article $(date +%Y-%m-%d)"
          git push
```

### 5. scripts/requirements.txt
```
openai>=1.0.0
requests>=2.31.0
pyyaml>=6.0
```

## 記事生成プロンプトの設計

generate_article.py 内のシステムプロンプトは、以下の要素を含めてください:

1. brand-voice.md の内容をそのまま埋め込む
2. style-guide.md のルールを埋め込む
3. seo-guidelines.md のSEO要件を埋め込む

ユーザープロンプトは:
- 選択されたキーワードとトピック
- 記事の目標文字数（3000〜5000文字）
- 「日本語で書いてください」の明示指定
- 「YAMLフロントマター付きMarkdown形式で出力してください」の指定

フロントマター形式:
```yaml
---
title: "記事タイトル"
description: "メタディスクリプション（120文字以内）"
category: "claude-code"
keywords: ["Claude Code", "使い方"]
date: "2026-04-08"
---
```

## 重要な注意点
- Groq APIの無料枠はレート制限あり（RPM: 30, RPD: 1000）
- API呼び出し間に最低2秒のsleepを入れること
- 長い記事は複数回のAPI呼び出しで生成（セクションごとに分割）
- エラー時はリトライ（最大3回、exponential backoff）
- 全てのスクリプトにログ出力を含めること
```

### 指示 3-2: テスト実行

Claude Codeに以下を入力:

```
作成したスクリプトをローカルでテスト実行してください。

1. まず scripts/select_topic.py を実行してトピック選択をテスト
2. 次に scripts/generate_article.py を実行して記事生成をテスト
   - 環境変数 GROQ_API_KEY を設定してから実行
3. 生成された記事の内容を確認して品質をチェック

※ publish_to_hatena.py のテストはまだ行わない（はてなブログ設定後に実施）
```

---

## Phase 4: GitHub Secretsの設定

### 手動で行う作業（Claude Codeではなく、GitHub WebUIで実施）

リポジトリの Settings > Secrets and variables > Actions で以下を登録:

| Secret名 | 値 |
|----------|---|
| `GROQ_API_KEY` | Groqのコンソールで取得したAPIキー |
| `HATENA_ID` | あなたのはてなID |
| `HATENA_BLOG_ID` | ブログのドメイン（例: your-blog.hatenablog.com） |
| `HATENA_API_KEY` | はてなブログの設定画面で確認したAPIキー |

---

## Phase 5: テストと初回実行

### 指示 5-1: GitHub Actionsの手動テスト

Claude Codeに以下を入力:

```
.github/workflows/daily-article.yml のワークフローに
workflow_dispatch トリガーが含まれていることを確認してください。

確認後、以下の手順でテストします:
1. 全ての変更をcommit & pushする
2. GitHubリポジトリの Actions タブから手動でワークフローを実行
3. ログを確認してエラーがないかチェック
```

### 指示 5-2: はてなブログAPIのテスト

Claude Codeに以下を入力:

```
scripts/publish_to_hatena.py を使って、テスト記事をはてなブログに
下書き投稿するテストを行います。

以下の環境変数を設定してから実行してください:
export HATENA_ID="あなたのはてなID"
export HATENA_BLOG_ID="your-blog.hatenablog.com"
export HATENA_API_KEY="あなたのAPIキー"

python scripts/publish_to_hatena.py

投稿後、はてなブログの管理画面で下書きに記事が追加されているか確認します。
```

---

## Phase 6: 運用開始後のメンテナンス

### 指示 6-1: 記事公開後の処理

記事を確認して公開した後、Claude Codeで以下を実行:

```
公開した記事を管理してください:

1. drafts/ の該当記事を published/ に移動
2. context/internal-links-map.md に新しい記事のURLを追加
3. 既存の関連記事に新しい記事への内部リンクを追加提案
4. 変更をcommit & push
```

### 指示 6-2: 週次メンテナンス（週1回実行）

Claude Codeに以下を入力:

```
週次メンテナンスを実行してください:

1. published/ の記事一覧と context/target-keywords.md を照合して、
   カバレッジを確認（何%のキーワードを記事化済みか）
2. context/internal-links-map.md を最新の状態に更新
3. 今週のおすすめトピック3つを提案
```

### 指示 6-3: 月次メンテナンス（月1回実行）

Claude Codeに以下を入力:

```
月次メンテナンスを実行してください:

1. published/ の全記事を確認し、情報が古くなっている記事をリストアップ
2. context/target-keywords.md に新しいキーワードの追加を提案
3. context/competitor-analysis.md の更新を提案
4. writing-examples.md をベスト記事5本に更新
```

---

## トラブルシューティング

### Groq APIでエラーが出る場合

Claude Codeに以下を入力:

```
scripts/generate_article.py のGroq API呼び出し部分を確認して、
以下をチェックしてください:
- レート制限に引っかかっていないか（429エラー）
- APIキーが正しく設定されているか
- モデル名が正しいか（llama-3.3-70b-versatile）
- リトライロジックが正しく動作するか
```

### はてなブログAPIでエラーが出る場合

Claude Codeに以下を入力:

```
scripts/publish_to_hatena.py のAPI呼び出し部分を確認して、
以下をチェックしてください:
- BASIC認証の形式が正しいか（はてなID:APIキー）
- エンドポイントURLが正しいか
- XMLの形式が正しいか
- content typeが text/x-markdown になっているか
```

### GitHub Actionsが失敗する場合

Claude Codeに以下を入力:

```
.github/workflows/daily-article.yml を確認して、
以下をチェックしてください:
- Secretsの名前がスクリプトの環境変数名と一致しているか
- Pythonバージョンが正しいか
- pip install で全依存関係がインストールされるか
- git push の権限が正しいか（contents: write が必要）
```

---

## ファイル一覧（最終状態）

```
seomachine/
├── .claude/                    # SEO Machine標準（変更なし）
│   ├── commands/
│   ├── agents/
│   └── skills/
├── .github/
│   └── workflows/
│       └── daily-article.yml   # ★新規: 自動化ワークフロー
├── context/                    # ★編集: 日本語AI ブログ用に設定
│   ├── brand-voice.md
│   ├── style-guide.md
│   ├── target-keywords.md
│   ├── features.md
│   ├── competitor-analysis.md
│   ├── internal-links-map.md
│   ├── seo-guidelines.md
│   └── writing-examples.md
├── scripts/                    # ★新規: 自動化スクリプト
│   ├── generate_article.py
│   ├── publish_to_hatena.py
│   ├── select_topic.py
│   └── requirements.txt
├── data_sources/               # SEO Machine標準（オプション）
├── topics/
│   └── selected-topics.log     # ★自動生成: 選択済みトピック記録
├── research/
├── drafts/                     # 自動生成された下書き
├── published/                  # 公開済み記事
├── rewrites/
└── README.md
```

---

## コスト一覧

| 項目 | 月額コスト |
|------|-----------|
| Claude Code | 契約済み（〜$20） |
| Groq API | 無料 |
| GitHub Actions | 無料（パブリックリポ）/ 無料枠内（プライベート） |
| はてなブログ | 無料 |
| **合計** | **Claude Codeの契約費用のみ** |
