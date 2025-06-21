#!/usr/bin/env python
import json
import faiss
from pathlib import Path

# 同じディレクトリ内の embedding.py を参照
from embedding import build_index

def main():
    # 1) インデックス生成
    idx, metas = build_index()

    # 2) 保存先ディレクトリ
    base = Path(__file__).resolve().parent / "memos"
    base.mkdir(parents=True, exist_ok=True)
    out_idx = base / "index.faiss"
    out_meta = base / "metas.json"

    # 3) FAISS インデックスを書き出し
    faiss.write_index(idx, str(out_idx))

    # 4) メタ情報を書き出し
    with open(out_meta, "w", encoding="utf-8") as f:
        json.dump(metas, f, ensure_ascii=False, indent=2)

    print(f"インデックス再構築完了: {idx.ntotal} vectors saved to '{out_idx}' and metas to '{out_meta}'.")

if __name__ == "__main__":
    main()
