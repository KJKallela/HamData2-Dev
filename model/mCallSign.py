# This is a file containing all the business logic and database actions of callsigns data table
#
# The table structure is as follows:
#
# TABLE: public.callsigns
#    id integer NOT NULL DEFAULT nextval('callsigns_id_seq'::regclass),
#    deletedate timestamp without time zone,
#    callsign character varying(40) COLLATE pg_catalog."default" NOT NULL,
#    aliases character varying(80) COLLATE pg_catalog."default",
#    dxcc integer,
#    qslinfo character varying(80) COLLATE pg_catalog."default",
#    firstname character varying(80) COLLATE pg_catalog."default",
#    lastname character varying(80) COLLATE pg_catalog."default",
#    wholename character varying(80) COLLATE pg_catalog."default",
#    namefmt character varying(80) COLLATE pg_catalog."default",
#    bornyear integer,
#    addr1 character varying(80) COLLATE pg_catalog."default",
#    addr2 character varying(80) COLLATE pg_catalog."default",
#    state character varying(80) COLLATE pg_catalog."default",
#    zip character varying(20) COLLATE pg_catalog."default",
#    country character varying(40) COLLATE pg_catalog."default",
#    lat double precision,
#    lon double precision,
#    grid character varying(15) COLLATE pg_catalog."default",
#    county character varying(40) COLLATE pg_catalog."default",
#    fips character varying(40) COLLATE pg_catalog."default",
#    land character varying(40) COLLATE pg_catalog."default",
#    email character varying(40) COLLATE pg_catalog."default",
#    url character varying(80) COLLATE pg_catalog."default",
#    image character varying(80) COLLATE pg_catalog."default",
#    eqsl smallint,
#    mqsl smallint,
#    cqzone smallint,
#    ituzone smallint,
#    firstseen timestamp without time zone,
#    lastseen timestamp without time zone,
#    qrzupdate timestamp without time zone,
#    qsostatus integer,
#    CONSTRAINT callsigns_pkey PRIMARY KEY (id),
#    CONSTRAINT callsigns_callsign_key UNIQUE (callsign),
#    CONSTRAINT callsigns_bornyear_check CHECK (bornyear > 1899),
#    CONSTRAINT callsigns_qsostatus_check CHECK (qsostatus >= 0)
#



