# デプロイガイド

このドキュメントでは、Baby Cry Analysis Systemをクラウド環境にデプロイする手順を説明します。

## Render でのデプロイ（推奨）

Renderは無料プランでPostgreSQL、Redis、Webサービスを提供しており、このプロジェクトに最適です。

### 前提条件

- GitHubアカウント
- Renderアカウント（https://render.com で無料登録）
- このプロジェクトがGitHubにpush済みであること

### デプロイ手順

#### 1. Renderにサインイン

https://dashboard.render.com にアクセスしてログイン

#### 2. GitHubリポジトリを接続

1. "New +" ボタンをクリック
2. "Blueprint" を選択
3. GitHubリポジトリ `baby-cry-analysis` を選択
4. `render.yaml` が自動的に検出されます

#### 3. 環境変数の設定

以下の環境変数が自動的に設定されますが、必要に応じて調整してください：

**バックエンド:**
- `DATABASE_URL`: PostgreSQLデータベースURL（自動設定）
- `REDIS_URL`: RedisURL（自動設定）
- `SECRET_KEY`: JWT署名用のシークレットキー（自動生成）
- `ALGORITHM`: HS256（自動設定）
- `ACCESS_TOKEN_EXPIRE_MINUTES`: 1440（自動設定）
- `ALLOWED_ORIGINS`: フロントエンドのURL（要更新）

**フロントエンド:**
- `VITE_API_URL`: バックエンドAPIのURL（要設定）

#### 4. デプロイ開始

"Apply" ボタンをクリックしてデプロイを開始します。

#### 5. デプロイ完了後

デプロイが完了すると、以下のURLが生成されます：

- **フロントエンド:** `https://baby-cry-frontend.onrender.com`
- **バックエンド:** `https://baby-cry-backend.onrender.com`

#### 6. CORS設定の更新

バックエンドの環境変数 `ALLOWED_ORIGINS` をフロントエンドのURLに更新：

```
ALLOWED_ORIGINS=https://baby-cry-frontend.onrender.com
```

#### 7. フロントエンドのAPI URL設定

フロントエンドの環境変数 `VITE_API_URL` をバックエンドのURLに設定：

```
VITE_API_URL=https://baby-cry-backend.onrender.com
```

### 注意事項

#### 無料プランの制限

- **スリープ:** 15分間アクセスがないとサービスがスリープします
- **起動時間:** スリープから復帰するのに約30秒かかります
- **データベース:** 無料プランは90日間のデータ保持制限があります
- **Redis:** 無料プランは25MBまで

#### Celeryについて

Renderの無料プランでは、Celeryワーカーを別サービスとして動作させることができません。
デモ用途の場合は、音声解析を同期処理に切り替えることを推奨します。

### トラブルシューティング

#### ビルドエラー

requirements.txtの依存関係が大きいため、ビルドに時間がかかります。
特にtorchやlibrosaのインストールに時間がかかる場合があります。

#### メモリ不足

無料プランはメモリ512MBの制限があります。
大きなファイルの解析時にメモリ不足が発生する可能性があります。

## 代替デプロイオプション

### Railway

1. https://railway.app にアクセス
2. GitHubリポジトリを接続
3. 環境変数を設定
4. デプロイ

### Vercel (フロントエンドのみ)

1. https://vercel.com にアクセス
2. GitHubリポジトリを接続
3. Build Command: `cd frontend && npm run build`
4. Output Directory: `frontend/dist`
5. 環境変数 `VITE_API_URL` を設定

### Heroku

1. Herokuアカウントを作成
2. Heroku CLIをインストール
3. 以下のコマンドを実行：

```bash
heroku create baby-cry-backend
heroku addons:create heroku-postgresql:essential-0
heroku addons:create heroku-redis:mini
heroku config:set SECRET_KEY=$(openssl rand -hex 32)
git push heroku main
```

## 本番環境のベストプラクティス

### セキュリティ

1. **環境変数の保護**
   - SECRET_KEYは強力なランダム文字列を使用
   - データベース認証情報を安全に管理

2. **HTTPS**
   - 本番環境では必ずHTTPSを使用

3. **CORS設定**
   - 許可するオリジンを明示的に指定

### パフォーマンス

1. **データベース**
   - インデックスを適切に設定
   - 定期的なバックアップ

2. **ファイルストレージ**
   - 大きな音声ファイルはS3やCloudinaryに保存

3. **キャッシング**
   - Redisを活用したキャッシング戦略

### モニタリング

1. **ログ**
   - アプリケーションログの監視
   - エラートラッキング（Sentry等）

2. **メトリクス**
   - レスポンスタイムの監視
   - エラーレートの監視

## サポート

デプロイに関する問題は、GitHubのIssuesセクションで報告してください。
