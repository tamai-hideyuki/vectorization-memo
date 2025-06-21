export async function createMemo(data: {
    category: string;
    title: string;
    tags: string;
    body: string;
}) {
    const form = new FormData();
    form.append('category', data.category);
    form.append('title', data.title);
    form.append('tags', data.tags);
    form.append('body', data.body);

    // FastAPI はポート 8001 で動作している前提です
    const res = await fetch('http://localhost:8001/api/memo', {
        method: 'POST',
        body: form,
        credentials: 'omit',
    });

    if (!res.ok) {
        throw new Error(`HTTP ${res.status}: ${res.statusText}`);
    }
    return res.json();
}
