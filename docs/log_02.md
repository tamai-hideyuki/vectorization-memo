- 記入: apps/backend/requirements.txt
- 記入: apps/backend/main.py
- 仮想環境を作成＆有効化 `python3 -m venv .venv` & `source .venv/bin/activate`
- Backend ディレクトリへ移動
- 依存パッケージをインストール: Backend ディレクトリで実行`pip install -r requirements.txt`
- requirements.txt にタイプミス: `unicorn` → `uvicorn`
- ファイルを保存し、再度インストール： `pip install -r requirements.txt`
- サーバ起動： `uvicorn main:app --reload --host 0.0.0.0 --port 8000`

