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
# for data manipulation
import pandas as pd
# for detailed data visualisation
import altair as alt
# for logging
import logging


# ---- LOGGER ----

# create and configure insights page logger, all log levels, custom log message, overwrites file per run instead of appending
LOG_FORMAT = "%(levelname)s %(asctime)s - %(message)s"
logging.basicConfig(filename = "applogs/insights.log", level = logging.DEBUG, format = LOG_FORMAT, filemode = "w")
logger = logging.getLogger()

# test messages to copy
#logger.debug("Harmless debug message") # 10
#logger.info("Some useful info") # 20
#logger.warning("I'm sorry I can't do that") # 30
#logger.error("This would cause an error") # 40
#logger.critical("The program became sentient, run") # 50


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
    """ write me"""
    # get only main item name for user select dropdowns
    get_main_item = db.get_from_db(f"SELECT DISTINCT i.item_name FROM CustomerItems i INNER JOIN CustomerData d on (i.transaction_id = d.transaction_id) WHERE d.store = '{user_store}'")
    main_item_list = []
    for item in get_main_item:
        main_item_list.append(item[0])
    # return the result
    return(main_item_list)


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


@st.cache
def get_hour_cups_data(flavour_x_concat, selected_stores_x, select_date, item_selector_x, final_size_select_x, final_flav_select_x):
    """ groups together all of the complex queries in to the final query and returns the data - is cached """

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
                            CONCAT({flavour_x_concat} i.item_name, i.item_size, store) AS item FROM CustomerItems i\
                            INNER JOIN CustomerData d ON (i.transaction_id = d.transaction_id) WHERE store = '{selected_stores_x}'\
                            AND DATE(d.time_stamp) {select_date} AND i.item_name = '{item_selector_x}' AND {final_size_select_x}\
                            AND {final_flav_select_x} GROUP BY d.time_stamp, item"
    logger.info("Final hour x cups Altair chart query (get_hour_cups_data) - {0}".format(cups_by_hour_query)) 
    hour_cups_data = db.get_from_db(cups_by_hour_query)  
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

    # initialise session state var if there is none, default to 1 (initial date select)
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
            return((use_date, end_of_week[0][0]))

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
    # BUG 
    # FIXME 
    # then put insights below, do this hella detailed and honestly almost wanna say maybe 1 page is fine for now
    # other project stuff may be better to move on to as this is repetitive after new insights stuff
    # if anything just make walkthrough recordings of my favourite bits (and other git projects too ooooo)




    # TODO 
    # BUG 
    # FIXME 
    # OK BOOM STILL HAVE TABS IDEA FOR CHARTS BUT HAVE IT LIKE EITHER DIFFERENT CHART TYPES OR DIFFERENT AXIS OR SUMNT IDK
    # IN THEORY IF WE GRAB THE DATE IN THE SELECT STATEMENT(or store or whatever but date best as can do weeks n shit)
    # CAN HAVE TABS FOR DATE (i.e. weeks) AND ALL TIME, ETC
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

        # get data for left side
        hour_cups_data_2_adv = get_hour_cups_data(flavour_1_concat, selected_stores_1, selected_date, item_selector_1, final_size_select_1, final_flav_select_1)
        # get data for right side
        hour_cups_data_3_adv = get_hour_cups_data(flavour_2_concat, selected_stores_2, selected_date, item_selector_2, final_size_select_2, final_flav_select_2)
        st.write("##")
        # log the results but only a tiny subset of the resulting queries else its far too chunky
        logger.info("Result of get_hour_cups_data query (right/item 2)\nFirst : {0}\nLast : {1}".format(hour_cups_data_3_adv[0], hour_cups_data_3_adv[-1]))
        logger.info("Result of get_hour_cups_data query (left/item 1)\nFirst : {0}\nLast : {1}".format(hour_cups_data_2_adv[0], hour_cups_data_2_adv[-1])) 
        
        
        # ---- CREATE AND PRINT ALTAIR CHART OF RESULTS ----

        # PORTFOLIO - ADD THIS STUFF
        # TODO - QUICKLY SEE IF CAN FIX THE STRING THING BUT COULD LEAVE FOR NOW TBF
        

        # left query (item 1)
        # empty lists used for transforming db data for df
        just_names_list_2 = []
        just_hour_list_2 = []
        just_cupcount_list_2 = []

        for cups_data in hour_cups_data_2_adv:
            just_cupcount_list_2.append(cups_data[0])
            just_hour_list_2.append(cups_data[1])
            just_names_list_2.append(cups_data[2])

        # right query (item 2)
        # empty lists used for transforming db data for df
        just_names_list_3 = []
        just_hour_list_3 = []
        just_cupcount_list_3 = []

        for cups_data in hour_cups_data_3_adv:
            just_cupcount_list_3.append(cups_data[0])
            just_hour_list_3.append(cups_data[1])
            just_names_list_3.append(cups_data[2])

        # extended one of the lists with the other for the final dataframe 
        just_names_list_2.extend(just_names_list_3)
        just_hour_list_2.extend(just_hour_list_3)
        just_cupcount_list_2.extend(just_cupcount_list_3)

        # create the dataframe
        source2 = pd.DataFrame({
        "DrinkName": just_names_list_2,
        "CupsSold":  just_cupcount_list_2,
        "HourOfDay": just_hour_list_2
        })

        # setup barchart
        bar_chart2 = alt.Chart(source2).mark_bar().encode(
            color="DrinkName:N",
            x="sum(CupsSold):Q",
            y="HourOfDay:N"
        ).properties(height=300)

        # setup text labels for barchart
        text2 = alt.Chart(source2).mark_text(dx=-10, dy=3, color='white', fontSize=12, fontWeight=600).encode(
            x=alt.X('sum(CupsSold):Q', stack='zero'),
            y=alt.Y('HourOfDay:N'),
            detail='DrinkName:N',
            text=alt.Text('sum(CupsSold):Q', format='.0f')
        )

        # render the chart
        st.write("##")
        st.markdown("#### Title")
        st.altair_chart(bar_chart2 + text2, use_container_width=True)



# ---- DRIVER ----
if __name__ == "__main__":
    run()