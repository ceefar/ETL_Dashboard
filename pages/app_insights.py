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



# ---- FUNCTIONS ----

# base queries used for the initial display of the web app using the default store, and other basic queries like valid dates
@st.experimental_singleton # is shared across all users connected to the app so can be accessed from multiple threads 
def base_queries() -> dict: # could place this in db integration in future btw
    """ run and cache these base queries, grabs a chunk of base data from 'Chesterfield' for the initially loaded dashboard """   
    
    # for min/max date ranges
    base_first_valid_date = db.get_from_db("SELECT current_day FROM BizInsights ORDER BY current_day ASC LIMIT 1")
    base_first_valid_date = base_first_valid_date[0][0]
    base_last_valid_date = db.get_from_db("SELECT current_day FROM BizInsights ORDER BY current_day DESC LIMIT 1")
    base_last_valid_date = base_last_valid_date[0][0]

    # bundle everything up in a dictionary so it's much easier (and slightly less computationally expensive) to extract - variable names are the keys
    base_dictionary = {"valid_dates":(base_first_valid_date, base_last_valid_date)}

    # return the bundle up data in a dictionary
    return(base_dictionary)



# ---- MAIN WEB APP ----

def run():

    # ---- BASE QUERIES ----
    # run any base (initial load of the page / default selections) queries
    base_data_dict = base_queries()


    # ---- BASE VARIABLES ----
    # for any heavily used/recycled variables, and unpacking of the base queries

    # base stores list, could be done dynamically but it doesn't change
    base_stores_list = ['Chesterfield', 'Uppingham', 'Longridge', 'London Camden', 'London Soho']

    # get valid dates from base data dict 
    first_valid_date, last_valid_date = base_data_dict["valid_dates"]
    # convert the dates to date objects 
    first_valid_date = datetime.datetime.strptime(first_valid_date, '%Y-%m-%d').date()
    last_valid_date = datetime.datetime.strptime(last_valid_date, '%Y-%m-%d').date()

    # initialise empty session state vars if there are none
    if "last_active_date_tab" not in st.session_state:
        st.session_state["last_active_date_tab"] = ""
    if "last_active_store_tab" not in st.session_state:
        st.session_state["last_active_store_tab"] = ""        
    # empty var for selected stores last active tab functionality
    selected_date = ""

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

    topcol1, topcol2 = st.columns([1,8])
    topcol2.markdown("# Insights Title")
    try:
        topcol1.image("imgs/cafe_sign.png", width=120)
    except:
        st.write("")
    st.write("##")


    # ---- USER SELECTS + VISUAL CLARITY ----

    def last_active_tab(the_tab:str = "off", want_return:bool = False):
        """ could just do with the actual variables instead of the tab?!?... blah, returns blah """

        # vars to hold the last active tab
        last_active_date_tab = st.session_state["last_active_date_tab"]

        print("the_tab", the_tab)
        print("want_return", want_return)
        print("last_active_date_tab : ", last_active_date_tab)

        # switch to either return the last active tab or store it
        if want_return:
                return(last_active_date_tab)
        else:
            st.session_state["last_active_date_tab"] = the_tab[1]


        # TODO 
        # FIXME 
        # THEN ITS LIKE BOOM - ANOTHER FUNCTION FOR USING THE LAST ACTIVE TAB FOR THE PRECEEDING QUERIES!

    # TODO 
    # want image or whatever of the date on the right too and maybe since this is a change between tabs thing
    # a button so you dont *have* to change to make the selection (make sure this is made clear to the user)
    # the button will just run last active tab with the relevant parameters!
    userSelectCol, _, storeImg1, storeImg2, storeImg3, storeImg4, storeImg5 = st.columns([4,1,1,1,1,1,1]) 
    with userSelectCol:
        dateTab1, dateTab2, dateTab3, dateTab4, dateTab5 = st.tabs(["Single Day", "Between 2 Dates", "Full Week", "Full Month", "All Time"])
        with dateTab1:
            selected_date_1 = st.date_input("What Date Would You Like Info On?", datetime.date(2022, 7, 5), max_value=last_valid_date, min_value=first_valid_date, on_change=last_active_tab, args=[("date", 1)], key="TODO")  
        with dateTab2:
            selected_date_2 = st.date_input("What Date Would You Like Info On?", datetime.date(2022, 7, 5), max_value=last_valid_date, min_value=first_valid_date, on_change=last_active_tab, args=[("date", 2)], key="TODO2")  
    st.write("##")

    # BUG - URGENT/FIRST 
    # TODO - ABANDON THIS ALL STORES IDEA FOR NOW FFS!!!!!
    with userSelectCol:
        storeTab1, storeTab2 = st.tabs(["Select Stores", "All Stores"])
        with storeTab1:
            selected_stores_1 = st.multiselect("Choose The Store", options=base_stores_list, default=["Chesterfield"])
        with storeTab2:
            selected_stores_2 = st.multiselect("Choose The Store", options=base_stores_list, default=base_stores_list, disabled=True)
            st.warning("Don't worry it's active, you just can't change the selections here")
    
    # TODO 
    # could make function? idk but defo can do with dictionary ting!
    use_date = last_active_tab(want_return=True)
    if use_date == 1:
        selected_date = selected_date_1
    elif use_date == 2:
        selected_date = selected_date_2

    print("selected_date", selected_date)

    # ---- VISUAL CLARITY STORE PRINT ----

    # dictionary to hold store related image paths, and their column vars for setting iteratively
    stores_img_dict = {"Chesterfield":{"col":storeImg1, "on":"imgs\coffee-shop-light-chesterfield.png", "off":"imgs\coffee-shop-light-chesterfield-saturated.png"},
                        "Uppingham":{"col":storeImg2, "on":"imgs\coffee-shop-light-uppingham.png", "off":"imgs\coffee-shop-light-uppingham-saturated.png"},
                        "Longridge":{"col":storeImg3, "on":"imgs\coffee-shop-light-longridge.png", "off":"imgs\coffee-shop-light-longridge-saturated.png"},
                        "London Camden":{"col":storeImg4, "on":"imgs\coffee-shop-light-london-camden.png", "off":"imgs\coffee-shop-light-london-camden-saturated.png"},
                        "London Soho":{"col":storeImg5, "on":"imgs\coffee-shop-light-london-soho.png", "off":"imgs\coffee-shop-light-london-soho-saturated.png"}
                        }

    # print function for images
    def print_on_off_stores(selected_stores_list:list, img_dict:dict):
        """ prints out the 5 store images as either on or off (saturated) based on whether they were selected, see comment for refactor"""
        # if you actually pass in the dict (and they always have cols + imgs, and same key names) then this could be reformatted to be multipurpose
        for store_name in base_stores_list:
                if store_name in selected_stores_list:
                    img_dict[store_name]["col"].image(img_dict[store_name]["on"])
                else:
                    img_dict[store_name]["col"].image(img_dict[store_name]["off"])

    print_on_off_stores(selected_stores_1, stores_img_dict)



# ---- DRIVER ----
run()