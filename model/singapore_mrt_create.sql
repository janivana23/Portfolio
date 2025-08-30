/* Author: Janice Ivana
   Date: 29 August 2025
   Programming Language: SQL
   Description: SQL script to create tables for Singapore MRT system with MYSQL
   Please to credit to the Author if using any of the work into your personal/work/study/research.
   Thanks for giving my small project an attention :)
*/


DROP TABLE IF EXISTS TRAIN_VOLUME;
DROP TABLE IF EXISTS TRAIN;
DROP TABLE IF EXISTS TRAIN_STATION;
DROP TABLE IF EXISTS URA;

CREATE TABLE TRAIN (
    train_code            VARCHAR(4)   NOT NULL,
    train_name            VARCHAR(50)  NOT NULL,
    train_line_name       VARCHAR(50)  NOT NULL,
    train_start_operation DATE          NOT NULL,
    train_station_address VARCHAR(200) NOT NULL,
    CONSTRAINT TRAIN_PK PRIMARY KEY (train_code),
    CONSTRAINT chk_train_line CHECK (train_line_name IN (
        'Bukit Panjang LRT',
        'Circle Line',
        'Circle Line Extension',
        'Changi Airport Branch Line',
        'Downtown Line',
        'East-West Line',
        'North East Line',
        'North-South Line',
        'Punggol LRT',
        'Sengkang LRT',
        'Thomson-East Coast Line'
    ))
);

CREATE TABLE TRAIN_STATION (
    train_station_address VARCHAR(200) NOT NULL,
    train_station_lat     DECIMAL(10,9)  NOT NULL,
    train_station_long    DECIMAL(10,7)  NOT NULL,
    ura_area              VARCHAR(50)  NOT NULL,
    CONSTRAINT TRAIN_STATION_PK PRIMARY KEY (train_station_address),
    CONSTRAINT TRAIN_STATION_UQ UNIQUE (train_station_lat, train_station_long)
);

CREATE TABLE TRAIN_VOLUME (
    train_volume_id INT AUTO_INCREMENT PRIMARY KEY,
    train_volume_year_month DATE NOT NULL,
    train_volume_day VARCHAR(50) NOT NULL,
    train_volume_hour INT NOT NULL,
    train_code VARCHAR(4) NOT NULL,
    train_volume_tap_in INT NOT NULL,
    train_volume_tap_out INT NOT NULL,
    CONSTRAINT TRAIN_VOLUME_NK UNIQUE (
        train_volume_year_month,
        train_volume_hour,
        train_volume_day,
        train_code
    )
);


CREATE TABLE URA (
    ura_area   VARCHAR(50)   NOT NULL,
    ura_region VARCHAR(100)  NOT NULL,
    CONSTRAINT URA_PK PRIMARY KEY (ura_area),
    CONSTRAINT chk_ura_region CHECK (ura_region IN (
        'CENTRAL REGION',
        'EAST REGION',
        'NORTH REGION',
        'NORTH-EAST REGION',
        'WEST REGION'
    ))
);

-- Foreign Keys
ALTER TABLE TRAIN_VOLUME
    ADD CONSTRAINT Relation_4 FOREIGN KEY (train_code)
    REFERENCES TRAIN (train_code);

ALTER TABLE TRAIN
    ADD CONSTRAINT train_station_train_fk FOREIGN KEY (train_station_address)
    REFERENCES TRAIN_STATION (train_station_address);

ALTER TABLE TRAIN_STATION
    ADD CONSTRAINT ura_train_station_fk FOREIGN KEY (ura_area)
    REFERENCES URA (ura_area);