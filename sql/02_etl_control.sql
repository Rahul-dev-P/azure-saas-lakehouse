-- 1. Create Control Schema
IF NOT EXISTS (SELECT * FROM sys.schemas WHERE name = 'etl_control')
    EXEC('CREATE SCHEMA etl_control');
GO

-- 2. Drop existing control tables if rebuilding
IF OBJECT_ID('etl_control.pipeline_log', 'U') IS NOT NULL DROP TABLE etl_control.pipeline_log;
IF OBJECT_ID('etl_control.watermark_control', 'U') IS NOT NULL DROP TABLE etl_control.watermark_control;
IF OBJECT_ID('etl_control.pipeline_config', 'U') IS NOT NULL DROP TABLE etl_control.pipeline_config;
GO

-- 3. Master Pipeline Configuration Table
CREATE TABLE etl_control.pipeline_config (
    source_id INT IDENTITY(1,1) PRIMARY KEY,
    source_system VARCHAR(50) NOT NULL,          -- 'azure_sql', 'adls_csv', 'adls_api'
    entity_name VARCHAR(100) NOT NULL,           -- 'plans', 'organizations', etc.
    source_type VARCHAR(50) NOT NULL,            -- 'table', 'file', 'json'
    source_schema_or_path VARCHAR(255) NOT NULL, -- Schema name or container/folder
    source_object_name VARCHAR(255) NOT NULL,    -- Table name, file name, or pattern
    watermark_column VARCHAR(100) NULL,          -- 'updated_at', 'event_timestamp', NULL
    target_container VARCHAR(50) NOT NULL DEFAULT 'bronze',
    target_subpath VARCHAR(255) NOT NULL,        -- 'sql_plans', 'file_feature_usage', etc.
    silver_table_name VARCHAR(100) NOT NULL,     -- 'cln_plans'
    gold_table_name VARCHAR(100) NULL,           -- 'dim_plan', 'fact_billing'
    load_type VARCHAR(20) NOT NULL DEFAULT 'incremental', -- 'full', 'incremental'
    execution_order INT NOT NULL DEFAULT 1,      -- 1 = Dimensions, 2 = Facts
    is_active BIT NOT NULL DEFAULT 1             -- 1 = Enabled, 0 = Paused
);
GO

-- 4. Watermark State Tracking Table
CREATE TABLE etl_control.watermark_control (
    source_id INT PRIMARY KEY,
    entity_name VARCHAR(100) NOT NULL,
    last_processed_watermark DATETIME2 NULL,
    current_watermark_in_flight DATETIME2 NULL,
    last_run_status VARCHAR(50) NOT NULL DEFAULT 'INIT',
    last_run_timestamp DATETIME2 DEFAULT SYSUTCDATETIME(),
    CONSTRAINT FK_watermark_config FOREIGN KEY (source_id) 
        REFERENCES etl_control.pipeline_config(source_id)
);
GO

-- 5. Execution Audit Logging Table
CREATE TABLE etl_control.pipeline_log (
    log_id BIGINT IDENTITY(1,1) PRIMARY KEY,
    run_id VARCHAR(100) NOT NULL,                -- ADF pipeline Run ID
    source_id INT NOT NULL,
    entity_name VARCHAR(100) NOT NULL,
    layer VARCHAR(20) NOT NULL,                  -- 'Bronze', 'Silver', 'Gold'
    start_time DATETIME2 NOT NULL,
    end_time DATETIME2 NULL,
    rows_read INT NULL,
    rows_written INT NULL,
    status VARCHAR(50) NOT NULL,                 -- 'RUNNING', 'SUCCESS', 'FAILED'
    error_message NVARCHAR(MAX) NULL
);
GO

-- 6. Seed Metadata for SaaS Entities
INSERT INTO etl_control.pipeline_config 
(source_system, entity_name, source_type, source_schema_or_path, source_object_name, watermark_column, target_container, target_subpath, silver_table_name, gold_table_name, load_type, execution_order, is_active)
VALUES
-- Dimensions / Lookups (Execution Order = 1)
('azure_sql', 'plans',         'table', 'dbo', 'plans',         'updated_at', 'bronze', 'sql_plans',         'cln_plans',         'dim_plan',         'incremental', 1, 1),
('azure_sql', 'organizations', 'table', 'dbo', 'organizations', 'updated_at', 'bronze', 'sql_organizations', 'cln_organizations', 'dim_organization', 'incremental', 1, 1),
('azure_sql', 'users',         'table', 'dbo', 'users',         'updated_at', 'bronze', 'sql_users',         'cln_users',         'dim_user',         'incremental', 1, 1),

-- Facts / Event Streams (Execution Order = 2)
('azure_sql', 'subscriptions', 'table', 'dbo', 'subscriptions', 'updated_at', 'bronze', 'sql_subscriptions', 'cln_subscriptions', 'fact_subscriptions', 'incremental', 2, 1),
('azure_sql', 'invoices',      'table', 'dbo', 'invoices',      'updated_at', 'bronze', 'sql_invoices',      'cln_invoices',      'fact_billing',      'incremental', 2, 1),
('adls_csv',  'feature_usage', 'file',  'landing/csv/feature_usage', 'feature_usage.csv', NULL, 'bronze', 'file_feature_usage', 'cln_feature_usage', 'fact_feature_usage', 'full', 2, 1),
('adls_api',  'logins',        'json',  'landing/api/logins',        'logins_batch_1.json', NULL, 'bronze', 'api_logins',       'cln_logins',        'fact_logins',        'full', 2, 1);
GO

-- 7. Initialize Watermark Tracking (Default baseline to historical epoch: 1970-01-01)
INSERT INTO etl_control.watermark_control (source_id, entity_name, last_processed_watermark, last_run_status)
SELECT source_id, entity_name, '1970-01-01 00:00:00', 'INIT'
FROM etl_control.pipeline_config;
GO