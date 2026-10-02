-- Latest successful run (METRIC_LOGIC rule 3). NULL run_id = no data yet (empty state).
SELECT max(run_id) AS run_id
FROM ingestion_runs
WHERE status = 'succeeded'
