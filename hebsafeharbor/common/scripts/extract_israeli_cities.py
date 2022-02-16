import urllib.request
import json
from typing import List, Dict

import numpy as np
import pandas as pd
import re


def clean_items_punctuation(ds, filter_items: List[str] = list()):
    """
    The function removes brackets from all the column items, and for each record with brackets or dash
    adds separate record with content within / outside brackets or each section separated by dash
    (Ex. ['Tel Aviv - Yaffo', 'Nir David (Tel Amal)'] ->
     ['Tel Aviv - Yaffo', 'Tel Aviv', 'Yaffo', 'Nir David (Tel Amal)', 'Nir David', 'Tel Amal'] )

    Parameters
    ----------
    limit_records : int
        Number of records for the API query (default is 2000). Before running an update, please check total available
        records for the required API at https://data.gov.il/dataset/residents_in_israel_by_communities_and_age_groups
    residents_threshold : int
        cities are devided into 2 lists based on the residents threshold
    """
    clean_list = list()
    for c in ds.values:
        splitted_list = re.split('\)|\(|-', c)
        if len(splitted_list) > 1:
            c = c.replace(")", "").replace("(", "")
            splitted_list.append(c)
        splitted_list = [item_part.strip() for item_part in splitted_list]
        splitted_list = [item_part.replace('"', '\\"') for item_part in splitted_list if item_part]
        clean_list.extend(splitted_list)
    if len(filter_items) > 0:
        for filter_item in filter_items:
            if filter_item in clean_list:
                clean_list.remove(filter_item)
    return clean_list


def save_lists_to_file(items_to_save: Dict[str, List[str]], output_file_name: str):
    with open(output_file_name, 'w') as f:
        for k, v in items_to_save.items():
            f.write(f"{k} = [\n")
            for item in set(v):
                f.write(f'\t"{item}",\n')
            f.write(']\n')


def update_cities_list(limit_records: int = 2000, residents_threshold: int = 2000) -> None:
    """

    Parameters
    ----------
    limit_records : int
        Number of records for the API query (default is 2000). Before running an update, please check total available
        records for the required API at https://data.gov.il/dataset/residents_in_israel_by_communities_and_age_groups
    residents_threshold : int
        cities are devided into 2 lists based on the residents threshold
    """

    URL = 'https://data.gov.il/api/3/action/datastore_search?resource_id=64edd0ee-3d5d-43ce-8562-c336c24dbc1f&limit=' + \
          str(limit_records)

    resource = urllib.request.urlopen(URL)
    content = resource.read().decode(resource.headers.get_content_charset())
    loaded_dict = json.loads(content)['result']['records']
    df = pd.DataFrame.from_dict(loaded_dict)
    df.rename(columns={"סהכ": "residents", "שם_ישוב": "city", "נפה": "county", "מועצה_אזורית": "council"}, inplace=True)
    df['above_threshold'] = np.where(df['residents'] >= residents_threshold, 'above', 'below')

    above = clean_items_punctuation(df.loc[df.above_threshold == "above", ("city")], ["לא רשום"])
    below = clean_items_punctuation(df.loc[df.above_threshold == "below", ("city")], ["לא רשום"])

    d = {
        "ABOVE_THRESHOLD_CITIES_LIST": above,
        "BELOW_THRESHOLD_CITIES_LIST": below,
    }

    save_lists_to_file(d, "../city_utils.py")


if __name__ == "__main__":
    update_cities_list(limit_records=2000, residents_threshold=2000)
