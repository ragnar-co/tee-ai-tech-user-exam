-- Q-BY-PROJECT: MET-01..04 + MET-06 + MET-08 per project.
-- Parameters: $run_id, $project_name (NULL = All Projects; a project = 1 row; unknown = 0 rows)
SELECT project_name,
       COUNT(*)                             AS total_actions,
       COUNT(*) FILTER (WHERE is_completed) AS completed_actions,
       COUNT(*) FILTER (WHERE is_open)      AS open_actions,
       COUNT(*) FILTER (WHERE is_overdue)   AS overdue_actions,
       COUNT(*) FILTER (WHERE is_open AND NOT is_overdue) AS open_not_overdue_actions,
       CASE WHEN COUNT(*) = 0 THEN 0
            ELSE COUNT(*) FILTER (WHERE is_completed)::DOUBLE / COUNT(*) END AS completion_rate
FROM stg_actions
WHERE run_id = $run_id
  AND ($project_name IS NULL OR project_name = $project_name)
GROUP BY project_name
ORDER BY project_name
