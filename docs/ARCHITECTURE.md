# アーキテクチャ設計書

Baby Cry Analysis System Architecture Documentation

## システム概要

本システムは、赤ちゃんの泣き声音声ファイルを解析し、音響特徴を抽出・可視化するWebアプリケーションです。
3層アーキテクチャを採用し、フロントエンド・バックエンド・データベースが疎結合で構成されています。

---

## システムアーキテクチャ図

```
┌─────────────────────────────────────────────────────────────┐
│                          Browser                             │
│                                                              │
│  ┌────────────────────────────────────────────────────────┐ │
│  │          Frontend (React + TypeScript)                 │ │
│  │                                                         │ │
│  │  - React 18                                            │ │
│  │  - TypeScript                                          │ │
│  │  - Plotly.js (Visualization)                           │ │
│  │  - Axios (HTTP Client)                                 │ │
│  │  - React Router (Routing)                              │ │
│  └────────────────────────────────────────────────────────┘ │
└──────────────────────────┬──────────────────────────────────┘
                           │ HTTP/HTTPS
                           │ REST API
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                    Backend Server                            │
│                                                              │
│  ┌────────────────────────────────────────────────────────┐ │
│  │           FastAPI Application                          │ │
│  │                                                         │ │
│  │  - FastAPI (Web Framework)                             │ │
│  │  - Pydantic (Validation)                               │ │
│  │  - SQLAlchemy (ORM)                                    │ │
│  │  - JWT Authentication                                  │ │
│  │  - CORS Middleware                                     │ │
│  └────────────────────────────────────────────────────────┘ │
│                           │                                  │
│                           │ Task Queue                       │
│                           ▼                                  │
│  ┌────────────────────────────────────────────────────────┐ │
│  │             Celery Workers                             │ │
│  │                                                         │ │
│  │  - librosa (Audio Processing)                          │ │
│  │  - parselmouth (Praat Integration)                     │ │
│  │  - numpy, scipy (Scientific Computing)                 │ │
│  └────────────────────────────────────────────────────────┘ │
└──────────────┬─────────────────────┬────────────────────────┘
               │                     │
               │                     │ Task Management
               │                     ▼
               │            ┌─────────────────┐
               │            │  Redis          │
               │            │                 │
               │            │  - Message      │
               │            │    Broker       │
               │            │  - Result       │
               │            │    Backend      │
               │            └─────────────────┘
               │
               │ Data Persistence
               ▼
    ┌─────────────────────┐
    │  PostgreSQL         │
    │                     │
    │  - Audio File       │
    │    Metadata         │
    │  - Analysis         │
    │    Results          │
    │  - User Data        │
    └─────────────────────┘
```

---

## 技術スタック

### フロントエンド

| カテゴリ | 技術 | バージョン | 用途 |
|---------|-----|-----------|------|
| フレームワーク | React | 18.x | UIライブラリ |
| 言語 | TypeScript | 5.x | 型安全な開発 |
| ビルドツール | Vite | 5.x | 高速ビルド・HMR |
| 状態管理 | React Context | - | グローバル状態管理 |
| ルーティング | React Router | 6.x | SPA ルーティング |
| HTTPクライアント | Axios | 1.x | API通信 |
| 可視化 | Plotly.js | 2.x | グラフ・チャート描画 |

### バックエンド

| カテゴリ | 技術 | バージョン | 用途 |
|---------|-----|-----------|------|
| フレームワーク | FastAPI | 0.109.x | Web API フレームワーク |
| 言語 | Python | 3.10+ | メイン言語 |
| ASGI サーバー | Uvicorn | 0.27.x | 非同期サーバー |
| ORM | SQLAlchemy | 2.x | データベースORM |
| バリデーション | Pydantic | 2.x | データバリデーション |
| マイグレーション | Alembic | 1.x | DBスキーマ管理 |
| タスクキュー | Celery | 5.x | 非同期タスク処理 |
| 認証 | PyJWT | 2.x | JWT認証 |
| パスワード | bcrypt | 4.x | パスワードハッシュ化 |

### 音声処理

| カテゴリ | 技術 | バージョン | 用途 |
|---------|-----|-----------|------|
| 音声解析 | librosa | 0.10.x | 音声信号処理 |
| 音響分析 | parselmouth | 0.4.x | Praat 機能の利用 |
| 数値計算 | NumPy | 1.26.x | 配列演算 |
| 科学計算 | SciPy | 1.11.x | 信号処理・統計 |
| ファイル操作 | soundfile | 0.12.x | 音声ファイルI/O |

### インフラストラクチャ

| カテゴリ | 技術 | バージョン | 用途 |
|---------|-----|-----------|------|
| データベース | PostgreSQL | 14+ | リレーショナルDB |
| メッセージブローカー | Redis | 7+ | Celery バックエンド |
| コンテナ | Docker | 24.x | 開発環境構築 |

---

## ディレクトリ構造

### バックエンド

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py                    # FastAPI アプリケーション
│   ├── config.py                  # 設定管理
│   ├── database.py                # データベース接続
│   ├── celery_app.py              # Celery設定
│   │
│   ├── api/                       # APIエンドポイント
│   │   ├── __init__.py
│   │   ├── deps.py                # 依存性注入
│   │   └── v1/
│   │       ├── __init__.py
│   │       ├── auth.py            # 認証API
│   │       ├── audio_files.py     # ファイル管理API
│   │       ├── analysis.py        # 解析API
│   │       ├── export.py          # エクスポートAPI
│   │       ├── visualization.py   # 可視化API
│   │       ├── users.py           # ユーザー管理API
│   │       └── tags.py            # タグ管理API
│   │
│   ├── models/                    # データベースモデル
│   │   ├── __init__.py
│   │   ├── user.py
│   │   ├── audio_file.py
│   │   ├── analysis_result.py
│   │   └── tag.py
│   │
│   ├── schemas/                   # Pydanticスキーマ
│   │   ├── __init__.py
│   │   ├── user.py
│   │   ├── audio_file.py
│   │   ├── analysis.py
│   │   ├── analysis_result.py
│   │   └── tag.py
│   │
│   ├── auth/                      # 認証・認可
│   │   ├── __init__.py
│   │   ├── jwt.py                 # JWTトークン処理
│   │   ├── password.py            # パスワード処理
│   │   └── permissions.py         # 権限チェック
│   │
│   ├── tasks/                     # Celeryタスク
│   │   ├── __init__.py
│   │   └── analysis_tasks.py      # 解析タスク
│   │
│   └── analysis/                  # 音声解析ロジック
│       ├── __init__.py
│       ├── episode_detector.py    # エピソード検出
│       ├── feature_extractor.py   # 特徴量抽出
│       ├── cry_unit_analyzer.py   # Cry Unit解析
│       └── statistics.py          # 統計計算
│
├── alembic/                       # DBマイグレーション
│   ├── versions/
│   ├── env.py
│   └── script.py.mako
│
├── storage/                       # ファイルストレージ
│   └── audio/
│
├── requirements.txt
├── .env.example
└── alembic.ini
```

### フロントエンド

```
frontend/
├── src/
│   ├── main.tsx                   # エントリーポイント
│   ├── App.tsx                    # ルートコンポーネント
│   ├── index.css                  # グローバルスタイル
│   │
│   ├── components/                # 再利用可能コンポーネント
│   │   ├── AudioPlayer.tsx
│   │   ├── WaveformVisualization.tsx
│   │   └── SpectrogramVisualization.tsx
│   │
│   ├── pages/                     # ページコンポーネント
│   │   ├── LoginPage.tsx
│   │   ├── RegisterPage.tsx
│   │   ├── DashboardPage.tsx
│   │   └── FileDetailPage.tsx
│   │
│   ├── contexts/                  # Reactコンテキスト
│   │   └── AuthContext.tsx        # 認証コンテキスト
│   │
│   ├── api/                       # APIクライアント
│   │   └── client.ts
│   │
│   └── types/                     # TypeScript型定義
│       └── index.ts
│
├── public/
├── index.html
├── package.json
├── tsconfig.json
└── vite.config.ts
```

---

## データフロー

### 1. ファイルアップロードフロー

```
User
  │
  │ 1. Select File
  ▼
Frontend (DashboardPage)
  │
  │ 2. POST /api/v1/audio-files/upload
  │    (multipart/form-data)
  ▼
Backend (audio_files.py)
  │
  ├─ 3. Validate File
  ├─ 4. Generate UUID Filename
  ├─ 5. Save to /storage/audio/
  │
  │ 6. Extract Metadata (librosa/soundfile)
  │    - Sample Rate
  │    - Duration
  │
  └─ 7. Save to DB (audio_files table)
       - status: "uploaded"
  │
  │ 8. Return AudioFile Object
  ▼
Frontend
  │
  │ 9. Update File List
  └─ 10. Display Success Message
```

### 2. 音声解析フロー

```
User
  │
  │ 1. Click "解析開始"
  ▼
Frontend (DashboardPage)
  │
  │ 2. POST /api/v1/analysis/{file_id}/start
  ▼
Backend (analysis.py)
  │
  ├─ 3. Check File Status
  ├─ 4. Update Status to "processing"
  │
  │ 5. Queue Celery Task
  └────────────────┐
                   ▼
              Celery Worker (analysis_tasks.py)
                   │
                   ├─ 6. Load Audio File
                   │
                   ├─ 7. Episode Detection
                   │    - Energy-based Detection
                   │    - Confidence Calculation
                   │
                   ├─ 8. Feature Extraction
                   │    For each episode:
                   │    - F0 (Fundamental Frequency)
                   │    - Formants (F1, F2, F3)
                   │    - HNR, Jitter, Shimmer
                   │    - Intensity
                   │
                   ├─ 9. Cry Unit Analysis
                   │    - Unit Segmentation
                   │    - Voiced/Unvoiced Classification
                   │    - Expiratory Phase Calculation
                   │
                   └─ 10. Statistics Calculation
                        - Mean, Std, Min, Max, Median
                        - For each acoustic parameter
  ┌─────────────────┘
  │
  │ 11. Save Results to DB
  │     (analysis_results table)
  │
  │ 12. Update File Status to "completed"
  ▼
Backend
  │
  │ 13. Task Complete
  ▼
Frontend (Polling)
  │
  │ 14. GET /api/v1/analysis/{file_id}/status
  │
  │ 15. status: "completed"
  │
  │ 16. GET /api/v1/analysis/{file_id}/result
  └─ 17. Display Results with Visualizations
```

### 3. 認証フロー

```
User
  │
  │ 1. Enter Credentials
  ▼
Frontend (LoginPage)
  │
  │ 2. POST /api/v1/auth/login
  │    { email, password }
  ▼
Backend (auth.py)
  │
  ├─ 3. Query User by Email
  ├─ 4. Verify Password (bcrypt)
  │
  │ 5. Generate JWT Token
  │    - Payload: {sub: user_id, email, role}
  │    - Expiration: 30 days
  │    - Sign with SECRET_KEY
  │
  └─ 6. Return Token + User Info
  │
  │ 7. Return to Frontend
  ▼
Frontend
  │
  ├─ 8. Store Token in localStorage
  ├─ 9. Update AuthContext
  │
  │ 10. Redirect to Dashboard
  └─────────────────────────────┐
                                ▼
                    All Subsequent Requests
                                │
                                │ Authorization: Bearer <token>
                                ▼
                         Backend Middleware
                                │
                                ├─ Verify JWT Signature
                                ├─ Check Expiration
                                ├─ Extract User Info
                                │
                                └─ Inject current_user
                                   into Request Handler
```

---

## セキュリティ設計

### 1. 認証・認可

#### JWT認証
- **トークン形式:** Bearer Token
- **アルゴリズム:** HS256 (HMAC-SHA256)
- **有効期限:** 30日
- **ペイロード:**
  ```json
  {
    "sub": "user_id",
    "email": "user@example.com",
    "role": "user",
    "exp": 1234567890
  }
  ```

#### パスワードセキュリティ
- **ハッシュアルゴリズム:** bcrypt
- **ストレッチング回数:** 12 rounds
- **ソルト:** 自動生成（bcrypt組み込み）

#### 権限レベル

| ロール | 権限 |
|-------|------|
| user | 自分のファイルのみアクセス可能 |
| researcher | 全ユーザーのファイルにアクセス可能 |

### 2. APIセキュリティ

#### CORS設定
```python
allow_origins = ["http://localhost:5173", "http://localhost:5174"]
allow_credentials = True
allow_methods = ["*"]
allow_headers = ["*"]
```

#### レート制限
- 現在未実装（将来的な拡張予定）

#### 入力バリデーション
- Pydantic による厳密な型チェック
- ファイルサイズ制限: 100MB
- ファイル形式制限: WAV, MP3, FLAC, M4A, OGG

### 3. データ保護

#### ファイルストレージ
- UUID v4 によるファイル名の匿名化
- ディレクトリトラバーサル対策

#### SQLインジェクション対策
- SQLAlchemy ORM の使用
- パラメータ化クエリの徹底

#### XSS対策
- React によるエスケープ処理
- CSP ヘッダーの設定（推奨）

---

## パフォーマンス最適化

### 1. バックエンド

#### 非同期処理
- Celery による重い処理の非同期化
- 音声解析タスクをバックグラウンドで実行

#### データベースクエリ最適化
```python
# Eager Loading によるN+1問題の回避
files = db.query(AudioFile).options(
    joinedload(AudioFile.tags),
    joinedload(AudioFile.analysis_results)
).all()

# ページネーション
files = db.query(AudioFile).offset(skip).limit(limit).all()
```

#### キャッシング
- Redis を使用した結果キャッシュ（将来実装予定）

### 2. フロントエンド

#### コード分割
- React.lazy() による動的インポート
- ページ単位でのコード分割

#### 画像・アセット最適化
- Vite による自動最適化
- Tree-shaking による不要コードの削除

#### メモ化
```typescript
const MemoizedComponent = React.memo(Component);
const memoizedValue = useMemo(() => computeExpensiveValue(a, b), [a, b]);
const memoizedCallback = useCallback(() => { doSomething(a, b); }, [a, b]);
```

---

## スケーラビリティ

### 水平スケーリング戦略

#### アプリケーションサーバー
```
        Load Balancer
              │
    ┌─────────┼─────────┐
    │         │         │
   API-1    API-2    API-3
    │         │         │
    └─────────┴─────────┘
              │
        PostgreSQL
```

#### Celery ワーカー
```
   Task Queue (Redis)
          │
    ┌─────┼─────┐
    │     │     │
Worker-1 W-2 W-3
```

### 垂直スケーリング

- CPU: 音声処理タスクに応じて増強
- メモリ: 大容量ファイル処理用に増強
- ストレージ: 音声ファイル保存用にSSD使用

---

## モニタリング・ロギング

### ログレベル

| レベル | 用途 |
|-------|------|
| DEBUG | 開発時の詳細情報 |
| INFO | 通常の動作ログ |
| WARNING | 潜在的な問題 |
| ERROR | エラー発生 |
| CRITICAL | システム停止レベル |

### ログ出力先

- **開発環境:** コンソール出力
- **本番環境:** ファイル出力 + 集約サービス（推奨）

### メトリクス収集（推奨）

- **Prometheus:** メトリクス収集
- **Grafana:** ダッシュボード可視化
- **監視項目:**
  - API レスポンスタイム
  - Celery タスク実行時間
  - データベースクエリ実行時間
  - エラー率

---

## デプロイメント

### 開発環境

```bash
# Backend
uvicorn app.main:app --reload

# Celery
celery -A app.celery_app worker --loglevel=info

# Frontend
npm run dev
```

### 本番環境（推奨構成）

#### Docker Compose構成例

```yaml
services:
  postgres:
    image: postgres:14
    environment:
      POSTGRES_DB: baby_cry_db
      POSTGRES_USER: user
      POSTGRES_PASSWORD: password
    volumes:
      - postgres_data:/var/lib/postgresql/data

  redis:
    image: redis:7
    volumes:
      - redis_data:/data

  backend:
    build: ./backend
    command: gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker
    environment:
      DATABASE_URL: postgresql://user:password@postgres:5432/baby_cry_db
      REDIS_URL: redis://redis:6379/0
    depends_on:
      - postgres
      - redis

  celery:
    build: ./backend
    command: celery -A app.celery_app worker --loglevel=info
    depends_on:
      - postgres
      - redis

  frontend:
    build: ./frontend
    command: nginx -g 'daemon off;'
    ports:
      - "80:80"
```

---

## 今後の拡張予定

1. **機能拡張:**
   - リアルタイム音声解析（WebSocket）
   - 機械学習モデルの統合
   - 複数言語対応

2. **パフォーマンス:**
   - Redis キャッシング層の追加
   - CDN による静的アセット配信

3. **セキュリティ:**
   - OAuth 2.0 認証の追加
   - 2要素認証（2FA）

4. **運用:**
   - CI/CD パイプライン構築
   - 自動テスト・デプロイ
   - ヘルスチェック・自動復旧

---

## 参考文献・技術ドキュメント

- FastAPI: https://fastapi.tiangolo.com/
- React: https://react.dev/
- librosa: https://librosa.org/
- Praat/parselmouth: https://parselmouth.readthedocs.io/
- PostgreSQL: https://www.postgresql.org/docs/
- Celery: https://docs.celeryq.dev/
