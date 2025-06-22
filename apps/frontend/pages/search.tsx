import { useState } from 'react'
import { searchMemos }    from '../lib/api'
import Link from 'next/link'

type Result = {
    uuid:       string
    title:      string
    snippet:    string
    body:       string
    category:   string
    tags:       string
    created_at: string
    score:      number
}

export default function SearchPage() {
    const [query, setQuery]   = useState('')
    const [k, setK]           = useState(5)
    const [results, setResults] = useState<Result[]>([])
    const [error, setError]     = useState<string | null>(null)
    const [loading, setLoading] = useState(false)
    const [selected, setSelected] = useState<Result | null>(null)

    const handleSearch = async (e: React.FormEvent) => {
        e.preventDefault()
        setLoading(true)
        setError(null)
        try {
            const res = await searchMemos(query, k)
            setResults(res)
        } catch (e: any) {
            setError(e.message)
        } finally {
            setLoading(false)
        }
    }

    return (
        <main style={styles.main}>
            <h1>メモ検索</h1>

            <form onSubmit={handleSearch} style={styles.form}>
                <input
                    placeholder="検索クエリ"
                    value={query}
                    onChange={e => setQuery(e.target.value)}
                    style={styles.input}
                />
                <label>
                    件数:
                    <select value={k} onChange={e => setK(Number(e.target.value))} style={styles.select}>
                        {[1,3,5,10].map(n => <option key={n} value={n}>{n}</option>)}
                    </select>
                </label>
                <button type="submit" disabled={loading} style={styles.button}>
                    {loading ? '検索中…' : '検索'}
                </button>
            </form>

            {error && <p style={styles.error}>エラー: {error}</p>}

            {results.length > 0 && (
                <section style={{ marginTop: '2rem' }}>
                    <h2>検索結果 ({results.length} 件)</h2>
                    <table style={styles.table}>
                        <thead>
                        <tr>
                            <th style={styles.th}>スコア</th>
                            <th style={styles.th}>タイトル</th>
                            <th style={styles.th}>スニペット</th>
                            <th style={styles.th}>カテゴリ</th>
                            <th style={styles.th}>タグ</th>
                            <th style={styles.th}>作成日時</th>
                        </tr>
                        </thead>
                        <tbody>
                        {results.map((r,i) => (
                            <tr key={i}>
                                <td style={styles.td}>{r.score}</td>
                                <td
                                    style={{ ...styles.td, cursor: 'pointer', color: '#0066cc' }}
                                    onClick={() => setSelected(r)}
                                >
                                    {r.title}
                                </td>
                                <td
                                    style={{ ...styles.td, cursor: 'pointer', color: '#0066cc' }}
                                    onClick={() => setSelected(r)}
                                >
                                    {r.snippet}
                                </td>
                                <td style={styles.td}>{r.category}</td>
                                <td style={styles.td}>{r.tags}</td>
                                <td style={styles.td}>{r.created_at}</td>
                            </tr>
                        ))}
                        </tbody>
                    </table>
                </section>
            )}

            {/* ─── モーダル ─── */}
            {selected && (
                <div style={styles.overlay} onClick={() => setSelected(null)}>
                    <div style={styles.modal} onClick={e => e.stopPropagation()}>
                        <h2 style={{ marginTop: 0 }}>{selected.title}</h2>
                        <pre style={styles.pre}>{selected.body}</pre>
                        <button onClick={() => setSelected(null)} style={styles.closeButton}>
                            閉じる
                        </button>
                    </div>
                </div>
            )}
            <p style={{ marginTop: '2rem' }}>
                <Link href="./">⏎ 戻る</Link>
            </p>
        </main>
    )
}

const styles = {
    main: {
        padding: '2rem',
        fontFamily: 'Arial, sans-serif'
    } as React.CSSProperties,
    form: {
        display: 'grid',
        gap: '0.5rem',
        maxWidth: '600px'
    } as React.CSSProperties,
    input: {
        padding: '0.5rem',
        fontSize: '1rem'
    } as React.CSSProperties,
    select: {
        marginLeft: '0.5rem'
    } as React.CSSProperties,
    button: {
        padding: '0.75rem',
        fontSize: '1rem'
    } as React.CSSProperties,
    error: {
        color: 'red'
    } as React.CSSProperties,
    table: {
        borderCollapse: 'collapse',
        width: '100%'
    } as React.CSSProperties,
    th: {
        border: '1px solid #ccc',
        padding: '0.5rem',
        textAlign: 'left',
        backgroundColor: '#f0f0f0'
    } as React.CSSProperties,
    td: {
        border: '1px solid #ccc',
        padding: '0.5rem'
    } as React.CSSProperties,
    overlay: {
        position: 'fixed' as 'fixed',
        top: 0,
        left: 0,
        width: '100vw',
        height: '100vh',
        backgroundColor: 'rgba(0,0,0,0.5)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        zIndex: 1000
    },
    modal: {
        backgroundColor: '#fff',
        padding: '1.5rem',
        maxWidth: '80%',
        maxHeight: '80%',
        overflowY: 'auto' as 'auto',
        boxShadow: '0 2px 8px rgba(0,0,0,0.3)',
        borderRadius: '4px'
    },
    pre: {
        whiteSpace: 'pre-wrap' as 'pre-wrap',
        wordBreak: 'break-word' as 'break-word',
        backgroundColor: '#fafafa',
        padding: '1rem',
        borderRadius: '4px'
    },
    closeButton: {
        marginTop: '1rem',
        padding: '0.5rem 1rem',
        cursor: 'pointer'
    }
}
