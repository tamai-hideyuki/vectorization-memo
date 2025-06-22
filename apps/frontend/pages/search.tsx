import { useState, useCallback } from 'react'
import { searchMemos } from '../lib/api'
import Link from "next/link";

type Result = {
    uuid:       string
    title:      string
    snippet:    string
    category:   string
    tags:       string
    created_at: string
    score:      number
}

export default function SearchPage() {
    const [query, setQuery]     = useState('')
    const [k, setK]             = useState(5)
    const [results, setResults] = useState<Result[]>([])
    const [error, setError]     = useState<string | null>(null)
    const [loading, setLoading] = useState(false)

    const handleSearch = useCallback(async (e: React.FormEvent) => {
        e.preventDefault()
        setLoading(true)
        setError(null)

        try {
            const res = await searchMemos(query, k)
            setResults(res)
        } catch (err: any) {
            setError(err.message || '検索に失敗しました')
        } finally {
            setLoading(false)
        }
    }, [query, k])

    return (
        <main style={styles.container}>
            <h1 style={styles.heading}>メモ検索</h1>

            <form onSubmit={handleSearch} style={styles.form}>
                <input
                    placeholder="検索クエリ"
                    value={query}
                    onChange={e => setQuery(e.target.value)}
                    style={styles.input}
                />

                <label style={styles.label}>
                    件数:
                    <select
                        value={k}
                        onChange={e => setK(Number(e.target.value))}
                        style={styles.select}
                    >
                        {[1, 3, 5, 10].map(n => (
                            <option key={n} value={n}>{n}</option>
                        ))}
                    </select>
                </label>

                <button type="submit" disabled={loading} style={styles.button}>
                    {loading ? '検索中…' : '検索'}
                </button>
            </form>

            {error && <p style={styles.error}>エラー: {error}</p>}

            {results.length > 0 && (
                <section style={styles.resultsSection}>
                    <h2>検索結果 ({results.length} 件)</h2>
                    <ResultTable data={results} />
                </section>
            )}
            <p style={{ marginTop: '2rem' }}>
                <Link href="./">→ 戻る</Link>
            </p>
        </main>
    )
}

// ─── ResultTable ───────────────────────────────────────────────
function ResultTable({ data }: { data: Result[] }) {
    return (
        <table style={styles.table}>
            <thead>
            <tr>
                <th style={styles.th}>タイトル</th>
                <th style={styles.th}>スニペット</th>
                <th style={styles.th}>カテゴリ</th>
                <th style={styles.th}>タグ</th>
                <th style={styles.th}>作成日時</th>
                <th style={styles.th}>スコア</th>
            </tr>
            </thead>
            <tbody>
            {data.map(r => (
                <tr key={r.uuid}>
                    <td style={styles.td}>{r.title}</td>
                    <td style={styles.td}>{r.snippet}</td>
                    <td style={styles.td}>{r.category}</td>
                    <td style={styles.td}>{r.tags}</td>
                    <td style={styles.td}>{r.created_at}</td>
                    <td style={styles.td}>{r.score}</td>
                </tr>
            ))}
            </tbody>
        </table>
    )
}

// ─── Styles ────────────────────────────────────────────────────
const styles: {[k: string]: React.CSSProperties} = {
    container: {
        padding: '2rem',
        fontFamily: 'Arial, sans-serif',
    },
    heading: {
        marginBottom: '1rem',
    },
    form: {
        display: 'grid',
        gap: '0.5rem',
        maxWidth: '600px',
    },
    input: {
        padding: '0.5rem',
        fontSize: '1rem',
    },
    label: {
        fontSize: '0.9rem',
    },
    select: {
        marginLeft: '0.5rem',
        padding: '0.3rem',
    },
    button: {
        padding: '0.6rem 1rem',
        fontSize: '1rem',
        cursor: 'pointer',
    },
    error: {
        color: 'red',
        marginTop: '1rem',
    },
    resultsSection: {
        marginTop: '2rem',
    },
    table: {
        borderCollapse: 'collapse',
        width: '100%',
    },
    th: {
        border: '1px solid #ccc',
        padding: '0.5rem',
        textAlign: 'left',
        background: '#f2f2f2',
    },
    td: {
        border: '1px solid #ccc',
        padding: '0.5rem',
    },
}
