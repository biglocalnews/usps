-- Create a table to store the Fabric addresses
CREATE TABLE IF NOT EXISTS fabric (
    location_id int PRIMARY KEY NOT NULL,
    addr varchar(2048) NOT NULL,
    point geometry NOT NULL,
    bsl boolean NOT NULL,
    building_type_code varchar(1) NOT NULL,
    unit_count int,
);

-- Add geospatial index on addresses.
CREATE INDEX IF NOT EXISTS f_point_idx ON fabric USING GIST(point);
