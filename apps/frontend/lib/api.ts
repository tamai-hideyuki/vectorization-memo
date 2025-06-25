import { Result } from './types'

/** メモ作成／検索で使うペイロードの共通型 */
export type MemoPayload = Record<string, string>

/** バックエンドから既存リストを取得 */

export async function getCategories(): Promise<string[]> {
    const res = await fetch('/api/categories');
    if (!res.ok) throw new Error('カテゴリ取得失敗');
    return res.json();
}
export async function getTags(): Promise<string[]> {
    const res = await fetch('/api/tags');
    if (!res.ok) throw new Error('タグ取得失敗');
    return res.json();
}


/** NEXT_PUBLIC_API_BASE_URL をビルド時に埋め込む */
const API_BASE = (() => {
    const base = process.env.NEXT_PUBLIC_API_BASE_URL
    if (!base) throw new Error('NEXT_PUBLIC_API_BASE_URL が設定されていません')
    // 末尾のスラッシュを除去
    return base.replace(/\/+$/, '')
})()

/**
 * 汎用 POST ヘルパー
 * - endpoint: `/api/memo` のように先頭スラッシュ付きで指定
 * - payload: 文字列同士のキー／バリューペア
 */
async function postForm<T>(endpoint: string, payload: MemoPayload): Promise<T> {
    const url = `${API_BASE}${endpoint}`
    const form = new FormData()
    Object.entries(payload).forEach(([key, val]) => form.append(key, val))

    const res = await fetch(url, {
        method: 'POST',
        body: form,
    })
    if (!res.ok) throw new Error(`HTTP ${res.status}: ${res.statusText}`)
    return res.json()
}

/** 全メモ取得（完全一致検索用） */
export async function listMemos(): Promise<Result[]> {
    const { results } = await postForm<{ results: Result[] }>('/api/search', { query: '' })
    return results
}

/** セマンティック検索 */
export async function searchMemos(query: string): Promise<Result[]> {
    const { results } = await postForm<{ results: Result[] }>('/api/search', { query })
    return results
}

/** メモ作成 */
export async function createMemo(
    payload: MemoPayload
): Promise<{ message: string; path: string }> {
    return postForm<{ message: string; path: string }>('/api/memo', payload)
}
