export async function createMemo(data: {
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

    // BASE を "" にしておけば、fetch('/api/memo') でリライト先に飛ぶはず。。
    const res = await fetch('/api/memo', {
        method: 'POST',
        body:   form,
    })
    if (!res.ok) throw new Error(`HTTP ${res.status}: ${res.statusText}`)
    return res.json()
}
