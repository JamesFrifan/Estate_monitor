import time
import os
import pandas as pd


def initiate_property_data(folder, property_ori, init_ignore):
    os.makedirs(folder)

    present = time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime())
    with open(f"{folder}log.txt", "w+") as f:
        f.write(f"Start monitoring properties at: {present} (UTC)\n")

    with open(f"{folder}preference.txt", "w+") as f:
        f.write("")
    with open(f"{folder}ignore_street.txt", "w+") as f:
        if init_ignore is None:
            f.write("")
        else:
            f.write(init_ignore)

    property_data = property_ori.copy()
    property_data.to_csv(f"{folder}tracked_properties.csv")
    return property_data


def get_prop_value_change(previous_prop, current_prop):
    row_same = previous_prop.eq(current_prop).all(axis=1)
    if all(row_same):
        return None
    else:
        diff_pids = row_same[~row_same].index

    diff_dict = dict()
    for pid in diff_pids:
        diff_val = dict()
        for col in previous_prop.columns:
            pre_val = previous_prop.loc[pid, col]
            cur_val = current_prop.loc[pid, col]
            if pre_val != cur_val:
                diff_val[col] = (pre_val, cur_val)
        diff_dict[pid] = diff_val
    return diff_dict


def diff_property_info(previous_ori, current_ori):
    check_col = ["Price", "Bedroom_num", "Bathroom_num", "Parking_num", "Source"]
    previous_prop = previous_ori.copy()
    current_prop = current_ori.copy()
    # If no update.
    if previous_prop[check_col].equals(current_prop[check_col]):
        return None

    pre_pids = set(previous_prop.index)
    cur_pids = set(current_prop.index)
    new_pids = cur_pids - pre_pids
    passed_pids = pre_pids - cur_pids
    same_pids = pre_pids & cur_pids
    change_dict = get_prop_value_change(
        previous_prop.loc[same_pids, check_col], current_prop.loc[same_pids, check_col]
    )
    return {"new": new_pids, "passed": passed_pids, "changed": change_dict}


def log_update_info(folder, diff_result):
    with open(f"{folder}log.txt", "a+") as f:
        present = time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime())
        f.write(f"  Update at: {present} (UTC)\n")
        if diff_result["changed"] is not None:
            f.write(f"    Properties' value change: {diff_result['changed']}\n")
        if len(diff_result["new"]) > 0:
            f.write(f"    Add new properties: {diff_result['new']}\n")
        if len(diff_result["passed"]) > 0:
            f.write(f"    Delete properties: {diff_result['passed']}\n")
    return


def print_changes_info(diff_dict, pid_set):
    for pid in diff_dict:
        if pid in pid_set:
            print(f"{pid}: ", end="")
            for categ, values in diff_dict[pid].items():
                print(f"{categ} from '{values[0]}' to '{values[1]}'. ", end="")
            print()
        else:
            continue
    return


def print_update_info(diff_result, pref):
    if diff_result["changed"] is not None:
        print(f"Value change for preferred property(ies):")
        print_changes_info(diff_result["changed"], pref)
        print()
        print(f"Value change for non-preferred property(ies):")
        print_changes_info(
            diff_result["changed"],
            [x for x in diff_result["changed"].keys() if x not in pref],
        )
        print("*" * 50)

    if len(diff_result["passed"]) > 0:
        print(
            f"No longer available preferred properties: {diff_result['passed'] & pref}"
        )
        print()
        print(
            f"{len(diff_result['passed'] - pref)} other properties are no longer available."
        )
        print("*" * 50)

    if len(diff_result["new"]) > 0:
        print("New properties found.")
    return


def update_property_data(folder, current_ori):
    previous_ori = pd.read_csv(f"{folder}tracked_properties.csv", index_col=0)
    diff_result = diff_property_info(previous_ori, current_ori)
    if diff_result is None:
        print("No update found.")
        return None

    current_ori.to_csv(f"{folder}tracked_properties.csv")
    log_update_info(folder, diff_result)
    with open(f"{folder}preference.txt", "r") as f:
        pref = set(f.read().split(","))
    print_update_info(diff_result, pref)

    if len(diff_result["new"]) == 0:
        return None
    else:
        return current_ori.loc[diff_result["new"]]


def filter_prop(new_prop_ori, folder):
    new_prop = new_prop_ori.copy()
    with open(f"{folder}ignore_street.txt", "r") as f:
        ignored = f.read().split(",")
    new_prop = new_prop[~new_prop["Street"].isin(ignored)]
    new_prop = new_prop[
        [
            "Name",
            "Price",
            "Bedroom_num",
            "Bathroom_num",
            "Url",
            "Available",
            "Type",
            "Parking_num",
            "Street",
        ]
    ]
    return new_prop
