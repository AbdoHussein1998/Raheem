CREATE SCHEMA IF NOT EXISTS processing_catalog;

CREATE TABLE IF NOT EXISTS processing_catalog.files_main (
    file_id BIGINT PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    hashed_name VARCHAR(255) UNIQUE,
    file_name VARCHAR(255) NOT NULL,
    object_key TEXT NOT NULL UNIQUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS processing_catalog.pdfs_progress (
    progress_id BIGINT PRIMARY KEY GENERATED ALWAYS AS IDENTITY,

    hashed_name VARCHAR(255)
        REFERENCES processing_catalog.files_main(hashed_name)
        ON DELETE CASCADE,

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

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Index for joining processing progress to files
CREATE INDEX IF NOT EXISTS idx_pdfs_progress_hashed_name
ON processing_catalog.pdfs_progress (hashed_name);

-- Index for filtering by processing status
CREATE INDEX IF NOT EXISTS idx_pdfs_progress_status
ON processing_catalog.pdfs_progress (status);


DROP TABLE IF EXISTS processing_catalog.files_main CASCADE;

DROP TABLE IF EXISTS processing_catalog.pdfs_progress CASCADE;