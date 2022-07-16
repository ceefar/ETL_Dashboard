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

    base_chesterfield_bi_alldays_allsum = db.get_from_db(f"SELECT AVG(total_revenue_for_day), AVG(avg_spend_per_customer_for_day), \
                                    AVG(total_customers_for_day), AVG(total_coffees_sold_for_day) FROM BizInsights WHERE store_name = 'Chesterfield';")
    base_chesterfield_bi_alldays_allsum = base_chesterfield_bi_alldays_allsum[0]                                    
    
    base_chesterfield_bi_alldays_allavg = db.get_from_db(f"SELECT SUM(total_revenue_for_day), SUM(avg_spend_per_customer_for_day), \
                                    SUM(total_customers_for_day), SUM(total_coffees_sold_for_day) FROM BizInsights WHERE store_name = 'Chesterfield';")
    base_chesterfield_bi_alldays_allavg = base_chesterfield_bi_alldays_allavg[0]  

    base_chesterfield_bi_alldays = db.get_from_db(f"SELECT total_revenue_for_day, avg_spend_per_customer_for_day, \
                                    total_customers_for_day, total_coffees_sold_for_day, current_day FROM BizInsights WHERE store_name = 'Chesterfield';")

    # bundle everything up in a dictionary so it's much easier (and slightly less computationally expensive) to extract - variable names are the keys
    base_dictionary = {"valid_dates":(base_first_valid_date, base_last_valid_date), "chesterfield_bi_alldays":base_chesterfield_bi_alldays,
                        "chesterfield_bi_alldays_allavg":base_chesterfield_bi_alldays_allavg, "chesterfield_bi_alldays_allsum":base_chesterfield_bi_alldays_allsum}

    # return the bundle up data in a dictionary
    return(base_dictionary)


@st.cache
def get_selected_stores_date_data(stores_part:str, date_part:datetime.date) -> tuple:
    """ for the specific data for any number of stores for one given date """

    stores_bi_oneday = db.get_from_db(f"SELECT total_revenue_for_day, avg_spend_per_customer_for_day, total_customers_for_day,\
                                        total_coffees_sold_for_day, current_day, store_name FROM BizInsights {stores_part} AND current_day = '{date_part}'")                                  

    # if has any length (greater than 0)
    if stores_bi_oneday:
        # return the result
        return(stores_bi_oneday)
    else:
        # else return dummy data which we'll flag and display (missing data) to user appropriately
        return((0,0,0,0))





# creates the end store_name part of a query 
def create_stores_query(user_stores_list:list, need_where:bool = True):
    """ for creating the dynamic query for store selection, given list should not be None """

    # parameter flag for if the WHERE part of the statement is needed or not
    if need_where:
        where_part = "WHERE "
    else:
        need_where = ""

    # if only one store then the query is simply the store itself
    if len(user_stores_list) == 1:
        return(f"{where_part}store_name = '{user_stores_list[0]}'")
    # else if the length is larger than 1 then we must join the stores dynamically for the resulting query
    else:
        final_query = " OR store_name=".join(list(map(lambda x: f"'{x}'",user_stores_list)))
        final_query = f"{where_part} (store_name=" + final_query + ")"
        return(final_query)


# ---- MAIN WEB APP ----
# think of this dash like a snapshot page more generalised info, not granular
# other pages will have store/product specifics (+insights), more indepth comparisons, etc

def run():

    # ---- BASE QUERIES ----
    # run the base queries
    base_data_dict = base_queries()


    # ---- BASE VARIABLES ----
    # any heavily used/recycled variables and unpacking of the base queries
    base_stores_list = ['Chesterfield', 'Uppingham', 'Longridge', 'London Camden', 'London Soho']
    # get valid dates from base data dict 
    first_valid_date, last_valid_date = base_data_dict["valid_dates"]
    # convert the dates to date objects 
    first_valid_date = datetime.datetime.strptime(first_valid_date, '%Y-%m-%d').date()
    last_valid_date = datetime.datetime.strptime(last_valid_date, '%Y-%m-%d').date()


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


    # ---- DASHBOARD SNAPSHOT ----
    
    # top tabs give options to user based on date types
    dashTab1, dashTab2, dashTab3, dashTab4, dashTab5 = st.tabs(["Single Day","Between 2 Dates","Full Week","Full Month","All Time"])

    # single day analysis
    with dashTab1:

        # columns to split display stores element and data elements
        dataCol1, dataCol2, selectCol = st.columns([1,1,2])

        # select col = side with images and user select inputs
        with selectCol:
            dash1_selected_date = st.date_input(label="What Date Would You Like Info On?", value=datetime.date(2022, 6, 7), max_value=last_valid_date, min_value=first_valid_date) 
            dash1_selected_stores = st.multiselect(label='Which Stores Would You Like Info On?', default=['Chesterfield'], options=base_stores_list)

            # var for storing the resulting data from the users selected date
            selected_stores_date_vals = ()

            # if None (because all options were removed from the select box by the user) or Chesterfield
            if len(dash1_selected_stores) == 0 or dash1_selected_stores[0] == "Chesterfield":
                # use the base queries, as Chesterfield is the default store
                # convert the date to a string so we can find it in the base query data
                userdate_as_string = str(dash1_selected_date)
                # loop the base dict 'all days' data to see if the users selected date is in there
                for i, daydata in enumerate(base_data_dict["chesterfield_bi_alldays"]):
                    for date in daydata:
                        if userdate_as_string == date:
                            selected_stores_date_vals = daydata
            else:
                selected_stores_date_query_storespart = create_stores_query(dash1_selected_stores)
                selected_stores_date_vals = get_selected_stores_date_data(selected_stores_date_query_storespart, dash1_selected_date)
                # if only one store (tuple) was returned then unpack it for metric display
                if len(selected_stores_date_vals) == 1:
                    selected_stores_date_vals = selected_stores_date_vals[0]


        try:
            # display basic metrics for user selected date and stores 
            # - note could put these in further nested tables, but tbf for single day analysis kinda less needed
            dataCol1.metric(label="Total Revenue", value=f"${selected_stores_date_vals[0]:.2f}", delta=f"${1:.2f}", delta_color="normal")
            dataCol1.metric(label="Avg Spend Per Customer", value=f"${selected_stores_date_vals[1]:.2f}", delta=f"${1:.2f}", delta_color="normal")
            # have this date in words pls, e.g. July 4th
            dataCol2.metric(label="Total Paying Customers", value=selected_stores_date_vals[2], delta=f"${1:.2f}", delta_color="normal")
            dataCol2.metric(label="Coffee's Sold", value=selected_stores_date_vals[3], delta=f"${1:.2f}", delta_color="normal")
        except IndexError:
            dataCol1.error("No Data")
        except TypeError:
            dataCol1.error("Actual Error")






  
        # DO ALL TIME NEXT AS MAKES IT EASIER TO SEE HOW IT ALL FITS




    # ---- FOOTER ----

    st.write("##")
    st.write("##")
    st.write("##")
    st.write("---")



# ---- DRIVER ----

# need try except here 
run()