-- ST-06 build_stg: the ONLY place the overdue flags / days_overdue are computed (METRIC_LOGIC).
-- reference_date comes from ingestion_runs for this run (CON-06), never from the system clock.
-- Parameter: $run_id
INSERT INTO stg_actions
WITH base AS (
  SELECT r.run_id, r.action_id, r.project_name, r.action_name, r.owner,
         CAST(strptime(r.due_date_raw, '%Y-%m-%d') AS DATE) AS due_date,
         r.status,
         i.reference_date,
         r.loaded_at
  FROM raw_actions r
  JOIN ingestion_runs i ON i.run_id = r.run_id
  WHERE r.run_id = $run_id
)
SELECT run_id, action_id, project_name, action_name, owner, due_date, status,
       (status = 'done')                                     AS is_completed,
       (status != 'done')                                    AS is_open,
       (status != 'done' AND due_date < reference_date)      AS is_overdue,
       CASE WHEN status != 'done' AND due_date < reference_date
            THEN date_diff('day', due_date, reference_date)
            ELSE 0 END                                       AS days_overdue,
       loaded_at
FROM base
