import property_monitor as ppm


def init_property_entity(prop_info):
    prop_entity = dict(prop_info)
    prop_entity.pop('Url')
    prop_entity.pop('PID')
    prop_entity.pop('Source')
    prop_entity['Offlist_date'] = []
    prop_entity['Listing_date'] = []
    prop_entity['Parking_num'] = {}
    prop_entity['Available'] = {}
    prop_entity['Images'] = {}
    prop_entity['Price'] = {}
    return prop_entity


def relist_property_entity(prop_info, prop_entity_input, current_time):
    prop_entity = prop_entity_input.copy()
    prop_entity['Listing_date'].append(current_time)
    prop_entity['Parking_num'][current_time] = prop_info['Parking_num']
    prop_entity['Available'][current_time] = prop_info['Available']
    prop_entity['Images'][current_time] = prop_info['Images']
    prop_entity['Price'][current_time] = prop_info['Price']
    return prop_entity


def init_property_database(current_list, current_time):
    init_props = current_list[current_list['PID'].notna()]
    props_db = dict()
    for pid, prop in init_props.iterrows():
        props_db[pid] = relist_property_entity(prop, init_property_entity(prop), current_time)
    return props_db


def updates_property_json(current_list, previous_list, props_db, current_time):
    update_dict = ppm.diff_property_info(previous_list, current_list)

    new_list_props = current_list.loc[list(update_dict['new'])]
    new_list_props = new_list_props[new_list_props['PID'].notna()]
    # Initiate new properties.
    create_props_pid = new_list_props[~new_list_props.index.isin(props_db.keys())].index
    create_props = new_list_props.loc[create_props_pid]
    for pid, prop in create_props.iterrows():
        props_db[pid] = init_property_entity(prop)
    # Add new listing (new properties or old properties listed again).
    for pid, prop in new_list_props.iterrows():
        props_db[pid] = relist_property_entity(prop, props_db[pid], current_time)

    # Add off listed.
    off_list_props = previous_list.loc[list(update_dict['passed'])]
    off_list_props = off_list_props[off_list_props['PID'].notna()]
    for pid, prop in off_list_props.iterrows():
        props_db[pid]['Offlist_date'].append(current_time)

    # Add price change.
    for pid, change in update_dict['changed'].items():
        if (pid[:5] == 'https') or (change.get('Price', None) is None):
            continue
        props_db[pid]['Price'][current_time] = prop['Price']

    return props_db