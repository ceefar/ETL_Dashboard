# ---- imports ----
 
# for db connection
import mysql.connector
# for secrets.toml, singleton, & memo
import streamlit as st


# ---- initialize connection ----
# uses st.experimental_singleton to only run once.

@st.experimental_singleton
def init_connection():
    return mysql.connector.connect(**st.secrets["mysql"])

conn = init_connection()


# ---- perform queries ----
# both uses st.experimental_memo to only rerun when the query changes or after 10 min

@st.experimental_memo(ttl=600)
def get_from_db(query):
    """ perform a query that gets from database and returns a value"""
    with conn.cursor() as cur:
        cur.execute(query)
        return cur.fetchall()


@st.experimental_memo(ttl=600)
def add_to_db(query):
    """ performs a query with no return needed """
    with conn.cursor() as cur:
        cur.execute(query)


# ---- end setup ----