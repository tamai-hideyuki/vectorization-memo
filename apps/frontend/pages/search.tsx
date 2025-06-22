import { useState } from 'react'
import Link from 'next/link'
import { searchMemos } from '../lib/api'
import styles from './SearchPage.module.css'

type Result = {
    uuid: string
    title: string
    snippet: string
    body: string
    category: string
    tags: string
    created_at: string
    score: number
}

export default function SearchPage() {
    const [query, setQuery] = useState('')
    const [results, setResults] = useState<Result[]>([])
    const [error, setError] = useState<string | null>(null)
    const [loading, setLoading] = useState(false)
    const [selected, setSelected] = useState<Result | null>(null)

    const handleSearch = async (e: React.FormEvent) => {
        e.preventDefault()
        setLoading(true)
        setError(null)
        try {
            const res = await searchMemos(query) // 全件取得
            setResults(res)
        } catch (e: any) {
            setError(e.message)
        } finally {
            setLoading(false)
        }
    }

    return (
        <main className={styles.main}>
            <h1>メモ検索</h1>

            <form onSubmit={handleSearch} className={styles.form}>
                <input
                    className={styles.input}
                    placeholder="検索クエリ"
                    value={query}
                    onChange={e => setQuery(e.target.value)}
                />
                <button type="submit" disabled={loading} className={styles.button}>
                    {loading ? '検索中…' : '検索'}
                </button>
            </form>

            {error && <p className={styles.error}>エラー: {error}</p>}

            {results.length > 0 && (
                <section className={styles.results}>
                    <h2>検索結果 ({results.length} 件)</h2>
                    <table className={styles.table}>
                        <thead>
                        <tr>
                            <th className={styles.th}>スコア</th>
                            <th className={styles.th}>タイトル</th>
                            <th className={styles.th}>スニペット</th>
                            <th className={styles.th}>カテゴリ</th>
                            <th className={styles.th}>タグ</th>
                            <th className={styles.th}>作成日時</th>
                        </tr>
                        </thead>
                        <tbody>
                        {results.map((r, i) => (
                            <tr key={i}>
                                <td className={styles.td}>{r.score}</td>
                                <td
                                    className={`${styles.td} ${styles.clickable}`}
                                    onClick={() => setSelected(r)}
                                >
                                    {r.title}
                                </td>
                                <td
                                    className={`${styles.td} ${styles.clickable}`}
                                    onClick={() => setSelected(r)}
                                >
                                    {r.snippet}
                                </td>
                                <td className={styles.td}>{r.category}</td>
                                <td className={styles.td}>{r.tags}</td>
                                <td className={styles.td}>{r.created_at}</td>
                            </tr>
                        ))}
                        </tbody>
                    </table>
                </section>
            )}

            {selected && (
                <div className={styles.overlay} onClick={() => setSelected(null)}>
                    <div className={styles.modal} onClick={e => e.stopPropagation()}>
                        <h2>{selected.title}</h2>
                        <pre className={styles.pre}>{selected.body}</pre>
                        <button
                            onClick={() => setSelected(null)}
                            className={styles.closeButton}
                        >
                            閉じる
                        </button>
                    </div>
                </div>
            )}

            <p className={styles.backLink}>
                <Link href="./">⏎ 戻る</Link>
            </p>
        </main>
    )
}
