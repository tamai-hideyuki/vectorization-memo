import { useState, useCallback, useMemo } from 'react'
import Link from 'next/link'
import { searchMemos, listMemos } from '../lib/api'
import styles from './SearchPage.module.css'

// 検索結果の型定義
export type Result = {
    uuid: string
    title: string
    snippet: string
    body: string
    category: string
    tags: string
    created_at: string
    score: number
}

// 定数
const ITEMS_PER_PAGE = 10

// 日時を日本時間に変換
function formatJST(dateString: string): string {
    return new Date(dateString).toLocaleString('ja-JP', {
        timeZone: 'Asia/Tokyo',
        hour12: false,
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit',
    })
}

export default function SearchPage() {
    const [query, setQuery] = useState('')
    const [results, setResults] = useState<Result[]>([])
    const [error, setError] = useState<string | null>(null)
    const [loading, setLoading] = useState(false)
    const [selected, setSelected] = useState<Result | null>(null)
    const [page, setPage] = useState(1)
    const [exactMatch, setExactMatch] = useState(false)

    // 検索実行
    const handleSearch = useCallback(async (e: React.FormEvent) => {
        e.preventDefault()
        setLoading(true)
        setError(null)
        setPage(1)
        try {
            const fetched: Result[] = exactMatch
                ? await listMemos()
                : await searchMemos(query)

            const filtered = exactMatch
                ? fetched.filter(r =>
                    r.title.includes(query) ||
                    r.snippet.includes(query) ||
                    r.body.includes(query)
                )
                : fetched

            setResults(filtered)
        } catch (e: any) {
            setError(e.message)
            setResults([])
        } finally {
            setLoading(false)
        }
    }, [query, exactMatch])

    // ページネーション計算
    const totalPages = useMemo(
        () => Math.max(1, Math.ceil(results.length / ITEMS_PER_PAGE)),
        [results]
    )

    const paginatedResults = useMemo(() => {
        const start = (page - 1) * ITEMS_PER_PAGE
        return results.slice(start, start + ITEMS_PER_PAGE)
    }, [results, page])

    // ページ変更
    const goToPage = useCallback((n: number) => {
        setPage(Math.min(Math.max(1, n), totalPages))
    }, [totalPages])

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
                <label className={styles.checkboxLabel}>
                    <input
                        type="checkbox"
                        checked={exactMatch}
                        onChange={e => setExactMatch(e.target.checked)}
                    /> 完全一致検索
                </label>
                <button type="submit" disabled={loading} className={styles.button}>
                    {loading ? '検索中…' : '検索'}
                </button>
            </form>

            {error && <p className={styles.error}>エラー: {error}</p>}

            {paginatedResults.length > 0 && (
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
                        {paginatedResults.map((r, i) => (
                            <tr key={r.uuid || i}>
                                <td className={styles.td}>{r.score}</td>
                                <td className={`${styles.td} ${styles.clickable}`} onClick={() => setSelected(r)}>
                                    {r.title}
                                </td>
                                <td className={`${styles.td} ${styles.clickable}`} onClick={() => setSelected(r)}>
                                    {r.snippet}
                                </td>
                                <td className={styles.td}>{r.category}</td>
                                <td className={styles.td}>{r.tags}</td>
                                <td className={styles.td}>{formatJST(r.created_at)}</td>
                            </tr>
                        ))}
                        </tbody>
                    </table>

                    {/* ページネーション */}
                    <div className={styles.pagination}>
                        <button onClick={() => goToPage(page - 1)} disabled={page === 1}>
                            前へ
                        </button>
                        {Array.from({ length: totalPages }, (_, idx) => idx + 1).map(num => (
                            <button
                                key={num}
                                onClick={() => goToPage(num)}
                                className={page === num ? styles.activePage : ''}
                            >
                                {num}
                            </button>
                        ))}
                        <button onClick={() => goToPage(page + 1)} disabled={page === totalPages}>
                            次へ
                        </button>
                    </div>
                </section>
            )}

            {selected && (
                <div className={styles.overlay} onClick={() => setSelected(null)}>
                    <div className={styles.modal} onClick={e => e.stopPropagation()}>
                        <h2>{selected.title}</h2>
                        <pre className={styles.pre}>{selected.body}</pre>
                        <button onClick={() => setSelected(null)} className={styles.closeButton}>
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
