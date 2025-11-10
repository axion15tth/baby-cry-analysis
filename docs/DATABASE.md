# データベース設計書

Baby Cry Analysis System Database Schema

## データベース情報

- **DBMS:** PostgreSQL 14+
- **文字コード:** UTF-8
- **タイムゾーン:** UTC

---

## テーブル一覧

1. [users](#1-users-ユーザーテーブル) - ユーザー情報
2. [audio_files](#2-audio_files-音声ファイルテーブル) - 音声ファイルメタデータ
3. [analysis_results](#3-analysis_results-解析結果テーブル) - 解析結果データ
4. [tags](#4-tags-タグテーブル) - タグマスタ
5. [audio_file_tags](#5-audio_file_tags-ファイルタグ関連テーブル) - ファイルとタグの多対多関連

---

## ER図

```
users (1) ----< (N) audio_files (1) ----< (N) analysis_results
                       |
                       | (M)
                       |
                    (N) |
                   audio_file_tags
                       | (N)
                       |
                    (1) |
                      tags
```

---

## 1. users (ユーザーテーブル)

システムを利用するユーザーの情報を管理します。

### カラム定義

| カラム名 | 型 | NULL | デフォルト | 説明 |
|----------|-----|------|-----------|------|
| id | SERIAL | NO | - | 主キー |
| email | VARCHAR(255) | NO | - | メールアドレス（ログインID） |
| hashed_password | VARCHAR(255) | NO | - | ハッシュ化されたパスワード |
| role | VARCHAR(50) | NO | 'user' | ユーザーロール |
| created_at | TIMESTAMP WITH TIME ZONE | NO | CURRENT_TIMESTAMP | 作成日時 |

### 制約

- **PRIMARY KEY:** `id`
- **UNIQUE:** `email`
- **CHECK:** `role IN ('user', 'researcher')`

### インデックス

- `ix_users_id` ON `id`
- `ix_users_email` ON `email`

### 備考

- `hashed_password`: bcryptでハッシュ化
- `role`:
  - `user`: 一般ユーザー（自分のファイルのみアクセス可）
  - `researcher`: 研究者（全ユーザーのデータにアクセス可）

---

## 2. audio_files (音声ファイルテーブル)

アップロードされた音声ファイルのメタデータを管理します。

### カラム定義

| カラム名 | 型 | NULL | デフォルト | 説明 |
|----------|-----|------|-----------|------|
| id | SERIAL | NO | - | 主キー |
| user_id | INTEGER | NO | - | ユーザーID（外部キー） |
| filename | VARCHAR(255) | NO | - | システム内部のファイル名（UUID） |
| original_filename | VARCHAR(255) | NO | - | 元のファイル名 |
| file_path | VARCHAR(500) | NO | - | ファイルの保存パス |
| file_size | BIGINT | NO | - | ファイルサイズ（バイト） |
| sample_rate | INTEGER | YES | NULL | サンプリングレート（Hz） |
| duration | FLOAT | YES | NULL | 継続時間（秒） |
| recording_start_time | TIMESTAMP WITH TIME ZONE | YES | NULL | 録音開始時刻 |
| status | VARCHAR(50) | NO | 'uploaded' | 処理ステータス |
| task_id | VARCHAR(255) | YES | NULL | Celeryタスクなど |
| uploaded_at | TIMESTAMP WITH TIME ZONE | NO | CURRENT_TIMESTAMP | アップロード日時 |

### 制約

- **PRIMARY KEY:** `id`
- **FOREIGN KEY:** `user_id` REFERENCES `users(id)` ON DELETE CASCADE
- **CHECK:** `status IN ('uploaded', 'processing', 'completed', 'failed')`

### インデックス

- `ix_audio_files_id` ON `id`
- `ix_audio_files_user_id` ON `user_id`
- `ix_audio_files_status` ON `status`
- `ix_audio_files_recording_start_time` ON `recording_start_time`

### 備考

- `filename`: UUID v4 + 拡張子（例: `abc123-def456.wav`）
- `file_path`: `/storage/audio/abc123-def456.wav`
- `status`:
  - `uploaded`: アップロード済み（未解析）
  - `processing`: 解析中
  - `completed`: 解析完了
  - `failed`: 解析失敗

---

## 3. analysis_results (解析結果テーブル)

音声ファイルの解析結果を格納します。

### カラム定義

| カラム名 | 型 | NULL | デフォルト | 説明 |
|----------|-----|------|-----------|------|
| id | SERIAL | NO | - | 主キー |
| audio_file_id | INTEGER | NO | - | 音声ファイルID（外部キー） |
| result_data | JSONB | NO | - | 解析結果データ（JSON形式） |
| analyzed_at | TIMESTAMP WITH TIME ZONE | NO | CURRENT_TIMESTAMP | 解析完了日時 |

### 制約

- **PRIMARY KEY:** `id`
- **FOREIGN KEY:** `audio_file_id` REFERENCES `audio_files(id)` ON DELETE CASCADE
- **UNIQUE:** `audio_file_id`（1ファイルにつき1解析結果）

### インデックス

- `ix_analysis_results_id` ON `id`
- `ix_analysis_results_audio_file_id` ON `audio_file_id`

### result_data JSONBスキーマ

```json
{
  "cry_episodes": [
    {
      "start_time": float,      // 開始時刻（秒）
      "end_time": float,        // 終了時刻（秒）
      "duration": float,        // 継続時間（秒）
      "confidence": float       // 信頼度（0.0-1.0）
    }
  ],
  "acoustic_features": {
    "episode_0": [
      {
        "time": float,          // 時刻（秒）
        "f0": float,            // 基本周波数（Hz）
        "f1": float,            // 第1フォルマント（Hz）
        "f2": float,            // 第2フォルマント（Hz）
        "f3": float,            // 第3フォルマント（Hz）
        "hnr": float,           // HNR（dB）
        "shimmer": float,       // シマー
        "jitter": float,        // ジッター
        "intensity": float      // 音響強度（dB）
      }
    ]
  },
  "statistics": {
    "episode_0": {
      "f0": {
        "mean": float,          // 平均
        "std": float,           // 標準偏差
        "min": float,           // 最小値
        "max": float,           // 最大値
        "median": float         // 中央値
      },
      // 他のパラメータも同様
      "duration": float,        // エピソード継続時間
      "num_frames": int         // フレーム数
    }
  },
  "cry_units": {
    "episode_0": {
      "units": [
        {
          "start_time": float,
          "end_time": float,
          "duration": float,
          "is_voiced": boolean,
          "mean_energy": float,
          "peak_frequency": float
        }
      ],
      "unit_count": int,
      "cryCE": float,           // Cry Expiratory Phase Ratio
      "unvoicedCE": float       // Unvoiced Cry Expiratory Phase Ratio
    }
  }
}
```

### 備考

- JSONBを使用することで、柔軟なスキーマと効率的なクエリを実現
- GINインデックスを使用して、JSONB内のキーによる検索を高速化可能

---

## 4. tags (タグテーブル)

ファイル分類用のタグマスタです。

### カラム定義

| カラム名 | 型 | NULL | デフォルト | 説明 |
|----------|-----|------|-----------|------|
| id | SERIAL | NO | - | 主キー |
| name | VARCHAR(100) | NO | - | タグ名 |
| created_at | TIMESTAMP WITH TIME ZONE | NO | CURRENT_TIMESTAMP | 作成日時 |

### 制約

- **PRIMARY KEY:** `id`
- **UNIQUE:** `name`

### インデックス

- `ix_tags_id` ON `id`
- `ix_tags_name` ON `name`

### 備考

- タグ名は重複不可
- ユーザー間で共有されるグローバルタグ

---

## 5. audio_file_tags (ファイルタグ関連テーブル)

音声ファイルとタグの多対多関連を管理します。

### カラム定義

| カラム名 | 型 | NULL | デフォルト | 説明 |
|----------|-----|------|-----------|------|
| audio_file_id | INTEGER | NO | - | 音声ファイルID（外部キー） |
| tag_id | INTEGER | NO | - | タグID（外部キー） |
| created_at | TIMESTAMP WITH TIME ZONE | NO | CURRENT_TIMESTAMP | 関連付け日時 |

### 制約

- **PRIMARY KEY:** (`audio_file_id`, `tag_id`)
- **FOREIGN KEY:** `audio_file_id` REFERENCES `audio_files(id)` ON DELETE CASCADE
- **FOREIGN KEY:** `tag_id` REFERENCES `tags(id)` ON DELETE CASCADE

### 備考

- 複合主キーにより、同じファイルに同じタグを重複して付けることを防止

---

## リレーションシップ詳細

### users → audio_files

- **種類:** 1対多
- **関係:** 1人のユーザーは複数のファイルをアップロード可能
- **削除時の動作:** ユーザー削除時、関連するファイルも削除（CASCADE）

### audio_files → analysis_results

- **種類:** 1対1
- **関係:** 1つのファイルに対して1つの解析結果
- **削除時の動作:** ファイル削除時、解析結果も削除（CASCADE）

### audio_files ←→ tags

- **種類:** 多対多
- **中間テーブル:** audio_file_tags
- **関係:** 1つのファイルに複数のタグ、1つのタグを複数のファイルに付与可能
- **削除時の動作:** ファイルまたはタグ削除時、関連レコードも削除（CASCADE）

---

## マイグレーション管理

本プロジェクトでは Alembic を使用してマイグレーションを管理しています。

### マイグレーションファイルの場所

```
backend/alembic/versions/
```

### マイグレーション履歴

| バージョン | 日付 | 説明 |
|-----------|------|------|
| 初期バージョン | 2024-01-01 | users, audio_files, analysis_results テーブル作成 |
| a02a7c0c0bf0 | 2024-01-01 | tags, audio_file_tags テーブル追加 |

### マイグレーションコマンド

```bash
# 新しいマイグレーションの作成
alembic revision --autogenerate -m "description"

# マイグレーションの適用
alembic upgrade head

# マイグレーションのロールバック
alembic downgrade -1

# 現在のバージョン確認
alembic current

# マイグレーション履歴表示
alembic history
```

---

## パフォーマンス最適化

### インデックス戦略

1. **頻繁に検索されるカラム:**
   - `users.email`
   - `audio_files.user_id`
   - `audio_files.status`
   - `analysis_results.audio_file_id`

2. **外部キー:**
   - すべての外部キーにインデックスを作成

3. **JSONB カラム (将来的な拡張):**
   ```sql
   CREATE INDEX idx_result_data_gin ON analysis_results USING gin(result_data);
   ```

### クエリ最適化のヒント

1. **N+1問題の回避:**
   ```python
   # Good: Eager Loading
   audio_files = db.query(AudioFile).options(joinedload(AudioFile.tags)).all()

   # Bad: N+1 Query
   audio_files = db.query(AudioFile).all()
   for f in audio_files:
       tags = f.tags  # 各ファイルごとにクエリ発行
   ```

2. **大量データの取得:**
   ```python
   # ページネーションの使用
   files = db.query(AudioFile).offset(skip).limit(limit).all()
   ```

3. **JSONB検索の最適化:**
   ```python
   # JSONBパスを使った検索
   results = db.query(AnalysisResult).filter(
       AnalysisResult.result_data['cry_episodes'].contains([{'confidence': 0.9}])
   ).all()
   ```

---

## バックアップ戦略

### 推奨バックアップ方法

1. **pg_dump を使用した論理バックアップ:**
   ```bash
   pg_dump -U user -d baby_cry_db -F c -f backup_$(date +%Y%m%d).dump
   ```

2. **ポイントインタイムリカバリ用のWALアーカイブ:**
   ```sql
   -- postgresql.confで設定
   wal_level = replica
   archive_mode = on
   archive_command = 'cp %p /path/to/archive/%f'
   ```

3. **バックアップ頻度:**
   - フルバックアップ: 毎日深夜
   - WALアーカイブ: リアルタイム

---

## セキュリティ考慮事項

1. **パスワードのハッシュ化:**
   - bcrypt を使用（ストレッチング回数: 12）

2. **SQLインジェクション対策:**
   - ORMの使用（SQLAlchemy）
   - パラメータ化クエリの徹底

3. **アクセス制御:**
   - データベースユーザーの権限を最小限に
   - 本番環境では専用DBユーザーを使用

4. **暗号化:**
   - 本番環境では SSL/TLS 接続を必須化
   - 機密データの暗号化（必要に応じて）

---

## 開発環境でのデータベースセットアップ

### Docker を使用する場合

```bash
docker run --name postgres-baby-cry \
  -e POSTGRES_USER=dev_user \
  -e POSTGRES_PASSWORD=dev_password \
  -e POSTGRES_DB=baby_cry_db \
  -p 5432:5432 \
  -v postgres_data:/var/lib/postgresql/data \
  -d postgres:14
```

### 直接インストールする場合

```bash
# PostgreSQLのインストール
sudo apt install postgresql-14

# データベースの作成
sudo -u postgres createdb baby_cry_db

# ユーザーの作成
sudo -u postgres createuser dev_user
sudo -u postgres psql -c "ALTER USER dev_user WITH PASSWORD 'dev_password';"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE baby_cry_db TO dev_user;"
```

---

## トラブルシューティング

### 接続エラー

```bash
# PostgreSQLの起動確認
sudo systemctl status postgresql

# 接続テスト
psql -h localhost -U dev_user -d baby_cry_db
```

### マイグレーションエラー

```bash
# マイグレーション状態の確認
alembic current

# 手動でのマイグレーション適用
alembic upgrade head

# 問題がある場合はロールバック
alembic downgrade -1
```

### パフォーマンス問題

```sql
-- スロークエリの確認
SELECT query, calls, total_time, mean_time
FROM pg_stat_statements
ORDER BY mean_time DESC
LIMIT 10;

-- インデックスの使用状況確認
SELECT schemaname, tablename, indexname, idx_scan, idx_tup_read, idx_tup_fetch
FROM pg_stat_user_indexes
ORDER BY idx_scan;
```

---

## 付録: SQLスキーマ定義

完全なスキーマ定義は Alembic マイグレーションファイルを参照してください。

```
backend/alembic/versions/
```
