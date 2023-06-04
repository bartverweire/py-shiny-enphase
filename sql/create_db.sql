CREATE ROLE enl WITH
  LOGIN
  NOSUPERUSER
  INHERIT
  CREATEDB
  NOCREATEROLE
  NOREPLICATION

  ;

CREATE DATABASE enlighten
    WITH
    OWNER = enl
    ENCODING = 'UTF8'
    LC_COLLATE = 'English_United States.1252'
    LC_CTYPE = 'English_United States.1252'
    TABLESPACE = pg_default
    CONNECTION LIMIT = -1
    IS_TEMPLATE = False;

\c enlighten enl

drop table production_micro;
create table production_micro (
    system_id           bigint,
    end_at              timestamp,
    devices_reporting   bigint,
    powr                bigint,
    enwh                bigint
);

drop table production_meter;
create table production_meter (
    system_id           bigint,
    end_at              timestamp,
    devices_reporting   bigint,
    wh_del              bigint
);

drop table battery;
create table battery (
    system_id                   bigint,
    end_at                      timestamp,
    charge_enwh                 bigint,
    charge_devices_reporting    bigint,
    discharge_enwh              bigint,
    discharge_devices_reporting bigint,
    soc_percent                 numeric(4, 1),
	soc_devices_reporting		bigint
);


create table consumption (
    system_id           bigint,
    end_at              timestamp,
    devices_reporting   bigint,
    enwh                bigint
);


create table export (
    system_id           bigint,
    end_at              timestamp,
    wh_exported         bigint
);

create table import (
    system_id           bigint,
    end_at              timestamp,
    wh_imported         bigint
);
