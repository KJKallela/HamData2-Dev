# This is a file containing all the business logic and database actions of callsigns data table
#
# The table structure is as follows:
#
# -- Table: public.dxcc_codes

#    entity_code integer NOT NULL,
#    name text COLLATE pg_catalog."default",
#    country_code text COLLATE pg_catalog."default",
#    prefix text COLLATE pg_catalog."default",
#    prefix_regex text COLLATE pg_catalog."default",
#    cq text COLLATE pg_catalog."default",
#    itu text COLLATE pg_catalog."default",
#    notes text COLLATE pg_catalog."default",
#    outgoing_qsl_service boolean,
#    third_party_traffic boolean,
#    valid_start text COLLATE pg_catalog."default",
#    valid_end text COLLATE pg_catalog."default",
#    CONSTRAINT dxcc_codes_pkey PRIMARY KEY (entity_code)

