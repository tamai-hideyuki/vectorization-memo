#!/usr/bin/env python3

from pathlib import Path
import os
try:
    os.nice(10)
except Exception:
    pass
os.environ["OMP_NUM_THREADS"] = "1"
os.environ["MKL_NUM_THREADS"] = "1"

import json
import numpy as np
import faiss
import torch
from sentence_transformers import SentenceTransformer

# torch スレッド設定
torch.set_num_threads(1)
torch.set_num_interop_threads(1)


def build_index(
    root_dir: str = None,
    model_name: str = "sentence-transformers/LaBSE",
    chunk_token_size: int = 300,
    batch_size: int = 8
):
    """
    ・プロジェクトルートの memos/ 以下の .txt を読み込み
    ・YAML Front Matter をスキップ
    ・トークン数ベースでチャンク化
    ・LaBSE 埋め込み + L2 正規化
    ・FAISS IndexFlatIP を構築して返却
    """
    # モデルロード + DataLoader 並列抑制
    model = SentenceTransformer(model_name)
    model._cpu_count = 0

    # メモ格納パス (project_root/memos)
    base = Path(root_dir) if root_dir else Path(__file__).resolve().parent.parent.parent / "memos"
    if not base.exists():
        raise FileNotFoundError(f"Memos directory not found: {base}")

    chunks, metas = [], []
    for cat in sorted(base.iterdir()):
        if not cat.is_dir():
            continue
        for file in sorted(cat.glob("*.txt")):
            text = file.read_text(encoding="utf-8")
            if text.startswith("---"):
                _, _, text = text.split("---", 2)
            tokens = text.split()
            for i in range(0, len(tokens), chunk_token_size):
                chunk = " ".join(tokens[i:i+chunk_token_size])
                chunks.append(chunk)
                metas.append({"category": cat.name, "filename": file.name, "offset": i})

    # 埋め込み計算
    embeddings = model.encode(
        chunks,
        batch_size=batch_size,
        convert_to_numpy=True,
        normalize_embeddings=False
    )

    # L2 正規化
    norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
    embeddings = embeddings / np.clip(norms, a_min=1e-12, a_max=None)

    # FAISS インデックス作成
    dim = embeddings.shape[1]
    index = faiss.IndexFlatIP(dim)
    index.add(embeddings)

    return index, metas


if __name__ == "__main__":
    # インデックス構築 + 永続化
    idx, metas = build_index()
    out_dir = Path(__file__).resolve().parent.parent.parent / "memos"
    out_dir.mkdir(parents=True, exist_ok=True)

    # FAISS インデックスを保存
    faiss.write_index(idx, str(out_dir / "index.faiss"))
    # メタ情報を保存
    with open(out_dir / "metas.json", "w", encoding="utf-8") as f:
        json.dump(metas, f, ensure_ascii=False, indent=2)

    print(f"{idx.ntotal} 個のベクトルを構築し、'{out_dir}' に保存しました")