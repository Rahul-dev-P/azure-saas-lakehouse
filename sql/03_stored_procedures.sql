-- Called at the start of a pipeline run to log "in-flight" watermark
CREATE OR ALTER PROCEDURE etl_control.sp_start_pipeline_run
    @source_id INT,
    @run_id VARCHAR(100),
    @new_watermark DATETIME2
AS
BEGIN
    SET NOCOUNT ON;
    
    UPDATE etl_control.watermark_control
    SET current_watermark_in_flight = @new_watermark,
        last_run_status = 'IN_PROGRESS'
    WHERE source_id = @source_id;

    INSERT INTO etl_control.pipeline_log (run_id, source_id, entity_name, layer, start_time, status)
    SELECT @run_id, @source_id, entity_name, 'Bronze', SYSUTCDATETIME(), 'RUNNING'
    FROM etl_control.pipeline_config
    WHERE source_id = @source_id;
END;
GO

-- Called upon successful completion of Databricks Silver/Gold or ADF Copy
CREATE OR ALTER PROCEDURE etl_control.sp_complete_pipeline_run
    @source_id INT,
    @run_id VARCHAR(100),
    @rows_written INT = 0,
    @rows_read INT = 0
AS
BEGIN
    SET NOCOUNT ON;

    UPDATE etl_control.watermark_control
    SET last_processed_watermark = ISNULL(current_watermark_in_flight, last_processed_watermark),
        current_watermark_in_flight = NULL,
        last_run_status = 'SUCCESS',
        last_run_timestamp = SYSUTCDATETIME()
    WHERE source_id = @source_id;

    UPDATE etl_control.pipeline_log
    SET end_time = SYSUTCDATETIME(),
        rows_written = @rows_written,
        rows_read = @rows_read,
        status = 'SUCCESS'
    WHERE run_id = @run_id AND source_id = @source_id AND layer = 'Bronze';
END;
GO

-- Create the Failure Stored Procedure
CREATE OR ALTER PROCEDURE etl_control.sp_fail_pipeline_run
    @source_id INT,
    @run_id VARCHAR(100),
    @error_message NVARCHAR(MAX) = NULL
AS
BEGIN
    SET NOCOUNT ON;

    -- Reset in-flight watermark so subsequent runs can retry cleanly
    UPDATE etl_control.watermark_control
    SET current_watermark_in_flight = NULL,
        last_run_status = 'FAILED',
        last_run_timestamp = SYSUTCDATETIME()
    WHERE source_id = @source_id;

    -- Mark the audit log as FAILED with error message and completion time
    UPDATE etl_control.pipeline_log
    SET end_time = SYSUTCDATETIME(),
        status = 'FAILED',
        error_message = @error_message
    WHERE run_id = @run_id 
      AND source_id = @source_id 
      AND layer = 'Bronze'
      AND status = 'RUNNING';
END;