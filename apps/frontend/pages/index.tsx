import Head from 'next/head';
import { useState, useEffect } from 'react';
import { createMemo, getCategories, getTags, incrementalVectorize } from '../lib/api';
import Link from 'next/link';

export default function Home() {
    const [categories, setCategories] = useState<string[]>([]);
    const [tagsList, setTagsList]     = useState<string[]>([]);

    const [category, setCategory] = useState('');
    const [title, setTitle]       = useState('');
    const [tags, setTags]         = useState('');  // comma–separated
    const [body, setBody]         = useState('');
    const [result, setResult]     = useState<any>(null);
    const [loading, setLoading]   = useState(false);
    const [error, setError]       = useState<string | null>(null);

    const [vectorizing, setVectorizing]       = useState(false);
    const [vectorizeStatus, setVectorizeStatus] = useState<string>('');


    // ① 既存のカテゴリー／タグを取得
    useEffect(() => {
        (async () => {
            try {
                const [cats, tgs] = await Promise.all([
                    getCategories(),
                    getTags(),
                ]);
                setCategories(cats);
                setTagsList(tgs);
            } catch {
                // 失敗してもフォームは動くように
            }
        })();
    }, []);

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

    const handleRevectorize = async () => {
        setVectorizing(true);
        setVectorizeStatus('再ベクトル化を開始しています…');
        try {
            const { status } = await incrementalVectorize();
            setVectorizeStatus(status);
        } catch (e: any) {
            setVectorizeStatus(`エラー: ${e.message}`);
        } finally {
            setVectorizing(false);
        }
    };

    return (
    <>
        {/* ① ここでタイトルを書き換える */}
        <Head>
            <title>vectorization-memo</title>
            <meta name="description" content="ベクトル化メモ検索ツール" />
        </Head>
        <main style={{ padding: '2rem', fontFamily: 'Arial, sans-serif' }}>
            <h1>メモ作成</h1>

            {/* ② カテゴリー候補を一覧表示 */}
            <div style={{ marginBottom: '1rem' }}>
                <strong>既存のカテゴリー：</strong>
                {categories.length
                    ? categories.map((c) => (
                        <span
                            key={c}
                            style={{
                                display: 'inline-block',
                                background: '#eef',
                                padding: '0.2em 0.5em',
                                margin: '0.1em',
                                borderRadius: '4px',
                            }}
                        >
                {c}
              </span>
                    ))
                    : '（読み込み中…）'}
            </div>

            {/* ③ フォーム */}
            <form onSubmit={handleSubmit} style={{ display: 'grid', gap: '1rem', maxWidth: '600px' }}>
                {/* コンボボックス化：datalist */}
                <input
                    list="category-list"
                    required
                    placeholder="カテゴリ"
                    value={category}
                    onChange={(e) => setCategory(e.target.value)}
                />
                <datalist id="category-list">
                    {categories.map((c) => (
                        <option key={c} value={c} />
                    ))}
                </datalist>

                <input
                    required
                    placeholder="タイトル"
                    value={title}
                    onChange={(e) => setTitle(e.target.value)}
                />

                {/* タグも同様にdatalistで候補提示 */}
                <input
                    list="tags-list"
                    placeholder="タグ (カンマ区切り)"
                    value={tags}
                    onChange={(e) => setTags(e.target.value)}
                />
                <datalist id="tags-list">
                    {tagsList.map((t) => (
                        <option key={t} value={t} />
                    ))}
                </datalist>

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

            <div style={{ marginTop: '2rem', borderTop: '1px solid #eee', paddingTop: '1rem' }}>
                <button
                    onClick={handleRevectorize}
                    disabled={vectorizing}
                    style={{ padding: '0.5rem 1rem' }}
                >
                    {vectorizing ? '再ベクトル化中…' : '再ベクトル化'}
                </button>
                {vectorizeStatus && <p style={{ marginTop: '0.5rem' }}>{vectorizeStatus}</p>}
            </div>

            <p style={{ marginTop: '2rem' }}>
                <Link href="./search">→ メモ検索ページへ</Link>
            </p>
        </main>
      </>
    );
}
