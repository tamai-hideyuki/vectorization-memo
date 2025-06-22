/** 汎用 POST ヘルパー */
async function postForm<T>(path: string, form: FormData): Promise<T> {
    const res = await fetch(path, {
        method: 'POST',
        body:   form,
    })
    if (!res.ok) throw new Error(`HTTP ${res.status}: ${res.statusText}`)
    return res.json()
}

/** メモ作成 */
export function createMemo(data: {
    category: string
    title:    string
    tags:     string
    body:     string
}) {
    const form = new FormData()
    form.append('category', data.category)
    form.append('title',    data.title)
    form.append('tags',     data.tags)
    form.append('body',     data.body)
    // ※BASE は不要。相対パスで叩くと next.config.js の rewrite が効く
    return postForm<{ message: 'saved'; path: string }>('/api/memo', form)
}

/** セマンティック検索 */
export function searchMemos(query: string, k = 5) {
    const form = new FormData()
    form.append('query', query)
    form.append('k',     String(k))
    return postForm<{ results: any[] }>('/api/search', form)
        .then(r => r.results)
}
