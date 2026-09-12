-- Add the ingestion sources emitted by the read-only mail import pipeline.
ALTER TABLE public.sales_mailbox_sources DROP CONSTRAINT IF EXISTS sales_mailbox_sources_source_type_check;
ALTER TABLE public.sales_mailbox_sources ADD CONSTRAINT sales_mailbox_sources_source_type_check
CHECK (source_type IN ('gmail', 'manual_upload', 'eml', 'txt', 'csv', 'api', 'imap', 'pop3', 'thunderbird_local'));
ALTER TABLE public.sales_email_messages DROP CONSTRAINT IF EXISTS sales_email_messages_source_type_check;
ALTER TABLE public.sales_email_messages ADD CONSTRAINT sales_email_messages_source_type_check
CHECK (source_type IN ('gmail', 'manual_upload', 'eml', 'txt', 'csv', 'api', 'imap', 'pop3', 'thunderbird_local'));
