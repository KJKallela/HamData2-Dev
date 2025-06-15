# This is a file containing all the business logic and database actions of QSOs data table
#
# The table structure is as follows:
#
# Table: public.qsos
#    id bigint NOT NULL DEFAULT nextval('qsos_id_seq'::regclass),
#    freq numeric(10,6) NOT NULL,
#    app_pskrep_brg integer,
#    distance numeric(10,2),
#    mode character varying(10) COLLATE pg_catalog."default" NOT NULL,
#    operator_id bigint,
#    call_id bigint,
#    my_gridsquare character varying(12) COLLATE pg_catalog."default",
#    qso_date date NOT NULL,
#    time_on time without time zone NOT NULL,
#    app_pskrep_snr smallint,
#    raw_operator character varying(20) COLLATE pg_catalog."default",
#    raw_call character varying(20) COLLATE pg_catalog."default",
#    country character varying(64) COLLATE pg_catalog."default",
#    dxcc integer,
#    gridsquare character varying(12) COLLATE pg_catalog."default",
#    qso_complete character varying(10) COLLATE pg_catalog."default",
#    swl boolean DEFAULT false,
#    created_at timestamp without time zone DEFAULT now(),
#    CONSTRAINT qsos_pkey PRIMARY KEY (id),
#    CONSTRAINT qsos_call_id_fkey FOREIGN KEY (call_id)
#        REFERENCES public.callsigns (id) MATCH SIMPLE
#        ON UPDATE NO ACTION
#        ON DELETE SET NULL,
#    CONSTRAINT qsos_operator_id_fkey FOREIGN KEY (operator_id)
#       REFERENCES public.callsigns (id) MATCH SIMPLE
#        ON UPDATE NO ACTION
#        ON DELETE SET NULL


