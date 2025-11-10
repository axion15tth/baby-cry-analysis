# 赤ちゃん泣き声解析システム - バックエンド

## 動作確認結果 ✅

### Phase 1: 認証機能 ✅ 完了
- ✅ FastAPIサーバーが正常に起動（DB接続あり）
- ✅ ルートエンドポイント (`/`) が動作
- ✅ ヘルスチェックエンドポイント (`/health`) が動作
- ✅ APIドキュメント (`/docs`) が正常に表示
- ✅ プロジェクト構造が正しく作成されている
- ✅ PostgreSQL 16.10 インストール・接続確認完了
- ✅ Redis 7.0.15 インストール・接続確認完了
- ✅ Alembic マイグレーション作成・適用完了
- ✅ ユーザー登録API（POST /api/v1/auth/register）動作確認済み
- ✅ ログインAPI（POST /api/v1/auth/login）動作確認済み
- ✅ JWT認証（GET /api/v1/auth/me）動作確認済み
- ✅ データベース書き込み確認済み

### Phase 2: ファイル管理機能 ✅ 完了
- ✅ AudioFileモデル作成（recording_start_time対応）
- ✅ audio_filesテーブルマイグレーション適用完了
- ✅ ファイルアップロードAPI（POST /api/v1/files/upload）動作確認済み
- ✅ ファイル一覧API（GET /api/v1/files/）動作確認済み
- ✅ ファイル詳細API（GET /api/v1/files/{id}）動作確認済み
- ✅ ファイル更新API（PATCH /api/v1/files/{id}）動作確認済み
- ✅ ファイル削除API（DELETE /api/v1/files/{id}）動作確認済み
- ✅ ファイルストレージ機能（./storage/audio/）動作確認済み

### Phase 3: 音声解析機能 ✅ 実装完了
- ✅ librosa、parselmouth、celery等の必要パッケージインストール完了
- ✅ CryDetectorクラス実装（長時間データ対応、チャンク処理）
- ✅ AcousticAnalyzerクラス実装（F0、フォルマント、HNR、Shimmer、Jitter）
- ✅ AnalysisResultモデル・スキーマ作成
- ✅ Celery設定とバックグラウンドタスク実装
- ✅ 解析API実装（POST /api/v1/analysis/start）
- ✅ ステータス確認API（GET /api/v1/analysis/status/{id}）
- ✅ 結果取得API（GET /api/v1/analysis/results/{id}）
- ✅ analysis_resultsテーブルマイグレーション適用完了

### Phase 4: エクスポート機能 ✅ 完了
- ✅ 時刻計算ユーティリティ実装
- ✅ CSVエクスポーター実装（泣き声エピソード、音響特徴、統計）
- ✅ Excelエクスポーター実装（3シート構成：概要、エピソード、音響特徴）
- ✅ PDFエクスポーター実装（レポート形式）
- ✅ エクスポートAPI実装
  - GET /api/v1/export/csv/episodes/{file_id}
  - GET /api/v1/export/csv/features/{file_id}/{episode_id}
  - GET /api/v1/export/excel/{file_id}
  - GET /api/v1/export/pdf/{file_id}
- ✅ 絶対時刻対応（recording_start_time + 相対秒）

### Phase 5: フロントエンド ✅ 完了
- ✅ Vite + React + TypeScript プロジェクトセットアップ
- ✅ React Router DOM によるルーティング実装
- ✅ APIクライアント実装（axios）
- ✅ 認証コンテキスト実装（JWT自動付与）
- ✅ ログイン・登録UI実装
- ✅ ダッシュボードUI実装
  - ファイルアップロード機能
  - ファイル一覧表示（ステータス別色分け）
  - 解析開始・進捗監視（自動ポーリング）
  - 解析結果表示（泣き声エピソード、統計）
  - エクスポート機能（Excel、PDF）
- ✅ フロントエンド開発サーバー起動確認（http://localhost:5173/）

### テスト結果
```bash
# ヘルスチェック
$ curl http://localhost:8000/health
{
    "status": "healthy"
}

# ユーザー登録
$ curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"test123456","role":"user"}'
{
    "id": 1,
    "email": "test@example.com",
    "role": "user",
    "created_at": "2025-11-06T14:55:35.314451Z"
}

# ログイン
$ curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"test123456"}'
{
    "access_token": "eyJhbGci...",
    "token_type": "bearer",
    "user": {
        "id": 1,
        "email": "test@example.com",
        "role": "user",
        "created_at": "2025-11-06T14:55:35.314451Z"
    }
}

# 現在のユーザー情報取得（JWT認証）
$ curl -X GET http://localhost:8000/api/v1/auth/me \
  -H "Authorization: Bearer eyJhbGci..."
{
    "id": 1,
    "email": "test@example.com",
    "role": "user",
    "created_at": "2025-11-06T14:55:35.314451Z"
}

# データベース確認
$ psql -h localhost -U baby_cry_user -d baby_cry_db -c "SELECT id, email, role FROM users;"
 id |      email       | role
----+------------------+------
  1 | test@example.com | user

# ファイルアップロード
$ curl -X POST http://localhost:8000/api/v1/files/upload \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@/path/to/audio.wav" \
  -F "recording_start_time=2025-11-06T10:00:00Z"
{
    "message": "File uploaded successfully",
    "file": {
        "id": 1,
        "user_id": 1,
        "filename": "cc840a78-92d0-4051-8ee7-db617bca099a.wav",
        "original_filename": "audio.wav",
        "file_path": "./storage/audio/cc840a78-92d0-4051-8ee7-db617bca099a.wav",
        "file_size": 1024,
        "recording_start_time": "2025-11-06T10:00:00Z",
        "status": "uploaded",
        "uploaded_at": "2025-11-06T15:05:39.557751Z"
    }
}

# ファイル一覧取得
$ curl -X GET http://localhost:8000/api/v1/files/ \
  -H "Authorization: Bearer $TOKEN"
{
    "total": 1,
    "files": [...]
}

# ファイル削除
$ curl -X DELETE http://localhost:8000/api/v1/files/1 \
  -H "Authorization: Bearer $TOKEN"
# 204 No Content

# APIドキュメント
http://localhost:8000/docs (Swagger UI)
http://localhost:8000/redoc (ReDoc)
```

## 実装済みファイル

### 設定ファイル
- `requirements.txt` - 全パッケージリスト
- `requirements-minimal.txt` - 動作確認用最小限パッケージ
- `.env` - 環境変数設定
- `alembic.ini` - データベースマイグレーション設定

### アプリケーションコア
- `app/main.py` - FastAPIアプリケーションエントリーポイント
- `app/main_test.py` - テスト用サーバー（DB接続なし）
- `app/config.py` - 設定管理
- `app/database.py` - データベース接続設定

### 認証機能
- `app/models/user.py` - Userモデル（SQLAlchemy）
- `app/schemas/user.py` - Userスキーマ（Pydantic）
- `app/utils/security.py` - JWT認証、パスワードハッシュ化（bcrypt）
- `app/api/deps.py` - 認証依存関数
- `app/api/v1/auth.py` - 認証API（登録、ログイン）

### ファイル管理機能
- `app/models/audio_file.py` - AudioFileモデル（SQLAlchemy）
- `app/schemas/audio_file.py` - AudioFileスキーマ（Pydantic）
- `app/api/v1/audio_files.py` - ファイル管理API（アップロード、一覧、詳細、更新、削除）
- `storage/audio/` - 音声ファイルストレージ

### マイグレーション
- `alembic/env.py` - Alembic環境設定
- `alembic/script.py.mako` - マイグレーションテンプレート
- `alembic/versions/5db98864bdb6_create_users_table.py` - usersテーブルマイグレーション
- `alembic/versions/26389e3ea6c7_create_audio_files_table.py` - audio_filesテーブルマイグレーション

## 実装済みAPIエンドポイント

### 認証API
- `POST /api/v1/auth/register` - ユーザー登録
  - リクエスト: `{email, password, role}`
  - レスポンス: ユーザー情報

- `POST /api/v1/auth/login` - ログイン
  - リクエスト: `{email, password}`
  - レスポンス: `{access_token, token_type, user}`

- `GET /api/v1/auth/me` - 現在のユーザー情報取得
  - ヘッダー: `Authorization: Bearer <token>`
  - レスポンス: ユーザー情報

### ファイル管理API
- `POST /api/v1/files/upload` - ファイルアップロード
  - リクエスト: `multipart/form-data {file, recording_start_time (optional)}`
  - レスポンス: ファイル情報
  - 認証: 必須

- `GET /api/v1/files/` - ファイル一覧取得
  - クエリ: `skip (default: 0), limit (default: 100)`
  - レスポンス: `{total, files}`
  - 認証: 必須

- `GET /api/v1/files/{file_id}` - ファイル詳細取得
  - レスポンス: ファイル情報
  - 認証: 必須

- `PATCH /api/v1/files/{file_id}` - ファイル情報更新
  - リクエスト: `{recording_start_time (optional), status (optional)}`
  - レスポンス: 更新後のファイル情報
  - 認証: 必須

- `DELETE /api/v1/files/{file_id}` - ファイル削除
  - レスポンス: 204 No Content
  - 認証: 必須

### システムAPI
- `GET /` - ルートエンドポイント
- `GET /health` - ヘルスチェック
- `GET /docs` - API仕様書（Swagger UI）
- `GET /redoc` - API仕様書（ReDoc）

## プロジェクト構造

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py                 # メインアプリケーション
│   ├── main_test.py           # テスト用サーバー
│   ├── config.py              # 設定管理
│   ├── database.py            # データベース接続
│   │
│   ├── api/                   # API層
│   │   ├── deps.py           # 依存性注入
│   │   └── v1/
│   │       ├── auth.py       # 認証API
│   │       └── audio_files.py # ファイル管理API
│   │
│   ├── models/               # SQLAlchemyモデル
│   │   ├── user.py          # Userモデル
│   │   └── audio_file.py    # AudioFileモデル
│   │
│   ├── schemas/              # Pydanticスキーマ
│   │   ├── user.py          # Userスキーマ
│   │   └── audio_file.py    # AudioFileスキーマ
│   │
│   ├── utils/                # ユーティリティ
│   │   └── security.py       # JWT、パスワード管理
│   │
│   ├── repositories/         # データアクセス層（未実装）
│   ├── services/            # ビジネスロジック層（未実装）
│   ├── audio/               # 音声処理（未実装）
│   ├── visualization/       # 可視化（未実装）
│   ├── export/              # エクスポート（未実装）
│   ├── external/            # 外部API連携（未実装）
│   └── tasks/               # Celeryタスク（未実装）
│
├── alembic/                 # データベースマイグレーション
│   ├── env.py
│   └── versions/
│
├── tests/                   # テスト（未実装）
├── storage/                 # ファイルストレージ
├── ml_models/               # 機械学習モデル
│
├── requirements.txt         # 依存パッケージ（全て）
├── requirements-minimal.txt # 依存パッケージ（最小限）
├── .env                     # 環境変数
└── README.md               # このファイル
```

## 次のステップ

### フェーズ2: ファイル管理機能 ✅ 完了
- [x] AudioFileモデル作成
- [x] ファイルアップロードAPI（録音開始時刻対応）
- [x] ファイル一覧・詳細・削除API
- [x] マイグレーション実行

### フェーズ3: 音声解析機能 ✅ 完了
- [x] CryDetector実装（長時間データ対応）
- [x] AcousticAnalyzer実装（F0、フォルマント、HNR、Shimmer、Jitter）
- [x] Celeryタスク実装
- [x] 解析API実装

### フェーズ4: エクスポート機能 ✅ 完了
- [x] CSV出力（絶対時刻対応）
- [x] Excel出力（3シート構成）
- [x] PDF出力
- [x] 時刻計算ユーティリティ

### フェーズ5: フロントエンド
- [ ] React + TypeScriptセットアップ
- [ ] 認証UI
- [ ] ファイルアップロードUI
- [ ] 解析結果表示
- [ ] データエクスポート

## 開発コマンド

### サーバー起動（本番モード - DB接続あり）
```bash
# backend/ディレクトリから実行
source .venv/bin/activate
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### サーバー起動（テストモード - DB接続なし）
```bash
# backend/ディレクトリから実行
source .venv/bin/activate
cd app
python -m uvicorn main_test:app --reload --host 0.0.0.0 --port 8000
```

### マイグレーション作成
```bash
alembic revision --autogenerate -m "Create users table"
```

### マイグレーション適用
```bash
alembic upgrade head
```

### テスト実行
```bash
pytest tests/
```

## 環境変数

`.env`ファイルに以下の変数を設定：

```bash
DATABASE_URL=postgresql://baby_cry_user:dev_password@localhost:5432/baby_cry_db
REDIS_URL=redis://localhost:6379/0
SECRET_KEY=your-secret-key-here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=1440
AWABABY_API_KEY=your-awababy-api-key
AWABABY_API_URL=https://api.awababy.example.com
MAX_FILE_SIZE_MB=500
STORAGE_PATH=./storage
ML_MODEL_PATH=./ml_models/cry_detector_v1.pth
ALLOWED_ORIGINS=http://localhost:3000,http://localhost:5173
```

## 環境情報

### インストール済みコンポーネント
- PostgreSQL 16.10 (ポート: 5432)
- Redis 7.0.15 (ポート: 6379)
- Python 3.12 仮想環境 (.venv)

### データベース接続情報
- データベース名: baby_cry_db
- ユーザー名: baby_cry_user
- パスワード: dev_password
- ホスト: localhost
- ポート: 5432

### パッケージインストール
全パッケージ（音声処理、機械学習ライブラリを含む）をインストールする場合：
```bash
pip install -r requirements.txt
```

最小限のパッケージのみ（FastAPI動作確認用）：
```bash
pip install -r requirements-minimal.txt
```
