-- Schema for the Cybersecurity Project Action Dashboard (DATA_MODEL_SPEC.md).
-- Idempotent: every statement uses IF NOT EXISTS (PIPELINE_SPEC ST-01).
-- Foreign keys are logical only (DATA_MODEL_SPEC "Relationships"); enforced by tests/DQ RI-xx.

CREATE SEQUENCE IF NOT EXISTS seq_run_id START 1;
CREATE SEQUENCE IF NOT EXISTS seq_quality_result_id START 1;
CREATE SEQUENCE IF NOT EXISTS seq_summary_id START 1;

CREATE TABLE IF NOT EXISTS ingestion_runs (
    run_id             BIGINT PRIMARY KEY DEFAULT nextval('seq_run_id'),
    source_file        VARCHAR NOT NULL,
    source_hash        VARCHAR NOT NULL,
    reference_date     DATE NOT NULL,
    started_at         TIMESTAMP NOT NULL,
    completed_at       TIMESTAMP,
    source_row_count   INTEGER,
    valid_row_count    INTEGER,
    invalid_row_count  INTEGER,
    status             VARCHAR NOT NULL CHECK (status IN ('running', 'succeeded', 'failed'))
);

CREATE TABLE IF NOT EXISTS raw_actions (
    run_id             BIGINT NOT NULL,
    action_id          VARCHAR,
    project_name       VARCHAR,
    action_name        VARCHAR,
    owner              VARCHAR,
    due_date_raw       VARCHAR,
    status             VARCHAR,
    source_row_number  INTEGER NOT NULL,
    loaded_at          TIMESTAMP NOT NULL,
    PRIMARY KEY (run_id, source_row_number)
);

CREATE TABLE IF NOT EXISTS stg_actions (
    run_id         BIGINT NOT NULL,
    action_id      VARCHAR NOT NULL,
    project_name   VARCHAR NOT NULL,
    action_name    VARCHAR NOT NULL,
    owner          VARCHAR NOT NULL,
    due_date       DATE NOT NULL,
    status         VARCHAR NOT NULL,
    is_completed   BOOLEAN NOT NULL,
    is_open        BOOLEAN NOT NULL,
    is_overdue     BOOLEAN NOT NULL,
    days_overdue   INTEGER NOT NULL,
    loaded_at      TIMESTAMP NOT NULL,
    PRIMARY KEY (run_id, action_id)
);

CREATE TABLE IF NOT EXISTS data_quality_results (
    quality_result_id  BIGINT PRIMARY KEY DEFAULT nextval('seq_quality_result_id'),
    run_id             BIGINT NOT NULL,
    check_name         VARCHAR NOT NULL,
    record_key         VARCHAR,
    severity_class     VARCHAR NOT NULL
                       CHECK (severity_class IN ('blocking', 'warning', 'investigation')),
    message            VARCHAR NOT NULL,
    created_at         TIMESTAMP NOT NULL
);

-- Bonus table (PL-02); created here so the schema is complete (field names per plan.md 9.5).
CREATE TABLE IF NOT EXISTS executive_summaries (
    summary_id      BIGINT PRIMARY KEY DEFAULT nextval('seq_summary_id'),
    created_at      TIMESTAMP NOT NULL,
    reference_date  DATE NOT NULL,
    project_filter  VARCHAR,
    source_run_id   BIGINT NOT NULL,
    summary_text    VARCHAR NOT NULL,
    provider        VARCHAR NOT NULL,
    model_name      VARCHAR NOT NULL,
    prompt_version  VARCHAR NOT NULL
);

-- Informational only: never holds secrets and is never the source of a run's reference_date.
CREATE TABLE IF NOT EXISTS app_config (
    config_key    VARCHAR PRIMARY KEY,
    config_value  VARCHAR NOT NULL,
    updated_at    TIMESTAMP NOT NULL
);
