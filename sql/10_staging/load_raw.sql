-- ST-05 load_raw: copy validated input rows into raw_actions untouched (no trim/convert).
-- Parameters: $run_id, $loaded_at
INSERT INTO raw_actions
SELECT $run_id, action_id, project_name, action_name, owner, due_date_raw, status,
       source_row_number, $loaded_at
FROM input_rows
ORDER BY source_row_number
