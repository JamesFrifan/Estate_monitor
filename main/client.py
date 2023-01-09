import os
import property_query as ppq
import property_monitor as ppm


def transform_angle(ms_angle):
    """Transform minute and second formatted angle to decimal degree."""
    de_angle = 0
    multiplier = 1 if ms_angle[0] > 0 else -1
    for i, value in enumerate(ms_angle):
        if i == 0:
            de_angle += value
        else:
            de_angle += multiplier * value / 60 ** i
    return de_angle


def monitor_properties(folder, requisition, init_ignore=None):
    realestate_property = ppq.get_realestate_properties(requisition)
    domain_property = ppq.get_domain_properties(requisition)
    property_data = ppq.merge_realestate_domain_properties(
        realestate_property, domain_property
    )

    if os.path.isdir(folder):
        print("Updating property monitor.")
        new_prop = ppm.update_property_data(folder, property_data)
    else:
        print("Initiating property monitor.")
        new_prop = ppm.initiate_property_data(folder, property_data, init_ignore)
    if new_prop is not None:
        new_prop = ppm.filter_prop(new_prop, folder)
    return new_prop


def make_clickable_url(props):
    # target _blank to open new window
    return props.style.format(
        {"Url": lambda val: '<a target="_blank" href="{}">{}</a>'.format(val, val)}
    )


def set_preferred_properties(folder, names, set_to_preferred=True):
    if type(names) == str:
        names = [names]
    names = set(names)
    with open(f"{folder}preference.txt", "r") as f:
        pref = set(f.read().split(","))

    if set_to_preferred:
        pref |= names
    else:
        pref -= names

    with open(f"{folder}preference.txt", "w") as f:
        f.write(",".join(pref))
    return


def set_ignored_streets(folder, streets, set_to_ignored=True):
    if type(streets) == str:
        streets = [streets]
    streets = set(streets)
    with open(f"{folder}ignore_street.txt", "r") as f:
        ignored = set(f.read().split(","))

    if set_to_ignored:
        ignored |= streets
    else:
        ignored -= streets

    with open(f"{folder}ignore_street.txt", "w") as f:
        f.write(",".join(ignored))
    return
