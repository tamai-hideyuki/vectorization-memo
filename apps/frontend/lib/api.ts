import {Result} from "./types";

/** 汎用 POST ヘルパー */
async function postForm<T>(path: string, form: FormData): Promise<T> {
    const res = await fetch(path, {
        method: 'POST',
        body: form,
    })
    if (!res.ok) throw new Error(`HTTP ${res.status}: ${res.statusText}`)
    return res.json()
}

/** 全メモ取得（完全一致検索で使う） */
export async function listMemos(): Promise<Result[]> {
    // 例えば /api/search に空クエリ投げて全件返すようにサーバーを調整してあるならこう書く
    const form = new FormData()
    form.append('query', '')
    const data = await postForm<{ results: Result[] }>('/api/search', form)
    return data.results
}

/** メモ作成 */
export function createMemo(/*…*/){ /* unchanged */ }

/** セマンティック検索（無制限返却） */
export function searchMemos(query: string) {
    const form = new FormData()
    form.append('query', query)
    return postForm<{ results: Result[] }>('/api/search', form)
        .then(r => r.results)
}
