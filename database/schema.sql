-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- 1. Custom User Profile Table (extends Supabase auth.users)
CREATE TABLE IF NOT EXISTS public.users (
    id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    email TEXT UNIQUE NOT NULL,
    full_name TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL
);

-- 2. Documents Table (Stores metadata & hot fingerprint indices)
CREATE TABLE IF NOT EXISTS public.documents (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
    filename TEXT NOT NULL,
    storage_path TEXT NOT NULL,
    original_size_bytes INT NOT NULL,
    compressed_size_bytes INT NOT NULL,
    fingerprints JSONB NOT NULL, -- Array of winnowing integer hashes
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL
);

-- 3. Plagiarism Reports Table
CREATE TABLE IF NOT EXISTS public.plagiarism_reports (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    source_doc_id UUID NOT NULL REFERENCES public.documents(id) ON DELETE CASCADE,
    matched_doc_id UUID NOT NULL REFERENCES public.documents(id) ON DELETE CASCADE,
    similarity_score FLOAT NOT NULL,
    matched_segments JSONB DEFAULT '[]'::jsonb NOT NULL, -- Line offsets & LCS matches
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL
);

-- Indexes for Accelerated Lookups
CREATE INDEX IF NOT EXISTS idx_documents_user_id ON public.documents(user_id);
CREATE INDEX IF NOT EXISTS idx_documents_fingerprints_gin ON public.documents USING GIN (fingerprints);
CREATE INDEX IF NOT EXISTS idx_reports_source_doc ON public.plagiarism_reports(source_doc_id);
CREATE INDEX IF NOT EXISTS idx_reports_matched_doc ON public.plagiarism_reports(matched_doc_id);

-- Storage Bucket Creation Policy
INSERT INTO storage.buckets (id, name, public) 
VALUES ('compressed_docs', 'compressed_docs', true)
ON CONFLICT (id) DO NOTHING;
