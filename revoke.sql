REVOKE CONNECT ON DATABASE gis FROM public;

SELECT pid, pg_terminate_backend(pid)
FROM pg_stat_activity
WHERE datname = current_database() AND pid <> pg_backend_pid();