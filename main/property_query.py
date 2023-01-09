import requests
import numpy as np
import pandas as pd
import warnings


def standardize_room_street(room, street):
    # Standardize room: check if room format is expected.
    if room not in ["", "-"]:
        if room[:4] == "UNIT":  # Unit 1510
            room_c = room[4:].strip()
        elif room[0] in [x for x in "ABCDEFGHIJKLMNOPQRSTUVWXYZ"]:  # G05, H8, C101
            room_c = room[1:]
        elif room[-1] in [x for x in "ABCDEFGHIJKLMNOPQRSTUVWXYZ"]:  # 407B
            room_c = room[:-1]
        else:
            room_c = room  # 308
        try:
            int(room_c)
        except ValueError:  # 2 Bedroom Apartment/800 Swanston Street
            room = ""

    # Standardize street.
    road_suff = [
        "Street",
        "Road",
        "St",
        "street",
        "STREET",
        "Rd",
        "ROAD",
        "Drive",
        "Place",
        "Lane",
        "Terrace",
        "ST",
        "RD",
    ]
    street = street.split(" ")
    if street[-1] in road_suff:
        street = street[:-1]
    street = "".join([x.lower().capitalize() for x in street])
    return room, street


def get_room_street(estate_name, estate_type):
    if estate_type in ["House", "Terrace", "Townhouse"]:
        is_apartment = False
    else:
        is_apartment = True

    # Split room and steet.
    if estate_name == "":
        return "", ""
    estate_name = estate_name.split("/")
    if len(estate_name) >= 3:  # Unexpected format.
        return "", ""
    if len(estate_name) == 2:  # 907/83 Flemington Road
        room = estate_name[0].strip().upper()
        street = estate_name[1]
    if len(estate_name) == 1:  # 33 Blackwood street
        street = estate_name[0]
        if is_apartment:
            room = ""
        else:
            room = "-"
    room, street = standardize_room_street(room, street)
    return room, street


def create_domain_url(requisition):
    min_bed = requisition.get("min_bed", 1)
    min_bath = requisition.get("min_bath", 1)
    max_price = requisition.get("max_price", "any")
    min_price = requisition.get("min_price", "0")
    north = requisition.get("north")
    west = requisition.get("west")
    south = requisition.get("south")
    east = requisition.get("east")
    domain_url = (
        f"https://www.domain.com.au/rent/?bedrooms={min_bed}-any&bathrooms={min_bath}-any&price={min_price}-"
        f"{max_price}&excludedeposittaken=1&startloc={north},{west}&endloc={south},{east}&"
        f"displaymap=0"
    )
    return domain_url


def request_domain_properties(requisition, url=None):
    if url is None:
        url = create_domain_url(requisition)
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:91.0) Gecko/20100101 Firefox/91.0",
        "Accept": "application/json",
    }
    content = requests.get(url, headers=headers).json()
    return content, url


def request_domain_multipages(content, url):
    pages = content["props"]["pageViewMetadata"]["searchResponse"]["SearchResults"][
        "totalPages"
    ]
    for page in range(2, pages + 1):
        new_url = url + f"&page={page}"
        page_content, _ = request_domain_properties(None, url=new_url)
        content["props"]["listingsMap"] = {
            **content["props"]["listingsMap"],
            **page_content["props"]["listingsMap"],
        }
    return content


def add_domain_detail_info(domain_properties):
    """
    Add available date and full image (floorplan).
    """
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:91.0) Gecko/20100101 Firefox/91.0",
        "Accept": "application/json",
    }
    domain_detail_info = domain_properties.copy()
    avail_date = []
    full_images = []
    for url in domain_properties.Url:
        content = requests.get(url, headers=headers).json()
        stats = pd.DataFrame(content["props"]["listingSummary"]["stats"])
        avail_date.append(stats.query("key=='availableFrom'")["value"].iloc[0])
        full_images.append(content["props"]["gallery"]["slides"])
    domain_detail_info["Available"] = avail_date
    domain_detail_info["Images"] = full_images
    return domain_detail_info


def get_domain_properties(requisition, get_details=False):
    content, url = request_domain_properties(requisition)

    # Quality control.
    page_info = content["props"]["pageViewMetadata"]["searchResponse"]["SearchResults"]
    if page_info["actualTotalResultsExceedsMaximum"]:
        warnings.warn("Number of Domain properties exceeds maximum limit")
    if page_info["totalPages"] != 1:
        content = request_domain_multipages(content, url)
    n_total = page_info["totalResults"]

    # Read information.
    property_info = []
    for estate_web in content["props"]["listingsMap"].values():
        estate_web = estate_web["listingModel"]
        estate_info = dict()
        estate_info["Url"] = "https://www.domain.com.au" + estate_web["url"]
        estate_info["Price"] = estate_web["price"]
        estate_info["Name"] = estate_web["address"]["street"]
        estate_info["Suburb"] = (
            "".join(estate_web["address"]["suburb"].split(" ")).lower().capitalize()
        )
        estate_info["State"] = estate_web["address"]["state"].upper()
        estate_info["Latitude"] = estate_web["address"]["lat"]
        estate_info["Longitude"] = estate_web["address"]["lng"]
        estate_info["Bedroom_num"] = estate_web["features"].get("beds", None)
        estate_info["Bathroom_num"] = estate_web["features"].get("baths", None)
        estate_info["Parking_num"] = estate_web["features"].get("parking", 0)
        estate_info["Type"] = estate_web["features"].get("propertyTypeFormatted", None)
        estate_info["Room"], estate_info["Street"] = get_room_street(
            estate_info["Name"], estate_info["Type"]
        )
        estate_info["Images"] = estate_web["images"]
        if estate_info["Room"] != "":
            estate_info["PID"] = (
                f"{estate_info['Room']}_{estate_info['Street']}_{estate_info['Suburb']}_"
                f"{estate_info['State']}"
            )
        property_info.append(estate_info)

    property_info = pd.DataFrame(property_info)
    property_info["Source"] = "Domain"
    property_info["Available"] = ""
    if get_details:
        property_info = add_domain_detail_info(property_info)
    return property_info


def create_realestate_url(requisition):
    min_bed = requisition.get("min_bed", 1)
    max_price = requisition.get("max_price", "any")
    min_price = requisition.get("min_price", "0")
    north = requisition.get("north")
    west = requisition.get("west")
    south = requisition.get("south")
    east = requisition.get("east")
    page_size = 200  # It seems that the maximum number is 200 for the website.
    realestate_url = (
        f"https://services.realestate.com.au/services/listings/search?query="
        f'{{"channel":"rent","filters":{{"priceRange":{{"minimum":"{min_price}","maximum":"{max_price}"}},'
        f'"bedroomsRange":{{"minimum":"{min_bed}"}},"surroundingSuburbs":"true",'
        f'"excludeTier2":"true","geoPrecision":"address","excludeAddressHidden":'
        f'"true"}},"boundingBoxSearch":[{south},{west},{north},{east}],"pageSize":"{page_size}"}}'
    )
    return realestate_url


def request_realestate_properties(requisition, url=None):
    if url is None:
        url = create_realestate_url(requisition)
    content = requests.get(url).json()
    return content, url


def request_realestate_multipages(content, url):
    n_count = content["totalResultsCount"]
    page_size = int(content["resolvedQuery"]["pageSize"])
    for page in range(2, int((n_count - 1) / page_size) + 2):
        if page == 11:
            warnings.warn("Number of Realestate properties exceeds maximum limit")
            continue
        new_url = url[:-1] + ',"page":"' + str(page) + '"}'
        page_content, _ = request_realestate_properties(None, url=new_url)
        content["tieredResults"][0]["results"].extend(
            page_content["tieredResults"][0]["results"]
        )
    return content


def get_realestate_properties(requisition):
    content, url = request_realestate_properties(requisition)

    # Quality control.
    if len(content["tieredResults"]) != 1:
        raise ValueError("Unexpected tier result count!")
    if int(content["totalResultsCount"]) >= 200:
        content = request_realestate_multipages(content, url)

    # Read information.
    property_info = []
    for estate_web in content["tieredResults"][0]["results"]:
        estate_info = dict()
        estate_info["Url"] = estate_web["_links"]["prettyUrl"]["href"]
        estate_info["Bedroom_num"] = estate_web["features"]["general"]["bedrooms"]
        estate_info["Bathroom_num"] = estate_web["features"]["general"]["bathrooms"]
        estate_info["Parking_num"] = estate_web["features"]["general"]["parkingSpaces"]
        estate_info["Price"] = estate_web["price"]["display"]
        estate_info["Type"] = estate_web["propertyType"].capitalize()
        estate_info["Name"] = estate_web["address"]["streetAddress"]
        estate_info["Room"], estate_info["Street"] = get_room_street(
            estate_info["Name"], estate_info["Type"]
        )
        estate_info["Suburb"] = (
            "".join(estate_web["address"]["suburb"].split(" ")).lower().capitalize()
        )
        estate_info["State"] = estate_web["address"]["state"].upper()
        estate_info["Latitude"] = estate_web["address"]["location"]["latitude"]
        estate_info["Longitude"] = estate_web["address"]["location"]["longitude"]
        estate_info["Available"] = estate_web["dateAvailable"]["date"]
        estate_info["Images"] = estate_web["images"]
        if estate_info["Room"] != "":
            estate_info["PID"] = (
                f"{estate_info['Room']}_{estate_info['Street']}_{estate_info['Suburb']}_"
                f"{estate_info['State']}"
            )
        property_info.append(estate_info)

    property_info = pd.DataFrame(property_info)
    property_info["Source"] = "Realestate"
    return property_info


def merge_realestate_domain_properties(rp, dp):
    # Check ID availability.
    if rp.PID.dropna().duplicated().any() or dp.PID.dropna().duplicated().any():
        warnings.warn("Duplicated property found!")
        dup_indices = rp.dropna()[rp.PID.dropna().duplicated(keep=False)].index
        rp.loc[dup_indices, "PID"] = np.nan
        dup_indices = dp.dropna()[dp.PID.dropna().duplicated(keep=False)].index
        dp.loc[dup_indices, "PID"] = np.nan
    rp_pid = set(rp.PID.dropna())
    dp_pid = set(dp.PID.dropna())
    both_pid = rp_pid & dp_pid
    ronly_pid = rp_pid - dp_pid
    donly_pid = dp_pid - rp_pid

    # Create merged property data.
    both = rp.query("PID in @both_pid").copy()
    both["Source"] = "Both"
    rsource = rp[rp["PID"].isin(ronly_pid) | rp["PID"].isna()]
    dsource = dp[dp["PID"].isin(donly_pid) | dp["PID"].isna()]
    merge_p = pd.concat([both, rsource, dsource], ignore_index=True).sort_values(
        ["Street", "Room"]
    )
    indices = merge_p["PID"].fillna(merge_p["Url"])
    indices.name = ""
    merge_p.index = indices
    return merge_p
