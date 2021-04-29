import pandas as pd
import numpy as np


def check_patient_data(file, mode):
    d = pd.read_csv(file)
    if mode == "pediatrics":
        d.rename(columns={"agedays": "age"}, inplace=True)
    elif mode == "adults":
        d.rename(columns={"age_years": "age"}, inplace=True)
    else:
        raise ValueError("mode must be 'adults' or 'pediatrics")

    warnings_list = []
    if d["sex"].isin([0, 1]).all() is False:
        warnings_list.append("'sex' contains values outside of 0 and 1")
    if (d["age"] >= 0).all() is False:
        warnings_list.append("age column contains values less than zero")
    if d["age"].dtype != np.number:
        warnings_list.append("age column is not numeric")
    if d["param"].isin(["WEIGHTKG", "HEIGHTCM"]).all() is False:
        warnings_list.append("'param' contains values other than WEIGHTKG and HEIGHTCM")
    if (d["measurement"] >= 0).all() is False:
        warnings_list.append("'measurement' contains values less than zero")
    needed_columns = ["subjid", "param", "measurement", "age", "sex", "result"]
    for nc in needed_columns:
        if nc not in d.columns:
            warnings_list.append(nc + " column not included in patient data")
    return warnings_list
