- 追記: apps/backend/requirements.txt
  - 理由: SentenceTransformer と FAISS が使えるようにするため
- cd apps/backend
  - `pip install -r requirements.txt` (必要なライブラリのインストール)
- 作成: apps/backend/embedding.py
- 修正: main.py
  - 起動時に memos/index.faiss と memos/metas.json を読み込むロジックを追加
  - LaBSE モデルでクエリを埋め込み＋正規化し /api/search で内積検索を行うエンドポイントを実装
- 問題: macOS (Apple Silicon) × Python 3.13 環境では、PyPI にある faiss-cpu wheel が正式対応しておらず、index.add() や faiss.read_index() 呼び出し時に SIGSEGV が発生
  - 対応方法: Python 3.11 環境に切り替える `brew install pyenv` && `pyenv install 3.11.9` && `pyenv local 3.11.9`      # このプロジェクトだけ 3.11 を有効化する。
  - venv を作り直して依存を再インストール: `python3 -m venv .venv` && `source .venv/bin/activate` && `pip install -r apps/backend/requirements.txt`
- `python3 embedding.py` を実行しベクトル構築成功
- API 連携テスト
```bash
cd apps/backend
source .venv/bin/activate   # 仮想環境有効化済みの場合
uvicorn main:app --reload --port 8000
```
- インデックス読み込み確認
  - サーバ開始ログにエラーが出ないことを確認
- curl で検索リクエスト
```bash
curl -X POST http://localhost:8000/api/search \
  -F 'query=テスト' \
  -F 'k=3' 
```
**HTTP 200 が返り、results 配列と各要素に category, filename, offset, score があること**

- Swagger UI で動作確認
- ブラウザで http://localhost:8000/docs にアクセス
- POST /api/search を選択
- パラメータ入力
  - query: 任意の検索語句（例: テスト）
  - k : ヒット数（例: 3）
- Execute を押下
  - レスポンスに正しく results が表示されること

- README.mdに追記
```bash
## インデックス生成

```bash
# プロジェクトルートから実行
python3 apps/backend/embedding.py 
```

**これで memos/index.faiss と memos/metas.json が生成される**

- 検索エンドポイント
```bash
# FastAPI サーバ起動
uvicorn apps/backend/main:app --reload --port 8000

# 検索例 (curl)
curl -X POST http://localhost:8000/api/search \
  -F 'query=検索ワード' \
  -F 'k=5'
```
**レスポンスは JSON の results 配列で返却されます。各要素に category, filename, offset, score が含まれます。**

