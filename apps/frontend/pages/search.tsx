import { useState } from 'react';
import { searchMemos } from '../lib/api';
import Link from 'next/link';

type Result = {
    score:      number;
    uuid:       string;
    title:      string;
    category:   string;
    created_at: string;
};

export default function SearchPage() {
    const [query, setQuery]       = useState('');
    const [k, setK]               = useState(5);
    const [results, setResults]   = useState<Result[]>([]);
    const [loading, setLoading]   = useState(false);
    const [error, setError]       = useState<string|null>(null);

    const handleSearch = async (e: React.FormEvent) => {
        e.preventDefault();
        setLoading(true);
        setError(null);
        try {
            const res = await searchMemos(query, k);
            setResults(res);
        } catch (err: any) {
            setError(err.message);
        } finally {
            setLoading(false);
        }
    };

    return (
        <main style={{ padding: '2rem', fontFamily: 'Arial, sans-serif' }}>
            <h1>メモ検索</h1>
            <form onSubmit={handleSearch} style={{ display: 'grid', gap: '1rem', maxWidth: '600px' }}>
                <input
                    required
                    placeholder="検索キーワード"
                    value={query}
                    onChange={(e) => setQuery(e.target.value)}
                />
                <div>
                    <label>
                        件数:
                        <input
                            type="number"
                            min={1}
                            max={20}
                            value={k}
                            onChange={(e) => setK(Number(e.target.value))}
                            style={{ width: '4rem', marginLeft: '0.5rem' }}
                        />
                    </label>
                </div>
                <button type="submit" disabled={loading}>
                    {loading ? '検索中…' : '検索'}
                </button>
            </form>

            {error && <p style={{ color: 'red' }}>エラー: {error}</p>}

            {results.length > 0 && (
                <section style={{ marginTop: '2rem' }}>
                    <h2>検索結果 ({results.length}件)</h2>
                    <table style={{ borderCollapse: 'collapse', width: '100%' }}>
                        <thead>
                        <tr>
                            <th style={{ border: '1px solid #ccc', padding: '0.5rem' }}>スコア</th>
                            <th style={{ border: '1px solid #ccc', padding: '0.5rem' }}>タイトル</th>
                            <th style={{ border: '1px solid #ccc', padding: '0.5rem' }}>カテゴリ</th>
                            <th style={{ border: '1px solid #ccc', padding: '0.5rem' }}>作成日時</th>
                        </tr>
                        </thead>
                        <tbody>
                        {results.map((r) => (
                            <tr key={r.uuid}>
                                <td style={{ border: '1px solid #ccc', padding: '0.5rem' }}>{r.score}</td>
                                <td style={{ border: '1px solid #ccc', padding: '0.5rem' }}>{r.title}</td>
                                <td style={{ border: '1px solid #ccc', padding: '0.5rem' }}>{r.category}</td>
                                <td style={{ border: '1px solid #ccc', padding: '0.5rem' }}>{r.created_at}</td>
                            </tr>
                        ))}
                        </tbody>
                    </table>
                </section>
            )}

            <p style={{ marginTop: '2rem' }}>
                <Link href="/">← メモ作成ページへ戻る</Link>
            </p>
        </main>
    );
}
