# ---- IMPORTS ----

# for web app 
import streamlit as st
import streamlit.components.v1 as stc
from streamlit.errors import StreamlitAPIException
# for date time objects
import datetime # from datetime import datetime
# for db integration
import db_integration as db
# for images and img manipulation
import PIL


# ---- SETUP WEB APP ----

def on_load():
    """ sets the layout default to wide, set page config needs to be the first streamlit action that is run for it to work """
    # potential bug that it sometimes doesn't do this first time round but does when you click a page again (consider re-run to force?)
    st.set_page_config(layout="wide")


# catch error in case that file is reloaded locally meaning app thinks config hasn't run first when it has (may have been snowflake specific so test it)
try: 
    on_load()
except StreamlitAPIException:
    pass


# ---- MAIN WEB APP ----

def run():

    # ---- SIDEBAR ----

    # portfolio/developer mode toggle
    with st.sidebar:
        dev_mode = st.checkbox(label="Portfolio Mode ", key="devmode-dash")
        if dev_mode:
            WIDE_MODE_INFO = """
            Portfolio Mode Active\n
            Check out expanders to see live code blocks
            """
            st.info(WIDE_MODE_INFO)
    
    
    # ---- HEADER ----

    topcol1, topcol2 = st.columns([1,5])
    topcol2.markdown("# Your Dashboard")
    try:
        topcol1.image("imgs/cafe_sign.png", width=120)
    except:
        st.write("")
    st.write("##")
    st.write("---")



# ---- driver ----

# need try except here 
run()