-- Q-OVERDUE-DETAIL: MET-05 + the overdue rows.
-- Parameters: $run_id, $project_name (NULL = All Projects)
SELECT action_id, project_name, action_name, owner, due_date, status, days_overdue
FROM stg_actions
WHERE run_id = $run_id
  AND is_overdue
  AND ($project_name IS NULL OR project_name = $project_name)
ORDER BY days_overdue DESC, due_date ASC, action_id ASC  -- action_id = deterministic tie-break
