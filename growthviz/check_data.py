import numpy as np
import pandas as pd


def check_patient_data(file):
    """
    Runs through a series of data checks on the original data file
    
    Parameters:
    file: (file) csv data file to check
    
    Returns:
    A list of warnings (strings)
    """
    d = pd.read_csv(file)
    d.rename(columns={"agedays": "age"}, inplace=True)
    warnings_list = []
    if d["sex"].isin([0, 1]).all() is False:
        warnings_list.append("'sex' contains values outside of 0 and 1")
    if (d["age"] >= 0).all() is False:
        warnings_list.append("age column contains values less than zero")
    if d["age"].dtype != np.int64:
        warnings_list.append("age column is not numeric")
    if d["param"].isin(["WEIGHTKG", "HEIGHTCM"]).all() is False:
        warnings_list.append("'param' contains values other than WEIGHTKG and HEIGHTCM")
    if (d["measurement"] >= 0).all() is False:
        warnings_list.append("'measurement' contains values less than zero")
    needed_columns = ["subjid", "param", "measurement", "age", "sex", "clean_res"]
    for nc in needed_columns:
        if nc not in d.columns:
            warnings_list.append(nc + " column not included in patient data")
    return warnings_list
