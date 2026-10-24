CREATE SCHEMA IF NOT EXISTS processing_catalog;


CREATE TABLE if not exists processing_catalog.files_main (
    file_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    file_name VARCHAR(255) NOT NULL,

    object_key TEXT NOT NULL UNIQUE,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);


CREATE TABLE if not exists processing_catalog.pdfs_progress (
    progress_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    file_id UUID NOT NULL
        REFERENCES processing_catalog.files_main(file_id),

    status VARCHAR(20) NOT NULL DEFAULT 'pending'
        CHECK (
            status IN (
                'pending',
                'processing',
                'success',
                'failed'
            )
        ),

    progress_message TEXT,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);


CREATE INDEX idx_pdfs_progress_file_id
ON processing_catalog.pdfs_progress (file_id);


CREATE INDEX idx_pdfs_progress_status
ON processing_catalog.pdfs_progress (status);