-- Q-PORTFOLIO: MET-01..04, MET-06, MET-07, MET-08 (portfolio, always 1 row).
-- Parameters: $run_id, $project_name (NULL = All Projects)
SELECT COUNT(*)                             AS total_actions,
       COUNT(*) FILTER (WHERE is_completed) AS completed_actions,
       COUNT(*) FILTER (WHERE is_open)      AS open_actions,
       COUNT(*) FILTER (WHERE is_overdue)   AS overdue_actions,
       COUNT(*) FILTER (WHERE is_open AND NOT is_overdue) AS open_not_overdue_actions,   -- MET-08
       COUNT(DISTINCT owner) FILTER (WHERE is_overdue)    AS owners_with_overdue_actions, -- MET-07
       CASE WHEN COUNT(*) = 0 THEN 0
            ELSE COUNT(*) FILTER (WHERE is_completed)::DOUBLE / COUNT(*) END AS completion_rate  -- MET-06
FROM stg_actions
WHERE run_id = $run_id
  AND ($project_name IS NULL OR project_name = $project_name)
