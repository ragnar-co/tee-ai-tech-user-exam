-- Normative DQ assertions (DATA_QUALITY.md). Each "-- name:" block is one query; every row it
-- returns is one finding. Relations: input_rows(source_row_number, action_id, project_name,
-- action_name, owner, due_date_raw, status) and input_columns(column_name) are temp tables
-- built by src/validation.py from the raw CSV text (all VARCHAR, nothing converted).

-- name: DQ-01-missing
SELECT c AS record_key FROM (VALUES ('action_id'),('project_name'),('action_name'),
                                    ('owner'),('due_date'),('status')) t(c)
WHERE c NOT IN (SELECT column_name FROM input_columns);

-- name: DQ-01-extra
SELECT column_name AS record_key FROM input_columns
WHERE column_name NOT IN ('action_id','project_name','action_name','owner','due_date','status');

-- name: DQ-01-duplicate
SELECT column_name AS record_key FROM input_columns GROUP BY column_name HAVING count(*) > 1;

-- name: DQ-11
-- Row shape (blocking): a record with more or fewer fields than the header is malformed (an
-- unquoted comma shifts every later column); never load it with fields silently dropped.
SELECT source_row_number FROM input_rows
WHERE field_count <> (SELECT count(*) FROM input_columns);

-- name: DQ-12
-- Control characters other than TAB / LF / CR (warning): kept as-is, reported per row.
SELECT source_row_number FROM input_rows
WHERE regexp_matches(coalesce(action_id,'') || coalesce(project_name,'') || coalesce(action_name,'')
                     || coalesce(owner,'') || coalesce(due_date_raw,'') || coalesce(status,''),
                     '[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]');

-- name: DQ-02
SELECT source_row_number FROM input_rows WHERE action_id IS NULL OR regexp_matches(action_id, '^[\s\p{Z}\x{200B}\x{FEFF}]*$');

-- name: DQ-03
SELECT action_id AS record_key, count(*) AS n, list(source_row_number) AS rows
FROM input_rows WHERE action_id IS NOT NULL AND NOT regexp_matches(action_id, '^[\s\p{Z}\x{200B}\x{FEFF}]*$')
GROUP BY action_id HAVING count(*) > 1;

-- name: DQ-04
SELECT source_row_number FROM input_rows WHERE project_name IS NULL OR regexp_matches(project_name, '^[\s\p{Z}\x{200B}\x{FEFF}]*$');

-- name: DQ-05
SELECT source_row_number FROM input_rows WHERE action_name IS NULL OR regexp_matches(action_name, '^[\s\p{Z}\x{200B}\x{FEFF}]*$');

-- name: DQ-06
SELECT source_row_number FROM input_rows WHERE owner IS NULL OR regexp_matches(owner, '^[\s\p{Z}\x{200B}\x{FEFF}]*$');

-- name: DQ-07
SELECT source_row_number FROM input_rows
WHERE due_date_raw IS NULL OR regexp_matches(due_date_raw, '^[\s\p{Z}\x{200B}\x{FEFF}]*$')
   OR NOT regexp_matches(due_date_raw, '^[0-9]{4}-[0-9]{2}-[0-9]{2}$')
   OR try_strptime(due_date_raw, '%Y-%m-%d') IS NULL;

-- name: DQ-08
SELECT source_row_number FROM input_rows WHERE status IS NULL OR regexp_matches(status, '^[\s\p{Z}\x{200B}\x{FEFF}]*$');

-- name: DQ-09
-- $action_status_values = values of enum action_status (passed from src/settings.py)
SELECT DISTINCT status AS record_key FROM input_rows
WHERE status IS NOT NULL AND NOT regexp_matches(status, '^[\s\p{Z}\x{200B}\x{FEFF}]*$')
  AND status NOT IN (SELECT unnest($action_status_values))
ORDER BY 1;

-- name: DQ-10
SELECT i.run_id FROM ingestion_runs i
WHERE i.run_id = $run_id
  AND NOT ( i.source_row_count = i.valid_row_count + i.invalid_row_count
        AND i.valid_row_count = (SELECT count(*) FROM raw_actions r WHERE r.run_id = i.run_id)
        AND i.valid_row_count = (SELECT count(*) FROM stg_actions s WHERE s.run_id = i.run_id) );

-- name: RI-01
SELECT s.run_id FROM stg_actions s LEFT JOIN ingestion_runs i USING (run_id)
WHERE i.run_id IS NULL OR i.status <> 'succeeded' GROUP BY s.run_id;

-- name: RI-02
SELECT run_id, action_id FROM stg_actions EXCEPT SELECT run_id, action_id FROM raw_actions;

-- name: RI-03
SELECT q.run_id FROM data_quality_results q LEFT JOIN ingestion_runs i USING (run_id)
WHERE i.run_id IS NULL;

-- name: RI-04
SELECT e.summary_id FROM executive_summaries e LEFT JOIN ingestion_runs i ON i.run_id = e.source_run_id
WHERE i.run_id IS NULL;

-- name: RI-05
SELECT run_id, action_id FROM stg_actions GROUP BY 1,2 HAVING count(*) > 1;
