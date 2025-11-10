# API仕様書

Baby Cry Analysis System API v1.0

## 基本情報

- **ベースURL:** `http://localhost:8000/api/v1`
- **認証方式:** JWT Bearer Token
- **コンテンツタイプ:** `application/json` (ファイルアップロードを除く)

## 認証

### トークンの取得

APIを使用するには、まずログインしてトークンを取得する必要があります。

```http
POST /auth/login
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "password123"
}
```

レスポンス:
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer",
  "user": {
    "id": 1,
    "email": "user@example.com",
    "role": "user",
    "created_at": "2024-01-01T00:00:00Z"
  }
}
```

### トークンの使用

取得したトークンを`Authorization`ヘッダーに含めてリクエストします。

```http
GET /audio-files/
Authorization: Bearer eyJhbGciOiJIUzI1NiIs...
```

---

## エンドポイント一覧

### 1. 認証API (`/auth`)

#### 1.1 ユーザー登録

```http
POST /auth/register
```

**リクエストボディ:**
```json
{
  "email": "user@example.com",
  "password": "password123",
  "role": "user"  // オプション: "user" または "researcher"
}
```

**レスポンス:** `201 Created`
```json
{
  "id": 1,
  "email": "user@example.com",
  "role": "user",
  "created_at": "2024-01-01T00:00:00Z"
}
```

#### 1.2 ログイン

```http
POST /auth/login
```

**リクエストボディ:**
```json
{
  "email": "user@example.com",
  "password": "password123"
}
```

**レスポンス:** `200 OK`
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer",
  "user": {
    "id": 1,
    "email": "user@example.com",
    "role": "user",
    "created_at": "2024-01-01T00:00:00Z"
  }
}
```

#### 1.3 現在のユーザー情報取得

```http
GET /auth/me
Authorization: Bearer <token>
```

**レスポンス:** `200 OK`
```json
{
  "id": 1,
  "email": "user@example.com",
  "role": "user",
  "created_at": "2024-01-01T00:00:00Z"
}
```

---

### 2. ファイル管理API (`/audio-files`)

#### 2.1 ファイルアップロード

```http
POST /audio-files/upload
Authorization: Bearer <token>
Content-Type: multipart/form-data
```

**フォームデータ:**
- `file` (required): 音声ファイル (.wav, .mp3, .flac, .m4a, .ogg)
- `recording_start_time` (optional): 録音開始時刻 (ISO 8601形式)

**レスポンス:** `201 Created`
```json
{
  "message": "File uploaded successfully",
  "file": {
    "id": 1,
    "user_id": 1,
    "filename": "uuid.wav",
    "original_filename": "baby_cry.wav",
    "file_path": "/storage/audio/uuid.wav",
    "file_size": 1048576,
    "sample_rate": 44100,
    "duration": 30.5,
    "recording_start_time": "2024-01-01T10:00:00Z",
    "status": "uploaded",
    "uploaded_at": "2024-01-01T11:00:00Z",
    "tags": []
  }
}
```

#### 2.2 一括ファイルアップロード

```http
POST /audio-files/upload/batch
Authorization: Bearer <token>
Content-Type: multipart/form-data
```

**フォームデータ:**
- `files` (required): 音声ファイル配列（最大10ファイル）
- `recording_start_times` (optional): 録音開始時刻の配列

**レスポンス:** `201 Created`
```json
{
  "message": "Successfully uploaded 3 files",
  "files": [ /* AudioFileオブジェクトの配列 */ ],
  "errors": null  // エラーがあればここに配列として記録
}
```

#### 2.3 ファイル一覧取得

```http
GET /audio-files/?skip=0&limit=100
Authorization: Bearer <token>
```

**クエリパラメータ:**
- `skip` (optional): スキップする件数（デフォルト: 0）
- `limit` (optional): 取得する最大件数（デフォルト: 100）

**レスポンス:** `200 OK`
```json
{
  "total": 5,
  "files": [
    {
      "id": 1,
      "user_id": 1,
      "filename": "uuid.wav",
      "original_filename": "baby_cry.wav",
      "file_path": "/storage/audio/uuid.wav",
      "file_size": 1048576,
      "sample_rate": 44100,
      "duration": 30.5,
      "recording_start_time": "2024-01-01T10:00:00Z",
      "status": "completed",
      "uploaded_at": "2024-01-01T11:00:00Z",
      "tags": [
        {
          "id": 1,
          "name": "夜泣き",
          "created_at": "2024-01-01T00:00:00Z"
        }
      ]
    }
  ]
}
```

#### 2.4 ファイル詳細取得

```http
GET /audio-files/{file_id}
Authorization: Bearer <token>
```

**レスポンス:** `200 OK`
```json
{
  "id": 1,
  "user_id": 1,
  "filename": "uuid.wav",
  "original_filename": "baby_cry.wav",
  "file_path": "/storage/audio/uuid.wav",
  "file_size": 1048576,
  "sample_rate": 44100,
  "duration": 30.5,
  "recording_start_time": "2024-01-01T10:00:00Z",
  "status": "completed",
  "uploaded_at": "2024-01-01T11:00:00Z",
  "tags": []
}
```

#### 2.5 ファイル情報更新

```http
PATCH /audio-files/{file_id}
Authorization: Bearer <token>
Content-Type: application/json
```

**リクエストボディ:**
```json
{
  "recording_start_time": "2024-01-01T10:00:00Z",
  "status": "completed"
}
```

**レスポンス:** `200 OK`
```json
{
  "id": 1,
  /* ... 更新されたファイル情報 */
}
```

#### 2.6 ファイル削除

```http
DELETE /audio-files/{file_id}
Authorization: Bearer <token>
```

**レスポンス:** `204 No Content`

#### 2.7 ファイルストリーミング/ダウンロード

```http
GET /audio-files/{file_id}/stream
Authorization: Bearer <token>
```

**レスポンス:** `200 OK`
- Content-Type: `audio/wav` (または対応する形式)
- Content-Disposition: `attachment; filename="original_filename.wav"`

---

### 3. 音声解析API (`/analysis`)

#### 3.1 解析開始

```http
POST /analysis/{file_id}/start
Authorization: Bearer <token>
```

**レスポンス:** `200 OK`
```json
{
  "message": "Analysis started",
  "task_id": "abc123-def456-...",
  "file_id": 1
}
```

#### 3.2 解析状態確認

```http
GET /analysis/{file_id}/status
Authorization: Bearer <token>
```

**レスポンス:** `200 OK`
```json
{
  "file_id": 1,
  "status": "processing",
  "message": "エピソード検出中...",
  "progress": 50,
  "task_id": "abc123-def456-..."
}
```

**ステータス値:**
- `uploaded`: 未解析
- `processing`: 解析中
- `completed`: 完了
- `failed`: 失敗

#### 3.3 解析結果取得

```http
GET /analysis/{file_id}/result
Authorization: Bearer <token>
```

**レスポンス:** `200 OK`
```json
{
  "id": 1,
  "audio_file_id": 1,
  "result_data": {
    "cry_episodes": [
      {
        "start_time": 5.2,
        "end_time": 8.7,
        "duration": 3.5,
        "confidence": 0.95
      }
    ],
    "acoustic_features": {
      "episode_0": [
        {
          "time": 5.2,
          "f0": 450.5,
          "f1": 1200.3,
          "f2": 2800.1,
          "f3": 3500.7,
          "hnr": 12.5,
          "shimmer": 0.08,
          "jitter": 0.02,
          "intensity": 75.3
        }
      ]
    },
    "statistics": {
      "episode_0": {
        "f0": {
          "mean": 450.5,
          "std": 50.2,
          "min": 380.0,
          "max": 520.0,
          "median": 445.0
        },
        "duration": 3.5,
        "num_frames": 150
      }
    },
    "cry_units": {
      "episode_0": {
        "units": [
          {
            "start_time": 5.2,
            "end_time": 5.8,
            "duration": 0.6,
            "is_voiced": true,
            "mean_energy": 0.75,
            "peak_frequency": 450.0
          }
        ],
        "unit_count": 5,
        "cryCE": 0.85,
        "unvoicedCE": 0.15
      }
    }
  },
  "analyzed_at": "2024-01-01T12:00:00Z"
}
```

---

### 4. エクスポートAPI (`/export`)

#### 4.1 CSV形式でエクスポート

```http
GET /export/{file_id}/csv
Authorization: Bearer <token>
```

**レスポンス:** `200 OK`
- Content-Type: `text/csv`
- Content-Disposition: `attachment; filename="analysis_results_{file_id}.csv"`

#### 4.2 JSON形式でエクスポート

```http
GET /export/{file_id}/json
Authorization: Bearer <token>
```

**レスポンス:** `200 OK`
- Content-Type: `application/json`
- Content-Disposition: `attachment; filename="analysis_results_{file_id}.json"`

---

### 5. 可視化API (`/visualization`)

#### 5.1 波形データ取得

```http
GET /visualization/{file_id}/waveform
Authorization: Bearer <token>
```

**レスポンス:** `200 OK`
```json
{
  "times": [0.0, 0.01, 0.02, ...],
  "amplitudes": [0.01, -0.02, 0.03, ...],
  "sample_rate": 44100,
  "duration": 30.5
}
```

#### 5.2 スペクトログラムデータ取得

```http
GET /visualization/{file_id}/spectrogram
Authorization: Bearer <token>
```

**レスポンス:** `200 OK`
```json
{
  "spectrogram": [[...]],  // 2D配列
  "times": [0.0, 0.01, ...],
  "frequencies": [0, 50, 100, ...]
}
```

---

### 6. ユーザー管理API (`/users`)

#### 6.1 ユーザー一覧取得 (研究者のみ)

```http
GET /users/?skip=0&limit=100
Authorization: Bearer <token>
```

**レスポンス:** `200 OK`
```json
{
  "total": 10,
  "users": [
    {
      "id": 1,
      "email": "user@example.com",
      "role": "user",
      "created_at": "2024-01-01T00:00:00Z"
    }
  ]
}
```

#### 6.2 ユーザー情報取得

```http
GET /users/{user_id}
Authorization: Bearer <token>
```

**レスポンス:** `200 OK`
```json
{
  "id": 1,
  "email": "user@example.com",
  "role": "user",
  "created_at": "2024-01-01T00:00:00Z"
}
```

---

### 7. タグ管理API (`/tags`)

#### 7.1 タグ一覧取得

```http
GET /tags/?skip=0&limit=100
Authorization: Bearer <token>
```

**レスポンス:** `200 OK`
```json
{
  "total": 5,
  "tags": [
    {
      "id": 1,
      "name": "夜泣き",
      "created_at": "2024-01-01T00:00:00Z"
    },
    {
      "id": 2,
      "name": "昼間",
      "created_at": "2024-01-01T00:00:00Z"
    }
  ]
}
```

#### 7.2 タグ作成

```http
POST /tags/
Authorization: Bearer <token>
Content-Type: application/json
```

**リクエストボディ:**
```json
{
  "name": "新しいタグ"
}
```

**レスポンス:** `201 Created`
```json
{
  "id": 3,
  "name": "新しいタグ",
  "created_at": "2024-01-01T00:00:00Z"
}
```

#### 7.3 タグ削除

```http
DELETE /tags/{tag_id}
Authorization: Bearer <token>
```

**レスポンス:** `204 No Content`

#### 7.4 ファイルのタグ一括更新

```http
PUT /tags/{file_id}/tags
Authorization: Bearer <token>
Content-Type: application/json
```

**リクエストボディ:**
```json
{
  "tag_ids": [1, 2, 3]
}
```

**レスポンス:** `200 OK`
```json
[
  {
    "id": 1,
    "name": "夜泣き",
    "created_at": "2024-01-01T00:00:00Z"
  },
  {
    "id": 2,
    "name": "昼間",
    "created_at": "2024-01-01T00:00:00Z"
  }
]
```

#### 7.5 ファイルにタグ追加

```http
POST /tags/{file_id}/tags/{tag_id}
Authorization: Bearer <token>
```

**レスポンス:** `200 OK`
```json
[
  /* 更新後のタグ一覧 */
]
```

#### 7.6 ファイルからタグ削除

```http
DELETE /tags/{file_id}/tags/{tag_id}
Authorization: Bearer <token>
```

**レスポンス:** `200 OK`
```json
[
  /* 更新後のタグ一覧 */
]
```

---

## エラーレスポンス

### 一般的なエラーフォーマット

```json
{
  "detail": "エラーメッセージ"
}
```

### HTTPステータスコード

| コード | 説明 |
|--------|------|
| 200 | 成功 |
| 201 | 作成成功 |
| 204 | 成功（コンテンツなし） |
| 400 | リクエストが不正 |
| 401 | 認証が必要 |
| 403 | アクセス権限なし |
| 404 | リソースが見つからない |
| 413 | ファイルサイズが大きすぎる |
| 422 | バリデーションエラー |
| 500 | サーバーエラー |

### バリデーションエラーの例

```json
{
  "detail": [
    {
      "loc": ["body", "email"],
      "msg": "value is not a valid email address",
      "type": "value_error.email"
    }
  ]
}
```

---

## レート制限

現在、レート制限は実装されていません。将来的に追加される可能性があります。

---

## ファイルサイズ制限

- 最大ファイルサイズ: 100MB (設定により変更可能)
- 一括アップロード: 最大10ファイル

---

## 対応音声形式

- WAV (.wav)
- MP3 (.mp3)
- FLAC (.flac)
- M4A (.m4a)
- OGG (.ogg)

---

## Swagger UIドキュメント

APIの対話的なドキュメントは以下のURLで利用可能です：

- **Swagger UI:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc

---

## バージョン履歴

### v1.0.0 (2024-01-01)
- 初回リリース
- 基本的なファイル管理機能
- 音声解析機能
- 可視化API
- タグ管理機能
