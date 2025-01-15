
DO $$ 
BEGIN
    IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'root') THEN
        CREATE USER root WITH PASSWORD 'zxyoright';
    END IF;
END $$;


DO $$ 
BEGIN
    IF NOT EXISTS (SELECT FROM pg_database WHERE datname = 'zxy') THEN
        CREATE DATABASE zxy;
    END IF;
END $$;

GRANT ALL PRIVILEGES ON DATABASE zxy TO root;