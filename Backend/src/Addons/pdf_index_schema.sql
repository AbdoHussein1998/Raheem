-- Fresh installation: only one application-level PDF table.
CREATE SCHEMA IF NOT EXISTS processing_catalog;
CREATE TABLE IF NOT EXISTS processing_catalog.pdf_index (
    file_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    hashed_name VARCHAR(64) NOT NULL UNIQUE,
    file_name VARCHAR(255) NOT NULL,
    bucket_name TEXT NOT NULL DEFAULT 'uploads',
    ocr_required BOOLEAN NOT NULL DEFAULT FALSE,
    object_key TEXT NOT NULL UNIQUE,
    registration_status VARCHAR(20) NOT NULL DEFAULT 'uploading'
        CHECK (registration_status IN ('uploading', 'ready', 'failed','completed')),
    result_object_key TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
