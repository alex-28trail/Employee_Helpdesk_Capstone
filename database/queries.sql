-- Queries used by the API (F2.3, F2.4). The backend runs the SQLAlchemy equivalents
-- in app/routers/tickets.py (list_tickets) and app/routers/dashboard.py (dashboard_summary).

-- tickets_with_requester (F2.3): GET /api/tickets
-- Each ticket with its requester and current status, plus when that status was last set.
-- Optional filters are applied as extra WHERE conditions.
SELECT t.id,
       t.title,
       t.category,
       t.priority,
       t.status,
       t.created_at,
       r.id          AS requester_id,
       r.name        AS requester_name,
       r.department  AS requester_department,
       r.email       AS requester_email,
       latest.created_at AS status_changed_at
FROM tickets t
JOIN requesters r ON r.id = t.requester_id
LEFT JOIN LATERAL (
    SELECT a.created_at
    FROM ticket_activity a
    WHERE a.ticket_id = t.id AND a.new_status IS NOT NULL
    ORDER BY a.created_at DESC, a.id DESC
    LIMIT 1
) latest ON TRUE
-- WHERE t.status = :status AND t.category = :category AND t.priority = :priority AND t.requester_id = :requester_id
ORDER BY t.created_at DESC, t.id DESC;

-- counts_by_status (F2.4): GET /api/dashboard/summary
SELECT status, COUNT(*) AS ticket_count
FROM tickets
GROUP BY status
ORDER BY status;

-- counts_by_priority (F2.4): GET /api/dashboard/summary
SELECT priority, COUNT(*) AS ticket_count
FROM tickets
GROUP BY priority
ORDER BY priority;

-- counts_by_category: GET /api/dashboard/summary
SELECT category, COUNT(*) AS ticket_count
FROM tickets
GROUP BY category
ORDER BY category;
