from pathlib import Path
import numpy as np
import faiss
from sentence_transformers import SentenceTransformer


def build_index(
    root_dir: str = None,
    model_name: str = "sentence-transformers/LaBSE",
    chunk_token_size: int = 300,
    batch_size: int = 8
):
    """
    ・ディレクトリ以下の .txt を読み込み
    ・YAML Front Matter 等をスキップして本文のみ抽出
    ・トークン数ベースでチャンク化 (chunk_token_sizeトークンごと)
    ・LaBSE 埋め込み計算 + L2 正規化
    ・FAISS IndexFlatIP に登録して返却
    """
    # 1) モデルロード
    model = SentenceTransformer(model_name)

    # 2) メモ格納パス
    base = Path(root_dir) if root_dir else Path(__file__).resolve().parent.parent / "memos"
    if not base.exists():
        raise FileNotFoundError(f"Memos directory not found: {base}")

    chunks, metas = [], []
    for cat in sorted(base.iterdir()):
        if not cat.is_dir():
            continue
        for file in sorted(cat.glob("*.txt")):
            text = file.read_text(encoding="utf-8")
            # YAML Front Matter を除去
            if text.startswith("---"):
                _, _, text = text.split("---", 2)

            # トークン分割によるチャンク化
            tokens = text.split()
            for i in range(0, len(tokens), chunk_token_size):
                chunk = " ".join(tokens[i : i + chunk_token_size])
                chunks.append(chunk)
                metas.append({
                    "category": cat.name,
                    "filename": file.name,
                    "offset": i,
                })

    # 3) 埋め込み計算
    embeddings = model.encode(
        chunks,
        batch_size=batch_size,
        convert_to_numpy=True,
        normalize_embeddings=False
    )

    # 4) L2 正規化
    norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
    embeddings = embeddings / np.clip(norms, a_min=1e-12, a_max=None)

    # 5) FAISS インデックス作成
    dim = embeddings.shape[1]
    index = faiss.IndexFlatIP(dim)
    index.add(embeddings)

    return index, metas

if __name__ == "__main__":
    idx, metas = build_index()
    print(f"{idx.ntotal} ベクトルで FAISS インデックスを構築しました。")
