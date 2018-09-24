--------------------------------------------------------------------------------------
-- CREATE
--------------------------------------------------------------------------------------

CREATE USER aswi_admin WITH SUPERUSER PASSWORD 'aswi_admin';
CREATE DATABASE aswi_comments OWNER aswi_admin;


-------------------------------------------------------------------------------------
-- TABLES
-------------------------------------------------------------------------------------
CREATE TABLE comments (
    id SERIAL PRIMARY KEY,
    author VARCHAR NOT NULL,
    create_time TIMESTAMP NOT NULL,
    comment TEXT NOT NULL,
    page_id VARCHAR(256) NOT NULL
);
