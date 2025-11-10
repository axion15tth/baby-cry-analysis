# 赤ちゃん泣き声解析システム - フロントエンド

## 概要

React + TypeScript + Vite で構築されたWebアプリケーション。赤ちゃんの泣き声を解析し、エピソードと音響特徴を可視化します。

## アクセス

**開発サーバー**: http://localhost:5173/

## 機能

### 認証機能
- ユーザー登録
- ログイン/ログアウト
- JWT認証（自動付与）

### ファイル管理
- 音声ファイルアップロード（WAV等）
- ファイル一覧表示
- ステータス管理（uploaded / processing / completed / failed）

### 解析機能
- 解析開始
- リアルタイムステータス監視（5秒ごと自動ポーリング）
- 解析結果表示
  - 泣き声エピソード一覧（開始時刻、終了時刻、継続時間、信頼度）
  - 統計サマリー（総エピソード数、総泣き時間）

### エクスポート機能
- Excel形式（3シート：概要、エピソード、音響特徴）
- PDF形式（レポート）

## 技術スタック

- **React 18** - UIライブラリ
- **TypeScript 5** - 型安全性
- **Vite 7** - 高速ビルドツール
- **React Router DOM 7** - SPAルーティング
- **Axios 1.7** - HTTP クライアント
- **Recharts 2.15** - グラフ表示ライブラリ

## セットアップ

### 依存パッケージのインストール

```bash
npm install
```

### 開発サーバー起動

```bash
npm run dev
```

アクセス: http://localhost:5173/

### ビルド

```bash
npm run build
```

ビルド成果物: `dist/` ディレクトリ

### プレビュー（本番ビルドの確認）

```bash
npm run preview
```

## プロジェクト構造

```
frontend/
├── src/
│   ├── api/
│   │   └── client.ts          # APIクライアント（axios）
│   ├── contexts/
│   │   └── AuthContext.tsx    # 認証コンテキスト（JWT管理）
│   ├── pages/
│   │   ├── LoginPage.tsx      # ログインページ
│   │   ├── RegisterPage.tsx   # 登録ページ
│   │   └── DashboardPage.tsx  # ダッシュボード（メイン画面）
│   ├── types/
│   │   └── index.ts           # TypeScript型定義
│   ├── App.tsx                # ルーティング設定
│   └── main.tsx               # エントリーポイント
├── package.json
├── vite.config.ts             # Vite設定
└── tsconfig.json
```

## バックエンド連携

**API URL**: http://localhost:8000

### エンドポイント

#### 認証
- `POST /api/v1/auth/register` - ユーザー登録
- `POST /api/v1/auth/login` - ログイン
- `GET /api/v1/auth/me` - 現在のユーザー情報

#### ファイル管理
- `POST /api/v1/files/upload` - ファイルアップロード
- `GET /api/v1/files/` - ファイル一覧
- `GET /api/v1/files/{id}` - ファイル詳細
- `DELETE /api/v1/files/{id}` - ファイル削除

#### 解析
- `POST /api/v1/analysis/start` - 解析開始
- `GET /api/v1/analysis/status/{id}` - ステータス確認
- `GET /api/v1/analysis/results/{id}` - 結果取得

#### エクスポート
- `GET /api/v1/export/csv/episodes/{id}` - CSV出力（エピソード）
- `GET /api/v1/export/excel/{id}` - Excel出力
- `GET /api/v1/export/pdf/{id}` - PDF出力

## 使い方

### 1. アカウント登録

1. 「アカウントをお持ちでない方はこちら」をクリック
2. メールアドレスとパスワード（6文字以上）を入力
3. 「登録」ボタンをクリック → 自動ログイン

### 2. ファイルアップロード

1. ダッシュボードの「ファイルを選択」をクリック
2. 音声ファイル（WAV等）を選択
3. 自動的にアップロード開始

### 3. 解析実行

1. ファイル一覧から「解析開始」ボタンをクリック
2. ステータスが「processing」に変化
3. 自動的に5秒ごとにポーリングで進捗監視
4. 完了すると「completed」に変化

### 4. 結果確認

1. 「結果表示」ボタンをクリック
2. 画面下部に解析結果が表示
   - 泣き声エピソード一覧テーブル
   - 統計サマリー

### 5. エクスポート

1. 「Excel」または「PDF」ボタンをクリック
2. ファイルが自動ダウンロード

## 注意事項

- バックエンドAPIが http://localhost:8000 で起動している必要があります
- JWTトークンはlocalStorageに保存されます（セキュリティ注意）
- 解析中は5秒ごとに自動的にステータスをポーリングします
- CORSが設定されているため、異なるオリジンからのアクセスは制限されます
