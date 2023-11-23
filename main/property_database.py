import numpy as np
import pandas as pd
import property_query as ppq


def make_equal_chunk_requistions(requisition, n_row, n_col):
    # print(make_equal_chunk_requistions({'min_bed': 1, 'min_bath': 1, 'north': -3., 'west': 4., 'south': -5., 'east': 6.}, 1, 1))
    # print(make_equal_chunk_requistions({'min_bed': 1, 'min_bath': 1, 'north': -3., 'west': 4., 'south': -5., 'east': 6.}, 2, 1))
    # print(make_equal_chunk_requistions({'min_bed': 1, 'min_bath': 1, 'north': -3., 'west': 4., 'south': -5., 'east': 6.}, 3, 2))

    north = requisition['north']
    south = requisition['south']
    east = requisition['east']
    west = requisition['west']

    lat_val = [north + 1e-15]
    for i in range(n_row):
        ratio = float(i + 1) / n_row
        lat_val.append(np.round(south * ratio + north * (1 - ratio), 15))

    lon_val = [west - 1e-15]
    for i in range(n_col):
        ratio = float(i + 1) / n_col
        lon_val.append(np.round(east * ratio + west * (1 - ratio), 15))

    req_list = []
    for i in range(n_row):
        for j in range(n_col):
            chunk_req = requisition.copy()
            chunk_req['north'] = lat_val[i] - 1e-15
            chunk_req['south'] = lat_val[i + 1]
            chunk_req['west'] = lon_val[j] + 1e-15
            chunk_req['east'] = lon_val[j + 1]
            req_list.append(chunk_req)

    return req_list


def query_multi_chunk_properties(requisition_list):
    rp = []
    dp = []
    for req in requisition_list:
        rp.append(ppq.get_realestate_properties(req))
        dp.append(ppq.get_domain_properties(req))
    rp = pd.concat(rp, ignore_index=True)
    dp = pd.concat(dp, ignore_index=True)
    property_data = ppq.merge_realestate_domain_properties(rp, dp)
    return property_data