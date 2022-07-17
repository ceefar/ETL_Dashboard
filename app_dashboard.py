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
        stores_bi_oneday_list = []
        # if more than one, make it a list and return (can check type then) 
        if len(stores_bi_oneday) > 1:
            for store in stores_bi_oneday:
                stores_bi_oneday_list.append(store)
            return(stores_bi_oneday_list)
        else:
            # else just return it (the one store tuple)
            return(stores_bi_oneday)
        
    else:
        # else return dummy data which we'll flag and display (missing data) to user appropriately
        return((0,0,0,0))


# creates the end store_name part of a query, cache it? 
def create_stores_query(user_stores_list:list, need_where:bool = True) -> str:
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


# session states to persit the users selection between tabs
def set_base_session_states():
    """ write me """
    if "curretDateSelection" not in st.session_state:
        st.session_state["curretDateSelection"] = datetime.date(2022, 6, 7)
    if "curretStoreSelection" not in st.session_state:
        st.session_state["curretStoresSelection"] = ["Chesterfield"]


@st.cache
def get_store_weekly_avg(storename:str|list, userdate:datetime) -> tuple[float]:
    """ gets weekly avg of bizinsights data for one or more stores, cached (but not efficiently due to store list (as order may change?))"""
    week_number = db.get_from_db(f"SELECT WEEK('{userdate}')")
    week_number = week_number[0][0]
    # if storename parameter is a string then there is only one store
    if isinstance(storename, str):
        stores_weekly_avg = db.get_from_db(f"SELECT AVG(total_revenue_for_day), AVG(avg_spend_per_customer_for_day), \
                                        AVG(total_customers_for_day), AVG(total_coffees_sold_for_day) FROM BizInsights WHERE store_name = '{storename}' \
                                        AND WEEK(current_day) = {week_number} ;")
    # else is more than one store so query is different
    else:
        # use existing function to take a list and return the stores part of the query
        store_part_query = create_stores_query(storename)
        stores_weekly_avg = db.get_from_db(f"SELECT AVG(total_revenue_for_day), AVG(avg_spend_per_customer_for_day), \
                                AVG(total_customers_for_day), AVG(total_coffees_sold_for_day) FROM BizInsights {store_part_query} \
                                AND WEEK(current_day) = {week_number} ;")   
    # convert the final avg values to floats (from decimal) before returning to save hassle
    return_value = (float(stores_weekly_avg[0][0]), float(stores_weekly_avg[0][1]), float(stores_weekly_avg[0][2]), float(stores_weekly_avg[0][3]))
    # return the result
    return(return_value)


# ---- MAIN WEB APP ----
# think of this dash like a snapshot page more generalised info, not granular
# other pages will have store/product specifics (+insights), more indepth comparisons, etc

def run():

    # ---- BASE QUERIES ----
    # run the base queries
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

    # base session stats - didnt actually change anything
    set_base_session_states()


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


    # ---- SINGLE DAY ANALYSIS ----

    with dashTab1:

        _, storeImg1, storeImg2, storeImg3, storeImg4, storeImg5 = st.columns([5,1,1,1,1,1]) 
        # dictionary to hold store related image paths, and their column vars for setting iteratively
        stores_img_dict = {"Chesterfield":{"col":storeImg1, "on":"imgs\coffee-shop-light-chesterfield.png", "off":"imgs\coffee-shop-light-chesterfield-saturated.png"},
                            "Uppingham":{"col":storeImg2, "on":"imgs\coffee-shop-light-uppingham.png", "off":"imgs\coffee-shop-light-uppingham-saturated.png"},
                            "Longridge":{"col":storeImg3, "on":"imgs\coffee-shop-light-longridge.png", "off":"imgs\coffee-shop-light-longridge-saturated.png"},
                            "London Camden":{"col":storeImg4, "on":"imgs\coffee-shop-light-london-camden.png", "off":"imgs\coffee-shop-light-london-camden-saturated.png"},
                            "London Soho":{"col":storeImg5, "on":"imgs\coffee-shop-light-london-soho.png", "off":"imgs\coffee-shop-light-london-soho-saturated.png"}
                            }

        # print function for images
        def print_on_off_stores(selected_stores_list:list):
            """ prints out the 5 store images as either on or off (saturated) based on whether they were selected, see comment for refactor"""
            # if you actually pass in the dict (and they always have cols + imgs, and same key names) then this could be reformatted to be multipurpose
            for store_name in base_stores_list:
                    if store_name in selected_stores_list:
                        stores_img_dict[store_name]["col"].image(stores_img_dict[store_name]["on"])
                    else:
                        stores_img_dict[store_name]["col"].image(stores_img_dict[store_name]["off"])

        # header tabs for the data section
        dataHeaderCol1, dataHeaderCol2  = st.tabs(["Combined Totals", "Averages"])

        # columns to split display stores element and data elements, select col = side with images and user select inputs
        # these are split up for the above tabs (combined totals and averages)
        with dataHeaderCol1:
            dataCol1, dataCol2, dataCol3, selectCol = st.columns([1,1,1,3])
        with dataHeaderCol2:
            data2Col1, data2Col2, data2Col3, select2Col = st.columns([1,1,1,3])
        
        # session state vars are used here to ensure user select data is persisted between tabs
        # for combined totals tab
        with selectCol:
            dash1_selected_date = st.date_input(label="What Date Would You Like Info On?", value=st.session_state["curretDateSelection"], max_value=last_valid_date, min_value=first_valid_date, key="date_combined") 
            dash1_selected_stores = st.multiselect(label='Which Stores Would You Like Info On?', default=st.session_state["curretStoresSelection"], options=base_stores_list, key="date_combined")                   
            st.session_state["curretDateSelection"] = dash1_selected_date
            st.session_state["curretStoresSelection"] = dash1_selected_stores
            if len(dash1_selected_stores) > 1:
                selectCol.success("By selecting 2 or more stores you can also view the average")
            if len(dash1_selected_stores) == 0:
                selectCol.warning("No Store Selected - Using Default Store 'Chesterfield'")

        # for averages tab
        with select2Col:
            dash1_selected_date = st.date_input(label="What Date Would You Like Info On?", value=st.session_state["curretDateSelection"], max_value=last_valid_date, min_value=first_valid_date, key="date_averages") 
            dash1_selected_stores = st.multiselect(label='Which Stores Would You Like Info On?', default=st.session_state["curretStoresSelection"], options=base_stores_list)
            st.session_state["curretDateSelection"] = dash1_selected_date
            st.session_state["curretStoresSelection"] = dash1_selected_stores
            if len(dash1_selected_stores) > 1:
                select2Col.success("By selecting 2 or more stores you can also view the average")
            if len(dash1_selected_stores) == 0:
                select2Col.warning("No Store Selected - Using Default Store 'Chesterfield'") 
            #FIXME - delta shows weekly avg text here (needs consideration to if being shown and what conditions cause that) 

        print_on_off_stores(dash1_selected_stores)
        # var for storing the resulting data from the users selected date
        selected_stores_date_vals = ()

        # if None (because all options were removed from the select box by the user) or Chesterfield
        if len(st.session_state["curretStoresSelection"]) == 0 or (st.session_state["curretStoresSelection"][0] == "Chesterfield" and len(st.session_state["curretStoresSelection"]) == 1):
            # use the base queries, as Chesterfield is the default store
            # convert the date to a string so we can find it in the base query data

            userdate_as_string = str(dash1_selected_date)
            # loop the base dict 'all days' data to see if the users selected date is in there
            for i, daydata in enumerate(base_data_dict["chesterfield_bi_alldays"]):
                for date in daydata:
                    if userdate_as_string == date:
                        selected_stores_date_vals = daydata

            # note if no date data is found it will still be sent through and a missingno error will be show to the user when trying to print the metrics

        else:
            selected_stores_date_query_storespart = create_stores_query(dash1_selected_stores)
            selected_stores_date_data = get_selected_stores_date_data(selected_stores_date_query_storespart, dash1_selected_date)
            
            if isinstance(selected_stores_date_data, tuple):
            # if only one store was returned unpack the values for metric display
                selected_stores_date_vals = selected_stores_date_data[0]
            # else is more than one store
            else:
                rt1, rt2, rt3, rt4 = 0, 0, 0, 0 # rt = running totals
                countforavg = len(selected_stores_date_data) 
                for store in selected_stores_date_data:
                    rt1 += float(store[0])
                    rt2 += float(store[1])
                    rt3 += store[2]
                    rt4 += store[3]
                selected_stores_date_vals = (rt1, rt2, rt3, rt4)
                selected_stores_date_avgs = (rt1/countforavg, rt2/countforavg, rt3/countforavg, rt4/countforavg)

        # get weekly average for metric deltas, unpack on arrival
        revenue_week_avg, avg_cust_spend_week_avg, tot_customers_week_avg, coffees_sold_week_avg  = get_store_weekly_avg(dash1_selected_stores, dash1_selected_date)

        try:
            # display basic metrics for user selected date and stores 
            
            def display_basic_metric(dataset:tuple, avg_or_vals:str):
                """ display metrics for given store and date for either 'vals' (sum totals) or 'avgs' based on given parameter """
                # function needs to stay nested else it loses scope of the column variables 
                # general totals
                if avg_or_vals == "vals":
                    # note deltas are the weekly avgs

                    # FIXME - WOULD PREFER DELTA HERE TO BE THE "BEST" VALS FOR WHICH EVER STORE WAS BEST IN EACH (+ its name???)

                    dataCol1.metric(label="Total Revenue", value=f"${dataset[0]:.2f}", delta=f"${revenue_week_avg:.2f}", delta_color="normal")
                    dataCol2.metric(label="Total Paying Customers", value=dataset[2], delta=int(tot_customers_week_avg), delta_color="normal")
                    dataCol3.metric(label="Coffees Sold", value=dataset[3], delta=int(coffees_sold_week_avg), delta_color="normal")
                    # should always be an average so div it by the amount of stores (as is sum/total before)
                    if len(dash1_selected_stores) > 0:
                        actual_avg_spend = (dataset[1] / len(dash1_selected_stores))
                    else:
                        actual_avg_spend = dataset[1]
                    dataCol1.metric(label="Avg Spend Per Customer", value=f"${actual_avg_spend:.2f}", delta=f"${avg_cust_spend_week_avg:.2f}", delta_color="normal")
                else:
                    # else is averages
                    data2Col1.metric(label="Total Revenue", value=f"${dataset[0]:.2f}", delta=f"${dataset[0]-revenue_week_avg:.2f}", delta_color="normal")
                    data2Col2.metric(label="Total Paying Customers", value=f"{dataset[2]:.0f}", delta=int(dataset[2])-int(tot_customers_week_avg), delta_color="normal")
                    data2Col3.metric(label="Coffees Sold", value=f"{dataset[3]:.0f}", delta=int(dataset[3])-int(coffees_sold_week_avg), delta_color="normal")
                    data2Col1.metric(label="Avg Spend Per Customer", value=f"${dataset[1]:.2f}", delta=f"${dataset[1]-avg_cust_spend_week_avg:.2f}", delta_color="normal")                    
                    # print spaces & empty metrics for equal vertical spacing
                    data2Col2.metric("-","-","-","off")
                    data2Col3.metric("-","-","-","off")
                    data2Col1.write("---")
                    data2Col2.write("---") 
                    data2Col3.write("---")
                    data2Col1.markdown("##### Weeks Average")
                    data2Col2.write(". ") 
                    data2Col3.write(". ")
                    # then the weekly avg data (so deltas make more sense/have clarity)
                    data2Col1.metric(label="Total Revenue", value=f"${revenue_week_avg:.2f}")
                    data2Col2.metric(label="Total Paying Customers", value=int(tot_customers_week_avg))
                    data2Col3.metric(label="Coffees Sold", value=int(coffees_sold_week_avg))
                    data2Col1.metric(label="Avg Spend Per Customer", value=f"${avg_cust_spend_week_avg:.2f}")                    
            # if more than one store display averages too, else don't
            if len(dash1_selected_stores) > 1:
                with dataHeaderCol1:
                    display_basic_metric(selected_stores_date_vals, "vals")
                with dataHeaderCol2:
                    display_basic_metric(selected_stores_date_avgs, "avgs")
            else:
                with dataHeaderCol1:
                    display_basic_metric(selected_stores_date_vals, "vals") 
                with dataHeaderCol2:
                    data2Col1.warning("Not Enough Stores")   
                    data2Col2.warning("For Average Data")

        # catch errors for no data (i.e. missing for a certain date)
        except IndexError:
            dataCol1.error("Missingno Error [No Data]")
            print("Index Error - Snapshot Metric")
        except TypeError:
            dataCol1.error("Actual Error [Bruhh]")
            print("Actual Error - Snapshot Metric")


    # ---- BETWEEN 2 DATES ANALYSIS ----

    with dashTab2:

        _, storeBImg1, storeBImg2, storeBImg3, storeBImg4, storeBImg5 = st.columns([5,1,1,1,1,1]) 
        # dictionary to hold store related image paths, and their column vars for setting iteratively
        stores_img_dict2 = {"Chesterfield":{"col":storeBImg1, "on":"imgs\coffee-shop-light-chesterfield.png", "off":"imgs\coffee-shop-light-chesterfield-saturated.png"},
                            "Uppingham":{"col":storeBImg2, "on":"imgs\coffee-shop-light-uppingham.png", "off":"imgs\coffee-shop-light-uppingham-saturated.png"},
                            "Longridge":{"col":storeBImg3, "on":"imgs\coffee-shop-light-longridge.png", "off":"imgs\coffee-shop-light-longridge-saturated.png"},
                            "London Camden":{"col":storeBImg4, "on":"imgs\coffee-shop-light-london-camden.png", "off":"imgs\coffee-shop-light-london-camden-saturated.png"},
                            "London Soho":{"col":storeBImg5, "on":"imgs\coffee-shop-light-london-soho.png", "off":"imgs\coffee-shop-light-london-soho-saturated.png"}
                            }

        # FIXME - test then use this refactored version above and update above code so it works with it too
        
        # print function for images
        def print_on_off_stores_refactor(selected_stores_list:list, img_dict:dict):
            """ prints out the 5 store images as either on or off (saturated) based on whether they were selected, see comment for refactor"""
            # if you actually pass in the dict (and they always have cols + imgs, and same key names) then this could be reformatted to be multipurpose
            for store_name in base_stores_list:
                    if store_name in selected_stores_list:
                        img_dict[store_name]["col"].image(img_dict[store_name]["on"])
                    else:
                        img_dict[store_name]["col"].image(img_dict[store_name]["off"])

        # header tabs for the data section
        dataBHeaderCol1, dataBHeaderCol2  = st.tabs(["Combined Totals", "Averages"])

         # columns to split display stores element and data elements, select col = side with images and user select inputs
        # these are split up for the above tabs (combined totals and averages)
        with dataBHeaderCol1:
            dataBCol1, dataBCol2, dataBCol3, selectBCol = st.columns([1,1,1,3])
        with dataBHeaderCol2:
            dataB2Col1, dataB2Col2, dataB2Col3, selectB2Col = st.columns([1,1,1,3])

        print_on_off_stores_refactor(dash1_selected_stores, stores_img_dict2)

        # DO THIS ABOVE REFACTOR FUNCTION THING QUICKLY PLS

        # NOTE 
        # FOR THE REST OF THESE THINGS LIKE DATA COMPLETENESS, WEEK DISPLAYS N TINGS CAN BE ADDED (sure more too so have a think)



    # ---- FOOTER ----

    st.write("##")
    st.write("##")
    st.write("##")
    st.write("---")


# ---- DRIVER ----

# need try except here 
run()