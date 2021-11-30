import requests
import pandas as pd
import re
import time
import warnings


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


MIN_BED = 1
MIN_BATH = 1
MAX_PRICE = "450"
MIN_PRICE = "250"
NORTH = -37.794567
WEST = 144.948628
SOUTH = transform_angle([-37, 48, 14])
EAST = 144.967744


def distill_from_pattern(string, start_pattern, end_pattern="<"):
    search = re.search(start_pattern, string)
    string = string[search.end() :]
    search = re.search(end_pattern, string)
    return string[: search.start()], string[search.end() :]


def domain_exceeding_check(collected_num, content):
    actual_num, _ = distill_from_pattern(content, '"actualTotalResults":', ",")
    if_exceed, _ = distill_from_pattern(
        content, '"actualTotalResultsExceedsMaximum":', "}"
    )
    if if_exceed != "false":
        warnings.warn("Number of Domain properties exceeds maximum limit")
    if int(actual_num) != collected_num:
        raise ValueError("Number of searched and collected entries mismatched.")
    return


def get_domain_content_info(content):
    info, _ = distill_from_pattern(content, "", '"SearchResults":{"results":')
    properties = pd.DataFrame()
    for property_info in info.split('"id"')[1:]:
        current_property = pd.Series()
        current_property["Url"], property_info = distill_from_pattern(
            property_info, '"url":"', '"'
        )
        current_property["Url"] = "https://www.domain.com.au" + current_property["Url"]
        current_property["Price"], property_info = distill_from_pattern(
            property_info, '"price":"', '"'
        )

        current_property["Name"], property_info = distill_from_pattern(
            property_info, '"street":"', '"'
        )
        current_property["Name"] += " (D)" + current_property["Url"][-4:]
        features, property_info = distill_from_pattern(
            property_info, '"features":{', "}"
        )
        features = eval(
            "{" + features.replace("false", "False").replace("true", "True") + "}"
        )
        current_property["Bedroom_num"] = features.get("beds", None)
        current_property["Bathroom_num"] = features.get("baths", None)
        current_property["Parking_num"] = features.get("parking", 0)
        current_property["Type"] = features.get("propertyTypeFormatted", None)
        properties = properties.append(current_property, ignore_index=True)
    domain_exceeding_check(len(properties), content)
    return properties


def get_candidate_domain_properties():
    min_bed = MIN_BED
    min_bath = MIN_BATH
    max_price = MAX_PRICE
    min_price = MIN_PRICE
    north = NORTH
    west = WEST
    south = SOUTH
    east = EAST
    if min_bath:
        response = requests.get(
            f"https://www.domain.com.au/rent/?bedrooms={min_bed}-any&bathrooms={min_bath}-any&price={min_price}-"
            f"{max_price}&excludedeposittaken=1&startloc={north},{west}&endloc={south},{east}&"
            f"displaymap=1"
        )
    else:
        response = requests.get(
            f"https://www.domain.com.au/rent/?bedrooms={min_bed}-any&price={min_price}-{max_price}&"
            f"excludedeposittaken=1&startloc={north},{west}&endloc={south},{east}&"
            f"displaymap=1"
        )
    content = response.content.decode("utf-8")
    property_info = get_domain_content_info(content)
    property_info["Source"] = "Domain"
    return property_info


def get_domain_details(url):
    detail_info = pd.Series()
    content = requests.get(url).content.decode("utf-8")

    start_point = re.search("Available from ", content).end()
    end_point = re.search('"', content[start_point:]).start()
    detail_info["Available"] = content[start_point : end_point + start_point]
    return detail_info


def initiate_domain_properties(property_info, get_avail_date=False):
    if get_avail_date:
        detail_info = pd.DataFrame()
        for url in property_info["Url"]:
            detail_info = detail_info.append(get_domain_details(url), ignore_index=True)
        detail_info.index = property_info.index
        property_data = pd.concat([property_info, detail_info], axis=1)
    else:
        property_data = property_info.copy()
        property_data["Available"] = ""
    return property_data


def slice_line(left_content, start, stop_str):
    start_str = left_content[start:]
    return start_str[: re.search(stop_str, start_str).start()]


def get_realestate_properties():
    min_bed = MIN_BED
    min_bath = MIN_BATH
    max_price = MAX_PRICE
    min_price = MIN_PRICE
    north = NORTH
    west = WEST
    south = SOUTH
    east = EAST
    page_size = (
        200  # It seems that the maximum number is 200 for the website.
    )
    content = requests.get(
        f"https://services.realestate.com.au/services/listings/search?query="
        f'{{"channel":"rent","filters":{{"priceRange":{{"minimum":"{min_price}",'
        f'"maximum":"{max_price}"}},'
        f'"bedroomsRange":{{"minimum":"{min_bed}"}},"surroundingSuburbs":"true",'
        f'"excludeTier2":"true","geoPrecision":"address","excludeAddressHidden":'
        f'"true"}},'
        f'"boundingBoxSearch":[{south},{west},{north},{east}],"pageSize":"{page_size}"}}'
    ).content.decode("UTF-8")
    property_info = pd.DataFrame()
    current_property = pd.Series()
    left_content = content
    while re.search('"lister":', left_content):
        left_content = left_content[re.search('"lister":', left_content).end() :]
        try:
            property_content = left_content[
                : re.search('"lister":', left_content).end()
            ]
        except AttributeError:
            property_content = left_content
        if len(current_property) != 0:
            property_info = property_info.append(current_property, ignore_index=True)
            current_property = pd.Series()

        if re.search('{"prettyUrl":{"href":"', property_content):
            current_property["Url"] = slice_line(
                property_content,
                re.search('{"prettyUrl":{"href":"', property_content).end(),
                '"',
            )

        if re.search('"price":{"display":"', property_content):
            current_property["Price"] = slice_line(
                property_content,
                re.search('"price":{"display":"', property_content).end(),
                '"',
            )

        if re.search('],"address":{"streetAddress":"', property_content):
            current_property["Name"] = (
                slice_line(
                    property_content,
                    re.search('],"address":{"streetAddress":"', property_content).end(),
                    '"',
                )
                + " (R)"
                + current_property["Url"][-4:]
            )

        if re.search('"propertyType":"', property_content):
            current_property["Type"] = slice_line(
                property_content,
                re.search('"propertyType":"', property_content).end(),
                '"',
            )

        if re.search('general":', property_content):
            room_feature = eval(
                slice_line(
                    property_content,
                    re.search('general":', property_content).end(),
                    "}",
                )
                + "}"
            )
            current_property["Bedroom_num"] = room_feature["bedrooms"]
            current_property["Bathroom_num"] = room_feature["bathrooms"]
            current_property["Parking_num"] = room_feature["parkingSpaces"]

        # if re.search('startTime":"', property_content):
        #    current_property['Inspection'] = slice_line(property_content,
        #                                                re.search('startTime":"', property_content).end(), '"')

        if re.search('dateAvailable":{"date":"', property_content):
            current_property["Available"] = slice_line(
                property_content,
                re.search('dateAvailable":{"date":"', property_content).end(),
                '"',
            )

    # if min_bath:
    #    print(current_property, 'ini')
    #    current_property = current_property[current_property['Bathroom_num'] >= min_bath]
    #    print(current_property)
    property_info = property_info.append(current_property, ignore_index=True)
    property_info["Source"] = "Realestate"
    if len(property_info) == page_size:
        warnings.warn("Number of Realestate properties may exceed maximum limit")

    if min_bath:
        property_info = property_info[property_info["Bathroom_num"] >= min_bath]

    return property_info


def initiate_property_data(file, domain_property_info, realestate_property_info):
    domain_property_data = initiate_domain_properties(domain_property_info)
    property_data = domain_property_data.append(
        realestate_property_info, ignore_index=True, sort=False
    ).sort_values("Name")
    property_data["Preferred"] = False
    property_data = property_data.set_index("Name")
    if file is not None:
        property_data.to_csv(file)
    return property_data


def get_diff_info(name_of_diff, previous_data, now_data):
    diff_dict = dict()
    for name in name_of_diff:
        diff_value = dict()
        for col in now_data:
            try:
                if previous_data.loc[name, col] != now_data.loc[name, col]:
                    diff_value[col] = [
                        previous_data.loc[name, col],
                        now_data.loc[name, col],
                    ]
            except ValueError:  # Duplicate index.
                if not previous_data.loc[name, col].equals(now_data.loc[name, col]):
                    diff_value[col] = [
                        previous_data.loc[name, col].iloc[0],
                        now_data.loc[name, col].iloc[0],
                    ]
        diff_dict[name] = diff_value
    return diff_dict


def print_diff_info(diff_dict, preferred_names):
    for name in diff_dict:
        if name in preferred_names:
            print(f"{name}: ", end="")
            for value in diff_dict[name]:
                print(
                    f"{value} from '{diff_dict[name][value][0]}' to '{diff_dict[name][value][1]}'. ",
                    end="",
                )
            print()
        else:
            continue
    return


def update_property_data(
    file, previous_data, domain_property_info, realestate_property_info, log_file
):
    common_col = ["Price", "Type", "Url", "Source"]
    now_data = (
        domain_property_info[common_col + ["Name"]]
        .append(
            realestate_property_info[common_col + ["Name"]],
            ignore_index=True,
            sort=False,
        )
        .sort_values("Name")
    )
    now_data = now_data.set_index("Name")

    if previous_data[common_col].sort_values("Url").equals(now_data.sort_values("Url")):
        print("No update found.")
        return

    else:
        pre_names = set(previous_data.index)
        now_names = set(now_data.index)
        same_names = pre_names & now_names
        diff_dict = None
        new_names = now_names - pre_names
        passed_names = pre_names - now_names
        add_data = pd.DataFrame()
        if (
            not previous_data.loc[same_names, common_col]
            .sort_values("Url")
            .equals(now_data.loc[same_names].sort_values("Url"))
        ):
            if_no_diff = (
                previous_data.loc[same_names, common_col]
                .sort_values("Url")
                .eq(now_data.loc[same_names].sort_values("Url"))
                .all(axis=1)
            )
            name_of_diff = if_no_diff[~if_no_diff].index
            diff_dict = get_diff_info(name_of_diff, previous_data, now_data)
            previous_data.loc[name_of_diff, common_col] = now_data.loc[
                name_of_diff, common_col
            ]
        if len(new_names) > 0:
            add_data = initiate_property_data(
                None,
                domain_property_info[domain_property_info["Name"].isin(new_names)],
                realestate_property_info[
                    realestate_property_info["Name"].isin(new_names)
                ],
            )

        updated_data = previous_data.loc[same_names].append(add_data).sort_index()
        updated_data.to_csv(file)
        with open(log_file, "a+") as f:
            present = time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime())
            preferred_names = set(previous_data[previous_data["Preferred"]].index)
            f.write(f"  Update at: {present} (UTC)\n")
            if diff_dict is not None:
                f.write(f"    Properties' value change: {diff_dict}\n")
                print_diff_info(diff_dict, preferred_names)
            if len(new_names) > 0:
                f.write(f"    Add new properties: {new_names}\n")
                print(f"New available properties:")
                for name in new_names:
                    print(f"  {name}: {updated_data.loc[name, 'Url']}")
            if len(passed_names) > 0:
                f.write(f"    Delete properties: {passed_names}\n")
                print(
                    f"No longer available preferred properties: {passed_names & preferred_names}"
                )
        return add_data


def monitor_properties(file, log_file):
    domain_property_info = get_candidate_domain_properties()
    realestate_property_info = get_realestate_properties()
    try:
        previous_data = pd.read_csv(file, index_col=0)
        return update_property_data(
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
        return initiate_property_data(
            file, domain_property_info, realestate_property_info
        )


def set_preference(file, names, set_not_preferred=True):
    foo = pd.read_csv(file, index_col=0)
    foo.loc[names, "Preferred"] = not set_not_preferred
    foo.to_csv(file)
    return
