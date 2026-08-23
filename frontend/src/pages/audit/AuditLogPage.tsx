import { Search } from "lucide-react";
import {
    useEffect,
    useRef,
    useState,
} from "react";

import apiClient from "../../api/client";


import "../../styles/pages/audit/AuditLogPage.css";

type AuditActionFilter =
    | ""
    | "quiz_created"
    | "quiz_updated"
    | "quiz_deleted"
    | "quiz_completed";

type AuditLog = {
    id: string;
    user_id: string;
    quiz_id: string | null;
    action:
    | "quiz_created"
    | "quiz_updated"
    | "quiz_deleted"
    | "quiz_completed";
    quiz_title: string;
    creator_name: string;
    created_at: string;
};

type AuditLogResponse = {
    audit_logs: AuditLog[];
    total: number;
    page: number;
    page_size: number;
    total_pages: number;
};


export default function AuditLogPage() {
    const [search, setSearch] = useState("");
    const [action, setAction] = useState<AuditActionFilter>("");
    const [dateFrom, setDateFrom] = useState("");
    const [dateTo, setDateTo] = useState("");
    const [auditLogs, setAuditLogs] = useState<AuditLog[]>([]);
    const [isLoading, setIsLoading] = useState(true);
    const [isLoadingMore, setIsLoadingMore] = useState(false);
    const [error, setError] = useState("");
    const [total, setTotal] = useState(0);
    const [page, setPage] = useState(1);
    const [totalPages, setTotalPages] = useState(0);
    const loadMoreRef = useRef<HTMLDivElement | null>(null);

    useEffect(() => {
        let cancelled = false;

        const loadAuditLogs = async () => {
            if (page > 1) {
                setIsLoadingMore(true);
            }
            try {
                const response = await apiClient.get<AuditLogResponse>(
                    "/audit-logs",
                    {
                        params: {
                            page,
                            page_size: 10,
                            action: action || undefined,
                            search: search.trim() || undefined,
                            date_from: dateFrom || undefined,
                            date_to: dateTo || undefined,
                        },
                    },
                );

                if (cancelled) {
                    return;
                }

                setAuditLogs((current) =>
                    page === 1
                        ? response.data.audit_logs
                        : [...current, ...response.data.audit_logs],
                );
                setTotal(response.data.total);
                setTotalPages(response.data.total_pages);
                setError("");
            } catch {
                if (cancelled) {
                    return;
                }

                if (page === 1) {
                    setAuditLogs([]);
                    setTotal(0);
                    setTotalPages(0);
                }

                setError("Unable to load your audit activity.");
            } finally {
                if (!cancelled) {
                    if (page === 1) {
                        setIsLoading(false);
                    } else {
                        setIsLoadingMore(false);
                    }
                }
            }
        };

        void loadAuditLogs();

        return () => {
            cancelled = true;
        };
    }, [page, action, search, dateFrom, dateTo]);


    useEffect(() => {
        const target = loadMoreRef.current;

        if (
            !target ||
            isLoading ||
            isLoadingMore ||
            page >= totalPages
        ) {
            return;
        }

        const observer = new IntersectionObserver(
            (entries) => {
                const firstEntry = entries[0];

                if (firstEntry?.isIntersecting) {
                    setPage((current) => current + 1);
                }
            },
            {
                rootMargin: "200px 0px",
            },
        );

        observer.observe(target);

        return () => {
            observer.disconnect();
        };
    }, [isLoading, isLoadingMore, page, totalPages]);


    return (
        <main className="audit-log-page">
            <div className="audit-log-page__container">
                <header className="audit-log-page__header">
                    <div>
                        <h1>Audit Log</h1>
                        <p>
                            Review your quiz activity and recent actions.
                        </p>
                    </div>
                </header>

                <section
                    className="audit-log-filters"
                    aria-label="Audit log filters"
                >
                    <div className="audit-log-filters__search">
                        <Search
                            size={18}
                            strokeWidth={1.9}
                            aria-hidden="true"
                        />

                        <input
                            type="search"
                            value={search}
                            onChange={(event) => {
                                setSearch(event.target.value);
                                setPage(1);
                            }}
                            placeholder="Search by quiz or creator..."
                            aria-label="Search by quiz or creator"
                        />
                    </div>

                    <select
                        className="audit-log-filters__control audit-log-filters__action"
                        value={action}
                        onChange={(event) => {
                            setAction(event.target.value as AuditActionFilter);
                            setPage(1);
                        }}
                        aria-label="Filter by action"
                    >
                        <option value="">All actions</option>
                        <option value="quiz_created">Created</option>
                        <option value="quiz_updated">Edited</option>
                        <option value="quiz_deleted">Deleted</option>
                        <option value="quiz_completed">Completed</option>
                    </select>

                    <div className="audit-log-filters__date">
                        <span>From</span>
                        <input
                            type="date"
                            value={dateFrom}
                            onChange={(event) => {
                                setDateFrom(event.target.value);
                                setPage(1);
                            }}
                            aria-label="Filter from date"
                        />
                    </div>

                    <div className="audit-log-filters__date">
                        <span>To</span>
                        <input
                            type="date"
                            value={dateTo}
                            min={dateFrom || undefined}
                            onChange={(event) => {
                                setDateTo(event.target.value);
                                setPage(1);
                            }}
                            aria-label="Filter to date"
                        />
                    </div>

                    {(search || action || dateFrom || dateTo) && (
                        <button
                            type="button"
                            className="audit-log-filters__clear"
                            onClick={() => {
                                setSearch("");
                                setAction("");
                                setDateFrom("");
                                setDateTo("");
                                setPage(1);
                            }}
                        >
                            Clear
                        </button>
                    )}
                </section>

                <section className="audit-log-page__content">
                    {isLoading && (
                        <div className="audit-log-state">
                            Loading activity...
                        </div>
                    )}

                    {!isLoading && error && (
                        <div className="audit-log-state audit-log-state--error">
                            {error}
                        </div>
                    )}

                    {!isLoading && !error && auditLogs.length === 0 && (
                        <div className="audit-log-state">
                            No activity found.
                        </div>
                    )}

                    {!isLoading && !error && auditLogs.length > 0 && (
                        <>
                            <div className="audit-log-table">
                                <div className="audit-log-table__header">
                                    <span>Quiz</span>
                                    <span>Creator</span>
                                    <span>Date</span>
                                    <span>Action</span>
                                </div>

                                <div className="audit-log-table__body">
                                    {auditLogs.map((log) => (
                                        <div
                                            className="audit-log-table__row audit-log-table__row--enter"
                                            key={log.id}
                                        >
                                            <div className="audit-log-table__quiz">
                                                {log.quiz_title}
                                            </div>

                                            <div className="audit-log-table__creator">
                                                {log.creator_name}
                                            </div>

                                            <div className="audit-log-table__date">
                                                {new Date(log.created_at).toLocaleString(
                                                    undefined,
                                                    {
                                                        month: "short",
                                                        day: "numeric",
                                                        year: "numeric",
                                                        hour: "numeric",
                                                        minute: "2-digit",
                                                    },
                                                )}
                                            </div>

                                            <div>
                                                <span
                                                    className={`audit-log-action audit-log-action--${log.action}`}
                                                >
                                                    {log.action === "quiz_created" &&
                                                        "Created"}

                                                    {log.action === "quiz_updated" &&
                                                        "Edited"}

                                                    {log.action === "quiz_deleted" &&
                                                        "Deleted"}

                                                    {log.action === "quiz_completed" &&
                                                        "Completed"}
                                                </span>
                                            </div>
                                        </div>
                                    ))}
                                </div>
                            </div>

                            <div className="audit-log-footer">
                                <span>
                                    {total} {total === 1 ? "activity" : "activities"}
                                </span>
                            </div>
                            {isLoadingMore && (
                                <div
                                    className="audit-log-loading-more"
                                    role="status"
                                >
                                    Loading more activity...
                                </div>
                            )}
                            {page < totalPages && (
                                <div
                                    ref={loadMoreRef}
                                    className="audit-log-load-more"
                                    aria-hidden="true"
                                />
                            )}
                        </>
                    )}
                </section>
            </div>
        </main>
    );
}