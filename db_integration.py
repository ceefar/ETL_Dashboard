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

#TODOASAP - ig try except here for operational error that reruns init connection (but a version that isn't a singleton?)

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
        conn.commit()
        #cur.close()
        #conn.close()


# ---- end setup ----


# ---- bobby manipulation ----

# ---- bobby alterations ----
# literally needed to be run once but still leaving the code to show how it works
# both run fine without errors, must admit haven't checked for accuracy fully but seems to be fine

# probably could have been done easier semi-manually tbh but took it as a learning opportunity (plus imagined that db was more complex - i.e. more items, more stores)
def update_productpricing_for_store_basic_inventory_unflavoured():
    """ 
    search for string in customers basket and return stores with string, then for valid stores flag them as true using the item id name 
    in the product pricing table, note some strings needed to be altered for validation due to having flavoured counterparts e.g. iced latte 
    """

    # VARIABLES
    # the stores name as key and the column name as value so can loop these to set the results easier
    stores_name_col_dict = {"London Camden":"london_camden", "London Soho":"london_soho", 
                            "Chesterfield":"chesterfield", "Longridge":"longridge", "Uppingham":"uppingham"}
    # for the search strings which will validate which store has each item, note some strings were altered for validation due to flavoured couterpart e.g. latte
    id_to_name_dict_unflavoured = {"Chai Latte":"CH_LTTE", "Cortado":"CRTD", "Flat White":"FLT_WHT", "Glass Of Milk":"GLSS_MLK",
                                "Regular Hot Chocolate":"G_HT_CHOC", "Regular Iced Latte":"G_ICE_LTTE", "Regular Latte":"G_LTTE", 
                                "Luxury Hot Chocolate":"LXRY_HT_CHOC", "Mocha":"MCH", "Red Label Tea":"RD_LBL_T", "Espresso":"XPRSO"}  
    # full dict, unused but leaving for reference for incase need it in future
    id_to_name_dict = {"Chai Latte":"CH_LTTE", "Cortado":"CRTD", "Flat White":"FLT_WHT", "Flavoured Hot Chocolate":"FLV_HT_CHOC", "Flavoured Iced Latte":"FLV_ICE_LTTE", 
                    "Flavoured Latte":"FLV_LTTE", "Frappes":"FRPPS", "Glass Of Milk":"GLSS_MLK", "Regular Hot Chocolate":"G_HT_CHOC", "Regular Iced Latte":"G_ICE_LTTE",
                    "Regular Latte":"G_LTTE", "Luxury Hot Chocolate":"LXRY_HT_CHOC", "Mocha":"MCH", "Red Label Tea":"RD_LBL_T", "Smoothies":"SMTHY",
                    "Speciality Tea":"SPEC_T", "Espresso":"XPRSO"}

    for item_keyname, item_idname in id_to_name_dict_unflavoured.items():
        # get unique stores where the item is in customer baskets, search with wildcard on either side
        get_valid_stores_query = f"SELECT DISTINCT store FROM CustomerData WHERE basket_items LIKE '%{item_keyname}%'"
        get_valid_stores = get_from_db(get_valid_stores_query)
        print(get_valid_stores)
        
        for valid_store in get_valid_stores:
            valid_store = valid_store[0]

            for storename, storecol in stores_name_col_dict.items():

                # if there is more than one store the second loop will invalidate the first so set them all to 0/false first
                update_productpricing_false_query = f"UPDATE ProductPricing SET {storecol} = 0 WHERE id_name LIKE '%{item_idname}'"
                print(update_productpricing_false_query)
                add_to_db(update_productpricing_false_query)

                # then if the store is validated switch it to 1/true
                if valid_store == storename:
                    # only require wildcard at the start as its only items with no flavour (and flavour comes at the end)
                    update_productpricing_true_query = f"UPDATE ProductPricing SET {storecol} = 1 WHERE id_name LIKE '%{item_idname}'"
                    print(update_productpricing_true_query)
                    add_to_db(update_productpricing_true_query)


def update_productpricing_for_store_basic_inventory_flavoured():
    """ write me - as above just more complex for flavours """
    
    # VARIABLES
    # flavours complicates things, as just using item_name would validate a store for all flavours stores but common case is not all flavours per store
    id_to_name_dict_flavoured = {"Flavoured Hot Chocolate":"FLV_HT_CHOC", "Smoothies":"SMTHY", "Speciality Tea":"SPEC_T",
                                "Flavoured Iced Latte":"FLV_ICE_LTTE", "Flavoured Latte":"FLV_LTTE", "Frappes":"FRPPS"}
    # the stores name as key and the column name as value so can loop these to set the results easier
    stores_name_col_dict = {"London Camden":"london_camden", "London Soho":"london_soho", 
                            "Chesterfield":"chesterfield", "Longridge":"longridge", "Uppingham":"uppingham"}

    for item_keyname, item_idname in id_to_name_dict_flavoured.items():
        # get unique stores where the item is in customer baskets, search with wildcard on either side
        get_valid_stores_query = f"SELECT DISTINCT store FROM CustomerData WHERE basket_items LIKE '%{item_keyname}%'"
        get_valid_stores = get_from_db(get_valid_stores_query)
        print(get_valid_stores)

        for valid_store in get_valid_stores:
            valid_store = valid_store[0]

            # is the same as the function get_item_flavours in app_insights but pointless importing for a single query 
            item_flavours = get_from_db(f"SELECT DISTINCT i.item_flavour FROM CustomerItems i INNER JOIN CustomerData d on (i.transaction_id = d.transaction_id) WHERE d.store = '{valid_store}' AND i.item_name = '{item_keyname}';")
            item_flavours_list = []
            [item_flavours_list.append(flavour[0]) for flavour in item_flavours]
            print(item_flavours_list)

            flavours_id_name_dict = {"Vanilla":"_VNLL", "Hazelnut":"_HZLNT", "Caramel":"_CRML", "Coffee":"_CFF", "Earl Grey":"_RL_GRY",
                                    "Strawberries & Cream":"_STRWBS_&_CRM", "Glowing Greens":"_GLW_GRNS", "Berry Beautiful":"_BRRY_BTFL", "Green":"_GRN",
                                    "Peppermint":"_PMNT", "Camomile":"_CMML"}        

            # for each store
            for storename, storecol in stores_name_col_dict.items():

                # for each flavour
                for flavaflav in item_flavours_list:

                    print(storename, flavaflav)

                    # if there is more than one store the second loop will invalidate the first so set them all to 0/false first
                    # uses the flavour from the list as the key in flavour_id_name_dict to set values, in this case only set to 0 if cell is already NULL 
                    update_productpricing_false_query = f"UPDATE ProductPricing SET {storecol} = 0 WHERE id_name LIKE '%{item_idname}{flavours_id_name_dict[flavaflav]}' AND {storecol} IS NULL"
                    print(update_productpricing_false_query)
                    add_to_db(update_productpricing_false_query)

                    # then if the store is validated switch it to 1/true
                    if valid_store == storename:
                        # still only require wildcard at the start, removed 'IS NULL' constraint so can freely write any cell to 1/true
                        update_productpricing_true_query = f"UPDATE ProductPricing SET {storecol} = 1 WHERE id_name LIKE '%{item_idname}{flavours_id_name_dict[flavaflav]}'"
                        print(update_productpricing_true_query)
                        add_to_db(update_productpricing_true_query)


# ---- end bobbys ----


# ---- driver - if needed ----
if __name__ == "__main__":
    update_productpricing_for_store_basic_inventory_flavoured()





