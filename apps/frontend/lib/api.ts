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

    const res = await fetch('http://localhost:8081/api/memo', {
        method: 'POST',
        body: 'form',
    });
    return red.json();
}
