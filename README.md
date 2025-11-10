# Baby Cry Analysis System (泣き声解析システム)

赤ちゃんの泣き声を解析し、音響特徴を抽出・可視化するWebアプリケーションシステムです。

## GitHubリポジトリ

https://github.com/axion15tth/baby-cry-analysis

## 概要

本システムは、赤ちゃんの泣き声音声ファイルをアップロードし、以下の機能を提供します：

- 泣き声エピソードの自動検出
- 音響特徴量（F0, F1-F3フォルマント、HNR、ジッター、シマーなど）の抽出
- 時系列データの可視化（波形、スペクトログラム、音響特徴プロット）
- 統計情報の集計と表示
- データのエクスポート（CSV、JSON）
- ファイルへのタグ付け機能

## システム構成

### バックエンド (FastAPI + Python)
- **フレームワーク:** FastAPI
- **データベース:** PostgreSQL
- **タスクキュー:** Celery + Redis
- **音声処理:** librosa, parselmouth (Praat)
- **認証:** JWT (JSON Web Token)

### フロントエンド (React + TypeScript)
- **フレームワーク:** React 18 + TypeScript
- **ビルドツール:** Vite
- **可視化:** Plotly.js
- **HTTP クライアント:** Axios
- **ルーティング:** React Router

## 必要な環境

### バックエンド
- Python 3.10+
- PostgreSQL 14+
- Redis 7+

### フロントエンド
- Node.js 18+
- npm 9+

## セットアップ手順

### 1. リポジトリのクローン

```bash
git clone https://github.com/axion15tth/baby-cry-analysis.git
cd baby-cry-analysis
```

### 2. バックエンドのセットアップ

#### 2.1 PostgreSQLの起動

```bash
# Dockerを使用する場合
docker run --name postgres-baby-cry \
  -e POSTGRES_USER=dev_user \
  -e POSTGRES_PASSWORD=dev_password \
  -e POSTGRES_DB=baby_cry_db \
  -p 5432:5432 \
  -d postgres:14
```

#### 2.2 Redisの起動

```bash
# Dockerを使用する場合
docker run --name redis-baby-cry \
  -p 6379:6379 \
  -d redis:7
```

#### 2.3 Python環境のセットアップ

```bash
cd backend

# 仮想環境の作成
python -m venv .venv

# 仮想環境の有効化
source .venv/bin/activate  # Linux/Mac
# または
.venv\Scripts\activate  # Windows

# 依存パッケージのインストール
pip install -r requirements.txt

# 環境変数の設定
cp .env.example .env
# .envファイルを編集してデータベース接続情報などを設定

# データベースマイグレーション
alembic upgrade head
```

#### 2.4 バックエンドサーバーの起動

```bash
# FastAPIサーバーの起動
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# 別のターミナルでCeleryワーカーの起動
celery -A app.celery_app worker --loglevel=info
```

### 3. フロントエンドのセットアップ

```bash
cd frontend

# 依存パッケージのインストール
npm install

# 環境変数の設定（オプション）
# フロントエンドの.envファイルを作成してAPIのURLを設定
# デフォルトではhttp://localhost:8000/api/v1を使用します
echo "VITE_API_URL=http://localhost:8000/api/v1" > .env

# 開発サーバーの起動
npm run dev
```

### 4. アクセス

- **フロントエンド:** http://localhost:5173
- **バックエンドAPI:** http://localhost:8000
- **API ドキュメント (Swagger):** http://localhost:8000/docs

## 初回ユーザー登録

1. ブラウザで http://localhost:5173 にアクセス
2. 「新規登録」をクリック
3. メールアドレスとパスワードを入力して登録
4. ログインして利用開始

## サンプル音声ファイル

動作確認用のサンプル音声ファイルが用意されています：

- **ファイル名:** `realistic_baby_cry.wav`
- **説明:** 赤ちゃんの泣き声を含むサンプル音声（約10秒、1.3MB）
- **使用方法:** システムにログイン後、このファイルをアップロードして解析機能をお試しください

## 使用方法

### 1. 音声ファイルのアップロード

1. ダッシュボードで「ファイルを選択」ボタンをクリック
2. WAV/MP3/FLAC形式の音声ファイルを選択
3. オプション: 録音開始時刻を入力
4. 「アップロード」ボタンをクリック

### 2. 音声解析の実行

1. アップロードしたファイルの「解析開始」ボタンをクリック
2. 解析の進行状況がリアルタイムで表示されます
3. 解析完了後、結果が自動的に表示されます

### 3. 解析結果の確認

ファイル詳細ページでは以下の情報が表示されます：

- **波形表示:** 音声ファイルの時間領域波形
- **スペクトログラム:** 周波数成分の時間変化
- **泣き声エピソード:** 検出された泣き声区間のタイムライン
- **音響特徴:** F0, フォルマント周波数の時系列プロット
- **統計情報:** 各エピソードの音響パラメータ統計

### 4. データのエクスポート

1. ダッシュボードで対象ファイルを選択
2. 「エクスポート」ボタンをクリック
3. 形式（CSV/JSON）を選択してダウンロード

### 5. ファイルへのタグ付け

1. ファイル詳細ページでタグセクションを表示
2. 既存タグの選択または新規タグの作成
3. ファイルに複数のタグを付けて分類・管理

## プロジェクト構造

```
nagoichi/
├── backend/                 # バックエンドアプリケーション
│   ├── app/
│   │   ├── api/            # APIエンドポイント
│   │   ├── models/         # データベースモデル
│   │   ├── schemas/        # Pydanticスキーマ
│   │   ├── auth/           # 認証・認可
│   │   ├── tasks/          # Celeryタスク
│   │   ├── analysis/       # 音声解析処理
│   │   └── config.py       # 設定
│   ├── alembic/            # DBマイグレーション
│   ├── requirements.txt    # Python依存パッケージ
│   └── .env.example        # 環境変数テンプレート
├── frontend/               # フロントエンドアプリケーション
│   ├── src/
│   │   ├── components/    # Reactコンポーネント
│   │   ├── pages/         # ページコンポーネント
│   │   ├── contexts/      # Reactコンテキスト
│   │   ├── api/           # APIクライアント
│   │   └── types/         # TypeScript型定義
│   ├── package.json       # npm依存パッケージ
│   └── vite.config.ts     # Vite設定
└── docs/                  # ドキュメント
    ├── API.md             # API仕様書
    ├── DATABASE.md        # データベース設計書
    └── ARCHITECTURE.md    # アーキテクチャ設計書
```

## 開発

### バックエンド開発

```bash
cd backend
source .venv/bin/activate

# マイグレーションの作成
alembic revision --autogenerate -m "description"

# マイグレーションの適用
alembic upgrade head

# テストの実行
pytest
```

### フロントエンド開発

```bash
cd frontend

# 開発サーバー起動
npm run dev

# ビルド
npm run build

# プレビュー
npm run preview

# 型チェック
npm run type-check
```

## デプロイ

### 外部アクセス設定

サーバーを外部に公開する場合、以下の設定が必要です：

#### バックエンド (.env)
```bash
# フロントエンドのURLをCORS許可リストに追加
ALLOWED_ORIGINS=http://localhost:3000,http://localhost:5173,http://your-server-ip:5173
```

#### フロントエンド (.env)
```bash
# バックエンドAPIのURLを設定
VITE_API_URL=http://your-server-ip:8000/api/v1
```

#### AWS EC2の場合
Security Groupで以下のポートを開放：
- ポート 8000（バックエンドAPI）
- ポート 5173（フロントエンド開発サーバー）
- ポート 22（SSH）

### バックエンド

```bash
# 本番用の環境変数を設定
export DATABASE_URL="postgresql://user:password@host:5432/dbname"
export REDIS_URL="redis://host:6379/0"
export SECRET_KEY="your-secret-key"
export ALLOWED_ORIGINS="http://your-frontend-url"

# Gunicornで起動
gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000

# Celeryワーカーの起動
celery -A app.celery_app worker --loglevel=info
```

### フロントエンド

```bash
# 環境変数を設定
export VITE_API_URL="http://your-backend-url/api/v1"

# ビルド
npm run build

# distディレクトリをWebサーバーにデプロイ
# （Nginx, Apache, Vercel, Netlify など）
```

## トラブルシューティング

### データベース接続エラー

```bash
# PostgreSQLが起動しているか確認
docker ps | grep postgres

# 接続テスト
psql -h localhost -U dev_user -d baby_cry_db
```

### Redis接続エラー

```bash
# Redisが起動しているか確認
docker ps | grep redis

# 接続テスト
redis-cli ping
```

### Celeryタスクが実行されない

```bash
# Celeryワーカーのログを確認
celery -A app.celery_app worker --loglevel=debug

# Redisのキューを確認
redis-cli
> KEYS *
```

### CORS エラー（外部アクセス時）

ブラウザのコンソールに「Access-Control-Allow-Origin」エラーが表示される場合：

1. バックエンドの `.env` ファイルを確認
```bash
# フロントエンドのURLが含まれているか確認
cat backend/.env | grep ALLOWED_ORIGINS
```

2. フロントエンドの `.env` ファイルを確認
```bash
# バックエンドのURLが正しいか確認
cat frontend/.env | grep VITE_API_URL
```

3. バックエンドを再起動して設定を反映
```bash
# 既存のプロセスを停止
lsof -ti:8000 | xargs -r kill -9

# 新しい設定で起動
cd backend
source .venv/bin/activate
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## ライセンス

本プロジェクトは研究・教育目的で開発されています。

## 貢献

プルリクエストを歓迎します。大きな変更の場合は、まずissueを開いて変更内容を議論してください。

## サポート

問題が発生した場合は、GitHubのIssuesセクションで報告してください。

## 関連ドキュメント

- [API仕様書](docs/API.md)
- [データベース設計書](docs/DATABASE.md)
- [アーキテクチャ設計書](docs/ARCHITECTURE.md)
- [デプロイガイド](docs/DEPLOYMENT.md)
