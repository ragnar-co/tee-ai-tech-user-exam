-- Q-BY-OWNER: MET-04 sliced by owner. Counts only; never a performance score (CON-09).
-- Parameters: $run_id, $project_name (NULL = All Projects)
SELECT owner, COUNT(*) FILTER (WHERE is_overdue) AS overdue_actions
FROM stg_actions
WHERE run_id = $run_id
  AND ($project_name IS NULL OR project_name = $project_name)
GROUP BY owner
HAVING COUNT(*) FILTER (WHERE is_overdue) > 0
ORDER BY overdue_actions DESC, owner
