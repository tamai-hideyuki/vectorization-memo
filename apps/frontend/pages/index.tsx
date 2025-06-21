import { useState } from 'react';
import { createMemo } from '../lib/api';

export default function Home() {
    const [category, setCategory] = useState('');
    const [title, setTitle] = useState('');
    const [tags, setTags] = useState('');
    const [body, setBody] = useState('');
    const [result, setResult] = useState<any>(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setLoading(true);
        setError(null);
        try {
            const data = await createMemo({ category, title, tags, body });
            setResult(data);
            setCategory('');
            setTitle('');
            setTags('');
            setBody('');
        } catch (e: any) {
            setError(e.message);
        } finally {
            setLoading(false);
        }
    };

    return (
        <main style={{ padding: '2rem', fontFamily: 'Arial, sans-serif' }}>
            <h1>メモ作成</h1>
            <form onSubmit={handleSubmit} style={{ display: 'grid', gap: '1rem', maxWidth: '600px' }}>
                <input
                    required
                    placeholder="カテゴリ"
                    value={category}
                    onChange={(e) => setCategory(e.target.value)}
                />
                <input
                    required
                    placeholder="タイトル"
                    value={title}
                    onChange={(e) => setTitle(e.target.value)}
                />
                <input
                    placeholder="タグ (カンマ区切り)"
                    value={tags}
                    onChange={(e) => setTags(e.target.value)}
                />
                <textarea
                    required
                    placeholder="本文"
                    value={body}
                    rows={8}
                    onChange={(e) => setBody(e.target.value)}
                />
                <button type="submit" disabled={loading}>
                    {loading ? '保存中…' : '保存'}
                </button>
            </form>

            {error && <p style={{ color: 'red' }}>エラー: {error}</p>}
            {result && (
                <div style={{ marginTop: '1rem', padding: '1rem', border: '1px solid #ddd' }}>
                    <h2>保存結果</h2>
                    <pre>{JSON.stringify(result, null, 2)}</pre>
                </div>
            )}
        </main>
    );
}
