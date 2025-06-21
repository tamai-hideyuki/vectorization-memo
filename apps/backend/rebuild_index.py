import json
import faiss
from pathlib import Path
from embedding import build_index

def main():
    # インデックス生成
    idx, metas = build_index()
    # 保存先設定
    base = Path(__file__).resolve().parent.parent / "memos"
    out_idx = base / "index.faiss"
    out_meta = base / "metas.json"

    # FAISS インデックス書き出し
    faiss.write_index(idx, str(out_idx))
    # メタ情報書き出し
    with open(out_meta, "w", encoding="utf-8") as f:
        json.dump(metas, f, ensure_ascii=False, indent=2)

    print(f"インデックス再構築完了: {idx.ntotal} ベクトルを '{out_idx}' に保存しました。")

if __name__ == "__main__":
    main()
