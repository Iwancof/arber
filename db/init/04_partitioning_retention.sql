-- Partitioning and retention guide (illustrative)
-- Use migration tooling to turn these into operational scripts.

-- Example partitioned table pattern for raw_document:
-- 1) create partitioned parent
-- 2) create monthly partitions
-- 3) attach retention jobs

-- Example retention policy:
-- raw_document raw_payload_json large blobs: 180 days hot, 3 years cold object storage
-- event/forecast/decision/order/outcome/postmortem ledgers: retained indefinitely
-- audit_log: 2 years hot, archived afterwards
-- watcher heartbeats: 30 days

-- Recommended operational process:
-- - create next 3 partitions ahead of time
-- - move old partitions to cheaper storage where allowed
-- - never drop a partition without confirming lineage/export policy
