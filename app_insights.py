# ---- IMPORTS ----

# for web app 
from pkg_resources import cleanup_resources
import streamlit as st
import streamlit.components.v1 as stc
from streamlit.errors import StreamlitAPIException, DuplicateWidgetID
# for date time objects
import datetime
# for db integration
import db_integration as db
# for dynamic image creation
import artist as arty
# for images and img manipulation
import PIL
# for data manipulation
import pandas as pd
import numpy as np
# for detailed data visualisation
import altair as alt
# for logging
import logging
# for error handling
import mysql.connector
# for html componenets 
from code_components import THREE_CARD_INFO, FOUR_CARD_INFO

# currently unused imports for debugging
#from streamlit.scriptrunner import RerunException
#from streamlit import legacy_caching


# ---- BUGS/ISSUE LOG ----
# - tabs cause a jump to the bottom of the current tabs viewport, is new streamlit module so likely to be bugfixed
#   - could temp fix by swapping to expanders?


# ---- LOGGER ----

# TODOASAP - FIX THIS WTF
# create and configure insights page logger, all log levels, custom log message, overwrites file per run instead of appending [.debug / .info / .warning / .error / .critical ]
LOG_FORMAT = "%(levelname)s %(asctime)s - %(message)s"
# i swear this doesn't work wtf
logging.basicConfig(filename = "insights.log", level = logging.DEBUG, format = LOG_FORMAT, filemode = "w")
logger = logging.getLogger()


# ---- SETUP WEB APP ----

# TODOASAP - MAKE SURE THIS LOADS IN WIDE MODE && 100 add a info box for this like "better in/designed for wide mode - if this has run in box mode use settings in top right..."
def on_load():
    """ sets the layout default to wide, set page config needs to be the first streamlit action that is run for it to work """
    # potential bug that it sometimes doesn't do this first time round but does when you click a page again (consider re-run to force?)
    st.set_page_config(layout="wide")


# catch error in case that file is reloaded locally meaning app thinks config hasn't run first when it has (may have been snowflake specific so test it)
try: 
    on_load()
except StreamlitAPIException:
    pass


# testing having the connection in main module to see if improves connection bug, tho am not hopeful
@st.experimental_singleton
def init_connection():
    return mysql.connector.connect(**st.secrets["mysql"])

conn = init_connection()
#conn = db.init_connection()


def get_from_db(query):
    """ perform a query that gets from database and returns a value"""
    with conn.cursor() as cur:
        cur.execute(query)
        return cur.fetchall()

def add_to_db(query):
    """ performs a query with no return needed """
    with conn.cursor() as cur:
        cur.execute(query)
        conn.commit()


# TODOASAP - REALLY SHOULD MOVE A LOT OF / ALL OF THESE (remember can always do the codesnippets in code_components anyways)

# ---- FUNCTIONS ----
# base queries used for the initial display of the web app using the default store, and other basic queries like valid dates

#@st.experimental_singleton # is shared across all users connected to the app so can be accessed from multiple threads # TODOASAP <<< this??
@st.cache
def base_queries() -> dict: # could place this in db integration in future btw
    """ run and cache these base queries, grabs a chunk of base data from 'Chesterfield' for the initially loaded dashboard """   
    
    # for min/max date ranges
    base_first_valid_date = get_from_db("SELECT current_day FROM BizInsights ORDER BY current_day ASC LIMIT 1")
    base_first_valid_date = base_first_valid_date[0][0]
    base_last_valid_date = get_from_db("SELECT current_day FROM BizInsights ORDER BY current_day DESC LIMIT 1")
    base_last_valid_date = base_last_valid_date[0][0]

    # bundle everything up in a dictionary so it's much easier (and slightly less computationally expensive) to extract - variable names are the keys
    base_dictionary = {"valid_dates":(base_first_valid_date, base_last_valid_date)}

    # return the bundle up data in a dictionary
    return(base_dictionary)


def create_stores_query(user_stores_list:list, dev_mode:bool = False) -> str:
    """ 
    //desc : for creating the dynamic query for store selection, given list should not be None 
    //param : user_stores_list = list of the stores the user has selected from the multi-select
                dev_mode = turns on/off the echo which prints the code that has run as live code snippets 
    //returns : stores part of the final query as a string
    """
    if dev_mode:
        with st.expander("Porfolio Mode [Function] : create_stores_query()"):
            with st.echo():
                st.markdown("###### Add Stores To See The Magic")

                # stored as vars incase revert to older version which had more dynamic options
                store_var = "store_name"
                where_part = "WHERE " 

                # if only one store then the query is simply the store itself
                if len(user_stores_list) == 1:
                    return(f"{where_part}{store_var} = '{user_stores_list[0]}'")
                # if all options removed from multi-select by user
                elif len(user_stores_list) == 0 or user_stores_list[0] == "":
                    return(f"{where_part}{store_var} = 'Chesterfield'")
                # else if the length is larger than 1 then we must join the stores dynamically for the resulting query
                else:
                    # see this change dynamically by adding 2 and then 3+ stores
                    final_query = f" OR {store_var}=".join(list(map(lambda x: f"'{x}'",user_stores_list)))
                    # show the resulting dynamic string
                    st.code(final_query, "sql")
                    final_query = f"{where_part} ({store_var}=" + final_query + ")"
                    # show the resulting dynamic string
                    st.code(final_query, "sql")
                    # return the result
                    return(final_query)
    else:
        store_var = "store_name"
        where_part = "WHERE " 
        if len(user_stores_list) == 1:
            return(f"{where_part}{store_var} = '{user_stores_list[0]}'")
        elif len(user_stores_list) == 0 or user_stores_list[0] == "":
            return(f"{where_part}{store_var} = 'Chesterfield'")
        else:
            final_query = f" OR {store_var}=".join(list(map(lambda x: f"'{x}'",user_stores_list)))
            final_query = f"{where_part} ({store_var}=" + final_query + ")"
            return(final_query)


@st.cache
def get_main_items_from_stores_updated(user_store:str) -> list:
    """ get only main item name for user select dropdowns using new, updated/improved productpricing table instead of complicated inner join  """
    # if london update the name so it matches the col
    if "London" in user_store:
        user_store = user_store.replace(" ","_") 
    # grab the main items for the selected store from the database
    get_main_items = get_from_db(f"SELECT DISTINCT item_name FROM ProductPricing WHERE {user_store.lower()} = 1")
    main_items_list = []
    for item in get_main_items:
        main_items_list.append(item[0])
    # return the result
    return(main_items_list)

@st.cache
def get_flavours_for_item_updated(user_store:str, user_item:str) -> list:
    """ uses newly updated product pricing table for speed/efficency of query """
    # if london update the name so it matches the col
    if "London" in user_store:
        user_store = user_store.replace(" ","_") 
    item_store_flavours = get_from_db(f"SELECT DISTINCT item_flavour FROM ProductPricing WHERE {user_store} = 1 AND item_name = '{user_item}'")
    item_store_flavours_list = []
    # convert the returned tuples into a list (don't print required as streamlit prints (to web app) list comprehensions that aren't assigned to variables)
    dont_print_flavs = [item_store_flavours_list.append(flavour[0]) for flavour in item_store_flavours]
    return(item_store_flavours_list)


# ---- OLD FUNCTIONS, DON'T USE ----

def get_flavours_for_item(user_store:str, user_item:str) -> list:
    """ OLD - computationally expensive inner join """
    item_flavours = get_from_db(f"SELECT DISTINCT i.item_flavour FROM CustomerItems i INNER JOIN CustomerData d on (i.transaction_id = d.transaction_id) WHERE d.store = '{user_store}' AND i.item_name = '{user_item}';")
    item_flavours_list = []
    # convert the returned tuples into a list (don't print required as streamlit prints (to web app) list comprehensions that aren't assigned to variables)
    dont_print_2 = [item_flavours_list.append(flavour[0]) for flavour in item_flavours]
    return(item_flavours_list)

def get_main_items_from_stores(user_store:str) -> list:
    """ OLD - computationally expensive inner join """
    # get only main item name for user select dropdowns
    get_main_item = get_from_db(f"SELECT DISTINCT i.item_name FROM CustomerItems i INNER JOIN CustomerData d on (i.transaction_id = d.transaction_id) WHERE d.store = '{user_store}'")
    main_item_list = []
    for item in get_main_item:
        main_item_list.append(item[0])
    # return the result
    return(main_item_list)

# END OLD 


def create_flavour_query(flavour_x_is_null:bool, multi_flav_selector_x:list, final_item_flavours_list_x:list, dev_mode:bool = False) -> str:
    """
    dynamically create the flavour part of the query based on the users input,
    including cases where there is no flavour for the item, and also if all options were removed by the user (just to be awkward)
    """

    if dev_mode:
        with st.expander("Portfolio Mode [Function] : create_flavour_query()"):   
            with st.echo(): 
                # first split flavour selector dynamically if multi select, requires bracket notation for AND / OR statement
                # only required for flavour, as size can only be regular or large

                # if only 1 flavour then 2 cases to deal with
                if len(multi_flav_selector_x) == 1:
                    # check if this item has flavours by checking what was returned by the database for this item
                    if multi_flav_selector_x[0] is None:
                        # if there is no flavour for this then set the query to validate on NULL values (no = operator, no '')
                        final_flav_select = f"i.item_flavour = ''"
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
                        final_flav_select = f"i.item_flavour = ''"
                    else:      
                        # else (if the first flavour select option isn't None) then it means the user removed all from valid flavours from multiselect   
                        # ternary statement prints None instead of a blank space if there is used removed all selections for flavours else prints the default flavour that's being used       
                        final_flav_select = f"i.item_flavour='{final_item_flavours_list_x[0] if final_item_flavours_list_x[0] != '' else 'None'}'"
                        # so add the 'default', aka first item in the flavours list, to the query and inform the user of what has happened          

                # since None can be in the box we just remove it if it gets added to the query and replace with a none string
                final_flav_select = final_flav_select.replace("None","")
                # return the result
                return(final_flav_select, flavour_x_is_null)
    
    else:

        # first split flavour selector dynamically if multi select, requires bracket notation for AND / OR statement
        # only required for flavour, as size can only be regular or large

        # if only 1 flavour then 2 cases to deal with
        if len(multi_flav_selector_x) == 1:
            # check if this item has flavours by checking what was returned by the database for this item
            if multi_flav_selector_x[0] is None:
                # if there is no flavour for this then set the query to validate on NULL values (no = operator, no '')
                final_flav_select = f"i.item_flavour = ''"
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
                final_flav_select = f"i.item_flavour = ''"
            else:      
                # else (if the first flavour select option isn't None) then it means the user removed all from valid flavours from multiselect   
                # ternary statement prints None instead of a blank space if there is used removed all selections for flavours else prints the default flavour that's being used       
                final_flav_select = f"i.item_flavour='{final_item_flavours_list_x[0] if final_item_flavours_list_x[0] != '' else 'None'}'"
                # so add the 'default', aka first item in the flavours list, to the query and inform the user of what has happened          

        # since None can be in the box we just remove it if it gets added to the query and replace with a none string
        final_flav_select = final_flav_select.replace("None","")
        # return the result
        return(final_flav_select, flavour_x_is_null)


def create_size_query(multi_size_selector_x:list) -> str:
    """ create the size part of the query based on which sizes the user selected """
    # split size selector if multi select, only ever Regular or Large so easier to do
    if len(multi_size_selector_x) == 1:
        final_size_select = f"i.item_size='{multi_size_selector_x[0]}'"
    elif len(multi_size_selector_x) == 0:
        final_size_select = "i.item_size='Regular'"
    else:
        final_size_select = f"(i.item_size='{multi_size_selector_x[0]}' OR i.item_size = '{multi_size_selector_x[1]}')"
    # return the result
    return(final_size_select)


# TODOASAP - BACK TO CACHED AND TEST ON 3.9 - 3.7, REALLY WANT THIS CACHED IF POSSIBLE 
# TODO - ALSO THE CONCAT ORDER NAMING THING! (skip for now but note elsewhere when tidying this shit)
#@st.cache()
def get_hour_cups_data(flavour_x_concat, selected_stores_x, select_date, item_selector_x, final_size_select_x, final_flav_select_x, after_concat:str) -> list[tuple]:
    """ 
    groups together all of the complex queries in to the final query and returns the data
    isn't cached, but should be, works locally but streamlit cloud hosting no likey hash type datetime - to test using v3.7 to v3.9 to see if improves
    returns list of tuples -> [(count, hour, flavour x item x size x store string, date as datetime.date)]
    """
    # ---- The Query Breakdown ----
    # select count of names of each unique item sold, with the unique items = concatinated name + size + flavour (if not null)
    # if flavour is null remove it from the concat in the select query
    # then group each item by unique flavour + name + size 
    # and for each hour of the day (e.g. 20 large mocha @ 9am, 15 large mocha @ 10am...)
    # inner joins between customerdata -> essentially raw data that has been cleaned/valdiated
    # and customeritems -> customer transactional data that has been normalised to first normal form (all unique records, all single values)
    # joined on the transaction id (which is the field that allows the transactional 'customeritems' table to adhere to 1nf)
    # where store, date, and item name are the users selected values

    # [new] note after concat parameter is for adding in a date column to the return values for separating results based on the dates

    # update concat order based readabililty/altering the string for readability (maybe add store), note have to take the comma into consideration
    cups_by_hour_query = f"SELECT COUNT(i.item_name) AS cupsSold, HOUR(d.time_stamp) AS theHour,\
                            CONCAT({flavour_x_concat} i.item_name, i.item_size, store) AS item {after_concat} FROM CustomerItems i\
                            INNER JOIN CustomerData d ON (i.transaction_id = d.transaction_id) WHERE store = '{selected_stores_x}'\
                            AND DATE(d.time_stamp) {select_date} AND i.item_name = '{item_selector_x}' AND {final_size_select_x}\
                            AND {final_flav_select_x} GROUP BY d.time_stamp, item"
    logger.info("Final hour x cups Altair chart query (get_hour_cups_data) - {0}".format(cups_by_hour_query)) 
    hour_cups_data = get_from_db(cups_by_hour_query)  
    # return the resulting list of tuples [(count, hour, flavour x item x size x store string, date as datetime.date)]
    return(hour_cups_data, cups_by_hour_query) 


def decide_to_include_flavour(flavour_x_is_null:bool) -> str:
    """ depending on if there is a flavour or not, return either i.itemflavour, or '' based on what is needed for the query """
    if flavour_x_is_null == False:
        # if flag is False, a valid flavour is included in the flavour part of the query (AND i.flavour = "x" OR i.flavour = "y")
        # so use it in the SELECT statement for finding unqiue items (unique item = item_name + unique size + unique flavour)
        return("i.item_flavour,")
    else:
        # if flag is True, the query has been adjusted for Null values in the flavour part of the query (AND i.flavour is NULL)
        # so remove it from the SELECT statement otherwise included NULL will invalidate it entirely (every i.itemname + i.itemsize will = NULL)
        return("")   


def make_date_query(user_date:tuple|datetime.date) -> str:
    """ takes the user selected date from the date selector widget (can be one or two dates), and return it as a query """
    # now what I should have done (and could still do in a refactor) is set the dates to session states before converting them to strings
    # then check last active tab to know if it was 1 or 2 dates, & *always* wipe clean 2nd date if it's only 1 date
    if isinstance(user_date, tuple):
        date_part = f" BETWEEN '{user_date[0]}' AND '{user_date[1]}' "
    else:
        # else it just stays as what it was
        date_part = f" = '{user_date}'"
    return(date_part)


def give_hour_am_or_pm(an_hour):
    """ takes an int (or float ig) and returns a string with am or pm appended to the end based on 24 hour clock """
    # cast to int just incase we get a float, could try except a type error but not expecting any other types (user can't input except dropdowns)
    an_hour = int(an_hour)
    # ternary if statement to set the string
    an_hour = f'{an_hour}pm' if an_hour > 11 else f'{an_hour}am'
    # return the result
    return(an_hour)


# TODOASAP - type hints?
def convert_raw_data_to_weeks(hour_cups_data_x_adv:list, just_cupcount_list_x_w0, just_cupcount_list_x_w1, just_cupcount_list_x_w2, just_cupcount_list_x_w3, just_cupcount_list_x_w4, just_cupcount_list_x_w5,
                                just_hour_list_x_w0, just_hour_list_x_w1, just_hour_list_x_w2, just_hour_list_x_w3, just_hour_list_x_w4, just_hour_list_x_w5,
                                just_names_list_x_w0, just_names_list_x_w1, just_names_list_x_w2, just_names_list_x_w3, just_names_list_x_w4, just_names_list_x_w5,
                                first_date_altair, end_of_first_week_date_altair, weeks_between_dates, last_date_altair) -> tuple[list]:
    """ write me - complex but not complicated, just multi-step af """

    # vars for start and end of week as datetime.date objects
    week_start_var, week_end_var = first_date_altair, end_of_first_week_date_altair

    # create loop to run for the needed weeks (sets of 7 days), starting from the first valid date, up to max of week 6, won't run for single date as weeks_between == 0
    for weeknum in range(1, weeks_between_dates + 1):

        # dict that sorts which list each loops results will be appended to
        weeks_dict = {1:(just_cupcount_list_x_w0, just_hour_list_x_w0, just_names_list_x_w0),
                        2:(just_cupcount_list_x_w1, just_hour_list_x_w1, just_names_list_x_w1),
                        3:(just_cupcount_list_x_w2, just_hour_list_x_w2, just_names_list_x_w2),
                        4:(just_cupcount_list_x_w3, just_hour_list_x_w3, just_names_list_x_w3),
                        5:(just_cupcount_list_x_w4, just_hour_list_x_w4, just_names_list_x_w4),
                        6:(just_cupcount_list_x_w5, just_hour_list_x_w5, just_names_list_x_w5),
                        }

        # set vars for the list that will be appended to based on the weeknum
        just_cupcount_list_1_week, just_hour_list_1_week, just_names_list_1_week = weeks_dict[weeknum][0], weeks_dict[weeknum][1], weeks_dict[weeknum][2]

        # the missing piece of data that would be cut off during the loop and a bool flag for knowing when to add it
        missingno_data = ()
        gone_missin = False

        # grab the cups data and add it to the relevant list
        for cups_data in hour_cups_data_x_adv[:]:

            # boolean flag to tag on the single piece of data that would be missing in each loop due to end of loop validation
            if gone_missin:
                just_cupcount_list_1_week.append(missingno_data[0])
                just_hour_list_1_week.append(missingno_data[1])
                just_names_list_1_week.append(missingno_data[2])
                # reset the flag
                gone_missin = False

            # if statement to only grab data for the given week
            if cups_data[3] >= week_start_var and cups_data[3] <= week_end_var:
                just_cupcount_list_1_week.append(cups_data[0])
                just_hour_list_1_week.append(cups_data[1])
                just_names_list_1_week.append(cups_data[2])

            # save just the date as a temporary variable so we can pop off the now completed item from this list
            just_date = cups_data[3]

            # remove the already appended elements to save time for future loops
            hour_cups_data_x_adv.remove(cups_data)

            # if reached a date thats greater than increment week var - note that it (the current cups_data) won't have been added
            if just_date > week_end_var:
                # first save this piece of data outside the loop to slot in it during the next loop (as it is not valid for 'this' week but the next)
                missingno_data = (cups_data[0], cups_data[1], cups_data[2])
                gone_missin = True
                # incremenet the vars to continue looping through the next set of 7 days
                weeknum += 1
                week_start_var = week_start_var + datetime.timedelta(days=8)
                week_end_var = week_start_var + datetime.timedelta(days=7)
                # though we're calculating and using the weeks in this loop, still dont allow the final date to be greater than the users selection
                if week_end_var > last_date_altair:
                    week_end_var = last_date_altair
                break
    
    # return a tuple of the results to unpack on receipt
    return((just_cupcount_list_x_w0, just_cupcount_list_x_w1, just_cupcount_list_x_w2, just_cupcount_list_x_w3, just_cupcount_list_x_w4, just_cupcount_list_x_w5,
            just_hour_list_x_w0, just_hour_list_x_w1, just_hour_list_x_w2, just_hour_list_x_w3, just_hour_list_x_w4, just_hour_list_x_w5,
            just_names_list_x_w0, just_names_list_x_w1, just_names_list_x_w2, just_names_list_x_w3, just_names_list_x_w4, just_names_list_x_w5))
        

# ---- INSIGHTS FUNCTIONS ----
# more functions, but just from the insights section, broken up sections for a bit more visual clarity

def create_hourcups_dataframe(just_names_list:list, just_cupcount_list:list, just_hours_list:list) -> pd.DataFrame:
    """ quickly whip up the same dataframe that was used for the chart, can be used for item 1, item 2, or both, plus 'all' or weeks """
    # primarily used for all, not weekly subsections but can be used for that too obvs if you want to add it in in the future
    df_sawce = pd.DataFrame({
        "DrinkName": just_names_list,
        "CupsSold": just_cupcount_list,
        "HourOfDay": just_hours_list
        })
    return(df_sawce)


def create_two_simple_cups_for_hour_dict(df_sawce:pd.DataFrame) -> tuple[dict, dict]:
    """ with a given dataframe, create two dictionaries (ordered/unordered) of hour as key and sum of cups sold as value """
    # get unique values in HourOfDay column to loop (returns array object so convert to list), then sort/order it
    uniqueCols = sorted(list(df_sawce['HourOfDay'].unique()))

    # get sum of cupsSold column based on condition (HourOfDay == x), added to dictionary with key = hour, value = sum of cups sold for hour
    results_dict = {}
    for value in uniqueCols:
        cupForHour = df_sawce.loc[df_sawce['HourOfDay'] == value, 'CupsSold'].sum()
        results_dict[value] = cupForHour

    # create a new dictionary from hour/cups dictionary but sorted
    sorted_by_value = dict(sorted(results_dict.items(), key=lambda x: x[1]))   
    
    # return both dictionaries, the initial unordered one, and the ordered one - technically as a tuple, then unpack it on receipt
    return(results_dict, sorted_by_value)


def get_avg_cups_sold_per_hour(hourcups_dict:dict) -> int:
    """ get the average cups sold per hour from a given dict, which is the dataframe from either item1, item2, or bothitems - unordered """
    # var to test if there is actually data, else we'll hit a ZeroDivisionError (which we could have just caught instead of if statement)
    hc_dict_size = len(hourcups_dict.values()) # dict_size = longlong (its not even a long int but i couldn't help myself... im sorry)
    # don't let something like a pesky zero division ruin everything (in case of no data)
    if hc_dict_size > 0:
        average_hourcups = sum(hourcups_dict.values()) / hc_dict_size
    else:
        average_hourcups = 0
    # return the result
    return(average_hourcups)


def create_formatted_hourcup_string_list_with_ampm(hcd_sort_by_value:dict) -> list[str]:
    """ create a list of formatted strings with times and cups sold, most importantly including am or pm suffix based on the given time """
    # lambda function appends am or pm to string based on the time, apply func to sorted dictionary items using map, then convert map object to list 
    sort_by_value_formatted_list = \
        list(map(lambda x: (f"{x[0]}pm [{x[1]} cups sold]") if x[0] > 11 else (f"{x[0]}am [{x[1]} cups sold]"), hcd_sort_by_value.items()))
    # return the result
    return(sort_by_value_formatted_list)


def get_worstbest_time_with_formattedstrings(hcd_sort_by_value:dict, hcd_sort_by_value_formatted:dict) -> tuple[int,int,str,str]:
    """ get the worst and best performing times, note worst performer is the formatted string version e.g. 10am [109 Cups Sold] """
    # try except covers case where there is no data in the dataframe (because there was no valid data to begin with)
    try:
        # list the keys (times, ordered) only, slice the first and last elements in the array (list) [start:stop:step]
        worst_time, best_time = list(hcd_sort_by_value.keys())[::len(hcd_sort_by_value.keys())-1]
        # convert them to ints (as due to the whole list sliceyness they were ofType numpy.int64)
        worst_time, best_time = int(worst_time), int(best_time)
        worst_performer, best_performer = hcd_sort_by_value_formatted[::len(hcd_sort_by_value_formatted)-1]
    except ValueError:
        # log it, and set the values to zeros
        logger.error("Papa I caught an error! - no data in dataframe (create_hourcups_insights_data)")
        worst_time, best_time, worst_performer, best_performer = 0,0,0,0
    return(worst_time, best_time, worst_performer, best_performer)


def get_dicts_for_above_below_avg_cups(hourcups_dict:dict, average_hourcups:int) -> tuple[dict, dict]:
    """ returns two new dicts for the key/value pairs above and below the average sales per hour """
    above_avg_hourcups = {}
    under_avg_hourcups = {}
    # loop the items and use simple if to decide whether the amount of cups is above or below the average sales per hour 
    for hour, cups in hourcups_dict.items():
            if cups >= average_hourcups:
                above_avg_hourcups[hour] = int(cups)
            else:
                under_avg_hourcups[hour] = int(cups)
    # return the results
    return(above_avg_hourcups, under_avg_hourcups)


# TODOASAP - TYPE HINTS HERE PLS (ik its long but pleeeeease)
# TODOASAP - also how about just dont run this, and other, functions if the df is empty duh
def create_hourcups_insights_data(hourcups_dict, hcd_sort_by_value):
    """ calls the (so far) four functions that create the hourcups insights data for either item1, item2, or bothitems """
    average_hourcups = get_avg_cups_sold_per_hour(hourcups_dict)
    # note - hcd formatted list (10am [109 cups sold]...) is only used in here, but could be returned if you want to use it
    hcd_sort_by_value_formatted_list = create_formatted_hourcup_string_list_with_ampm(hcd_sort_by_value)
    worst_time, best_time, worst_performer, best_performer = get_worstbest_time_with_formattedstrings(hcd_sort_by_value, hcd_sort_by_value_formatted_list)
    above_avg_hc, below_avg_hc = get_dicts_for_above_below_avg_cups(hourcups_dict, average_hourcups)
    overperformed_by_dict = get_more_insights(above_avg_hc, average_hourcups)
    hc_std_dict, hc_standard_deviation = get_standard_deviation_and_floor_div_dict_for_hc(hourcups_dict)
    return(average_hourcups, worst_time, best_time, worst_performer, best_performer, above_avg_hc, below_avg_hc, overperformed_by_dict, hc_std_dict, hc_standard_deviation)


def get_standard_deviation_and_floor_div_dict_for_hc(hourcups_dict:dict) -> tuple[dict, float]:
    """ standard deviation... write me """
    hourcups_values_list = []
    # get the values of the hc dict in a list (as numpy standard deviation funct wont just take dict.values())
    dont_print_me_3 = [hourcups_values_list.append(cupcount) for cupcount in hourcups_dict.values()]
    # run the standard deviation on the values of cups sold for each hour - hour cups standard deviation = hc_std
    hc_std = np.std(hourcups_values_list)
    # chuck those values into a new dict, same format as always but values are floor div vs standard deviation, e.g. value=109, sd=30, valuestd=3
    hc_std_diff_dict = {}
    for hourkey, cupsvalue in hourcups_dict.items():
        # unsure about floor division but makes sense as its standard deviation we're calculating (and i dont wanna play around with a jillion dps)
        hc_std_diff_dict[hourkey] = cupsvalue // hc_std
    # return the dict and the standard deviation
    return((hc_std_diff_dict, float(hc_std)))


def get_more_insights(above_avg_hc_dict:dict, average_hourcups:int):
    """ function for new misc insights """
    # amount overperformed by (only above average hourly sales)
    amount_above_the_avg_dict =  {}
    for hourkey, cupsvalue in above_avg_hc_dict.items():
        # populate new dictionary with key = hour (again), but the value as the difference between the sum of cups sold for the hour and the hourly average  
        amount_above_the_avg_dict[hourkey] = cupsvalue - average_hourcups
    # return the dict
    return(amount_above_the_avg_dict)


def get_price_for_item(item_selector, final_size_select, final_flav_select):
    """ write me """
    # whole thing including query kinda hacky but if it works it works
    updated_flava_select = final_flav_select.replace("= ''","is NULL")
    # straight up if this doesn't break at times i'll be shocked, only tested based on one case... so test more duh
    price_of_item = get_from_db(f"SELECT price FROM ProductPricing i WHERE item_name = '{item_selector}' AND {final_size_select} AND {updated_flava_select}")
    price_of_item = price_of_item[0][0]
    # return the price
    return(price_of_item)


# might not be a float, check please
def create_revenue_by_hour_dict_n_total_revenue(hourcups_dict:dict, price_of_item:float) -> tuple[dict, float, int]:
    """ create revenue metrics using volume of cups sold with price of each item, returns revenue per hour(dict), tot revenue, & tot volume """
    revenue_by_hour_dict = {}
    total_revenue = 0
    total_volume = 0
    for hourkey, valuecups in hourcups_dict.items():
        revenue_by_hour_dict[hourkey] = valuecups * price_of_item
        total_revenue += revenue_by_hour_dict[hourkey]
        total_volume += valuecups
    # return the results
    return(revenue_by_hour_dict, total_revenue, total_volume)


def get_hours_at_highest_standard_deviation(hc_std_dict:dict) -> list:
    """ uses hour dict to get the hours over the standard deviation - sd was calculated using floor div so there can be multiple hours """
    # get the highest/max standard deviations value 
    highest_sd = max(list(hc_std_dict.values())) 
    # loop the items to return the keys only if it matches the highest standard deviation value - incase there is more than one
    highest_sd_hours = [key for key, value in hc_std_dict.items() if value == highest_sd]
    # return the result
    return(highest_sd_hours)


def create_hc_1_vs_2_difference_in_revenue_by_hour_dict(rev_by_hour_dict_1:dict, rev_by_hour_dict_2:dict) -> dict[int:float]:
    """ create dictionary of the difference between item 1 and item 2 revenue per hour """
    diff_in_revenue_by_hour_dict = {}
    # random af comment but i looooooove stuff like this, mmm complex for loop with multiple zips, dict items, placeholder, unpacking, mmmmmmmmmmm
    for (hourkey, revvalue), (_, revvalue2) in zip(rev_by_hour_dict_1.items(), rev_by_hour_dict_2.items()):
        # important to note that minus means item 2 had more sales as we're doing item 1 minus item 2 (just remove minus and its gravy)
        # also cast these to python number types as they were numpy types before this which is fine, except until it isn't and aint nobody got time for dat
        diff_in_revenue_by_hour_dict[int(hourkey)] = float(revvalue - revvalue2) # hourkey will be the same either way since using the unordered versions (so 9am - 16pm)
    return(diff_in_revenue_by_hour_dict)


def combine_both_items_data_lists_for_df(first_item_list:list, second_item_list:list): 
    """ combined data from both items (1&2) to get generalised insights, used for creating df, is not the same as 'all' dates, both here means stores """ 
    # copy first, as its a list - despite the lack of type hints :(
    just_list_both_for_df = first_item_list.copy() 
    # then extend
    just_list_both_for_df.extend(second_item_list) 
    # return the result
    return(just_list_both_for_df)


def extend_list_1_with_list_2(the_list_1:list[list], the_list_2:list[list]):
    """ extended the first lists with the second lists for the final dataframe (since we only pass it one dataset) """
    the_final_list = []
    # zip the lists together to loop them
    for list_1, list_2 in zip(the_list_1, the_list_2):
        list_1.extend(list_2)
        the_final_list.append(list_1)
    return(the_final_list)


def extend_all_lists(just_cupcount_list_x_all, just_hour_list_x_all, just_names_list_x_all, 
                    just_cupcount_list_x_w0,just_cupcount_list_x_w1,just_cupcount_list_x_w2,just_cupcount_list_x_w3,just_cupcount_list_x_w4,just_cupcount_list_x_w5,
                    just_hour_list_x_w0,just_hour_list_x_w1,just_hour_list_x_w2,just_hour_list_x_w3,just_hour_list_x_w4,just_hour_list_x_w5,
                    just_names_list_x_w0,just_names_list_x_w1,just_names_list_x_w2,just_names_list_x_w3,just_names_list_x_w4,just_names_list_x_w5):
    """ the 'all' lists are just the first tab that is the sum total of all the weeks, so extend all the week lists together to get that result """
    # 'all dates' is just everything together so extend the 'all' lists with everything from the 'week_x' lists
    cupcount_weeks_list = [just_cupcount_list_x_w0,just_cupcount_list_x_w1,just_cupcount_list_x_w2,just_cupcount_list_x_w3,just_cupcount_list_x_w4,just_cupcount_list_x_w5]
    for cupcount_list in cupcount_weeks_list:    
        just_cupcount_list_x_all.extend(cupcount_list)

    justhour_weeks_list = [just_hour_list_x_w0,just_hour_list_x_w1,just_hour_list_x_w2,just_hour_list_x_w3,just_hour_list_x_w4,just_hour_list_x_w5]
    for justhour_list in justhour_weeks_list:
        just_hour_list_x_all.extend(justhour_list)

    justnames_weeks_list = [just_names_list_x_w0,just_names_list_x_w1,just_names_list_x_w2,just_names_list_x_w3,just_names_list_x_w4,just_names_list_x_w5]
    for justnames_list in justnames_weeks_list:
        just_names_list_x_all.extend(justnames_list)

    return((just_cupcount_list_x_all, just_hour_list_x_all, just_names_list_x_all))


def create_dataframe_setup_chart(just_names_list_1_range, just_cupcount_list_1_range, just_hour_list_1_range):
    """ create the dataframes and resulting altair chart data (barchart + text) for a given range and return the results for rendering """
    # idelly would run a small formatting function on just_names to make them more readable but is fine for now

    # create the dataframe
    sawce = create_hourcups_dataframe(just_names_list_1_range, just_cupcount_list_1_range, just_hour_list_1_range)

    # customising altair chart personal notes - particularly for colouring
    # set1 blue red start, too powerful but contrasting, category10 orange blue start - for reference see links below
    # https://vega.github.io/vega/docs/schemes/  https://altair-viz.github.io/user_guide/customization.html#color-schemes

    # setup barchart
    bar_chart = alt.Chart(sawce).mark_bar().encode(
        color=alt.Color('DrinkName', scale=alt.Scale(scheme='category10'), legend=alt.Legend(title = "Product Name", orient="left")),  
        x="sum(CupsSold):Q",
        y="HourOfDay:N",
    ).properties(height=300)

    # setup text labels for barchart
    chart_text = alt.Chart(sawce).mark_text(dx=-12, dy=3, color='white', fontSize=12, fontWeight=600).encode(
        x=alt.X('sum(CupsSold):Q', stack='zero'),
        y=alt.Y('HourOfDay:N'),
        detail='DrinkName:N',                   
        text=alt.Text('sum(CupsSold):Q', format='.0f')
    )
    # return the result
    return((bar_chart, chart_text))


# ---- PURELY DATE/TIME BASED FUNCTION ----

def make_dt_next_week_basic(display_date:str, add_days:int = 8) -> str:
    """
    //desc - takes string date, makes it dt object, adds 8 days to it so it starts from the next week,
                optional add_days param for also specifying the amount of days which defaults to 8
                note doesn't do anything with start date of week i.e. monday
    //param - date [as string], optional amount of days [as int] 
    //returns - date + 8 days [as string]
    """
    # cover to datetime object
    date_as_dt = datetime.datetime.strptime(display_date, '%Y-%m-%d').date()
    # use the user defined days else use 8 days to get the next week, note is not 7 as its exclusive at one end
    days_to_add = add_days if add_days != 8 else 8
    # add the amount of days to the given date
    date_next_week = date_as_dt + datetime.timedelta(days=days_to_add)
    # return the result
    return(date_next_week)


def get_commencing_week_from_weektab(display_date:str, weektab:int):
    """
    //desc - for commencing week using only the tab numbers (e.g. 1, 2, 3, etc), but not week 0 as doesn't need to be altered
                takes the week number and runs get next week function for the needed amount of extra days from the first date
                note - thinking about it should have done this recursively and returned as a chunk (tuple) ?
    //param - date [as string], tab of the week number ranging from 1 to 5 [as int]
    //returns - date + 8 days [as string]
    """
    # get the amount of days to add from the tabs week number * 7 days, + 1
    extra_days_to_add = (weektab*7) + 1 
    # call function to make the calculation and get the result
    next_week_date = make_dt_next_week_basic(display_date, extra_days_to_add)
    # reformat the final date so its prettier
    clean_next_week_date = datetime.datetime.strftime(next_week_date, "%d %B %Y")
    # return the result
    return(clean_next_week_date)


# ---- ERRORS & DEBUGGING FUNCTIONS ----

# TODOASAP - doesnt log but it should duh!
def thats_how_we_play_handy_hands(var_chunk:tuple = (), play_handy_hands:bool = False):
    """ turn on to print some handy variables to console... its a rick and morty reference [https://www.youtube.com/watch?v=0HAbLnpq52o&ab_]"""
    # use bool and a function as its easier to turn on off as a chunk and make bulk changes
    if play_handy_hands:
        # unpack vars
        hourcups_dict, overperformed_by_dict, hc_std_dict, hc_std, worst_time, best_time,\
        worst_performer, best_performer, above_avg_hc, below_avg_hc, revenue_by_hour_dict,\
        price_of_item, total_revenue, total_volume = var_chunk
        # print the handy vars
        print("hourcups_dict", hourcups_dict)  # same as hcd_sort_by_value_1
        print("overperformed_by_dict", overperformed_by_dict)
        print("hc_std_dict", hc_std_dict)
        print("hc_std", hc_std)
        print("worst_time, best_time", worst_time, best_time)
        print("worst_performer, best_performer", worst_performer, best_performer)
        print("above_avg_hc, below_avg_hc", above_avg_hc, below_avg_hc)
        print("revenue_by_hour_dict", revenue_by_hour_dict)
        # should print revenue_diff_by_hour_dict but it's not chunked with everything else so leaving it
        print("price for item = ", f"$", price_of_item, sep='')
        print("total revenue for item = ", f"$", f"{total_revenue:.2f}", sep='')
        print("total_volume", total_volume)


# old error message that have resolved the error for, but may reimplement the display part in future so leaving as function
def display_db_conn_error_msg():
    """ print error message and provide buttons to refresh and fix the app """
    # print the message
    ERROR_MSG_1 = """(╯°□°）╯︵ ┻━┻\n
    Critical Error Averted\n
    It's A DB Connection Bug [not a duplicate error, silly streamlit]\n
    Change any field or push the button in the sidebar/below to rerun"""
    st.error(ERROR_MSG_1)
    # pressing any button (not necessarily these) will reset the app state, but provide some clear options to the user
    st.button("Push Me - I Don't Bite", key="pushme2")
    st.sidebar.warning("Push The Button To Re-Run")
    st.sidebar.button("ReRun App", key="pushme1")


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


    # ---- CREATE SESSION STATES ----
    # initialise session state vars if there are none, these (dictionaries) are persisted throughout page reruns
    if "last_active_date_tab" not in st.session_state:
        # last active tab defaults to 2 (this is the initial tab number (key) for between 2 dates select - & is currently more stable)
        st.session_state["last_active_date_tab"] = 2 
    
    # want quicker/easier access to dates as datetime.date object so adding this in
    if "active_date_1" not in st.session_state:
        st.session_state["active_date_1"] = datetime.date(2020, 7, 1) # 1 = start date
    if "active_date_2" not in st.session_state:
        st.session_state["active_date_2"] = datetime.date(2000, 1, 1) # 2 = end date (if valid, hence different default)


    # ---- SIDEBAR ----

    # portfolio/developer mode toggle
    with st.sidebar:

        dev_mode = st.checkbox(label="Portfolio Mode ", key="devmode-insights")
        if dev_mode:
            DEV_MODE_INFO = """
            Portfolio Mode Active\n
            Check out expanders to see live code blocks
            """
            st.info(DEV_MODE_INFO)

        st.write("##")
        st.markdown("#### Advanced Mode")
        st.write("For more advanced query options")
        advanced_options_1 = st.checkbox("Advanced Mode", value=True, disabled=True) 

        st.write("##")
        st.markdown("*Note - Dashboard is designed for desktop*")
    

    # ---- HEADER ----

    topcol1, topcol2 = st.columns([1,8])
    topcol2.markdown("# Insights Title")
    try:
        # TODOASAP - edit the image so is smaller (currently is 512x512)
        topcol1.image("imgs/insight_chart.png", width=120)
    except:
        st.write("")
    st.write("##")


    # ---- USER SELECTS + VISUAL CLARITY ----

    def last_active_tab(the_tab:str = "off", want_return:bool = False) -> None|int:
        """ 
        //desc - write me
        //param - write me
        //returns - for technical return, its the date from the last active tab [as datetime.date object]
                    for the actual (stupid) return its the last active tab number/key [as int]
        """

        # use a session state var to persist the last active tab
        last_active_date_tab = st.session_state["last_active_date_tab"]

        # new session state for easy date display because last active date tab sessionstate is kinda buggy and running outside of on_change so might remove
        # for single day
        if last_active_date_tab == 1:
            st.session_state["active_date_1"] = selected_date_1
            # guna just check if date 2 is this date, if it is dont print it
            st.session_state["active_date_2"] = datetime.date(2000, 1, 1)
        # for between 2 dates    
        elif last_active_date_tab == 2:
            st.session_state["active_date_1"] = selected_date_2_start
            st.session_state["active_date_2"] = selected_date_2_end
        # for single week (bit long winded but is fine)
        elif last_active_date_tab == 3:
            # for single week first grab just the date from the string
            to_make_date = selected_date_3[10:]
            # then make a query to get the date in the future (yes ik, i actually have a function for this now but just leaving this as is for now)
            end_of_week = str(make_dt_next_week_basic(to_make_date, 6))
            # convert these strings to have times so that strptime actually works on them
            to_make_date = to_make_date + " 00:00:00.000000"
            end_of_week = end_of_week + " 00:00:00.000000"
            # convert the string dates to datetime objects, and then to date objects 
            date_1 = datetime.datetime.strptime(to_make_date, '%Y-%m-%d %H:%M:%S.%f').date()
            date_2 = datetime.datetime.strptime(end_of_week, '%Y-%m-%d %H:%M:%S.%f').date()
            # set the result to session states as the correct type
            st.session_state["active_date_1"] = date_1
            st.session_state["active_date_2"] = date_2

        # ngl this is so dumb, if want return just use the session state var but whatever
        if want_return:
                # switch case to either return the last active tab or store it
                return(last_active_date_tab) 
        else:
            st.session_state["last_active_date_tab"] = the_tab


    # TODOASAP 
    # want image or whatever of the date on the right too and maybe since this is a change between tabs thing 
    # DEFO WANT THE DATE/S DISPLAYED CLEARLY REGARDLESS (do this first ig and skip the images for now)

    userSelectCol, _, storeImg1, storeImg2, storeImg3, storeImg4, storeImg5 = st.columns([5,1,1,1,1,1,1]) 
    with userSelectCol:

        # ---- STORE SELECT ----
        selected_stores_1 = st.multiselect("Choose The Store/s", options=base_stores_list, default=["Chesterfield"])
        # run the query
        stores_query = create_stores_query(selected_stores_1, dev_mode)

    userSelectCol2, _, calendarCol = st.columns([5,1,5]) 
    with userSelectCol2:
        

        # ---- DATE SELECT ----
        #dateTab2, dateTab1, dateTab3, dateTab4, dateTab5, dateTabs6 = st.tabs(["Between 2 Dates", "Single Day", "Single Week", "Mulitple Weeks", "Full Month", "All Time"]) 
        dateTab2, dateTab1, dateTab3, dateTab4 = st.tabs(["Between 2 Dates", "Single Day", "Single Week", "Mulitple Weeks"]) 
        
        def force_date_run_btn(run_button_key:str):
            """ write me """
            # strip the key to just it's number
            keynumb = int(run_button_key[-1:])
            last_active_tab(keynumb)

        # ---- SINGLE DAY ----
        with dateTab1:
            selected_date_1 = st.date_input("What Date Would You Like Info On?", datetime.date(2022, 7, 5), max_value=last_valid_date, min_value=first_valid_date, on_change=last_active_tab, args=[1], key="TODO")  
            st.write("##")
            st.button("Get Insights For This Date", help="To Get New Insights : change the date, press this button, use physic powers", key="run_1", on_click=force_date_run_btn, args=["run_1"])

        # ---- BETWEEN 2 DAYS ----
        with dateTab2:
            selected_date_2_start = st.date_input("What Start Date?", datetime.date(2022, 7, 1), max_value=last_valid_date, min_value=first_valid_date, on_change=last_active_tab, args=[2], key="TODO2")  
            selected_date_2_end = st.date_input("What End Date?", datetime.date(2022, 7, 8), max_value=last_valid_date, min_value=first_valid_date, on_change=last_active_tab, args=[2], key="TODO3")
            st.write("##")
            st.button("Get Insights For These Dates", help="To Get New Insights : change the date, press this button, use physic powers", key="run_2", on_click=force_date_run_btn, args=["run_2"])
            # TODO - print days between dates here 

        # ---- SINGLE WEEK ----
        with dateTab3:
            stores_avail_weeks = sorted(get_from_db(f"SELECT DISTINCT WEEKOFYEAR(current_day) FROM BizInsights {stores_query}"))
            first_day_of_week_list = [] # for zipping with stores_available_weeks (must ensure order is correct)
            for weeknum in stores_avail_weeks:
                first_day_of_week = get_from_db(f"SELECT '2022-01-01'+INTERVAL ({weeknum[0]}-WEEK('2022-01-01', 1))*7 - WEEKDAY('2022-01-01') DAY")
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
            st.button("Get Insights For This Week", help="To Get New Insights : change the date, press this button, use physic powers", key="run_3", on_click=force_date_run_btn, args=["run_3"])        
        
        # ---- MULTIPLE WEEKS [NOT IMPLEMENTED YET] ----
        with dateTab4:
            # ensure it isn't going to error due to the default
            if len(stores_available_weeks) > 1:
                multiweek_default = [stores_available_weeks[0],stores_available_weeks[1]]
            else:
                multiweek_default = [stores_available_weeks[0]]
            selected_date_4 = st.multiselect("Which Weeks?", options=stores_available_weeks, default=multiweek_default, key="TODO5", help="See 'Single Week' for week commencing date", on_change=last_active_tab, disabled=True, args=[4])
            # TODO - obvs have this on the right hand side with the img ting and ig like completeness too (total days && available days)
            st.info("Functionality Coming Soon")
            #st.write(f"Total Days = {len(selected_date_4) * 7}")
            st.write("##")
            st.button("Get Insights For These Weeks", help="To Get New Insights : change the date, press this button, use physic powers", key="run_4", on_click=force_date_run_btn, args=["run_4"], disabled=True)        

    # var that holds the key/on_change args from each date select plus the variables that store the result, used for getting the last active tab
    use_vs_selected_date_dict = {1:selected_date_1, 2:(selected_date_2_start, selected_date_2_end), 3:selected_date_3, 4:selected_date_4}

    def set_selected_date_from_last_active_tab(date_dict:dict) -> datetime.date|tuple: 
        """ use the on_change arguments (which is just the key as an int) from each date select and returns the variables holding the relevant dates """
        use_date = last_active_tab(want_return=True)

        # option 3 is week number with week beginning so we need the date at week end too
        if st.session_state["last_active_date_tab"] == 3:
            to_make_date = date_dict[use_date][10:]
            end_of_week = get_from_db(f"SELECT DATE_ADD('{to_make_date}', INTERVAL 6 DAY);")
            return((to_make_date, end_of_week[0][0]))

        # TODOASAP 
        # 4 IS LITERALLY THE SAME AS OPTION 3, IT JUST BECOMES AN AND STATEMENT 
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
        """ prints out the 5 store images as either on or off (saturated) based on whether they were selected, see comment for refactor """
        # if you actually pass in the dict (and they always have cols + imgs, and same key names) then this could be reformatted to be multipurpose
        for store_name in base_stores_list:
                if store_name in selected_stores_list:
                    img_dict[store_name]["col"].image(img_dict[store_name]["on"])
                else:
                    img_dict[store_name]["col"].image(img_dict[store_name]["off"])


    # handle error in case the images can't be found (tho most likely is due to backslash not forward slash so just fix that duh)
    try:
        print_on_off_stores(selected_stores_1, stores_img_dict)
    except FileNotFoundError:
        pass


    # ---- VISUAL CLARITY CALENDAR PRINT ----

    # TODOASAP - make me dynamic for other img stuff
    if st.session_state["last_active_date_tab"] == 3:
        june_start_weeknumb = 22
        weeknumberselect = int(selected_date_3[5:8])
        highlight_week = weeknumberselect - june_start_weeknumb
        # calendar_highlight = arty.highlight_calendar(highlight_week, weeknumberselect, week_array)
        calendar_highlight = arty.highlight_calendar(highlight_week, weeknumberselect)
        calendarCol.image(calendar_highlight) 


    # ---- DIVIDER ----
    # i divide things
    st.write("---")


    # ---- THE COMPARISION CHARTS ---- 

    # ALTAIR CHART product sold by hour of day
    with st.container():

        # title and column setup
        st.write(f"### :bulb: Dynamic Insights - Compare & Contrast") 

        # select any item from the store for comparison
        item1Col, itemInfoCol, item2Col = st.columns([2,1,2])

        # ---- USER SELECTS ----

        with item1Col:
            # user select store and then item 1
            store_selector_1 = st.selectbox(label=f"Which Store Do You Want To Choose An Item From?", key="store_sel_1", options=selected_stores_1, index=0, help="For more stores update the above multiselect")
            final_main_item_list = get_main_items_from_stores_updated(store_selector_1)
            item_selector_1 = st.selectbox(label=f"Choose An Item From Store {store_selector_1}", key="item_selector_1", options=final_main_item_list, index=0) 
            
        with item2Col:
            # show the second store in the list if there is more than one store
            store_select_2_index = 1 if len(selected_stores_1) > 1 else 0
            # user select store and then item 2
            store_selector_2 = st.selectbox(label=f"Which Store Do You Want To Choose An Item From?", key="store_sel_2", options=selected_stores_1, index=store_select_2_index, help="For more stores update the above multiselect")
            final_main_item_list = get_main_items_from_stores_updated(store_selector_2)
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

        # log control flow
        logger.debug("Get list of flavours from the db, for the users selected item") # actually tuples not list but whatever

        with item1Col:
            #final_item_flavours_list = get_flavours_for_item(selected_stores_1, item_selector_1)
            final_item_flavours_list = get_flavours_for_item_updated(selected_stores_1, item_selector_1)
            multi_flav_selector_1 = st.multiselect(label=f"Choose A Flavour For {item_selector_1}", key="multi_flav_select_1", options=final_item_flavours_list, default=final_item_flavours_list[0])
            multi_size_selector_1 = st.multiselect(label=f"Choose A Size For {item_selector_1}", key="multi_size_select_1", options=["Regular","Large"], default="Regular")

        with item2Col:
            #final_item_flavours_list_2 = get_flavours_for_item(selected_stores_2, item_selector_2)
            final_item_flavours_list_2 = get_flavours_for_item_updated(selected_stores_2, item_selector_2)
            multi_flav_selector_2 = st.multiselect(label=f"Choose A Flavour For {item_selector_2}", key="multi_flav_select_2", options=final_item_flavours_list_2, default=final_item_flavours_list_2[0])
            multi_size_selector_2 = st.multiselect(label=f"Choose A Size For {item_selector_2}", key="multi_size_select_2", options=["Regular","Large"], default="Regular")

        # because why not make clear to the user when you know they're trying to break stuff
        if len(multi_flav_selector_1) == 0 or len(multi_flav_selector_2) == 0 or len(multi_size_selector_1) == 0 or len(multi_size_selector_2) == 0:
            with st.sidebar:
                JUDGING_MESSAGE = """You just gotta be awkward huh...\n
                *judges you*
                """
                # is literally the only way to get multiline warning/error/info boxes
                st.warning(JUDGING_MESSAGE)


        # ---- FLAVOUR & SIZE SUB-QUERY CREATION ----

        # if flavour is Null/None then we need to tweek the initial SELECT to get the correct (unique) item name (flavour is the only case with Null values so simple boolean flag is fine)
        flavour_1_is_null = False
        flavour_2_is_null = False
        # call functions that dynamically creates the complex flavour part of the query, plus the simpler size query
        final_flav_select_1, flavour_1_is_null = create_flavour_query(flavour_1_is_null, multi_flav_selector_1, final_item_flavours_list, dev_mode)
        final_size_select_1 = create_size_query(multi_size_selector_1)
        final_flav_select_2, flavour_2_is_null = create_flavour_query(flavour_2_is_null, multi_flav_selector_2, final_item_flavours_list_2)
        final_size_select_2 = create_size_query(multi_size_selector_2)
        # decide how flavour will be included in the final query based on previous flags
        flavour_1_concat = decide_to_include_flavour(flavour_1_is_null)
        flavour_2_concat = decide_to_include_flavour(flavour_2_is_null)

        # due to the way streamlit works with rerunning the entire app on update, occassional bugs slip in
        # this covers the last active tab being reset to a less stable state, and forces it to the more stable 'between two dates' option
        if st.session_state["last_active_date_tab"] == 4: # think i might be hopping around between int and str for this var btw
            last_active_tab(2)
            selected_date = set_selected_date_from_last_active_tab(use_vs_selected_date_dict)
            selected_date = make_date_query(selected_date)

        # the key/int of the last active tab for deciding whether want results to have week based tab display
        # legit should just use the session state here instead of the functions return value duhhhhhhhhhh
        active_tab_key = last_active_tab(want_return=True)

        # if is a "BETWEEN" date query, then add in new column after the CONCAT part of the SELECT statement to also include the date (for making tabs)
        if active_tab_key != 1:
            post_concat_addition = ", DATE(d.time_stamp) AS theDate "
        else:
            post_concat_addition = " "

        # log last active tab before running function
        logger.info("last active date tab = {0}".format(active_tab_key))
        # get data for left side
        hour_cups_data_1_adv, the_query_1 = get_hour_cups_data(flavour_1_concat, selected_stores_1, selected_date, item_selector_1, final_size_select_1, final_flav_select_1, post_concat_addition)
        # get data for right side
        hour_cups_data_2_adv, the_query_2 = get_hour_cups_data(flavour_2_concat, selected_stores_2, selected_date, item_selector_2, final_size_select_2, final_flav_select_2, post_concat_addition)
        st.write("##")

        if dev_mode:
            st.write("---")
            st.write("##")
            st.markdown("##### Portfolio Mode - The Resulting Dynamic Queries")
            st.write("")
            with st.expander(label="The Query : Item 1"):
                stripped_query = str(the_query_1).replace("          ","").replace("        "," ")
                st.code(stripped_query, "sql")
            with st.expander(label="The Query : Item 2"):
                stripped_query = str(the_query_2).replace("          ","").replace("        "," ")
                st.code(stripped_query, "sql")
            st.write("---")

        # ---- CREATE AND PRINT ALTAIR CHART OF RESULTS ----

        # PORTFOLIO - ADD THIS STUFF

        if active_tab_key != 1:
            # get the needed date info (first valid date, date at end of first week, difference in days from start to end)

            # trim the strings to get the dates, start and end will change based on last tab but not the length
            true_start_date_str = (selected_date[10:20])
            true_end_date_str = (selected_date[27:37])
            first_date_altair = datetime.datetime.strptime(true_start_date_str, '%Y-%m-%d')
            last_date_altair = datetime.datetime.strptime(true_end_date_str, '%Y-%m-%d')

            # some logs for debugging this area, which can get sticky due to the large amount of data from different types
            logger.debug("selected_date", selected_date)
            logger.debug("true_start_date_str", true_start_date_str)
            logger.debug("true_end_date_str", true_end_date_str)
            logger.debug(st.session_state["last_active_date_tab"])
            logger.debug("first_date_altair", first_date_altair)
            logger.debug("last_date_altair", last_date_altair)

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
        try:
            # but dont error the entire program just to log outputs when there is no data
            logger.info("\n\nResult of get_hour_cups_data query (left/item 1)\nFirst : {0}\nLast : {1}".format(hour_cups_data_1_adv[0], hour_cups_data_1_adv[-1]))
            logger.info("\n\nResult of get_hour_cups_data query (right/item 2)\nFirst : {0}\nLast : {1}".format(hour_cups_data_2_adv[0], hour_cups_data_2_adv[-1])) 
        except IndexError:
            pass
        


        #TODOASAP - MULTITHREAD THIS, ALSO WHY ITS BEST IN FUNCTION CHUNKS IG

        # ---- declaring vars - week_x and all lists ----

        # empty lists used for transforming db data for df, 'all' covers all dates, the rest is week by week 
        # [item 1 / left]
        just_names_list_1_all, just_names_list_1_w0, just_names_list_1_w1, just_names_list_1_w2, just_names_list_1_w3, just_names_list_1_w4, just_names_list_1_w5 = [], [], [], [], [], [], []
        just_hour_list_1_all, just_hour_list_1_w0, just_hour_list_1_w1, just_hour_list_1_w2, just_hour_list_1_w3, just_hour_list_1_w4, just_hour_list_1_w5 = [], [], [], [], [], [], []
        just_cupcount_list_1_all, just_cupcount_list_1_w0, just_cupcount_list_1_w1, just_cupcount_list_1_w2, just_cupcount_list_1_w3, just_cupcount_list_1_w4, just_cupcount_list_1_w5 = [], [], [], [], [], [], []      
        # [item 2 / right]
        just_names_list_2_all, just_names_list_2_w0, just_names_list_2_w1, just_names_list_2_w2, just_names_list_2_w3, just_names_list_2_w4, just_names_list_2_w5 = [], [], [], [], [], [], []
        just_hour_list_2_all, just_hour_list_2_w0, just_hour_list_2_w1, just_hour_list_2_w2, just_hour_list_2_w3, just_hour_list_2_w4, just_hour_list_2_w5 = [], [], [], [], [], [], []
        just_cupcount_list_2_all, just_cupcount_list_2_w0, just_cupcount_list_2_w1, just_cupcount_list_2_w2, just_cupcount_list_2_w3, just_cupcount_list_2_w4, just_cupcount_list_2_w5 = [], [], [], [], [], [], []   
        

        # ---- SINGLE DAY [active date tab = 1] ----

        if weeks_between_dates == 0:
            # do item 1
            for cups_data in hour_cups_data_1_adv:
                just_cupcount_list_1_all.append(cups_data[0])
                just_hour_list_1_all.append(cups_data[1])
                just_names_list_1_all.append(cups_data[2])
            # then item 2
            for cups_data in hour_cups_data_2_adv:
                just_cupcount_list_2_all.append(cups_data[0])
                just_hour_list_2_all.append(cups_data[1])
                just_names_list_2_all.append(cups_data[2])
            # then extend the first (item 1) 'all' lists to include the second (item 2) dataset   
            just_cupcount_list_1_all.extend(just_cupcount_list_2_all)
            just_hour_list_1_all.extend(just_hour_list_2_all)
            just_names_list_1_all.extend(just_names_list_2_all)         

        # END SINGLE DAY (hilariously simple by comparison to below)


        # ---- BETWEEN 2 DAYS [so far only this - active date tab = 2]----


        # ---- FOR ITEM 1 / LEFT SIDE ---- 
        # run the function
        result_weeks_date_tuple = convert_raw_data_to_weeks(hour_cups_data_1_adv, just_cupcount_list_1_w0, just_cupcount_list_1_w1, just_cupcount_list_1_w2, just_cupcount_list_1_w3, just_cupcount_list_1_w4, just_cupcount_list_1_w5,
                                                            just_hour_list_1_w0, just_hour_list_1_w1, just_hour_list_1_w2, just_hour_list_1_w3, just_hour_list_1_w4, just_hour_list_1_w5,
                                                            just_names_list_1_w0, just_names_list_1_w1, just_names_list_1_w2, just_names_list_1_w3, just_names_list_1_w4, just_names_list_1_w5,
                                                            first_date_altair, end_of_first_week_date_altair, weeks_between_dates, last_date_altair)

        # unpack the results
        just_cupcount_list_1_w0, just_cupcount_list_1_w1, just_cupcount_list_1_w2, just_cupcount_list_1_w3, just_cupcount_list_1_w4, just_cupcount_list_1_w5 = result_weeks_date_tuple[0], result_weeks_date_tuple[1], result_weeks_date_tuple[2], result_weeks_date_tuple[3], result_weeks_date_tuple[4], result_weeks_date_tuple[5]
        just_hour_list_1_w0, just_hour_list_1_w1, just_hour_list_1_w2, just_hour_list_1_w3, just_hour_list_1_w4, just_hour_list_1_w5 = result_weeks_date_tuple[6], result_weeks_date_tuple[7], result_weeks_date_tuple[8], result_weeks_date_tuple[9], result_weeks_date_tuple[10], result_weeks_date_tuple[11]
        just_names_list_1_w0, just_names_list_1_w1, just_names_list_1_w2, just_names_list_1_w3, just_names_list_1_w4, just_names_list_1_w5 = result_weeks_date_tuple[12], result_weeks_date_tuple[13], result_weeks_date_tuple[14], result_weeks_date_tuple[15], result_weeks_date_tuple[16], result_weeks_date_tuple[17]


        # ---- FOR ITEM 2 / RIGHT SIDE ---- 
        # run the function
        result_weeks_date_tuple = convert_raw_data_to_weeks(hour_cups_data_2_adv, just_cupcount_list_2_w0, just_cupcount_list_2_w1, just_cupcount_list_2_w2, just_cupcount_list_2_w3, just_cupcount_list_2_w4, just_cupcount_list_2_w5,
                                                            just_hour_list_2_w0, just_hour_list_2_w1, just_hour_list_2_w2, just_hour_list_2_w3, just_hour_list_2_w4, just_hour_list_2_w5,
                                                            just_names_list_2_w0, just_names_list_2_w1, just_names_list_2_w2, just_names_list_2_w3, just_names_list_2_w4, just_names_list_2_w5,
                                                            first_date_altair, end_of_first_week_date_altair, weeks_between_dates, last_date_altair)
 
        # unpack the results
        just_cupcount_list_2_w0, just_cupcount_list_2_w1, just_cupcount_list_2_w2, just_cupcount_list_2_w3, just_cupcount_list_2_w4, just_cupcount_list_2_w5 = result_weeks_date_tuple[0], result_weeks_date_tuple[1], result_weeks_date_tuple[2], result_weeks_date_tuple[3], result_weeks_date_tuple[4], result_weeks_date_tuple[5]
        just_hour_list_2_w0, just_hour_list_2_w1, just_hour_list_2_w2, just_hour_list_2_w3, just_hour_list_2_w4, just_hour_list_2_w5 = result_weeks_date_tuple[6], result_weeks_date_tuple[7], result_weeks_date_tuple[8], result_weeks_date_tuple[9], result_weeks_date_tuple[10], result_weeks_date_tuple[11]
        just_names_list_2_w0, just_names_list_2_w1, just_names_list_2_w2, just_names_list_2_w3, just_names_list_2_w4, just_names_list_2_w5 = result_weeks_date_tuple[12], result_weeks_date_tuple[13], result_weeks_date_tuple[14], result_weeks_date_tuple[15], result_weeks_date_tuple[16], result_weeks_date_tuple[17]

        # ---- FOR ITEM 1 / LEFT SIDE ---- 
        result_all_1 = extend_all_lists(just_cupcount_list_1_all, just_hour_list_1_all, just_names_list_1_all, 
                        just_cupcount_list_1_w0,just_cupcount_list_1_w1,just_cupcount_list_1_w2,just_cupcount_list_1_w3,just_cupcount_list_1_w4,just_cupcount_list_1_w5,
                        just_hour_list_1_w0,just_hour_list_1_w1,just_hour_list_1_w2,just_hour_list_1_w3,just_hour_list_1_w4,just_hour_list_1_w5,
                        just_names_list_1_w0, just_names_list_1_w1, just_names_list_1_w2, just_names_list_1_w3, just_names_list_1_w4, just_names_list_1_w5)
        # unpack the results
        just_cupcount_list_1_all, just_hour_list_1_all, just_names_list_1_all = result_all_1[0], result_all_1[1], result_all_1[2]

        # make copies for item 1s all lists before extending for insights dataframes
        just_cupcount_1_for_df = just_cupcount_list_1_all.copy()
        just_hours_1_for_df = just_hour_list_1_all.copy()
        just_names_1_for_df = just_names_list_1_all.copy()

        # ---- FOR ITEM 2 / RIGHT SIDE ---- 
        result_all_2 = extend_all_lists(just_cupcount_list_2_all, just_hour_list_2_all, just_names_list_2_all, 
                        just_cupcount_list_2_w0,just_cupcount_list_2_w1,just_cupcount_list_2_w2,just_cupcount_list_2_w3,just_cupcount_list_2_w4,just_cupcount_list_2_w5,
                        just_hour_list_2_w0,just_hour_list_2_w1,just_hour_list_2_w2,just_hour_list_2_w3,just_hour_list_2_w4,just_hour_list_2_w5,
                        just_names_list_2_w0, just_names_list_2_w1, just_names_list_2_w2, just_names_list_2_w3, just_names_list_2_w4, just_names_list_2_w5)
        # unpack the results
        just_cupcount_list_2_all, just_hour_list_2_all, just_names_list_2_all = result_all_2[0], result_all_2[1], result_all_2[2]

        # make copies for item 2s all lists before extending for insights dataframes
        just_cupcount_2_for_df = just_cupcount_list_2_all.copy()
        just_hours_2_for_df = just_hour_list_2_all.copy()
        just_names_2_for_df = just_names_list_2_all.copy()        

        # ---- EXTEND LIST 1 WITH LIST 2 ----
        # organise for passing to the extend function
        all_list_1, all_list_2 = [just_names_list_1_all, just_cupcount_list_1_all, just_hour_list_1_all], [just_names_list_2_all, just_cupcount_list_2_all, just_hour_list_2_all]
        w0_list_1, w0_list_2 = [just_names_list_1_w0, just_cupcount_list_1_w0, just_hour_list_1_w0], [just_names_list_2_w0, just_cupcount_list_2_w0, just_hour_list_2_w0] 
        w1_list_1, w1_list_2 = [just_names_list_1_w1, just_cupcount_list_1_w1, just_hour_list_1_w1], [just_names_list_2_w1, just_cupcount_list_2_w1, just_hour_list_2_w1]
        w2_list_1, w2_list_2 = [just_names_list_1_w2, just_cupcount_list_1_w2, just_hour_list_1_w2], [just_names_list_2_w2, just_cupcount_list_2_w2, just_hour_list_2_w2]
        w3_list_1, w3_list_2 = [just_names_list_1_w3, just_cupcount_list_1_w3, just_hour_list_1_w3], [just_names_list_2_w3, just_cupcount_list_2_w3, just_hour_list_2_w3]    
        w4_list_1, w4_list_2 = [just_names_list_1_w4, just_cupcount_list_1_w4, just_hour_list_1_w4], [just_names_list_2_w4, just_cupcount_list_2_w4, just_hour_list_2_w4]  
        w5_list_1, w5_list_2 = [just_names_list_1_w5, just_cupcount_list_1_w5, just_hour_list_1_w5], [just_names_list_2_w5, just_cupcount_list_2_w5, just_hour_list_2_w5]   
        
        # call the extend function
        final_all_list_1 = extend_list_1_with_list_2(all_list_1, all_list_2)
        final_w0_list_1 = extend_list_1_with_list_2(w0_list_1, w0_list_2)
        final_w1_list_1 = extend_list_1_with_list_2(w1_list_1, w1_list_2)
        final_w2_list_1 = extend_list_1_with_list_2(w2_list_1, w2_list_2)
        final_w3_list_1 = extend_list_1_with_list_2(w3_list_1, w3_list_2)
        final_w4_list_1 = extend_list_1_with_list_2(w4_list_1, w4_list_2)
        final_w5_list_1 = extend_list_1_with_list_2(w5_list_1, w5_list_2)

        # unpack the results       
        just_names_list_1_all, just_cupcount_list_1_all, just_hour_list_1_all = final_all_list_1[0], final_all_list_1[1], final_all_list_1[2]
        just_names_list_1_w0, just_cupcount_list_1_w0, just_hour_list_1_w0 = final_w0_list_1[0], final_w0_list_1[1], final_w0_list_1[2]
        just_names_list_1_w1, just_cupcount_list_1_w1, just_hour_list_1_w1 = final_w1_list_1[0], final_w1_list_1[1], final_w1_list_1[2]
        just_names_list_1_w2, just_cupcount_list_1_w2, just_hour_list_1_w2 = final_w2_list_1[0], final_w2_list_1[1], final_w2_list_1[2]
        just_names_list_1_w3, just_cupcount_list_1_w3, just_hour_list_1_w3 = final_w3_list_1[0], final_w3_list_1[1], final_w3_list_1[2]
        just_names_list_1_w4, just_cupcount_list_1_w4, just_hour_list_1_w4 = final_w4_list_1[0], final_w4_list_1[1], final_w4_list_1[2]
        just_names_list_1_w5, just_cupcount_list_1_w5, just_hour_list_1_w5 = final_w5_list_1[0], final_w5_list_1[1], final_w5_list_1[2]



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
        
        # lightly format if just one date
        if st.session_state["last_active_date_tab"] == 1:
            date_as_word = datetime.datetime.strftime(st.session_state["active_date_1"], "%d %B, %Y")
        else:
            date_as_word = "01/01/2022"
        # or chuck in the date range if its between two dates
        display_date_1 = str(st.session_state["active_date_1"])
        display_date_2 = str(st.session_state["active_date_2"])
        # lightly format to clean these up too
        clean_display_date_1 = datetime.datetime.strftime(st.session_state["active_date_1"], "%d %B %Y")
        clean_display_date_2 = datetime.datetime.strftime(st.session_state["active_date_2"], "%d %B %Y")


        # TODOASAP - THE DATE HERE WOULD BE WAAAAY BETTER AS SUBTITLE DUHHHH!
        chartTab_dict = {0:(chartTab0, f"{f'All Dates' if weeks_between_dates != 0 else date_as_word}", (just_names_list_1_all, just_cupcount_list_1_all, just_hour_list_1_all), f"{f'{clean_display_date_1} to {clean_display_date_2}' if weeks_between_dates != 0 else date_as_word}"),
                            1:(chartTab1, "First Week", (just_names_list_1_w0, just_cupcount_list_1_w0, just_hour_list_1_w0), f"Commencing {clean_display_date_1}"),
                            2:(chartTab2, "Some Title", (just_names_list_1_w1, just_cupcount_list_1_w1, just_hour_list_1_w1), f"Commencing {get_commencing_week_from_weektab(display_date_1, 1)}"),
                            3:(chartTab3, "Some Title", (just_names_list_1_w2, just_cupcount_list_1_w2, just_hour_list_1_w2), f"Commencing {get_commencing_week_from_weektab(display_date_1, 2)}"),
                            4:(chartTab4, "Some Title", (just_names_list_1_w3, just_cupcount_list_1_w3, just_hour_list_1_w3), f"Commencing {get_commencing_week_from_weektab(display_date_1, 3)}"),
                            5:(chartTab5, "Some Title", (just_names_list_1_w4, just_cupcount_list_1_w4, just_hour_list_1_w4), f"Commencing {get_commencing_week_from_weektab(display_date_1, 4)}"),
                            6:(chartTab6, "Some Title", (just_names_list_1_w5, just_cupcount_list_1_w5, just_hour_list_1_w5), f"Commencing {get_commencing_week_from_weektab(display_date_1, 5)}")
                        }


        # procedurally generate the charts based on the dynamic datasets
        for i in range(0,7):
            # randomly changed to camelcase but meh
            # better title names as this is the tab name too? (also subtitles pls) defo include the actual dates DUHHHHH
            theTab, theTitle, theDataset, theSubTitle = chartTab_dict[i][0], chartTab_dict[i][1], chartTab_dict[i][2], chartTab_dict[i][3]
            
            with theTab:
                # grab the data for the chart based on the dates
                barchart, barchart_text = create_dataframe_setup_chart(theDataset[0], theDataset[1], theDataset[2])
                # render the chart
                st.markdown(f"### {theTitle}")
                st.markdown(f"##### {theSubTitle}")
                st.write("##")
                st.altair_chart(barchart + barchart_text, use_container_width=True)


        # TODOASAP
        # HAVE REMOVED THE ONLY ONE DATE TRY EXCEPT INDEXERROR FOR NOW - might not need anymore btw but what if not data for a single day (find out duh)
        # JUST GENERALLY BE SURE TO COVER WITH TRY EXCEPTS WHERE NECESSARY WHEN THERE IS NO DATA + WHATEVER ELSE

        # ---- END ALTAIR CHART - PHEW ----


        # ---- START INSIGHTS SECTION ----

        # ---- RUN INSIGHTS CALCUALTIONS ----
        # gain insights by running some indepth calculations and displaying info back to user using tabs
            
        # create a dataset of item 1 and 2 combined to use as a dataframe
        just_names_both_for_df = combine_both_items_data_lists_for_df(just_names_1_for_df, just_names_2_for_df)
        just_cupcount_both_for_df = combine_both_items_data_lists_for_df(just_cupcount_1_for_df, just_cupcount_2_for_df)
        just_hours_both_for_df = combine_both_items_data_lists_for_df(just_hours_1_for_df, just_hours_2_for_df)

        # create the needed dataframes, for item 1, item 2, and the comination of both
        df_sawce_1 = create_hourcups_dataframe(just_names_1_for_df, just_cupcount_1_for_df, just_hours_1_for_df)
        df_sawce_2 = create_hourcups_dataframe(just_names_2_for_df, just_cupcount_2_for_df, just_hours_2_for_df)
        df_sawce_both = create_hourcups_dataframe(just_names_both_for_df, just_cupcount_both_for_df, just_hours_both_for_df)

        # for item 1
        # create hour vs cups sold dictionaries used for insights 
        hourcups_dict_1, hcd_sort_by_value_1 = create_two_simple_cups_for_hour_dict(df_sawce_1)
        # then get the hourcups insights data
        average_hourcups_1, worst_time_1, best_time_1, worst_performer_1, best_performer_1, above_avg_hc_1, below_avg_hc_1,\
            overperformed_by_dict_1, hc_std_dict_1, hc_std_1 = create_hourcups_insights_data(hourcups_dict_1, hcd_sort_by_value_1)
        # new things - price of item, revenue for each hour dict, total revenue for item for timeframe
        price_of_item_1 = get_price_for_item(item_selector_1, final_size_select_1, final_flav_select_1)
        revenue_by_hour_dict_1, total_revenue_1, total_volume_1 = create_revenue_by_hour_dict_n_total_revenue(hourcups_dict_1, price_of_item_1)   
        highest_sd_hours_1 = get_hours_at_highest_standard_deviation(hc_std_dict_1)

        # for item 2
        # create hour vs cups sold dictionaries used for insights 
        hourcups_dict_2, hcd_sort_by_value_2 = create_two_simple_cups_for_hour_dict(df_sawce_2)
        # then get the hourcups insights data
        average_hourcups_2, worst_time_2, best_time_2, worst_performer_2, best_performer_2, above_avg_hc_2, below_avg_hc_2,\
            overperformed_by_dict_2, hc_std_dict_2, hc_std_2 = create_hourcups_insights_data(hourcups_dict_2, hcd_sort_by_value_2)
        # new things - price of item, revenue for each hour dict, total revenue for item for timeframe
        price_of_item_2 = get_price_for_item(item_selector_2, final_size_select_2, final_flav_select_2)
        revenue_by_hour_dict_2, total_revenue_2, total_volume_2 = create_revenue_by_hour_dict_n_total_revenue(hourcups_dict_2, price_of_item_2)   
        highest_sd_hours_2 = get_hours_at_highest_standard_deviation(hc_std_dict_2)

        # for both items together (sum of compared hourcups per hour)
        # create hour vs cups sold dictionaries used for insights 
        hourcups_dict_both, hcd_sort_by_value_both = create_two_simple_cups_for_hour_dict(df_sawce_both)
        # then get the hourcups insights data
        average_hourcups_both, worst_time_both, best_time_both, worst_performer_both, best_performer_both, above_avg_hc_both, below_avg_hc_both,\
            overperformed_by_dict_both, hc_std_dict_both, hc_std_both = create_hourcups_insights_data(hourcups_dict_both, hcd_sort_by_value_both)
        # new things
        total_revenue_both = total_revenue_1 + total_revenue_2
        highest_sd_hours_both = get_hours_at_highest_standard_deviation(hc_std_dict_both)
        # price of item not relevant for both so discarded, price here is just both prices added together
        revenue_by_hour_dict_both, _, total_volume_both = create_revenue_by_hour_dict_n_total_revenue(hourcups_dict_both, (price_of_item_1 + price_of_item_2))   

        # ---- END INSIGHT CALCULATIONS (mostly) ----


        # ---- FINALISE && PRINT INSIGHTS TO TABS/NESTED TABS ----

        # note ideally would move this with the other functions at the top of the page but it gets updated regularly so leaving it where it is
        def fill_sublevel_tabs_with_insights(worst_performer, worst_time, best_performer, best_time, average_hourcups, above_avg_hc, below_avg_hc, hourcups_dict,
                                            overperformed_by_dict, hc_std_dict, hc_std, revenue_by_hour_dict, total_revenue, total_volume, highest_sd_hours,
                                            price_of_item:float=0.0, rev_diff_dict:dict={1:1.0}):
            """
            programmatically fill subtabs with insights for item 1, 2, or both, tabs are initialised inside the function and must stay there,
            last two parameters are default args since they based on if function runs for item 1 or 2 (price of item), or both items (revenue diff dict)
            """

            # NEW STUFF - TEST AREA
            # TODOASAP - MAKE THESE FUNCTIONS DUH!

            # a simple boolean flag so we know if we are dealing with solo items or both, relevant for any calculation/print using price_of_item
            is_solo_item = True if price_of_item > 0 else False

            # if is solo item create overperformance specifics, i.e. the *best (singular) volume and revenue *over* the average per hour
            if is_solo_item: 
                # volume that this hour outperformed the average by
                best_op_hour_volume = sorted(list(overperformed_by_dict.items()))[0]
                # grab the actual base value (not just the amount over the average), use the hour in the above hour/volume tuple as the key for the main dict
                best_op_hour_totalvolume = hourcups_dict[int(best_op_hour_volume[0])]
                # that volume converted to revenue
                best_op_hour_revenue = best_op_hour_volume[1] * price_of_item
                best_op_hour_totalrevenue = best_op_hour_totalvolume * price_of_item
            else:
                # else set to a null default of same type and we'll display something else relevant for 'both' only if we need to
                best_op_hour_volume = {0:0}
                best_op_hour_revenue = 0.0
                best_op_hour_totalrevenue = 0.0

            # note this should be a function but kinda low on time right now so skipping
            # for tab 2 expand this concept to include revenue also, this currently is only used for the snapshot cards
            # overperforming hours and volumes (op over the average)
            op_hours_volume = []
            op_hours_hour = []
            for hour, count in overperformed_by_dict.items():
                # format the hours to strings and create new lists with the items cast to strings
                op_hours_volume.append(str(f"{count:.0f}"))
                formatted_hour = give_hour_am_or_pm(hour)
                op_hours_hour.append(str(formatted_hour))
            # if just one item thats overperforming
            if len(op_hours_hour) == 1:
                display_op_hours = op_hours_hour[0]
                display_op_volume = op_hours_volume[0]
                # var for the display string, swap to plural if more than one hour
                is_or_are_2 = "is punching above it's weight"
            # if two an ampersand in the middle will suffice
            elif len(op_hours_hour) == 2:
                display_op_hours = " & ".join(op_hours_hour)
                display_op_volume = " & ".join(op_hours_volume)
                is_or_are_2 = "are punching above their weight"
            # if more than 2
            elif len(op_hours_hour) > 2:
                # add commas to the first items in the list and ampersand to the last 
                # for volume
                display_op_volume_left = ", ".join(op_hours_volume[0:-1])
                display_op_volume = str(display_op_volume_left) + " & " + str(op_hours_volume[-1])
                # for hours
                display_op_hours_left = ", ".join(op_hours_hour[0:-1])
                display_op_hours = str(display_op_hours_left) + " & " + str(op_hours_hour[-1])
                # alter display string based since list count is plural 
                is_or_are_2 = "are punching above their weight"
            else:
                # if nothing in the list set the var anyway so it doesnt break (tho shouldnt even be displaying the block anyway but bugs happen)
                display_op_hours = " "
                display_op_volume = " "
                is_or_are_2 = " "

            # just the dates handy as strings, should have done waaaay earlier but ah well
            date2_year = (st.session_state["active_date_2"].year)
            display_date_insights_1 = st.session_state["active_date_1"]
            display_date_insights_1 = datetime.datetime.strftime(display_date_insights_1, "%d %B %Y")
            if date2_year > 2000:
                display_date_insights_2 = st.session_state["active_date_2"]
                display_date_insights_2 = datetime.datetime.strftime(display_date_insights_2, "%d %B %Y")
                display_date_string = f"{display_date_insights_1} to {display_date_insights_2}"
            else:
                display_date_string = display_date_insights_1

            # add am/pm to the hours by applying the function using map
            highest_hours_string_list = list(map(give_hour_am_or_pm, highest_sd_hours))
            highest_sd_multiplier = max(list(hc_std_dict.values()))             
            # if theres only one item in the list just display that
            if len(highest_hours_string_list) == 1:
                display_sd_hours = highest_hours_string_list[0]
                # var for the display string, swap to plural if more than one hour
                is_or_are = "is"
            # if two an ampersand in the middle will suffice
            elif len(highest_hours_string_list) == 2:
                display_sd_hours = " & ".join(highest_hours_string_list)
                is_or_are = "are"
            # if more than 2
            elif len(highest_hours_string_list) > 2:
                # join every element but the last with commas
                display_sd_hours_left = ", ".join(highest_hours_string_list[0:-1])
                # then join the comma part with the last item using an ampersand
                display_sd_hours = str(display_sd_hours_left) + " & " + str(highest_hours_string_list[-1])
                is_or_are = "are"
            else:
                # if nothing in the list set the var anyway so it doesnt break (tho shouldnt even be displaying the block anyway but bugs happen)
                display_sd_hours = " "
                is_or_are = " "

            # END NEW TESTING AREA STUFF FOR THIS FUNCTION

            st.markdown("### Get The Insights Below")
            st.markdown("Toggle items above with tabs above, toggle insights using tabs below")
            st.markdown("*Note - Currently Insights are only for the full date range, not week by week*")

            # obviously rename these tabs, add subtitles and explanation text (be succinct tho pls)
            insightTab1, insightTab2, insightTab3 = st.tabs(["Core Insights", "Detailed Insights", "More Insights"])
            
            # some lambdas for extracting vars that didn't require functions
            hours_above_avg_sales = ', '.join(list(map(lambda x : f'{x}pm' if x > 11 else f'{x}am' , list(above_avg_hc.keys()))))
            hours_below_avg_sales = ', '.join(list(map(lambda x : f'{x}pm' if x > 11 else f'{x}am' , list(below_avg_hc.keys()))))

            # ---- CORE INSIGHTS - CARDS ----
            with insightTab1:
                # TODOASAP - THIS, AND 100% SHOW A INFO BOX WITH A CLOSE BUTTON TOO
                # ACTUALLY MAYBE THIS ISN'T WORKING ANYWAY (THE EXPANDER) SO CHECK!!!
                # use an expander to solve the jumping screen issue
                #st.success("The Custom HTML Component has a bug which causes jump_to functionality, so it's placed in the expander below")
                #cardblock1 = st.expander(label="See Your Insights")
                #with cardblock1:
                st.write("Take action without the effort with this easy to digest snapshot which showcases key insights from the data you've selected, don't forget to hit the tabs above to discover more")
                stc.html(FOUR_CARD_INFO.format(display_sd_hours, is_or_are, f"{highest_sd_multiplier:.0f}", total_volume, total_revenue, display_op_hours, display_op_volume, is_or_are_2, average_hourcups, display_date_string), height=1000)
    

            # ---- INSIGHT DETAILS - TEXT ----
            with insightTab2:

                # ---- NEW - TEST AREA ----
                # new and super rough but kinda just skipping through this to do more interesting/harder/new things since this is for learning

                # make this a function
                st.write("")
                by_hour_string = []
                for (revkey, revvalue), (sdkey, sdvalue) in zip(revenue_by_hour_dict.items(), hc_std_dict.items()):
                    by_hour_string.append(f"{give_hour_am_or_pm(revkey)}" + f" : ${revvalue:.2f} at {sdvalue:.0f}x SD volume")
                by_hour_string = "<br>".join(by_hour_string)

                # yup I got bored of this page, last thing im doing here then moving on to move complex stuff
                worst_string_1 = f"Worst Performing Hour:<br> - {worst_performer}<br><br>"
                worst_string_2 = f"At {worst_time}{'pm' if worst_time > 11 else 'am'} consider offers + less staff<br><br>"
                hours_under_avg_sales = ', '.join(list(map(lambda x : f'{x}pm' if x > 11 else f'{x}am' , list(below_avg_hc.keys()))))
                worst_string_3 = "Hours Under Average Sales: " + hours_under_avg_sales + "<br>"
                worst_string_4 = "Actionable Insight - Consider running product offers or discounts during these hours"

                # make this a function
                if len(highest_sd_hours) > 1:
                    display_sd_string = "performers here were"
                    # this is actually wrong rn but its too much of a time sink for me to care anymore
                    besthourrev = (highest_sd_hours)[0]
                    display_sd_string_2 = f"with the best [{give_hour_am_or_pm(besthourrev)}] coming in at"
                else:
                    display_sd_string = "perfomer here was"            
                    display_sd_string_2 = ""
                # END NEW TEST AREA

                try:
                    # new html/css component, cards again, 3x horizontal, better suited for descriptive text, more cards can be added if needed
                    stc.html(THREE_CARD_INFO.format(average_hourcups, display_op_hours, display_sd_hours, best_op_hour_volume[1], best_op_hour_revenue,
                                                    best_op_hour_totalrevenue, highest_sd_multiplier, display_sd_string, display_sd_string_2, by_hour_string,
                                                    worst_string_1, worst_string_2, worst_string_3, worst_string_4), height=1200)
                except TypeError:
                    # temporarily catch the error that is due to the difference in data between solo items and both items datasets
                    st.write("Both Items Comparison Analysis - Coming Soon")
                except KeyError:
                    # temporarily catch the error that is due to the difference in data between solo items and both items datasets
                    st.write("Both Items Comparison Analysis - Coming Soon")


            # ---- MORE INSIGHTS - CHART/S ----
            with insightTab3:
                # i got a bit too wrapped up in the whole pie thing, mb
                my_hungry_ass, cooling_window, _ = st.columns([4,3,1])
                
                with my_hungry_ass:
                    # prepare the dataframe from the amount of cups (item 1) sold per hour
                    st.write("##")
                    st.write("##")
                    pie_sawce = pd.DataFrame({"values": hourcups_dict.values(), "hours":hourcups_dict.keys()}) # mmmmm pie sauce
                    # prepare the pie (gas mark 5, 25 minutes)
                    pie_base = alt.Chart(pie_sawce).encode(
                        theta=alt.Theta("values:Q", stack=True),
                        radius=alt.Radius("values", scale=alt.Scale(type="sqrt", zero=True, rangeMin=20)),
                        color=alt.Color('hours:N', legend=alt.Legend(title = "Hour", orient="left")))  # scale=alt.Scale(scheme='category10'), 
                    # render the pie... i mean kettle... wait
                    pie_crust = pie_base.mark_arc(innerRadius=20, stroke="#fff") # the actual chart
                    pie_decotation = pie_base.mark_text(radiusOffset=10).encode(text="values:Q") # the text... i get bored sometimes
                    st.altair_chart(pie_crust + pie_decotation, use_container_width=True)   

                with cooling_window:
                    st.write("##")
                    st.write("##")
                    st.markdown("##### Hourly Breakdown")
                    st.write("Let's take a deep dive into the hourly data to see what insights lie beneath the surface lorem...")



        # so for second tab, lets get average sales with revenue and stuff first card - including over/under hours stuff?
        # then another card with those hour specifics
        # then last card just whatever the hell else is left
        # then the chart
        # then do portfolio mode
        # then bounce to new stuff tbh and come back to this after a break 
        # (to do the all stores week by week insights (taking ALL data so can properly compare a week to the weekly avgs for example!))



        # ---- CREATE & DISPLAY INSIGHTS PROGRAMATICALLY ----
    
        # initialise tabs, named dynamically based on (main) item name
        insightItem1Tab, insightItem2Tab, insightBothItemsTab = st.tabs([f"1.{item_selector_1}", f"2.{item_selector_2}", "Insights - Both Items"])


        with insightItem1Tab:
            # ---- ITEMS 1 ----
            fill_sublevel_tabs_with_insights(worst_performer_1, worst_time_1, best_performer_1, best_time_1,\
                                            average_hourcups_1, above_avg_hc_1, below_avg_hc_1, hourcups_dict_1,\
                                            overperformed_by_dict_1, hc_std_dict_1, hc_std_1, revenue_by_hour_dict_1,\
                                            total_revenue_1, total_volume_1, highest_sd_hours_1, price_of_item=price_of_item_1)

        with insightItem2Tab:
            # ---- ITEMS 2 ----
            fill_sublevel_tabs_with_insights(worst_performer_2, worst_time_2, best_performer_2, best_time_2,\
                                            average_hourcups_2, above_avg_hc_2, below_avg_hc_2, hourcups_dict_2,\
                                            overperformed_by_dict_2, hc_std_dict_2, hc_std_2, revenue_by_hour_dict_2,\
                                            total_revenue_2, total_volume_2, highest_sd_hours_2, price_of_item=price_of_item_2)

        # for each tab, run function which creates nested tabs and dynamically fills them with the relevant data (item 1, item 2, both items)
        with insightBothItemsTab:
            # ---- BOTH ITEMS ----
            # this is 1 minus 2 so is really unique and not valid for 1 or 2 hence why it is here (legit placed here so i dont forget it too)
            revenue_diff_by_hour_dict = create_hc_1_vs_2_difference_in_revenue_by_hour_dict(revenue_by_hour_dict_1,revenue_by_hour_dict_2)
            print("\nrevenue_diff_by_hour_dict", revenue_diff_by_hour_dict)
            fill_sublevel_tabs_with_insights(worst_performer_both, worst_time_both, best_performer_both, best_time_both,\
                                            average_hourcups_both, above_avg_hc_both, below_avg_hc_both, hourcups_dict_both,\
                                            overperformed_by_dict_both, hc_std_dict_both, hc_std_both, revenue_by_hour_dict_both,\
                                            total_revenue_both, total_volume_both, highest_sd_hours_both, rev_diff_dict=revenue_diff_by_hour_dict)
        

        # general debugging
        
        item1_vars = (hourcups_dict_1, overperformed_by_dict_1, hc_std_dict_1, hc_std_1, worst_time_1, best_time_1, 
                        worst_performer_1, best_performer_1, above_avg_hc_1, below_avg_hc_1, revenue_by_hour_dict_1, 
                        price_of_item_1, total_revenue_1, total_volume_1)

        thats_how_we_play_handy_hands(item1_vars, play_handy_hands=False)


# ---- DRIVER ----
if __name__ == "__main__":
    try:
        run()
    # if the connection errors, wipe the entire cache, then show user rerun button which fixes issue (using any widget will do the same)
    except mysql.connector.errors.OperationalError as operr:
        # note this error mostly happens due to local save causing the old connection to not work anymore as its cached in singleton
        # log error messages
        logger.error("ERROR! - (╯°□°）╯︵ ┻━┻")
        logger.info("What The Connection Doin?")
        logger.error("Connection bugged again")
        logger.info(operr)
        # wipe the cache thoroughly
        st.experimental_memo.clear()
        st.experimental_singleton.clear()
        # rerun the app
        st.experimental_rerun()
        # problem solved
    except DuplicateWidgetID as dupwid:
        logger.error("ERROR! - (╯°□°）╯︵ ┻━┻")
        logger.error("DuplicateWidgetID")
        logger.info("This literally has never been an actual duplicate error btw")
        logger.info(dupwid)
        



# RN
# - isnt really time to reimplement portfolio mode
# - would love to get into finishing up the insights but is kinda diminishing returns at this hour
# - so just do interview prep and unwind to get a good nights sleep :D