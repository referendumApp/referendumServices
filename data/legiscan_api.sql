--
-- PostgreSQL database dump
--

-- Dumped from database version 13.16 (Debian 13.16-1.pgdg120+1)
-- Dumped by pg_dump version 13.16 (Debian 13.16-1.pgdg120+1)

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

--
-- Name: update_ts_column(); Type: FUNCTION; Schema: public; Owner: legiscan_api
--

CREATE FUNCTION public.update_ts_column() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
BEGIN
  NEW.updated := now();
  RETURN NEW;	
END;
$$;


ALTER FUNCTION public.update_ts_column() OWNER TO legiscan_api;

SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: ls_bill; Type: TABLE; Schema: public; Owner: legiscan_api
--

CREATE TABLE public.ls_bill (
    bill_id integer NOT NULL,
    state_id smallint NOT NULL,
    session_id smallint NOT NULL,
    body_id smallint NOT NULL,
    current_body_id smallint NOT NULL,
    bill_type_id smallint NOT NULL,
    bill_number character varying(10) NOT NULL,
    status_id smallint NOT NULL,
    status_date date,
    title text NOT NULL,
    description text NOT NULL,
    pending_committee_id smallint NOT NULL,
    legiscan_url character varying(255) NOT NULL,
    state_url character varying(255) NOT NULL,
    change_hash character(32) NOT NULL,
    updated timestamp without time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    created timestamp without time zone DEFAULT CURRENT_TIMESTAMP NOT NULL
);


ALTER TABLE public.ls_bill OWNER TO legiscan_api;

--
-- Name: ls_bill_amendment; Type: TABLE; Schema: public; Owner: legiscan_api
--

CREATE TABLE public.ls_bill_amendment (
    amendment_id integer NOT NULL,
    bill_id integer NOT NULL,
    adopted smallint NOT NULL,
    amendment_body_id smallint NOT NULL,
    amendment_mime_id smallint NOT NULL,
    amendment_date date,
    amendment_title character varying(255) NOT NULL,
    amendment_desc text NOT NULL,
    amendment_size integer DEFAULT 0 NOT NULL,
    amendment_hash character(32) DEFAULT NULL::bpchar,
    local_copy smallint NOT NULL,
    local_fragment character varying(255) DEFAULT NULL::character varying,
    legiscan_url character varying(255) NOT NULL,
    state_url character varying(255) NOT NULL,
    updated timestamp without time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    created timestamp without time zone DEFAULT CURRENT_TIMESTAMP NOT NULL
);


ALTER TABLE public.ls_bill_amendment OWNER TO legiscan_api;

--
-- Name: ls_bill_calendar; Type: TABLE; Schema: public; Owner: legiscan_api
--

CREATE TABLE public.ls_bill_calendar (
    bill_id integer NOT NULL,
    event_hash character(8) NOT NULL,
    event_type_id smallint DEFAULT 0 NOT NULL,
    event_date date,
    event_time time without time zone,
    event_location character varying(64) NOT NULL,
    event_desc character varying(128) NOT NULL,
    updated timestamp without time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    created timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE public.ls_bill_calendar OWNER TO legiscan_api;

--
-- Name: ls_bill_history; Type: TABLE; Schema: public; Owner: legiscan_api
--

CREATE TABLE public.ls_bill_history (
    bill_id integer NOT NULL,
    history_step smallint NOT NULL,
    history_major smallint NOT NULL,
    history_body_id smallint NOT NULL,
    history_date date,
    history_action text NOT NULL
);


ALTER TABLE public.ls_bill_history OWNER TO legiscan_api;

--
-- Name: ls_bill_progress; Type: TABLE; Schema: public; Owner: legiscan_api
--

CREATE TABLE public.ls_bill_progress (
    bill_id integer NOT NULL,
    progress_step smallint NOT NULL,
    progress_date date,
    progress_event_id smallint NOT NULL
);


ALTER TABLE public.ls_bill_progress OWNER TO legiscan_api;

--
-- Name: ls_bill_reason; Type: TABLE; Schema: public; Owner: legiscan_api
--

CREATE TABLE public.ls_bill_reason (
    bill_id integer NOT NULL,
    reason_id smallint NOT NULL,
    created timestamp without time zone DEFAULT CURRENT_TIMESTAMP NOT NULL
);


ALTER TABLE public.ls_bill_reason OWNER TO legiscan_api;

--
-- Name: ls_bill_referral; Type: TABLE; Schema: public; Owner: legiscan_api
--

CREATE TABLE public.ls_bill_referral (
    bill_id integer NOT NULL,
    referral_step smallint NOT NULL,
    referral_date date,
    committee_id smallint NOT NULL
);


ALTER TABLE public.ls_bill_referral OWNER TO legiscan_api;

--
-- Name: ls_bill_sast; Type: TABLE; Schema: public; Owner: legiscan_api
--

CREATE TABLE public.ls_bill_sast (
    bill_id integer NOT NULL,
    sast_type_id smallint NOT NULL,
    sast_bill_id integer NOT NULL,
    sast_bill_number character varying(10) DEFAULT NULL::character varying
);


ALTER TABLE public.ls_bill_sast OWNER TO legiscan_api;

--
-- Name: ls_bill_sponsor; Type: TABLE; Schema: public; Owner: legiscan_api
--

CREATE TABLE public.ls_bill_sponsor (
    bill_id integer NOT NULL,
    people_id smallint NOT NULL,
    sponsor_order smallint NOT NULL,
    sponsor_type_id smallint NOT NULL
);


ALTER TABLE public.ls_bill_sponsor OWNER TO legiscan_api;

--
-- Name: ls_bill_subject; Type: TABLE; Schema: public; Owner: legiscan_api
--

CREATE TABLE public.ls_bill_subject (
    bill_id integer NOT NULL,
    subject_id integer NOT NULL
);


ALTER TABLE public.ls_bill_subject OWNER TO legiscan_api;

--
-- Name: ls_bill_supplement; Type: TABLE; Schema: public; Owner: legiscan_api
--

CREATE TABLE public.ls_bill_supplement (
    supplement_id integer NOT NULL,
    bill_id integer NOT NULL,
    supplement_type_id smallint NOT NULL,
    supplement_mime_id smallint NOT NULL,
    supplement_date date,
    supplement_title character varying(255) NOT NULL,
    supplement_desc text NOT NULL,
    supplement_size integer DEFAULT 0 NOT NULL,
    supplement_hash character(32) DEFAULT NULL::bpchar,
    local_copy smallint NOT NULL,
    local_fragment character varying(255) DEFAULT NULL::character varying,
    legiscan_url character varying(255) NOT NULL,
    state_url character varying(255) NOT NULL,
    updated timestamp without time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    created timestamp without time zone DEFAULT CURRENT_TIMESTAMP NOT NULL
);


ALTER TABLE public.ls_bill_supplement OWNER TO legiscan_api;

--
-- Name: ls_bill_text; Type: TABLE; Schema: public; Owner: legiscan_api
--

CREATE TABLE public.ls_bill_text (
    text_id integer NOT NULL,
    bill_id integer NOT NULL,
    bill_text_type_id smallint NOT NULL,
    bill_text_mime_id smallint NOT NULL,
    bill_text_date date,
    bill_text_size integer DEFAULT 0 NOT NULL,
    bill_text_hash character(32) DEFAULT NULL::bpchar,
    local_copy smallint NOT NULL,
    local_fragment character varying(255) DEFAULT NULL::character varying,
    legiscan_url character varying(255) NOT NULL,
    state_url character varying(255) NOT NULL,
    updated timestamp without time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    created timestamp without time zone DEFAULT CURRENT_TIMESTAMP NOT NULL
);


ALTER TABLE public.ls_bill_text OWNER TO legiscan_api;

--
-- Name: ls_bill_vote; Type: TABLE; Schema: public; Owner: legiscan_api
--

CREATE TABLE public.ls_bill_vote (
    roll_call_id integer NOT NULL,
    bill_id integer NOT NULL,
    roll_call_body_id smallint NOT NULL,
    roll_call_date date,
    roll_call_desc character varying(255) NOT NULL,
    yea smallint DEFAULT 0 NOT NULL,
    nay smallint DEFAULT 0 NOT NULL,
    nv smallint DEFAULT 0 NOT NULL,
    absent smallint DEFAULT 0 NOT NULL,
    total smallint DEFAULT 0 NOT NULL,
    passed smallint DEFAULT 0 NOT NULL,
    legiscan_url character varying(255) NOT NULL,
    state_url character varying(255) NOT NULL,
    updated timestamp without time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    created timestamp without time zone DEFAULT CURRENT_TIMESTAMP NOT NULL
);


ALTER TABLE public.ls_bill_vote OWNER TO legiscan_api;

--
-- Name: ls_bill_vote_detail; Type: TABLE; Schema: public; Owner: legiscan_api
--

CREATE TABLE public.ls_bill_vote_detail (
    roll_call_id integer NOT NULL,
    people_id smallint NOT NULL,
    vote_id smallint DEFAULT 0 NOT NULL
);


ALTER TABLE public.ls_bill_vote_detail OWNER TO legiscan_api;

--
-- Name: ls_body; Type: TABLE; Schema: public; Owner: legiscan_api
--

CREATE TABLE public.ls_body (
    body_id smallint NOT NULL,
    state_id smallint NOT NULL,
    role_id smallint NOT NULL,
    body_abbr character(1) NOT NULL,
    body_short character varying(16) DEFAULT NULL::character varying,
    body_name character varying(128) NOT NULL,
    body_role_abbr character varying(3) DEFAULT NULL::character varying,
    body_role_name character varying(15) DEFAULT NULL::character varying
);


ALTER TABLE public.ls_body OWNER TO legiscan_api;

--
-- Name: ls_committee; Type: TABLE; Schema: public; Owner: legiscan_api
--

CREATE TABLE public.ls_committee (
    committee_id smallint NOT NULL,
    committee_body_id smallint NOT NULL,
    committee_name character varying(128) NOT NULL
);


ALTER TABLE public.ls_committee OWNER TO legiscan_api;

--
-- Name: ls_event_type; Type: TABLE; Schema: public; Owner: legiscan_api
--

CREATE TABLE public.ls_event_type (
    event_type_id smallint NOT NULL,
    event_type_desc character varying(32) NOT NULL
);


ALTER TABLE public.ls_event_type OWNER TO legiscan_api;

--
-- Name: ls_ignore; Type: TABLE; Schema: public; Owner: legiscan_api
--

CREATE TABLE public.ls_ignore (
    bill_id integer NOT NULL,
    created timestamp without time zone DEFAULT CURRENT_TIMESTAMP NOT NULL
);


ALTER TABLE public.ls_ignore OWNER TO legiscan_api;

--
-- Name: ls_mime_type; Type: TABLE; Schema: public; Owner: legiscan_api
--

CREATE TABLE public.ls_mime_type (
    mime_id smallint NOT NULL,
    mime_type character varying(80) NOT NULL,
    mime_ext character varying(4) NOT NULL,
    is_binary smallint DEFAULT '1'::smallint NOT NULL
);


ALTER TABLE public.ls_mime_type OWNER TO legiscan_api;

--
-- Name: ls_monitor; Type: TABLE; Schema: public; Owner: legiscan_api
--

CREATE TABLE public.ls_monitor (
    bill_id integer NOT NULL,
    stance smallint DEFAULT 0 NOT NULL,
    created timestamp without time zone DEFAULT CURRENT_TIMESTAMP NOT NULL
);


ALTER TABLE public.ls_monitor OWNER TO legiscan_api;

--
-- Name: ls_party; Type: TABLE; Schema: public; Owner: legiscan_api
--

CREATE TABLE public.ls_party (
    party_id smallint NOT NULL,
    party_abbr character(1) NOT NULL,
    party_short character(3) NOT NULL,
    party_name character varying(32) NOT NULL
);


ALTER TABLE public.ls_party OWNER TO legiscan_api;

--
-- Name: ls_people; Type: TABLE; Schema: public; Owner: legiscan_api
--

CREATE TABLE public.ls_people (
    people_id smallint NOT NULL,
    state_id smallint NOT NULL,
    role_id smallint NOT NULL,
    party_id smallint DEFAULT 0 NOT NULL,
    name character varying(128) NOT NULL,
    first_name character varying(32) NOT NULL,
    middle_name character varying(32) NOT NULL,
    last_name character varying(32) NOT NULL,
    suffix character varying(32) NOT NULL,
    nickname character varying(32) NOT NULL,
    district character varying(9) DEFAULT ''::character varying,
    committee_sponsor_id smallint DEFAULT 0 NOT NULL,
    ballotpedia character varying(64) DEFAULT NULL::character varying,
    followthemoney_eid bigint DEFAULT 0 NOT NULL,
    votesmart_id integer DEFAULT 0 NOT NULL,
    knowwho_pid integer DEFAULT 0 NOT NULL,
    opensecrets_id character(9) DEFAULT NULL::bpchar,
    person_hash character(8) NOT NULL,
    updated timestamp without time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    created timestamp without time zone DEFAULT CURRENT_TIMESTAMP NOT NULL
);


ALTER TABLE public.ls_people OWNER TO legiscan_api;

--
-- Name: ls_progress; Type: TABLE; Schema: public; Owner: legiscan_api
--

CREATE TABLE public.ls_progress (
    progress_event_id smallint NOT NULL,
    progress_desc character varying(24) NOT NULL
);


ALTER TABLE public.ls_progress OWNER TO legiscan_api;

--
-- Name: ls_reason; Type: TABLE; Schema: public; Owner: legiscan_api
--

CREATE TABLE public.ls_reason (
    reason_id smallint NOT NULL,
    reason_desc character varying(32) NOT NULL
);


ALTER TABLE public.ls_reason OWNER TO legiscan_api;

--
-- Name: ls_role; Type: TABLE; Schema: public; Owner: legiscan_api
--

CREATE TABLE public.ls_role (
    role_id smallint NOT NULL,
    role_name character varying(64) NOT NULL,
    role_abbr character(3) NOT NULL
);


ALTER TABLE public.ls_role OWNER TO legiscan_api;

--
-- Name: ls_sast_type; Type: TABLE; Schema: public; Owner: legiscan_api
--

CREATE TABLE public.ls_sast_type (
    sast_id smallint NOT NULL,
    sast_description character varying(32) NOT NULL
);


ALTER TABLE public.ls_sast_type OWNER TO legiscan_api;

--
-- Name: ls_session; Type: TABLE; Schema: public; Owner: legiscan_api
--

CREATE TABLE public.ls_session (
    session_id smallint NOT NULL,
    state_id smallint NOT NULL,
    year_start smallint NOT NULL,
    year_end smallint NOT NULL,
    prefile smallint DEFAULT 0 NOT NULL,
    sine_die smallint DEFAULT 0 NOT NULL,
    prior smallint DEFAULT 0 NOT NULL,
    special smallint NOT NULL,
    session_name character varying(64) NOT NULL,
    session_title character varying(64) NOT NULL,
    session_tag character varying(32) NOT NULL,
    import_date date,
    import_hash character(32)
);


ALTER TABLE public.ls_session OWNER TO legiscan_api;

--
-- Name: ls_signal; Type: TABLE; Schema: public; Owner: legiscan_api
--

CREATE TABLE public.ls_signal (
    object_type character varying(10) NOT NULL,
    object_id integer NOT NULL,
    processed smallint NOT NULL,
    updated timestamp without time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    created timestamp without time zone DEFAULT CURRENT_TIMESTAMP NOT NULL
);


ALTER TABLE public.ls_signal OWNER TO legiscan_api;

--
-- Name: ls_sponsor_type; Type: TABLE; Schema: public; Owner: legiscan_api
--

CREATE TABLE public.ls_sponsor_type (
    sponsor_type_id smallint NOT NULL,
    sponsor_type_desc character varying(24) NOT NULL
);


ALTER TABLE public.ls_sponsor_type OWNER TO legiscan_api;

--
-- Name: ls_stance; Type: TABLE; Schema: public; Owner: legiscan_api
--

CREATE TABLE public.ls_stance (
    stance smallint NOT NULL,
    stance_desc character varying(24) NOT NULL
);


ALTER TABLE public.ls_stance OWNER TO legiscan_api;

--
-- Name: ls_state; Type: TABLE; Schema: public; Owner: legiscan_api
--

CREATE TABLE public.ls_state (
    state_id smallint NOT NULL,
    state_abbr character(2) NOT NULL,
    state_name character varying(64) NOT NULL,
    biennium smallint DEFAULT 0 NOT NULL,
    carry_over character(2) DEFAULT NULL::bpchar,
    capitol character varying(16) NOT NULL,
    latitude numeric(9,6) DEFAULT NULL::numeric,
    longitude numeric(9,6) DEFAULT NULL::numeric
);


ALTER TABLE public.ls_state OWNER TO legiscan_api;

--
-- Name: ls_subject; Type: TABLE; Schema: public; Owner: legiscan_api
--

CREATE TABLE public.ls_subject (
    subject_id integer NOT NULL,
    state_id smallint NOT NULL,
    subject_name character varying(128) NOT NULL
);


ALTER TABLE public.ls_subject OWNER TO legiscan_api;

--
-- Name: ls_supplement_type; Type: TABLE; Schema: public; Owner: legiscan_api
--

CREATE TABLE public.ls_supplement_type (
    supplement_type_id smallint NOT NULL,
    supplement_type_desc character varying(64) NOT NULL
);


ALTER TABLE public.ls_supplement_type OWNER TO legiscan_api;

--
-- Name: ls_text_type; Type: TABLE; Schema: public; Owner: legiscan_api
--

CREATE TABLE public.ls_text_type (
    bill_text_type_id smallint NOT NULL,
    bill_text_name character varying(64) NOT NULL,
    bill_text_sort smallint DEFAULT 0 NOT NULL,
    bill_text_supplement smallint DEFAULT 0 NOT NULL
);


ALTER TABLE public.ls_text_type OWNER TO legiscan_api;

--
-- Name: ls_type; Type: TABLE; Schema: public; Owner: legiscan_api
--

CREATE TABLE public.ls_type (
    bill_type_id smallint NOT NULL,
    bill_type_name character varying(64) NOT NULL,
    bill_type_abbr character varying(4) NOT NULL
);


ALTER TABLE public.ls_type OWNER TO legiscan_api;

--
-- Name: ls_variable; Type: TABLE; Schema: public; Owner: legiscan_api
--

CREATE TABLE public.ls_variable (
    name character varying(64) NOT NULL,
    value text NOT NULL
);


ALTER TABLE public.ls_variable OWNER TO legiscan_api;

--
-- Name: ls_vote; Type: TABLE; Schema: public; Owner: legiscan_api
--

CREATE TABLE public.ls_vote (
    vote_id smallint NOT NULL,
    vote_desc character varying(24) NOT NULL
);


ALTER TABLE public.ls_vote OWNER TO legiscan_api;

--
-- Name: lsv_bill; Type: VIEW; Schema: public; Owner: legiscan_api
--

CREATE VIEW public.lsv_bill AS
 SELECT b.bill_id,
    st.state_abbr,
    b.bill_number,
    b.status_id,
    p.progress_desc AS status_desc,
    b.status_date,
    b.title,
    b.description,
    b.bill_type_id,
    t.bill_type_name,
    t.bill_type_abbr,
    b.body_id,
    bo1.body_abbr,
    bo1.body_short,
    bo1.body_name,
    b.current_body_id,
    bo2.body_abbr AS current_body_abbr,
    bo2.body_short AS current_body_short,
    bo2.body_name AS current_body_name,
    b.pending_committee_id,
    c.committee_body_id AS pending_committee_body_id,
    bo3.body_abbr AS pending_committee_body_abbr,
    bo3.body_short AS pending_committee_body_short,
    bo3.body_name AS pending_committee_body_name,
    c.committee_name AS pending_committee_name,
    b.legiscan_url,
    b.state_url,
    b.change_hash,
    b.created,
    b.updated,
    b.state_id,
    st.state_name,
    b.session_id,
    s.year_start AS session_year_start,
    s.year_end AS session_year_end,
    s.prefile AS session_prefile,
    s.sine_die AS session_sine_die,
    s.prior AS session_prior,
    s.special AS session_special,
    s.session_tag,
    s.session_title,
    s.session_name
   FROM ((((((((public.ls_bill b
     JOIN public.ls_type t ON ((b.bill_type_id = t.bill_type_id)))
     JOIN public.ls_session s ON ((b.session_id = s.session_id)))
     JOIN public.ls_body bo1 ON ((b.body_id = bo1.body_id)))
     JOIN public.ls_body bo2 ON ((b.current_body_id = bo2.body_id)))
     LEFT JOIN public.ls_committee c ON ((b.pending_committee_id = c.committee_id)))
     LEFT JOIN public.ls_body bo3 ON ((c.committee_body_id = bo3.body_id)))
     LEFT JOIN public.ls_progress p ON ((b.status_id = p.progress_event_id)))
     JOIN public.ls_state st ON ((b.state_id = st.state_id)));


ALTER TABLE public.lsv_bill OWNER TO legiscan_api;

--
-- Name: lsv_bill_amendment; Type: VIEW; Schema: public; Owner: legiscan_api
--

CREATE VIEW public.lsv_bill_amendment AS
 SELECT b.bill_id,
    st.state_abbr,
    b.bill_number,
    ba.amendment_id,
    ba.amendment_date,
    ba.amendment_body_id,
    ba.amendment_size,
    ba.amendment_title,
    ba.amendment_desc,
    ba.adopted,
    ba.amendment_mime_id,
    mt.mime_type,
    mt.mime_ext,
    ba.amendment_hash,
    ba.legiscan_url,
    ba.state_url,
    ba.local_copy,
    ba.local_fragment,
    b.state_id,
    st.state_name,
    b.session_id,
    b.body_id,
    b.current_body_id,
    b.bill_type_id,
    b.status_id,
    b.pending_committee_id,
    ba.created,
    ba.updated
   FROM (((public.ls_bill b
     JOIN public.ls_bill_amendment ba ON ((b.bill_id = ba.bill_id)))
     JOIN public.ls_mime_type mt ON ((ba.amendment_mime_id = mt.mime_id)))
     JOIN public.ls_state st ON ((b.state_id = st.state_id)));


ALTER TABLE public.lsv_bill_amendment OWNER TO legiscan_api;

--
-- Name: lsv_bill_calendar; Type: VIEW; Schema: public; Owner: legiscan_api
--

CREATE VIEW public.lsv_bill_calendar AS
 SELECT b.bill_id,
    st.state_abbr,
    b.bill_number,
    bc.event_date,
    bc.event_time,
    bc.event_location,
    bc.event_desc,
    bc.event_type_id,
    et.event_type_desc,
    bc.event_hash,
    b.pending_committee_id,
    c.committee_body_id AS pending_committee_body_id,
    bo.body_abbr AS pending_committee_body_abbr,
    bo.body_short AS pending_committee_body_short,
    c.committee_name AS pending_committee_name,
    bc.created,
    bc.updated,
    b.state_id,
    st.state_name,
    b.session_id,
    b.body_id,
    b.current_body_id,
    b.bill_type_id,
    b.status_id
   FROM (((((public.ls_bill b
     JOIN public.ls_bill_calendar bc ON ((b.bill_id = bc.bill_id)))
     JOIN public.ls_event_type et ON ((bc.event_type_id = et.event_type_id)))
     LEFT JOIN public.ls_committee c ON ((b.pending_committee_id = c.committee_id)))
     LEFT JOIN public.ls_body bo ON ((c.committee_body_id = bo.body_id)))
     JOIN public.ls_state st ON ((b.state_id = st.state_id)));


ALTER TABLE public.lsv_bill_calendar OWNER TO legiscan_api;

--
-- Name: lsv_bill_history; Type: VIEW; Schema: public; Owner: legiscan_api
--

CREATE VIEW public.lsv_bill_history AS
 SELECT b.bill_id,
    st.state_abbr,
    b.bill_number,
    bh.history_step,
    bh.history_date,
    bo.body_short AS history_body_short,
    bh.history_action,
    bh.history_body_id,
    bo.body_abbr AS history_body_abbr,
    bo.body_name AS history_body_name,
    b.state_id,
    st.state_name,
    b.session_id,
    b.body_id,
    b.current_body_id,
    b.bill_type_id,
    b.status_id,
    b.pending_committee_id
   FROM (((public.ls_bill b
     JOIN public.ls_bill_history bh ON ((b.bill_id = bh.bill_id)))
     LEFT JOIN public.ls_body bo ON ((bh.history_body_id = bo.body_id)))
     JOIN public.ls_state st ON ((b.state_id = st.state_id)));


ALTER TABLE public.lsv_bill_history OWNER TO legiscan_api;

--
-- Name: lsv_bill_reason; Type: VIEW; Schema: public; Owner: legiscan_api
--

CREATE VIEW public.lsv_bill_reason AS
 SELECT b.bill_id,
    st.state_abbr,
    b.bill_number,
    br.reason_id,
    r.reason_desc,
    br.created AS change_time,
    b.state_id,
    st.state_name,
    b.session_id,
    b.body_id,
    b.current_body_id,
    b.bill_type_id,
    b.status_id,
    b.pending_committee_id
   FROM (((public.ls_bill b
     JOIN public.ls_bill_reason br ON ((b.bill_id = br.bill_id)))
     JOIN public.ls_reason r ON ((br.reason_id = r.reason_id)))
     JOIN public.ls_state st ON ((b.state_id = st.state_id)));


ALTER TABLE public.lsv_bill_reason OWNER TO legiscan_api;

--
-- Name: lsv_bill_referral; Type: VIEW; Schema: public; Owner: legiscan_api
--

CREATE VIEW public.lsv_bill_referral AS
 SELECT b.bill_id,
    st.state_abbr,
    b.bill_number,
    br.referral_step,
    br.referral_date,
    br.committee_id AS referral_committee_id,
    bo1.body_abbr AS referral_committee_body_abbr,
    bo1.body_short AS referral_committee_body_short,
    bo1.body_name AS referral_committee_body_name,
    c1.committee_name AS referral_committee_name,
    b.pending_committee_id,
    bo2.body_abbr AS pending_committee_body_abbr,
    bo2.body_short AS pending_committee_body_short,
    bo2.body_name AS pending_committee_body_name,
    c2.committee_name AS pending_committee_name,
    b.state_id,
    st.state_name,
    b.session_id,
    b.body_id,
    b.current_body_id,
    b.bill_type_id,
    b.status_id
   FROM ((((((public.ls_bill b
     JOIN public.ls_bill_referral br ON ((b.bill_id = br.bill_id)))
     LEFT JOIN public.ls_committee c1 ON ((br.committee_id = c1.committee_id)))
     JOIN public.ls_body bo1 ON ((c1.committee_body_id = bo1.body_id)))
     LEFT JOIN public.ls_committee c2 ON ((b.pending_committee_id = c2.committee_id)))
     LEFT JOIN public.ls_body bo2 ON ((c2.committee_body_id = bo2.body_id)))
     JOIN public.ls_state st ON ((b.state_id = st.state_id)));


ALTER TABLE public.lsv_bill_referral OWNER TO legiscan_api;

--
-- Name: lsv_bill_sast; Type: VIEW; Schema: public; Owner: legiscan_api
--

CREATE VIEW public.lsv_bill_sast AS
 SELECT b1.bill_id,
    st1.state_abbr,
    b1.bill_number,
    bs.sast_type_id,
    sty.sast_description,
    b1.state_id,
    b1.session_id,
    b1.body_id,
    b1.current_body_id,
    b1.bill_type_id,
    b1.status_id,
    b1.pending_committee_id,
    bs.sast_bill_id,
    st2.state_abbr AS sast_state_abbr,
    bs.sast_bill_number,
    b2.state_id AS sast_state_id,
    b2.session_id AS sast_session_id,
    b2.body_id AS sast_body_id,
    b2.current_body_id AS sast_current_body_id,
    b2.bill_type_id AS sast_bill_type_id,
    b2.status_id AS sast_status_id,
    b2.pending_committee_id AS sast_pending_committee_id
   FROM (((((public.ls_bill b1
     JOIN public.ls_bill_sast bs ON ((b1.bill_id = bs.bill_id)))
     JOIN public.ls_sast_type sty ON ((bs.sast_type_id = sty.sast_id)))
     JOIN public.ls_state st1 ON ((b1.state_id = st1.state_id)))
     LEFT JOIN public.ls_bill b2 ON ((bs.sast_bill_id = b2.bill_id)))
     LEFT JOIN public.ls_state st2 ON ((b2.state_id = st2.state_id)));


ALTER TABLE public.lsv_bill_sast OWNER TO legiscan_api;

--
-- Name: lsv_bill_sponsor; Type: VIEW; Schema: public; Owner: legiscan_api
--

CREATE VIEW public.lsv_bill_sponsor AS
 SELECT b.bill_id,
    st.state_abbr,
    b.bill_number,
    bs.people_id,
    bs.sponsor_order,
    bs.sponsor_type_id,
    spt.sponsor_type_desc,
    p.party_id,
    pa.party_abbr,
    pa.party_name,
    p.role_id,
    r.role_abbr,
    r.role_name,
    p.name,
    p.first_name,
    p.middle_name,
    p.last_name,
    p.suffix,
    p.nickname,
    p.ballotpedia,
    p.followthemoney_eid,
    p.votesmart_id,
    p.opensecrets_id,
    p.knowwho_pid,
    p.committee_sponsor_id,
    c.committee_body_id AS committee_sponsor_body_id,
    c.committee_name AS committee_sponsor_name,
    p.person_hash,
    b.state_id,
    st.state_name,
    b.session_id,
    b.body_id,
    b.current_body_id,
    b.bill_type_id,
    b.status_id,
    b.pending_committee_id
   FROM (((((((public.ls_bill b
     JOIN public.ls_bill_sponsor bs ON ((b.bill_id = bs.bill_id)))
     JOIN public.ls_sponsor_type spt ON ((bs.sponsor_type_id = spt.sponsor_type_id)))
     JOIN public.ls_people p ON ((bs.people_id = p.people_id)))
     LEFT JOIN public.ls_committee c ON ((p.committee_sponsor_id = c.committee_id)))
     JOIN public.ls_party pa ON ((p.party_id = pa.party_id)))
     JOIN public.ls_role r ON ((p.role_id = r.role_id)))
     JOIN public.ls_state st ON ((b.state_id = st.state_id)));


ALTER TABLE public.lsv_bill_sponsor OWNER TO legiscan_api;

--
-- Name: lsv_bill_subject; Type: VIEW; Schema: public; Owner: legiscan_api
--

CREATE VIEW public.lsv_bill_subject AS
 SELECT b.bill_id,
    st.state_abbr,
    b.bill_number,
    bs.subject_id,
    s.subject_name,
    b.state_id,
    st.state_name,
    b.session_id,
    b.body_id,
    b.current_body_id,
    b.bill_type_id,
    b.status_id,
    b.pending_committee_id
   FROM (((public.ls_bill b
     JOIN public.ls_bill_subject bs ON ((b.bill_id = bs.bill_id)))
     JOIN public.ls_subject s ON ((bs.subject_id = s.subject_id)))
     JOIN public.ls_state st ON ((b.state_id = st.state_id)));


ALTER TABLE public.lsv_bill_subject OWNER TO legiscan_api;

--
-- Name: lsv_bill_supplement; Type: VIEW; Schema: public; Owner: legiscan_api
--

CREATE VIEW public.lsv_bill_supplement AS
 SELECT b.bill_id,
    st.state_abbr,
    b.bill_number,
    bs.supplement_id,
    bs.supplement_date,
    bs.supplement_type_id,
    sut.supplement_type_desc,
    bs.supplement_size,
    bs.supplement_mime_id,
    mt.mime_type,
    mt.mime_ext,
    bs.supplement_hash,
    bs.legiscan_url,
    bs.state_url,
    bs.local_copy,
    bs.local_fragment,
    b.state_id,
    st.state_name,
    b.session_id,
    b.body_id,
    b.current_body_id,
    b.bill_type_id,
    b.status_id,
    b.pending_committee_id,
    bs.created,
    bs.updated
   FROM ((((public.ls_bill b
     JOIN public.ls_bill_supplement bs ON ((b.bill_id = bs.bill_id)))
     JOIN public.ls_supplement_type sut ON ((bs.supplement_type_id = sut.supplement_type_id)))
     JOIN public.ls_mime_type mt ON ((bs.supplement_mime_id = mt.mime_id)))
     JOIN public.ls_state st ON ((b.state_id = st.state_id)));


ALTER TABLE public.lsv_bill_supplement OWNER TO legiscan_api;

--
-- Name: lsv_bill_text; Type: VIEW; Schema: public; Owner: legiscan_api
--

CREATE VIEW public.lsv_bill_text AS
 SELECT b.bill_id,
    st.state_abbr,
    b.bill_number,
    bt.text_id,
    bt.bill_text_size,
    bt.bill_text_date,
    bt.bill_text_type_id,
    tt.bill_text_name,
    tt.bill_text_sort,
    bt.bill_text_mime_id,
    mt.mime_type,
    mt.mime_ext,
    bt.bill_text_hash,
    bt.legiscan_url,
    bt.state_url,
    bt.local_copy,
    bt.local_fragment,
    b.state_id,
    st.state_name,
    b.session_id,
    b.body_id,
    b.current_body_id,
    b.bill_type_id,
    b.status_id,
    b.pending_committee_id,
    bt.created,
    bt.updated
   FROM ((((public.ls_bill b
     JOIN public.ls_bill_text bt ON ((b.bill_id = bt.bill_id)))
     JOIN public.ls_text_type tt ON ((bt.bill_text_type_id = tt.bill_text_type_id)))
     JOIN public.ls_mime_type mt ON ((bt.bill_text_mime_id = mt.mime_id)))
     JOIN public.ls_state st ON ((b.state_id = st.state_id)));


ALTER TABLE public.lsv_bill_text OWNER TO legiscan_api;

--
-- Name: lsv_bill_vote; Type: VIEW; Schema: public; Owner: legiscan_api
--

CREATE VIEW public.lsv_bill_vote AS
 SELECT b.bill_id,
    st.state_abbr,
    b.bill_number,
    bv.roll_call_id,
    bv.roll_call_date,
    bv.roll_call_desc,
    bv.roll_call_body_id,
    bo.body_abbr AS roll_call_body_abbr,
    bo.body_short AS roll_call_body_short,
    bo.body_name AS roll_call_body_name,
    bv.yea,
    bv.nay,
    bv.nv,
    bv.absent,
    bv.total,
    bv.passed,
    bv.legiscan_url,
    bv.state_url,
    b.state_id,
    st.state_name,
    b.session_id,
    b.body_id,
    b.current_body_id,
    b.bill_type_id,
    b.status_id,
    b.pending_committee_id,
    bv.created,
    bv.updated
   FROM (((public.ls_bill b
     JOIN public.ls_bill_vote bv ON ((b.bill_id = bv.bill_id)))
     JOIN public.ls_body bo ON ((bv.roll_call_body_id = bo.body_id)))
     JOIN public.ls_state st ON ((b.state_id = st.state_id)));


ALTER TABLE public.lsv_bill_vote OWNER TO legiscan_api;

--
-- Name: lsv_bill_vote_detail; Type: VIEW; Schema: public; Owner: legiscan_api
--

CREATE VIEW public.lsv_bill_vote_detail AS
 SELECT b.bill_id,
    st.state_abbr,
    b.bill_number,
    bv.roll_call_id,
    bvd.people_id,
    bvd.vote_id,
    v.vote_desc,
    p.party_id,
    pa.party_abbr,
    p.role_id,
    r.role_abbr,
    r.role_name,
    p.name,
    p.first_name,
    p.middle_name,
    p.last_name,
    p.suffix,
    p.nickname,
    p.ballotpedia,
    p.followthemoney_eid,
    p.votesmart_id,
    p.opensecrets_id,
    p.knowwho_pid,
    p.person_hash,
    b.state_id,
    st.state_name,
    b.session_id,
    b.body_id,
    b.current_body_id,
    b.bill_type_id,
    b.status_id,
    b.pending_committee_id
   FROM (((((((public.ls_bill b
     JOIN public.ls_bill_vote bv ON ((b.bill_id = bv.bill_id)))
     JOIN public.ls_bill_vote_detail bvd ON ((bv.roll_call_id = bvd.roll_call_id)))
     JOIN public.ls_vote v ON ((bvd.vote_id = v.vote_id)))
     JOIN public.ls_people p ON ((bvd.people_id = p.people_id)))
     JOIN public.ls_party pa ON ((p.party_id = pa.party_id)))
     JOIN public.ls_role r ON ((p.role_id = r.role_id)))
     JOIN public.ls_state st ON ((b.state_id = st.state_id)));


ALTER TABLE public.lsv_bill_vote_detail OWNER TO legiscan_api;

--
-- Data for Name: ls_bill; Type: TABLE DATA; Schema: public; Owner: legiscan_api
--

COPY public.ls_bill (bill_id, state_id, session_id, body_id, current_body_id, bill_type_id, bill_number, status_id, status_date, title, description, pending_committee_id, legiscan_url, state_url, change_hash, updated, created) FROM stdin;
1642361	52	2041	115	115	2	SR2	1	2023-01-03	A resolution informing the House of Representatives that a quorum of the Senate is assembled.	A resolution informing the House of Representatives that a quorum of the Senate is assembled.	0	https://legiscan.com/US/bill/SR2/2023	https://www.congress.gov/bill/118th-congress/senate-resolution/2/all-info	8f0a0a23714699c59af75f8673bd34cb	2024-09-29 22:58:19	2024-09-29 22:58:19
1642332	52	2041	115	115	2	SR5	1	2023-01-03	A resolution notifying the House of Representatives of the election of a President pro tempore.	A resolution notifying the House of Representatives of the election of a President pro tempore.	0	https://legiscan.com/US/bill/SR5/2023	https://www.congress.gov/bill/118th-congress/senate-resolution/5/all-info	d6e415838a67d908b1eca4cebec3be4c	2024-09-29 22:58:20	2024-09-29 22:58:20
1642307	52	2041	115	115	2	SR6	1	2023-01-03	A resolution fixing the hour of daily meeting of the Senate.	A resolution fixing the hour of daily meeting of the Senate.	0	https://legiscan.com/US/bill/SR6/2023	https://www.congress.gov/bill/118th-congress/senate-resolution/6/all-info	58d937dafa40eae4ceb9f774789c0093	2024-09-29 22:58:20	2024-09-29 22:58:20
1642421	52	2041	115	115	2	SR7	1	2023-01-03	A resolution fixing the hour of daily meeting of the Senate.	A resolution fixing the hour of daily meeting of the Senate.	0	https://legiscan.com/US/bill/SR7/2023	https://www.congress.gov/bill/118th-congress/senate-resolution/7/all-info	847175daddcebe2a79ca1f1e5555d26c	2024-09-29 22:58:20	2024-09-29 22:58:20
1642389	52	2041	115	115	2	SR9	1	2023-01-03	A resolution to make effective appointment of Deputy Senate Legal Counsel.	A resolution to make effective appointment of Deputy Senate Legal Counsel.	0	https://legiscan.com/US/bill/SR9/2023	https://www.congress.gov/bill/118th-congress/senate-resolution/9/all-info	32fa325baaf8d0d3475291b43e14d920	2024-09-29 22:58:20	2024-09-29 22:58:20
1741372	52	2041	114	114	1	HB1	1	2023-03-14	Lower Energy Costs Act TAPP American Resources Act Water Quality Certification and Energy Project Improvement Act of 2023 Transparency, Accountability, Permitting, and Production of American Resources Act	To lower energy costs by increasing American energy production, exports, infrastructure, and critical minerals processing, by promoting transparency, accountability, permitting, and production of American resources, and by improving water quality certification and energy projects, and for other purposes.	0	https://legiscan.com/US/bill/HB1/2023	https://www.congress.gov/bill/118th-congress/house-bill/1/all-info	5db9f4c551f54eecfce1768f5e0bac1b	2024-09-29 20:54:53	2024-09-29 20:54:53
1724917	52	2041	114	115	1	HB5	2	2023-03-27	Parents Bill of Rights Act	To ensure the rights of parents are honored and protected in the Nation's public schools.	2328	https://legiscan.com/US/bill/HB5/2023	https://www.congress.gov/bill/118th-congress/house-bill/5/all-info	b81d99d571318fbddf0cef958366a269	2024-09-29 20:56:02	2024-09-29 20:56:02
\.


--
-- Data for Name: ls_bill_amendment; Type: TABLE DATA; Schema: public; Owner: legiscan_api
--

COPY public.ls_bill_amendment (amendment_id, bill_id, adopted, amendment_body_id, amendment_mime_id, amendment_date, amendment_title, amendment_desc, amendment_size, amendment_hash, local_copy, local_fragment, legiscan_url, state_url, updated, created) FROM stdin;
\.


--
-- Data for Name: ls_bill_calendar; Type: TABLE DATA; Schema: public; Owner: legiscan_api
--

COPY public.ls_bill_calendar (bill_id, event_hash, event_type_id, event_date, event_time, event_location, event_desc, updated, created) FROM stdin;
\.


--
-- Data for Name: ls_bill_history; Type: TABLE DATA; Schema: public; Owner: legiscan_api
--

COPY public.ls_bill_history (bill_id, history_step, history_major, history_body_id, history_date, history_action) FROM stdin;
1642361	1	0	115	2023-01-03	Submitted in the Senate, considered, and agreed to without amendment by Unanimous Consent. (consideration: CR S6; text: CR S6)
1642361	2	0	115	2023-01-03	Message on Senate action sent to the House.
1642332	1	0	115	2023-01-03	Submitted in the Senate, considered, and agreed to without amendment by Unanimous Consent. (consideration: CR S7; text: CR S7)
1642332	2	0	115	2023-01-03	Message on Senate action sent to the House.
1642307	1	0	115	2023-01-03	Submitted in the Senate, considered, and agreed to without amendment by Unanimous Consent. (consideration: CR S7; text: CR S7)
1642421	1	0	115	2023-01-03	Submitted in the Senate. Placed on Senate Legislative Calendar under Over, Under the Rule. (text: CR S20)
1642389	1	0	115	2023-01-03	Submitted in the Senate, considered, and agreed to without amendment by Unanimous Consent. (consideration: CR S7; text: CR S7)
1741372	1	0	114	2023-03-14	Introduced in House
1741372	2	1	114	2023-03-14	Referred to the Committee on Natural Resources, and in addition to the Committees on Energy and Commerce, Agriculture, Transportation and Infrastructure, and the Budget, for a period to be subsequently determined by the Speaker, in each case for consideration of such provisions as fall within the jurisdiction of the committee concerned.
\.


--
-- Data for Name: ls_bill_progress; Type: TABLE DATA; Schema: public; Owner: legiscan_api
--

COPY public.ls_bill_progress (bill_id, progress_step, progress_date, progress_event_id) FROM stdin;
1642361	1	2023-01-03	1
1642332	1	2023-01-03	1
1642307	1	2023-01-03	1
1642421	1	2023-01-03	1
1642389	1	2023-01-03	1
1741372	1	2023-03-14	1
1741372	2	2023-03-14	9
1741372	3	2023-03-15	9
1741372	4	2023-03-15	9
1741372	5	2023-03-15	9
1741372	6	2023-03-15	9
1741372	7	2023-03-15	9
1741372	8	2023-03-24	9
\.


--
-- Data for Name: ls_bill_reason; Type: TABLE DATA; Schema: public; Owner: legiscan_api
--

COPY public.ls_bill_reason (bill_id, reason_id, created) FROM stdin;
\.


--
-- Data for Name: ls_bill_referral; Type: TABLE DATA; Schema: public; Owner: legiscan_api
--

COPY public.ls_bill_referral (bill_id, referral_step, referral_date, committee_id) FROM stdin;
\.


--
-- Data for Name: ls_bill_sast; Type: TABLE DATA; Schema: public; Owner: legiscan_api
--

COPY public.ls_bill_sast (bill_id, sast_type_id, sast_bill_id, sast_bill_number) FROM stdin;
\.


--
-- Data for Name: ls_bill_sponsor; Type: TABLE DATA; Schema: public; Owner: legiscan_api
--

COPY public.ls_bill_sponsor (bill_id, people_id, sponsor_order, sponsor_type_id) FROM stdin;
1642361	9414	1	1
1642332	9414	1	1
1642307	9414	1	1
1642421	9414	1	1
1642389	9414	1	1
1741372	9176	21	2
1741372	9193	2	2
1741372	9209	34	2
1741372	9216	14	2
1741372	9217	8	2
1741372	9273	4	2
1741372	9274	25	2
1741372	9329	42	2
1741372	9346	26	2
1741372	9381	44	2
1741372	9384	1	1
1741372	11049	43	2
1741372	11077	29	2
1741372	14084	23	2
1741372	14922	22	2
1741372	16447	15	2
1741372	16454	18	2
1741372	16477	5	2
1741372	16480	3	2
1741372	16483	27	2
1741372	16490	24	2
1741372	16503	6	2
1741372	17717	45	2
1741372	18300	17	2
1741372	18303	9	2
1741372	18335	33	2
1741372	19436	12	2
1741372	19676	20	2
1741372	20040	13	2
1741372	20049	19	2
1741372	20076	11	2
1741372	20083	7	2
1741372	20092	32	2
1741372	20114	50	2
1741372	21927	10	2
1741372	21928	30	2
1741372	21940	40	2
1741372	21941	31	2
1741372	21945	49	2
1741372	21963	47	2
1741372	21971	16	2
1741372	21974	46	2
1741372	22915	35	2
1741372	22967	28	2
1741372	23997	41	2
1741372	24007	36	2
1741372	24012	38	2
1741372	24026	39	2
1741372	24039	48	2
1741372	24069	37	2
\.
1724917	9157	83	2
1724917	9175	25	2
1724917	9176	118	2
1724917	9192	71	2
1724917	9193	50	2
1724917	9197	97	2
1724917	9211	35	2
1724917	9217	53	2
1724917	9237	89	2
1724917	9269	7	2
1724917	9274	44	2
1724917	9329	11	2
1724917	9337	10	2
1724917	9346	95	2
1724917	9368	77	2
1724917	9384	2	2
1724917	9389	64	2
1724917	11042	93	2
1724917	11047	66	2
1724917	11049	51	2
1724917	11058	61	2
1724917	11077	111	2
1724917	11124	29	2
1724917	11137	31	2
1724917	13318	99	2
1724917	14084	6	2
1724917	14923	47	2
1724917	14924	84	2
1724917	15228	102	2
1724917	15240	36	2
1724917	16447	13	2
1724917	16449	109	2
1724917	16452	39	2
1724917	16454	103	2
1724917	16458	3	2
1724917	16460	12	2
1724917	16471	22	2
1724917	16472	55	2
1724917	16473	23	2
1724917	16476	65	2
1724917	16477	4	2
1724917	16483	70	2
1724917	16503	49	2
1724917	17704	112	2
1724917	17717	87	2
1724917	18288	14	2
1724917	18303	96	2
1724917	18310	26	2
1724917	18313	5	2
1724917	18317	42	2
1724917	18330	48	2
1724917	18331	15	2
1724917	18335	28	2
1724917	19370	78	2
1724917	19407	38	2
1724917	19646	121	2
1724917	19676	63	2
1724917	19692	73	2
1724917	20042	104	2
1724917	20047	114	2
1724917	20049	54	2
1724917	20064	56	2
1724917	20065	113	2
1724917	20066	59	2
1724917	20075	120	2
1724917	20076	72	2
1724917	20083	40	2
1724917	20096	21	2
1724917	20108	117	2
1724917	20109	46	2
1724917	20110	80	2
1724917	20120	81	2
1724917	20121	41	2
1724917	21646	43	2
1724917	21647	33	2
1724917	21921	34	2
1724917	21926	17	2
1724917	21927	115	2
1724917	21928	69	2
1724917	21930	107	2
1724917	21931	57	2
1724917	21935	88	2
1724917	21938	82	2
1724917	21939	37	2
1724917	21940	24	2
1724917	21941	8	2
1724917	21945	94	2
1724917	21946	86	2
1724917	21950	100	2
1724917	21961	91	2
1724917	21963	101	2
1724917	21965	45	2
1724917	21966	58	2
1724917	21967	30	2
1724917	21968	60	2
1724917	21969	123	2
1724917	21970	98	2
1724917	21974	16	2
1724917	21977	9	2
1724917	22915	1	1
1724917	22947	74	2
1724917	22967	68	2
1724917	23162	27	2
1724917	23998	18	2
1724917	24009	90	2
1724917	24013	85	2
1724917	24015	67	2
1724917	24016	32	2
1724917	24023	20	2
1724917	24025	122	2
1724917	24026	75	2
1724917	24035	62	2
1724917	24036	79	2
1724917	24038	76	2
1724917	24039	92	2
1724917	24047	108	2
1724917	24048	52	2
1724917	24050	105	2
1724917	24053	116	2
1724917	24055	106	2
1724917	24060	110	2
1724917	24067	119	2
1724917	24069	19	2


--
-- Data for Name: ls_bill_subject; Type: TABLE DATA; Schema: public; Owner: legiscan_api
--

COPY public.ls_bill_subject (bill_id, subject_id) FROM stdin;
1642361	13525
1642332	13525
1642307	13525
1642421	13525
1642389	13525
1741372	13399
1724917	13329
\.


--
-- Data for Name: ls_bill_supplement; Type: TABLE DATA; Schema: public; Owner: legiscan_api
--

COPY public.ls_bill_supplement (supplement_id, bill_id, supplement_type_id, supplement_mime_id, supplement_date, supplement_title, supplement_desc, supplement_size, supplement_hash, local_copy, local_fragment, legiscan_url, state_url, updated, created) FROM stdin;
\.


--
-- Data for Name: ls_bill_text; Type: TABLE DATA; Schema: public; Owner: legiscan_api
--

COPY public.ls_bill_text (text_id, bill_id, bill_text_type_id, bill_text_mime_id, bill_text_date, bill_text_size, bill_text_hash, local_copy, local_fragment, legiscan_url, state_url, updated, created) FROM stdin;
2624356	1642361	5	2	2023-01-04	188917	c6eb2219f61490bfbe9940ae1f00af0f	0	\N	https://legiscan.com/US/text/SR2/id/2624356	https://www.congress.gov/118/bills/sres2/BILLS-118sres2ats.pdf	2024-09-29 22:58:19	2024-09-29 22:58:19
2624450	1642332	5	2	2023-01-04	188916	f0f89fff152412710bb2906fdb719100	0	\N	https://legiscan.com/US/text/SR5/id/2624450	https://www.congress.gov/118/bills/sres5/BILLS-118sres5ats.pdf	2024-09-29 22:58:20	2024-09-29 22:58:20
2624460	1642307	5	2	2023-01-04	188854	67132aaf4879162eb82b76eedfc7c57e	0	\N	https://legiscan.com/US/text/SR6/id/2624460	https://www.congress.gov/118/bills/sres6/BILLS-118sres6ats.pdf	2024-09-29 22:58:20	2024-09-29 22:58:20
2624933	1642421	1	2	2023-01-06	188851	072de7c01beac7a28481b4ca2defb27e	0	\N	https://legiscan.com/US/text/SR7/id/2624933	https://www.congress.gov/118/bills/sres7/BILLS-118sres7is.pdf	2024-09-29 22:58:20	2024-09-29 22:58:20
2624417	1642389	5	2	2023-01-04	189024	8b8411ce6fb4cbb47fe35987cc553ea6	0	\N	https://legiscan.com/US/text/SR9/id/2624417	https://www.congress.gov/118/bills/sres9/BILLS-118sres9ats.pdf	2024-09-29 22:58:20	2024-09-29 22:58:20
2746931	1741372	1	2	2023-03-15	505174	6d3ae2f2eb69aa701e45d279aff1564f	0	\N	https://legiscan.com/US/text/HB1/id/2746931	https://www.congress.gov/118/bills/hr1/BILLS-118hr1ih.pdf	2024-09-29 20:54:53	2024-09-29 20:54:53
2769605	1741372	4	2	2023-04-03	419110	4a4a28978c9dff9636fc022c596687e7	0	\N	https://legiscan.com/US/text/HB1/id/2769605	https://www.congress.gov/118/bills/hr1/BILLS-118hr1eh.pdf	2024-09-29 20:54:53	2024-09-29 20:54:53
2723963	1724917	1	2	2023-03-01	264937	b6bb2065cb7ab2ad89ba59322521db49	0	\N	https://legiscan.com/US/text/HB5/id/2723963	https://www.congress.gov/118/bills/hr5/BILLS-118hr5ih.pdf	2024-09-29 20:56:02	2024-09-29 20:56:02
2746970	1724917	1	2	2023-03-15	279863	ca021a041b15b1d9c4c1b53123326931	0	\N	https://legiscan.com/US/text/HB5/id/2746970	https://www.congress.gov/118/bills/hr5/BILLS-118hr5rh.pdf	2024-09-29 20:56:02	2024-09-29 20:56:02
2761423	1724917	4	2	2023-03-28	163102	682304c392983cafb0af6381c5812251	0	\N	https://legiscan.com/US/text/HB5/id/2761423	https://www.congress.gov/118/bills/hr5/BILLS-118hr5eh.pdf	2024-09-29 20:56:02	2024-09-29 20:56:02
\.


--
-- Data for Name: ls_bill_vote; Type: TABLE DATA; Schema: public; Owner: legiscan_api
--

COPY public.ls_bill_vote (roll_call_id, bill_id, roll_call_body_id, roll_call_date, roll_call_desc, yea, nay, nv, absent, total, passed, legiscan_url, state_url, updated, created) FROM stdin;
1290285	1741372	114	2023-03-30	On Agreeing to the Amendment RC# 175	23	109	0	8	440	1	https://legiscan.com/US/rollcall/HB1/id/1290285	https://clerk.house.gov/Votes/2023175	2024-09-29 21:50:52.852903	2024-09-29 20:54:53
1290286	1741372	114	2023-03-30	On Agreeing to the Amendment RC# 176	205	228	0	7	440	0	https://legiscan.com/US/rollcall/HB1/id/1290286	https://clerk.house.gov/Votes/2023176	2024-09-29 21:50:54.710454	2024-09-29 20:54:53
1290287	1741372	114	2023-03-30	On Agreeing to the Amendment RC# 177	405	24	0	11	440	1	https://legiscan.com/US/rollcall/HB1/id/1290287	https://clerk.house.gov/Votes/2023177	2024-09-29 21:50:56.718596	2024-09-29 20:54:53
1290288	1741372	114	2023-03-30	On Agreeing to the Amendment RC# 178	201	230	0	9	440	0	https://legiscan.com/US/rollcall/HB1/id/1290288	https://clerk.house.gov/Votes/2023178	2024-09-29 21:50:58.556783	2024-09-29 20:54:53
1290289	1741372	114	2023-03-30	On Agreeing to the Amendment RC# 179	244	189	0	7	440	1	https://legiscan.com/US/rollcall/HB1/id/1290289	https://clerk.house.gov/Votes/2023179	2024-09-29 21:51:00.711614	2024-09-29 20:54:53
1290290	1741372	114	2023-03-30	On Agreeing to the Amendment RC# 180	220	213	0	7	440	1	https://legiscan.com/US/rollcall/HB1/id/1290290	https://clerk.house.gov/Votes/2023180	2024-09-29 21:51:02.699607	2024-09-29 20:54:53
1290291	1741372	114	2023-03-30	On Motion to Recommit RC# 181	207	222	0	6	435	0	https://legiscan.com/US/rollcall/HB1/id/1290291	https://clerk.house.gov/Votes/2023181	2024-09-29 21:51:04.566979	2024-09-29 20:54:53
1290292	1741372	114	2023-03-30	On Passage RC# 182	225	204	0	6	435	1	https://legiscan.com/US/rollcall/HB1/id/1290292	https://clerk.house.gov/Votes/2023182	2024-09-29 21:51:06.41839	2024-09-29 20:54:53
1289042	1741372	114	2023-03-29	On Agreeing to the Amendment RC# 167	221	208	0	11	440	1	https://legiscan.com/US/rollcall/HB1/id/1289042	https://clerk.house.gov/Votes/2023167	2024-09-29 21:50:36.650009	2024-09-29 20:54:53
1289043	1741372	114	2023-03-29	On Agreeing to the Amendment RC# 168	228	206	0	6	440	1	https://legiscan.com/US/rollcall/HB1/id/1289043	https://clerk.house.gov/Votes/2023168	2024-09-29 21:50:40.353048	2024-09-29 20:54:53
1289044	1741372	114	2023-03-29	On Agreeing to the Amendment RC# 169	245	189	0	6	440	1	https://legiscan.com/US/rollcall/HB1/id/1289044	https://clerk.house.gov/Votes/2023169	2024-09-29 21:50:42.240541	2024-09-29 20:54:53
1289045	1741372	114	2023-03-29	On Agreeing to the Amendment RC# 170	268	163	0	9	440	1	https://legiscan.com/US/rollcall/HB1/id/1289045	https://clerk.house.gov/Votes/2023170	2024-09-29 21:50:44.002623	2024-09-29 20:54:53
1289046	1741372	114	2023-03-29	On Agreeing to the Amendment RC# 171	251	181	0	8	440	1	https://legiscan.com/US/rollcall/HB1/id/1289046	https://clerk.house.gov/Votes/2023171	2024-09-29 21:50:45.809417	2024-09-29 20:54:53
1289047	1741372	114	2023-03-29	On Agreeing to the Amendment RC# 172	210	223	0	7	440	0	https://legiscan.com/US/rollcall/HB1/id/1289047	https://clerk.house.gov/Votes/2023172	2024-09-29 21:50:47.645147	2024-09-29 20:54:53
1289048	1741372	114	2023-03-29	On Agreeing to the Amendment RC# 173	96	336	0	8	440	0	https://legiscan.com/US/rollcall/HB1/id/1289048	https://clerk.house.gov/Votes/2023173	2024-09-29 21:50:49.423232	2024-09-29 20:54:53
1290284	1741372	114	2023-03-30	On Agreeing to the Amendment RC# 174	407	26	0	7	440	1	https://legiscan.com/US/rollcall/HB1/id/1290284	https://clerk.house.gov/Votes/2023174	2024-09-29 21:50:51.124625	2024-09-29 20:54:53
1284907	1724917	114	2023-03-24	On Agreeing to the Amendment RC# 154	420	5	0	15	440	1	https://legiscan.com/US/rollcall/HB5/id/1284907	https://clerk.house.gov/Votes/2023154	2024-09-29 21:51:23.26382	2024-09-29 20:56:02
1284908	1724917	114	2023-03-24	On Agreeing to the Amendment RC# 155	203	217	0	21	441	0	https://legiscan.com/US/rollcall/HB5/id/1284908	https://clerk.house.gov/Votes/2023155	2024-09-29 21:51:25.116861	2024-09-29 20:56:02
1283748	1724917	114	2023-03-23	On Agreeing to the Amendment RC# 150	203	223	0	14	440	0	https://legiscan.com/US/rollcall/HB5/id/1283748	https://clerk.house.gov/Votes/2023150	2024-09-29 21:51:15.951149	2024-09-29 20:56:02
1283749	1724917	114	2023-03-23	On Agreeing to the Amendment RC# 151	61	365	0	14	440	0	https://legiscan.com/US/rollcall/HB5/id/1283749	https://clerk.house.gov/Votes/2023151	2024-09-29 21:51:17.829891	2024-09-29 20:56:02
1283750	1724917	114	2023-03-23	On Agreeing to the Amendment RC# 152	89	338	0	13	440	0	https://legiscan.com/US/rollcall/HB5/id/1283750	https://clerk.house.gov/Votes/2023152	2024-09-29 21:51:19.669638	2024-09-29 20:56:02
1283751	1724917	114	2023-03-23	On Agreeing to the Amendment RC# 153	386	39	0	15	440	1	https://legiscan.com/US/rollcall/HB5/id/1283751	https://clerk.house.gov/Votes/2023153	2024-09-29 21:51:21.48206	2024-09-29 20:56:02
1284910	1724917	114	2023-03-24	On Agreeing to the Amendment RC# 157	107	317	0	16	440	0	https://legiscan.com/US/rollcall/HB5/id/1284910	https://clerk.house.gov/Votes/2023157	2024-09-29 21:51:28.646776	2024-09-29 20:56:02
1284912	1724917	114	2023-03-24	On Agreeing to the Amendment RC# 159	83	331	0	26	440	0	https://legiscan.com/US/rollcall/HB5/id/1284912	https://clerk.house.gov/Votes/2023159	2024-09-29 21:51:32.592212	2024-09-29 20:56:02
1284913	1724917	114	2023-03-24	On Motion to Recommit RC# 160	203	218	0	13	434	0	https://legiscan.com/US/rollcall/HB5/id/1284913	https://clerk.house.gov/Votes/2023160	2024-09-29 21:51:34.432836	2024-09-29 20:56:02
1284914	1724917	114	2023-03-24	On Passage RC# 161	213	208	0	14	435	1	https://legiscan.com/US/rollcall/HB5/id/1284914	https://clerk.house.gov/Votes/2023161	2024-09-29 21:51:36.159335	2024-09-29 20:56:02
1284909	1724917	114	2023-03-24	On Agreeing to the Amendment RC# 156	161	265	0	15	441	0	https://legiscan.com/US/rollcall/HB5/id/1284909	https://clerk.house.gov/Votes/2023156	2024-09-29 21:51:26.871597	2024-09-29 20:56:02
1284911	1724917	114	2023-03-24	On Agreeing to the Amendment RC# 158	113	311	0	16	440	0	https://legiscan.com/US/rollcall/HB5/id/1284911	https://clerk.house.gov/Votes/2023158	2024-09-29 21:51:30.873667	2024-09-29 20:56:02
\.


--
-- Data for Name: ls_bill_vote_detail; Type: TABLE DATA; Schema: public; Owner: legiscan_api
--

COPY public.ls_bill_vote_detail (roll_call_id, people_id, vote_id) FROM stdin;
1290285	8955	1
1290285	8957	1
1290285	8963	4
1290285	8964	1
1290285	8965	1
1290285	8967	1
1290285	8971	1
1290285	8972	1
1290285	8976	1
1290285	8983	1
1290285	8987	1
1290285	8988	1
1290285	8989	1
1290285	8995	1
1290285	9010	1
1290285	9019	1
1290285	9021	1
1290285	9023	4
1290285	9024	1
1290285	9025	1
1290285	9029	1
1290285	9032	1
1290285	9035	1
1290285	9037	1
1290285	9050	1
1290285	9051	1
1290285	9058	1
1290285	9059	1
1290285	9065	1
1290285	9068	1
1290285	9070	1
1290285	9076	1
1290285	9077	1
1290285	9078	4
1290285	9083	1
1290285	9085	1
1290285	9089	1
1290285	9095	1
1290285	9099	1
1290285	9100	1
1290285	9109	1
1290285	9118	1
1290285	9121	1
1290285	9123	1
1290285	9124	1
1290285	9126	1
1290285	9127	1
1290285	9137	1
1290285	9138	1
1290285	9140	1
1290285	9144	1
1290285	9151	1
1290285	9157	1
1290285	9160	1
1290285	9161	1
1290285	9165	1
1290285	9167	1
1290285	9175	1
1290285	9176	2
1290285	9182	1
1290285	9192	2
1290285	9193	1
1290285	9197	2
1290285	9200	1
1290285	9201	1
1290285	9209	2
1290285	9211	2
1290285	9213	1
1290285	9216	2
1290285	9217	1
1290285	9220	1
1290285	9222	1
1290285	9233	1
1290285	9234	1
1290285	9237	1
1290285	9254	1
1290285	9269	2
1290285	9273	1
1290285	9274	1
1290285	9279	2
1290285	9294	1
1290285	9295	1
1290285	9307	1
1290285	9312	1
1290285	9324	2
1290285	9329	1
1290285	9333	1
1290285	9337	1
1290285	9340	1
1290285	9346	1
1290285	9360	1
1290285	9365	2
1290285	9368	2
1290285	9372	1
1290285	9381	1
1290285	9384	2
1290285	9389	1
1290285	9394	1
1290285	11042	1
1290285	11047	1
1290285	11049	2
1290285	11054	2
1290285	11058	2
1290285	11059	2
1290285	11077	2
1290285	11099	1
1290285	11124	2
1290285	11129	2
1290285	11132	1
1290285	11137	2
1290285	11145	2
1290285	11164	1
1290285	11200	1
1290285	11201	1
1290285	11605	2
1290285	11606	2
1290285	11807	1
1290285	11867	1
1290285	13318	2
1290285	13869	1
1290285	14026	2
1290285	14071	1
1290285	14082	1
1290285	14084	1
1290285	14085	1
1290285	14090	1
1290285	14137	1
1290285	14882	1
1290285	14884	1
1290285	14893	1
1290285	14898	1
1290285	14906	2
1290285	14916	1
1290285	14918	1
1290285	14920	1
1290285	14922	2
1290285	14923	1
1290285	14924	2
1290285	15051	1
1290285	15204	1
1290285	15205	1
1290285	15208	1
1290285	15216	4
1290285	15217	1
1290285	15224	1
1290285	15226	1
1290285	15227	1
1290285	15228	1
1290285	15234	4
1290285	15235	1
1290285	15236	1
1290285	15238	1
1290285	15239	1
1290285	15240	1
1290285	15241	1
1290285	15243	1
1290285	16022	4
1290285	16037	1
1290285	16065	1
1290285	16269	1
1290285	16271	1
1290285	16447	1
1290285	16449	2
1290285	16452	1
1290285	16453	2
1290285	16454	1
1290285	16458	1
1290285	16460	2
1290285	16463	1
1290285	16468	1
1290285	16471	1
1290285	16472	2
1290285	16473	1
1290285	16476	1
1290285	16477	1
1290285	16480	1
1290285	16483	1
1290285	16485	1
1290285	16487	1
1290285	16488	1
1290285	16490	1
1290285	16492	1
1290285	16495	1
1290285	16496	1
1290285	16497	1
1290285	16498	1
1290285	16500	1
1290285	16502	1
1290285	16503	1
1290285	16824	1
1290285	17510	1
1290285	17704	2
1290285	17717	2
1290285	17958	2
1290285	17980	2
1290285	17981	1
1290285	18286	2
1290285	18287	1
1290285	18288	2
1290285	18289	1
1290285	18290	1
1290285	18291	2
1290285	18292	1
1290285	18295	1
1290285	18297	1
1290285	18300	1
1290285	18301	1
1290285	18303	2
1290285	18304	1
1290285	18305	2
1290285	18306	1
1290285	18308	1
1290285	18309	1
1290285	18310	1
1290285	18312	1
1290285	18313	2
1290285	18314	1
1290285	18316	1
1290285	18317	2
1290285	18321	1
1290285	18326	1
1290285	18327	1
1290285	18330	1
1290285	18331	2
1290285	18332	1
1290285	18335	1
1290285	18411	2
1290285	19370	2
1290285	19407	2
1290285	19409	1
1290285	19436	1
1290285	19646	2
1290285	19664	2
1290285	19676	2
1290285	19692	1
1290285	19693	1
1290285	19694	1
1290285	19700	1
1290285	20039	1
1290285	20040	1
1290285	20042	1
1290285	20044	2
1290285	20045	1
1290285	20046	1
1290285	20047	2
1290285	20048	1
1290285	20049	2
1290285	20050	1
1290285	20054	1
1290285	20056	1
1290285	20057	1
1290285	20059	1
1290285	20060	2
1290285	20061	1
1290285	20062	1
1290285	20064	2
1290285	20065	2
1290285	20066	1
1290285	20067	1
1290285	20069	1
1290285	20071	1
1290285	20074	1
1290285	20075	1
1290285	20076	2
1290285	20077	1
1290285	20078	1
1290285	20081	1
1290285	20083	2
1290285	20084	2
1290285	20086	1
1290285	20088	1
1290285	20089	1
1290285	20090	1
1290285	20091	1
1290285	20092	1
1290285	20093	1
1290285	20094	1
1290285	20095	1
1290285	20096	2
1290285	20098	2
1290285	20100	2
1290285	20103	1
1290285	20104	1
1290285	20105	1
1290285	20107	1
1290285	20108	1
1290285	20109	1
1290285	20110	2
1290285	20111	1
1290285	20112	1
1290285	20114	2
1290285	20115	1
1290285	20116	1
1290285	20117	1
1290285	20119	1
1290285	20120	1
1290285	20121	2
1290285	20123	1
1290285	21385	2
1290285	21386	1
1290285	21642	1
1290285	21646	1
1290285	21647	2
1290285	21921	2
1290285	21922	2
1290285	21923	1
1290285	21924	1
1290285	21925	1
1290285	21926	1
1290285	21927	2
1290285	21928	2
1290285	21929	2
1290285	21930	2
1290285	21931	1
1290285	21932	1
1290285	21934	2
1290285	21935	2
1290285	21936	1
1290285	21938	1
1290285	21939	1
1290285	21940	1
1290285	21941	2
1290285	21943	1
1290285	21944	2
1290285	21945	1
1290285	21946	1
1290285	21947	1
1290285	21948	2
1290285	21950	1
1290285	21951	1
1290285	21952	2
1290285	21954	1
1290285	21955	1
1290285	21957	1
1290285	21958	1
1290285	21959	1
1290285	21961	1
1290285	21962	1
1290285	21963	2
1290285	21964	1
1290285	21965	1
1290285	21966	2
1290285	21967	2
1290285	21968	1
1290285	21969	2
1290285	21970	2
1290285	21971	2
1290285	21972	2
1290285	21973	1
1290285	21974	1
1290285	21975	2
1290285	21976	1
1290285	21977	2
1290285	22915	1
1290285	22929	1
1290285	22939	4
1290285	22947	1
1290285	22966	1
1290285	22967	2
1290285	23048	1
1290285	23161	1
1290285	23162	1
1290285	23172	1
1290285	23173	1
1290285	23182	1
1290285	23997	1
1290285	23998	2
1290285	23999	1
1290285	24000	2
1290285	24001	2
1290285	24002	1
1290285	24003	2
1290285	24004	1
1290285	24005	1
1290285	24006	2
1290285	24007	1
1290285	24008	1
1290285	24009	1
1290285	24010	1
1290285	24011	1
1290285	24012	2
1290285	24013	1
1290285	24014	2
1290285	24015	1
1290285	24016	1
1290285	24017	1
1290285	24018	1
1290285	24019	2
1290285	24020	1
1290285	24021	1
1290285	24022	1
1290285	24023	2
1290285	24024	4
1290285	24025	2
1290285	24026	2
1290285	24027	1
1290285	24028	1
1290285	24029	1
1290285	24030	1
1290285	24031	1
1290285	24032	1
1290285	24033	1
1290285	24034	1
1290285	24035	2
1290285	24036	1
1290285	24037	1
1290285	24038	1
1290285	24039	1
1290285	24040	1
1290285	24041	1
1290285	24042	2
1290285	24043	1
1290285	24044	1
1290285	24045	2
1290285	24046	1
1290285	24047	1
1290285	24048	1
1290285	24049	1
1290285	24050	2
1290285	24051	1
1290285	24052	1
1290285	24053	1
1290285	24054	1
1290285	24055	2
1290285	24056	1
1290285	24057	1
1290285	24058	2
1290285	24059	1
1290285	24060	2
1290285	24061	1
1290285	24062	2
1290285	24063	1
1290285	24064	1
1290285	24065	1
1290285	24066	1
1290285	24067	2
1290285	24068	1
1290285	24069	1
1290285	24071	1
1290285	24913	1
1290286	8955	1
1290286	8957	1
1290286	8963	4
1290286	8964	1
1290286	8965	2
1290286	8967	1
1290286	8971	1
1290286	8972	1
1290286	8976	1
1290286	8983	1
1290286	8987	1
1290286	8988	1
1290286	8989	1
1290286	8995	1
1290286	9010	1
1290286	9019	1
1290286	9021	1
1290286	9023	4
1290286	9024	1
1290286	9025	1
1290286	9029	1
1290286	9032	1
1290286	9035	1
1290286	9037	1
1290286	9050	1
1290286	9051	1
1290286	9058	1
1290286	9059	1
1290286	9065	1
1290286	9068	1
1290286	9070	1
1290286	9076	1
1290286	9077	1
1290286	9078	4
1290286	9083	1
1290286	9085	1
1290286	9089	1
1290286	9095	1
1290286	9099	1
1290286	9100	1
1290286	9109	1
1290286	9118	1
1290286	9121	1
1290286	9123	1
1290286	9124	1
1290286	9126	1
1290286	9127	1
1290286	9137	1
1290286	9138	1
1290286	9140	1
1290286	9144	1
1290286	9151	1
1290286	9157	2
1290286	9160	1
1290286	9161	1
1290286	9165	1
1290286	9167	1
1290286	9175	2
1290286	9176	2
1290286	9182	2
1290286	9192	2
1290286	9193	2
1290286	9197	2
1290286	9200	2
1290286	9201	1
1290286	9209	2
1290286	9211	2
1290286	9213	2
1290286	9216	2
1290286	9217	2
1290286	9220	2
1290286	9222	2
1290286	9233	4
1290286	9234	1
1290286	9237	2
1290286	9254	2
1290286	9269	2
1290286	9273	2
1290286	9274	2
1290286	9279	2
1290286	9294	2
1290286	9295	2
1290286	9307	1
1290286	9312	1
1290286	9324	2
1290286	9329	2
1290286	9333	2
1290286	9337	2
1290286	9340	1
1290286	9346	2
1290286	9360	1
1290286	9365	2
1290286	9368	2
1290286	9372	2
1290286	9381	2
1290286	9384	2
1290286	9389	2
1290286	9394	1
1290286	11042	2
1290286	11047	2
1290286	11049	2
1290286	11054	2
1290286	11058	2
1290286	11059	2
1290286	11077	2
1290286	11099	2
1290286	11124	2
1290286	11129	2
1290286	11132	2
1290286	11137	2
1290286	11145	2
1290286	11164	2
1290286	11200	1
1290286	11201	1
1290286	11605	2
1290286	11606	2
1290286	11807	1
1290286	11867	1
1290286	13318	2
1290286	13869	1
1290286	14026	2
1290286	14071	1
1290286	14082	1
1290286	14084	2
1290286	14085	1
1290286	14090	1
1290286	14137	1
1290286	14882	1
1290286	14884	1
1290286	14893	1
1290286	14898	1
1290286	14906	2
1290286	14916	1
1290286	14918	2
1290286	14920	1
1290286	14922	2
1290286	14923	2
1290286	14924	2
1290286	15051	2
1290286	15204	1
1290286	15205	1
1290286	15208	1
1290286	15216	4
1290286	15217	1
1290286	15224	2
1290286	15226	1
1290286	15227	1
1290286	15228	2
1290286	15234	1
1290286	15235	1
1290286	15236	1
1290286	15238	1
1290286	15239	1
1290286	15240	2
1290286	15241	1
1290286	15243	2
1290286	16022	4
1290286	16037	2
1290286	16065	1
1290286	16269	1
1290286	16271	1
1290286	16447	2
1290286	16449	2
1290286	16452	2
1290286	16453	2
1290286	16454	2
1290286	16458	2
1290286	16460	2
1290286	16463	2
1290286	16468	2
1290286	16471	2
1290286	16472	2
1290286	16473	2
1290286	16476	2
1290286	16477	2
1290286	16480	2
1290286	16483	2
1290286	16485	1
1290286	16487	1
1290286	16488	1
1290286	16490	2
1290286	16492	1
1290286	16495	1
1290286	16496	1
1290286	16497	1
1290286	16498	1
1290286	16500	1
1290286	16502	1
1290286	16503	2
1290286	16824	1
1290286	17510	2
1290286	17704	2
1290286	17717	2
1290286	17958	2
1290286	17980	2
1290286	17981	1
1290286	18286	2
1290286	18287	2
1290286	18288	2
1290286	18289	1
1290286	18290	2
1290286	18291	2
1290286	18292	1
1290286	18295	1
1290286	18297	1
1290286	18300	2
1290286	18301	1
1290286	18303	2
1290286	18304	2
1290286	18305	2
1290286	18306	2
1290286	18308	2
1290286	18309	1
1290286	18310	2
1290286	18312	1
1290286	18313	2
1290286	18314	1
1290286	18316	1
1290286	18317	2
1290286	18321	2
1290286	18326	1
1290286	18327	1
1290286	18330	2
1290286	18331	2
1290286	18332	1
1290286	18335	2
1290286	18411	2
1290286	19370	2
1290286	19407	2
1290286	19409	1
1290286	19436	2
1290286	19646	2
1290286	19664	2
1290286	19676	2
1290286	19692	2
1290286	19693	1
1290286	19694	1
1290286	19700	1
1290286	20039	1
1290286	20040	2
1290286	20042	2
1290286	20044	2
1290286	20045	1
1290286	20046	1
1290286	20047	2
1290286	20048	1
1290286	20049	2
1290286	20050	1
1290286	20054	1
1290286	20056	1
1290286	20057	1
1290286	20059	1
1290286	20060	2
1290286	20061	1
1290286	20062	1
1290286	20064	2
1290286	20065	2
1290286	20066	2
1290286	20067	1
1290286	20069	1
1290286	20071	1
1290286	20074	1
1290286	20075	2
1290286	20076	2
1290286	20077	1
1290286	20078	1
1290286	20081	1
1290286	20083	2
1290286	20084	2
1290286	20086	1
1290286	20088	1
1290286	20089	1
1290286	20090	1
1290286	20091	1
1290286	20092	2
1290286	20093	1
1290286	20094	1
1290286	20095	1
1290286	20096	2
1290286	20098	2
1290286	20100	2
1290286	20103	1
1290286	20104	1
1290286	20105	1
1290286	20107	1
1290286	20108	2
1290286	20109	2
1290286	20110	2
1290286	20111	1
1290286	20112	1
1290286	20114	2
1290286	20115	1
1290286	20116	1
1290286	20117	1
1290286	20119	1
1290286	20120	2
1290286	20121	2
1290286	20123	1
1290286	21385	2
1290286	21386	2
1290286	21642	1
1290286	21646	2
1290286	21647	2
1290286	21921	2
1290286	21922	2
1290286	21923	1
1290286	21924	2
1290286	21925	2
1290286	21926	2
1290286	21927	2
1290286	21928	2
1290286	21929	2
1290286	21930	2
1290286	21931	2
1290286	21932	2
1290286	21934	2
1290286	21935	2
1290286	21936	1
1290286	21938	2
1290286	21939	2
1290286	21940	2
1290286	21941	2
1290286	21943	1
1290286	21944	2
1290286	21945	2
1290286	21946	2
1290286	21947	1
1290286	21948	2
1290286	21950	2
1290286	21951	1
1290286	21952	2
1290286	21954	1
1290286	21955	1
1290286	21957	1
1290286	21958	1
1290286	21959	2
1290286	21961	2
1290286	21962	1
1290286	21963	2
1290286	21964	2
1290286	21965	2
1290286	21966	2
1290286	21967	2
1290286	21968	2
1290286	21969	2
1290286	21970	2
1290286	21971	2
1290286	21972	2
1290286	21973	2
1290286	21974	2
1290286	21975	2
1290286	21976	1
1290286	21977	2
1290286	22915	2
1290286	22929	1
1290286	22939	1
1290286	22947	2
1290286	22966	1
1290286	22967	2
1290286	23048	1
1290286	23161	2
1290286	23162	2
1290286	23172	1
1290286	23173	1
1290286	23182	2
1290286	23997	2
1290286	23998	2
1290286	23999	1
1290286	24000	2
1290286	24001	2
1290286	24002	1
1290286	24003	2
1290286	24004	1
1290286	24005	1
1290286	24006	2
1290286	24007	2
1290286	24008	1
1290286	24009	2
1290286	24010	2
1290286	24011	2
1290286	24012	2
1290286	24013	2
1290286	24014	2
1290286	24015	2
1290286	24016	2
1290286	24017	1
1290286	24018	1
1290286	24019	2
1290286	24020	1
1290286	24021	1
1290286	24022	1
1290286	24023	2
1290286	24024	4
1290286	24025	2
1290286	24026	2
1290286	24027	1
1290286	24028	2
1290286	24029	1
1290286	24030	1
1290286	24031	2
1290286	24032	2
1290286	24033	1
1290286	24034	2
1290286	24035	2
1290286	24036	2
1290286	24037	2
1290286	24038	2
1290286	24039	2
1290286	24040	1
1290286	24041	1
1290286	24042	2
1290286	24043	2
1290286	24044	1
1290286	24045	2
1290286	24046	1
1290286	24047	2
1290286	24048	2
1290286	24049	1
1290286	24050	2
1290286	24051	1
1290286	24052	1
1290286	24053	2
1290286	24054	1
1290286	24055	2
1290286	24056	1
1290286	24057	1
1290286	24058	2
1290286	24059	1
1290286	24060	2
1290286	24061	1
1290286	24062	2
1290286	24063	1
1290286	24064	1
1290286	24065	1
1290286	24066	1
1290286	24067	2
1290286	24068	1
1290286	24069	2
1290286	24071	2
1290286	24913	1
1290287	8955	1
1290287	8957	1
1290287	8963	4
1290287	8964	1
1290287	8965	1
1290287	8967	1
1290287	8971	1
1290287	8972	1
1290287	8976	2
1290287	8983	1
1290287	8987	1
1290287	8988	1
1290287	8989	2
1290287	8995	1
1290287	9010	4
1290287	9019	1
1290287	9021	2
1290287	9023	4
1290287	9024	1
1290287	9025	1
1290287	9029	1
1290287	9032	1
1290287	9035	1
1290287	9037	1
1290287	9050	1
1290287	9051	1
1290287	9058	1
1290287	9059	1
1290287	9065	1
1290287	9068	1
1290287	9070	1
1290287	9076	1
1290287	9077	1
1290287	9078	4
1290287	9083	1
1290287	9085	1
1290287	9089	1
1290287	9095	1
1290287	9099	1
1290287	9100	1
1290287	9109	1
1290287	9118	1
1290287	9121	1
1290287	9123	1
1290287	9124	1
1290287	9126	1
1290287	9127	1
1290287	9137	1
1290287	9138	1
1290287	9140	1
1290287	9144	1
1290287	9151	1
1290287	9157	1
1290287	9160	1
1290287	9161	1
1290287	9165	1
1290287	9167	1
1290287	9175	1
1290287	9176	1
1290287	9182	1
1290287	9192	1
1290287	9193	1
1290287	9197	1
1290287	9200	1
1290287	9201	1
1290287	9209	1
1290287	9211	1
1290287	9213	1
1290287	9216	1
1290287	9217	1
1290287	9220	1
1290287	9222	1
1290287	9233	1
1290287	9234	1
1290287	9237	1
1290287	9254	1
1290287	9269	1
1290287	9273	1
1290287	9274	1
1290287	9279	1
1290287	9294	1
1290287	9295	1
1290287	9307	1
1290287	9312	1
1290287	9324	1
1290287	9329	1
1290287	9333	1
1290287	9337	1
1290287	9340	1
1290287	9346	1
1290287	9360	1
1290287	9365	1
1290287	9368	1
1290287	9372	1
1290287	9381	1
1290287	9384	1
1290287	9389	1
1290287	9394	1
1290287	11042	1
1290287	11047	1
1290287	11049	1
1290287	11054	1
1290287	11058	1
1290287	11059	1
1290287	11077	1
1290287	11099	1
1290287	11124	1
1290287	11129	1
1290287	11132	1
1290287	11137	1
1290287	11145	1
1290287	11164	1
1290287	11200	1
1290287	11201	1
1290287	11605	1
1290287	11606	1
1290287	11807	1
1290287	11867	1
1290287	13318	1
1290287	13869	2
1290287	14026	1
1290287	14071	1
1290287	14082	4
1290287	14084	1
1290287	14085	2
1290287	14090	1
1290287	14137	1
1290287	14882	1
1290287	14884	1
1290287	14893	1
1290287	14898	2
1290287	14906	1
1290287	14916	1
1290287	14918	1
1290287	14920	1
1290287	14922	1
1290287	14923	1
1290287	14924	1
1290287	15051	1
1290287	15204	1
1290287	15205	1
1290287	15208	1
1290287	15216	4
1290287	15217	1
1290287	15224	1
1290287	15226	1
1290287	15227	1
1290287	15228	1
1290287	15234	1
1290287	15235	1
1290287	15236	1
1290287	15238	1
1290287	15239	2
1290287	15240	1
1290287	15241	1
1290287	15243	1
1290287	16022	4
1290287	16037	1
1290287	16065	1
1290287	16269	1
1290287	16271	1
1290287	16447	1
1290287	16449	1
1290287	16452	1
1290287	16453	1
1290287	16454	1
1290287	16458	1
1290287	16460	1
1290287	16463	1
1290287	16468	1
1290287	16471	1
1290287	16472	1
1290287	16473	1
1290287	16476	1
1290287	16477	1
1290287	16480	1
1290287	16483	1
1290287	16485	1
1290287	16487	1
1290287	16488	1
1290287	16490	1
1290287	16492	1
1290287	16495	1
1290287	16496	1
1290287	16497	1
1290287	16498	1
1290287	16500	4
1290287	16502	1
1290287	16503	1
1290287	16824	1
1290287	17510	1
1290287	17704	1
1290287	17717	1
1290287	17958	1
1290287	17980	1
1290287	17981	1
1290287	18286	1
1290287	18287	1
1290287	18288	1
1290287	18289	1
1290287	18290	1
1290287	18291	1
1290287	18292	1
1290287	18295	1
1290287	18297	2
1290287	18300	1
1290287	18301	1
1290287	18303	1
1290287	18304	1
1290287	18305	1
1290287	18306	1
1290287	18308	1
1290287	18309	1
1290287	18310	1
1290287	18312	2
1290287	18313	1
1290287	18314	1
1290287	18316	1
1290287	18317	1
1290287	18321	1
1290287	18326	1
1290287	18327	1
1290287	18330	1
1290287	18331	1
1290287	18332	1
1290287	18335	1
1290287	18411	1
1290287	19370	1
1290287	19407	1
1290287	19409	4
1290287	19436	1
1290287	19646	1
1290287	19664	1
1290287	19676	1
1290287	19692	1
1290287	19693	1
1290287	19694	1
1290287	19700	1
1290287	20039	1
1290287	20040	1
1290287	20042	1
1290287	20044	1
1290287	20045	1
1290287	20046	1
1290287	20047	1
1290287	20048	1
1290287	20049	1
1290287	20050	1
1290287	20054	1
1290287	20056	1
1290287	20057	1
1290287	20059	2
1290287	20060	1
1290287	20061	1
1290287	20062	1
1290287	20064	1
1290287	20065	1
1290287	20066	1
1290287	20067	1
1290287	20069	1
1290287	20071	1
1290287	20074	1
1290287	20075	1
1290287	20076	1
1290287	20077	2
1290287	20078	1
1290287	20081	1
1290287	20083	1
1290287	20084	1
1290287	20086	1
1290287	20088	1
1290287	20089	2
1290287	20090	2
1290287	20091	1
1290287	20092	1
1290287	20093	1
1290287	20094	1
1290287	20095	1
1290287	20096	1
1290287	20098	1
1290287	20100	1
1290287	20103	1
1290287	20104	1
1290287	20105	1
1290287	20107	1
1290287	20108	1
1290287	20109	1
1290287	20110	1
1290287	20111	1
1290287	20112	1
1290287	20114	1
1290287	20115	2
1290287	20116	1
1290287	20117	1
1290287	20119	1
1290287	20120	1
1290287	20121	4
1290287	20123	1
1290287	21385	1
1290287	21386	1
1290287	21642	1
1290287	21646	1
1290287	21647	1
1290287	21921	1
1290287	21922	1
1290287	21923	2
1290287	21924	1
1290287	21925	1
1290287	21926	1
1290287	21927	1
1290287	21928	1
1290287	21929	1
1290287	21930	1
1290287	21931	1
1290287	21932	1
1290287	21934	1
1290287	21935	1
1290287	21936	1
1290287	21938	1
1290287	21939	1
1290287	21940	1
1290287	21941	1
1290287	21943	1
1290287	21944	1
1290287	21945	1
1290287	21946	1
1290287	21947	1
1290287	21948	1
1290287	21950	1
1290287	21951	2
1290287	21952	1
1290287	21954	1
1290287	21955	1
1290287	21957	1
1290287	21958	2
1290287	21959	1
1290287	21961	1
1290287	21962	1
1290287	21963	1
1290287	21964	1
1290287	21965	1
1290287	21966	1
1290287	21967	1
1290287	21968	1
1290287	21969	1
1290287	21970	1
1290287	21971	1
1290287	21972	1
1290287	21973	1
1290287	21974	1
1290287	21975	1
1290287	21976	1
1290287	21977	1
1290287	22915	1
1290287	22929	1
1290287	22939	1
1290287	22947	1
1290287	22966	1
1290287	22967	1
1290287	23048	1
1290287	23161	1
1290287	23162	1
1290287	23172	1
1290287	23173	1
1290287	23182	1
1290287	23997	1
1290287	23998	1
1290287	23999	1
1290287	24000	1
1290287	24001	1
1290287	24002	1
1290287	24003	1
1290287	24004	1
1290287	24005	2
1290287	24006	1
1290287	24007	1
1290287	24008	1
1290287	24009	1
1290287	24010	1
1290287	24011	1
1290287	24012	1
1290287	24013	1
1290287	24014	1
1290287	24015	1
1290287	24016	1
1290287	24017	2
1290287	24018	1
1290287	24019	1
1290287	24020	2
1290287	24021	1
1290287	24022	1
1290287	24023	1
1290287	24024	4
1290287	24025	1
1290287	24026	1
1290287	24027	1
1290287	24028	1
1290287	24029	1
1290287	24030	1
1290287	24031	1
1290287	24032	1
1290287	24033	2
1290287	24034	1
1290287	24035	1
1290287	24036	1
1290287	24037	1
1290287	24038	1
1290287	24039	1
1290287	24040	1
1290287	24041	2
1290287	24042	1
1290287	24043	1
1290287	24044	1
1290287	24045	1
1290287	24046	1
1290287	24047	1
1290287	24048	1
1290287	24049	1
1290287	24050	1
1290287	24051	1
1290287	24052	1
1290287	24053	1
1290287	24054	1
1290287	24055	1
1290287	24056	1
1290287	24057	2
1290287	24058	1
1290287	24059	1
1290287	24060	1
1290287	24061	1
1290287	24062	1
1290287	24063	1
1290287	24064	1
1290287	24065	2
1290287	24066	1
1290287	24067	1
1290287	24068	1
1290287	24069	1
1290287	24071	1
1290287	24913	1
1284907	8955	1
1284913	8955	1
1284909	8955	2
1284912	8955	2
1283750	8955	2
1284908	8955	1
1284910	8955	2
1283751	8955	1
1283749	8955	2
1283748	8955	1
1284911	8955	2
1284914	8955	2
1284912	8957	2
1284914	8957	2
1284908	8957	1
1284910	8957	2
1284911	8957	2
1284909	8957	2
1283751	8957	1
1283748	8957	1
1284907	8957	1
1284913	8957	1
1283750	8957	2
1283749	8957	2
1284912	8963	2
1283750	8963	2
1284908	8963	1
1284907	8963	1
1284914	8963	2
1284909	8963	2
1284913	8963	1
1284910	8963	2
1283749	8963	2
1283748	8963	1
1284911	8963	2
1283751	8963	1
1284914	8964	2
1284913	8964	1
1284908	8964	1
1284907	8964	1
1284910	8964	2
1283748	8964	1
1283749	8964	2
1284912	8964	2
1283751	8964	1
1284909	8964	2
1283750	8964	2
1284911	8964	2
1284913	8965	4
1284914	8965	4
1283749	8965	4
1284908	8965	4
1283750	8965	4
1284907	8965	4
1284912	8965	4
1284909	8965	4
1283751	8965	4
1284911	8965	4
1284910	8965	4
1283748	8965	4
1284909	8967	2
1283751	8967	1
1284912	8967	2
1284913	8967	1
1284907	8967	1
1284914	8967	2
1283750	8967	2
1283749	8967	2
1284908	8967	1
1283748	8967	1
1284911	8967	2
1284910	8967	2
1284907	8971	1
1284909	8971	2
1284910	8971	2
1284913	8971	1
1284912	8971	2
1284908	8971	1
1283748	8971	1
1283750	8971	2
1284911	8971	2
1284914	8971	2
1283751	8971	1
1283749	8971	2
1284912	8972	2
1284910	8972	2
1284908	8972	1
1284914	8972	2
1284911	8972	2
1283749	8972	2
1283751	8972	1
1283750	8972	2
1284909	8972	2
1284913	8972	1
1283748	8972	1
1284907	8972	1
1283751	8976	2
1283749	8976	2
1284911	8976	2
1284909	8976	2
1284907	8976	2
1284910	8976	2
1283750	8976	2
1284912	8976	2
1284913	8976	1
1284914	8976	2
1284908	8976	1
1283748	8976	1
1283749	8983	2
1283748	8983	1
1284912	8983	2
1284908	8983	1
1283751	8983	1
1284913	8983	1
1284910	8983	2
1284907	8983	1
1284909	8983	2
1283750	8983	2
1284914	8983	2
1284911	8983	2
1284908	8987	1
1283748	8987	1
1283749	8987	2
1284914	8987	2
1284913	8987	1
1284909	8987	2
1283750	8987	2
1284912	8987	2
1284911	8987	2
1284907	8987	1
1283751	8987	1
1284910	8987	2
1284908	8988	1
1283748	8988	1
1284907	8988	1
1284912	8988	2
1284910	8988	4
1284913	8988	1
1284909	8988	2
1284911	8988	2
1283751	8988	1
1283750	8988	2
1283749	8988	2
1284914	8988	2
1283750	8989	2
1283751	8989	1
1283748	8989	1
1284914	8989	2
1284908	8989	1
1284912	8989	2
1284909	8989	2
1284913	8989	1
1283749	8989	2
1284911	8989	2
1284910	8989	2
1284907	8989	1
1284909	8995	2
1284908	8995	1
1283751	8995	1
1283749	8995	2
1283748	8995	1
1284910	8995	2
1284912	8995	2
1284911	8995	2
1284913	8995	1
1284914	8995	2
1284907	8995	1
1283750	8995	2
1284914	9010	4
1284912	9010	4
1284911	9010	4
1284909	9010	4
1284913	9010	4
1284910	9010	4
1284908	9010	4
1283751	9010	4
1283748	9010	4
1283750	9010	4
1283749	9010	4
1284907	9010	4
1284911	9019	2
1284907	9019	1
1284909	9019	2
1284910	9019	2
1283750	9019	2
1284908	9019	1
1284913	9019	1
1283748	9019	1
1283751	9019	1
1283749	9019	2
1284912	9019	2
1284914	9019	2
1284907	9021	1
1283751	9021	1
1283748	9021	1
1284911	9021	2
1284910	9021	2
1283750	9021	2
1284914	9021	2
1283749	9021	2
1284913	9021	1
1284909	9021	2
1284912	9021	2
1284908	9021	1
1284908	9023	4
1283751	9023	4
1284909	9023	4
1283748	9023	4
1284907	9023	4
1284913	9023	4
1284912	9023	4
1284910	9023	4
1284911	9023	4
1283749	9023	4
1283750	9023	4
1284914	9023	4
1284914	9024	2
1284908	9024	1
1284911	9024	2
1283748	9024	1
1283749	9024	2
1284909	9024	2
1283751	9024	1
1284907	9024	1
1284912	9024	2
1284913	9024	1
1284910	9024	2
1283750	9024	2
1283749	9025	4
1284909	9025	2
1284910	9025	2
1283751	9025	4
1284913	9025	1
1284912	9025	4
1284907	9025	1
1284914	9025	2
1283750	9025	4
1284911	9025	2
1283748	9025	4
1284908	9025	1
1284914	9029	2
1284909	9029	2
1284907	9029	1
1283749	9029	2
1284912	9029	2
1283750	9029	2
1284911	9029	2
1283748	9029	1
1283751	9029	1
1284908	9029	1
1284910	9029	2
1284913	9029	1
1284907	9032	1
1284912	9032	2
1283748	9032	1
1284909	9032	2
1284910	9032	2
1284911	9032	2
1283751	9032	1
1283749	9032	2
1284908	9032	1
1284914	9032	2
1284913	9032	1
1283750	9032	2
1284910	9035	2
1284914	9035	2
1284912	9035	2
1284908	9035	1
1283750	9035	2
1284907	9035	1
1284909	9035	2
1283748	9035	1
1284913	9035	1
1283749	9035	2
1284911	9035	2
1283751	9035	1
1284913	9037	1
1283751	9037	1
1284910	9037	2
1284911	9037	2
1283748	9037	1
1284914	9037	2
1284912	9037	2
1283750	9037	2
1283749	9037	2
1284907	9037	1
1284908	9037	1
1284909	9037	2
1284907	9050	1
1284911	9050	2
1284914	9050	2
1283749	9050	2
1283750	9050	2
1284910	9050	2
1284909	9050	2
1283751	9050	1
1284913	9050	1
1284908	9050	1
1284912	9050	2
1283748	9050	1
1284910	9051	2
1283750	9051	2
1284909	9051	2
1283749	9051	2
1284912	9051	2
1284914	9051	2
1284907	9051	1
1283748	9051	1
1284911	9051	2
1284908	9051	4
1284913	9051	1
1283751	9051	1
1284911	9058	2
1283748	9058	1
1284912	9058	2
1284909	9058	2
1283751	9058	1
1284908	9058	1
1283750	9058	2
1284914	9058	2
1283749	9058	2
1284910	9058	2
1284913	9058	1
1284907	9058	1
1284907	9059	1
1283748	9059	1
1284909	9059	2
1284913	9059	1
1284914	9059	2
1283750	9059	2
1284908	9059	1
1283751	9059	1
1284910	9059	2
1284911	9059	2
1284912	9059	2
1283749	9059	2
1283750	9065	2
1283751	9065	1
1283749	9065	2
1284907	9065	1
1283748	9065	1
1284914	9065	2
1284913	9065	1
1284912	9065	2
1284908	9065	1
1284910	9065	2
1284911	9065	2
1284909	9065	2
1283748	9068	1
1284907	9068	1
1283751	9068	1
1284910	9068	2
1283749	9068	2
1284912	9068	2
1284909	9068	2
1284911	9068	2
1284914	9068	2
1283750	9068	2
1284908	9068	1
1284913	9068	1
1284914	9070	2
1283749	9070	2
1284911	9070	2
1283748	9070	1
1283751	9070	1
1284910	9070	2
1283750	9070	2
1284909	9070	2
1284913	9070	1
1284908	9070	1
1284912	9070	2
1284907	9070	1
1284914	9076	2
1284908	9076	1
1284907	9076	1
1283748	9076	1
1284913	9076	1
1284910	9076	2
1284912	9076	2
1283750	9076	2
1284909	9076	2
1283751	9076	1
1283749	9076	2
1284911	9076	2
1283751	9077	1
1284909	9077	2
1284911	9077	2
1284914	9077	2
1284912	9077	2
1283750	9077	2
1284908	9077	1
1284910	9077	2
1284913	9077	1
1283748	9077	1
1284907	9077	1
1283749	9077	2
1284908	9078	1
1283750	9078	2
1284914	9078	2
1284911	9078	2
1283749	9078	2
1283751	9078	1
1284909	9078	2
1284912	9078	2
1284910	9078	2
1284913	9078	1
1283748	9078	1
1284907	9078	1
1284912	9083	2
1284909	9083	2
1283749	9083	2
1283748	9083	1
1283751	9083	1
1284913	9083	1
1284911	9083	2
1283750	9083	2
1284914	9083	2
1284910	9083	2
1284907	9083	1
1284908	9083	1
1283751	9085	2
1284910	9085	2
1284909	9085	2
1283749	9085	2
1283750	9085	2
1284908	9085	1
1284914	9085	2
1283748	9085	1
1284913	9085	1
1284912	9085	2
1284907	9085	1
1284911	9085	2
1284912	9089	2
1284911	9089	2
1284908	9089	1
1283750	9089	2
1284913	9089	1
1283751	9089	1
1284910	9089	2
1283749	9089	2
1284914	9089	2
1284909	9089	2
1284907	9089	1
1283748	9089	1
1283749	9095	2
1284912	9095	2
1284913	9095	1
1284914	9095	2
1284911	9095	2
1283750	9095	2
1284908	9095	1
1284907	9095	1
1284909	9095	2
1283748	9095	1
1283751	9095	1
1284910	9095	2
1284912	9099	2
1283749	9099	4
1284910	9099	2
1283751	9099	4
1284911	9099	2
1284908	9099	1
1284914	9099	2
1284913	9099	1
1284907	9099	1
1284909	9099	2
1283748	9099	4
1283750	9099	4
1283748	9100	1
1284907	9100	1
1284908	9100	1
1283750	9100	2
1284912	9100	2
1283751	9100	1
1283749	9100	2
1284911	9100	2
1284909	9100	2
1284910	9100	2
1284911	9109	2
1284912	9109	2
1284907	9109	1
1284908	9109	1
1284914	9109	2
1283751	9109	1
1283748	9109	1
1283749	9109	2
1284913	9109	1
1284910	9109	2
1284909	9109	2
1283750	9109	2
1283748	9118	1
1284908	9118	4
1283749	9118	2
1284909	9118	4
1284911	9118	2
1284913	9118	1
1283750	9118	2
1284914	9118	2
1284907	9118	1
1284912	9118	2
1284910	9118	2
1283751	9118	1
1284910	9121	2
1283751	9121	1
1283749	9121	2
1283750	9121	2
1284908	9121	1
1284914	9121	2
1284912	9121	2
1284909	9121	2
1283748	9121	1
1284907	9121	1
1284913	9121	1
1284911	9121	2
1283750	9123	2
1283749	9123	2
1284907	9123	1
1284913	9123	1
1284910	9123	2
1284912	9123	2
1283748	9123	1
1283751	9123	1
1284909	9123	2
1284908	9123	1
1284911	9123	2
1284914	9123	2
1284908	9124	1
1284914	9124	2
1284910	9124	2
1283750	9124	2
1284911	9124	2
1283748	9124	1
1284907	9124	1
1284912	9124	2
1283749	9124	2
1284913	9124	1
1284909	9124	2
1283751	9124	1
1283749	9126	2
1283748	9126	1
1284909	9126	2
1284913	9126	1
1284907	9126	1
1284910	9126	2
1283751	9126	1
1283750	9126	2
1284912	9126	2
1284914	9126	2
1284908	9126	1
1284911	9126	2
1284907	9127	1
1284914	9127	2
1284911	9127	2
1283751	9127	1
1283749	9127	2
1284909	9127	2
1284908	9127	1
1284912	9127	2
1284910	9127	2
1283750	9127	2
1284913	9127	1
1283748	9127	1
1284909	9137	2
1283748	9137	1
1284910	9137	2
1284911	9137	2
1283749	9137	2
1284912	9137	2
1284914	9137	2
1283750	9137	2
1284908	9137	1
1284913	9137	1
1284907	9137	1
1283751	9137	1
1284911	9138	2
1284914	9138	2
1284908	9138	1
1284909	9138	2
1283750	9138	2
1284912	9138	2
1284910	9138	1
1284907	9138	1
1283751	9138	1
1283748	9138	1
1284913	9138	1
1283749	9138	2
1284909	9140	2
1283749	9140	2
1283750	9140	2
1283748	9140	1
1283751	9140	1
1284907	9140	1
1284913	9140	1
1284911	9140	2
1284908	9140	1
1284914	9140	2
1284910	9140	2
1284912	9140	2
1283749	9144	2
1284910	9144	2
1284908	9144	1
1284914	9144	2
1284913	9144	1
1283750	9144	2
1284912	9144	2
1284909	9144	2
1283748	9144	1
1284911	9144	2
1284907	9144	1
1283751	9144	1
1284912	9151	2
1284909	9151	2
1284908	9151	1
1284907	9151	1
1284910	9151	2
1283749	9151	2
1284913	9151	1
1283748	9151	1
1284914	9151	2
1283751	9151	1
1283750	9151	2
1284911	9151	2
1284914	9157	1
1283750	9157	2
1284910	9157	1
1283748	9157	2
1283749	9157	2
1284913	9157	2
1284912	9157	2
1284911	9157	1
1283751	9157	1
1284907	9157	1
1284908	9157	2
1284909	9157	1
1284908	9160	1
1284907	9160	1
1284912	9160	2
1284911	9160	2
1283751	9160	1
1284910	9160	2
1283748	9160	1
1284914	9160	2
1284909	9160	2
1283750	9160	2
1284913	9160	1
1283749	9160	2
1284909	9161	2
1284908	9161	1
1283748	9161	1
1284913	9161	1
1284914	9161	2
1284910	9161	2
1284912	9161	2
1283750	9161	2
1284907	9161	1
1283751	9161	1
1284911	9161	2
1283749	9161	2
1283749	9165	2
1283750	9165	2
1284907	9165	1
1284908	9165	1
1283748	9165	1
1283751	9165	1
1284911	9165	2
1284909	9165	2
1284910	9165	2
1284912	9165	2
1284908	9167	1
1284913	9167	1
1284910	9167	2
1284914	9167	2
1283750	9167	2
1283748	9167	1
1284907	9167	1
1284911	9167	2
1283749	9167	2
1283751	9167	1
1284912	9167	2
1284909	9167	2
1284913	9175	2
1284910	9175	2
1284909	9175	1
1283751	9175	1
1284911	9175	2
1284908	9175	2
1283750	9175	2
1284907	9175	1
1284912	9175	4
1284914	9175	1
1283749	9175	2
1283748	9175	2
1283751	9176	2
1283748	9176	2
1284909	9176	1
1284908	9176	2
1284914	9176	1
1283749	9176	2
1284910	9176	1
1284907	9176	1
1284913	9176	2
1283750	9176	1
1284911	9176	1
1284912	9176	1
1284914	9182	1
1283749	9182	2
1283751	9182	1
1284907	9182	1
1283750	9182	2
1284909	9182	2
1284912	9182	2
1284911	9182	2
1284908	9182	2
1283748	9182	2
1284913	9182	2
1284910	9182	2
1283751	9192	1
1284910	9192	2
1283748	9192	2
1284911	9192	2
1284914	9192	1
1283749	9192	2
1284908	9192	2
1284913	9192	2
1284912	9192	2
1284907	9192	1
1283750	9192	2
1284909	9192	2
1284911	9193	2
1283750	9193	2
1284913	9193	2
1284907	9193	1
1284908	9193	2
1283749	9193	2
1284914	9193	1
1284912	9193	2
1284909	9193	1
1283748	9193	2
1283751	9193	1
1284910	9193	2
1284912	9197	1
1284908	9197	2
1284914	9197	1
1283749	9197	1
1284909	9197	1
1283750	9197	1
1284911	9197	1
1284907	9197	1
1284910	9197	1
1283751	9197	2
1283748	9197	2
1284913	9197	2
1284908	9200	2
1283748	9200	2
1284911	9200	1
1284909	9200	1
1284912	9200	1
1284913	9200	2
1283749	9200	2
1284914	9200	1
1283750	9200	2
1284907	9200	1
1283751	9200	1
1284910	9200	1
1283750	9201	2
1284911	9201	2
1284907	9201	1
1283748	9201	1
1284912	9201	2
1284908	9201	1
1284913	9201	1
1283751	9201	1
1284910	9201	2
1284909	9201	2
1283749	9201	2
1284914	9201	2
1283751	9209	1
1284912	9209	1
1283750	9209	1
1284909	9209	1
1283749	9209	2
1284907	9209	1
1283748	9209	2
1284911	9209	2
1284910	9209	1
1284914	9209	1
1284908	9209	2
1284913	9209	2
1284912	9211	2
1283749	9211	2
1284908	9211	2
1284914	9211	1
1284909	9211	2
1283750	9211	2
1284913	9211	2
1284911	9211	2
1283748	9211	2
1284907	9211	1
1284910	9211	2
1283751	9211	1
1283749	9213	2
1283751	9213	1
1283748	9213	2
1284907	9213	1
1284912	9213	2
1284909	9213	2
1284908	9213	2
1283750	9213	2
1284913	9213	2
1284910	9213	2
1284911	9213	2
1284914	9213	1
1283748	9216	2
1283751	9216	1
1284912	9216	2
1284911	9216	2
1284914	9216	1
1283750	9216	2
1284910	9216	2
1284913	9216	2
1284907	9216	1
1284908	9216	2
1283749	9216	2
1284909	9216	1
1283749	9217	1
1283750	9217	1
1284914	9217	1
1284911	9217	1
1284913	9217	2
1284907	9217	1
1284908	9217	2
1283751	9217	1
1284912	9217	1
1284910	9217	1
1283748	9217	2
1284909	9217	1
1284910	9220	1
1283750	9220	2
1284907	9220	1
1283751	9220	1
1283748	9220	2
1284912	9220	2
1284908	9220	2
1284913	9220	2
1284911	9220	2
1284909	9220	1
1283749	9220	2
1284914	9220	1
1284913	9222	2
1284910	9222	2
1284912	9222	2
1284909	9222	2
1283749	9222	2
1283751	9222	1
1284911	9222	2
1284907	9222	1
1284914	9222	1
1283748	9222	2
1284908	9222	2
1283750	9222	2
1283750	9233	2
1284908	9233	1
1284912	9233	2
1284910	9233	2
1284913	9233	1
1284907	9233	1
1284914	9233	2
1283749	9233	2
1284911	9233	2
1284909	9233	2
1283751	9233	1
1283748	9233	1
1284908	9234	1
1284907	9234	1
1284911	9234	2
1284912	9234	2
1284913	9234	1
1283751	9234	1
1284910	9234	2
1283748	9234	1
1284909	9234	2
1283750	9234	2
1284914	9234	2
1283749	9234	2
1283749	9237	2
1284912	9237	2
1283750	9237	2
1284914	9237	1
1284909	9237	2
1284910	9237	2
1283748	9237	2
1283751	9237	1
1284908	9237	2
1284913	9237	2
1284911	9237	2
1284907	9237	1
1284909	9254	2
1284914	9254	1
1284913	9254	2
1284908	9254	2
1284911	9254	2
1283751	9254	1
1283748	9254	2
1284910	9254	2
1284912	9254	2
1283750	9254	2
1283749	9254	2
1284907	9254	1
1284909	9269	1
1284907	9269	1
1284911	9269	2
1283749	9269	2
1283750	9269	2
1284910	9269	2
1283748	9269	2
1283751	9269	1
1284908	9269	2
1284914	9269	1
1284913	9269	2
1284912	9269	2
1284911	9273	2
1284907	9273	1
1283748	9273	2
1284912	9273	2
1284913	9273	2
1284910	9273	2
1283749	9273	2
1284914	9273	1
1284909	9273	2
1283750	9273	2
1283751	9273	1
1284908	9273	2
1284910	9274	2
1284913	9274	2
1283750	9274	2
1283748	9274	2
1284907	9274	1
1284912	9274	2
1284911	9274	2
1284908	9274	2
1283751	9274	1
1284914	9274	1
1283749	9274	2
1284909	9274	1
1284908	9279	2
1284910	9279	1
1284914	9279	1
1283750	9279	2
1284913	9279	2
1283748	9279	2
1283751	9279	1
1284909	9279	1
1284912	9279	2
1284907	9279	1
1283749	9279	2
1284911	9279	1
1283751	9294	1
1284913	9294	2
1284914	9294	1
1283749	9294	2
1284909	9294	2
1284907	9294	1
1284911	9294	2
1283750	9294	2
1283748	9294	2
1284908	9294	2
1284910	9294	2
1284912	9294	2
1284909	9295	2
1284908	9295	2
1284907	9295	1
1284910	9295	2
1283749	9295	2
1284914	9295	1
1284911	9295	2
1284912	9295	2
1283751	9295	1
1283750	9295	2
1284913	9295	2
1283748	9295	2
1284914	9307	2
1284908	9307	1
1283748	9307	1
1284911	9307	2
1284907	9307	1
1284909	9307	2
1283751	9307	2
1284913	9307	1
1284910	9307	2
1283749	9307	2
1283750	9307	2
1284912	9307	2
1284908	9312	1
1284909	9312	2
1284914	9312	2
1283749	9312	2
1283750	9312	2
1284910	9312	2
1284912	9312	2
1283751	9312	1
1284913	9312	1
1283748	9312	1
1284907	9312	1
1284911	9312	2
1284912	9324	2
1284910	9324	2
1284907	9324	1
1283750	9324	2
1284908	9324	2
1284909	9324	1
1284911	9324	4
1283751	9324	1
1283748	9324	2
1284914	9324	1
1283749	9324	1
1284913	9324	2
1284909	9329	2
1284913	9329	2
1284912	9329	2
1283748	9329	2
1284910	9329	1
1284908	9329	2
1284911	9329	2
1283750	9329	2
1284907	9329	1
1283749	9329	2
1284914	9329	1
1283751	9329	1
1283751	9333	1
1284911	9333	2
1283750	9333	2
1284914	9333	1
1284907	9333	1
1284912	9333	4
1284910	9333	2
1283749	9333	2
1284909	9333	2
1284913	9333	2
1283748	9333	2
1284908	9333	4
1283750	9337	2
1284911	9337	1
1284913	9337	2
1283748	9337	2
1284910	9337	1
1283751	9337	1
1284912	9337	1
1284907	9337	1
1284908	9337	2
1284914	9337	1
1283749	9337	1
1284909	9337	1
1284914	9340	4
1284907	9340	4
1284913	9340	4
1284910	9340	4
1283749	9340	4
1283750	9340	4
1284908	9340	4
1284911	9340	4
1283751	9340	4
1284909	9340	4
1284912	9340	4
1283748	9340	4
1283751	9346	1
1284911	9346	2
1284913	9346	2
1283750	9346	2
1284912	9346	2
1284910	9346	1
1284908	9346	4
1284909	9346	1
1284914	9346	1
1283749	9346	2
1284907	9346	1
1283748	9346	2
1283749	9360	2
1284914	9360	2
1284911	9360	2
1284912	9360	2
1284909	9360	2
1283751	9360	1
1284907	9360	1
1283748	9360	1
1284910	9360	2
1283750	9360	2
1284913	9360	1
1284908	9360	1
1284911	9365	1
1284907	9365	1
1284910	9365	1
1284908	9365	2
1284913	9365	2
1284914	9365	1
1284909	9365	1
1283748	9365	2
1283749	9365	1
1284912	9365	1
1283750	9365	1
1283751	9365	1
1283748	9368	2
1284908	9368	2
1284914	9368	1
1284909	9368	1
1283749	9368	1
1284913	9368	2
1284912	9368	1
1284911	9368	1
1283751	9368	1
1284907	9368	1
1283750	9368	1
1284910	9368	2
1284908	9371	2
1284909	9371	1
1284914	9371	1
1283751	9372	1
1284907	9372	1
1283750	9372	2
1284914	9372	1
1284909	9372	1
1284913	9372	2
1284910	9372	2
1284908	9372	2
1283749	9372	2
1284911	9372	2
1284912	9372	2
1283748	9372	2
1283749	9381	2
1284910	9381	2
1283750	9381	2
1284908	9381	2
1284911	9381	2
1283751	9381	1
1283748	9381	2
1284912	9381	2
1284909	9381	2
1284907	9381	1
1284914	9381	1
1284913	9381	2
1283749	9384	1
1284913	9384	2
1284914	9384	1
1284909	9384	1
1284911	9384	1
1283750	9384	1
1283748	9384	2
1284912	9384	2
1284908	9384	2
1284907	9384	1
1284910	9384	2
1283751	9384	1
1284909	9389	1
1283750	9389	2
1284914	9389	1
1284912	9389	2
1283749	9389	2
1283751	9389	1
1284910	9389	1
1284907	9389	1
1284913	9389	2
1283748	9389	2
1284908	9389	2
1284911	9389	1
1283751	9394	2
1284912	9394	2
1284908	9394	1
1284911	9394	2
1284913	9394	1
1284909	9394	2
1283750	9394	2
1284910	9394	2
1283748	9394	1
1283749	9394	2
1284914	9394	2
1284907	9394	1
1284910	11042	4
1284911	11042	4
1283751	11042	4
1283750	11042	4
1284908	11042	4
1284909	11042	4
1284914	11042	4
1283749	11042	4
1284912	11042	4
1284913	11042	4
1283748	11042	4
1284907	11042	4
1284907	11047	1
1283748	11047	2
1284910	11047	2
1284912	11047	2
1283749	11047	2
1283751	11047	1
1283750	11047	2
1284908	11047	2
1284913	11047	2
1284914	11047	1
1284909	11047	2
1284911	11047	2
1283751	11049	1
1284913	11049	2
1284909	11049	1
1283749	11049	1
1284912	11049	1
1284907	11049	1
1284910	11049	1
1284908	11049	2
1283750	11049	1
1284911	11049	1
1283748	11049	2
1284914	11049	1
1284913	11054	2
1284908	11054	2
1283751	11054	2
1284909	11054	1
1284911	11054	1
1284914	11054	1
1283750	11054	1
1283749	11054	1
1283748	11054	2
1284912	11054	1
1284907	11054	1
1284910	11054	1
1283750	11058	2
1284912	11058	1
1283751	11058	1
1284908	11058	2
1283749	11058	2
1284910	11058	1
1284914	11058	1
1284913	11058	2
1284909	11058	2
1283748	11058	2
1284907	11058	1
1284911	11058	2
1284908	11059	2
1284911	11059	1
1283749	11059	2
1284912	11059	2
1283750	11059	1
1284914	11059	1
1284913	11059	2
1283748	11059	2
1283751	11059	1
1284910	11059	2
1284907	11059	1
1284909	11059	1
1284912	11077	2
1284910	11077	2
1283748	11077	2
1283749	11077	2
1284907	11077	1
1284914	11077	1
1283750	11077	2
1284911	11077	2
1284909	11077	1
1283751	11077	1
1284913	11077	2
1284908	11077	2
1284912	11099	2
1284913	11099	2
1284910	11099	2
1283749	11099	2
1284909	11099	2
1284911	11099	2
1283750	11099	2
1284907	11099	1
1284908	11099	2
1283748	11099	2
1283751	11099	1
1284914	11099	1
1284909	11124	1
1284912	11124	1
1283750	11124	1
1284914	11124	1
1283749	11124	1
1283751	11124	1
1284908	11124	2
1284910	11124	1
1284907	11124	1
1283748	11124	2
1284911	11124	1
1284913	11124	2
1284910	11129	1
1284908	11129	2
1283751	11129	1
1284911	11129	2
1283750	11129	2
1284912	11129	2
1283749	11129	2
1283748	11129	2
1284913	11129	2
1284907	11129	1
1284909	11129	1
1284914	11129	1
1284914	11132	1
1283748	11132	2
1283749	11132	1
1284913	11132	2
1283750	11132	1
1284912	11132	1
1283751	11132	2
1284911	11132	1
1284907	11132	1
1284910	11132	1
1284908	11132	2
1284909	11132	1
1284914	11137	1
1283751	11137	1
1284912	11137	2
1284913	11137	2
1283748	11137	2
1283750	11137	2
1284911	11137	1
1284908	11137	2
1284909	11137	2
1284910	11137	1
1284907	11137	1
1283749	11137	2
1283750	11145	1
1284910	11145	1
1284911	11145	1
1284914	11145	1
1284907	11145	1
1283751	11145	1
1283749	11145	1
1284912	11145	1
1284909	11145	1
1284913	11145	2
1283748	11145	2
1284908	11145	2
1283750	11164	2
1284908	11164	2
1283749	11164	1
1284912	11164	4
1284913	11164	2
1284909	11164	1
1284911	11164	2
1284914	11164	1
1284910	11164	1
1283748	11164	2
1284907	11164	1
1283751	11164	1
1283750	11200	2
1283751	11200	1
1284910	11200	2
1283749	11200	2
1284912	11200	2
1284911	11200	2
1284907	11200	1
1284913	11200	1
1284914	11200	2
1284909	11200	2
1283748	11200	1
1284908	11200	1
1284911	11201	2
1284907	11201	1
1284910	11201	2
1284912	11201	2
1283751	11201	1
1284909	11201	2
1283749	11201	2
1284913	11201	1
1284908	11201	1
1283750	11201	2
1283748	11201	1
1284914	11201	2
1284907	11605	1
1283748	11605	2
1284912	11605	2
1284909	11605	1
1284908	11605	2
1283750	11605	1
1284913	11605	2
1284911	11605	1
1284910	11605	1
1283749	11605	1
1283751	11605	2
1284914	11605	1
1283749	11606	2
1284914	11606	1
1284912	11606	2
1283750	11606	1
1283748	11606	2
1284909	11606	1
1283751	11606	1
1284907	11606	1
1284911	11606	1
1284913	11606	2
1284910	11606	2
1284908	11606	2
1284914	11807	2
1284907	11807	1
1284911	11807	2
1284908	11807	1
1283750	11807	2
1283749	11807	2
1284913	11807	1
1283751	11807	1
1284909	11807	2
1283748	11807	1
1284912	11807	2
1284910	11807	2
1284907	11867	1
1283751	11867	1
1284908	11867	4
1284914	11867	2
1284913	11867	1
1284909	11867	2
1284911	11867	2
1284910	11867	2
1284912	11867	2
1283748	11867	1
1283750	11867	2
1283749	11867	2
1283751	13318	1
1284914	13318	1
1284910	13318	2
1284909	13318	1
1283748	13318	2
1284907	13318	1
1284912	13318	2
1283749	13318	2
1283750	13318	2
1284913	13318	2
1284911	13318	2
1284908	13318	2
1284910	13869	2
1284912	13869	2
1283750	13869	2
1284907	13869	1
1283749	13869	2
1284914	13869	2
1283751	13869	1
1284911	13869	2
1284913	13869	1
1284908	13869	1
1284909	13869	2
1283748	13869	1
1284907	14026	1
1283751	14026	1
1284911	14026	1
1284909	14026	1
1284913	14026	2
1284910	14026	1
1283748	14026	2
1283750	14026	1
1283749	14026	2
1284912	14026	1
1284914	14026	1
1284908	14026	2
1284910	14071	2
1284908	14071	1
1283748	14071	1
1284914	14071	2
1284912	14071	2
1283751	14071	2
1284913	14071	1
1284909	14071	2
1283749	14071	2
1283750	14071	2
1284907	14071	1
1284911	14071	2
1283749	14082	2
1283751	14082	1
1284914	14082	2
1283750	14082	2
1284907	14082	1
1284908	14082	1
1284913	14082	1
1284910	14082	2
1283748	14082	1
1284912	14082	2
1284911	14082	2
1284909	14082	2
1284912	14084	2
1283751	14084	1
1284914	14084	1
1283750	14084	1
1284911	14084	2
1284913	14084	2
1284910	14084	2
1284907	14084	1
1284908	14084	2
1283749	14084	1
1284909	14084	1
1283748	14084	2
1283748	14085	1
1284910	14085	2
1284912	14085	2
1284911	14085	2
1284907	14085	1
1284908	14085	1
1283751	14085	1
1284913	14085	1
1283750	14085	2
1283749	14085	2
1284914	14085	2
1284909	14085	2
1284909	14090	2
1284908	14090	1
1284914	14090	2
1284913	14090	1
1284910	14090	2
1283749	14090	2
1284912	14090	2
1283751	14090	1
1284911	14090	2
1283750	14090	2
1283748	14090	1
1284907	14090	1
1283751	14137	1
1284908	14137	1
1283748	14137	1
1284909	14137	2
1284907	14137	1
1283749	14137	2
1283750	14137	2
1284912	14137	2
1284913	14137	1
1284910	14137	2
1284911	14137	2
1284914	14137	2
1283749	14882	2
1284914	14882	2
1284910	14882	2
1283751	14882	1
1284907	14882	1
1283748	14882	1
1284911	14882	2
1284909	14882	2
1284908	14882	1
1284913	14882	1
1284912	14882	2
1283750	14882	2
1284907	14884	1
1284912	14884	2
1284908	14884	1
1283748	14884	1
1283751	14884	1
1284909	14884	2
1284914	14884	2
1284911	14884	2
1284910	14884	2
1284913	14884	1
1283750	14884	2
1283749	14884	2
1283749	14893	2
1284912	14893	2
1283750	14893	2
1284907	14893	1
1283751	14893	1
1284913	14893	1
1284909	14893	2
1284911	14893	2
1284914	14893	2
1284908	14893	1
1283748	14893	1
1284910	14893	2
1284911	14898	2
1283750	14898	2
1284910	14898	2
1284912	14898	2
1283749	14898	2
1284907	14898	1
1283751	14898	1
1284909	14898	2
1283748	14898	1
1284914	14898	2
1284913	14898	1
1284908	14898	1
1284909	14906	1
1284908	14906	2
1284910	14906	1
1283750	14906	1
1284912	14906	1
1284914	14906	1
1283751	14906	2
1284911	14906	1
1283749	14906	2
1284907	14906	1
1284913	14906	2
1283748	14906	2
1284914	14916	2
1283751	14916	1
1284908	14916	1
1283749	14916	2
1284913	14916	1
1284912	14916	2
1283748	14916	1
1284907	14916	1
1283750	14916	2
1284911	14916	2
1284909	14916	2
1284910	14916	2
1284910	14918	2
1284911	14918	1
1284914	14918	1
1284912	14918	1
1283750	14918	2
1283749	14918	2
1284908	14918	2
1284909	14918	1
1284913	14918	2
1283751	14918	1
1283748	14918	2
1284907	14918	1
1284909	14920	2
1284912	14920	2
1284914	14920	2
1284910	14920	2
1283750	14920	2
1284913	14920	1
1284907	14920	1
1284908	14920	1
1283751	14920	1
1283748	14920	1
1283749	14920	2
1284911	14920	2
1284910	14922	1
1283751	14922	1
1283748	14922	2
1283750	14922	1
1284907	14922	1
1284911	14922	1
1283749	14922	2
1284908	14922	2
1284914	14922	1
1284912	14922	1
1284913	14922	2
1284909	14922	1
1283750	14923	2
1284913	14923	2
1284914	14923	1
1284912	14923	2
1284909	14923	1
1284910	14923	2
1284907	14923	1
1284911	14923	2
1283749	14923	2
1283751	14923	1
1283748	14923	2
1284908	14923	2
1284907	14924	1
1284909	14924	1
1284911	14924	1
1283750	14924	1
1284910	14924	1
1284914	14924	1
1283749	14924	2
1284913	14924	2
1284912	14924	2
1283748	14924	2
1283751	14924	1
1284908	14924	2
1283751	15051	1
1283750	15051	2
1283748	15051	2
1284911	15051	2
1284913	15051	2
1283749	15051	2
1284909	15051	1
1284910	15051	2
1284914	15051	1
1284912	15051	2
1284908	15051	2
1284907	15051	1
1284911	15204	2
1284914	15204	2
1284909	15204	2
1284910	15204	2
1284913	15204	1
1284907	15204	1
1283751	15204	1
1283748	15204	1
1284908	15204	1
1283750	15204	2
1284912	15204	2
1283749	15204	2
1284914	15205	2
1284912	15205	2
1284913	15205	1
1283748	15205	1
1283751	15205	1
1283750	15205	2
1284909	15205	2
1284908	15205	1
1284911	15205	2
1283749	15205	2
1284907	15205	1
1284910	15205	2
1284914	15208	2
1284910	15208	2
1284911	15208	2
1284912	15208	2
1284907	15208	1
1284913	15208	1
1283750	15208	2
1283751	15208	1
1284909	15208	2
1283748	15208	1
1284908	15208	1
1283749	15208	2
1284909	15216	4
1283750	15216	4
1283749	15216	4
1283751	15216	4
1284914	15216	4
1284910	15216	4
1284907	15216	4
1284911	15216	4
1284913	15216	4
1283748	15216	4
1284912	15216	4
1284908	15216	4
1283748	15217	1
1283751	15217	2
1283750	15217	2
1284909	15217	2
1284907	15217	1
1284910	15217	2
1284911	15217	2
1284908	15217	1
1284913	15217	1
1284912	15217	2
1284914	15217	2
1283749	15217	2
1284910	15224	2
1283749	15224	2
1284914	15224	1
1284912	15224	2
1283748	15224	2
1284907	15224	1
1283750	15224	2
1284911	15224	2
1284908	15224	2
1284913	15224	2
1283751	15224	1
1284909	15224	2
1284912	15226	2
1283750	15226	2
1284911	15226	2
1284913	15226	1
1284907	15226	1
1284910	15226	2
1284914	15226	2
1283748	15226	1
1284909	15226	2
1284908	15226	1
1283749	15226	2
1283751	15226	1
1283750	15227	2
1284912	15227	2
1283749	15227	2
1283748	15227	1
1284909	15227	2
1283751	15227	1
1284911	15227	2
1284910	15227	2
1284913	15227	1
1284907	15227	1
1284908	15227	1
1284914	15227	2
1284907	15228	1
1284912	15228	2
1284910	15228	1
1284908	15228	2
1283751	15228	1
1283748	15228	2
1284909	15228	1
1284914	15228	1
1284911	15228	1
1283750	15228	2
1283749	15228	2
1284913	15228	2
1284914	15234	2
1284909	15234	2
1284910	15234	2
1283750	15234	2
1283751	15234	1
1284912	15234	2
1284908	15234	1
1284911	15234	2
1283749	15234	2
1284907	15234	1
1284913	15234	1
1283748	15234	1
1284913	15235	1
1284914	15235	2
1284910	15235	2
1284909	15235	2
1283750	15235	2
1283751	15235	1
1284911	15235	2
1284908	15235	1
1284907	15235	1
1283749	15235	2
1284912	15235	2
1283748	15235	1
1284909	15236	2
1284907	15236	1
1283748	15236	1
1284911	15236	2
1284912	15236	2
1284913	15236	1
1284910	15236	2
1283750	15236	2
1284914	15236	2
1283749	15236	2
1284908	15236	1
1283751	15236	1
1284909	15238	2
1284911	15238	2
1284912	15238	2
1283750	15238	2
1284907	15238	1
1284914	15238	2
1283751	15238	1
1284910	15238	2
1283749	15238	2
1283748	15238	1
1284908	15238	1
1284913	15238	1
1283751	15239	1
1284913	15239	1
1284914	15239	2
1284909	15239	2
1283749	15239	2
1284911	15239	2
1284910	15239	2
1284907	15239	1
1283748	15239	1
1284912	15239	2
1284908	15239	1
1283750	15239	2
1284909	15240	2
1283750	15240	2
1284911	15240	2
1284913	15240	2
1284910	15240	2
1284914	15240	1
1283749	15240	2
1283748	15240	2
1283751	15240	1
1284908	15240	2
1284912	15240	2
1284907	15240	1
1283749	15241	2
1284914	15241	2
1283751	15241	1
1284907	15241	1
1283748	15241	1
1283750	15241	2
1284911	15241	2
1284913	15241	1
1284912	15241	2
1284910	15241	2
1284908	15241	1
1284909	15241	2
1284907	15243	1
1284910	15243	2
1283748	15243	2
1283751	15243	1
1284914	15243	1
1283749	15243	2
1284908	15243	2
1284913	15243	2
1284912	15243	2
1283750	15243	2
1284911	15243	2
1284909	15243	2
1284913	16022	4
1284911	16022	4
1283751	16022	4
1284909	16022	4
1283750	16022	4
1284912	16022	4
1284914	16022	4
1283749	16022	4
1284908	16022	4
1284910	16022	4
1283748	16022	4
1284907	16022	4
1283749	16037	2
1284914	16037	1
1284908	16037	2
1284913	16037	2
1284910	16037	2
1284912	16037	2
1284909	16037	2
1283748	16037	2
1284911	16037	2
1284907	16037	1
1283751	16037	1
1283750	16037	2
1284909	16065	2
1284913	16065	1
1284908	16065	1
1284910	16065	2
1284911	16065	2
1283749	16065	2
1284914	16065	2
1283748	16065	1
1284912	16065	2
1284907	16065	1
1283751	16065	1
1283750	16065	2
1284910	16269	2
1284908	16269	1
1284912	16269	2
1283751	16269	1
1284914	16269	2
1283748	16269	1
1284911	16269	2
1283750	16269	2
1284913	16269	1
1283749	16269	2
1284909	16269	2
1284907	16269	1
1284911	16271	2
1284913	16271	1
1283750	16271	2
1284908	16271	1
1284912	16271	2
1284910	16271	2
1283751	16271	1
1284914	16271	2
1283749	16271	2
1284907	16271	1
1283748	16271	1
1284909	16271	2
1284911	16447	1
1284913	16447	2
1283751	16447	1
1284914	16447	1
1283750	16447	2
1284910	16447	1
1283748	16447	2
1284907	16447	1
1284908	16447	2
1284909	16447	1
1283749	16447	2
1284912	16447	2
1284909	16449	1
1284907	16449	1
1283749	16449	2
1284908	16449	2
1284913	16449	2
1283750	16449	2
1284911	16449	1
1283748	16449	2
1284914	16449	1
1283751	16449	1
1284912	16449	4
1284910	16449	1
1284914	16452	1
1283748	16452	2
1283750	16452	2
1284910	16452	2
1283749	16452	2
1284911	16452	1
1284913	16452	2
1284909	16452	1
1284912	16452	2
1284908	16452	2
1284907	16452	1
1283751	16452	1
1283748	16453	2
1284913	16453	2
1284911	16453	1
1284908	16453	2
1284910	16453	2
1283749	16453	2
1284914	16453	2
1283751	16453	2
1284912	16453	1
1284907	16453	2
1283750	16453	2
1284909	16453	1
1283748	16454	2
1283751	16454	1
1284911	16454	2
1283749	16454	2
1284907	16454	1
1284912	16454	2
1283750	16454	2
1284913	16454	2
1284909	16454	1
1284910	16454	1
1284914	16454	1
1284908	16454	2
1284914	16458	1
1283751	16458	1
1284909	16458	1
1283748	16458	2
1283749	16458	2
1284908	16458	2
1284912	16458	1
1284911	16458	1
1283750	16458	1
1284907	16458	1
1284913	16458	2
1284910	16458	1
1284911	16460	1
1284912	16460	2
1283751	16460	4
1283748	16460	2
1283750	16460	2
1284913	16460	2
1284907	16460	1
1284910	16460	2
1283749	16460	2
1284909	16460	1
1284914	16460	1
1284908	16460	2
1284908	16463	2
1284907	16463	1
1284910	16463	2
1283751	16463	1
1284913	16463	2
1283750	16463	2
1284912	16463	2
1284909	16463	1
1284914	16463	1
1283749	16463	2
1283748	16463	2
1284911	16463	2
1283750	16468	1
1284914	16468	1
1284911	16468	1
1284910	16468	1
1284912	16468	1
1283749	16468	2
1284907	16468	1
1283751	16468	2
1284913	16468	2
1284908	16468	2
1284909	16468	1
1283748	16468	2
1284907	16471	1
1284910	16471	1
1284912	16471	1
1283751	16471	1
1284914	16471	1
1284911	16471	2
1284908	16471	2
1283748	16471	2
1284909	16471	1
1283750	16471	1
1284913	16471	2
1283749	16471	2
1284909	16472	1
1284911	16472	1
1284908	16472	2
1283749	16472	1
1284907	16472	1
1284913	16472	2
1284914	16472	1
1283750	16472	1
1284912	16472	1
1283751	16472	1
1283748	16472	2
1284910	16472	1
1283748	16473	2
1284908	16473	2
1284911	16473	2
1284913	16473	2
1283750	16473	2
1284914	16473	1
1284910	16473	2
1284907	16473	1
1283749	16473	2
1283751	16473	1
1284912	16473	2
1284909	16473	1
1284912	16476	2
1284909	16476	1
1283751	16476	1
1283750	16476	2
1283749	16476	2
1284910	16476	2
1284907	16476	1
1284914	16476	1
1284908	16476	2
1283748	16476	2
1284911	16476	2
1284913	16476	2
1283749	16477	2
1284910	16477	2
1284907	16477	1
1284913	16477	2
1283748	16477	2
1283750	16477	2
1284909	16477	2
1284911	16477	2
1284914	16477	1
1283751	16477	1
1284912	16477	2
1284908	16477	2
1284913	16480	2
1283751	16480	1
1283749	16480	2
1284908	16480	2
1283748	16480	2
1284912	16480	2
1284914	16480	1
1284911	16480	2
1284910	16480	2
1284907	16480	1
1284909	16480	2
1283750	16480	2
1284907	16483	1
1284909	16483	1
1283751	16483	1
1284914	16483	1
1283748	16483	2
1284911	16483	1
1284908	16483	2
1284913	16483	2
1284910	16483	1
1283750	16483	2
1284912	16483	2
1283749	16483	1
1284912	16485	2
1283748	16485	1
1284914	16485	2
1283750	16485	2
1284909	16485	2
1284908	16485	1
1283749	16485	2
1284911	16485	2
1284907	16485	1
1284913	16485	1
1284910	16485	2
1283751	16485	1
1284913	16487	1
1284909	16487	2
1284911	16487	2
1284908	16487	1
1284914	16487	2
1284912	16487	2
1283749	16487	2
1283748	16487	1
1284907	16487	1
1283750	16487	2
1284910	16487	2
1283751	16487	1
1284913	16488	1
1284912	16488	2
1283750	16488	2
1284909	16488	2
1284910	16488	2
1284911	16488	2
1284914	16488	2
1283748	16488	1
1283749	16488	2
1283751	16488	1
1284907	16488	1
1284908	16488	1
1283748	16490	2
1284912	16490	4
1284914	16490	4
1284908	16490	4
1284913	16490	4
1284910	16490	4
1284911	16490	4
1284909	16490	4
1283750	16490	1
1284907	16490	4
1283751	16490	1
1283749	16490	1
1284909	16492	2
1284910	16492	2
1284908	16492	1
1284907	16492	1
1284912	16492	2
1283749	16492	2
1284914	16492	2
1284911	16492	2
1283751	16492	1
1284913	16492	1
1283748	16492	1
1283750	16492	2
1284913	16495	1
1283749	16495	2
1284910	16495	2
1284912	16495	2
1283748	16495	1
1283750	16495	2
1284907	16495	1
1284909	16495	2
1283751	16495	1
1284908	16495	1
1284914	16495	2
1284911	16495	2
1283750	16496	2
1284908	16496	1
1284909	16496	2
1284907	16496	1
1284910	16496	2
1283749	16496	2
1283751	16496	1
1283748	16496	1
1284914	16496	2
1284911	16496	2
1284912	16496	2
1284913	16496	1
1283751	16497	1
1284911	16497	4
1284913	16497	4
1283750	16497	2
1284912	16497	4
1283749	16497	2
1284909	16497	4
1284907	16497	4
1284908	16497	4
1283748	16497	1
1284914	16497	4
1284910	16497	4
1284907	16498	1
1283750	16498	2
1284912	16498	2
1283751	16498	1
1284911	16498	2
1284908	16498	1
1283748	16498	1
1284914	16498	2
1284910	16498	2
1284913	16498	1
1283749	16498	2
1284909	16498	2
1284908	16500	1
1284913	16500	1
1283748	16500	1
1284909	16500	2
1283750	16500	2
1284907	16500	1
1284911	16500	2
1284914	16500	2
1283751	16500	1
1284912	16500	2
1284910	16500	2
1283749	16500	2
1283749	16502	2
1284912	16502	2
1283748	16502	1
1284914	16502	2
1283751	16502	1
1284908	16502	1
1283750	16502	2
1284907	16502	1
1284910	16502	2
1284913	16502	1
1284911	16502	2
1284909	16502	2
1284913	16503	2
1284911	16503	2
1284909	16503	2
1284914	16503	1
1283749	16503	2
1283750	16503	2
1284907	16503	1
1284912	16503	2
1284908	16503	2
1283748	16503	2
1284910	16503	2
1283751	16503	1
1284909	16824	2
1283749	16824	2
1283751	16824	1
1283748	16824	1
1284910	16824	2
1284911	16824	2
1284912	16824	2
1284907	16824	1
1284908	16824	1
1283750	16824	2
1284911	17510	2
1284910	17510	2
1283751	17510	4
1284909	17510	1
1284908	17510	2
1283750	17510	4
1284912	17510	4
1283749	17510	4
1284907	17510	1
1283748	17510	4
1284912	17704	1
1284914	17704	1
1284907	17704	1
1284910	17704	1
1283751	17704	1
1283748	17704	2
1284908	17704	2
1284909	17704	1
1284911	17704	1
1283749	17704	1
1284913	17704	2
1283750	17704	1
1284912	17717	2
1284911	17717	2
1284907	17717	1
1283749	17717	2
1284914	17717	1
1284909	17717	1
1284908	17717	2
1284913	17717	2
1283751	17717	1
1283750	17717	2
1283748	17717	2
1284910	17717	2
1284909	17958	1
1284907	17958	1
1283751	17958	2
1284910	17958	1
1284912	17958	1
1284911	17958	1
1283748	17958	2
1283749	17958	1
1284913	17958	2
1284914	17958	1
1283750	17958	1
1284908	17958	2
1283750	17980	2
1284908	17980	2
1283751	17980	1
1284909	17980	1
1283748	17980	2
1284911	17980	2
1284914	17980	1
1284913	17980	2
1284907	17980	1
1284910	17980	2
1283749	17980	2
1284912	17980	2
1284911	17981	2
1283751	17981	1
1284910	17981	2
1284907	17981	1
1284914	17981	2
1284909	17981	2
1284908	17981	1
1283750	17981	2
1284913	17981	1
1284912	17981	2
1283748	17981	1
1283749	17981	2
1283748	18286	2
1283749	18286	2
1284911	18286	1
1284914	18286	1
1284910	18286	2
1284908	18286	2
1283750	18286	1
1284907	18286	1
1283751	18286	1
1284909	18286	1
1284912	18286	4
1284913	18286	2
1284912	18287	2
1284913	18287	2
1284909	18287	2
1284911	18287	2
1283748	18287	2
1283750	18287	2
1284908	18287	2
1284914	18287	1
1283749	18287	2
1284910	18287	2
1284907	18287	1
1283751	18287	1
1284914	18288	1
1284912	18288	2
1283751	18288	1
1284911	18288	1
1283750	18288	1
1284913	18288	2
1284907	18288	1
1284910	18288	1
1283749	18288	1
1284909	18288	1
1284908	18288	2
1283748	18288	2
1284910	18289	2
1284908	18289	1
1283750	18289	2
1283751	18289	1
1284911	18289	2
1283749	18289	2
1284907	18289	1
1283748	18289	1
1284909	18289	2
1284912	18289	2
1284914	18289	2
1284913	18289	1
1284908	18290	2
1284911	18290	2
1284912	18290	2
1284910	18290	2
1284913	18290	2
1284914	18290	1
1283748	18290	2
1284909	18290	1
1284907	18290	1
1283751	18290	1
1283750	18290	2
1283749	18290	2
1284908	18291	2
1284907	18291	1
1283751	18291	2
1284913	18291	2
1284914	18291	2
1283748	18291	2
1284911	18291	1
1284910	18291	1
1284912	18291	1
1283749	18291	1
1284909	18291	1
1283750	18291	1
1284909	18292	2
1283750	18292	2
1284907	18292	1
1284913	18292	1
1284908	18292	1
1283749	18292	2
1284912	18292	2
1284914	18292	2
1284910	18292	2
1283748	18292	1
1284911	18292	2
1283751	18292	1
1284909	18295	2
1284910	18295	2
1284911	18295	2
1283748	18295	1
1284912	18295	2
1284913	18295	1
1284914	18295	2
1284907	18295	1
1283750	18295	2
1283749	18295	2
1283751	18295	1
1284908	18295	1
1284909	18297	2
1283751	18297	1
1283749	18297	2
1283748	18297	1
1284908	18297	1
1284907	18297	1
1284914	18297	2
1284911	18297	2
1283750	18297	2
1284913	18297	1
1284910	18297	2
1284912	18297	2
1283748	18300	2
1284910	18300	2
1284914	18300	1
1284908	18300	2
1283750	18300	1
1284909	18300	1
1283751	18300	1
1283749	18300	2
1284907	18300	1
1284911	18300	2
1284912	18300	2
1284913	18300	2
1283750	18301	2
1284909	18301	2
1284912	18301	2
1284910	18301	2
1283748	18301	1
1284911	18301	2
1284907	18301	1
1284914	18301	2
1283751	18301	1
1283749	18301	2
1284908	18301	1
1284913	18301	1
1284909	18303	1
1283751	18303	1
1284907	18303	1
1284911	18303	1
1283748	18303	2
1284912	18303	2
1284910	18303	2
1284913	18303	2
1283750	18303	2
1284908	18303	2
1284914	18303	1
1283749	18303	2
1283749	18304	2
1283750	18304	2
1283748	18304	2
1284909	18304	2
1284914	18304	1
1284911	18304	2
1284907	18304	1
1284912	18304	2
1284913	18304	2
1284908	18304	1
1284910	18304	2
1283751	18304	1
1284914	18305	2
1284913	18305	2
1283748	18305	2
1284911	18305	1
1283750	18305	2
1284908	18305	2
1283751	18305	2
1284909	18305	1
1284907	18305	2
1283749	18305	2
1284912	18305	1
1284910	18305	2
1283750	18306	2
1284914	18306	1
1284908	18306	2
1284909	18306	2
1284907	18306	1
1283749	18306	2
1284913	18306	2
1283748	18306	2
1284910	18306	2
1284912	18306	2
1283751	18306	1
1284911	18306	2
1284907	18308	1
1283749	18308	2
1284912	18308	2
1284909	18308	2
1283751	18308	1
1284913	18308	1
1284908	18308	1
1283748	18308	1
1284914	18308	2
1283750	18308	2
1284910	18308	2
1284911	18308	2
1284912	18309	2
1284908	18309	1
1284914	18309	2
1283749	18309	2
1284907	18309	1
1284910	18309	1
1284911	18309	2
1283751	18309	1
1284913	18309	1
1284909	18309	2
1283748	18309	1
1283750	18309	2
1283748	18310	2
1284914	18310	1
1284913	18310	2
1284911	18310	1
1284912	18310	1
1283750	18310	1
1284910	18310	1
1283749	18310	1
1284907	18310	1
1283751	18310	2
1284909	18310	1
1284908	18310	2
1284914	18312	2
1284907	18312	1
1283751	18312	1
1284913	18312	1
1284910	18312	2
1283748	18312	1
1284909	18312	2
1283750	18312	2
1284908	18312	1
1284911	18312	2
1283749	18312	2
1284912	18312	2
1283751	18313	1
1284912	18313	4
1284908	18313	4
1283750	18313	1
1284913	18313	4
1284911	18313	4
1283749	18313	2
1284914	18313	4
1284910	18313	4
1284909	18313	4
1284907	18313	4
1283748	18313	2
1284912	18314	2
1284910	18314	2
1283749	18314	2
1284907	18314	1
1283751	18314	1
1284913	18314	1
1284909	18314	2
1284908	18314	1
1283750	18314	2
1284911	18314	2
1284914	18314	2
1283748	18314	1
1284909	18316	2
1284910	18316	2
1284914	18316	2
1283748	18316	1
1283749	18316	2
1284913	18316	1
1283751	18316	1
1284907	18316	1
1284911	18316	2
1284912	18316	2
1283750	18316	2
1284908	18316	1
1283749	18317	2
1283748	18317	2
1283750	18317	2
1283751	18317	1
1284907	18317	1
1284908	18317	2
1284909	18317	1
1284910	18317	2
1284911	18317	2
1284912	18317	2
1284913	18317	2
1284914	18317	1
1284907	18321	1
1283751	18321	1
1284908	18321	2
1283749	18321	1
1284909	18321	1
1284910	18321	2
1283748	18321	2
1284914	18321	1
1284913	18321	2
1284911	18321	4
1283750	18321	1
1284912	18321	2
1284909	18326	2
1283750	18326	2
1283749	18326	2
1284914	18326	2
1284908	18326	1
1284907	18326	1
1284911	18326	2
1283748	18326	1
1284910	18326	2
1284913	18326	1
1284912	18326	2
1283751	18326	1
1284910	18327	2
1284909	18327	2
1284911	18327	2
1283750	18327	2
1284912	18327	2
1284908	18327	1
1284913	18327	1
1283751	18327	1
1284914	18327	2
1283748	18327	1
1283749	18327	2
1284907	18327	1
1284912	18330	2
1283751	18330	1
1284914	18330	1
1284909	18330	1
1284911	18330	1
1284913	18330	2
1283749	18330	2
1284908	18330	2
1284907	18330	1
1284910	18330	1
1283748	18330	2
1283750	18330	2
1283749	18331	2
1284909	18331	2
1284907	18331	1
1283751	18331	1
1284908	18331	2
1283750	18331	1
1284914	18331	1
1284913	18331	2
1284912	18331	2
1284910	18331	2
1284911	18331	1
1283748	18331	2
1283748	18332	1
1284912	18332	2
1284908	18332	1
1284914	18332	2
1284910	18332	2
1283750	18332	2
1284909	18332	2
1284907	18332	1
1284911	18332	2
1283751	18332	1
1284913	18332	1
1283749	18332	2
1284908	18335	2
1283749	18335	1
1284911	18335	1
1284912	18335	2
1283751	18335	1
1284910	18335	1
1284913	18335	2
1284907	18335	1
1284909	18335	1
1283748	18335	2
1284914	18335	1
1283750	18335	1
1283750	18411	2
1284909	18411	2
1283748	18411	2
1284910	18411	2
1284907	18411	1
1284908	18411	2
1284911	18411	2
1284912	18411	2
1283751	18411	1
1283749	18411	2
1284909	19370	1
1284907	19370	1
1284911	19370	2
1283748	19370	2
1284913	19370	2
1284910	19370	2
1283750	19370	2
1283749	19370	2
1283751	19370	1
1284908	19370	2
1284914	19370	1
1284912	19370	2
1283749	19407	1
1283750	19407	1
1283748	19407	2
1283751	19407	2
1284907	19407	1
1284912	19407	1
1284909	19407	1
1284913	19407	2
1284911	19407	1
1284914	19407	1
1284910	19407	1
1284908	19407	2
1284907	19409	1
1283750	19409	2
1284909	19409	2
1284908	19409	1
1283749	19409	2
1284911	19409	2
1283748	19409	1
1283751	19409	1
1284910	19409	2
1284914	19409	2
1284913	19409	1
1284912	19409	2
1283751	19436	1
1284911	19436	1
1284912	19436	1
1284914	19436	1
1284913	19436	2
1283750	19436	2
1284908	19436	2
1283748	19436	2
1284909	19436	1
1284907	19436	1
1283749	19436	2
1284910	19436	2
1284911	19646	1
1283751	19646	2
1284907	19646	1
1284913	19646	2
1284908	19646	2
1283748	19646	2
1284914	19646	1
1283750	19646	1
1284909	19646	1
1283749	19646	1
1284912	19646	1
1284910	19646	1
1283748	19664	2
1284913	19664	2
1284909	19664	1
1284907	19664	1
1284910	19664	1
1283750	19664	1
1284911	19664	1
1284912	19664	1
1283751	19664	2
1284908	19664	2
1283749	19664	1
1284914	19664	1
1283749	19676	2
1284914	19676	1
1284913	19676	2
1283750	19676	2
1284910	19676	2
1284911	19676	2
1284907	19676	1
1284909	19676	1
1283748	19676	2
1284908	19676	2
1283751	19676	1
1284912	19676	2
1284912	19692	2
1283749	19692	2
1284911	19692	1
1283750	19692	1
1284913	19692	2
1284907	19692	1
1284910	19692	1
1283748	19692	2
1284914	19692	1
1284908	19692	2
1283751	19692	1
1284909	19692	1
1283750	19693	2
1283751	19693	1
1284912	19693	2
1284910	19693	2
1284911	19693	2
1284909	19693	2
1284907	19693	1
1284913	19693	1
1284914	19693	2
1283748	19693	1
1284908	19693	1
1283749	19693	2
1283750	19694	2
1284907	19694	1
1284913	19694	1
1283748	19694	1
1284910	19694	2
1283749	19694	2
1284914	19694	2
1283751	19694	1
1284908	19694	1
1284912	19694	2
1284911	19694	2
1284909	19694	2
1284912	19700	2
1283750	19700	2
1284907	19700	1
1283748	19700	1
1284908	19700	1
1284910	19700	1
1283751	19700	1
1284911	19700	2
1284914	19700	2
1284909	19700	2
1284913	19700	1
1283749	19700	2
1284913	20039	1
1283748	20039	1
1283751	20039	1
1284914	20039	2
1284911	20039	2
1283750	20039	2
1284910	20039	2
1283749	20039	2
1284907	20039	1
1284912	20039	2
1284909	20039	2
1284908	20039	1
1284913	20040	2
1283751	20040	1
1283750	20040	2
1283748	20040	2
1284909	20040	1
1284912	20040	2
1284908	20040	2
1284911	20040	2
1284907	20040	1
1284914	20040	1
1283749	20040	2
1284910	20040	1
1283749	20042	2
1284914	20042	1
1284909	20042	1
1284910	20042	2
1283750	20042	2
1283751	20042	1
1284911	20042	2
1284907	20042	1
1284912	20042	2
1283748	20042	2
1284908	20042	2
1284913	20042	2
1284908	20044	2
1284912	20044	1
1284914	20044	1
1283751	20044	2
1284907	20044	1
1284909	20044	1
1283748	20044	2
1283750	20044	1
1283749	20044	1
1284910	20044	1
1284913	20044	2
1284911	20044	1
1284913	20045	1
1283751	20045	1
1284907	20045	1
1284912	20045	2
1284908	20045	1
1283749	20045	2
1284914	20045	2
1283748	20045	1
1284909	20045	2
1284910	20045	2
1284911	20045	2
1283750	20045	2
1284907	20046	2
1283748	20046	1
1284909	20046	2
1283750	20046	2
1284913	20046	1
1283749	20046	2
1284908	20046	1
1284914	20046	2
1284910	20046	2
1284911	20046	2
1284912	20046	2
1283751	20046	1
1284910	20047	1
1284909	20047	1
1283750	20047	1
1283748	20047	2
1284913	20047	2
1284912	20047	1
1284911	20047	1
1283749	20047	1
1284908	20047	2
1284907	20047	1
1284914	20047	1
1283751	20047	2
1284912	20048	2
1283750	20048	2
1284907	20048	1
1284908	20048	1
1284911	20048	2
1284914	20048	2
1284909	20048	2
1283749	20048	2
1284913	20048	1
1284910	20048	2
1283751	20048	1
1283748	20048	1
1283749	20049	2
1283748	20049	2
1284913	20049	2
1284907	20049	1
1283751	20049	1
1284909	20049	1
1284910	20049	2
1283750	20049	2
1284914	20049	1
1284912	20049	2
1284911	20049	2
1284908	20049	2
1284911	20050	2
1283750	20050	2
1284908	20050	1
1283749	20050	2
1284907	20050	1
1283751	20050	1
1283748	20050	1
1284912	20050	2
1284910	20050	2
1284909	20050	2
1284914	20050	2
1284913	20050	1
1284914	20054	2
1283751	20054	1
1283749	20054	2
1284913	20054	1
1284909	20054	2
1284910	20054	2
1284911	20054	2
1283748	20054	2
1284908	20054	1
1284907	20054	1
1283750	20054	2
1284912	20054	2
1283750	20056	2
1284910	20056	2
1284911	20056	2
1283748	20056	1
1284909	20056	2
1284914	20056	2
1283749	20056	2
1284913	20056	1
1284912	20056	2
1284908	20056	1
1283751	20056	1
1284907	20056	1
1284911	20057	2
1283751	20057	1
1284914	20057	2
1284912	20057	2
1284908	20057	1
1284909	20057	2
1283749	20057	2
1284910	20057	2
1283748	20057	1
1284907	20057	1
1283750	20057	2
1284913	20057	1
1284910	20059	2
1283749	20059	2
1283750	20059	2
1284913	20059	1
1284914	20059	2
1283748	20059	1
1284912	20059	2
1284907	20059	1
1284911	20059	2
1284908	20059	1
1284909	20059	2
1283751	20059	1
1283749	20060	2
1284912	20060	1
1284910	20060	1
1284913	20060	2
1283751	20060	1
1284909	20060	1
1284908	20060	2
1284907	20060	1
1284914	20060	1
1283748	20060	2
1283750	20060	1
1284911	20060	1
1284907	20061	1
1284912	20061	2
1283751	20061	1
1284910	20061	2
1284908	20061	1
1284909	20061	2
1284914	20061	2
1283749	20061	2
1283750	20061	2
1283748	20061	1
1284913	20061	1
1284911	20061	2
1284907	20062	1
1284914	20062	2
1284910	20062	2
1283751	20062	1
1283750	20062	2
1284911	20062	2
1284913	20062	1
1283749	20062	2
1284908	20062	1
1284909	20062	2
1284912	20062	2
1283748	20062	1
1284909	20064	1
1284908	20064	2
1284914	20064	1
1283749	20064	2
1284911	20064	2
1283750	20064	2
1284907	20064	1
1283751	20064	1
1284912	20064	2
1284913	20064	2
1284910	20064	2
1283748	20064	2
1284909	20065	1
1283751	20065	1
1284913	20065	2
1284912	20065	1
1284914	20065	1
1283750	20065	1
1283748	20065	2
1284907	20065	1
1283749	20065	2
1284910	20065	1
1284908	20065	2
1284911	20065	1
1284914	20066	1
1284910	20066	2
1284909	20066	2
1284908	20066	2
1283749	20066	2
1283750	20066	1
1284911	20066	1
1284912	20066	1
1284907	20066	1
1283751	20066	1
1283748	20066	2
1284913	20066	2
1284910	20067	2
1284911	20067	2
1283751	20067	1
1283750	20067	2
1283749	20067	2
1284908	20067	1
1284909	20067	2
1284914	20067	2
1284913	20067	1
1283748	20067	1
1284912	20067	2
1284907	20067	1
1283749	20069	2
1283750	20069	2
1284908	20069	1
1284912	20069	2
1283748	20069	1
1284910	20069	2
1284914	20069	2
1284909	20069	2
1284907	20069	1
1284911	20069	2
1283751	20069	1
1284913	20069	1
1283749	20071	2
1284913	20071	1
1283750	20071	2
1284912	20071	2
1284908	20071	1
1284907	20071	1
1284909	20071	2
1284910	20071	2
1283748	20071	1
1284911	20071	2
1283751	20071	1
1284914	20071	2
1284909	20074	2
1284914	20074	2
1284908	20074	1
1283748	20074	1
1283750	20074	2
1284913	20074	1
1284907	20074	1
1284910	20074	2
1283749	20074	2
1284911	20074	2
1284912	20074	2
1283751	20074	1
1284907	20075	1
1284912	20075	1
1284909	20075	1
1284913	20075	2
1283748	20075	2
1284914	20075	1
1283751	20075	1
1283750	20075	1
1284911	20075	2
1284908	20075	2
1284910	20075	2
1283749	20075	2
1284910	20076	1
1284911	20076	1
1284912	20076	2
1284907	20076	1
1283748	20076	2
1283750	20076	1
1283749	20076	2
1284909	20076	1
1284914	20076	1
1283751	20076	1
1284913	20076	2
1284908	20076	2
1284910	20077	2
1284907	20077	1
1284913	20077	1
1284914	20077	2
1283751	20077	1
1284912	20077	2
1284911	20077	2
1283749	20077	2
1284908	20077	1
1284909	20077	2
1283750	20077	2
1283748	20077	1
1284909	20078	2
1284914	20078	2
1284910	20078	2
1284911	20078	2
1283751	20078	1
1283750	20078	2
1284908	20078	1
1283748	20078	1
1284912	20078	2
1284913	20078	1
1283749	20078	2
1284907	20078	1
1284907	20081	1
1284911	20081	2
1284913	20081	1
1283750	20081	2
1283749	20081	2
1284912	20081	2
1284908	20081	1
1283751	20081	1
1284914	20081	2
1283748	20081	1
1284909	20081	2
1284910	20081	2
1284914	20083	1
1284911	20083	1
1283749	20083	2
1284909	20083	2
1284913	20083	2
1283750	20083	1
1284907	20083	1
1283748	20083	2
1284912	20083	1
1284908	20083	2
1283751	20083	1
1284910	20083	1
1284913	20084	2
1284911	20084	1
1283749	20084	2
1283751	20084	1
1284908	20084	2
1284909	20084	1
1284910	20084	2
1284914	20084	1
1283750	20084	2
1284907	20084	1
1283748	20084	2
1284912	20084	1
1284910	20086	2
1284909	20086	2
1284907	20086	1
1284913	20086	1
1284911	20086	2
1283748	20086	1
1284908	20086	1
1283749	20086	2
1283751	20086	1
1284912	20086	2
1284914	20086	2
1283750	20086	2
1283751	20088	1
1284913	20088	1
1284907	20088	1
1283748	20088	1
1283750	20088	2
1284910	20088	2
1284909	20088	2
1283749	20088	2
1284911	20088	2
1284908	20088	1
1284912	20088	2
1284914	20088	2
1284907	20089	1
1283751	20089	1
1284910	20089	2
1283749	20089	2
1284911	20089	2
1283750	20089	2
1284908	20089	1
1284909	20089	2
1284914	20089	2
1284913	20089	1
1284912	20089	2
1283748	20089	1
1284908	20090	1
1283751	20090	1
1283750	20090	2
1284907	20090	1
1283748	20090	1
1284910	20090	2
1284914	20090	2
1283749	20090	2
1284912	20090	2
1284911	20090	2
1284909	20090	2
1284913	20090	1
1284907	20091	1
1283750	20091	2
1284913	20091	1
1284908	20091	1
1284910	20091	2
1283751	20091	1
1284914	20091	2
1283749	20091	2
1284909	20091	2
1283748	20091	1
1284911	20091	2
1284912	20091	2
1284909	20092	4
1283750	20092	1
1283748	20092	2
1284914	20092	1
1284907	20092	4
1283751	20092	1
1284910	20092	4
1284908	20092	4
1284911	20092	4
1284913	20092	2
1284912	20092	4
1283749	20092	2
1284913	20093	1
1284912	20093	2
1283751	20093	1
1283748	20093	1
1284910	20093	2
1284911	20093	2
1283749	20093	2
1284908	20093	1
1283750	20093	2
1284914	20093	2
1284909	20093	2
1284907	20093	1
1284908	20094	1
1283751	20094	1
1284914	20094	2
1283749	20094	2
1283748	20094	1
1284907	20094	1
1284911	20094	2
1284912	20094	2
1283750	20094	2
1284913	20094	1
1284909	20094	2
1284910	20094	2
1284912	20095	2
1284911	20095	2
1284910	20095	2
1283751	20095	1
1284907	20095	1
1283749	20095	2
1284909	20095	2
1284913	20095	1
1284914	20095	2
1283748	20095	1
1283750	20095	2
1284908	20095	1
1283751	20096	1
1284908	20096	2
1284914	20096	1
1284907	20096	1
1283748	20096	2
1284911	20096	1
1284909	20096	1
1284913	20096	2
1284910	20096	2
1284912	20096	1
1283749	20096	1
1283750	20096	2
1284911	20098	2
1284914	20098	1
1283748	20098	2
1284907	20098	1
1283750	20098	2
1284913	20098	2
1284910	20098	2
1283751	20098	1
1284909	20098	1
1284908	20098	2
1284912	20098	1
1283749	20098	2
1284907	20100	1
1283748	20100	2
1284912	20100	1
1284911	20100	1
1284909	20100	1
1284914	20100	1
1284910	20100	1
1284908	20100	2
1283750	20100	2
1284913	20100	2
1283749	20100	2
1283751	20100	2
1284911	20103	2
1283751	20103	1
1283749	20103	2
1284914	20103	2
1284907	20103	1
1284910	20103	2
1284908	20103	1
1284913	20103	1
1284912	20103	2
1284909	20103	2
1283748	20103	1
1283750	20103	2
1284909	20104	2
1284907	20104	1
1284910	20104	2
1283751	20104	1
1283749	20104	2
1283750	20104	2
1283748	20104	1
1284914	20104	2
1284911	20104	2
1284912	20104	2
1284913	20104	1
1284908	20104	1
1283749	20105	1
1284909	20105	2
1284913	20105	1
1284911	20105	2
1283748	20105	1
1284910	20105	2
1284914	20105	2
1284908	20105	1
1283750	20105	2
1283751	20105	1
1284912	20105	2
1284907	20105	1
1284912	20107	2
1284909	20107	2
1283751	20107	1
1284911	20107	2
1284910	20107	2
1284913	20107	1
1283750	20107	2
1284907	20107	1
1283749	20107	2
1284914	20107	2
1283748	20107	1
1284908	20107	1
1284911	20108	2
1283750	20108	2
1284907	20108	1
1283748	20108	2
1284908	20108	2
1283749	20108	2
1284912	20108	2
1284909	20108	2
1284910	20108	1
1284913	20108	2
1283751	20108	1
1284914	20108	1
1284909	20109	2
1283749	20109	2
1284907	20109	1
1284911	20109	2
1284912	20109	2
1284914	20109	1
1283751	20109	1
1283748	20109	2
1284913	20109	2
1284910	20109	2
1284908	20109	2
1283750	20109	2
1283748	20110	2
1284910	20110	1
1284913	20110	2
1283751	20110	2
1283750	20110	1
1284908	20110	2
1284911	20110	1
1284907	20110	1
1284912	20110	1
1283749	20110	1
1284914	20110	1
1284909	20110	1
1283748	20111	1
1284913	20111	1
1284914	20111	2
1283749	20111	2
1284911	20111	2
1283751	20111	1
1284908	20111	1
1284907	20111	1
1284910	20111	2
1284912	20111	2
1283750	20111	2
1284909	20111	2
1283750	20112	2
1284911	20112	2
1284914	20112	2
1284908	20112	1
1283748	20112	1
1283751	20112	1
1284910	20112	2
1284907	20112	1
1283749	20112	2
1284912	20112	2
1284913	20112	1
1284909	20112	2
1283751	20114	1
1283749	20114	2
1284912	20114	1
1283748	20114	2
1284908	20114	2
1284907	20114	1
1283750	20114	1
1284913	20114	2
1284909	20114	1
1284911	20114	1
1284914	20114	1
1284910	20114	1
1284907	20115	1
1284910	20115	2
1283749	20115	2
1283751	20115	2
1284908	20115	1
1283750	20115	2
1284913	20115	1
1284912	20115	2
1284909	20115	2
1283748	20115	1
1284911	20115	2
1284914	20115	2
1283750	20116	2
1283748	20116	1
1284909	20116	2
1284907	20116	1
1284910	20116	2
1284911	20116	2
1283749	20116	2
1284912	20116	2
1284908	20116	1
1283751	20116	1
1284913	20116	1
1284914	20116	2
1284912	20117	2
1283750	20117	2
1284913	20117	1
1283748	20117	1
1284909	20117	2
1284907	20117	1
1284910	20117	2
1283751	20117	1
1284914	20117	2
1284908	20117	1
1284911	20117	2
1283749	20117	2
1284913	20119	1
1283751	20119	1
1283750	20119	2
1284908	20119	1
1284910	20119	2
1283749	20119	2
1284912	20119	2
1284914	20119	2
1283748	20119	1
1284907	20119	1
1284909	20119	2
1284911	20119	2
1284908	20120	2
1284907	20120	1
1284910	20120	1
1284913	20120	2
1283751	20120	1
1284914	20120	1
1283749	20120	1
1284912	20120	2
1284909	20120	1
1283750	20120	1
1283748	20120	2
1284911	20120	1
1283750	20121	1
1283748	20121	2
1284912	20121	1
1283749	20121	2
1284913	20121	2
1284911	20121	1
1284908	20121	2
1284914	20121	1
1283751	20121	4
1284910	20121	1
1284907	20121	1
1284909	20121	1
1283750	20123	2
1284912	20123	2
1283748	20123	1
1284910	20123	2
1284909	20123	2
1284914	20123	2
1283751	20123	1
1284913	20123	1
1284908	20123	1
1283749	20123	2
1284911	20123	2
1284907	20123	1
1284910	21385	1
1284911	21385	1
1284914	21385	1
1284908	21385	2
1283749	21385	1
1283751	21385	2
1284912	21385	1
1284909	21385	1
1284913	21385	2
1283750	21385	1
1283748	21385	2
1284907	21385	1
1283750	21386	2
1284912	21386	2
1283751	21386	1
1283749	21386	2
1284910	21386	1
1284909	21386	1
1284907	21386	1
1284911	21386	2
1284914	21386	1
1284913	21386	2
1283748	21386	2
1284908	21386	2
1284913	21642	1
1283750	21642	2
1283748	21642	1
1283751	21642	1
1284914	21642	2
1284912	21642	2
1284909	21642	2
1284907	21642	1
1284911	21642	2
1284908	21642	1
1283749	21642	2
1284910	21642	2
1283750	21646	1
1283751	21646	1
1284908	21646	2
1283748	21646	2
1284909	21646	1
1284907	21646	1
1284910	21646	2
1284912	21646	2
1284911	21646	2
1284913	21646	2
1284914	21646	1
1283749	21646	2
1283749	21647	1
1284910	21647	1
1284914	21647	1
1284908	21647	2
1284912	21647	1
1283751	21647	1
1284911	21647	1
1284913	21647	2
1284909	21647	1
1283748	21647	2
1284907	21647	1
1283750	21647	1
1283751	21921	1
1284911	21921	2
1283750	21921	2
1284912	21921	2
1284907	21921	1
1284908	21921	2
1284909	21921	1
1283748	21921	2
1284910	21921	2
1283749	21921	2
1284913	21921	2
1284914	21921	1
1284910	21922	1
1283748	21922	2
1284913	21922	2
1284914	21922	1
1284908	21922	2
1283751	21922	1
1283749	21922	1
1284907	21922	1
1284909	21922	1
1283750	21922	1
1284912	21922	1
1284911	21922	1
1284909	21923	2
1283748	21923	1
1283750	21923	2
1284910	21923	2
1284911	21923	2
1284908	21923	1
1284914	21923	2
1284912	21923	2
1284913	21923	1
1284907	21923	1
1283751	21923	1
1283749	21923	2
1283751	21924	1
1284913	21924	2
1284907	21924	1
1284910	21924	1
1283750	21924	2
1284912	21924	2
1284908	21924	2
1283748	21924	2
1284909	21924	2
1284911	21924	2
1283749	21924	2
1284914	21924	1
1283748	21925	2
1283749	21925	2
1284912	21925	2
1284911	21925	2
1284914	21925	1
1284910	21925	2
1284909	21925	1
1283750	21925	2
1283751	21925	1
1284907	21925	1
1284908	21925	2
1284913	21925	2
1284907	21926	1
1284912	21926	2
1284913	21926	2
1284911	21926	2
1283750	21926	2
1283749	21926	2
1284908	21926	2
1284910	21926	2
1283751	21926	1
1284909	21926	2
1283748	21926	2
1284914	21926	1
1284907	21927	1
1284913	21927	2
1284908	21927	2
1283750	21927	1
1283748	21927	2
1283749	21927	1
1284914	21927	1
1283751	21927	2
1284909	21927	1
1284912	21927	1
1284911	21927	1
1284910	21927	1
1284910	21928	1
1284909	21928	1
1284913	21928	2
1283751	21928	1
1283749	21928	1
1283748	21928	2
1284908	21928	2
1284907	21928	1
1284912	21928	1
1284914	21928	1
1283750	21928	1
1284911	21928	1
1284911	21929	1
1284910	21929	1
1284907	21929	1
1283751	21929	1
1284912	21929	1
1284913	21929	2
1284909	21929	1
1283749	21929	1
1284914	21929	1
1283748	21929	2
1283750	21929	1
1284908	21929	2
1284908	21930	2
1284913	21930	2
1284909	21930	1
1284914	21930	1
1284910	21930	1
1284907	21930	1
1283751	21930	1
1283748	21930	2
1283749	21930	2
1283750	21930	2
1284912	21930	1
1284911	21930	1
1284909	21931	2
1284914	21931	1
1284908	21931	2
1283748	21931	2
1284913	21931	2
1284907	21931	1
1284910	21931	2
1283749	21931	2
1284912	21931	2
1283751	21931	1
1284911	21931	2
1283750	21931	2
1284914	21932	1
1283749	21932	2
1284909	21932	2
1284908	21932	2
1283751	21932	1
1284911	21932	2
1284912	21932	2
1284910	21932	2
1284907	21932	1
1284913	21932	2
1283750	21932	2
1283748	21932	2
1284911	21934	1
1284910	21934	1
1284912	21934	1
1284908	21934	2
1283748	21934	2
1283750	21934	1
1284909	21934	1
1284914	21934	1
1283749	21934	1
1283751	21934	1
1284913	21934	2
1284907	21934	1
1283751	21935	2
1284910	21935	1
1283750	21935	1
1284909	21935	1
1283749	21935	1
1284912	21935	1
1284913	21935	2
1284911	21935	1
1284914	21935	1
1284907	21935	1
1283748	21935	2
1284908	21935	2
1284908	21936	1
1284907	21936	1
1283750	21936	2
1284912	21936	2
1283748	21936	1
1284909	21936	2
1284914	21936	2
1284913	21936	1
1283749	21936	2
1284911	21936	2
1284910	21936	2
1283751	21936	1
1284911	21938	1
1284907	21938	1
1284913	21938	2
1284908	21938	2
1284910	21938	2
1284909	21938	2
1284912	21938	2
1283750	21938	2
1283748	21938	2
1283749	21938	2
1283751	21938	1
1284914	21938	1
1283751	21939	1
1283748	21939	2
1283750	21939	2
1284912	21939	2
1284914	21939	1
1283749	21939	2
1284908	21939	2
1284910	21939	2
1284907	21939	1
1284911	21939	2
1284909	21939	2
1284913	21939	2
1284910	21940	2
1283750	21940	2
1283749	21940	2
1284908	21940	2
1284912	21940	4
1284914	21940	1
1283751	21940	1
1284909	21940	2
1284913	21940	2
1284911	21940	2
1284907	21940	1
1283748	21940	2
1284907	21941	1
1283750	21941	1
1284910	21941	1
1284908	21941	2
1284911	21941	1
1283751	21941	1
1283749	21941	1
1284914	21941	1
1284913	21941	2
1284909	21941	1
1284912	21941	2
1283748	21941	2
1283750	21943	2
1284912	21943	2
1284910	21943	2
1283749	21943	2
1284908	21943	1
1283748	21943	1
1284907	21943	1
1284911	21943	2
1283751	21943	1
1284914	21943	2
1284913	21943	1
1284909	21943	2
1284912	21944	1
1283751	21944	1
1283749	21944	4
1284910	21944	1
1284907	21944	1
1284911	21944	1
1284913	21944	2
1283748	21944	2
1284909	21944	1
1283750	21944	1
1284908	21944	2
1284914	21944	1
1283750	21945	2
1284910	21945	1
1284911	21945	1
1284907	21945	1
1284913	21945	2
1284909	21945	1
1283748	21945	2
1283749	21945	2
1283751	21945	1
1284912	21945	1
1284908	21945	2
1284914	21945	1
1283749	21946	2
1283751	21946	1
1284908	21946	2
1284912	21946	2
1283750	21946	2
1284914	21946	1
1284909	21946	1
1283748	21946	2
1284907	21946	1
1284911	21946	1
1284910	21946	1
1284913	21946	2
1283750	21947	2
1283748	21947	1
1284913	21947	1
1284911	21947	2
1283751	21947	1
1284910	21947	2
1284908	21947	1
1284914	21947	2
1284907	21947	1
1283749	21947	2
1284909	21947	2
1284912	21947	2
1283751	21948	1
1284913	21948	2
1284914	21948	1
1284909	21948	1
1284907	21948	1
1284911	21948	2
1284910	21948	2
1284908	21948	2
1283749	21948	2
1284912	21948	2
1283750	21948	2
1283748	21948	2
1284910	21950	1
1283748	21950	2
1283749	21950	2
1284912	21950	1
1283751	21950	1
1284911	21950	1
1283750	21950	2
1284909	21950	1
1284914	21950	1
1284907	21950	1
1284913	21950	2
1284908	21950	2
1283748	21951	1
1284909	21951	2
1284908	21951	1
1283749	21951	2
1284912	21951	2
1284914	21951	2
1284907	21951	1
1284910	21951	2
1283750	21951	2
1283751	21951	1
1284913	21951	1
1284911	21951	2
1283748	21952	2
1284908	21952	2
1284909	21952	1
1284907	21952	1
1284910	21952	1
1283751	21952	2
1284911	21952	1
1283750	21952	1
1284912	21952	1
1283749	21952	1
1284913	21952	2
1284914	21952	2
1283751	21954	1
1284912	21954	2
1284911	21954	2
1284907	21954	1
1283748	21954	1
1284914	21954	2
1283750	21954	2
1284910	21954	2
1284909	21954	2
1283749	21954	2
1284908	21954	1
1284913	21954	1
1283750	21955	2
1284910	21955	2
1284908	21955	1
1284912	21955	2
1283751	21955	1
1284907	21955	1
1284913	21955	1
1284914	21955	2
1283748	21955	1
1284909	21955	2
1284911	21955	2
1283749	21955	2
1284914	21957	4
1283750	21957	4
1283748	21957	4
1284907	21957	4
1284911	21957	4
1284909	21957	4
1283751	21957	4
1284913	21957	4
1284912	21957	4
1283749	21957	4
1284908	21957	4
1284910	21957	4
1283750	21958	2
1284913	21958	1
1283748	21958	1
1284909	21958	2
1284912	21958	2
1284907	21958	1
1284910	21958	2
1284911	21958	2
1284914	21958	2
1283751	21958	1
1284908	21958	1
1283749	21958	2
1284912	21959	2
1284908	21959	2
1284909	21959	2
1284913	21959	2
1284911	21959	2
1283750	21959	2
1283748	21959	2
1284914	21959	1
1284907	21959	1
1283749	21959	2
1284910	21959	2
1283751	21959	1
1283750	21961	2
1283749	21961	2
1283751	21961	1
1284908	21961	4
1284913	21961	2
1284909	21961	2
1284910	21961	2
1284912	21961	2
1284914	21961	1
1283748	21961	2
1284907	21961	1
1284911	21961	2
1284910	21962	2
1284909	21962	2
1283751	21962	1
1284913	21962	1
1284908	21962	1
1283749	21962	2
1283750	21962	2
1283748	21962	1
1284907	21962	1
1284914	21962	2
1284911	21962	2
1284912	21962	2
1284914	21963	1
1283750	21963	2
1284911	21963	2
1284909	21963	2
1283749	21963	2
1284907	21963	1
1284913	21963	2
1284912	21963	2
1284910	21963	2
1283751	21963	1
1283748	21963	2
1284908	21963	2
1284907	21964	1
1284911	21964	2
1283751	21964	1
1284910	21964	2
1283748	21964	2
1283750	21964	2
1284914	21964	1
1283749	21964	2
1284909	21964	1
1284913	21964	2
1284908	21964	2
1284912	21964	2
1284911	21965	1
1283748	21965	2
1284909	21965	2
1284910	21965	2
1284907	21965	1
1284914	21965	1
1284912	21965	1
1283751	21965	1
1284908	21965	2
1283749	21965	2
1284913	21965	2
1283750	21965	1
1284909	21966	1
1283751	21966	1
1284913	21966	2
1284914	21966	1
1283748	21966	2
1284910	21966	1
1283749	21966	1
1284908	21966	2
1284911	21966	1
1284907	21966	1
1284912	21966	1
1283750	21966	1
1284911	21967	1
1284909	21967	1
1284912	21967	1
1284910	21967	1
1284914	21967	1
1283749	21967	2
1283750	21967	2
1284908	21967	2
1283751	21967	1
1284913	21967	2
1283748	21967	2
1284907	21967	1
1284909	21968	2
1284914	21968	1
1283751	21968	1
1284912	21968	2
1284908	21968	2
1284910	21968	2
1283749	21968	2
1284907	21968	1
1283750	21968	2
1284913	21968	2
1283748	21968	2
1284911	21968	2
1284910	21969	1
1284909	21969	1
1284914	21969	1
1283749	21969	2
1283750	21969	1
1283748	21969	2
1284908	21969	2
1284912	21969	4
1284911	21969	1
1284913	21969	2
1283751	21969	1
1284907	21969	1
1283749	21970	1
1284910	21970	1
1284913	21970	2
1284911	21970	1
1284909	21970	1
1284908	21970	2
1283748	21970	2
1284907	21970	1
1284912	21970	1
1283751	21970	1
1283750	21970	1
1284914	21970	1
1283749	21971	2
1284913	21971	2
1283751	21971	1
1284907	21971	1
1284910	21971	2
1284911	21971	2
1284908	21971	2
1284912	21971	2
1284909	21971	1
1284914	21971	1
1283748	21971	2
1283750	21971	2
1284909	21972	1
1284907	21972	1
1284913	21972	2
1284914	21972	1
1283749	21972	2
1284910	21972	2
1283748	21972	2
1284908	21972	2
1283750	21972	1
1284912	21972	1
1284911	21972	1
1283751	21972	1
1284910	21973	2
1284908	21973	2
1284911	21973	2
1284912	21973	2
1283748	21973	2
1284913	21973	2
1283750	21973	2
1283749	21973	2
1284914	21973	1
1284909	21973	2
1284907	21973	1
1283751	21973	1
1284911	21974	1
1284907	21974	1
1284912	21974	1
1283749	21974	2
1284909	21974	1
1283750	21974	2
1284910	21974	4
1284913	21974	2
1283748	21974	2
1284914	21974	1
1284908	21974	2
1283751	21974	1
1284913	21975	2
1283749	21975	1
1284914	21975	1
1283748	21975	2
1284909	21975	1
1284912	21975	1
1283751	21975	2
1284907	21975	1
1284910	21975	1
1284911	21975	1
1284908	21975	2
1283750	21975	1
1283749	21976	2
1283748	21976	1
1284913	21976	1
1284911	21976	2
1284908	21976	1
1284910	21976	2
1283750	21976	2
1284909	21976	2
1283751	21976	1
1284907	21976	1
1284914	21976	2
1284912	21976	2
1284907	21977	1
1284909	21977	1
1283750	21977	1
1283748	21977	2
1284908	21977	2
1284911	21977	1
1284913	21977	2
1283751	21977	1
1284910	21977	1
1284912	21977	2
1283749	21977	2
1284914	21977	1
1283750	22915	2
1284913	22915	2
1284911	22915	2
1283749	22915	2
1284910	22915	2
1284907	22915	1
1284908	22915	2
1284912	22915	2
1284909	22915	2
1284914	22915	1
1283751	22915	1
1283748	22915	2
1283751	22929	1
1283748	22929	1
1284908	22929	1
1284911	22929	2
1284913	22929	1
1284912	22929	2
1283750	22929	2
1283749	22929	2
1284907	22929	1
1284914	22929	2
1284910	22929	2
1284909	22929	2
1284914	22939	2
1284908	22939	1
1284907	22939	1
1283750	22939	2
1283751	22939	2
1283748	22939	1
1284913	22939	1
1284911	22939	2
1283749	22939	2
1284909	22939	2
1284910	22939	2
1284912	22939	2
1283749	22947	2
1284909	22947	1
1283751	22947	1
1284910	22947	1
1284914	22947	1
1283750	22947	2
1283748	22947	2
1284907	22947	1
1284908	22947	2
1284913	22947	2
1284911	22947	1
1284912	22947	2
1284911	22966	2
1283748	22966	1
1284914	22966	2
1283751	22966	1
1284913	22966	1
1284910	22966	2
1284907	22966	1
1283750	22966	2
1284909	22966	2
1283749	22966	2
1284908	22966	1
1284912	22966	2
1284909	22967	1
1283749	22967	2
1284912	22967	2
1283748	22967	2
1284911	22967	2
1284913	22967	2
1284908	22967	2
1284907	22967	1
1284910	22967	2
1283751	22967	1
1283750	22967	2
1284914	22967	1
1284908	23048	1
1283749	23048	2
1283751	23048	1
1284911	23048	2
1284913	23048	1
1284909	23048	2
1284907	23048	1
1284912	23048	2
1284910	23048	2
1283748	23048	1
1283750	23048	2
1284914	23048	2
1283748	23161	2
1284910	23161	2
1284913	23161	2
1283750	23161	2
1284907	23161	1
1283751	23161	1
1284909	23161	1
1284908	23161	2
1283749	23161	2
1284912	23161	2
1284914	23161	1
1284911	23161	1
1284910	23162	1
1284907	23162	1
1284912	23162	2
1283748	23162	2
1284913	23162	2
1283751	23162	1
1284911	23162	1
1283750	23162	2
1283749	23162	2
1284909	23162	1
1284914	23162	1
1284908	23162	2
1284910	23172	2
1284911	23172	2
1284912	23172	2
1283751	23172	1
1283749	23172	2
1284909	23172	2
1284908	23172	1
1283750	23172	2
1284914	23172	2
1284913	23172	1
1284907	23172	1
1283748	23172	1
1283751	23173	1
1284907	23173	1
1284913	23173	1
1283749	23173	2
1284914	23173	2
1284908	23173	1
1283750	23173	2
1284910	23173	2
1284911	23173	2
1284912	23173	2
1284909	23173	2
1283748	23173	1
1283749	23182	2
1283751	23182	1
1284907	23182	1
1284913	23182	2
1284910	23182	2
1283748	23182	2
1284911	23182	2
1284914	23182	1
1284912	23182	2
1284908	23182	2
1284909	23182	1
1283750	23182	2
1283751	23997	1
1284907	23997	1
1284911	23997	1
1284913	23997	2
1284914	23997	1
1284908	23997	2
1283748	23997	2
1283749	23997	2
1284912	23997	1
1284910	23997	2
1283750	23997	2
1284909	23997	1
1283751	23998	1
1283750	23998	2
1284910	23998	2
1284912	23998	2
1283748	23998	2
1284908	23998	2
1284914	23998	1
1283749	23998	2
1284913	23998	2
1284911	23998	2
1284907	23998	1
1284909	23998	1
1283751	23999	1
1284909	23999	2
1283750	23999	2
1284914	23999	2
1284910	23999	2
1284913	23999	1
1284912	23999	2
1283749	23999	2
1284907	23999	1
1283748	23999	1
1284911	23999	2
1284908	23999	1
1283751	24000	2
1283750	24000	1
1284911	24000	1
1284914	24000	1
1284912	24000	1
1283749	24000	1
1284910	24000	1
1284907	24000	1
1284913	24000	2
1284908	24000	2
1283748	24000	2
1284909	24000	1
1284912	24001	1
1283748	24001	2
1283751	24001	2
1284908	24001	2
1284909	24001	1
1284907	24001	1
1284913	24001	2
1283750	24001	1
1284911	24001	1
1284910	24001	1
1283749	24001	1
1284914	24001	1
1284912	24002	2
1284909	24002	2
1284913	24002	1
1284914	24002	2
1283749	24002	2
1283748	24002	1
1284910	24002	2
1283751	24002	1
1283750	24002	2
1284907	24002	1
1284908	24002	1
1284911	24002	2
1284910	24003	1
1284907	24003	1
1284913	24003	2
1283751	24003	1
1284909	24003	1
1284911	24003	1
1283749	24003	1
1284912	24003	1
1283750	24003	1
1283748	24003	2
1284914	24003	1
1284908	24003	2
1284911	24004	2
1283751	24004	1
1283750	24004	2
1283749	24004	2
1284908	24004	1
1284914	24004	2
1283748	24004	1
1284912	24004	2
1284910	24004	2
1284907	24004	1
1284913	24004	1
1284909	24004	2
1284909	24005	2
1283750	24005	2
1283749	24005	2
1284908	24005	1
1283751	24005	1
1284912	24005	2
1283748	24005	1
1284914	24005	2
1284910	24005	2
1284913	24005	1
1284907	24005	1
1284911	24005	2
1283748	24006	2
1284914	24006	1
1284910	24006	1
1284912	24006	1
1284907	24006	1
1284908	24006	2
1284911	24006	1
1284913	24006	2
1283749	24006	1
1283751	24006	2
1284909	24006	1
1283750	24006	1
1283749	24007	2
1283750	24007	2
1284911	24007	2
1284913	24007	2
1284912	24007	2
1284910	24007	2
1284908	24007	2
1284907	24007	1
1283748	24007	2
1284914	24007	1
1283751	24007	1
1284909	24007	2
1284913	24008	1
1284908	24008	1
1283750	24008	2
1284912	24008	2
1284907	24008	1
1284909	24008	2
1283748	24008	1
1284910	24008	2
1283751	24008	1
1284911	24008	2
1283749	24008	2
1284914	24008	2
1283749	24009	2
1284914	24009	1
1283748	24009	2
1284913	24009	2
1284909	24009	2
1284911	24009	2
1284910	24009	2
1284912	24009	2
1284908	24009	2
1283750	24009	2
1284907	24009	1
1283751	24009	1
1284911	24010	2
1283750	24010	2
1284913	24010	1
1284909	24010	2
1284914	24010	2
1283751	24010	1
1283749	24010	2
1284907	24010	1
1284908	24010	1
1284912	24010	2
1283748	24010	1
1284910	24010	2
1284914	24011	2
1284910	24011	2
1284912	24011	2
1284909	24011	2
1283749	24011	2
1284913	24011	1
1284908	24011	1
1283750	24011	2
1284907	24011	1
1283748	24011	1
1284911	24011	2
1283751	24011	1
1284913	24012	2
1283750	24012	2
1284911	24012	2
1283751	24012	1
1284907	24012	1
1284910	24012	2
1284912	24012	2
1284908	24012	2
1283749	24012	2
1283748	24012	2
1284909	24012	1
1284914	24012	1
1284910	24013	2
1284909	24013	2
1283750	24013	2
1284907	24013	1
1284911	24013	2
1283748	24013	2
1284914	24013	1
1284913	24013	2
1284912	24013	2
1284908	24013	2
1283751	24013	1
1283749	24013	2
1284907	24014	1
1284912	24014	2
1284910	24014	2
1284913	24014	2
1284909	24014	1
1284914	24014	1
1284908	24014	2
1283749	24014	2
1283751	24014	1
1283748	24014	2
1284911	24014	2
1283750	24014	2
1283750	24015	2
1283751	24015	1
1284913	24015	2
1284908	24015	2
1284910	24015	1
1284907	24015	1
1284911	24015	2
1284909	24015	1
1283748	24015	2
1283749	24015	2
1284914	24015	1
1284912	24015	2
1283748	24016	2
1284911	24016	1
1284910	24016	2
1284913	24016	2
1284912	24016	1
1284908	24016	2
1283749	24016	2
1284909	24016	1
1283750	24016	2
1284914	24016	1
1284907	24016	1
1283751	24016	1
1284912	24017	2
1284907	24017	1
1283749	24017	2
1283751	24017	1
1283750	24017	2
1284910	24017	2
1284911	24017	2
1283748	24017	1
1284908	24017	1
1284914	24017	2
1284909	24017	2
1284913	24017	1
1284914	24018	2
1283750	24018	2
1284913	24018	1
1284911	24018	2
1284908	24018	1
1283748	24018	1
1283749	24018	2
1284907	24018	1
1284910	24018	2
1283751	24018	1
1284912	24018	2
1284909	24018	2
1284907	24019	1
1284911	24019	1
1284912	24019	1
1284909	24019	1
1284913	24019	2
1284908	24019	2
1283750	24019	1
1283751	24019	1
1283748	24019	2
1283749	24019	1
1284914	24019	1
1284910	24019	1
1283748	24020	1
1284911	24020	2
1283751	24020	1
1284908	24020	1
1284907	24020	1
1284910	24020	2
1284912	24020	2
1284914	24020	2
1284909	24020	2
1284913	24020	1
1283750	24020	2
1283749	24020	2
1284909	24021	2
1283749	24021	2
1283750	24021	2
1284912	24021	2
1284910	24021	2
1284908	24021	1
1283751	24021	1
1284907	24021	1
1284914	24021	2
1284913	24021	1
1284911	24021	2
1283748	24021	1
1284914	24022	2
1284913	24022	1
1283749	24022	2
1284911	24022	2
1283751	24022	1
1284910	24022	2
1284909	24022	2
1283750	24022	2
1284907	24022	1
1284908	24022	1
1283748	24022	1
1284912	24022	2
1283750	24023	2
1284908	24023	2
1284907	24023	1
1284912	24023	2
1284911	24023	1
1284913	24023	2
1284910	24023	1
1283748	24023	2
1283749	24023	2
1283751	24023	1
1284909	24023	1
1284914	24023	1
1284913	24024	1
1283751	24024	1
1284909	24024	2
1284908	24024	1
1284912	24024	2
1284907	24024	1
1284914	24024	2
1283748	24024	1
1284910	24024	2
1284911	24024	2
1283749	24024	2
1283750	24024	2
1283749	24025	1
1284911	24025	1
1284910	24025	1
1284907	24025	1
1283750	24025	1
1284909	24025	1
1283748	24025	2
1284914	24025	1
1284908	24025	2
1284912	24025	1
1283751	24025	1
1284913	24025	2
1284914	24026	1
1284910	24026	1
1284908	24026	2
1284907	24026	1
1283751	24026	1
1284911	24026	1
1283749	24026	1
1283750	24026	1
1284913	24026	2
1284912	24026	1
1284909	24026	1
1283748	24026	2
1283748	24027	1
1284909	24027	2
1284913	24027	1
1283750	24027	2
1284908	24027	1
1283749	24027	2
1284914	24027	2
1284911	24027	2
1283751	24027	1
1284907	24027	1
1284910	24027	2
1284912	24027	2
1284911	24028	1
1283751	24028	1
1284907	24028	1
1284908	24028	2
1284909	24028	1
1284914	24028	1
1284910	24028	2
1284912	24028	2
1284913	24028	2
1283750	24028	2
1283749	24028	2
1283748	24028	2
1283749	24029	2
1284908	24029	1
1284913	24029	1
1284909	24029	2
1284907	24029	1
1283750	24029	2
1283748	24029	1
1284914	24029	2
1284911	24029	2
1283751	24029	1
1284912	24029	2
1284910	24029	2
1283749	24030	2
1283751	24030	1
1284908	24030	1
1284907	24030	1
1284911	24030	2
1283750	24030	2
1284912	24030	2
1284909	24030	2
1284914	24030	2
1284910	24030	2
1284913	24030	1
1283748	24030	4
1283751	24031	1
1284913	24031	2
1284914	24031	1
1284907	24031	1
1283748	24031	2
1284911	24031	2
1283749	24031	2
1284912	24031	2
1284908	24031	2
1283750	24031	2
1284909	24031	2
1284910	24031	2
1284908	24032	2
1284910	24032	2
1284912	24032	2
1284909	24032	2
1283751	24032	2
1284913	24032	2
1283750	24032	2
1283749	24032	2
1284907	24032	1
1284911	24032	2
1283748	24032	2
1284914	24032	1
1283750	24033	2
1284912	24033	2
1284911	24033	2
1283748	24033	1
1284913	24033	1
1284914	24033	2
1284909	24033	2
1284910	24033	2
1283751	24033	1
1284907	24033	1
1284908	24033	1
1283749	24033	2
1283749	24034	2
1284909	24034	2
1283751	24034	1
1284914	24034	1
1284907	24034	1
1283750	24034	1
1284911	24034	2
1284913	24034	2
1284910	24034	2
1284908	24034	2
1283748	24034	2
1284912	24034	2
1284914	24035	1
1284911	24035	1
1283749	24035	1
1284913	24035	2
1283750	24035	1
1284908	24035	2
1284910	24035	1
1283748	24035	2
1284912	24035	1
1284909	24035	1
1283751	24035	2
1284907	24035	1
1284914	24036	1
1284908	24036	2
1283749	24036	2
1283750	24036	2
1284912	24036	2
1284909	24036	1
1284907	24036	1
1283751	24036	1
1284911	24036	2
1283748	24036	2
1284910	24036	2
1284913	24036	2
1284907	24037	1
1284909	24037	2
1284912	24037	2
1283748	24037	2
1284914	24037	1
1283749	24037	1
1283750	24037	2
1284908	24037	2
1284911	24037	2
1284913	24037	2
1284910	24037	1
1283751	24037	1
1284913	24038	2
1283749	24038	2
1283750	24038	2
1284912	24038	2
1284910	24038	2
1283751	24038	1
1284908	24038	2
1284907	24038	1
1283748	24038	2
1284911	24038	2
1284914	24038	2
1284909	24038	2
1284907	24039	1
1284911	24039	2
1284908	24039	2
1283748	24039	2
1283751	24039	1
1284912	24039	2
1284914	24039	1
1283749	24039	2
1284913	24039	2
1283750	24039	2
1284910	24039	1
1284909	24039	2
1283751	24040	1
1284913	24040	1
1284911	24040	2
1283749	24040	2
1284907	24040	1
1283750	24040	2
1284908	24040	1
1284910	24040	2
1283748	24040	1
1284914	24040	2
1284909	24040	2
1284912	24040	2
1284907	24041	1
1284909	24041	2
1284912	24041	2
1284913	24041	1
1284911	24041	2
1283748	24041	1
1284910	24041	2
1283749	24041	2
1284914	24041	2
1283751	24041	1
1283750	24041	2
1284908	24041	1
1283749	24042	1
1284913	24042	2
1284909	24042	1
1284911	24042	1
1283751	24042	1
1283748	24042	2
1284914	24042	1
1283750	24042	1
1284912	24042	1
1284907	24042	1
1284908	24042	2
1284910	24042	1
1284907	24043	1
1284911	24043	1
1284909	24043	1
1284910	24043	1
1284914	24043	1
1284912	24043	1
1283751	24043	1
1283750	24043	1
1284913	24043	2
1283748	24043	2
1284908	24043	2
1283749	24043	1
1283748	24044	4
1284910	24044	4
1283751	24044	4
1284913	24044	4
1284914	24044	4
1284907	24044	4
1284908	24044	4
1284909	24044	4
1283750	24044	4
1284912	24044	4
1283749	24044	4
1284911	24044	4
1284910	24045	1
1283748	24045	2
1283750	24045	1
1284913	24045	2
1284911	24045	1
1284914	24045	1
1284907	24045	1
1284909	24045	1
1284908	24045	2
1283751	24045	1
1284912	24045	1
1283749	24045	1
1284912	24046	2
1284911	24046	2
1284907	24046	1
1284914	24046	2
1283748	24046	1
1283750	24046	2
1283751	24046	1
1284913	24046	1
1283749	24046	2
1284910	24046	2
1284908	24046	1
1284909	24046	2
1284910	24047	2
1283748	24047	2
1284913	24047	2
1283750	24047	2
1284908	24047	2
1284909	24047	2
1284907	24047	1
1284914	24047	1
1283751	24047	1
1283749	24047	2
1284912	24047	2
1284911	24047	2
1283749	24048	2
1283750	24048	1
1284912	24048	2
1284913	24048	2
1283748	24048	2
1284911	24048	1
1284910	24048	2
1284914	24048	1
1284907	24048	1
1284909	24048	1
1283751	24048	1
1284908	24048	2
1284909	24049	2
1284907	24049	1
1284908	24049	4
1283748	24049	1
1284914	24049	2
1283751	24049	1
1284911	24049	2
1284910	24049	2
1284913	24049	1
1284912	24049	2
1283750	24049	2
1283749	24049	2
1284913	24050	2
1284907	24050	1
1284911	24050	1
1284912	24050	1
1284908	24050	2
1283749	24050	1
1284909	24050	1
1283750	24050	1
1283751	24050	1
1283748	24050	2
1284910	24050	1
1284914	24050	1
1283749	24051	4
1284913	24051	4
1283748	24051	4
1284908	24051	4
1284907	24051	4
1283750	24051	4
1284911	24051	4
1284914	24051	4
1284910	24051	4
1284912	24051	4
1284909	24051	4
1283751	24051	4
1283750	24052	2
1284911	24052	2
1283751	24052	1
1284912	24052	2
1283749	24052	2
1284910	24052	2
1284908	24052	1
1284913	24052	1
1283748	24052	1
1284909	24052	2
1284907	24052	1
1284914	24052	2
1284909	24053	2
1284907	24053	1
1284910	24053	2
1284908	24053	2
1283749	24053	2
1284913	24053	2
1284912	24053	4
1284911	24053	2
1283748	24053	2
1283751	24053	1
1284914	24053	4
1283750	24053	2
1284914	24054	2
1283751	24054	1
1284907	24054	1
1284909	24054	2
1284908	24054	1
1283748	24054	1
1284911	24054	2
1284912	24054	2
1283749	24054	2
1283750	24054	2
1284913	24054	1
1284910	24054	2
1284914	24055	1
1284908	24055	2
1283751	24055	2
1283749	24055	2
1284912	24055	1
1283748	24055	2
1284909	24055	1
1284907	24055	1
1283750	24055	1
1284913	24055	2
1284911	24055	1
1284910	24055	1
1284909	24056	2
1283748	24056	1
1284908	24056	1
1284914	24056	2
1283750	24056	2
1284912	24056	2
1283749	24056	2
1284913	24056	1
1283751	24056	1
1284907	24056	1
1284910	24056	2
1284911	24056	2
1283750	24057	2
1284910	24057	2
1284911	24057	2
1283751	24057	1
1283748	24057	1
1284908	24057	1
1284914	24057	2
1284913	24057	1
1284912	24057	2
1284909	24057	2
1284907	24057	1
1283749	24057	2
1284910	24058	2
1283750	24058	2
1284908	24058	2
1284913	24058	2
1284907	24058	1
1284914	24058	1
1283748	24058	2
1283751	24058	1
1284911	24058	2
1284909	24058	1
1284912	24058	2
1283749	24058	2
1284911	24059	2
1284907	24059	1
1283748	24059	1
1284913	24059	1
1284909	24059	2
1283751	24059	1
1284908	24059	1
1284910	24059	2
1284912	24059	2
1283750	24059	2
1283749	24059	2
1284914	24059	2
1284912	24060	1
1283748	24060	2
1284913	24060	2
1284914	24060	1
1284907	24060	2
1284910	24060	1
1283751	24060	2
1283749	24060	1
1284911	24060	2
1284908	24060	2
1284909	24060	1
1283750	24060	1
1283749	24061	2
1284909	24061	2
1284910	24061	2
1284907	24061	1
1283748	24061	1
1284914	24061	2
1283750	24061	2
1284912	24061	2
1283751	24061	1
1284908	24061	1
1284911	24061	2
1284913	24061	1
1283750	24062	1
1284908	24062	2
1284909	24062	1
1283748	24062	2
1283749	24062	2
1284910	24062	1
1284911	24062	1
1284914	24062	1
1283751	24062	1
1284907	24062	1
1284912	24062	1
1284913	24062	2
1283750	24063	2
1284914	24063	2
1284907	24063	1
1284908	24063	1
1283751	24063	1
1284909	24063	2
1284910	24063	2
1284913	24063	1
1284911	24063	2
1284912	24063	2
1283748	24063	1
1283749	24063	2
1283750	24064	2
1284908	24064	1
1283749	24064	2
1284910	24064	2
1284907	24064	1
1283751	24064	1
1284913	24064	1
1284909	24064	2
1284912	24064	2
1283748	24064	1
1284911	24064	2
1284914	24064	2
1283751	24065	1
1284911	24065	2
1284912	24065	2
1284908	24065	1
1284907	24065	1
1284914	24065	2
1284913	24065	1
1284910	24065	2
1283750	24065	2
1283748	24065	1
1283749	24065	2
1284909	24065	2
1283751	24066	1
1283750	24066	2
1283748	24066	1
1283749	24066	2
1284909	24066	2
1284912	24066	2
1284907	24066	1
1284914	24066	2
1284913	24066	1
1284911	24066	2
1284910	24066	2
1284908	24066	1
1283748	24067	2
1283751	24067	1
1284908	24067	2
1284909	24067	2
1284912	24067	4
1284913	24067	2
1284910	24067	2
1283750	24067	2
1283749	24067	2
1284914	24067	1
1284911	24067	2
1284907	24067	1
1284911	24068	2
1284913	24068	1
1283751	24068	1
1284908	24068	1
1283749	24068	2
1284907	24068	1
1284912	24068	2
1284910	24068	2
1283748	24068	1
1284914	24068	2
1283750	24068	2
1284909	24068	2
1284913	24069	2
1283748	24069	2
1284911	24069	1
1284910	24069	2
1284914	24069	1
1284909	24069	2
1283751	24069	1
1283749	24069	2
1284907	24069	1
1284912	24069	4
1283750	24069	2
1284908	24069	2
1283750	24071	2
1283748	24071	2
1283749	24071	2
1284910	24071	2
1284907	24071	4
1284912	24071	2
1284911	24071	2
1284908	24071	2
1284909	24071	1
1283751	24071	1
1284908	24913	1
1284910	24913	2
1284909	24913	2
1283751	24913	1
1283750	24913	2
1284907	24913	1
1284911	24913	2
1283748	24913	1
1284913	24913	1
1284912	24913	2
1284914	24913	2
1283749	24913	2
\.


--
-- Data for Name: ls_body; Type: TABLE DATA; Schema: public; Owner: legiscan_api
--

COPY public.ls_body (body_id, state_id, role_id, body_abbr, body_short, body_name, body_role_abbr, body_role_name) FROM stdin;
1	48	1	H	House	House of Delegates	Del	Delegate
2	48	2	S	Senate	Senate	Sen	Senator
3	38	1	H	House	House of Representatives	Rep	Representative
4	38	2	S	Senate	Senate	Sen	Senator
5	35	1	H	House	House of Representatives	Rep	Representative
6	35	2	S	Senate	Senate	Sen	Senator
7	46	1	H	House	House of Delegates	Del	Delegate
8	46	2	S	Senate	Senate	Sen	Senator
11	1	1	H	House	House of Representatives	Rep	Representative
12	1	2	S	Senate	Senate	Sen	Senator
13	2	1	H	House	House of Representatives	Rep	Representative
14	2	2	S	Senate	Senate	Sen	Senator
15	3	1	H	House	House of Representatives	Rep	Representative
16	3	2	S	Senate	Senate	Sen	Senator
17	4	1	H	House	House of Representatives	Rep	Representative
18	4	2	S	Senate	Senate	Sen	Senator
19	5	1	A	Assembly	State Assembly	Asm	Assemblymember
20	5	2	S	Senate	Senate	Sen	Senator
21	6	1	H	House	House of Representatives	Rep	Representative
22	6	2	S	Senate	Senate	Sen	Senator
23	7	1	H	House	House of Representatives	Rep	Representative
24	7	2	S	Senate	Senate	Sen	Senator
25	8	1	H	House	House of Representatives	Rep	Representative
26	8	2	S	Senate	Senate	Sen	Senator
27	9	1	H	House	House of Representatives	Rep	Representative
28	9	2	S	Senate	Senate	Sen	Senator
29	10	1	H	House	House of Representatives	Rep	Representative
30	10	2	S	Senate	Senate	Sen	Senator
31	11	1	H	House	House of Representatives	Rep	Representative
32	11	2	S	Senate	Senate	Sen	Senator
33	12	1	H	House	House of Representatives	Rep	Representative
34	12	2	S	Senate	Senate	Sen	Senator
35	13	1	H	House	House of Representatives	Rep	Representative
36	13	2	S	Senate	Senate	Sen	Senator
37	14	1	H	House	House of Representatives	Rep	Representative
38	14	2	S	Senate	Senate	Sen	Senator
39	15	1	H	House	House of Representatives	Rep	Representative
40	15	2	S	Senate	Senate	Sen	Senator
41	16	1	H	House	House of Representatives	Rep	Representative
42	16	2	S	Senate	Senate	Sen	Senator
43	17	1	H	House	House of Representatives	Rep	Representative
44	17	2	S	Senate	Senate	Sen	Senator
45	18	1	H	House	House of Representatives	Rep	Representative
46	18	2	S	Senate	Senate	Sen	Senator
47	19	1	H	House	House of Representatives	Rep	Representative
48	19	2	S	Senate	Senate	Sen	Senator
49	20	1	H	House	House of Delegates	Del	Delegate
50	20	2	S	Senate	Senate	Sen	Senator
51	21	1	H	House	House of Representatives	Rep	Representative
52	21	2	S	Senate	Senate	Sen	Senator
53	22	1	H	House	House of Representatives	Rep	Representative
54	22	2	S	Senate	Senate	Sen	Senator
55	23	1	H	House	House of Representatives	Rep	Representative
56	23	2	S	Senate	Senate	Sen	Senator
57	24	1	H	House	House of Representatives	Rep	Representative
58	24	2	S	Senate	Senate	Sen	Senator
59	25	1	H	House	House of Representatives	Rep	Representative
60	25	2	S	Senate	Senate	Sen	Senator
61	26	1	H	House	House of Representatives	Rep	Representative
62	26	2	S	Senate	Senate	Sen	Senator
64	27	2	L	Legislature	Legislature	Sen	Senator
65	28	1	A	Assembly	Assembly	Rep	Representative
66	28	2	S	Senate	Senate	Sen	Senator
67	29	1	H	House	House of Representatives	Rep	Representative
68	29	2	S	Senate	Senate	Sen	Senator
69	30	1	A	Assembly	General Assembly	Rep	Representative
70	30	2	S	Senate	Senate	Sen	Senator
71	31	1	H	House	House of Representatives	Rep	Representative
72	31	2	S	Senate	Senate	Sen	Senator
73	32	1	A	Assembly	Assembly	Asm	Assemblymember
74	32	2	S	Senate	Senate	Sen	Senator
75	33	1	H	House	House of Representatives	Rep	Representative
76	33	2	S	Senate	Senate	Sen	Senator
77	34	1	H	House	House of Representatives	Rep	Representative
78	34	2	S	Senate	Senate	Sen	Senator
79	36	1	H	House	House of Representatives	Rep	Representative
80	36	2	S	Senate	Senate	Sen	Senator
81	37	1	H	House	House of Representatives	Rep	Representative
82	37	2	S	Senate	Senate	Sen	Senator
83	39	1	H	House	House of Representatives	Rep	Representative
84	39	2	S	Senate	Senate	Sen	Senator
85	40	1	H	House	House of Representatives	Rep	Representative
86	40	2	S	Senate	Senate	Sen	Senator
87	41	1	H	House	House of Representatives	Rep	Representative
88	41	2	S	Senate	Senate	Sen	Senator
89	42	1	H	House	House of Representatives	Rep	Representative
90	42	2	S	Senate	Senate	Sen	Senator
91	43	1	H	House	House of Representatives	Rep	Representative
92	43	2	S	Senate	Senate	Sen	Senator
93	44	1	H	House	House of Representatives	Rep	Representative
94	44	2	S	Senate	Senate	Sen	Senator
95	45	1	H	House	House of Representatives	Rep	Representative
96	45	2	S	Senate	Senate	Sen	Senator
97	47	1	H	House	House of Representatives	Rep	Representative
98	47	2	S	Senate	Senate	Sen	Senator
99	49	1	A	House	State Assembly	Rep	Representative
100	49	2	S	Senate	Senate	Sen	Senator
101	50	1	H	House	House of Representatives	Rep	Representative
102	50	2	S	Senate	Senate	Sen	Senator
103	21	3	J	Joint	Joint Conference	Jnt	Joint
106	49	3	J	Joint	Joint Conference	Jnt	Joint
107	39	3	J	Joint	Joint Conference	Jnt	Joint
108	7	3	J	Joint	Joint Conference	Jnt	Joint
109	16	3	J	Joint	Joint Conference	Jnt	Joint
110	34	3	J	Joint	Joint Conference	Jnt	Joint
111	4	3	J	Joint	Joint Conference	Jnt	Joint
112	50	3	J	Joint	Joint Conference	Jnt	Joint
113	8	3	J	Joint	Joint Conference	Jnt	Joint
114	52	1	H	House	House of Representatives	Rep	Representative
115	52	2	S	Senate	Senate	Sen	Senator
116	51	2	C	Council	City Council	Cnc	Councilmember
117	36	3	J	Joint	Joint Conference	Jnt	Joint
118	37	3	J	Joint	Joint Conference	Jnt	Joint
119	19	3	J	Joint	Joint Conference	Jnt	Joint
120	26	3	J	Joint	Joint Conference	Jnt	Joint
121	42	3	J	Joint	Joint Conference	Jnt	Joint
122	25	3	J	Joint	Joint Conference	Jnt	Joint
123	52	3	J	Joint	Joint Conference	Jnt	Joint
124	6	3	J	Joint	Joint Conference	Jnt	Joint
125	15	3	J	Joint	Joint Conference	Jnt	Joint
126	20	3	J	Joint	Joint Conference	Jnt	Joint
127	41	3	J	Joint	Joint Conference	Jnt	Joint
\.


--
-- Data for Name: ls_committee; Type: TABLE DATA; Schema: public; Owner: legiscan_api
--

COPY public.ls_committee (committee_id, committee_body_id, committee_name) FROM stdin;
2310	114	Natural Resources
2550	114	Subcommittee on Coast Guard and Maritime Transportation
4010	114	Subcommittee on Economic Development, Public Buildings, and Emergency Management
2526	114	Subcommittee on Highways and Transit
2527	114	Subcommittee on Railroads, Pipelines, and Hazardous Materials
2551	114	Subcommittee on Water Resources and Environment
4858	114	Subcommittee on Energy, Climate and Grid Security
2309	114	Judiciary
2328	115	Health, Education, Labor, And Pensions
2301	114	Education And The Workforce
2302	114	Energy And Commerce
2355	114	Subcommittee on Health
3681	114	Subcommittee on Cybersecurity and Infrastructure Protection
2307	114	Administration
2324	115	Energy And Natural Resources
2317	114	Ways And Means
4692	114	Oversight and Accountability
4882	114	Subcommittee on Border Security and Enforcement
2306	114	Homeland Security
2597	114	Subcommittee on Disability Assistance and Memorial Affairs
2316	114	Veterans' Affairs
2358	114	Subcommittee on Communications and Technology
2305	114	Foreign Affairs
4883	114	Subcommittee on Counterterrorism, Law Enforcement, and Intelligence
2304	114	Financial Services
4859	114	Subcommittee on Environment, Manufacturing, and Critical Minerals
4837	114	Water, Wildlife, and Fisheries
3359	114	Subcommittee on Federal Lands
2367	114	Subcommittee on Energy and Mineral Resources
2313	114	Science, Space, And Technology
2549	114	Subcommittee on Aviation
2315	114	Transportation And Infrastructure
4804	114	Subcommittee on Commodity Markets, Digital Assets, and Rural Development
2297	114	Agriculture
2300	114	Budget
4836	114	Indian and Insular Affairs
4894	114	Subcommittee on Environment, Manufacturing, and Critical Materials
4016	114	Subcommittee on Transportation and Maritime Security
2299	114	Armed Services
2329	115	Homeland Security And Governmental Affairs
2298	114	Appropriations
4805	114	Subcommittee on Forestry
4884	114	Subcommittee on Oversight, Investigations, and Accountability
2631	114	Subcommittee on Oversight and Investigations
4811	114	Subcommittee on Nutrition, Foreign Agriculture, and Horticulture
2576	114	Subcommittee on Livestock, Dairy, and Poultry
4782	114	Subcommittee on Innovation, Data, and Commerce
2598	114	Subcommittee on Economic Opportunity
4793	114	Subcommittee on the National Security Agency and Cyber
2312	114	Rules
4885	114	Subcommittee on Emergency Management and Technology
4792	114	Subcommittee on the National Intelligence Enterprise
2308	114	Intelligence
2323	115	Commerce, Science, And Transportation
2321	115	Banking, Housing, And Urban Affairs
2330	115	Judiciary
2333	115	Veterans' Affairs
2332	115	Small Business And Entrepreneurship
2314	114	Small Business
2327	115	Foreign Relations
2326	115	Finance
2325	115	Environment And Public Works
4835	114	Subcommittee on General Farm Commodities, Risk Management, and Credit
2335	115	Indian Affairs
4878	114	Subcommittee on the Central Intelligence Agency
4849	114	Subcommittee on Conservation, Research, and Biotechnology
2319	115	Appropriations
4903	114	Subcommittee on Modernization
4902	114	Subcommittee on Defense Intelligence and Overhead Architecture
4234	114	Subcommittee on Oversight
2318	115	Agriculture, Nutrition, And Forestry
2596	114	Subcommittee on Elections
4893	114	Subcommittee on Cyber, Information Technologies, and Innovation
4564	114	Subcommittee on Intelligence and Special Operations
2361	114	Subcommittee on Military Personnel
2360	114	Subcommittee on Readiness
2617	114	Subcommittee on Seapower and Projection Forces
2583	114	Subcommittee on Strategic Forces
2616	114	Subcommittee on Tactical Air and Land Forces
2854	114	Transportation
2331	115	Rules And Administration
2320	115	Armed Services
2322	115	Budget
2565	115	Select Intelligence
2303	114	Ethics
\.


--
-- Data for Name: ls_event_type; Type: TABLE DATA; Schema: public; Owner: legiscan_api
--

COPY public.ls_event_type (event_type_id, event_type_desc) FROM stdin;
1	Hearing
2	Executive Session
3	Markup Session
\.


--
-- Data for Name: ls_ignore; Type: TABLE DATA; Schema: public; Owner: legiscan_api
--

COPY public.ls_ignore (bill_id, created) FROM stdin;
\.


--
-- Data for Name: ls_mime_type; Type: TABLE DATA; Schema: public; Owner: legiscan_api
--

COPY public.ls_mime_type (mime_id, mime_type, mime_ext, is_binary) FROM stdin;
1	text/html	html	0
2	application/pdf	pdf	1
3	application/wordperfect	wpd	1
4	application/msword	doc	1
5	application/rtf	rtf	1
6	application/vnd.openxmlformats-officedocument.wordprocessingml.document	docx	1
7	application/vnd.ms-excel	xls	1
8	application/vnd.openxmlformats-officedocument.spreadsheetml.sheet	xlsx	1
9	text/csv	csv	0
10	application/json	json	0
11	application/zip	zip	1
\.


--
-- Data for Name: ls_monitor; Type: TABLE DATA; Schema: public; Owner: legiscan_api
--

COPY public.ls_monitor (bill_id, stance, created) FROM stdin;
\.


--
-- Data for Name: ls_party; Type: TABLE DATA; Schema: public; Owner: legiscan_api
--

COPY public.ls_party (party_id, party_abbr, party_short, party_name) FROM stdin;
1	D	Dem	Democrat
2	R	Rep	Republican
3	I	Ind	Independent
4	G	Grn	Green Party
5	L	Lib	Libertarian
6	N	NP 	Nonpartisan
\.


--
-- Data for Name: ls_people; Type: TABLE DATA; Schema: public; Owner: legiscan_api
--

COPY public.ls_people (people_id, state_id, role_id, party_id, name, first_name, middle_name, last_name, suffix, nickname, district, committee_sponsor_id, ballotpedia, followthemoney_eid, votesmart_id, knowwho_pid, opensecrets_id, person_hash, updated, created) FROM stdin;
9209	52	1	2	Gus Bilirakis	Gus	M.	Bilirakis			HD-FL-12	0	Gus_Bilirakis	12998704	17318	193559	N00027462	nnqnietk	2024-09-29 21:51:08.645968	2024-09-29 20:54:53
9216	52	1	2	Robert Latta	Robert	E.	Latta			HD-OH-5	0	Bob_Latta	3428798	9926	209172	N00012233	lkizgzxc	2024-09-29 21:51:08.667686	2024-09-29 20:54:53
9217	52	1	2	Tom McClintock	Tom		McClintock			HD-CA-5	0	Tom_McClintock	2481759	9715	193067	N00006863	gnqvmela	2024-09-29 21:51:08.674829	2024-09-29 20:54:53
9273	52	1	2	Sam Graves	Sam		Graves			HD-MO-6	0	Sam_Graves	3836803	9425	195969	N00013323	qxalf223	2024-09-29 21:51:08.733587	2024-09-29 20:54:53
9274	52	1	2	Brett Guthrie	Brett		Guthrie			HD-KY-2	0	Brett_Guthrie	6573540	18829	194385	N00029675	e9i9kjv8	2024-09-29 21:51:08.740392	2024-09-29 20:54:53
9329	52	1	2	Glenn Thompson	Glenn		Thompson			HD-PA-15	0	Glenn_Thompson_(Pennsylvania)	4811486	24046	267269	N00029736	s48rqguv	2024-09-29 21:51:08.790835	2024-09-29 20:54:53
9346	52	1	2	Robert Aderholt	Robert	B.	Aderholt			HD-AL-4	0	Robert_Aderholt	6307650	441	158703	N00003028	qg8ps5s1	2024-09-29 21:51:08.820783	2024-09-29 20:54:53
9381	52	1	2	Harold Rogers	Harold		Rogers			HD-KY-5	0	Hal_Rogers	17657470	26875	158866	N00003473	ms77q5ej	2024-09-29 21:51:08.856737	2024-09-29 20:54:53
9384	52	1	2	Steve Scalise	Steve		Scalise			HD-LA-1	0	Steve_Scalise	6627583	9026	194976	N00009660	lc8gvmwa	2024-09-29 21:51:08.863795	2024-09-29 20:54:53
11049	52	1	2	Jeff Duncan	Jeff		Duncan			HD-SC-3	0	Jeff_Duncan_(South_Carolina)	8045191	47967	213970	N00030752	tzdxxeto	2024-09-29 21:51:08.899124	2024-09-29 20:54:53
11077	52	1	2	Tim Walberg	Tim		Walberg			HD-MI-5	0	Tim_Walberg	200642	8618	248304	N00026368	t1xxilhf	2024-09-29 21:51:08.927938	2024-09-29 20:54:53
14084	52	1	2	Richard Hudson	Richard		Hudson			HD-NC-9	0	Richard_Hudson	6611759	136448	161542	N00033630	m78r4asr	2024-09-29 21:51:09.068167	2024-09-29 20:54:53
14922	52	1	2	Randy Weber	Randy	K.	Weber	Sr.		HD-TX-14	0	Randy_Weber	13006857	102026	269711	N00033539	m6il9679	2024-09-29 21:51:09.165934	2024-09-29 20:54:53
16447	52	1	2	Rick Allen	Rick	W.	Allen			HD-GA-12	0	Rick_Allen	6939101	136062	378450	N00032240	gvpp7oqw	2024-09-29 21:51:09.376484	2024-09-29 20:54:53
16454	52	1	2	Earl Carter	Earl	L.	Carter		Buddy	HD-GA-1	0	Earl_%22Buddy%22_Carter	6806386	32085	228474	N00035346	8v83hjk6	2024-09-29 21:51:09.407196	2024-09-29 20:54:53
16477	52	1	2	Elise Stefanik	Elise		Stefanik			HD-NY-21	0	Elise_Stefanik	21236694	152539	247560	N00035523	zuh8egxj	2024-09-29 21:51:09.473857	2024-09-29 20:54:53
16480	52	1	2	Bruce Westerman	Bruce		Westerman			HD-AR-4	0	Bruce_Westerman	6682617	119120	290802	N00035527	zu2wct93	2024-09-29 21:51:09.481369	2024-09-29 20:54:53
16483	52	1	2	Ryan Zinke	Ryan		Zinke			HD-MT-1	0	Ryan_Zinke	6675530	104073	271177	N00035616	krllaano	2024-09-29 21:51:09.49181	2024-09-29 20:54:53
16490	52	1	2	Gary Palmer	Gary	J.	Palmer			HD-AL-6	0	Gary_Palmer	22027757	146274	475776	N00035691	2tdlpmkt	2024-09-29 21:51:09.527978	2024-09-29 20:54:53
16503	52	1	2	Garret Graves	Garret		Graves			HD-LA-6	0	Garret_Graves	26395838	155424	160828	N00036135	4z13x8m3	2024-09-29 21:51:09.594892	2024-09-29 20:54:53
17717	52	1	2	Darin LaHood	Darin		LaHood			HD-IL-16	0	Darin_LaHood	2782492	128760	333096	N00037031	59iwww1n	2024-09-29 21:51:09.6241	2024-09-29 20:54:53
18300	52	1	2	Neal Dunn	Neal	P.	Dunn			HD-FL-2	0	Neal_Dunn	117671	166297	547694	N00037442	pzu9xprp	2024-09-29 21:51:09.722865	2024-09-29 20:54:53
18303	52	1	2	Drew Ferguson	Drew		Ferguson	IV		HD-GA-3	0	Drew_Ferguson	7259444	168132	603326	N00039090	yj5aoa7r	2024-09-29 21:51:09.738324	2024-09-29 20:54:53
18335	52	1	2	Claudia Tenney	Claudia		Tenney			HD-NY-24	0	Claudia_Tenney	4644381	127668	216162	N00036351	xaopd1td	2024-09-29 21:51:09.879529	2024-09-29 20:54:53
19436	52	1	2	John Curtis	John		Curtis			HD-UT-3	0	John_Curtis_(Utah)	6444263	123390	626323	N00041221	4ggjmoax	2024-09-29 21:51:09.920526	2024-09-29 20:54:53
20040	52	1	2	Kelly Armstrong	Kelly		Armstrong			HD-ND	0	Kelly_Armstrong	11029961	139338	411641	N00042868	py56x01z	2024-09-29 21:51:09.987813	2024-09-29 20:54:53
20049	52	1	2	Dan Crenshaw	Dan		Crenshaw			HD-TX-2	0	Daniel_Crenshaw	44449939	177270	644108	N00042224	v02baz57	2024-09-29 21:51:10.088992	2024-09-29 20:54:53
20076	52	1	2	John Joyce	John		Joyce			HD-PA-13	0	John_Joyce_(Pennsylvania)	44955073	178911	659206	N00043242	yfzzetnh	2024-09-29 21:51:10.228255	2024-09-29 20:54:53
20083	52	1	2	Dan Meuser	Dan		Meuser			HD-PA-9	0	Dan_Meuser	4671601	102438	331999	N00029416	tog1c8nl	2024-09-29 21:51:10.261542	2024-09-29 20:54:53
20092	52	1	2	Gregory Pence	Gregory	J.	Pence			HD-IN-6	0	Greg_Pence	44044678	177876	640272	N00041956	eazmksby	2024-09-29 21:51:10.315857	2024-09-29 20:54:53
20114	52	1	2	William Timmons	William	R.	Timmons	IV		HD-SC-4	0	William_Timmons	20742278	168923	575426	N00042715	sbb50n88	2024-09-29 21:51:10.443781	2024-09-29 20:54:53
21927	52	1	2	Lauren Boebert	Lauren		Boebert			HD-CO-3	0	Lauren_Boebert	19528829	191290	724132	N00045974	h42uqcqf	2024-09-29 21:51:10.586534	2024-09-29 20:54:53
21928	52	1	2	Kat Cammack	Kat		Cammack			HD-FL-3	0	Kat_Cammack	49284296	191306	447426	N00045978	6aoc44nq	2024-09-29 21:51:10.593404	2024-09-29 20:54:53
21940	52	1	2	Mariannette Miller-Meeks	Mariannette	J.	Miller-Meeks			HD-IA-1	0	Mariannette_Miller-Meeks	6022032	103294	267080	N00029495	li3dutka	2024-09-29 21:51:10.672708	2024-09-29 20:54:53
21941	52	1	2	Mary Miller	Mary		Miller			HD-IL-15	0	Mary_Miller_(Illinois)	48161308	187988	721413	N00045703	meparsvp	2024-09-29 21:51:10.680561	2024-09-29 20:54:53
21945	52	1	2	Jacob Laturner	Jacob		Laturner		Jack	HD-KS-2	0	Jacob_LaTurner	6677579	107024	298236	N00044232	dtze58v2	2024-09-29 21:51:10.70412	2024-09-29 20:54:53
21963	52	1	2	Stephanie Bice	Stephanie		Bice			HD-OK-5	0	Stephanie_Bice	23442515	152294	495403	N00044579	4l5vd66s	2024-09-29 21:51:10.810669	2024-09-29 20:54:53
21971	52	1	2	August Pfluger	August	Lee	Pfluger	II		HD-TX-11	0	August_Pfluger	48161883	188165	717802	N00045421	a4hz6x9i	2024-09-29 21:51:10.867626	2024-09-29 20:54:53
21974	52	1	2	Burgess Owens	Burgess		Owens			HD-UT-4	0	Burgess_Owens	24352095	191166	722306	N00045812	ds1jt8in	2024-09-29 21:51:10.890588	2024-09-29 20:54:53
22915	52	1	2	Julia Letlow	Julia	Janelle	Letlow			HD-LA-5	0	Julia_Letlow	52851959	195745	768497	N00047972	9al4kovy	2024-09-29 21:51:10.919473	2024-09-29 20:54:53
22967	52	1	2	Mike Carey	Mike		Carey			HD-OH-15	0	Mike_Carey_(Ohio)	12101236	196349	776441	N00048568	luj8q7rc	2024-09-29 21:51:10.956696	2024-09-29 20:54:53
23997	52	1	2	Mark Alford	Mark		Alford			HD-MO-4	0	Mark_Alford	0	205858	0	         	5z7epvoj	2024-09-29 21:51:11.00828	2024-09-29 20:54:53
24007	52	1	2	Juan Ciscomani	Juan		Ciscomani			HD-AZ-6	0	Juan_Ciscomani	0	106728	0	         	2lohiw3j	2024-09-29 21:51:11.080836	2024-09-29 20:54:53
24012	52	1	2	Monica De La Cruz	Monica		De La Cruz			HD-TX-15	0	Monica_De_La_Cruz	0	188292	0	         	mnp2k03h	2024-09-29 21:51:11.117234	2024-09-29 20:54:53
24026	52	1	2	Harriet Hageman	Harriet	M.	Hageman			HD-WY	0	Harriet_Hageman	0	182961	0	         	jebw9c7u	2024-09-29 21:51:11.21917	2024-09-29 20:54:53
24039	52	1	2	Nicholas Langworthy	Nicholas	A.	Langworthy			HD-NY-23	0	Nicholas_A._Langworthy	0	208663	0	         	a7p72wxh	2024-09-29 21:51:11.317274	2024-09-29 20:54:53
24069	52	1	2	Brandon Williams	Brandon		Williams			HD-NY-22	0	Brandon_Williams_(New_York)	0	206001	0	         	psvt3lju	2024-09-29 21:51:11.554335	2024-09-29 20:54:53
8955	52	1	1	Nydia Velazquez	Nydia	M.	Velazquez			HD-NY-7	0	Nydia_Velazquez	17658223	26975	158981	N00001102	zy55u68d	2024-09-29 21:51:08.161448	2024-09-29 20:55:51
8957	52	1	1	Frank Pallone	Frank		Pallone	Jr.		HD-NJ-6	0	Frank_Pallone	17658803	26951	158957	N00000781	0lt6ddgr	2024-09-29 21:51:08.169212	2024-09-29 20:55:51
9193	52	1	2	Cathy McMorris Rodgers	Cathy		McMorris Rodgers			HD-WA-5	0	Cathy_McMorris_Rodgers	2941046	3217	199779	N00026314	4p9iymg5	2024-09-29 21:51:08.61735	2024-09-29 20:54:53
8964	52	1	1	Gerald Connolly	Gerald	E.	Connolly		Gerry	HD-VA-11	0	Gerald_Connolly	16577898	95078	267105	N00029891	2drw2yg6	2024-09-29 21:51:08.183908	2024-09-29 20:55:51
8965	52	1	1	Henry Cuellar	Henry		Cuellar			HD-TX-28	0	Henry_Cuellar	6443275	5486	199164	N00024978	ykjgp489	2024-09-29 21:51:08.191474	2024-09-29 20:55:51
8967	52	1	1	Diana DeGette	Diana		DeGette			HD-CO-1	0	Diana_DeGette	6006202	561	158770	N00006134	klyveg3n	2024-09-29 21:51:08.198939	2024-09-29 20:55:51
8971	52	1	1	Anna Eshoo	Anna	G.	Eshoo			HD-CA-16	0	Anna_Eshoo	8050793	26741	158731	N00007335	q2r4ba8v	2024-09-29 21:51:08.20636	2024-09-29 20:55:51
8972	52	1	1	Bill Foster	Bill		Foster			HD-IL-11	0	Bill_Foster	16623751	101632	263138	N00029139	iojagoko	2024-09-29 21:51:08.213584	2024-09-29 20:55:51
8976	52	1	1	Henry Johnson	Henry	C.	Johnson	Jr.	Hank	HD-GA-4	0	Hank_Johnson	17658662	68070	248293	N00027848	rffp6oz3	2024-09-29 21:51:08.221277	2024-09-29 20:55:51
8983	52	1	1	Doris Matsui	Doris	O.	Matsui			HD-CA-7	0	Doris_Matsui	17658638	28593	232639	N00027459	4guocnsd	2024-09-29 21:51:08.228416	2024-09-29 20:55:51
8987	52	1	1	Bill Pascrell	Bill		Pascrell	Jr.		HD-NJ-9	0	Bill_Pascrell	16580040	478	158959	N00000751	1narqjxv	2024-09-29 21:51:08.235931	2024-09-29 20:55:51
8988	52	1	1	Janice Schakowsky	Janice	D.	Schakowsky			HD-IL-9	0	Jan_Schakowsky	6419995	6387	158836	N00004724	2vo8uaxr	2024-09-29 21:51:08.243036	2024-09-29 20:55:51
8989	52	1	1	Brad Sherman	Brad		Sherman			HD-CA-32	0	Brad_Sherman	369166	142	158741	N00006897	jzmzq7nk	2024-09-29 21:51:08.250118	2024-09-29 20:55:51
8995	52	1	1	Debbie Wasserman Schultz	Debbie		Wasserman Schultz			HD-FL-25	0	Debbie_Wasserman_Schultz	704716	24301	226499	N00026106	ugd19v5h	2024-09-29 21:51:08.257996	2024-09-29 20:55:51
9010	52	1	1	Earl Blumenauer	Earl		Blumenauer			HD-OR-3	0	Earl_Blumenauer	4977792	367	159028	N00007727	wwcneni0	2024-09-29 21:51:08.265162	2024-09-29 20:55:51
9019	52	1	1	Andre Carson	Andre		Carson			HD-IN-7	0	Andr%C3%A9_Carson	17658782	84917	263260	N00029513	lcudj1xk	2024-09-29 21:51:08.272093	2024-09-29 20:55:51
9021	52	1	1	Yvette Clarke	Yvette	D.	Clarke			HD-NY-9	0	Yvette_Clarke	5418023	44741	248335	N00026961	qs5uninn	2024-09-29 21:51:08.279302	2024-09-29 20:55:51
9023	52	1	1	Emanuel Cleaver	Emanuel		Cleaver			HD-MO-5	0	Emanuel_Cleaver	4396432	39507	226522	N00026790	6f2n6oig	2024-09-29 21:51:08.286524	2024-09-29 20:55:51
9024	52	1	1	James Clyburn	James	E.	Clyburn			HD-SC-6	0	James_Clyburn	5019671	27066	159060	N00002408	ria848mh	2024-09-29 21:51:08.293632	2024-09-29 20:55:51
9025	52	1	1	Steve Cohen	Steve		Cohen			HD-TN-9	0	Steve_Hobbs,_Missouri_Representative	6442808	24340	198993	N00003225	0flzaozy	2024-09-29 21:51:08.301144	2024-09-29 20:55:51
9029	52	1	1	Joe Courtney	Joe		Courtney			HD-CT-2	0	Joe_Courtney	7236851	30333	248833	N00024842	2qvf13k9	2024-09-29 21:51:08.308056	2024-09-29 20:55:51
9032	52	1	1	Danny Davis	Danny	K.	Davis			HD-IL-7	0	Danny_K._Davis	16565454	233	158834	N00004884	fem2kor1	2024-09-29 21:51:08.315317	2024-09-29 20:55:51
9035	52	1	1	Rosa DeLauro	Rosa	L.	DeLauro			HD-CT-3	0	Rosa_DeLauro	5349073	26788	158778	N00000615	g25cpbse	2024-09-29 21:51:08.322292	2024-09-29 20:55:51
9037	52	1	1	Lloyd Doggett	Lloyd		Doggett			HD-TX-37	0	Lloyd_Doggett	17658622	21689	159080	N00006023	x8u7gn7k	2024-09-29 21:51:08.329829	2024-09-29 20:55:51
9050	52	1	1	Al Green	Al		Green			HD-TX-9	0	Al_Green_(Texas)	11567524	49680	226547	N00026686	mk25m4b8	2024-09-29 21:51:08.337343	2024-09-29 20:55:51
9051	52	1	1	Raul Grijalva	Raul	M.	Grijalva			HD-AZ-7	0	Raul_Grijalva	17657668	28253	211719	N00025284	76g36sia	2024-09-29 21:51:08.34444	2024-09-29 20:55:51
9058	52	1	1	Brian Higgins	Brian		Higgins			HD-NY-26	0	Brian_Higgins	4689854	23127	197797	N00027060	klc5fkcs	2024-09-29 21:51:08.354075	2024-09-29 20:55:51
9059	52	1	1	James Himes	James	A.	Himes			HD-CT-4	0	Jim_Himes	14257522	106744	266938	N00029070	2l42ff6o	2024-09-29 21:51:08.362499	2024-09-29 20:55:51
9065	52	1	1	Steny Hoyer	Steny	H.	Hoyer			HD-MD-5	0	Steny_Hoyer	5702081	26890	158889	N00001821	2on8y3dn	2024-09-29 21:51:08.373104	2024-09-29 20:55:51
9070	52	1	1	Marcy Kaptur	Marcy		Kaptur			HD-OH-9	0	Marcy_Kaptur	3503114	27016	159009	N00003522	w9iuhiap	2024-09-29 21:51:08.390889	2024-09-29 20:55:51
9076	52	1	1	Rick Larsen	Rick		Larsen			HD-WA-2	0	Rick_Larsen	17657616	56231	124078	N00009759	31giymui	2024-09-29 21:51:08.398726	2024-09-29 20:55:51
9077	52	1	1	John Larson	John	B.	Larson			HD-CT-1	0	John_Larson_(Connecticut)	16565470	17188	158776	N00000575	3lsd7um3	2024-09-29 21:51:08.405645	2024-09-29 20:55:51
9078	52	1	1	Barbara Lee	Barbara		Lee			HD-CA-12	0	Barbara_Lee_(California)	1263932	8315	158726	N00008046	npbfeqjs	2024-09-29 21:51:08.412541	2024-09-29 20:55:51
9083	52	1	1	Zoe Lofgren	Zoe		Lofgren			HD-CA-18	0	Zoe_Lofgren	761620	21899	158733	N00007479	t7m0s2ft	2024-09-29 21:51:08.420242	2024-09-29 20:55:51
9085	52	1	1	Stephen Lynch	Stephen	F.	Lynch			HD-MA-8	0	Stephen_Lynch	1819740	4844	195035	N00013855	6nc2hqqs	2024-09-29 21:51:08.427509	2024-09-29 20:55:51
9089	52	1	1	Betty McCollum	Betty		McCollum			HD-MN-4	0	Betty_McCollum	6428407	3812	195933	N00012942	awr612hp	2024-09-29 21:51:08.43505	2024-09-29 20:55:52
9095	52	1	1	Gwen Moore	Gwen		Moore			HD-WI-4	0	Gwen_Moore	2653235	3457	199871	N00026914	dfoj059c	2024-09-29 21:51:08.442146	2024-09-29 20:55:52
9099	52	1	1	Jerrold Nadler	Jerrold		Nadler			HD-NY-12	0	Jerrold_Nadler	17658246	26980	158977	N00000939	rwffcw9q	2024-09-29 21:51:08.450207	2024-09-29 20:55:52
9100	52	1	1	Eleanor Norton	Eleanor	Holmes	Norton			HD-DC	0	Eleanor_Holmes_Norton	18929695	775	158782	N00001692	h8rinfel	2024-09-29 21:51:08.457556	2024-09-29 20:55:52
9109	52	1	1	Chellie Pingree	Chellie		Pingree			HD-ME-1	0	Chellie_Pingree	1656640	6586	267137	N00013817	caxcxyw5	2024-09-29 21:51:08.465295	2024-09-29 20:55:52
9118	52	1	1	C.A. Ruppersberger	C.A.	Dutch	Ruppersberger			HD-MD-2	0	Dutch_Ruppersberger	17658031	36130	120144	N00025482	6pt9at2x	2024-09-29 21:51:08.472564	2024-09-29 20:55:52
9121	52	1	1	Linda Sanchez	Linda	T.	Sanchez			HD-CA-38	0	Linda_S%C3%A1nchez	17657762	29674	211684	N00024870	7ammm44v	2024-09-29 21:51:08.479844	2024-09-29 20:55:52
9123	52	1	1	John Sarbanes	John	P.	Sarbanes			HD-MD-3	0	John_Sarbanes	17658676	66575	248303	N00027751	rsmtoq6c	2024-09-29 21:51:08.487047	2024-09-29 20:55:52
9124	52	1	1	Adam Schiff	Adam	B.	Schiff			HD-CA-30	0	Adam_Schiff	15203357	9489	193010	N00009585	1r7551ta	2024-09-29 21:51:08.494049	2024-09-29 20:55:52
9126	52	1	1	David Scott	David		Scott			HD-GA-13	0	David_Scott_(Georgia)	13011507	7826	193670	N00024871	v86fk0xj	2024-09-29 21:51:08.501229	2024-09-29 20:55:52
9127	52	1	1	Robert Scott	Robert	C.	Scott		Bobby	HD-VA-3	0	Robert_Scott_(Delaware)	17658728	173269	159106	N00002147	yj5zsql5	2024-09-29 21:51:08.508389	2024-09-29 20:55:52
9137	52	1	1	Bennie Thompson	Bennie	G.	Thompson			HD-MS-2	0	Bennie_Thompson	8348996	26929	158929	N00003288	bhtcm97e	2024-09-29 21:51:08.515423	2024-09-29 20:55:52
9138	52	1	1	Mike Thompson	Mike		Thompson			HD-CA-4	0	Mike_Thompson_(California)	1952480	3564	158718	N00007419	btn7lzt9	2024-09-29 21:51:08.522498	2024-09-29 20:55:52
9140	52	1	1	Dina Titus	Dina		Titus			HD-NV-1	0	Dina_Titus	12996791	2629	197530	N00030191	tzyevmen	2024-09-29 21:51:08.529667	2024-09-29 20:55:52
9144	52	1	1	Maxine Waters	Maxine		Waters			HD-CA-43	0	Maxine_Waters	1257359	26759	158752	N00006690	ijja8k71	2024-09-29 21:51:08.536702	2024-09-29 20:55:52
9151	52	1	1	Sanford Bishop	Sanford	D.	Bishop	Jr.		HD-GA-2	0	Sanford_Bishop_Jr.	5134027	26817	158808	N00002674	1m2s0603	2024-09-29 21:51:08.543926	2024-09-29 20:55:52
9157	52	1	2	Mario Diaz-Balart	Mario		Diaz-Balart			HD-FL-26	0	Mario_Diaz-Balart	12999048	24312	193508	N00025337	nyixi862	2024-09-29 21:51:08.551241	2024-09-29 20:55:52
9160	52	1	1	James McGovern	James	P.	McGovern			HD-MA-2	0	James_J._McGovern	17658594	552	158877	N00000179	o1zhlthv	2024-09-29 21:51:08.55886	2024-09-29 20:55:52
9165	52	1	1	Gregorio Sablan	Gregorio		Sablan			HD-MP	0	Gregorio_Sablan	0	110903	274097	N00030418	gvoo8umn	2024-09-29 21:51:08.573537	2024-09-29 20:55:52
9167	52	1	1	Paul Tonko	Paul	D.	Tonko			HD-NY-20	0	Paul_Tonko	4469600	4403	197757	N00030196	aaq2jux5	2024-09-29 21:51:08.580544	2024-09-29 20:55:52
9175	52	1	2	Vern Buchanan	Vern		Buchanan			HD-FL-16	0	Vern_Buchanan	17658661	66247	250707	N00027626	gmwmkrf2	2024-09-29 21:51:08.587799	2024-09-29 20:55:52
9182	52	1	2	Kay Granger	Kay		Granger			HD-TX-12	0	Kay_Granger	17658723	334	159082	N00008799	xlecopz0	2024-09-29 21:51:08.602299	2024-09-29 20:55:52
9192	52	1	2	Michael McCaul	Michael	T.	McCaul			HD-TX-10	0	Michael_McCaul	15456789	49210	226551	N00026460	77p1skl0	2024-09-29 21:51:08.609995	2024-09-29 20:55:52
9197	52	1	2	Bill Posey	Bill		Posey			HD-FL-8	0	Bill_Posey	12998616	24280	193543	N00029662	cw1v2ewn	2024-09-29 21:51:08.62462	2024-09-29 20:55:52
9200	52	1	2	Pete Sessions	Pete		Sessions			HD-TX-17	0	Pete_Sessions	10838573	288	159075	N00005681	69y137x9	2024-09-29 21:51:08.631914	2024-09-29 20:55:52
9201	52	1	1	Adam Smith	Adam		Smith			HD-WA-9	0	Adam_Smith_(Washington)	17658734	845	159125	N00007833	76ewpko5	2024-09-29 21:51:08.638959	2024-09-29 20:55:52
9211	52	1	2	Ken Calvert	Ken		Calvert			HD-CA-41	0	Ken_Calvert	2378663	26777	158760	N00007099	lvvhvgma	2024-09-29 21:51:08.653424	2024-09-29 20:55:52
9213	52	1	2	Tom Cole	Tom		Cole			HD-OK-4	0	Tom_Cole_(Oklahoma)	14964187	46034	211693	N00025726	86i58pyg	2024-09-29 21:51:08.660621	2024-09-29 20:55:52
9220	52	1	2	Mike D. Rogers	Mike	D.	Rogers			HD-AL-3	0	Mike_Rogers_(Alabama)	6571477	5705	192661	N00024759	ahue4yxo	2024-09-29 21:51:08.682515	2024-09-29 20:55:52
9222	52	1	2	Michael Simpson	Michael	K.	Simpson			HD-ID-2	0	Michael_Simpson_(Idaho)	7913824	2917	158827	N00006263	js7du00v	2024-09-29 21:51:08.689641	2024-09-29 20:55:52
9233	52	1	1	Grace Napolitano	Grace	F.	Napolitano			HD-CA-31	0	Grace_Napolitano	774257	8393	158751	N00006789	766xm3eo	2024-09-29 21:51:08.696901	2024-09-29 20:55:52
9234	52	1	1	Judy Chu	Judy		Chu			HD-CA-28	0	Judy_Chu	1258090	16539	209456	N00030600	lvs1rvrk	2024-09-29 21:51:08.704245	2024-09-29 20:55:52
9237	52	1	2	Christopher Smith	Christopher	H.	Smith			HD-NJ-4	0	Chris_Smith_(New_Jersey)	17658186	26952	158955	N00009816	td566tn1	2024-09-29 21:51:08.712058	2024-09-29 20:55:52
9254	52	1	2	John Carter	John	R.	Carter			HD-TX-31	0	John_Carter_(Texas)	17658461	49296	211726	N00025095	qxy4osah	2024-09-29 21:51:08.719252	2024-09-29 20:55:52
9269	52	1	2	Virginia Foxx	Virginia		Foxx			HD-NC-5	0	Virginia_Foxx	6285984	6051	196515	N00026166	swa3u5tf	2024-09-29 21:51:08.726515	2024-09-29 20:55:52
9279	52	1	2	Darrell Issa	Darrell	E.	Issa			HD-CA-48	0	Darrell_Issa	61054	16553	205554	N00007017	wchtw30t	2024-09-29 21:51:08.74735	2024-09-29 20:55:52
9294	52	1	2	Frank Lucas	Frank	D.	Lucas			HD-OK-3	0	Frank_Lucas	17658609	27032	159025	N00005559	pxa5pays	2024-09-29 21:51:08.754428	2024-09-29 20:55:52
9295	52	1	2	Blaine Luetkemeyer	Blaine		Luetkemeyer			HD-MO-3	0	Blaine_Luetkemeyer	4243467	20400	196108	N00030026	ijnja6t2	2024-09-29 21:51:08.761437	2024-09-29 20:55:52
9307	52	1	1	Richard Neal	Richard	E.	Neal			HD-MA-1	0	Richard_Neal	17441075	26895	158876	N00000153	4cughglp	2024-09-29 21:51:08.768313	2024-09-29 20:55:52
9312	52	1	1	Mike Quigley	Mike		Quigley			HD-IL-5	0	Mike_Quigley	8785226	83310	277349	N00030581	pf1tkip8	2024-09-29 21:51:08.775389	2024-09-29 20:55:52
9324	52	1	2	Adrian Smith	Adrian		Smith			HD-NE-3	0	Adrian_Smith	6558263	21284	196871	N00027623	88p7q4un	2024-09-29 21:51:08.782994	2024-09-29 20:55:52
9333	52	1	2	Michael Turner	Michael	R.	Turner			HD-OH-10	0	Michael_Turner_(Ohio)	17658265	45519	211690	N00025175	ftinbgg3	2024-09-29 21:51:08.797989	2024-09-29 20:55:52
9337	52	1	2	Joe Wilson	Joe		Wilson			HD-SC-2	0	Joe_Wilson_(South_Carolina)	6644962	3985	198713	N00024809	2w1xowbw	2024-09-29 21:51:08.805769	2024-09-29 20:55:52
9340	52	1	1	Jim Costa	Jim		Costa			HD-CA-21	0	Jim_Costa	732074	3577	193005	N00026341	vgqv6s3v	2024-09-29 21:51:08.813214	2024-09-29 20:55:52
9360	52	1	1	John Garamendi	John		Garamendi			HD-CA-8	0	John_Garamendi	12997062	29664	240331	N00030856	evhmkp91	2024-09-29 21:51:08.82815	2024-09-29 20:55:52
9365	52	1	2	Jim Jordan	Jim		Jordan			HD-OH-4	0	Jim_Jordan_(Ohio)	13004893	8158	197920	N00027894	n0dre2k1	2024-09-29 21:51:08.835355	2024-09-29 20:55:52
9368	52	1	2	Doug Lamborn	Doug		Lamborn			HD-CO-5	0	Doug_Lamborn	6368620	2698	193118	N00028133	pv8v5nzy	2024-09-29 21:51:08.842452	2024-09-29 20:55:52
9372	52	1	2	Patrick McHenry	Patrick	T.	McHenry			HD-NC-10	0	Patrick_McHenry	6009425	21031	212009	N00026627	9q3ib5o9	2024-09-29 21:51:08.849909	2024-09-29 20:55:52
9389	52	1	2	Robert Wittman	Robert	J.	Wittman			HD-VA-1	0	Rob_Wittman	6666723	58133	241260	N00029459	8gue0k26	2024-09-29 21:51:08.870812	2024-09-29 20:55:52
9394	52	1	1	Nancy Pelosi	Nancy		Pelosi			HD-CA-11	0	Nancy_Pelosi	2022063	26732	158725	n00007360	i3785rxp	2024-09-29 21:51:08.878019	2024-09-29 20:55:52
11042	52	1	2	Larry Bucshon	Larry		Bucshon			HD-IN-8	0	Larry_Bucshon	7004017	120335	284631	N00031227	q6aavo7l	2024-09-29 21:51:08.885005	2024-09-29 20:55:52
11047	52	1	2	Eric Crawford	Eric	A.	Crawford		Rick	HD-AR-1	0	Rick_Crawford_(Arkansas)	17657353	119208	283914	N00030770	73ahm40c	2024-09-29 21:51:08.89212	2024-09-29 20:55:52
11054	52	1	2	Paul Gosar	Paul	A.	Gosar			HD-AZ-9	0	Paul_Gosar	8461058	123491	283933	N00030771	2v8g0j52	2024-09-29 21:51:08.906328	2024-09-29 20:55:52
11058	52	1	2	Bill Huizenga	Bill		Huizenga			HD-MI-4	0	Bill_Huizenga	6574786	38351	288017	N00030673	eom7jyq1	2024-09-29 21:51:08.9135	2024-09-29 20:55:52
11059	52	1	2	Bill Johnson	Bill		Johnson			HD-OH-6	0	Bill_Johnson_(Ohio)	17657550	120649	287357	N00032088	ckst1sva	2024-09-29 21:51:08.920428	2024-09-29 20:55:52
11099	52	1	2	Steve Womack	Steve		Womack			HD-AR-3	0	Steve_Womack	9604218	71815	285713	N00031857	wdolqnr4	2024-09-29 21:51:08.934776	2024-09-29 20:55:52
11124	52	1	2	Scott DesJarlais	Scott		DesJarlais			HD-TN-4	0	Scott_DesJarlais	16586618	123473	285129	N00030957	u7i7b4fl	2024-09-29 21:51:08.942361	2024-09-29 20:55:52
11132	52	1	2	Morgan Griffith	H. Morgan		Griffith			HD-VA-9	0	Morgan_Griffith	6276976	5148	199430	N00032029	arpp6czy	2024-09-29 21:51:08.956403	2024-09-29 20:55:52
11137	52	1	2	Mike Kelly	Mike		Kelly			HD-PA-16	0	Mike_Kelly_(Pennsylvania)	5007914	119463	286955	N00031647	vr8srqc8	2024-09-29 21:51:08.963231	2024-09-29 20:55:52
11145	52	1	2	Daniel Webster	Daniel		Webster			HD-FL-11	0	Daniel_Webster_(Florida)	13011367	24302	193483	N00026335	l2rb7t8r	2024-09-29 21:51:08.97083	2024-09-29 20:55:52
11164	52	1	2	Austin Scott	Austin		Scott			HD-GA-8	0	Austin_Scott	6805076	11812	193858	N00032457	qvy181au	2024-09-29 21:51:08.977708	2024-09-29 20:55:52
11200	52	1	1	Frederica Wilson	Frederica	S.	Wilson			HD-FL-24	0	Frederica_Wilson	12999016	17319	211856	N00030650	zm3hjkaf	2024-09-29 21:51:08.985018	2024-09-29 20:55:52
11201	52	1	1	Terri Sewell	Terri	A.	Sewell			HD-AL-7	0	Terri_Sewell	17657351	121621	283908	N00030622	wknbt2m7	2024-09-29 21:51:08.99238	2024-09-29 20:55:52
11605	52	1	2	Andy Harris	Andy		Harris			HD-MD-1	0	Andy_Harris	4600723	19157	195206	N00029147	gz4ylu49	2024-09-29 21:51:08.999523	2024-09-29 20:55:52
11606	52	1	2	David Schweikert	David		Schweikert			HD-AZ-1	0	David_Schweikert	8573431	106387	267202	N00006460	2aroxdt4	2024-09-29 21:51:09.008017	2024-09-29 20:55:52
11807	52	1	1	David Cicilline	David	N.	Cicilline			HD-RI-1	0	David_Cicilline	6441236	7349	198593	N00032019	0cn18vb4	2024-09-29 21:51:09.016632	2024-09-29 20:55:52
11867	52	1	1	William Keating	William	R.	Keating		Bill	HD-MA-9	0	Bill_Keating	17657478	4743	286684	N00031933	mcmybet0	2024-09-29 21:51:09.023814	2024-09-29 20:55:52
13318	52	1	2	Mark Amodei	Mark	E.	Amodei			HD-NV-2	0	Mark_Amodei	6596644	12537	197540	N00031177	xhxpchi7	2024-09-29 21:51:09.032123	2024-09-29 20:55:52
14026	52	1	2	Thomas Massie	Thomas		Massie			HD-KY-4	0	Thomas_Massie	9195688	132068	391510	N00034041	zz9y056y	2024-09-29 21:51:09.046717	2024-09-29 20:55:52
14071	52	1	1	Donald Payne	Donald		Payne	Jr.		HD-NJ-10	0	Donald_Payne_Jr.	17658196	26957	409583	N00034639	yqszpflr	2024-09-29 21:51:09.053878	2024-09-29 20:55:52
14082	52	1	1	Joyce Beatty	Joyce		Beatty			HD-OH-3	0	Joyce_Beatty	2954872	2427	197852	N00033904	7db3fndh	2024-09-29 21:51:09.061003	2024-09-29 20:55:52
14085	52	1	1	Grace Meng	Grace		Meng			HD-NY-6	0	Grace_Meng	4676224	69157	271828	N00034547	1jqtnj2v	2024-09-29 21:51:09.075452	2024-09-29 20:55:52
14090	52	1	1	Suzan DelBene	Suzan		DelBene			HD-WA-1	0	Suzan_DelBene	2610675	126272	284676	N00030693	asdkm81r	2024-09-29 21:51:09.082759	2024-09-29 20:55:52
14137	52	1	1	Hakeem Jeffries	Hakeem	S.	Jeffries			HD-NY-8	0	Hakeem_Jeffries	13009236	55285	250929	N00033640	rny8gmgr	2024-09-29 21:51:09.092401	2024-09-29 20:55:53
14882	52	1	1	Julia Brownley	Julia		Brownley			HD-CA-26	0	Julia_Brownley	1256839	59904	248455	N00034254	y7ptrsug	2024-09-29 21:51:09.099531	2024-09-29 20:55:53
14884	52	1	1	Matthew Cartwright	Matthew	A.	Cartwright			HD-PA-8	0	Matt_Cartwright	15013323	136236	392004	N00034128	kin1xws6	2024-09-29 21:51:09.110032	2024-09-29 20:55:53
14893	52	1	1	Lois Frankel	Lois		Frankel			HD-FL-22	0	Lois_Frankel	12998905	8102	193594	N00002893	15yl52n3	2024-09-29 21:51:09.117896	2024-09-29 20:55:53
14898	52	1	1	Jared Huffman	Jared		Huffman			HD-CA-2	0	Jared_Huffman	13008447	59849	248432	N00033030	4lcpvs6s	2024-09-29 21:51:09.127105	2024-09-29 20:55:53
14906	52	1	2	Scott Perry	Scott		Perry			HD-PA-10	0	Scott_Perry	13005805	59980	248703	N00034120	rr5rm7hf	2024-09-29 21:51:09.135449	2024-09-29 20:55:53
14916	52	1	1	Bradley Schneider	Bradley	S.	Schneider			HD-IL-10	0	Brad_Schneider	2671149	134948	378769	N00033101	mw71sc7y	2024-09-29 21:51:09.14416	2024-09-29 20:55:53
14918	52	1	2	Chris Stewart	Chris		Stewart			HD-UT-2	0	Chris_Smith_(New_Jersey)	17658507	135930	392415	N00033932	ve5gp77t	2024-09-29 21:51:09.151445	2024-09-29 20:55:53
14920	52	1	1	Juan Vargas	Juan		Vargas			HD-CA-52	0	Juan_Vargas	622640	29100	143356	N00007021	vwwni2ga	2024-09-29 21:51:09.158461	2024-09-29 20:55:53
14923	52	1	2	Brad Wenstrup	Brad	R.	Wenstrup			HD-OH-2	0	Brad_Wenstrup	2596103	135326	378835	N00033310	01ht21s1	2024-09-29 21:51:09.173546	2024-09-29 20:55:53
14924	52	1	2	Roger Williams	Roger		Williams			HD-TX-25	0	Roger_Williams_(Texas)	17658466	50112	244512	N00030602	cnqmdgob	2024-09-29 21:51:09.181078	2024-09-29 20:55:53
15051	52	1	2	Garland Barr	Garland		Barr		Andy	HD-KY-6	0	Andy_Barr	9192076	117290	284674	N00031233	hme4jiwz	2024-09-29 21:51:09.188191	2024-09-29 20:55:53
15204	52	1	1	Daniel Kildee	Daniel	T.	Kildee			HD-MI-8	0	Dan_Kildee	520771	136102	294255	N00033395	vvfjs61b	2024-09-29 21:51:09.19578	2024-09-29 20:55:53
15205	52	1	1	Ami Bera	Ami		Bera			HD-CA-6	0	Ami_Bera	12556998	120030	284011	N00030717	7nu68xqa	2024-09-29 21:51:09.202917	2024-09-29 20:55:53
15208	52	1	1	Steven Horsford	Steven	A.	Horsford			HD-NV-4	0	Steven_Horsford	13012984	44064	227658	N00033638	gn2k0q2m	2024-09-29 21:51:09.210414	2024-09-29 20:55:53
15216	52	1	1	Joaquin Castro	Joaquin		Castro			HD-TX-20	0	Joaquin_Castro	6396620	49227	212619	N00033316	2ml7kllf	2024-09-29 21:51:09.217783	2024-09-29 20:55:53
15217	52	1	1	Tony Cardenas	Tony		Cardenas			HD-CA-29	0	Tony_C%C3%A1rdenas	17657742	9754	193068	N00033373	ti9w2cwq	2024-09-29 21:51:09.225087	2024-09-29 20:55:53
15224	52	1	2	David Joyce	David		Joyce			HD-OH-14	0	David_Joyce	14885217	143052	439365	N00035007	t5ugyagd	2024-09-29 21:51:09.232131	2024-09-29 20:55:53
15226	52	1	1	Derek Kilmer	Derek		Kilmer			HD-WA-6	0	Derek_Kilmer	1230035	51516	226622	N00034453	y42rdobd	2024-09-29 21:51:09.239328	2024-09-29 20:55:53
15227	52	1	1	Ann Kuster	Ann	M.	Kuster			HD-NH-2	0	Annie_Kuster	9794994	122256	284835	N00030875	yx3y1j2l	2024-09-29 21:51:09.246257	2024-09-29 20:55:53
15228	52	1	2	Doug LaMalfa	Doug		LaMalfa			HD-CA-1	0	Doug_LaMalfa	1560957	29713	211738	N00033987	pbm46q1a	2024-09-29 21:51:09.253176	2024-09-29 20:55:53
15234	52	1	1	Mark Pocan	Mark		Pocan			HD-WI-2	0	Mark_Pocan	17658558	26238	199986	N00033549	1nzjk413	2024-09-29 21:51:09.260149	2024-09-29 20:55:53
15235	52	1	1	Scott Peters	Scott	H.	Peters			HD-CA-50	0	Scott_Peters	14148706	70351	378729	N00033591	n5lq0wml	2024-09-29 21:51:09.267454	2024-09-29 20:55:53
15236	52	1	1	Raul Ruiz	Raul		Ruiz			HD-CA-25	0	Raul_Ruiz	17657757	136407	291125	N00033510	rl5dmta8	2024-09-29 21:51:09.274405	2024-09-29 20:55:53
15238	52	1	1	Eric Swalwell	Eric		Swalwell			HD-CA-14	0	Eric_Swalwell	15742560	129529	378800	N00033508	kwz5gke3	2024-09-29 21:51:09.281372	2024-09-29 20:55:53
15239	52	1	1	Mark Takano	Mark		Takano			HD-CA-39	0	Mark_Takano	17657771	22337	378804	N00006701	cbif7qo8	2024-09-29 21:51:09.288214	2024-09-29 20:55:53
15240	52	1	2	David Valadao	David	G.	Valadao			HD-CA-22	0	David_Valadao	13008587	120200	289367	N00033367	6f67rqij	2024-09-29 21:51:09.295506	2024-09-29 20:55:53
15241	52	1	1	Marc Veasey	Marc	A.	Veasey			HD-TX-33	0	Marc_Veasey	6453720	49671	228540	N00033839	jwjl1axk	2024-09-29 21:51:09.302569	2024-09-29 20:55:53
15243	52	1	2	Ann Wagner	Ann		Wagner			HD-MO-2	0	Ann_Wagner	4493676	136083	378827	N00033106	5gbai9gz	2024-09-29 21:51:09.309659	2024-09-29 20:55:53
16022	52	1	1	Robin Kelly	Robin		Kelly			HD-IL-2	0	Robin_Kelly	2665398	33384	212680	N00035215	qfvt1amx	2024-09-29 21:51:09.316835	2024-09-29 20:55:53
16065	52	1	1	Katherine Clark	Katherine	M.	Clark			HD-MA-5	0	Katherine_Clark	20536475	35858	263010	N00035278	05q57si5	2024-09-29 21:51:09.331069	2024-09-29 20:55:53
16269	52	1	1	Donald Norcross	Donald		Norcross			HD-NJ-1	0	Donald_Norcross	6498707	116277	282657	N00036154	m7qt84fc	2024-09-29 21:51:09.35457	2024-09-29 20:55:53
16271	52	1	1	Alma Adams	Alma	S.	Adams			HD-NC-12	0	Alma_Adams	5890773	5935	196595	N00035451	jlk6q4zn	2024-09-29 21:51:09.367546	2024-09-29 20:55:53
16449	52	1	2	Brian Babin	Brian		Babin			HD-TX-36	0	Brian_Babin	11282531	360	481703	N00005736	q4j4scaf	2024-09-29 21:51:09.384625	2024-09-29 20:55:53
16452	52	1	2	Mike Bost	Mike		Bost			HD-IL-12	0	Mike_Bost	6577297	6302	194400	N00035420	dcxcla13	2024-09-29 21:51:09.392084	2024-09-29 20:55:53
16453	52	1	2	Ken Buck	Ken		Buck			HD-CO-4	0	Ken_Buck	12004621	125319	285181	N00030829	u2djua92	2024-09-29 21:51:09.399936	2024-09-29 20:55:53
16458	52	1	2	Tom Emmer	Tom		Emmer			HD-MN-6	0	Tom_Emmer	12996955	38894	227769	N00035440	3z9mh67s	2024-09-29 21:51:09.414805	2024-09-29 20:55:53
16460	52	1	2	Glenn Grothman	Glenn		Grothman			HD-WI-6	0	Glenn_Grothman	2927726	3493	199967	N00036409	ntqo7c9d	2024-09-29 21:51:09.422377	2024-09-29 20:55:53
16463	52	1	2	French Hill	French		Hill			HD-AR-2	0	French_Hill	9620575	146290	475052	N00035792	v6sesxl9	2024-09-29 21:51:09.429624	2024-09-29 20:55:53
16468	52	1	2	Barry Loudermilk	Barry		Loudermilk			HD-GA-11	0	Barry_Loudermilk	12999116	31618	228409	N00035347	gs8koi0n	2024-09-29 21:51:09.437225	2024-09-29 20:55:53
16471	52	1	2	John Moolenaar	John	R.	Moolenaar			HD-MI-2	0	John_Moolenaar	609969	37676	212920	N00036275	3mjk18or	2024-09-29 21:51:09.444464	2024-09-29 20:55:53
16472	52	1	2	Alexander Mooney	Alexander		Mooney			HD-WV-2	0	Alexander_Mooney	1280122	19114	195200	N00033814	3lki1svp	2024-09-29 21:51:09.451493	2024-09-29 20:55:53
16473	52	1	2	Dan Newhouse	Dan		Newhouse			HD-WA-4	0	Dan_Newhouse	2971537	51522	211847	N00036403	687vmrnw	2024-09-29 21:51:09.459214	2024-09-29 20:55:53
16476	52	1	2	David Rouzer	David		Rouzer			HD-NC-7	0	David_Rouzer	5876933	102964	164497	N00033527	fds8xyci	2024-09-29 21:51:09.466605	2024-09-29 20:55:53
16485	52	1	1	Bonnie Coleman	Bonnie		Watson Coleman			HD-NJ-12	0	Bonnie_Watson_Coleman	6389632	24799	362925	N00036158	lw3q4fox	2024-09-29 21:51:09.499624	2024-09-29 20:55:53
16487	52	1	1	Brendan Boyle	Brendan	F.	Boyle			HD-PA-2	0	Brendan_Boyle	13006066	47357	269627	N00035307	yd02ug7m	2024-09-29 21:51:09.507562	2024-09-29 20:55:53
16492	52	1	1	Mark DeSaulnier	Mark		DeSaulnier			HD-CA-10	0	Mark_DeSaulnier	24686	69477	248434	N00030709	c3i655ka	2024-09-29 21:51:09.535545	2024-09-29 20:55:53
16495	52	1	1	Norma Torres	Norma	J.	Torres			HD-CA-35	0	Norma_Torres	6485739	71284	267783	N00036107	uvauj2ke	2024-09-29 21:51:09.543203	2024-09-29 20:55:53
16496	52	1	1	Pete Aguilar	Pete		Aguilar			HD-CA-33	0	Pete_Aguilar	17657748	70114	397292	N00033997	u4haou2y	2024-09-29 21:51:09.550463	2024-09-29 20:55:53
16497	52	1	1	Ruben Gallego	Ruben		Gallego			HD-AZ-3	0	Ruben_Gallego	6507394	123732	293802	N00036097	mttbdtlr	2024-09-29 21:51:09.564885	2024-09-29 20:55:53
16498	52	1	1	Seth Moulton	Seth		Moulton			HD-MA-6	0	Seth_Moulton	25004670	146299	464944	N00035431	etwlc6gj	2024-09-29 21:51:09.572019	2024-09-29 20:55:53
16500	52	1	1	Ted Lieu	Ted		Lieu			HD-CA-36	0	Ted_Lieu	2451821	1516	240581	N00035825	m83u4by6	2024-09-29 21:51:09.579128	2024-09-29 20:55:53
16824	52	1	1	Stacey Plaskett	Stacey	E.	Plaskett			HD-VI	0	Stacey_Plaskett	0	155929	439826	N00035000	le3tseyc	2024-09-29 21:51:09.602523	2024-09-29 20:55:53
17510	52	1	2	Amata Radewagen	Amata	Coleman	Radewagen			HD-AS	0	Aumua_Amata_Radewagen	0	128380	439739	N00007635	tb58v807	2024-09-29 21:51:09.609928	2024-09-29 20:55:53
17704	52	1	2	Trent Kelly	Trent		Kelly			HD-MS-1	0	Trent_Kelly	29268676	156389	536266	N00037003	8hybslek	2024-09-29 21:51:09.616839	2024-09-29 20:55:53
17958	52	1	2	Warren Davidson	Warren		Davidson			HD-OH-8	0	Warren_Davidson	2882234	166760	565476	N00038767	rmzpv0s6	2024-09-29 21:51:09.631095	2024-09-29 20:55:53
17980	52	1	2	James Comer	James		Comer			HD-KY-1	0	James_Comer_Jr.	13000729	35169	205575	N00038260	75y3d29y	2024-09-29 21:51:09.638478	2024-09-29 20:55:53
17981	52	1	1	Dwight Evans	Dwight		Evans			HD-PA-3	0	Dwight_Evans	13006152	9128	198425	N00038450	12yeqz9n	2024-09-29 21:51:09.64661	2024-09-29 20:55:53
18286	52	1	2	Jody Arrington	Jody	C	Arrington			HD-TX-19	0	Jodey_Arrington	26357872	155685	555820	N00038285	w4zk2uw8	2024-09-29 21:51:09.657787	2024-09-29 20:55:53
18287	52	1	2	Don Bacon	Don		Bacon			HD-NE-2	0	Don_Bacon	32158683	166299	346086	N00037049	u4dxffng	2024-09-29 21:51:09.665398	2024-09-29 20:55:53
18288	52	1	2	Jim Banks	Jim		Banks			HD-IN-3	0	Jim_Banks_(Indiana)	2949733	116801	291462	N00037185	prykhtgd	2024-09-29 21:51:09.672749	2024-09-29 20:55:53
18289	52	1	1	Nanette Barragan	Nanette	Diaz	Barragan			HD-CA-44	0	Nanette_Barrag%C3%A1n	39707282	166270	536062	N00037019	k4hlca04	2024-09-29 21:51:09.67997	2024-09-29 20:55:53
18290	52	1	2	Jack Bergman	Jack		Bergman			HD-MI-1	0	Jack_Bergman	39849758	170172	577460	N00039533	exu0ye64	2024-09-29 21:51:09.6871	2024-09-29 20:55:53
18291	52	1	2	Andy Biggs	Andy		Biggs			HD-AZ-5	0	Andy_Biggs	6602301	28088	212155	N00039293	3fg4gjfb	2024-09-29 21:51:09.694187	2024-09-29 20:55:53
18292	52	1	1	Lisa Rochester	Lisa	Blunt	Rochester			HD-DE	0	Lisa_Blunt_Rochester	38420440	173249	558891	N00038414	c8kj8aoc	2024-09-29 21:51:09.700895	2024-09-29 20:55:53
18295	52	1	1	Salud Carbajal	Salud	O.	Carbajal			HD-CA-24	0	Salud_Carbajal	39707235	81569	460424	N00037015	h6wxpim8	2024-09-29 21:51:09.707581	2024-09-29 20:55:53
18297	52	1	1	Luis Correa	Luis		Correa			HD-CA-46	0	Lou_Correa	6398747	9732	193097	N00037260	0hvmix5k	2024-09-29 21:51:09.714775	2024-09-29 20:55:53
18301	52	1	1	Adriano Espaillat	Adriano		Espaillat			HD-NY-13	0	Adriano_Espaillat	6512516	14379	197725	N00034549	n4tj3j3m	2024-09-29 21:51:09.729866	2024-09-29 20:55:53
18304	52	1	2	Brian Fitzpatrick	Brian	K.	Fitzpatrick			HD-PA-1	0	Brian_Fitzpatrick	39434649	167708	568624	N00038779	7k4jnnep	2024-09-29 21:51:09.745699	2024-09-29 20:55:53
18305	52	1	2	Matt Gaetz	Matt		Gaetz			HD-FL-1	0	Matt_Gaetz	12998496	117101	286600	N00039503	nduyjfng	2024-09-29 21:51:09.752576	2024-09-29 20:55:53
18306	52	1	2	Mike Gallagher	Mike		Gallagher			HD-WI-8	0	Mike_Gallagher_(New_York)	40609598	171843	577549	N00039330	h18j43v2	2024-09-29 21:51:09.759952	2024-09-29 20:55:53
18308	52	1	1	Vicente Gonzalez	Vicente		Gonzalez			HD-TX-34	0	Vicente_Gonzalez_Jr.	17872003	166483	561764	N00038809	eai4hd0g	2024-09-29 21:51:09.767521	2024-09-29 20:55:53
18309	52	1	1	Josh Gottheimer	Josh		Gottheimer			HD-NJ-5	0	Josh_Gottheimer	39707518	169202	346665	N00036944	9dqdbujj	2024-09-29 21:51:09.774899	2024-09-29 20:55:53
18310	52	1	2	Clay Higgins	Clay		Higgins			HD-LA-3	0	Clay_Higgins	41316479	174484	588003	N00039953	mpcv1p4d	2024-09-29 21:51:09.781812	2024-09-29 20:55:53
18312	52	1	1	Pramila Jayapal	Pramila		Jayapal			HD-WA-7	0	Pramila_Jayapal	2644458	153141	499054	N00038858	612z08hj	2024-09-29 21:51:09.789205	2024-09-29 20:55:53
18313	52	1	2	Mike Johnson	Mike		Johnson			HD-LA-4	0	Mike_Johnson_(Louisiana)	19895272	156097	527158	N00039106	zb879n0c	2024-09-29 21:51:09.796552	2024-09-29 20:55:54
18314	52	1	1	Ro Khanna	Ro		Khanna			HD-CA-17	0	Ro_Khanna	373494	29473	281537	N00026427	mapln5bo	2024-09-29 21:51:09.80364	2024-09-29 20:55:54
18316	52	1	1	Raja Krishnamoorthi	Raja		Krishnamoorthi			HD-IL-8	0	Raja_Krishnamoorthi	6265333	117519	385662	N00033240	kvbno8r6	2024-09-29 21:51:09.811471	2024-09-29 20:55:54
18317	52	1	2	David Kustoff	David		Kustoff			HD-TN-8	0	David_Kustoff	9383528	48997	570162	N00025445	my6vsc0l	2024-09-29 21:51:09.819201	2024-09-29 20:55:54
18321	52	1	2	Brian Mast	Brian	J.	Mast			HD-FL-21	0	Brian_Mast	32158682	166245	541019	N00037269	lfefmwns	2024-09-29 21:51:09.827367	2024-09-29 20:55:54
18326	52	1	1	Jimmy Panetta	Jimmy		Panetta			HD-CA-19	0	Jimmy_Panetta	35018515	169078	561057	N00038601	wwhiv48t	2024-09-29 21:51:09.834798	2024-09-29 20:55:54
18327	52	1	1	Jamie Raskin	Jamie		Raskin			HD-MD-8	0	Jamie_Raskin	1066956	65904	248823	N00037036	ne1btca3	2024-09-29 21:51:09.842389	2024-09-29 20:55:54
18330	52	1	2	John Rutherford	John	H.	Rutherford			HD-FL-5	0	John_Rutherford_(Florida)	37039917	172542	581000	N00039777	flc8imp1	2024-09-29 21:51:09.853211	2024-09-29 20:55:54
18331	52	1	2	Lloyd Smucker	Lloyd		Smucker			HD-PA-11	0	Lloyd_Smucker	5582657	102454	269658	N00038781	qm5kg4tm	2024-09-29 21:51:09.86103	2024-09-29 20:55:54
18332	52	1	1	Darren Soto	Darren		Soto			HD-FL-9	0	Darren_Soto	198924	67618	255376	N00037422	fizx4b9o	2024-09-29 21:51:09.87247	2024-09-29 20:55:54
19370	52	1	2	Ron Estes	Ron		Estes			HD-KS-4	0	Ron_Estes_(U.S._House_representative)	6691026	125031	311777	N00040712	4216q1mj	2024-09-29 21:51:09.897193	2024-09-29 20:55:54
19407	52	1	2	Ralph Norman	Ralph	W.	Norman			HD-SC-5	0	Ralph_Norman	6126950	47930	227505	N00027783	5gfyvsdp	2024-09-29 21:51:09.905088	2024-09-29 20:55:54
19409	52	1	1	Jimmy Gomez	Jimmy		Gomez			HD-CA-34	0	Jimmy_Gomez	13008707	138524	390070	N00040597	9eg16r7f	2024-09-29 21:51:09.9129	2024-09-29 20:55:54
19646	52	1	2	Debbie Lesko	Debbie		Lesko			HD-AZ-8	0	Debbie_Lesko	12997825	106483	267627	N00042056	mdc8hgzr	2024-09-29 21:51:09.928996	2024-09-29 20:55:54
19664	52	1	2	Michael Cloud	Michael		Cloud			HD-TX-27	0	Michael_Cloud_(Texas)	44045161	177350	636744	N00041882	her26bfa	2024-09-29 21:51:09.93611	2024-09-29 20:55:54
19676	52	1	2	Troy Balderson	Troy		Balderson			HD-OH-12	0	Troy_Balderson	3499988	102781	271784	N00042194	aii9kehb	2024-09-29 21:51:09.943683	2024-09-29 20:54:53
19692	52	1	2	Kevin Hern	Kevin		Hern			HD-OK-1	0	Kevin_Hern	44044988	180004	618789	N00040829	ttdzm6wu	2024-09-29 21:51:09.952429	2024-09-29 20:55:54
19693	52	1	1	Joseph Morelle	Joseph	D.	Morelle		Joe	HD-NY-25	0	Joseph_Morelle	5413103	145182	197784	N00043207	wqycx9xg	2024-09-29 21:51:09.959609	2024-09-29 20:55:54
19694	52	1	1	Mary Gay Scanlon	Mary		Scanlon			HD-PA-5	0	Mary_Gay_Scanlon	44954452	178890	655204	N00042706	gdvbkhz9	2024-09-29 21:51:09.967123	2024-09-29 20:55:54
19700	52	1	1	Susan Wild	Susan		Wild			HD-PA-7	0	Susan_Wild	17853601	178895	638609	N00041997	ku74u6oh	2024-09-29 21:51:09.973955	2024-09-29 20:55:54
20039	52	1	1	Colin Allred	Colin	Z.	Allred			HD-TX-32	0	Colin_Allred	44045171	177357	623979	N00040989	nqx5az23	2024-09-29 21:51:09.981018	2024-09-29 20:55:54
20044	52	1	2	Tim Burchett	Tim		Burchett			HD-TN-2	0	Tim_Burchett	6607163	24379	198970	N00041594	zo7df675	2024-09-29 21:51:10.033469	2024-09-29 20:55:54
20045	52	1	1	Ed Case	Ed		Case			HD-HI-1	0	Ed_Case	10085353	3422	193944	N00025882	a2aso5jv	2024-09-29 21:51:10.050365	2024-09-29 20:55:54
20046	52	1	1	Sean Casten	Sean		Casten			HD-IL-6	0	Sean_Casten	43471680	176982	629120	N00041338	rytchshd	2024-09-29 21:51:10.060677	2024-09-29 20:55:54
20047	52	1	2	Ben Cline	Ben	L.	Cline			HD-VA-6	0	Ben_Cline	6613874	50959	212955	N00042296	s8gvila1	2024-09-29 21:51:10.071655	2024-09-29 20:55:54
20048	52	1	1	Angela Craig	Angela	Dawn	Craig			HD-MN-2	0	Angie_Craig	32141809	166261	536254	N00037039	3uco5608	2024-09-29 21:51:10.080657	2024-09-29 20:55:54
20050	52	1	1	Jason Crow	Jason		Crow			HD-CO-6	0	Jason_Crow	44044490	180218	621716	N00040876	xd7063do	2024-09-29 21:51:10.103494	2024-09-29 20:55:54
20054	52	1	1	Sharice Davids	Sharice		Davids			HD-KS-3	0	Sharice_Davids	15561443	181201	655850	N00042626	ue5szndm	2024-09-29 21:51:10.111601	2024-09-29 20:55:54
20056	52	1	1	Madeleine Dean	Madeleine		Dean			HD-PA-4	0	Madeleine_Dean	4701392	136484	569358	N00042894	64vfxa51	2024-09-29 21:51:10.119645	2024-09-29 20:55:54
20057	52	1	1	Veronica Escobar	Veronica		Escobar			HD-TX-16	0	Veronica_Escobar	44045126	99345	634679	N00041702	6pdl4n1z	2024-09-29 21:51:10.127023	2024-09-29 20:55:54
20059	52	1	1	Elizabeth Fletcher	Elizabeth	Pannill	Fletcher			HD-TX-7	0	Lizzie_Pannill_Fletcher	44045104	177031	625330	N00041194	xs2edxvf	2024-09-29 21:51:10.138793	2024-09-29 20:55:54
20060	52	1	2	Russ Fulcher	Russ		Fulcher			HD-ID-1	0	Russ_Fulcher	6668632	33091	239426	N00041335	bu6y6nd5	2024-09-29 21:51:10.147456	2024-09-29 20:55:54
20061	52	1	1	Jesus Garcia	Jesus		Garcia		Chuy	HD-IL-4	0	Jesus_Garcia	28299070	6261	645347	N00042114	hgpd80bs	2024-09-29 21:51:10.154778	2024-09-29 20:55:54
20062	52	1	1	Sylvia Garcia	Sylvia		Garcia			HD-TX-29	0	Sylvia_Garcia	16351467	49734	454041	N00042282	7x1uts8s	2024-09-29 21:51:10.161948	2024-09-29 20:55:54
20064	52	1	2	Lance Gooden	Lance		Gooden			HD-TX-5	0	Lance_Gooden	6681277	116935	236203	N00042237	qq4mzp7h	2024-09-29 21:51:10.169487	2024-09-29 20:55:54
20065	52	1	2	Mark Green	Mark		Green			HD-TN-7	0	Mark_Green_(Tennessee)	11030026	139030	399479	N00041873	ciu7yxo6	2024-09-29 21:51:10.177184	2024-09-29 20:55:54
20066	52	1	2	Michael Guest	Michael		Guest			HD-MS-3	0	Michael_Guest	16352053	179667	651006	N00042458	j5fkx86s	2024-09-29 21:51:10.185581	2024-09-29 20:55:54
20067	52	1	1	Jared Golden	Jared		Golden			HD-ME-2	0	Jared_Golden	23424266	151420	372438	N00041668	omf1h5se	2024-09-29 21:51:10.193024	2024-09-29 20:55:54
20069	52	1	1	Jahana Hayes	Jahana		Hayes			HD-CT-5	0	Jahana_Hayes	45681143	181744	666101	N00043421	bfp27mah	2024-09-29 21:51:10.200018	2024-09-29 20:55:54
20071	52	1	1	Chrissy Houlahan	Chrissy		Houlahan			HD-PA-6	0	Chrissy_Houlahan	44045003	178893	621721	N00040949	jtfybl9j	2024-09-29 21:51:10.206818	2024-09-29 20:55:54
20074	52	1	1	Josh Harder	Josh		Harder			HD-CA-9	0	Josh_Harder	43937863	179326	624344	N00040853	5i07cyjn	2024-09-29 21:51:10.214032	2024-09-29 20:55:54
20075	52	1	2	Dusty Johnson	Dusty		Johnson			HD-SD	0	Dusty_Johnson	43398875	48307	240544	N00040559	r8owixum	2024-09-29 21:51:10.221454	2024-09-29 20:55:54
20077	52	1	1	Andy Kim	Andy		Kim			HD-NJ-3	0	Andrew_Kim_(New_Jersey)	44044858	179640	628795	N00041370	ngoor9ky	2024-09-29 21:51:10.239133	2024-09-29 20:55:54
20081	52	1	1	Mike Levin	Mike		Levin			HD-CA-49	0	Mike_Levin	44044456	179416	617967	N00040667	cn1wguew	2024-09-29 21:51:10.252913	2024-09-29 20:55:54
20084	52	1	2	Carol Miller	Carol	D.	Miller			HD-WV-1	0	Carol_Miller_(West_Virginia)	6659422	52123	249553	N00041542	jgz93z1y	2024-09-29 21:51:10.268298	2024-09-29 20:55:54
20086	52	1	1	Lucy McBath	Lucy		McBath			HD-GA-7	0	Lucy_McBath	44893293	178538	658185	N00042813	l9o4b44r	2024-09-29 21:51:10.275333	2024-09-29 20:55:54
20088	52	1	1	Joseph Neguse	Joseph		Neguse			HD-CO-2	0	Joe_Neguse	23406914	151075	485964	N00041080	3omk7yar	2024-09-29 21:51:10.282148	2024-09-29 20:55:54
20089	52	1	1	Alexandria Ocasio-Cortez	Alexandria		Ocasio-Cortez			HD-NY-14	0	Alexandria_Ocasio-Cortez	43884749	180416	624858	N00041162	bo9op4iq	2024-09-29 21:51:10.289242	2024-09-29 20:55:54
20090	52	1	1	Ilhan Omar	Ilhan		Omar			HD-MN-5	0	Ilhan_Omar	40606750	171628	583510	N00043581	32tjrlyp	2024-09-29 21:51:10.299399	2024-09-29 20:55:54
20091	52	1	1	Christopher Pappas	Christopher	C.	Pappas		Chris	HD-NH-1	0	Chris_Pappas	6394987	42635	213040	N00042161	wl661lbn	2024-09-29 21:51:10.308769	2024-09-29 20:55:54
20093	52	1	1	Dean Phillips	Dean	Benson	Phillips			HD-MN-3	0	Dean_Phillips	14700222	181357	626096	N00041134	uv1ly2v1	2024-09-29 21:51:10.322833	2024-09-29 20:55:54
20094	52	1	1	Ayanna Pressley	Ayanna	S.	Pressley			HD-MA-7	0	Ayanna_Pressley	45365104	122700	234321	N00042581	8q0j3im4	2024-09-29 21:51:10.331218	2024-09-29 20:55:54
20095	52	1	1	Katie Porter	Katie		Porter			HD-CA-47	0	Katie_Porter	44044441	179393	621002	N00040865	nw650itd	2024-09-29 21:51:10.33799	2024-09-29 20:55:54
20096	52	1	2	Guy Reschenthaler	Guy		Reschenthaler			HD-PA-14	0	Guy_Reschenthaler	24650451	166004	560660	N00041871	fkmxwvoo	2024-09-29 21:51:10.34477	2024-09-29 20:55:54
20098	52	1	2	John Rose	John	W.	Rose			HD-TN-6	0	John_Rose_(Tennessee)	44045074	180452	632997	N00041599	vfwl31f5	2024-09-29 21:51:10.351621	2024-09-29 20:55:54
20100	52	1	2	Chip Roy	Chip		Roy			HD-TX-21	0	Chip_Roy	44449969	177319	223268	N00042268	cqzhn7pe	2024-09-29 21:51:10.35939	2024-09-29 20:55:54
20103	52	1	1	Rebecca Sherrill	Rebecca	Michelle	Sherrill		Mikie	HD-NJ-11	0	Mikie_Sherrill	43965079	179651	625260	N00041154	clc8hanm	2024-09-29 21:51:10.366387	2024-09-29 20:55:54
20104	52	1	1	Elissa Slotkin	Elissa		Slotkin			HD-MI-7	0	Elissa_Slotkin	44044762	181080	261745	N00041357	2guyleny	2024-09-29 21:51:10.374036	2024-09-29 20:55:54
20105	52	1	1	Abigail Spanberger	Abigail		Spanberger			HD-VA-7	0	Abigail_Spanberger	44045205	179682	630216	N00041418	pj9a15df	2024-09-29 21:51:10.382303	2024-09-29 20:55:54
20107	52	1	1	Greg Stanton	Greg		Stanton			HD-AZ-4	0	Greg_Stanton	44044364	72030	638908	N00041750	pmq7yftp	2024-09-29 21:51:10.389781	2024-09-29 20:55:54
20108	52	1	2	Pete Stauber	Pete		Stauber			HD-MN-8	0	Pete_Stauber	44044791	159954	630211	N00041511	1zy2f82t	2024-09-29 21:51:10.396489	2024-09-29 20:55:54
20109	52	1	2	Bryan Steil	Bryan		Steil			HD-WI-1	0	Bryan_Steil	45356811	181289	664604	N00043379	bd7h9wdk	2024-09-29 21:51:10.404808	2024-09-29 20:55:54
20110	52	1	2	Greg Steube	Greg		Steube			HD-FL-17	0	Greg_Steube	6692870	117248	289471	N00042808	a7fpcibx	2024-09-29 21:51:10.413331	2024-09-29 20:55:54
20111	52	1	1	Haley Stevens	Haley		Stevens			HD-MI-11	0	Haley_Stevens	44044764	181092	623571	N00040915	lr9fsdh3	2024-09-29 21:51:10.426558	2024-09-29 20:55:54
20112	52	1	1	Kim Schrier	Kim		Schrier			HD-WA-8	0	Kim_Schrier	44045231	181124	632874	N00041606	4cjgano2	2024-09-29 21:51:10.436082	2024-09-29 20:55:54
20115	52	1	1	Rashida Tlaib	Rashida		Tlaib			HD-MI-12	0	Rashida_Tlaib	13002117	105368	268236	N00042649	pie8gfo6	2024-09-29 21:51:10.451563	2024-09-29 20:55:54
20116	52	1	1	Lori Trahan	Lori		Trahan			HD-MA-3	0	Lori_Trahan	15875826	182310	636951	N00041808	6vjcpbk4	2024-09-29 21:51:10.458542	2024-09-29 20:55:55
20117	52	1	1	David Trone	David	John	Trone			HD-MD-6	0	David_Trone	5631712	167336	568351	N00039122	k70n0p91	2024-09-29 21:51:10.467565	2024-09-29 20:55:55
20119	52	1	1	Lauren Underwood	Lauren	A.	Underwood			HD-IL-14	0	Lauren_Underwood	44044644	177001	601601	N00041569	47xhlnm7	2024-09-29 21:51:10.474652	2024-09-29 20:55:55
20120	52	1	2	Jeff Van Drew	Jeff		Van Drew			HD-NJ-2	0	Jeff_Van_Drew	6389812	24685	209970	N00042164	nuddykio	2024-09-29 21:51:10.481635	2024-09-29 20:55:55
20121	52	1	2	Michael Waltz	Michael		Waltz			HD-FL-6	0	Michael_Waltz	45399438	182261	652214	N00042403	jgbq6rbf	2024-09-29 21:51:10.488762	2024-09-29 20:55:55
20123	52	1	1	Jennifer Wexton	Jennifer		Wexton			HD-VA-10	0	Jennifer_Wexton	19907288	147013	484877	N00041002	mv7yhv1z	2024-09-29 21:51:10.498321	2024-09-29 20:55:55
21386	52	1	2	Greg Murphy	Gregory	Francis	Murphy		Greg	HD-NC-3	0	Gregory_Murphy	166135	5975268	558576	N00044027	nbwt47im	2024-09-29 21:51:10.512567	2024-09-29 20:55:55
21642	52	1	1	Kweisi Mfume	Kweisi		Mfume			HD-MD-7	0	Kweisi_Mfume	15479665	26892	722075	N00001799	epwa383j	2024-09-29 21:51:10.519339	2024-09-29 20:55:55
21646	52	1	2	Mike Garcia	Mike		Garcia			HD-CA-27	0	Mike_Garcia	48160633	188664	703179	N00044298	ze3h7vbh	2024-09-29 21:51:10.528403	2024-09-29 20:55:55
21647	52	1	2	Tom Tiffany	Tom		Tiffany			HD-WI-7	0	Tom_Tiffany	48524679	51831	310033	N00045307	u6uhwq63	2024-09-29 21:51:10.535349	2024-09-29 20:55:55
21921	52	1	2	Jerry Carl	Jerry	Lee	Carl	Jr.		HD-AL-1	0	Jerry_Carl	48161159	143749	702881	N00044245	qz3e9ggs	2024-09-29 21:51:10.542284	2024-09-29 20:55:55
21922	52	1	2	Barry Moore	Felix	Barry	Moore		Barry	HD-AL-2	0	Barry_Moore_(Alabama)	12997504	121792	290770	N00041295	rndxrhr4	2024-09-29 21:51:10.54938	2024-09-29 20:55:55
21923	52	1	1	Sara Jacobs	Sara	J.	Jacobs			HD-CA-51	0	Sara_Jacobs	19388816	179414	644085	N00042081	0fh0a2gj	2024-09-29 21:51:10.557782	2024-09-29 20:55:55
21924	52	1	2	Young Kim	Young		Kim			HD-CA-40	0	Young_Kim_(California)	22215539	151787	494206	N00042386	n6djpvpp	2024-09-29 21:51:10.564679	2024-09-29 20:55:55
21926	52	1	2	Michelle Steel	Michelle	E.	Steel			HD-CA-45	0	Michelle_Steel	197551	157194	694474	N00044501	cz8e84xr	2024-09-29 21:51:10.579626	2024-09-29 20:55:55
21929	52	1	2	Byron Donalds	Byron		Donalds			HD-FL-19	0	Byron_Donalds	17657863	137655	391126	N00034016	nnf8tn83	2024-09-29 21:51:10.602091	2024-09-29 20:55:55
21930	52	1	2	Scott Franklin	Scott		Franklin			HD-FL-18	0	Scott_Franklin	49846565	191355	735595	N00046760	m8rwshmx	2024-09-29 21:51:10.609259	2024-09-29 20:55:55
21931	52	1	2	Carlos Gimenez	Carlos		Gimenez			HD-FL-28	0	Carlos_Gimenez	49846593	81366	731724	N00046394	v8f2spmx	2024-09-29 21:51:10.61611	2024-09-29 20:55:55
21932	52	1	2	Maria Salazar	Maria	Elvira	Salazar			HD-FL-27	0	Maria_Elvira_Salazar	45399472	182300	658161	N00042810	r7glzu6y	2024-09-29 21:51:10.623343	2024-09-29 20:55:55
21934	52	1	2	Andrew Clyde	Andrew		Clyde			HD-GA-9	0	Andrew_Clyde	49394308	189770	733887	N00046654	xfgfdpcq	2024-09-29 21:51:10.633124	2024-09-29 20:55:55
21935	52	1	2	Marjorie Greene	Marjorie	Taylor	Greene			HD-GA-14	0	Marjorie_Taylor_Greene	48161226	189785	707878	N00044701	21y0ga9h	2024-09-29 21:51:10.640121	2024-09-29 20:55:55
21936	52	1	1	Nikema Williams	Nikema		Williams			HD-GA-5	0	Nikema_Williams	26177470	176751	648743	N00047361	n4prpgbl	2024-09-29 21:51:10.647562	2024-09-29 20:55:55
21938	52	1	2	Randy Feenstra	Randy	L.	Feenstra			HD-IA-4	0	Randy_Feenstra	6079832	103301	271911	N00044011	hesujqm7	2024-09-29 21:51:10.657269	2024-09-29 20:55:55
21939	52	1	2	Ashley Hinson	Ashley	E.	Hinson			HD-IA-2	0	Ashley_Hinson	38148887	168783	572935	N00044521	zj18zmyg	2024-09-29 21:51:10.665082	2024-09-29 20:55:55
21943	52	1	1	Frank Mrvan	Frank	J.	Mrvan	Jr.		HD-IN-1	0	Frank_Mrvan_(Indiana_congressional_candidate)	6393363	113775	722372	N00045905	64slefqy	2024-09-29 21:51:10.687576	2024-09-29 20:55:55
21944	52	1	2	Victoria Spartz	Victoria	K.	Spartz			HD-IN-5	0	Victoria_Spartz	6986460	178203	638877	N00046537	hksmuovv	2024-09-29 21:51:10.694644	2024-09-29 20:55:55
21946	52	1	2	Tracey Mann	Tracey		Mann			HD-KS-1	0	Tracey_Mann	15488021	125007	284640	N00030743	tangsk64	2024-09-29 21:51:10.711111	2024-09-29 20:55:55
21947	52	1	1	Jake Auchincloss	Jake		Auchincloss			HD-MA-4	0	Jake_Auchincloss	48161414	173832	719720	N00045506	3qw9rp5n	2024-09-29 21:51:10.719033	2024-09-29 20:55:55
21948	52	1	2	Lisa McClain	Lisa		McClain			HD-MI-9	0	Lisa_McClain	49944007	191633	721727	N00045730	8bibtcrv	2024-09-29 21:51:10.726667	2024-09-29 20:55:55
21950	52	1	2	Michelle Fischbach	Michelle		Fischbach			HD-MN-7	0	Michelle_Fischbach	13012379	3882	195769	N00045251	ss0arjml	2024-09-29 21:51:10.733667	2024-09-29 20:55:55
21951	52	1	1	Cori Bush	Cori		Bush			HD-MO-1	0	Cori_Bush	39656831	169020	571342	N00039373	enexntgx	2024-09-29 21:51:10.743515	2024-09-29 20:55:55
21952	52	1	2	Matt Rosendale	Matt		Rosendale			HD-MT-2	0	Matt_Rosendale	13003681	120815	290215	N00035517	hye1mnv1	2024-09-29 21:51:10.751315	2024-09-29 20:55:55
21954	52	1	1	Kathy Manning	Kathy	Ellen	Manning			HD-NC-6	0	Kathy_Manning	1441679	178304	646745	N00042159	zx715i36	2024-09-29 21:51:10.759155	2024-09-29 20:55:55
21955	52	1	1	Deborah Ross	Deborah		Ross			HD-NC-2	0	Deborah_Ross	5853356	41560	211983	N00038565	d0quaw5t	2024-09-29 21:51:10.766405	2024-09-29 20:55:55
21957	52	1	1	Teresa Fernandez	Teresa	Leger	Fernandez			HD-NM-3	0	Teresa_Leger_Fernandez	1921149	189882	453352	N00044559	adh14aa5	2024-09-29 21:51:10.773643	2024-09-29 20:55:55
21958	52	1	1	Jamaal Bowman	Jamaal		Bowman			HD-NY-16	0	Jamaal_Bowman	48160953	191205	709495	N00044790	rmp3jam1	2024-09-29 21:51:10.780801	2024-09-29 20:55:55
21959	52	1	2	Andrew Garbarino	Andrew	R.	Garbarino			HD-NY-2	0	Andrew_Garbarino	15666124	143103	433049	N00046030	osz2vvaz	2024-09-29 21:51:10.789305	2024-09-29 20:55:55
21961	52	1	2	Nicole Malliotakis	Nicole		Malliotakis			HD-NY-11	0	Nicole_Malliotakis	13009241	127929	309650	N00044040	f7cd23g4	2024-09-29 21:51:10.796448	2024-09-29 20:55:55
21962	52	1	1	Ritchie Torres	Ritchie	John	Torres			HD-NY-15	0	Ritchie_Torres	48161012	161718	703996	N00044346	v3uhlrlu	2024-09-29 21:51:10.803542	2024-09-29 20:55:55
21964	52	1	2	Cliff Bentz	Cliff	B.	Bentz			HD-OR-2	0	Cliff_Bentz	4964521	102400	262468	N00045773	hu876n3v	2024-09-29 21:51:10.817598	2024-09-29 20:55:55
21965	52	1	2	Nancy Mace	Nancy		Mace			HD-SC-1	0	Nancy_Mace	23424620	146076	466143	N00035670	m0fy0tv1	2024-09-29 21:51:10.824462	2024-09-29 20:55:55
21966	52	1	2	Diana Harshbarger	Diana		Harshbarger			HD-TN-1	0	Diana_Harshbarger	49626376	190524	734559	N00046688	q1jc8j5b	2024-09-29 21:51:10.831766	2024-09-29 20:55:55
21967	52	1	2	Patrick Fallon	Patrick		Fallon		Pat	HD-TX-4	0	Pat_Fallon	12553367	115056	414616	N00047264	5bcp8t50	2024-09-29 21:51:10.838842	2024-09-29 20:55:55
21968	52	1	2	Ernest Gonzales	Ernest	Anthony	Gonzales	II	Tony	HD-TX-23	0	Tony_Gonzales	48161835	188225	706319	N00044592	9a6lbhre	2024-09-29 21:51:10.84588	2024-09-29 20:55:55
21969	52	1	2	Ronny Jackson	Ronny		Jackson			HD-TX-13	0	Ronny_Jackson	48644982	188325	342600	N00046055	repkb6w1	2024-09-29 21:51:10.85306	2024-09-29 20:55:55
21970	52	1	2	Troy Nehls	Troy		Nehls			HD-TX-22	0	Troy_Nehls	48645001	188334	719080	N00046067	x0zaa9xd	2024-09-29 21:51:10.860278	2024-09-29 20:55:55
21972	52	1	2	Elizabeth Van Duyne	Elizabeth	Ann	Van Duyne		Beth	HD-TX-24	0	Beth_Van_Duyne	48161909	79150	661605	N00045167	57vjrlfd	2024-09-29 21:51:10.876037	2024-09-29 20:55:55
21973	52	1	2	Blake Moore	Blake	David	Moore			HD-UT-1	0	Blake_Moore	49449645	191164	732706	N00046598	3ejqjytg	2024-09-29 21:51:10.883466	2024-09-29 20:55:55
21975	52	1	2	Robert Good	Robert		Good			HD-VA-5	0	Bob_Good	48161945	190745	718990	N00045557	honh8nuo	2024-09-29 21:51:10.898314	2024-09-29 20:55:55
21976	52	1	1	Marilyn Strickland	Marilyn		Strickland			HD-WA-10	0	Marilyn_Strickland	49946469	80596	727678	N00046320	90b3h640	2024-09-29 21:51:10.905458	2024-09-29 20:55:55
22929	52	1	1	Troy Carter	Troy		Carter			HD-LA-2	0	Troy_Carter	5051668	35462	266759	N00025766	ndmtm3it	2024-09-29 21:51:10.926756	2024-09-29 20:55:55
22939	52	1	1	Melanie Stansbury	Melanie	Ann	Stansbury			HD-NM-1	0	Melanie_Ann_Stansbury	44581391	180789	461875	N00047871	wfmzd4jc	2024-09-29 21:51:10.934411	2024-09-29 20:55:55
22947	52	1	2	Jake Ellzey	John	K.	Ellzey	Sr.	Jake	HD-TX-6	0	Jake_Ellzey	22214513	68070	533891	N00042243	9ltdxb73	2024-09-29 21:51:10.942092	2024-09-29 20:55:55
22966	52	1	1	Shontel Brown	Shontel		Brown			HD-OH-11	0	Shontel_Brown	2964354	161622	772727	N00047875	c74atuk2	2024-09-29 21:51:10.949552	2024-09-29 20:55:55
23048	52	1	1	Sheila Cherfilus-McCormick	Sheila		Cherfilus-McCormick			HD-FL-20	0	Sheila_Cherfilus-McCormick	0	182285	665191	N00043504	8w2noj9v	2024-09-29 21:51:10.96388	2024-09-29 20:55:55
23162	52	1	2	Brad Finstad	Brad		Finstad			HD-MN-1	0	Brad_Finstad	6597648	38612	212943	N00050649	nnuydsw9	2024-09-29 21:51:10.978612	2024-09-29 20:55:55
23172	52	1	1	Mary Peltola	Mary		Peltola			HD-AK	0	Mary_Peltola	12997276	207620	803941	         	uf9endr7	2024-09-29 21:51:10.985656	2024-09-29 20:55:55
23173	52	1	1	Pat Ryan	Pat		Ryan			HD-NY-18	0	Pat_Ryan_(New_York)	44044931	180314	627919	N00041165	2cma4mxv	2024-09-29 21:51:10.993211	2024-09-29 20:55:55
23182	52	1	2	Rudolph Yakym III	Rudolph		Yakym	III	Rudy	HD-IN-2	0	Rudy_Yakym	0	210545	0	         	d9xrip0d	2024-09-29 21:51:11.001062	2024-09-29 20:55:55
23998	52	1	2	Aaron Bean	Aaron		Bean			HD-FL-4	0	Aaron_Bean	0	53932	0	         	69pyyv23	2024-09-29 21:51:11.015457	2024-09-29 20:55:55
23999	52	1	1	Nikki Budzinski	Nikki		Budzinski			HD-IL-13	0	Nikki_Budzinski	0	204328	0	         	qdl1hdjc	2024-09-29 21:51:11.02259	2024-09-29 20:55:55
24000	52	1	2	Eric Burlison	Eric		Burlison			HD-MO-7	0	Eric_Burlison	0	104635	0	         	i2f7xgaz	2024-09-29 21:51:11.029918	2024-09-29 20:55:55
24001	52	1	2	Josh Brecheen	Josh		Brecheen			HD-OK-2	0	Josh_Brecheen	0	124973	0	         	f5m3mhg0	2024-09-29 21:51:11.037262	2024-09-29 20:55:55
24002	52	1	1	Becca Balint	Becca		Balint			HD-VT	0	Becca_Balint	0	154056	0	         	b0ijn7b8	2024-09-29 21:51:11.044548	2024-09-29 20:55:55
24003	52	1	2	Mike Collins	Mike		Collins			HD-GA-10	0	Mike_Collins_(Georgia)	0	151225	0	         	xy5va846	2024-09-29 21:51:11.051756	2024-09-29 20:55:55
24004	52	1	1	Jasmine Crockett	Jasmine		Crockett			HD-TX-30	0	Jasmine_Crockett	0	188486	0	         	60cnh5zu	2024-09-29 21:51:11.058839	2024-09-29 20:55:55
24005	52	1	1	Greg Casar	Greg		Casar			HD-TX-35	0	Greg_Casar	0	161953	0	         	6gjke85u	2024-09-29 21:51:11.066109	2024-09-29 20:55:55
24006	52	1	2	Elijah Crane	Elijah		Crane			HD-AZ-2	0	Eli_Crane	0	205885	0	         	ka83ezh4	2024-09-29 21:51:11.073087	2024-09-29 20:55:55
24008	52	1	1	Yadira Caraveo	Yadira		Caraveo			HD-CO-8	0	Yadira_Caraveo	0	181770	0	         	60vnyjk4	2024-09-29 21:51:11.087954	2024-09-29 20:55:55
24009	52	1	2	Lori Chavez-DeRemer	Lori		Chavez-DeRemer			HD-OR-5	0	Lori_Chavez-DeRemer	0	202792	0	         	uiyqdlif	2024-09-29 21:51:11.09513	2024-09-29 20:55:55
24010	52	1	1	Donald Davis	Donald	G.	Davis		Don	HD-NC-1	0	Donald_Davis	0	102950	0	         	ro4rptlb	2024-09-29 21:51:11.102335	2024-09-29 20:55:56
24011	52	1	1	Christopher Deluzio	Christopher	R.	Deluzio		Chris	HD-PA-17	0	Christopher_Deluzio	0	202954	0	         	3cjmrfqe	2024-09-29 21:51:11.109753	2024-09-29 20:55:56
24013	52	1	2	Anthony D'Esposito	Anthony		D'Esposito			HD-NY-4	0	Anthony_D'Esposito	0	174091	0	         	2m9vrgk8	2024-09-29 21:51:11.124382	2024-09-29 20:55:56
24014	52	1	2	John Duarte	John	S.	Duarte			HD-CA-13	0	John_Duarte	0	204965	0	         	s80dp162	2024-09-29 21:51:11.13144	2024-09-29 20:55:56
24015	52	1	2	Mike Ezell	Mike		Ezell			HD-MS-4	0	Mike_Ezell	0	202526	0	         	u73ke64w	2024-09-29 21:51:11.138636	2024-09-29 20:55:56
24016	52	1	2	Chuck Edwards	Charles		Edwards		Chuck	HD-NC-11	0	Chuck_Edwards	0	166600	0	         	8fipzkjy	2024-09-29 21:51:11.145637	2024-09-29 20:55:56
24017	52	1	1	Maxwell Frost	Maxwell	Alejandro	Frost			HD-FL-10	0	Maxwell_Alejandro_Frost	0	209096	0	         	h8v0p6ju	2024-09-29 21:51:11.153074	2024-09-29 20:55:56
24018	52	1	1	Valerie Foushee	Valerie	P.	Foushee			HD-NC-4	0	Valerie_Foushee	0	93091	0	         	wkrm3izc	2024-09-29 21:51:11.159983	2024-09-29 20:55:56
24019	52	1	2	Russell Fry	Russell		Fry			HD-SC-7	0	Russell_Fry	0	157265	0	         	k9uqc6mh	2024-09-29 21:51:11.167142	2024-09-29 20:55:56
24021	52	1	1	Daniel Goldman	Daniel	S.	Goldman			HD-NY-10	0	Daniel_Goldman	0	208627	0	         	imessbim	2024-09-29 21:51:11.181463	2024-09-29 20:55:56
24022	52	1	1	Marie Gluesenkamp Perez	Marie		Gluesenkamp Perez			HD-WA-3	0	Marie_Gluesenkamp_Perez	0	207307	0	         	mzhnsrg3	2024-09-29 21:51:11.188688	2024-09-29 20:55:56
24023	52	1	2	Erin Houchin	Erin		Houchin			HD-IN-9	0	Erin_Houchin	0	149614	0	         	cn8ra6ur	2024-09-29 21:51:11.196003	2024-09-29 20:55:56
24024	52	1	1	Val Hoyle	Val	T.	Hoyle			HD-OR-4	0	Val_Hoyle	0	116336	0	         	1mfvoxo7	2024-09-29 21:51:11.203221	2024-09-29 20:55:56
24025	52	1	2	Wesley Hunt	Wesley		Hunt			HD-TX-38	0	Wesley_Hunt_(Texas_Congress)	0	188147	0	         	aigqyfff	2024-09-29 21:51:11.211743	2024-09-29 20:55:56
24027	52	1	1	Glenn Ivey	Glenn		Ivey			HD-MD-4	0	Glenn_Ivey	0	166279	0	         	37gl3dyr	2024-09-29 21:51:11.226244	2024-09-29 20:55:56
24028	52	1	2	John James	John		James			HD-MI-10	0	John_James_(Michigan)	0	181062	0	         	ggwf09z2	2024-09-29 21:51:11.233238	2024-09-29 20:55:56
24029	52	1	1	Jeff Jackson	Jeff		Jackson			HD-NC-14	0	Jeff_Jackson	0	153729	0	         	xjvhd3qm	2024-09-29 21:51:11.241759	2024-09-29 20:55:56
24030	52	1	1	Jonathan Jackson	Jonathan	L.	Jackson			HD-IL-1	0	Jonathan_Jackson_(Illinois)	0	204284	0	         	ye1dkrv0	2024-09-29 21:51:11.248731	2024-09-29 20:55:56
24031	52	1	2	Thomas Kean	Thomas	H.	Kean	Jr.		HD-NJ-7	0	Thomas_Kean_Jr.	0	43250	0	         	v9e6a71p	2024-09-29 21:51:11.255891	2024-09-29 20:55:56
24032	52	1	2	Jennifer Kiggans	Jennifer		Kiggans			HD-VA-2	0	Jennifer_Kiggans	0	186387	0	         	sczd4c5b	2024-09-29 21:51:11.26416	2024-09-29 20:55:56
24033	52	1	1	Sydney Kamlager-Dove	Sydney		Kamlager-Dove			HD-CA-37	0	Sydney_Kamlager-Dove	0	178079	0	         	x3crkx3z	2024-09-29 21:51:11.271375	2024-09-29 20:55:56
24034	52	1	2	Kevin Kiley	Kevin		Kiley			HD-CA-3	0	Kevin_Kiley	0	169303	0	         	5kms13xw	2024-09-29 21:51:11.279359	2024-09-29 20:55:56
24035	52	1	2	Anna Luna	Anna	Paulina	Luna			HD-FL-13	0	Anna_Paulina_Luna	0	191344	0	         	cgyrto9z	2024-09-29 21:51:11.288319	2024-09-29 20:55:56
24036	52	1	2	Laurel Lee	Laurel	M.	Lee			HD-FL-15	0	Laurel_Lee	0	186114	0	         	w2q3cz7x	2024-09-29 21:51:11.295705	2024-09-29 20:55:56
24037	52	1	2	Nick LaLota	Nicholas	J.	LaLota		Nick	HD-NY-1	0	Nicholas_J._LaLota	0	191957	0	         	atp2pl3v	2024-09-29 21:51:11.302595	2024-09-29 20:55:56
24038	52	1	2	Michael Lawler	Michael		Lawler			HD-NY-17	0	Michael_Lawler_(New_York)	0	192271	0	         	fgm5xr9f	2024-09-29 21:51:11.310154	2024-09-29 20:55:56
24040	52	1	1	Greg Landsman	Greg		Landsman			HD-OH-1	0	Greg_Landsman	0	186237	0	         	dqvhgpdo	2024-09-29 21:51:11.324338	2024-09-29 20:55:56
24041	52	1	1	Summer Lee	Summer	L.	Lee			HD-PA-12	0	Summer_Lee	0	179240	0	         	l6mkki00	2024-09-29 21:51:11.33192	2024-09-29 20:55:56
24042	52	1	2	Morgan Luttrell	Morgan		Luttrell			HD-TX-8	0	Morgan_Luttrell	0	200930	0	         	nqkudebp	2024-09-29 21:51:11.339089	2024-09-29 20:55:56
24043	52	1	2	Cory Mills	Cory		Mills			HD-FL-7	0	Cory_Mills	0	209085	0	         	9pnzm67a	2024-09-29 21:51:11.346078	2024-09-29 20:55:56
24044	52	1	1	Jared Moskowitz	Jared		Moskowitz			HD-FL-23	0	Jared_Moskowitz	0	138155	0	         	fnbvq8zz	2024-09-29 21:51:11.353191	2024-09-29 20:55:56
24045	52	1	2	Richard McCormick	Richard		McCormick		Rich	HD-GA-6	0	Rich_McCormick	0	189765	0	         	kxmwymqd	2024-09-29 21:51:11.36045	2024-09-29 20:55:56
24046	52	1	1	Morgan McGarvey	Morgan		McGarvey			HD-KY-3	0	Morgan_McGarvey	0	139826	0	         	st9wzra0	2024-09-29 21:51:11.367695	2024-09-29 20:55:56
24047	52	1	2	Marcus Molinaro	Marcus	J.	Molinaro			HD-NY-19	0	Marcus_Molinaro	0	69202	0	         	cn43egr0	2024-09-29 21:51:11.374594	2024-09-29 20:55:56
24048	52	1	2	Max Miller	Max	L.	Miller			HD-OH-7	0	Max_Miller	0	206947	0	         	klshbo22	2024-09-29 21:51:11.382672	2024-09-29 20:55:56
24963	52	1	1	Gabe Amo	Gabe		Amo			HD-RI-1	0	Gabe_Amo	0	212295	0	         	00oe17xw	2024-09-29 21:51:39.842282	2024-09-29 20:56:27
25201	52	1	1	Timothy Kennedy	Timothy	M.	Kennedy		Tim	HD-NY-26	0	Tim_Kennedy_(New_York)	4689854	91670	0	         	b1ts1aiw	2024-09-29 21:51:39.849441	2024-09-29 20:56:27
18333	52	1	1	Thomas Suozzi	Thomas	R.	Suozzi			HD-NY-3	0	Tom_Suozzi	12996931	92111	462663	N00038742	0akuuwt3	2024-09-29 21:51:39.856832	2024-09-29 20:56:27
25207	52	1	2	Michael Rulli	Michael	A.	Rulli			HD-OH-6	0	Michael_Rulli	44423028	179016	0	         	ymurg8sq	2024-09-29 21:53:52.919639	2024-09-29 20:58:55
25204	52	1	2	Vince Fong	Vince		Fong			HD-CA-20	0	Vince_Fong	39707425	169357	224498	         	07ojd34c	2024-09-29 21:53:52.927083	2024-09-29 20:58:55
25210	52	1	2	Greg Lopez	Greg		Lopez			HD-CO-4	0	Greg_Lopez	6742495	16895	0	         	cc0ylurm	2024-09-29 21:54:33.817226	2024-09-29 20:59:41
8979	52	2	1	Ben Lujan	Ben	Ray	Lujan			SD-NM	0	Ben_Lujan,_Sr.	9025644	102842	266495	N00029562	s3k15nh3	2024-09-29 21:57:07.98146	2024-09-29 21:02:48
24049	52	1	1	Seth Magaziner	Seth		Magaziner			HD-RI-2	0	Seth_Magaziner	0	154457	0	         	qugy5otc	2024-09-29 21:51:11.389679	2024-09-29 20:55:56
24050	52	1	2	Nathaniel Moran	Nathaniel		Moran			HD-TX-1	0	Nathaniel_Moran	0	79156	0	         	61763t2y	2024-09-29 21:51:11.396898	2024-09-29 20:55:56
24051	52	1	1	Kevin Mullin	Kevin		Mullin			HD-CA-15	0	Kevin_Mullin_(California)	0	105586	0	         	7z1vjzm5	2024-09-29 21:51:11.409197	2024-09-29 20:55:56
24052	52	1	1	Robert Menendez	Robert		Menendez		Rob	HD-NJ-8	0	Rob_Menendez_(New_Jersey)	0	205678	0	         	xtua7l27	2024-09-29 21:51:11.416337	2024-09-29 20:55:56
24053	52	1	2	Zachary Nunn	Zachary		Nunn		Zach	HD-IA-3	0	Zach_Nunn	0	151170	0	         	d6p4ilmt	2024-09-29 21:51:11.424591	2024-09-29 20:55:56
24054	52	1	1	Wiley Nickel	Wiley		Nickel	III		HD-NC-13	0	Wiley_Nickel	0	178326	0	         	4jqygsbq	2024-09-29 21:51:11.432123	2024-09-29 20:55:56
24055	52	1	2	Andrew Ogles	Andrew		Ogles		Andy	HD-TN-5	0	Andrew_Ogles	0	48673	0	         	nrb9q75z	2024-09-29 21:51:11.440329	2024-09-29 20:55:56
24056	52	1	1	Brittany Pettersen	Brittany		Pettersen			HD-CO-7	0	Brittany_Pettersen	0	138744	0	         	6ytb7lul	2024-09-29 21:51:11.447612	2024-09-29 20:55:56
24057	52	1	1	Delia Ramirez	Delia	C.	Ramirez			HD-IL-3	0	Delia_Ramirez	0	177128	0	         	l0ympizj	2024-09-29 21:51:11.456105	2024-09-29 20:55:56
24058	52	1	2	Dale Strong	Dale	W.	Strong			HD-AL-5	0	Dale_Strong	0	81485	0	         	1ezf6heo	2024-09-29 21:51:11.463359	2024-09-29 20:55:56
24059	52	1	1	Hillary Scholten	Hillary	J.	Scholten			HD-MI-3	0	Hillary_Scholten	0	191584	0	         	j4jwsyw5	2024-09-29 21:51:11.470772	2024-09-29 20:55:56
24060	52	1	2	George Santos	George		Devolder-Santos			HD-NY-3	0	George_Devolder-Santos	0	191234	719723	         	fhzc4b5l	2024-09-29 21:51:11.477964	2024-09-29 20:55:56
24061	52	1	1	Emilia Sykes	Emilia	Strong	Sykes			HD-OH-13	0	Emilia_Sykes	0	152164	0	         	w00dbdao	2024-09-29 21:51:11.487311	2024-09-29 20:55:56
24062	52	1	2	Keith Self	Keith		Self			HD-TX-3	0	Keith_Self	0	97491	0	         	4sbc6bxz	2024-09-29 21:51:11.494895	2024-09-29 20:55:56
24063	52	1	1	Eric Sorensen	Eric		Sorensen			HD-IL-17	0	Eric_Sorensen	0	204339	0	         	ycb7okbe	2024-09-29 21:51:11.502072	2024-09-29 20:55:56
24064	52	1	1	Andrea Salinas	Andrea		Salinas			HD-OR-6	0	Andrea_Salinas	0	178196	0	         	f59u7g2h	2024-09-29 21:51:11.511784	2024-09-29 20:55:56
24065	52	1	1	Jill Tokuda	Jill	N.	Tokuda			HD-HI-2	0	Jill_Tokuda	0	68493	0	         	u7dspu3v	2024-09-29 21:51:11.519272	2024-09-29 20:55:56
24066	52	1	1	Shri Thanedar	Shri		Thanedar			HD-MI-13	0	Shri_Thanedar	0	182346	0	         	bg5uyv29	2024-09-29 21:51:11.526518	2024-09-29 20:55:56
24067	52	1	2	Derrick Van Orden	Derrick		Van Orden			HD-WI-3	0	Derrick_Van_Orden	0	192343	0	         	5u3zr6ni	2024-09-29 21:51:11.533809	2024-09-29 20:55:56
24068	52	1	1	Gabe Vasquez	Gabriel		Vasquez		Gabe	HD-NM-2	0	Gabriel_Vasquez	0	192343	0	         	t1eird11	2024-09-29 21:51:11.544574	2024-09-29 20:55:56
24071	52	1	2	James Moylan	James	C.	Moylan			HD-GU	0	James_Moylan	0	209781	0	         	zpq5ktdu	2024-09-29 21:51:11.568099	2024-09-29 20:55:56
24913	52	1	1	Jennifer McClellan	Jennifer		McClellan			HD-VA-4	0	Jennifer_McClellan	5703418	58655	241253	         	nur3um73	2024-09-29 21:51:11.575241	2024-09-29 20:55:56
9371	52	1	2	Kevin McCarthy	Kevin		McCarthy			HD-CA-20	0	Kevin_McCarthy_(California)	331199	28918	211752	N00028152	n1t7mtfg	2024-09-29 21:51:11.582589	2024-09-29 20:55:56
24984	52	1	2	Celeste Maloy	Celeste		Maloy			HD-UT-2	0	Celeste_Maloy	0	212289	0	         	et1nurfl	2024-09-29 21:51:38.876703	2024-09-29 20:56:25
8981	52	2	1	Edward Markey	Edward	J.	Markey			SD-MA	0	Edward_Markey	17658675	26900	158881	N00000270	hdvrlylp	2024-09-29 21:57:07.988516	2024-09-29 21:02:48
8986	52	2	1	Christopher Murphy	Christopher	S.	Murphy			SD-CT	0	Chris_Murphy_(Connecticut)	6384200	17189	193324	N00027566	m2pvngcc	2024-09-29 21:57:07.995548	2024-09-29 21:02:48
8997	52	2	1	Peter Welch	Peter		Welch			SD-VT	0	Peter_Welch	9959484	51272	210068	N00000515	ctbezjsi	2024-09-29 21:57:08.006609	2024-09-29 21:02:48
9004	52	2	1	Tammy Baldwin	Tammy		Baldwin			SD-WI	0	Tammy_Baldwin	2924660	3470	159127	N00004367	mzzpsyfc	2024-09-29 21:57:08.014527	2024-09-29 21:02:48
9047	52	2	1	Kirsten Gillibrand	Kirsten	E.	Gillibrand			SD-NY	0	Kirsten_Gillibrand	1577524	65147	248345	N00027658	qm3c1xjn	2024-09-29 21:57:08.02491	2024-09-29 21:02:48
9057	52	2	1	Martin Heinrich	Martin		Heinrich			SD-NM	0	Martin_Heinrich	8939798	74517	266934	N00029835	xtyb5c1g	2024-09-29 21:57:08.033898	2024-09-29 21:02:48
9061	52	2	1	Mazie Hirono	Mazie	K.	Hirono			SD-HI	0	Mazie_Hirono	6401094	1677	248294	N00028139	yqm2ur4v	2024-09-29 21:57:08.041473	2024-09-29 21:02:48
9107	52	2	1	Gary Peters	Gary	C.	Peters			SD-MI	0	Gary_Peters	363232	8749	195614	N00029277	n0hm1fke	2024-09-29 21:57:08.055654	2024-09-29 21:02:48
9141	52	2	1	Chris Van Hollen	Chris		Van Hollen			SD-MD	0	Chris_Van_Hollen	5552236	6098	195215	N00013820	52gl0w7n	2024-09-29 21:57:08.064106	2024-09-29 21:02:48
9172	52	2	2	Marsha Blackburn	Marsha		Blackburn			SD-TN	0	Marsha_Blackburn	6654369	25186	198986	N00003105	e1pw64ek	2024-09-29 21:57:08.07117	2024-09-29 21:02:48
9210	52	2	2	John Boozman	John		Boozman			SD-AR	0	John_Boozman	9687692	27958	209930	N00013873	jdd9osw6	2024-09-29 21:57:08.078236	2024-09-29 21:02:48
9212	52	2	2	Shelley Capito	Shelley	Moore	Capito			SD-WV	0	Shelley_Moore_Capito	6651319	11701	200084	N00009771	l1ed938k	2024-09-29 21:57:08.085318	2024-09-29 21:02:48
9255	52	2	2	Bill Cassidy	Bill		Cassidy			SD-LA	0	Bill_Cassidy	6673315	69494	266763	N00030245	8t4a6t34	2024-09-29 21:57:08.092504	2024-09-29 21:02:48
9296	52	2	2	Cynthia Lummis	Cynthia	M.	Lummis			SD-WY	0	Cynthia_Lummis	6365823	15546	240578	N00029788	ca5denhm	2024-09-29 21:57:08.099584	2024-09-29 21:02:48
9305	52	2	2	Jerry Moran	Jerry		Moran			SD-KS	0	Jerry_Moran	19889609	542	158858	N00005282	t3dzh81l	2024-09-29 21:57:08.107335	2024-09-29 21:02:48
9403	52	2	1	Robert Casey	Robert	P.	Casey	Jr.	Bob	SD-PA	0	Robert_Casey_(Pennsylvania)	5967054	2541	240529	N00027503	dbwfjn2h	2024-09-29 21:57:08.123068	2024-09-29 21:02:48
9405	52	2	1	Richard Durbin	Richard		Durbin			SD-IL	0	Dick_Durbin	3414130	26847	165219	N00004981	i4x14koe	2024-09-29 21:57:08.130015	2024-09-29 21:02:48
9408	52	2	1	Amy Klobuchar	Amy		Klobuchar			SD-MN	0	Amy_Klobuchar	17659011	65092	248506	N00027500	r7nps3ip	2024-09-29 21:57:08.137399	2024-09-29 21:02:48
9413	52	2	1	Robert Menendez	Robert		Menendez			SD-NJ	0	Bob_Menendez	17659015	26961	158964	N00000699	fpzplzoq	2024-09-29 21:57:08.145472	2024-09-29 21:02:48
9414	52	2	1	Charles Schumer	Charles	E.	Schumer		Chuck	SD-NY	0	Chuck_Schumer	19890086	26976	165260	N00001093	5pzkxb3w	2024-09-29 21:57:08.155944	2024-09-29 21:02:48
9415	52	2	1	Debbie Stabenow	Debbie		Stabenow			SD-MI	0	Debbie_Stabenow	10688869	515	205511	N00004118	m7c3vp1o	2024-09-29 21:57:08.164243	2024-09-29 21:02:48
9417	52	2	1	Ron Wyden	Ron		Wyden			SD-OR	0	Ron_Wyden	5397600	27036	165265	N00007724	9kl7g1rn	2024-09-29 21:57:08.171823	2024-09-29 21:02:48
9422	52	2	1	Jeanne Shaheen	Jeanne		Shaheen			SD-NH	0	Jeanne_Shaheen	2227644	1663	209675	N00024790	cleoh36j	2024-09-29 21:57:08.179099	2024-09-29 21:02:48
9425	52	2	1	Thomas Carper	Thomas	R.	Carper			SD-DE	0	Tom_Carper	8428238	22421	205484	N00012508	dayilu15	2024-09-29 21:57:08.186264	2024-09-29 21:02:48
9427	52	2	1	Maria Cantwell	Maria		Cantwell			SD-WA	0	Maria_Cantwell	3465258	27122	205537	N00007836	ajo63a1r	2024-09-29 21:57:08.195589	2024-09-29 21:02:48
9431	52	2	1	Patty Murray	Patty		Murray			SD-WA	0	Patty_Murray	18930579	53358	165286	N00007876	y4pijgni	2024-09-29 21:57:08.203321	2024-09-29 21:02:48
9434	52	2	3	Bernard Sanders	Bernard		Sanders			SD-VT	0	Bernie_Sanders	9960190	27110	159116	N00000528	tz8vuv7x	2024-09-29 21:57:08.213249	2024-09-29 21:02:48
9441	52	2	1	Benjamin Cardin	Benjamin	L.	Cardin			SD-MD	0	Ben_Cardin	8046162	26888	158887	N00001955	m9ujezsn	2024-09-29 21:57:08.222032	2024-09-29 21:02:48
9443	52	2	1	Sheldon Whitehouse	Sheldon		Whitehouse			SD-RI	0	Sheldon_Whitehouse	373538	2572	248425	N00027533	jgbb1oef	2024-09-29 21:57:08.229287	2024-09-29 21:02:48
9444	52	2	2	John Cornyn	John		Cornyn			SD-TX	0	John_Cornyn	6646197	15375	211675	N00024852	0ie58qto	2024-09-29 21:57:08.236776	2024-09-29 21:02:48
9445	52	2	2	Mike Crapo	Mike		Crapo			SD-ID	0	Mike_Crapo	19890076	26830	165218	N00006267	f2k79x2t	2024-09-29 21:57:08.244004	2024-09-29 21:02:48
9459	52	2	2	Susan Collins	Susan	M.	Collins			SD-ME	0	Susan_Collins_(Maine)	10045641	379	165234	N00000491	f0qn5jvf	2024-09-29 21:57:08.251223	2024-09-29 21:02:48
9460	52	2	1	Jack Reed	Jack		Reed			SD-RI	0	Jack_Reed	5584992	27060	165269	N00000362	glri16zi	2024-09-29 21:57:08.261941	2024-09-29 21:02:48
9463	52	2	1	Michael Bennet	Michael	F.	Bennet			SD-CO	0	Michael_Bennet	5995587	110942	274906	N00030608	ldf3b0fy	2024-09-29 21:57:08.27252	2024-09-29 21:02:48
9469	52	2	1	Jeff Merkley	Jeff		Merkley			SD-OR	0	Jeff_Merkley	13005237	23644	198129	N00029303	58q1t500	2024-09-29 21:57:08.279488	2024-09-29 21:02:48
9471	52	2	1	Jon Tester	Jon		Tester			SD-MT	0	Jon_Tester	7974707	20928	196276	N00027605	61xtznm6	2024-09-29 21:57:08.287523	2024-09-29 21:02:48
9473	52	2	1	Mark Warner	Mark	R.	Warner			SD-VA	0	Mark_Warner	6003122	535	210000	N00002097	2xdc4klw	2024-09-29 21:57:08.295327	2024-09-29 21:02:48
9483	52	2	2	John Barrasso	John		Barrasso			SD-WY	0	John_Barrasso	10154698	52662	214311	N00006236	sjcjzxst	2024-09-29 21:57:08.302487	2024-09-29 21:02:48
9484	52	2	2	Chuck Grassley	Chuck		Grassley			SD-IA	0	Chuck_Grassley	6338995	53293	165215	N00001758	1zy2f3m5	2024-09-29 21:57:08.312271	2024-09-29 21:02:48
9491	52	2	2	Lisa Murkowski	Lisa		Murkowski			SD-AK	0	Lisa_Murkowski	6604204	15841	192554	N00026050	isieh7x3	2024-09-29 21:57:08.327911	2024-09-29 21:02:48
9492	52	2	2	John Thune	John		Thune			SD-SD	0	John_Thune	19897787	398	159061	N00004572	xyfooh2c	2024-09-29 21:57:08.335615	2024-09-29 21:02:48
9493	52	2	2	Roger Wicker	Roger	F.	Wicker			SD-MS	0	Roger_Wicker	17659028	21926	158928	N00003280	cabmgf99	2024-09-29 21:57:08.342539	2024-09-29 21:02:48
9496	52	2	2	James Risch	James	E.	Risch			SD-ID	0	Jim_Risch	6576171	2919	213702	N00029441	gcopvn6m	2024-09-29 21:57:08.349406	2024-09-29 21:02:48
9497	52	2	2	Mitch McConnell	Mitch		McConnell			SD-KY	0	Mitch_McConnell	9284790	53298	165225	N00003389	qbqukfax	2024-09-29 21:57:08.356744	2024-09-29 21:02:48
9624	52	2	1	Christopher Coons	Christopher	A.	Coons			SD-DE	0	Chris_Coons	5584171	122834	286419	N00031820	rsz1qtnd	2024-09-29 21:57:08.364696	2024-09-29 21:02:48
9625	52	2	1	Joe Manchin	Joe		Manchin	III		SD-WV	0	Joe_Manchin_III	7573477	7547	219013	N00032838	7pac6cxl	2024-09-29 21:57:08.372782	2024-09-29 21:02:48
11061	52	2	2	James Lankford	James		Lankford			SD-OK	0	James_Lankford	17657561	124938	284972	N00031129	r3ltpj5e	2024-09-29 21:57:08.379775	2024-09-29 21:02:48
11074	52	2	2	Tim Scott	Tim		Scott			SD-SC	0	Tim_Scott	6644860	11940	272024	N00031782	68wregy0	2024-09-29 21:57:08.386945	2024-09-29 21:02:48
11080	52	2	2	Todd Young	Todd	C.	Young			SD-IN	0	Todd_Young	7157141	120345	284637	N00030670	t1iqdrnz	2024-09-29 21:57:08.39388	2024-09-29 21:02:48
11199	52	2	1	Richard Blumenthal	Richard		Blumenthal			SD-CT	0	Richard_Blumenthal	6378136	1568	218586	N00031685	crmbr7rg	2024-09-29 21:57:08.401447	2024-09-29 21:02:48
11893	52	2	2	Rand Paul	Rand		Paul			SD-KY	0	Rand_Paul	9337758	117285	285781	N00030836	kj744t8v	2024-09-29 21:57:08.413513	2024-09-29 21:02:48
11907	52	2	2	Ron Johnson	Ron		Johnson			SD-WI	0	Ron_Johnson_(Wisconsin)	2938769	126217	309565	N00032546	xt753gnn	2024-09-29 21:57:08.421037	2024-09-29 21:02:48
11909	52	2	2	Mike Lee	Mike		Lee			SD-UT	0	Mike_Lee_(Utah)	19890610	66395	268656	N00031696	yhq11h7j	2024-09-29 21:57:08.428161	2024-09-29 21:02:48
11910	52	2	2	Marco Rubio	Marco		Rubio			SD-FL	0	Marco_Rubio	12999040	1601	193597	N00030612	8u29wj1z	2024-09-29 21:57:08.435547	2024-09-29 21:02:48
11971	52	2	2	John Hoeven	John		Hoeven			SD-ND	0	John_Hoeven	144736	41788	209683	N00031688	iwcgtwmm	2024-09-29 21:57:08.444339	2024-09-29 21:02:48
14081	52	2	1	Brian Schatz	Brian		Schatz			SD-HI	0	Brian_Schatz	6397188	17852	193945	N00028138	uqrd4tgh	2024-09-29 21:57:08.452912	2024-09-29 21:02:48
14887	52	2	2	Tom Cotton	Tom		Cotton			SD-AR	0	Tom_Cotton	13607871	135651	378517	N00033363	zd3asd1k	2024-09-29 21:57:08.460258	2024-09-29 21:02:48
14888	52	2	2	Kevin Cramer	Kevin		Cramer			SD-ND	0	Kevin_Cramer	13010662	444	240471	N00004614	00ti0jne	2024-09-29 21:57:08.467464	2024-09-29 21:02:48
14889	52	2	2	Steve Daines	Steve		Daines			SD-MT	0	Steve_Daines	7687176	135720	378524	N00033054	tc69v8nn	2024-09-29 21:57:08.474721	2024-09-29 21:02:48
14903	52	2	2	Markwayne Mullin	Markwayne		Mullin			SD-OK	0	Markwayne_Mullin	12013169	135898	378700	N00033410	cosc4d3k	2024-09-29 21:57:08.482389	2024-09-29 21:02:48
15053	52	2	1	Tammy Duckworth	Tammy		Duckworth			SD-IL	0	Tammy_Duckworth	17658669	57442	264841	N00027860	k23gdpqr	2024-09-29 21:57:08.490157	2024-09-29 21:02:48
15237	52	2	3	Kyrsten Sinema	Kyrsten	Lee	Sinema			SD-AZ	0	Kyrsten_Sinema	6459171	28338	227495	N00033983	ebb3e9rf	2024-09-29 21:57:08.497522	2024-09-29 21:02:48
15313	52	2	2	Ted Cruz	Ted		Cruz			SD-TX	0	Ted_Cruz	210204	135705	378522	N00033085	kkwugc78	2024-09-29 21:57:08.504695	2024-09-29 21:02:48
15315	52	2	2	Deb Fischer	Deb		Fischer			SD-NE	0	Deb_Fischer	13012823	41963	228296	N00033443	gjw81slg	2024-09-29 21:57:08.512699	2024-09-29 21:02:48
15348	52	2	3	Angus King	Angus	S.	King	Jr.		SD-ME	0	Angus_King	1792907	22381	209655	N00034580	ov53d9s8	2024-09-29 21:57:08.528612	2024-09-29 21:02:48
15350	52	2	1	Elizabeth Warren	Elizabeth		Warren			SD-MA	0	Elizabeth_Warren	1789719	141272	309189	N00033492	18701e4h	2024-09-29 21:57:08.537375	2024-09-29 21:02:48
15418	52	2	1	Tim Kaine	Tim		Kaine			SD-VA	0	Tim_Kaine	5743146	50772	140385	N00033177	0wvwru9t	2024-09-29 21:57:08.544366	2024-09-29 21:02:48
8963	52	1	1	Kathy Castor	Kathy		Castor			HD-FL-14	0	Kathy_Castor	170335	53825	248289	N00027514	lghvcrvx	2024-09-29 21:51:08.176441	2024-09-29 20:55:51
9068	52	1	1	Sheila Jackson-Lee	Sheila		Jackson-Lee			HD-TX-18	0	Sheila_Jackson_Lee	6716263	21692	159088	N00005818	ludkkyov	2024-09-29 21:51:08.383008	2024-09-29 20:55:51
9161	52	1	1	Gregory Meeks	Gregory	W.	Meeks			HD-NY-5	0	Gregory_Meeks	17658810	4360	158975	N00001171	7h209b0k	2024-09-29 21:51:08.566349	2024-09-29 20:55:52
9176	52	1	2	Michael Burgess	Michael	C.	Burgess			HD-TX-26	0	Michael_Burgess	17658442	50120	211708	N00025219	cu7fgqvh	2024-09-29 21:51:08.594901	2024-09-29 20:54:53
11129	52	1	2	Charles Fleischmann	Charles	J.	Fleischmann		Chuck	HD-TN-3	0	Charles_Fleischmann	9391800	123456	285119	N00030815	4rsz141z	2024-09-29 21:51:08.949261	2024-09-29 20:55:52
13869	52	1	1	Suzanne Bonamici	Suzanne		Bonamici			HD-OR-1	0	Suzanne_Bonamici	339835	59641	249764	N00033474	zwfqam9j	2024-09-29 21:51:09.039497	2024-09-29 20:55:52
16037	52	1	2	Jason Smith	Jason	T.	Smith			HD-MO-8	0	Jason_Smith_(Missouri_representative)	6669122	59318	243054	N00035282	ncwbj52d	2024-09-29 21:51:09.323823	2024-09-29 20:55:53
16488	52	1	1	Don Beyer	Don	S.	Beyer	Jr.		HD-VA-8	0	Don_Beyer	1579842	1707	487540	N00036018	g9uiscjq	2024-09-29 21:51:09.520039	2024-09-29 20:55:53
16502	52	1	1	Debbie Dingell	Debbie		Dingell			HD-MI-6	0	Debbie_Dingell	252193	152482	357079	N00036149	eac0mgw7	2024-09-29 21:51:09.586395	2024-09-29 20:55:53
18411	52	1	2	Jenniffer Gonzalez-Colon	Jenniffer		Gonzalez-Colon			HD-PR	0	Jenniffer_Gonz%C3%A1lez-Col%C3%B3n	0	47514	221612	N00037615	k3rdw8m0	2024-09-29 21:51:09.886826	2024-09-29 20:55:54
20042	52	1	2	James Baird	James	R.	Baird		Jim	HD-IN-4	0	James_Baird	6682179	86013	291484	N00041954	n6smy528	2024-09-29 21:51:09.995482	2024-09-29 20:55:54
20078	52	1	1	Suzanne Lee	Suzanne	Kelley	Lee		Susie	HD-NV-3	0	Susie_Lee	9713907	169344	541030	N00037247	3v5vyjqg	2024-09-29 21:51:10.246115	2024-09-29 20:55:54
21385	52	1	2	Dan Bishop	James	Daniel	Bishop		Dan	HD-NC-8	0	Dan_Bishop	92423	16777215	488139	N00044335	ghemfd9a	2024-09-29 21:51:10.50531	2024-09-29 20:55:55
21925	52	1	2	Jay Obernolte	Jay	P.	Obernolte			HD-CA-23	0	Jay_Obernolte	13479345	151831	494135	N00045377	l4oudi6e	2024-09-29 21:51:10.571876	2024-09-29 20:55:55
21977	52	1	2	Scott Fitzgerald	Scott	L.	Fitzgerald			HD-WI-5	0	Scott_Fitzgerald	13013877	3446	199880	N00045434	udjuvnqs	2024-09-29 21:51:10.912297	2024-09-29 20:55:55
23161	52	1	2	Mike Flood	Mike		Flood			HD-NE-1	0	Mike_Flood	6560805	41983	227029	         	hj4ydmhp	2024-09-29 21:51:10.971322	2024-09-29 20:55:55
24020	52	1	1	Robert Garcia	Robert		Garcia			HD-CA-42	0	Robert_Garcia_(California)	0	29749	0	         	43tsyjhu	2024-09-29 21:51:11.174224	2024-09-29 20:55:56
9402	52	2	1	Sherrod Brown	Sherrod		Brown			SD-OH	0	Sherrod_Brown	3439679	27018	159013	N00003535	bsdo1kgr	2024-09-29 21:57:08.114409	2024-09-29 21:02:48
9488	52	2	2	Lindsey Graham	Lindsey		Graham			SD-SC	0	Lindsey_Graham	8463292	21992	159057	N00009975	vxlaliuo	2024-09-29 21:57:08.320963	2024-09-29 21:02:48
16055	52	2	1	Cory Booker	Cory	A.	Booker			SD-NJ	0	Cory_Booker	1987417	76151	462025	N00035267	39h7tph8	2024-09-29 21:57:08.551346	2024-09-29 21:02:48
16519	52	2	2	Joni Ernst	Joni		Ernst			SD-IA	0	Joni_Ernst	6151700	128583	328986	N00035483	39r6j2zz	2024-09-29 21:57:08.559463	2024-09-29 21:02:48
16521	52	2	2	Mike Rounds	Mike		Rounds			SD-SD	0	Mike_Rounds	6580808	7455	198882	N00035187	0gww5x7w	2024-09-29 21:57:08.566621	2024-09-29 21:02:48
16523	52	2	2	Dan Sullivan	Dan		Sullivan			SD-AK	0	Daniel_S._Sullivan	39833727	114964	328336	N00035774	urkh79kr	2024-09-29 21:57:08.574084	2024-09-29 21:02:48
16524	52	2	2	Thom Tillis	Thom		Tillis			SD-NC	0	Thom_Tillis_(North_Carolina)	5942566	57717	250143	N00035492	gt38jrsy	2024-09-29 21:57:08.581505	2024-09-29 21:02:48
18294	52	2	2	Ted Budd	Ted		Budd			SD-NC	0	Ted_Budd	40620470	171489	576530	N00039551	7hm53cv6	2024-09-29 21:57:08.588943	2024-09-29 21:02:48
18320	52	2	2	Roger Marshall	Roger	W.	Marshall			SD-KS	0	Roger_Marshall	8816503	172080	536160	N00037034	foub2xo0	2024-09-29 21:57:08.59665	2024-09-29 21:02:48
18329	52	2	1	Jacky Rosen	Jacky		Rosen			SD-NV	0	Jacky_Rosen	39827617	169471	567336	N00038734	jgkrx0ce	2024-09-29 21:57:08.603737	2024-09-29 21:02:48
18413	52	2	2	John Kennedy	John		Kennedy			SD-LA	0	John_Neely_Kennedy	13010864	35496	240389	N00026823	i8432eqr	2024-09-29 21:57:08.610606	2024-09-29 21:02:49
18485	52	2	1	Catherine Cortez Masto	Catherine		Cortez Masto			SD-NV	0	Catherine_Cortez_Masto	13010255	69579	252293	N00037161	no060koh	2024-09-29 21:57:08.623021	2024-09-29 21:02:49
18486	52	2	1	Margaret Hassan	Margaret	Wood	Hassan			SD-NH	0	Maggie_Hassan	9693318	42552	227982	N00038397	8009qp8o	2024-09-29 21:57:08.640817	2024-09-29 21:02:49
19499	52	2	1	Tina Smith	Tina		Smith			SD-MN	0	Tina_Smith	4173995	152968	332335	N00042353	xk4y3m3y	2024-09-29 21:57:08.648493	2024-09-29 21:02:49
19622	52	2	2	Cindy Hyde-Smith	Cindy		Hyde-Smith			SD-MS	0	Cindy_Hyde-Smith	6408036	20784	196212	N00043298	0ya4l9wg	2024-09-29 21:57:08.655344	2024-09-29 21:02:49
20294	52	2	2	Mike Braun	Mike		Braun			SD-IN	0	Mike_Braun	21084493	148564	484213	N00041731	1lllgwva	2024-09-29 21:57:08.662606	2024-09-29 21:02:49
20295	52	2	2	Josh Hawley	Joshua	David	Hawley		Josh	SD-MO	0	Josh_Hawley	16205449	169716	572072	N00041620	r2b3zv8g	2024-09-29 21:57:08.669635	2024-09-29 21:02:49
20296	52	2	2	Mitt Romney	Willard	Mitt	Romney		Mitt	SD-UT	0	Mitt_Romney	43351	21942	213247	N00000286	ha9dgec0	2024-09-29 21:57:08.676973	2024-09-29 21:02:49
20297	52	2	2	Rick Scott	Richard	L.	Scott		Rick	SD-FL	0	Rick_Scott	422306	124204	289276	N00043290	9aqi5rh3	2024-09-29 21:57:08.684051	2024-09-29 21:02:49
21702	52	2	1	Mark Kelly	Mark		Kelly			SD-AZ	0	Mark_Kelly	48160599	190594	709398	N00044223	c8fd3zmw	2024-09-29 21:57:08.6915	2024-09-29 21:02:49
22003	52	2	2	Tommy Tuberville	Thomas	H.	Tuberville		Tommy	SD-AL	0	Tommy_Tuberville	48161175	188306	703296	N00044434	uikvpmn3	2024-09-29 21:57:08.699139	2024-09-29 21:02:49
22004	52	2	1	John Hickenlooper	John	W.	Hickenlooper			SD-CO	0	John_Hickenlooper	6001155	71547	288619	N00044206	jm9d1r57	2024-09-29 21:57:08.707009	2024-09-29 21:02:49
22005	52	2	2	Bill Hagerty	William	F.	Hagerty	IV	Bill	SD-TN	0	Bill_Hagerty	2170351	128466	333606	N00045369	n83iln24	2024-09-29 21:57:08.714904	2024-09-29 21:02:49
22485	52	2	1	Jon Ossoff	Thomas	Jonathan	Ossoff		Jon	SD-GA	0	Jon_Ossoff	43492014	176134	251917	N00040675	qvqzpvm8	2024-09-29 21:57:08.721922	2024-09-29 21:02:49
22486	52	2	1	Alex Padilla	Alex		Padilla			SD-CA	0	Alex_Padilla	6468901	59742	248511	N00047888	xs0w7jfs	2024-09-29 21:57:08.730503	2024-09-29 21:02:49
22487	52	2	1	Raphael Warnock	Raphael	G.	Warnock			SD-GA	0	Raphael_Warnock	18063880	189794	730636	N00046489	5yderwpg	2024-09-29 21:57:08.737516	2024-09-29 21:02:49
24548	52	2	2	Katie Boyd Britt	Katie		Boyd Britt			SD-AL	0	Katie_Britt	0	201704	596651	         	fqwttmu8	2024-09-29 21:57:08.744966	2024-09-29 21:02:49
24549	52	2	1	John Fetterman	John	K.	Fetterman			SD-PA	0	John_Fetterman	15982010	166286	552695	         	fiejoqwt	2024-09-29 21:57:08.752103	2024-09-29 21:02:49
24828	52	2	2	J.D. Vance	J.D.		Vance			SD-OH	0	J.D._Vance	0	201794	781111	         	va2e2x80	2024-09-29 21:57:08.759396	2024-09-29 21:02:49
24863	52	2	2	Pete Ricketts	John	Peter	Ricketts		Pete	SD-NE	0	Pete_Ricketts	5723939	57777	0	         	22ao4tcr	2024-09-29 21:57:08.766367	2024-09-29 21:02:49
24864	52	2	2	Eric Schmitt	Eric		Schmitt			SD-MO	0	Eric_Schmitt	6676482	150182	229398	         	1pl5bq82	2024-09-29 21:57:08.781061	2024-09-29 21:02:49
24958	52	2	1	Laphonza Butler	Laphonza		Butler			SD-CA	0	Laphonza_Butler	0	212818	0	         	myaar9k0	2024-09-29 21:57:08.788137	2024-09-29 21:02:49
25216	52	1	1	LaMonica McIver	LaMonica		McIver			HD-NJ-10	0	LaMonica_McIver	0	186801	0	         	k7tkktgp	2024-09-29 22:08:10.221783	2024-09-29 21:16:20
9423	52	2	1	Dianne Feinstein	Dianne		Feinstein			SD-CA	0	Dianne_Feinstein	26294	53273	165201	N00007364	mswz9g79	2024-09-29 22:10:06.33006	2024-09-29 21:18:53
25215	52	2	1	George Helmy	George	S.	Helmy			SD-NJ	0	George_Helmy	0	219660	0	         	j43vfj4t	2024-09-29 22:38:08	2024-09-29 22:38:08
\.


--
-- Data for Name: ls_progress; Type: TABLE DATA; Schema: public; Owner: legiscan_api
--

COPY public.ls_progress (progress_event_id, progress_desc) FROM stdin;
0	Prefiled
1	Introduced
2	Engrossed
3	Enrolled
4	Passed
5	Vetoed
6	Failed
7	Override
8	Chaptered
9	Refer
10	Report Pass
11	Report DNP
12	Draft
\.


--
-- Data for Name: ls_reason; Type: TABLE DATA; Schema: public; Owner: legiscan_api
--

COPY public.ls_reason (reason_id, reason_desc) FROM stdin;
1	NewBill
2	StatusChange
3	Chamber
4	Complete
5	Title
6	Description
7	CommRefer
8	CommReport
9	SponsorAdd
10	SponsorRemove
11	SponsorChange
12	HistoryAdd
13	HistoryRemove
14	HistoryRevised
15	HistoryMajor
16	HistoryMinor
17	SubjectAdd
18	SubjectRemove
19	SAST
20	Text
21	Amendment
22	Supplement
23	Vote
24	Calendar
25	Progress
26	VoteUpdate
27	TextUpdate
99	ICBM
\.


--
-- Data for Name: ls_role; Type: TABLE DATA; Schema: public; Owner: legiscan_api
--

COPY public.ls_role (role_id, role_name, role_abbr) FROM stdin;
1	Representative	Rep
2	Senator	Sen
3	Joint Conference	Jnt
\.


--
-- Data for Name: ls_sast_type; Type: TABLE DATA; Schema: public; Owner: legiscan_api
--

COPY public.ls_sast_type (sast_id, sast_description) FROM stdin;
1	Same As
2	Similar To
3	Replaced by
4	Replaces
5	Crossfiled
6	Enabling for
7	Enabled by
8	Related
9	Carry Over
\.


--
-- Data for Name: ls_session; Type: TABLE DATA; Schema: public; Owner: legiscan_api
--

COPY public.ls_session (session_id, state_id, year_start, year_end, prefile, sine_die, prior, special, session_name, session_title, session_tag, import_date, import_hash) FROM stdin;
2041	52	2023	2024	0	0	0	0	118th Congress	2023-2024 Regular Session	Regular Session	2024-09-29	4b1509ea9155f2bc43721b210416f84e
\.


--
-- Data for Name: ls_signal; Type: TABLE DATA; Schema: public; Owner: legiscan_api
--

COPY public.ls_signal (object_type, object_id, processed, updated, created) FROM stdin;
\.


--
-- Data for Name: ls_sponsor_type; Type: TABLE DATA; Schema: public; Owner: legiscan_api
--

COPY public.ls_sponsor_type (sponsor_type_id, sponsor_type_desc) FROM stdin;
0	Sponsor
1	Primary Sponsor
2	Co-Sponsor
3	Joint Sponsor
\.


--
-- Data for Name: ls_stance; Type: TABLE DATA; Schema: public; Owner: legiscan_api
--

COPY public.ls_stance (stance, stance_desc) FROM stdin;
0	Watch
1	Support
2	Oppose
\.


--
-- Data for Name: ls_state; Type: TABLE DATA; Schema: public; Owner: legiscan_api
--

COPY public.ls_state (state_id, state_abbr, state_name, biennium, carry_over, capitol, latitude, longitude) FROM stdin;
1	AL	Alabama	0	NO	Montgomery	32.377716	-86.300489
2	AK	Alaska	1	OE	Juneau	58.301105	-134.412957
3	AZ	Arizona	0	NO	Phoenix	33.448113	-112.097037
4	AR	Arkansas	0	NO	Little Rock	34.746361	-92.289422
5	CA	California	1	OE	Sacramento	38.576700	-121.493766
6	CO	Colorado	0	NO	Denver	39.739276	-104.984848
7	CT	Connecticut	0	NO	Hartford	41.762831	-72.682383
8	DE	Delaware	1	OE	Dover	39.157354	-75.519570
9	FL	Florida	0	NO	Tallahassee	30.438086	-84.282196
10	GA	Georgia	1	OE	Atlanta	33.749035	-84.388195
11	HI	Hawaii	0	OE	Honolulu	21.294786	-157.858818
12	ID	Idaho	0	NO	Boise	43.617850	-116.199940
13	IL	Illinois	1	OE	Springfield	39.798358	-89.654972
14	IN	Indiana	0	NO	Indianapolis	39.768590	-86.162634
15	IA	Iowa	1	OE	Des Moines	41.591183	-93.603694
16	KS	Kansas	1	OE	Topeka	39.048070	-95.678080
17	KY	Kentucky	0	NO	Frankfort	38.186658	-84.875265
18	LA	Louisiana	0	NO	Baton Rouge	30.456615	-91.187356
19	ME	Maine	1	OE	Augusta	44.307185	-69.781390
20	MD	Maryland	0	NO	Annapolis	38.978862	-76.490685
21	MA	Massachusetts	1	OE	Boston	42.358424	-71.063701
22	MI	Michigan	1	OE	Lansing	42.733470	-84.555300
23	MN	Minnesota	1	OE	Saint Paul	44.948232	-93.105406
24	MS	Mississippi	0	NO	Jackson	32.303799	-90.182005
25	MO	Missouri	0	NO	Jefferson City	38.579206	-92.173019
26	MT	Montana	0	NO	Helena	46.585774	-112.018180
27	NE	Nebraska	1	OE	Lincoln	40.807935	-96.699655
28	NV	Nevada	0	NO	Carson City	39.164009	-119.766153
29	NH	New Hampshire	0	OE	Concord	43.206854	-71.537659
30	NJ	New Jersey	1	EO	Trenton	40.220280	-74.770140
31	NM	New Mexico	0	NO	Santa Fe	35.682440	-105.940074
32	NY	New York	1	OE	Albany	40.771120	-73.974190
33	NC	North Carolina	1	OE	Raleigh	35.780498	-78.639110
34	ND	North Dakota	1	NO	Bismarck	46.820900	-100.781955
35	OH	Ohio	1	OE	Columbus	39.961392	-82.999065
36	OK	Oklahoma	0	OE	Oklahoma City	35.492320	-97.503340
37	OR	Oregon	0	NO	Salem	44.938361	-123.030155
38	PA	Pennsylvania	1	OE	Harrisburg	40.264330	-76.883521
39	RI	Rhode Island	0	OE	Providence	41.831097	-71.414883
40	SC	South Carolina	1	OE	Columbia	34.000386	-81.033210
41	SD	South Dakota	0	NO	Pierre	44.367630	-100.346040
42	TN	Tennessee	1	OE	Nashville	36.166011	-86.784297
43	TX	Texas	1	NO	Austin	30.274001	-97.740631
44	UT	Utah	0	NO	Salt Lake City	40.777200	-111.888280
45	VT	Vermont	1	OE	Montpelier	44.262141	-72.580716
46	VA	Virginia	0	EO	Richmond	37.538783	-77.433449
47	WA	Washington	1	OE	Olympia	47.035964	-122.904799
48	WV	West Virginia	0	OE	Charleston	38.336166	-81.612186
49	WI	Wisconsin	1	OE	Madison	43.074530	-89.384120
50	WY	Wyoming	0	NO	Cheyenne	41.140101	-104.820112
51	DC	Washington D.C.	1	OE	Washington, DC	38.894825	-77.031338
52	US	US Congress	1	OE	Washington, DC	38.889873	-77.008823
\.


--
-- Data for Name: ls_subject; Type: TABLE DATA; Schema: public; Owner: legiscan_api
--

COPY public.ls_subject (subject_id, state_id, subject_name) FROM stdin;
13399	52	Energy
13346	52	Immigration
13329	52	Education
13304	52	Health
13356	52	Government operations and politics
13321	52	Civil rights and liberties, minority issues
13328	52	Labor and employment
13338	52	Taxation
13477	52	Finance and financial sector
13340	52	Crime and law enforcement
13358	52	Armed forces and national security
13513	52	Science, technology, communications
13422	52	International affairs
13377	52	Native Americans
13375	52	Housing and community development
13383	52	Social welfare
13404	52	Law
13525	52	Congress
13330	52	Environmental protection
13395	52	Public lands and natural resources
13531	52	Transportation and public works
13597	52	Agriculture and food
13124	52	Economics and public finance
13437	52	Emergency management
13637	52	Commerce
13390	52	Water resources development
13481	52	Animals
13624	52	Arts, culture, religion
13903	52	Social sciences and history
13731	52	Foreign trade and international finance
13700	52	Families
13633	52	Private legislation
13747	52	Sports and recreation
\.


--
-- Data for Name: ls_supplement_type; Type: TABLE DATA; Schema: public; Owner: legiscan_api
--

COPY public.ls_supplement_type (supplement_type_id, supplement_type_desc) FROM stdin;
1	Fiscal Note
2	Analysis
3	Fiscal Note/Analysis
4	Vote Image
5	Local Mandate
6	Corrections Impact
7	Misc
8	Veto Letter
\.


--
-- Data for Name: ls_text_type; Type: TABLE DATA; Schema: public; Owner: legiscan_api
--

COPY public.ls_text_type (bill_text_type_id, bill_text_name, bill_text_sort, bill_text_supplement) FROM stdin;
1	Introduced	2	0
2	Comm Sub	4	0
3	Amended	3	0
4	Engrossed	7	0
5	Enrolled	8	0
6	Chaptered	9	0
7	Fiscal Note	0	1
8	Analysis	0	1
9	Draft	1	0
10	Conference Sub	5	0
11	Prefiled	0	0
12	Veto Message	0	1
13	Veto Response	0	1
14	Substitute	6	0
\.


--
-- Data for Name: ls_type; Type: TABLE DATA; Schema: public; Owner: legiscan_api
--

COPY public.ls_type (bill_type_id, bill_type_name, bill_type_abbr) FROM stdin;
1	Bill	B
2	Resolution	R
3	Concurrent Resolution	CR
4	Joint Resolution	JR
5	Joint Resolution Constitutional Amendment	JRCA
6	Executive Order	EO
7	Constitutional Amendment	CA
8	Memorial	M
9	Claim	CL
10	Commendation	C
11	Committee Study Request	CSR
12	Joint Memorial	JM
13	Proclamation	P
14	Study Request	SR
15	Address	A
16	Concurrent Memorial	CM
17	Initiative	I
18	Petition	PET
19	Study Bill	SB
20	Initiative Petition	IP
21	Repeal Bill	RB
22	Remonstration	RM
23	Committee Bill	CB
\.


--
-- Data for Name: ls_variable; Type: TABLE DATA; Schema: public; Owner: legiscan_api
--

COPY public.ls_variable (name, value) FROM stdin;
schema	9
version	"1.4.0"
\.


--
-- Data for Name: ls_vote; Type: TABLE DATA; Schema: public; Owner: legiscan_api
--

COPY public.ls_vote (vote_id, vote_desc) FROM stdin;
1	Yea
2	Nay
3	Not Voting
4	Absent
\.


--
-- Name: ls_bill_amendment ls_bill_amendment_pkey; Type: CONSTRAINT; Schema: public; Owner: legiscan_api
--

ALTER TABLE ONLY public.ls_bill_amendment
    ADD CONSTRAINT ls_bill_amendment_pkey PRIMARY KEY (amendment_id);


--
-- Name: ls_bill_calendar ls_bill_calendar_pkey; Type: CONSTRAINT; Schema: public; Owner: legiscan_api
--

ALTER TABLE ONLY public.ls_bill_calendar
    ADD CONSTRAINT ls_bill_calendar_pkey PRIMARY KEY (bill_id, event_hash);


--
-- Name: ls_bill_history ls_bill_history_pkey; Type: CONSTRAINT; Schema: public; Owner: legiscan_api
--

ALTER TABLE ONLY public.ls_bill_history
    ADD CONSTRAINT ls_bill_history_pkey PRIMARY KEY (bill_id, history_step);


--
-- Name: ls_bill ls_bill_pkey; Type: CONSTRAINT; Schema: public; Owner: legiscan_api
--

ALTER TABLE ONLY public.ls_bill
    ADD CONSTRAINT ls_bill_pkey PRIMARY KEY (bill_id);


--
-- Name: ls_bill_progress ls_bill_progress_pkey; Type: CONSTRAINT; Schema: public; Owner: legiscan_api
--

ALTER TABLE ONLY public.ls_bill_progress
    ADD CONSTRAINT ls_bill_progress_pkey PRIMARY KEY (bill_id, progress_step);


--
-- Name: ls_bill_referral ls_bill_referral_pkey; Type: CONSTRAINT; Schema: public; Owner: legiscan_api
--

ALTER TABLE ONLY public.ls_bill_referral
    ADD CONSTRAINT ls_bill_referral_pkey PRIMARY KEY (bill_id, referral_step);


--
-- Name: ls_bill_sast ls_bill_sast_pkey; Type: CONSTRAINT; Schema: public; Owner: legiscan_api
--

ALTER TABLE ONLY public.ls_bill_sast
    ADD CONSTRAINT ls_bill_sast_pkey PRIMARY KEY (bill_id, sast_type_id, sast_bill_id);


--
-- Name: ls_bill_sponsor ls_bill_sponsor_pkey; Type: CONSTRAINT; Schema: public; Owner: legiscan_api
--

ALTER TABLE ONLY public.ls_bill_sponsor
    ADD CONSTRAINT ls_bill_sponsor_pkey PRIMARY KEY (bill_id, people_id);


--
-- Name: ls_bill_subject ls_bill_subject_pkey; Type: CONSTRAINT; Schema: public; Owner: legiscan_api
--

ALTER TABLE ONLY public.ls_bill_subject
    ADD CONSTRAINT ls_bill_subject_pkey PRIMARY KEY (bill_id, subject_id);


--
-- Name: ls_bill_supplement ls_bill_supplement_pkey; Type: CONSTRAINT; Schema: public; Owner: legiscan_api
--

ALTER TABLE ONLY public.ls_bill_supplement
    ADD CONSTRAINT ls_bill_supplement_pkey PRIMARY KEY (supplement_id);


--
-- Name: ls_bill_text ls_bill_text_pkey; Type: CONSTRAINT; Schema: public; Owner: legiscan_api
--

ALTER TABLE ONLY public.ls_bill_text
    ADD CONSTRAINT ls_bill_text_pkey PRIMARY KEY (text_id);


--
-- Name: ls_bill_vote_detail ls_bill_vote_detail_pkey; Type: CONSTRAINT; Schema: public; Owner: legiscan_api
--

ALTER TABLE ONLY public.ls_bill_vote_detail
    ADD CONSTRAINT ls_bill_vote_detail_pkey PRIMARY KEY (roll_call_id, people_id);


--
-- Name: ls_bill_vote ls_bill_vote_pkey; Type: CONSTRAINT; Schema: public; Owner: legiscan_api
--

ALTER TABLE ONLY public.ls_bill_vote
    ADD CONSTRAINT ls_bill_vote_pkey PRIMARY KEY (roll_call_id);


--
-- Name: ls_body ls_body_pkey; Type: CONSTRAINT; Schema: public; Owner: legiscan_api
--

ALTER TABLE ONLY public.ls_body
    ADD CONSTRAINT ls_body_pkey PRIMARY KEY (body_id);


--
-- Name: ls_committee ls_committee_pkey; Type: CONSTRAINT; Schema: public; Owner: legiscan_api
--

ALTER TABLE ONLY public.ls_committee
    ADD CONSTRAINT ls_committee_pkey PRIMARY KEY (committee_id);


--
-- Name: ls_event_type ls_event_type_pkey; Type: CONSTRAINT; Schema: public; Owner: legiscan_api
--

ALTER TABLE ONLY public.ls_event_type
    ADD CONSTRAINT ls_event_type_pkey PRIMARY KEY (event_type_id);


--
-- Name: ls_ignore ls_ignore_pkey; Type: CONSTRAINT; Schema: public; Owner: legiscan_api
--

ALTER TABLE ONLY public.ls_ignore
    ADD CONSTRAINT ls_ignore_pkey PRIMARY KEY (bill_id);


--
-- Name: ls_mime_type ls_mime_type_pkey; Type: CONSTRAINT; Schema: public; Owner: legiscan_api
--

ALTER TABLE ONLY public.ls_mime_type
    ADD CONSTRAINT ls_mime_type_pkey PRIMARY KEY (mime_id);


--
-- Name: ls_monitor ls_monitor_pkey; Type: CONSTRAINT; Schema: public; Owner: legiscan_api
--

ALTER TABLE ONLY public.ls_monitor
    ADD CONSTRAINT ls_monitor_pkey PRIMARY KEY (bill_id);


--
-- Name: ls_party ls_party_pkey; Type: CONSTRAINT; Schema: public; Owner: legiscan_api
--

ALTER TABLE ONLY public.ls_party
    ADD CONSTRAINT ls_party_pkey PRIMARY KEY (party_id);


--
-- Name: ls_people ls_people_pkey; Type: CONSTRAINT; Schema: public; Owner: legiscan_api
--

ALTER TABLE ONLY public.ls_people
    ADD CONSTRAINT ls_people_pkey PRIMARY KEY (people_id);


--
-- Name: ls_progress ls_progress_pkey; Type: CONSTRAINT; Schema: public; Owner: legiscan_api
--

ALTER TABLE ONLY public.ls_progress
    ADD CONSTRAINT ls_progress_pkey PRIMARY KEY (progress_event_id);


--
-- Name: ls_reason ls_reason_pkey; Type: CONSTRAINT; Schema: public; Owner: legiscan_api
--

ALTER TABLE ONLY public.ls_reason
    ADD CONSTRAINT ls_reason_pkey PRIMARY KEY (reason_id);


--
-- Name: ls_role ls_role_pkey; Type: CONSTRAINT; Schema: public; Owner: legiscan_api
--

ALTER TABLE ONLY public.ls_role
    ADD CONSTRAINT ls_role_pkey PRIMARY KEY (role_id);


--
-- Name: ls_sast_type ls_sast_type_pkey; Type: CONSTRAINT; Schema: public; Owner: legiscan_api
--

ALTER TABLE ONLY public.ls_sast_type
    ADD CONSTRAINT ls_sast_type_pkey PRIMARY KEY (sast_id);


--
-- Name: ls_session ls_session_pkey; Type: CONSTRAINT; Schema: public; Owner: legiscan_api
--

ALTER TABLE ONLY public.ls_session
    ADD CONSTRAINT ls_session_pkey PRIMARY KEY (session_id);


--
-- Name: ls_signal ls_signal_pkey; Type: CONSTRAINT; Schema: public; Owner: legiscan_api
--

ALTER TABLE ONLY public.ls_signal
    ADD CONSTRAINT ls_signal_pkey PRIMARY KEY (object_type, object_id);


--
-- Name: ls_sponsor_type ls_sponsor_type_pkey; Type: CONSTRAINT; Schema: public; Owner: legiscan_api
--

ALTER TABLE ONLY public.ls_sponsor_type
    ADD CONSTRAINT ls_sponsor_type_pkey PRIMARY KEY (sponsor_type_id);


--
-- Name: ls_stance ls_stance_pkey; Type: CONSTRAINT; Schema: public; Owner: legiscan_api
--

ALTER TABLE ONLY public.ls_stance
    ADD CONSTRAINT ls_stance_pkey PRIMARY KEY (stance);


--
-- Name: ls_state ls_state_pkey; Type: CONSTRAINT; Schema: public; Owner: legiscan_api
--

ALTER TABLE ONLY public.ls_state
    ADD CONSTRAINT ls_state_pkey PRIMARY KEY (state_id);


--
-- Name: ls_subject ls_subject_pkey; Type: CONSTRAINT; Schema: public; Owner: legiscan_api
--

ALTER TABLE ONLY public.ls_subject
    ADD CONSTRAINT ls_subject_pkey PRIMARY KEY (subject_id);


--
-- Name: ls_supplement_type ls_supplement_type_pkey; Type: CONSTRAINT; Schema: public; Owner: legiscan_api
--

ALTER TABLE ONLY public.ls_supplement_type
    ADD CONSTRAINT ls_supplement_type_pkey PRIMARY KEY (supplement_type_id);


--
-- Name: ls_text_type ls_text_type_pkey; Type: CONSTRAINT; Schema: public; Owner: legiscan_api
--

ALTER TABLE ONLY public.ls_text_type
    ADD CONSTRAINT ls_text_type_pkey PRIMARY KEY (bill_text_type_id);


--
-- Name: ls_type ls_type_pkey; Type: CONSTRAINT; Schema: public; Owner: legiscan_api
--

ALTER TABLE ONLY public.ls_type
    ADD CONSTRAINT ls_type_pkey PRIMARY KEY (bill_type_id);


--
-- Name: ls_variable ls_variable_pkey; Type: CONSTRAINT; Schema: public; Owner: legiscan_api
--

ALTER TABLE ONLY public.ls_variable
    ADD CONSTRAINT ls_variable_pkey PRIMARY KEY (name);


--
-- Name: ls_vote ls_vote_pkey; Type: CONSTRAINT; Schema: public; Owner: legiscan_api
--

ALTER TABLE ONLY public.ls_vote
    ADD CONSTRAINT ls_vote_pkey PRIMARY KEY (vote_id);


--
-- Name: ls_bill_amendment_bill_id_idx; Type: INDEX; Schema: public; Owner: legiscan_api
--

CREATE INDEX ls_bill_amendment_bill_id_idx ON public.ls_bill_amendment USING btree (bill_id);


--
-- Name: ls_bill_bill_number_idx; Type: INDEX; Schema: public; Owner: legiscan_api
--

CREATE INDEX ls_bill_bill_number_idx ON public.ls_bill USING btree (bill_number);


--
-- Name: ls_bill_reason_bill_id_idx; Type: INDEX; Schema: public; Owner: legiscan_api
--

CREATE INDEX ls_bill_reason_bill_id_idx ON public.ls_bill_reason USING btree (bill_id);


--
-- Name: ls_bill_session_id_idx; Type: INDEX; Schema: public; Owner: legiscan_api
--

CREATE INDEX ls_bill_session_id_idx ON public.ls_bill USING btree (session_id);


--
-- Name: ls_bill_state_id_idx; Type: INDEX; Schema: public; Owner: legiscan_api
--

CREATE INDEX ls_bill_state_id_idx ON public.ls_bill USING btree (state_id);


--
-- Name: ls_bill_supplement_bill_id_idx; Type: INDEX; Schema: public; Owner: legiscan_api
--

CREATE INDEX ls_bill_supplement_bill_id_idx ON public.ls_bill_supplement USING btree (bill_id);


--
-- Name: ls_bill_text_bill_id_idx; Type: INDEX; Schema: public; Owner: legiscan_api
--

CREATE INDEX ls_bill_text_bill_id_idx ON public.ls_bill_text USING btree (bill_id);


--
-- Name: ls_body_body_abbr_idx; Type: INDEX; Schema: public; Owner: legiscan_api
--

CREATE INDEX ls_body_body_abbr_idx ON public.ls_body USING btree (body_abbr);


--
-- Name: ls_body_role_id_idx; Type: INDEX; Schema: public; Owner: legiscan_api
--

CREATE INDEX ls_body_role_id_idx ON public.ls_body USING btree (role_id);


--
-- Name: ls_body_state_id_idx; Type: INDEX; Schema: public; Owner: legiscan_api
--

CREATE INDEX ls_body_state_id_idx ON public.ls_body USING btree (state_id);


--
-- Name: ls_committee_committee_body_id_idx; Type: INDEX; Schema: public; Owner: legiscan_api
--

CREATE INDEX ls_committee_committee_body_id_idx ON public.ls_committee USING btree (committee_body_id);


--
-- Name: ls_people_party_id_idx; Type: INDEX; Schema: public; Owner: legiscan_api
--

CREATE INDEX ls_people_party_id_idx ON public.ls_people USING btree (party_id);


--
-- Name: ls_people_role_id_idx; Type: INDEX; Schema: public; Owner: legiscan_api
--

CREATE INDEX ls_people_role_id_idx ON public.ls_people USING btree (role_id);


--
-- Name: ls_people_state_id_idx; Type: INDEX; Schema: public; Owner: legiscan_api
--

CREATE INDEX ls_people_state_id_idx ON public.ls_people USING btree (state_id);


--
-- Name: ls_state_state_abbr_idx; Type: INDEX; Schema: public; Owner: legiscan_api
--

CREATE INDEX ls_state_state_abbr_idx ON public.ls_state USING btree (state_abbr);


--
-- Name: ls_subject_state_id_idx; Type: INDEX; Schema: public; Owner: legiscan_api
--

CREATE INDEX ls_subject_state_id_idx ON public.ls_subject USING btree (state_id);


--
-- Name: ls_bill_amendment trig_ls_bill_amendment_update; Type: TRIGGER; Schema: public; Owner: legiscan_api
--

CREATE TRIGGER trig_ls_bill_amendment_update BEFORE UPDATE ON public.ls_bill_amendment FOR EACH ROW EXECUTE FUNCTION public.update_ts_column();


--
-- Name: ls_bill_calendar trig_ls_bill_calendar_update; Type: TRIGGER; Schema: public; Owner: legiscan_api
--

CREATE TRIGGER trig_ls_bill_calendar_update BEFORE UPDATE ON public.ls_bill_calendar FOR EACH ROW EXECUTE FUNCTION public.update_ts_column();


--
-- Name: ls_bill_supplement trig_ls_bill_supplement_update; Type: TRIGGER; Schema: public; Owner: legiscan_api
--

CREATE TRIGGER trig_ls_bill_supplement_update BEFORE UPDATE ON public.ls_bill_supplement FOR EACH ROW EXECUTE FUNCTION public.update_ts_column();


--
-- Name: ls_bill_text trig_ls_bill_text_update; Type: TRIGGER; Schema: public; Owner: legiscan_api
--

CREATE TRIGGER trig_ls_bill_text_update BEFORE UPDATE ON public.ls_bill_text FOR EACH ROW EXECUTE FUNCTION public.update_ts_column();


--
-- Name: ls_bill trig_ls_bill_update; Type: TRIGGER; Schema: public; Owner: legiscan_api
--

CREATE TRIGGER trig_ls_bill_update BEFORE UPDATE ON public.ls_bill FOR EACH ROW EXECUTE FUNCTION public.update_ts_column();


--
-- Name: ls_bill_vote trig_ls_bill_vote_update; Type: TRIGGER; Schema: public; Owner: legiscan_api
--

CREATE TRIGGER trig_ls_bill_vote_update BEFORE UPDATE ON public.ls_bill_vote FOR EACH ROW EXECUTE FUNCTION public.update_ts_column();


--
-- Name: ls_people trig_ls_people_update; Type: TRIGGER; Schema: public; Owner: legiscan_api
--

CREATE TRIGGER trig_ls_people_update BEFORE UPDATE ON public.ls_people FOR EACH ROW EXECUTE FUNCTION public.update_ts_column();


--
-- Name: ls_signal trig_ls_signal_update; Type: TRIGGER; Schema: public; Owner: legiscan_api
--

CREATE TRIGGER trig_ls_signal_update BEFORE UPDATE ON public.ls_signal FOR EACH ROW EXECUTE FUNCTION public.update_ts_column();


--
-- Name: SCHEMA public; Type: ACL; Schema: -; Owner: user
--

GRANT CREATE ON SCHEMA public TO legiscan_api;


--
-- PostgreSQL database dump complete
--

