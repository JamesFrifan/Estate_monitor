import pandas as pd
import time
import property_query as ppq


def monitor_properties(file, log_file, requisition):
    domain_property_info = ppq.get_candidate_domain_properties(requisition)
    realestate_property_info = ppq.get_realestate_properties(requisition)
    try:
        previous_data = pd.read_csv(file, index_col=0)
        return ppq.update_property_data(
            file,
            previous_data,
            domain_property_info,
            realestate_property_info,
            log_file,
        )
    except FileNotFoundError:
        present = time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime())
        with open(log_file, "w+") as f:
            f.write(f"Start monitoring properties in {file} at: {present} (UTC)\n")
        print("Property monitor initiating...")
        return ppq.initiate_property_data(
            file, domain_property_info, realestate_property_info
        )


def set_preference(file, names, set_not_preferred=True):
    # should be logged
    foo = pd.read_csv(file, index_col=0)
    foo.loc[names, "Preferred"] = not set_not_preferred
    foo.to_csv(file)
    return


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


def make_clickable(val):
    # target _blank to open new window
    return '<a target="_blank" href="{}">{}</a>'.format(val, val)
