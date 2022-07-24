# ---- IMPORTS ----

# for web app 
import streamlit as st
import streamlit.components.v1 as stc
from streamlit.errors import StreamlitAPIException
# for date time objects
import datetime
# for db integration
import db_integration as db
# for images and img manipulation
import PIL
# for data manipulation
import pandas as pd
# for detailed data visualisation
import altair as alt
# for logging
import logging


# ---- LOGGER ----

# create and configure insights page logger, all log levels, custom log message, overwrites file per run instead of appending
LOG_FORMAT = "%(levelname)s %(asctime)s - %(message)s"
logging.basicConfig(filename = "C:/Users/robfa/Downloads/ETL_Dashboard/applogs/insights.log", level = logging.DEBUG, format = LOG_FORMAT, filemode = "w")
logger = logging.getLogger()

# test messages to copy
#logger.debug("Harmless debug message") # 10
#logger.info("Some useful info") # 20
#logger.warning("I'm sorry I can't do that") # 30
#logger.error("This would cause an error") # 40
#logger.critical("The program became sentient, run") # 50


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


# TODO - move to a general functions/similar module
@st.cache
def create_stores_query(user_stores_list:list, need_where:bool = True, for_data:bool = False, is_join:bool = False) -> str:
    """ for creating the dynamic query for store selection, given list should not be None """

    # for data flag sets the store name column var to either store_name or store
    # for join flag adds d. to the store variable as it is being used in a join
    if for_data:
        if is_join:
            store_var = "d.store"
        else:
            store_var = "store"
    else:
        store_var = "store_name"

    # parameter flag for if the WHERE part of the statement is needed or not
    if need_where:
        where_part = "WHERE "
    else:
        where_part = " "

    # if only one store then the query is simply the store itself
    if len(user_stores_list) == 1:
        return(f"{where_part}{store_var} = '{user_stores_list[0]}'")
    # if 
    elif len(user_stores_list) == 0 or user_stores_list[0] == "":
        return(f"{where_part}{store_var} = 'Chesterfield'")
    # else if the length is larger than 1 then we must join the stores dynamically for the resulting query
    else:
        final_query = f" OR {store_var}=".join(list(map(lambda x: f"'{x}'",user_stores_list)))
        final_query = f"{where_part} ({store_var}=" + final_query + ")"
        return(final_query)


# TODOASAP 
# SHOULD ACTUALLY MAKE A TABLE FOR THIS NOW INSTEAD, LIKE THE PRODUCT PRICING TABLE BUT SHOULD INCLUDE THE STORES DUHHHHH
#  - THEN (THIS FUNCTION) CAN QUERY FROM THAT 
@st.cache
def get_main_items_from_stores(user_store:str) -> list:
    """ write me """
    # get only main item name for user select dropdowns
    get_main_item = db.get_from_db(f"SELECT DISTINCT i.item_name FROM CustomerItems i INNER JOIN CustomerData d on (i.transaction_id = d.transaction_id) WHERE d.store = '{user_store}'")
    main_item_list = []
    for item in get_main_item:
        main_item_list.append(item[0])
    # return the result
    return(main_item_list)


def get_main_items_from_stores_updated(user_store:str) -> list:
    """ write me """
    pass


@st.cache
def get_flavours_for_item(user_store:str, user_item:str) -> list:
    """ write me """
    item_flavours = db.get_from_db(f"SELECT DISTINCT i.item_flavour FROM CustomerItems i INNER JOIN CustomerData d on (i.transaction_id = d.transaction_id) WHERE d.store = '{user_store}' AND i.item_name = '{user_item}';")
    item_flavours_list = []
    # convert the returned tuples into a list (don't print required as streamlit prints (to web app) list comprehensions that aren't assigned to variables)
    dont_print_2 = [item_flavours_list.append(flavour[0]) for flavour in item_flavours]
    return(item_flavours_list)


@st.cache
def create_flavour_query(flavour_x_is_null:bool, multi_flav_selector_x:list, final_item_flavours_list_x:list) -> str:
    """ write me """

    # first split flavour selector dynamically if multi select, requires bracket notation for AND / OR statement
    # only required for flavour, as size can only be regular or large

    # if only 1 flavour then 2 cases to deal with
    if len(multi_flav_selector_x) == 1:
        # check if this item has flavours by checking what was returned by the database for this item
        if multi_flav_selector_x[0] is None:
            # if there is no flavour for this then set the query to validate on NULL values (no = operator, no '')
            final_flav_select = f"i.item_flavour is NULL"
            # also set null flavour flag to True so that final sql can be altered to output valid string (i.item_name, i.item_size, i.item_flavour) 
            flavour_x_is_null = True
        else:
            # else just 1 valid flavour was selected so create standard query
            final_flav_select = f"i.item_flavour='{multi_flav_selector_x[0]}'"

    # else if more than 1 flavour was selected then we must dynamically join them together so the query include OR statements
    elif len(multi_flav_selector_x) > 1:
        final_flav_select = " OR i.item_flavour=".join(list(map(lambda x: f"'{x}'", multi_flav_selector_x)))
        final_flav_select = "(i.item_flavour=" + final_flav_select + ")"

    # else if no flavour was selected (any valid flavour was removed from the multiselect box by the user) then 2 cases to deal with  
    elif len(multi_flav_selector_x) == 0:
        # first check the available flavours that were returned by the database for this item, if true user has removed the 'None' flavour option from multiselect
        if multi_flav_selector_x is None:
            # if there is no flavour then set to validate on NULL
            final_flav_select = f"i.item_flavour is NULL"
        else:      
            # else (if the first flavour select option isn't None) then it means the user removed all from valid flavours from multiselect   
            # ternary statement prints None instead of a blank space if there is used removed all selections for flavours else prints the default flavour that's being used       
            final_flav_select = f"i.item_flavour='{final_item_flavours_list_x[0] if final_item_flavours_list_x[0] != '' else 'None'}'"
            # so add the 'default', aka first item in the flavours list, to the query and inform the user of what has happened
            
            # TODO - way to flag this for this column - skipping for now 
            #itemInfoCol.error(f"Flavour = {final_item_flavours_list_x[0]} >")

    return(final_flav_select, flavour_x_is_null)


@st.cache
def create_size_query(multi_size_selector_x:list) -> str:
    """ write me """
    # split size selector if multi select, only ever Regular or Large so easier to do
    if len(multi_size_selector_x) == 1:
        final_size_select = f"i.item_size='{multi_size_selector_x[0]}'"
    elif len(multi_size_selector_x) == 0:
        final_size_select = "i.item_size='Regular'"
        # TODO again to do this column thing
        #itemInfoCol.error(f"< Size defaults to Regular")
    else:
        final_size_select = f"(i.item_size='{multi_size_selector_x[0]}' OR i.item_size = '{multi_size_selector_x[1]}')"
    # return the result
    return(final_size_select)


#@st.cache()
def get_hour_cups_data(flavour_x_concat, selected_stores_x, select_date, item_selector_x, final_size_select_x, final_flav_select_x, after_concat:str):
    """ groups together all of the complex queries in to the final query and returns the data - is cached """

    # new after concat parameter is for adding in a date column to the return values for separating results based on the dates

    # ---- The Query Breakdown ----
    # select count of names of each unique item sold, with the unique items = concatinated name + size + flavour (if not null)
    # if flavour is null remove it from the concat in the select query
    # then group each item by unique flavour + name + size 
    # and for each hour of the day (e.g. 20 large mocha @ 9am, 15 large mocha @ 10am...)
    # inner joins between customerdata -> essentially raw data that has been cleaned/valdiated
    # and customeritems -> customer transactional data that has been normalised to first normal form (all unique records, all single values)
    # joined on the transaction id (which is the field that allows the transactional 'customeritems' table to adhere to 1nf)
    # where store, date, and item name are the users selected values

    # TODO - UPDATE CONCAT ORDER SO FLAVOUR IS FIRST (maybe add store) - NOTE HAVE TO TAKE COMMA INTO CONSIDERATION 
    cups_by_hour_query = f"SELECT COUNT(i.item_name) AS cupsSold, HOUR(d.time_stamp) AS theHour,\
                            CONCAT({flavour_x_concat} i.item_name, i.item_size, store) AS item {after_concat} FROM CustomerItems i\
                            INNER JOIN CustomerData d ON (i.transaction_id = d.transaction_id) WHERE store = '{selected_stores_x}'\
                            AND DATE(d.time_stamp) {select_date} AND i.item_name = '{item_selector_x}' AND {final_size_select_x}\
                            AND {final_flav_select_x} GROUP BY d.time_stamp, item"
    logger.info("Final hour x cups Altair chart query (get_hour_cups_data) - {0}".format(cups_by_hour_query)) 
    hour_cups_data = db.get_from_db(cups_by_hour_query)  

    # TODOASAP - TO CACHE THIS (& HASH IT FOR RETURN) IT SEEMS LIKE YOU NEED TO CHANGE THE DATE TO A STRING PROBABLY IDK THO

    return(hour_cups_data) 


# is so simple am not guna cache it
def decide_to_include_flavour(flavour_x_is_null):
    """ write me """
    if flavour_x_is_null == False:
        # if flag is False, a valid flavour is included in the flavour part of the query (AND i.flavour = "x" OR i.flavour = "y")
        # so use it in the SELECT statement for finding unqiue items (unique item = item_name + unique size + unique flavour)
        return("i.item_flavour,")
    else:
        # if flag is True, the query has been adjusted for Null values in the flavour part of the query (AND i.flavour is NULL)
        # so remove it from the SELECT statement otherwise included NULL will invalidate it entirely (every i.itemname + i.itemsize will = NULL)
        return("")   


# again so simple is no need to cache
def make_date_query(user_date:tuple|datetime.date) -> str:
    """ write me """
    if isinstance(user_date, tuple):
        date_part = f" BETWEEN '{user_date[0]}' AND '{user_date[1]}' "
    else:
        # else it just stays as what it was
        date_part = f" = '{user_date}'"
    return(date_part)



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

    # initialise session state var if there is none, default to 1 (this is the initial tab number (key) for single date select)
    if "last_active_date_tab" not in st.session_state:
        st.session_state["last_active_date_tab"] = 1  
    # empty var for selected stores last active tab functionality
    selected_date = ""


    # ---- SIDEBAR ----

    # portfolio/developer mode toggle
    with st.sidebar:

        # TODO - add in dev mode things but heck just do code snippets or whatever forget echo as its pointless (unless absolutely necessary) 
        dev_mode = st.checkbox(label="Portfolio Mode ", key="devmode-insights")
        if dev_mode:
            WIDE_MODE_INFO = """
            Portfolio Mode Active\n
            Check out expanders to see live code blocks
            """
            st.info(WIDE_MODE_INFO)

        st.write("##")
        st.markdown("#### Advanced Mode")
        st.write("For more advanced query options")
        advanced_options_1 = st.checkbox("Advanced Mode", value=True, disabled=True) 
    

    # ---- HEADER ----

    topcol1, topcol2 = st.columns([1,8])
    topcol2.markdown("# Insights Title")
    try:
        # TODO - edit the image so is smaller (currently is 512x512)
        topcol1.image("imgs/insight_chart.png", width=120)
    except:
        st.write("")
    st.write("##")


    # ---- USER SELECTS + VISUAL CLARITY ----

    def last_active_tab(the_tab:str = "off", want_return:bool = False):
        """ could just do with the actual variables instead of the tab?!?... blah, returns blah """

        # use a session state var to persist the last active tab
        last_active_date_tab = st.session_state["last_active_date_tab"]

        # switch to either return the last active tab or store it
        if want_return:
                return(last_active_date_tab)
        else:
            st.session_state["last_active_date_tab"] = the_tab


    # TODO 
    # want image or whatever of the date on the right too and maybe since this is a change between tabs thing
    # a button so you dont *have* to change to make the selection (make sure this is made clear to the user)
    # the button will just run last active tab with the relevant parameters!

    userSelectCol, _, storeImg1, storeImg2, storeImg3, storeImg4, storeImg5 = st.columns([4,1,1,1,1,1,1]) 
    with userSelectCol:
        # ---- STORE SELECT ----
        selected_stores_1 = st.multiselect("Choose The Store/s", options=base_stores_list, default=["Chesterfield"])
        
        # ---- DATE SELECT ----
        dateTab1, dateTab2, dateTab3, dateTab4, dateTab5, dateTabs6 = st.tabs(["Single Day", "Between 2 Dates", "Single Week", "Mulitple Weeks", "Full Month", "All Time"]) # multiple weeks is a maybe rn btw
        
        def force_date_run_btn(run_button_key:str):
            """ write me """
            # strip the key to just it's number
            keynumb = int(run_button_key[-1:])
            last_active_tab(keynumb)

        # --- SINGLE DAY ----
        with dateTab1:
            selected_date_1 = st.date_input("What Date Would You Like Info On?", datetime.date(2022, 7, 5), max_value=last_valid_date, min_value=first_valid_date, on_change=last_active_tab, args=[1], key="TODO")  
            st.write("##")
            st.button("Get Insights", help="To Get New Insights : change the date, press this button, use physic powers", key="run_1", on_click=force_date_run_btn, args=["run_1"])
        
        # ---- BETWEEN 2 DAYS ----
        with dateTab2:
            selected_date_2_start = st.date_input("What Start Date?", datetime.date(2022, 7, 1), max_value=last_valid_date, min_value=first_valid_date, on_change=last_active_tab, args=[2], key="TODO2")  
            selected_date_2_end = st.date_input("What End Date?", datetime.date(2022, 7, 8), max_value=last_valid_date, min_value=first_valid_date, on_change=last_active_tab, args=[2], key="TODO3")
            st.write("##")
            st.button("Get Insights", help="To Get New Insights : change the date, press this button, use physic powers", key="run_2", on_click=force_date_run_btn, args=["run_2"])
            # TODO - days between dates here 

        # ---- SINGLE WEEK ----
        with dateTab3:
            # TODO 
            # put query in db_interaction and rest in own function
            stores_query = create_stores_query(selected_stores_1)
            stores_avail_weeks = sorted(db.get_from_db(f"SELECT DISTINCT WEEKOFYEAR(current_day) FROM BizInsights {stores_query}"))
            first_day_of_week_list = [] # for zipping with stores_available_weeks (must ensure order is correct)
            for weeknum in stores_avail_weeks:
                first_day_of_week = db.get_from_db(f"SELECT '2022-01-01'+INTERVAL ({weeknum[0]}-WEEK('2022-01-01', 1))*7 - WEEKDAY('2022-01-01') DAY")
                first_day_of_week_list.append(first_day_of_week[0][0])
            # TODO - REFORMAT THE DATE AS ITS YUCKY LIKE THIS 
            stores_available_weeks_formatted = []
            stores_available_weeks = []
            # reformat the nested tuples into a clean list, dont print var needed else prints result due to being a list comprehension
            dont_print_me = [stores_available_weeks_formatted.append(f"Week {weeknumb[0]} : {firstday}") for weeknumb, firstday in zip(stores_avail_weeks, first_day_of_week_list)]
            dont_print_me_2 = [stores_available_weeks.append(weeknumb[0]) for weeknumb in stores_avail_weeks]
            # print the resulting selectbox for user input
            # TODO - add the actual first date instead of just an int and get the img ting sorted too
            selected_date_3 = st.selectbox("Which Week?", options=stores_available_weeks_formatted, key="TODO4", help="Date shown is week commencing. Weeks start on Monday", on_change=last_active_tab, args=[3])
            st.write("##")
            st.button("Get Insights", help="To Get New Insights : change the date, press this button, use physic powers", key="run_3", on_click=force_date_run_btn, args=["run_3"])        
        
        # ---- MULTIPLE WEEKS [NOT IMPLEMENTED YET] ----
        with dateTab4:
            # ensure it isn't going to error due to the default
            if len(stores_available_weeks) > 1:
                multiweek_default = [stores_available_weeks[0],stores_available_weeks[1]]
            else:
                multiweek_default = [stores_available_weeks[0]]
            selected_date_4 = st.multiselect("Which Weeks?", options=stores_available_weeks, default=multiweek_default, key="TODO5", help="See 'Single Week' for week commencing date", on_change=last_active_tab, args=[4])
            # TODO - obvs have this on the right hand side with the img ting and ig like completeness too (total days && available days)
            st.write(f"Total Days = {len(selected_date_4) * 7}")
            st.write("##")
            st.button("Get Insights", help="To Get New Insights : change the date, press this button, use physic powers", key="run_4", on_click=force_date_run_btn, args=["run_4"])        


    # var that holds the key/on_change args from each date select plus the variables that store the result, used for getting the last active tab
    use_vs_selected_date_dict = {1:selected_date_1, 2:(selected_date_2_start, selected_date_2_end), 3:selected_date_3, 4:selected_date_4}

    def set_selected_date_from_last_active_tab(date_dict:dict) -> datetime.date|tuple: # technically isn't returning a datetime object but a datewidget object but meh same same and probs convert it anyways
        """ use the on_change arguments (which is just the key as an int) from each date select and returns the variables holding the relevant dates """
        use_date = last_active_tab(want_return=True)

        # option 3 is week number with week beginning so we need the date at week end too
        if st.session_state["last_active_date_tab"] == 3:
            to_make_date = date_dict[use_date][10:]
            end_of_week = db.get_from_db(f"SELECT DATE_ADD('{to_make_date}', INTERVAL 6 DAY);")
            return((to_make_date, end_of_week[0][0]))

        # TODO 
        # FOR IS LITERALLY THE SAME AS OPTION 3, IT JUST BECOMES AN AND STATEMENT 
        #   - unless ig the dates are next to each other but meh doesn't make enough diff so just do one way with AND
            
        return(date_dict[use_date])    
    # END NESTED FUNCTION

    # set the selected date based on the last active (modified user select) tab
    selected_date = set_selected_date_from_last_active_tab(use_vs_selected_date_dict)
    selected_date = make_date_query(selected_date)

 
    # ---- VISUAL CLARITY STORE PRINT ----

    # dictionary to hold store related image paths, and their column vars for setting iteratively
    stores_img_dict = {"Chesterfield":{"col":storeImg1, "on":"imgs/coffee-shop-light-chesterfield.png", "off":"imgs/coffee-shop-light-chesterfield-saturated.png"},
                        "Uppingham":{"col":storeImg2, "on":"imgs/coffee-shop-light-uppingham.png", "off":"imgs/coffee-shop-light-uppingham-saturated.png"},
                        "Longridge":{"col":storeImg3, "on":"imgs/coffee-shop-light-longridge.png", "off":"imgs/coffee-shop-light-longridge-saturated.png"},
                        "London Camden":{"col":storeImg4, "on":"imgs/coffee-shop-light-london-camden.png", "off":"imgs/coffee-shop-light-london-camden-saturated.png"},
                        "London Soho":{"col":storeImg5, "on":"imgs/coffee-shop-light-london-soho.png", "off":"imgs/coffee-shop-light-london-soho-saturated.png"}
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


    # handle error in case the images can't be found, but this generally only happens when using backslash instead of forward slash so fixing that too
    try:
        print_on_off_stores(selected_stores_1, stores_img_dict)
    except FileNotFoundError:
        pass


    # TODO 
    # ---- VISUAL CLARITY CALENDAR PRINT (TO-DO) ----

    # should cache artist prints btw as will be atleast somewhat computationally expensive
    # june_start_weeknumb = 22
    # highlight_week = weeknumberselect - june_start_weeknumb
    # calendar_highlight = arty.highlight_calendar(highlight_week, weeknumberselect, week_array)
    # weekBreakdownCol2.image(calendar_highlight)         



    # ---- DIVIDER ----
    st.write("---")


    # ---- THE COMPARISION CHARTS ---- 


    # TODO 
    # ALSO
    # MAYBE FOR ADVANCED MODE HAVE INDIVIDUAL TOGGLES TO REMOVE THINGS OR ALWAYS USE MULTISELECT IDK!


    # ALTAIR CHART product sold by hour of day
    with st.container():
        st.write(f"### :bulb: Insight - Compare Two Items") 

        # select any item from the store for comparison
        item1Col, itemInfoCol, item2Col = st.columns([2,1,2])

        with item1Col:
            store_selector_1 = st.selectbox(label=f"Which Store Do You Want To Choose An Item From?", key="store_sel_1", options=selected_stores_1, index=0, help="For more stores update the above multiselect")
            final_main_item_list = get_main_items_from_stores(store_selector_1)
            item_selector_1 = st.selectbox(label=f"Choose An Item From Store {store_selector_1}", key="item_selector_1", options=final_main_item_list, index=0) 
            
        with item2Col:
            store_select_2_index = 1 if len(selected_stores_1) > 1 else 0
            store_selector_2 = st.selectbox(label=f"Which Store Do You Want To Choose An Item From?", key="store_sel_2", options=selected_stores_1, index=store_select_2_index, help="For more stores update the above multiselect")
            final_main_item_list = get_main_items_from_stores(store_selector_2)
            item_selector_2 = st.selectbox(label=f"Choose An Item From Store {store_selector_2}", key="item_selector_2", options=final_main_item_list, index=1)
            
        # set the user results to vars used in the queries
        selected_stores_2 = store_selector_2
        selected_stores_1 = store_selector_1

        with itemInfoCol:
            st.write("##")
            if advanced_options_1:
                st.info("Advanced Mode : On")
            else:
                st.warning("Try Advanced Mode!")


        # ---- USER SELECTS ----
        logger.debug("Get list of flavours from the db, for the users selected item") # actually tuples not list but whatever

        with item1Col:
            final_item_flavours_list = get_flavours_for_item(selected_stores_1, item_selector_1)
            multi_flav_selector_1 = st.multiselect(label=f"Choose A Flavour For {item_selector_1}", key="multi_flav_select_1", options=final_item_flavours_list, default=final_item_flavours_list[0])
            multi_size_selector_1 = st.multiselect(label=f"Choose A Size For {item_selector_1}", key="multi_size_select_1", options=["Regular","Large"], default="Regular")

        with item2Col:
            final_item_flavours_list_2 = get_flavours_for_item(selected_stores_2, item_selector_2)
            multi_flav_selector_2 = st.multiselect(label=f"Choose A Flavour For {item_selector_2}", key="multi_flav_select_2", options=final_item_flavours_list_2, default=final_item_flavours_list_2[0])
            multi_size_selector_2 = st.multiselect(label=f"Choose A Size For {item_selector_2}", key="multi_size_select_2", options=["Regular","Large"], default="Regular")


        # ---- FLAVOUR & SIZE SUB-QUERY CREATION ----

        # if flavour is Null/None then we need to tweek the initial SELECT to get the correct (unique) item name (flavour is the only case with Null values so simple boolean flag is fine)
        flavour_1_is_null = False
        flavour_2_is_null = False
        # call functions that dynamically creates the complex flavour part of the query, plus the simpler size query
        final_flav_select_1, flavour_1_is_null = create_flavour_query(flavour_1_is_null, multi_flav_selector_1, final_item_flavours_list)
        final_size_select_1 = create_size_query(multi_size_selector_1)
        final_flav_select_2, flavour_2_is_null = create_flavour_query(flavour_2_is_null, multi_flav_selector_2, final_item_flavours_list_2)
        final_size_select_2 = create_size_query(multi_size_selector_2)
        # decide how flavour will be included in the final query based on previous flags
        flavour_1_concat = decide_to_include_flavour(flavour_1_is_null)
        flavour_2_concat = decide_to_include_flavour(flavour_2_is_null)

        # the key/int of the last active tab for deciding whether want results to have week based tab display
        active_tab_key = last_active_tab(want_return=True)

        # if is a "BETWEEN" date query, then add in new column after the CONCAT part of the SELECT statement to also include the date (for making tabs)
        if active_tab_key != 1:
            post_concat_addition = ", DATE(d.time_stamp) AS theDate "
        else:
            post_concat_addition = " "

        # log last active tab before running function
        logger.info("last active date tab = {0}".format(active_tab_key))
        # get data for left side
        hour_cups_data_1_adv = get_hour_cups_data(flavour_1_concat, selected_stores_1, selected_date, item_selector_1, final_size_select_1, final_flav_select_1, post_concat_addition)
        # get data for right side
        hour_cups_data_2_adv = get_hour_cups_data(flavour_2_concat, selected_stores_2, selected_date, item_selector_2, final_size_select_2, final_flav_select_2, post_concat_addition)
        st.write("##")


        # ---- CREATE AND PRINT ALTAIR CHART OF RESULTS ----

        # PORTFOLIO - ADD THIS STUFF
        # TODO - QUICKLY SEE IF CAN FIX THE STRING THING BUT COULD LEAVE FOR NOW TBF

        if active_tab_key != 1:
            # get the needed date info (first valid date, date at end of first week, difference in days from start to end)
            true_start_date_str = (selected_date[10:20])
            true_end_date_str = (selected_date[27:37])
            first_date_altair = datetime.datetime.strptime(true_start_date_str, '%Y-%m-%d')
            last_date_altair = datetime.datetime.strptime(true_end_date_str, '%Y-%m-%d')
            end_of_first_week_date_altair = first_date_altair + datetime.timedelta(days=7)
            end_of_first_week_date_altair = end_of_first_week_date_altair.date()
            first_date_altair = first_date_altair.date()
            last_date_altair = last_date_altair.date()
            days_difference = (last_date_altair - first_date_altair).days
            # cant use only floor div, must know if had remainder for deciding if need an extra "week"
            weeks_between_dates = (days_difference // 7) # max 6 weeks btw
            if (days_difference % 7) != 0:
                weeks_between_dates += 1
        else: 
            # set these as defaults so they don't error
            weeks_between_dates, first_date_altair, end_of_first_week_date_altair = 0, 0, 0
            
        # log the hour cup results for multi-dates but only a tiny subset of the resulting queries else its far too chunky
        logger.info("\n\nResult of get_hour_cups_data query (left/item 1)\nFirst : {0}\nLast : {1}".format(hour_cups_data_1_adv[0], hour_cups_data_1_adv[-1]))
        #logger.info("\n\nResult of get_hour_cups_data query (right/item 2)\nFirst : {0}\nLast : {1}".format(hour_cups_data_2_adv[0], hour_cups_data_2_adv[-1])) 

        # left query (item 1)
        # empty lists used for transforming db data for df, 'all' covers all dates, the rest is week by week
        just_names_list_1_all, just_names_list_1_w0, just_names_list_1_w1, just_names_list_1_w2, just_names_list_1_w3, just_names_list_1_w4, just_names_list_1_w5= [], [], [], [], [], [], []
        just_hour_list_1_all, just_hour_list_1_w0, just_hour_list_1_w1, just_hour_list_1_w2, just_hour_list_1_w3, just_hour_list_1_w4, just_hour_list_1_w5 = [], [], [], [], [], [], []
        just_cupcount_list_1_all, just_cupcount_list_1_w0, just_cupcount_list_1_w1, just_cupcount_list_1_w2, just_cupcount_list_1_w3, just_cupcount_list_1_w4, just_cupcount_list_1_w5 = [], [], [], [], [], [], []      

        # if just select 1 date
        if weeks_between_dates == 0:
            for cups_data in hour_cups_data_1_adv:
                just_cupcount_list_1_all.append(cups_data[0])
                just_hour_list_1_all.append(cups_data[1])
                just_names_list_1_all.append(cups_data[2])

        # vars for start and end of week as datetime.date objects
        week_start_var, week_end_var = first_date_altair, end_of_first_week_date_altair

        # run for the needed weeks (sets of 7 days), starting from the first valid date, won't be run for single date btw which is perf obvs
        for weeknum in range(1, weeks_between_dates + 1):

            # dict that sorts which list each loops results will be appended to
            weeks_dict = {1:(just_cupcount_list_1_w0, just_hour_list_1_w0, just_names_list_1_w0),
                            2:(just_cupcount_list_1_w1, just_hour_list_1_w1, just_names_list_1_w1),
                            3:(just_cupcount_list_1_w2, just_hour_list_1_w2, just_names_list_1_w2),
                            4:(just_cupcount_list_1_w3, just_hour_list_1_w3, just_names_list_1_w3),
                            5:(just_cupcount_list_1_w4, just_hour_list_1_w4, just_names_list_1_w4),
                            6:(just_cupcount_list_1_w5, just_hour_list_1_w5, just_names_list_1_w5),
                            }

            # set vars for the list that will be appended to based on the weeknum
            just_cupcount_list_1_week, just_hour_list_1_week, just_names_list_1_week = weeks_dict[weeknum][0], weeks_dict[weeknum][1], weeks_dict[weeknum][2]

            # grab the cups data and add it to the relevant list
            for cups_data in hour_cups_data_1_adv:
                # TODO - slice thing below else is some minor pointless looping
                # what you should actually do then is slice off the preceding stuff thats already been added

                # if statement to only grab data for the given week
                if cups_data[3] >= week_start_var and cups_data[3] <= week_end_var:
                    just_cupcount_list_1_week.append(cups_data[0])
                    just_hour_list_1_week.append(cups_data[1])
                    just_names_list_1_week.append(cups_data[2])

                # if reached a date thats greater than increment week var
                # TODOASAP
                # this will cut off one piece of data, ig save it outside the loop and just tag it on? <<<<<<<<<<<<<<<<<<<<<<<<< !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
                if cups_data[3] > week_end_var:
                    # had been appending it here, but that will be appending it to the wrong (before) week
                    #just_cupcount_list_1_week.append(cups_data[0])
                    #just_hour_list_1_week.append(cups_data[1])
                    #just_names_list_1_week.append(cups_data[2])
                    weeknum += 1
                    week_start_var = week_start_var + datetime.timedelta(days=8)
                    week_end_var = week_start_var + datetime.timedelta(days=7)
                    # though we're calculating and using the weeks in this loop, still dont allow the final date to be greater than the users selection
                    if week_end_var > last_date_altair:
                        week_end_var = last_date_altair
                    break


        # TODOASAP - MAKE THIS A FUNCTION
        # 'all dates' is just everything together
        cupcount_weeks_list = [just_cupcount_list_1_w0,just_cupcount_list_1_w1,just_cupcount_list_1_w2,just_cupcount_list_1_w3,just_cupcount_list_1_w4,just_cupcount_list_1_w5]
        for cupcount_list in cupcount_weeks_list:    
            just_cupcount_list_1_all.extend(cupcount_list)

        justhour_weeks_list = [just_hour_list_1_w0,just_hour_list_1_w1,just_hour_list_1_w2,just_hour_list_1_w3,just_hour_list_1_w4,just_hour_list_1_w5]
        for justhour_list in justhour_weeks_list:
            just_hour_list_1_all.extend(justhour_list)

        justnames_weeks_list = [just_names_list_1_w0,just_names_list_1_w1,just_names_list_1_w2,just_names_list_1_w3,just_names_list_1_w4,just_names_list_1_w5]
        for justnames_list in justnames_weeks_list:
            just_names_list_1_all.extend(justnames_list)


        # TODOASAP
        # HAVE REMOVED THE ONLY ONE DATE TRY EXCEPT INDEXERROR FOR NOW - might not need anymore btw but what if not data for a single day (find out duh)


        # right query (item 2)
        # empty lists used for transforming db data for df
        # first - for all dates, aka all of the data
        just_names_list_2_all = []
        just_hour_list_2_all = []
        just_cupcount_list_2_all = []
        # then - for the first set of 7 days, starting from the first given date
        just_names_list_2_w0 = []
        just_hour_list_2_w0 = []
        just_cupcount_list_2_w0 = []  

        for cups_data in hour_cups_data_2_adv:
            just_cupcount_list_2_all.append(cups_data[0])
            just_hour_list_2_all.append(cups_data[1])
            just_names_list_2_all.append(cups_data[2])
            # try except for case with only 1 date (so no [3], aka date data)
            try:
                # then run for the first week (first 7 days), starting from the first valid date
                if cups_data[3] >= first_date_altair and cups_data[3] <= end_of_first_week_date_altair:
                    just_cupcount_list_2_w0.append(cups_data[0])
                    just_hour_list_2_w0.append(cups_data[1])
                    just_names_list_2_w0.append(cups_data[2])
            except IndexError:
                pass


        # TODOASAP - still need to add this back btw
        # extended one of the lists with the other for the final dataframe
        # first - for all dates
        #just_names_list_1_all.extend(just_names_list_2_all)
        #just_cupcount_list_1_all.extend(just_cupcount_list_2_all)
        #just_hour_list_1_all.extend(just_hour_list_2_all)
        # then - for the first set of 7 days
        #just_names_list_1_w0.extend(just_names_list_2_w0)
        #just_cupcount_list_1_w0.extend(just_cupcount_list_2_w0)
        #just_hour_list_1_w0.extend(just_hour_list_2_w0)
        

        # TODOASAP - move this outside of run function
        @st.cache
        def create_dataframe_setup_chart(just_names_list_1_range, just_cupcount_list_1_range, just_hour_list_1_range):
            """ create the dataframes and resulting altair chart data (barchart + text) for a given range and return the results for rendering """

            # create the dataframe
            sawce = pd.DataFrame({
            "DrinkName": just_names_list_1_range,
            "CupsSold":  just_cupcount_list_1_range,
            "HourOfDay": just_hour_list_1_range
            })

            # setup barchart
            bar_chart = alt.Chart(sawce).mark_bar().encode(
                color="DrinkName:N",
                x="sum(CupsSold):Q",
                y="HourOfDay:N"
            ).properties(height=300)

            # setup text labels for barchart
            chart_text = alt.Chart(sawce).mark_text(dx=-10, dy=3, color='white', fontSize=12, fontWeight=600).encode(
                x=alt.X('sum(CupsSold):Q', stack='zero'),
                y=alt.Y('HourOfDay:N'),
                detail='DrinkName:N',
                text=alt.Text('sum(CupsSold):Q', format='.0f')
            )

            return((bar_chart,chart_text))


        # TODOASAP - ADD SUBTITLE N SHIT
        # create the tabs for the bar chart based on weeks, ternary statements show tabs based on amount of weeks between user selected dates
        st.write("##")
        chartTab0, chartTab1, chartTab2, chartTab3, chartTab4, chartTab5, chartTab6 = st.tabs([f"{'All Dates' if weeks_between_dates != 0 else 'Selected Date'}",
                                                                                                f"{'Week 1' if weeks_between_dates >= 1 else ' '}",
                                                                                                f"{'Week 2' if weeks_between_dates >= 2 else ' '}",
                                                                                                f"{'Week 3' if weeks_between_dates >= 3 else ' '}",
                                                                                                f"{'Week 4' if weeks_between_dates >= 4 else ' '}",
                                                                                                f"{'Week 5' if weeks_between_dates >= 5 else ' '}",
                                                                                                f"{'Week 6' if weeks_between_dates >= 6 else ' '}"])
        # TODO - convert the ternary condition here to a var, then to a datetime object, then use strftime to get a better date
        chartTab_dict = {0:(chartTab0, f"{'All Dates' if weeks_between_dates != 0 else selected_date[4:14]}", (just_names_list_1_all, just_cupcount_list_1_all, just_hour_list_1_all)),
                            1:(chartTab1, "First Week", (just_names_list_1_w0, just_cupcount_list_1_w0, just_hour_list_1_w0)),
                            2:(chartTab2, "Some Title", (just_names_list_1_w1, just_cupcount_list_1_w1, just_hour_list_1_w1)),
                            3:(chartTab3, "Some Title", (just_names_list_1_w2, just_cupcount_list_1_w2, just_hour_list_1_w2)),
                            4:(chartTab4, "Some Title", (just_names_list_1_w3, just_cupcount_list_1_w3, just_hour_list_1_w3)),
                            5:(chartTab5, "Some Title", (just_names_list_1_w4, just_cupcount_list_1_w4, just_hour_list_1_w4)),
                            6:(chartTab6, "Some Title", (just_names_list_1_w5, just_cupcount_list_1_w5, just_hour_list_1_w5))
                        }

        for i in range(0,7):

            # randomly changed to camelcase but meh
            # better title names as this is the tab name too? (also subtitles pls) defo include the actual dates DUHHHHH
            theTab, theTitle, theDataset = chartTab_dict[i][0], chartTab_dict[i][1], chartTab_dict[i][2]
            
            with theTab:
                # grab the data for the chart based on the dates
                barchart, barchart_text = create_dataframe_setup_chart(theDataset[0], theDataset[1], theDataset[2])
                # render the chart
                st.markdown(f"#### {theTitle}")
                st.altair_chart(barchart + barchart_text, use_container_width=True)




# OK SO NEXT/RN

# rnrn
# - this new table function update thing
# - item 2
# - extend function
# - date ranges (just 1 more or maybe even just skip for now tbh)
# - actual fucking insights

# - dynamically doing all of the weeks
#   - extend function, wtf random markdown number, comments, right side (item 2), single week, multiple weeks
#   - ideally starting on a monday or sunday if is easy enough (should be tbf but should skip this part either way to do insights asap)
# - the actual insights stuff! :D
# - logging, unittest, ci/cd basics
# - update functions for new product pricing thing (particularly get flavours n shit)
#   - so much this because havent checked run times on live db
#   - 100% have the initial data preloaded (to cache?)
# - try out multithreading with some simple testing
#   - create a new page for it duh

# - tab stuff like title subtitle etc
# - move functions, ig and comment and clean up a bit quickly
# - ensure single day is still working fine btw (ideally with no tabs showing) 
# - obvs 100 needs portfolio mode before done, oh and advanced mode too maybe but idk
# - the calendar print
    # - also tho owt else could do with artist?
# - make insights the homepages, and have dash as sumnt else, means insights should set to wide (and rerun to ensure is wide thing btw)
#   - also ig can jazz it up a teeny bit (gifs n shit)
# - also things like github/website image thing btw
# - also check history to find that kid that had the exact same condition as me as can't remember what else he posted

# NO CAP, ONCE THIS INSIGHTS IS DONE MOVE ON TO OTHER (QUICKER PROJECTS LIKE 2 IDEAS AM JUST GUNA COPY AND CANCER TING)
# - one was the map idea (best suited area for you, could add in whatever user selects I want tbh but house price and like council tax, average shop sumnt is good start)
# - other was skal.es week time thing
# - obvs my other 2 projects but really just the new atmoic which is 80HD, focus on just one thing ffs get that done and live with user login and db stuff then and only then move on


# ---- DRIVER ----
if __name__ == "__main__":
    # TODOASAP - force experiemental rerun one time initially (use a singleton function ig?) so it is forced to wide mode
    # TODOASAP - also add a info box for this like "better in/designed for wide mode - if this has run in box mode use settings in top right..."
    run()