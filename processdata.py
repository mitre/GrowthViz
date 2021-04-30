import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib as mpl
from IPython.display import FileLinks


def setup_individual_obs_df(obs_df, mode):
    """
    Standardizes adults and pediatrics files for clean processing in GrowthViz notebooks
    """
    df = obs_df.copy()
    if mode == "adults":
        df.rename(columns={"result": "clean_value", "age_years": "age"}, inplace=True)
    elif mode == "pediatrics":
        df["age"] = df["agedays"] / 365.25
        df.drop(columns=["agedays"], inplace=True)
    else:
        raise ValueError("Mode must be equal to 'adults' or 'pediatrics'")
    df["clean_cat"] = df["clean_value"].astype("category")
    df["include"] = df.clean_value.eq("Include")
    col_list = [
        "id",
        "subjid",
        "param",
        "measurement",
        "age",
        "sex",
        "clean_value",
        "clean_cat",
        "include",
    ]
    if mode == "adults":
        return df[col_list + ["reason"]]
    elif mode == "pediatrics":
        return df[col_list]


def setup_percentiles_adults(percentiles):
    """
    Processes adults percentiles from CDC
    """
    # expand decade rows into one row per year
    pct = percentiles[
        percentiles["Age (All race and Hispanic-origin groups)"] != "20 and over"
    ].copy()
    pct.loc[pct["Age_low"] == 20, "Age_low"] = 18
    range_col = pct.apply(lambda row: row.Age_high - row.Age_low + 1, axis=1)
    pct = pct.assign(range=range_col.values)
    dta = pd.DataFrame(
        (np.repeat(pct.values, pct["range"], axis=0)), columns=pct.columns
    )
    dta["count"] = dta.groupby(["Sex", "Measure", "Age_low", "Age_high"]).cumcount()
    dta["age"] = dta["Age_low"] + dta["count"]
    # add standard deviation and other values
    dta["sqrt"] = np.sqrt(pd.to_numeric(dta["Number of examined persons"]))
    dta["sd"] = dta["Standard error of the mean"] * dta["sqrt"]
    dta["Sex"] = dta.Sex.replace("Male", 0).replace("Female", 1)
    dta.rename(columns={"Measure": "param"}, inplace=True)
    dta.drop(
        columns=[
            "Age (All race and Hispanic-origin groups)",
            "Age_low",
            "sqrt",
            "Standard error of the mean",
            "Age_high",
            "range",
            "count",
            "Number of examined persons",
        ],
        inplace=True,
    )
    # smooth percentiles between X9-(X+1)1 (i.e., 29-31)
    dta["decade"] = np.where(dta["age"] == (round(dta["age"].astype(float), -1)), 1, 0)
    mcol_list = [
        "Mean",
        "sd",
        "P5",
        "P10",
        "P15",
        "P25",
        "P50",
        "P75",
        "P85",
        "P90",
        "P95",
    ]
    for col in mcol_list:
        dta[col] = np.where(
            (dta["decade"] == 1) & (dta["age"] < 110),
            (dta[col] + dta[col].shift(1)) / 2,
            dta[col],
        )
    dta.drop(columns={"decade"}, inplace=True)
    col_list = ["param", "Sex", "age"] + mcol_list
    dta = dta.reindex(columns=col_list)
    return dta


def setup_percentiles_pediatrics(percentiles_file):
    """
    Processes pediatrics percentiles from CDC
    """
    percentiles = pd.read_csv(
        percentiles_file,
        dtype={
            "Agemos": float,
            "P5": float,
            "P50": float,
            "P95": float,
            "L": float,
            "M": float,
            "S": float,
            "Sex": int,
        },
    )
    percentiles["age"] = percentiles["Agemos"] / 12
    # Values by CDC (1=male; 2=female) differ from growthcleanr
    # which uses a numeric value of 0 (male) or 1 (female).
    # This aligns things to the growthcleanr values
    percentiles["Sex"] = percentiles["Sex"] - 1
    return percentiles


def keep_age_range(df, mode):
    """
    Restricts patient data to acceptable age range for notebooks
    """
    obs_grp = df
    # create age buckets for chart
    def label_excl_grp(row):
        if mode == "adults":
            if row["age"] < 18:
                return " Below 18 (Exclude)"
            if (row["age"] >= 18) & (row["age"] < 30):
                return " 18 to < 30"
            if (row["age"] >= 30) & (row["age"] < 40):
                return " 30 to < 40"
            if (row["age"] >= 40) & (row["age"] < 50):
                return " 40 to < 50"
            if (row["age"] >= 50) & (row["age"] < 60):
                return " 50 to < 60"
            if (row["age"] >= 60) & (row["age"] <= 65):
                return " 60 to 65"
            if (row["age"] > 65) & (row["age"] <= 80):
                return " > 65 to 80 (Not Recommended)"
            if row["age"] > 80:
                return "Above 80 (Exclude)"
        elif mode == "pediatrics":
            if row["age"] < 2:
                return " Below 2 (Exclude)"
            if (row["age"] >= 2) & (row["age"] < 5):
                return " 02 to < 05"
            if (row["age"] >= 5) & (row["age"] < 8):
                return " 05 to < 08"
            if (row["age"] >= 8) & (row["age"] < 11):
                return " 08 to < 11"
            if (row["age"] >= 11) & (row["age"] < 14):
                return " 11 to < 14"
            if (row["age"] >= 14) & (row["age"] < 17):
                return " 14 to < 17"
            if (row["age"] >= 17) & (row["age"] <= 20):
                return " 17 to 20"
            if (row["age"] > 20) & (row["age"] <= 25):
                return " > 20 to 25 (Not Recommended)"
            if row["age"] > 25:
                return "Above 25 (Exclude)"

    label_excl_col = obs_grp.apply(lambda row: label_excl_grp(row), axis=1)
    obs_grp = obs_grp.assign(cat=label_excl_col.values)
    obs_grp = (
        obs_grp.groupby("cat")["subjid"]
        .count()
        .reset_index()
        .sort_values("cat", ascending=True)
    )
    # assign bar colors
    cat_list = obs_grp["cat"].values.tolist()
    color_list = []
    patterns = []
    for n in cat_list:
        if ("Below" in n) | ("Above" in n):
            color_list = color_list + ["C3"]
            patterns = patterns + ["x"]
        if ("to" in n) & ("Not" not in n):
            color_list = color_list + ["C0"]
            patterns = patterns + [""]
        if "Not" in n:
            color_list = color_list + ["orange"]
            patterns = patterns + ["/"]
    # create chart
    fig, ax1 = plt.subplots()
    obs_grp_plot = plt.bar(
        obs_grp["cat"],
        obs_grp["subjid"],
        color=color_list,
    )
    for bar, pattern in zip(obs_grp_plot, patterns):
        bar.set_hatch(pattern)
    plt.xticks(rotation=45, ha="right")
    ax1.get_yaxis().set_major_formatter(
        mpl.ticker.FuncFormatter(lambda x, p: format(int(x), ","))
    )
    # return specified age range
    if mode == "adults":
        return df[df["age"].between(18, 80, inclusive=True)]
    elif mode == "pediatrics":
        return df[df["age"].between(2, 25, inclusive=True)]


def setup_merged_df(obs_df, mode):
    """
    Merges together weight and height data for calculating BMI
    """
    obs_df = obs_df.assign(height=obs_df["measurement"], weight=obs_df["measurement"])
    obs_df.loc[obs_df.param == "WEIGHTKG", "height"] = np.NaN
    obs_df.loc[obs_df.param == "HEIGHTCM", "weight"] = np.NaN
    heights = obs_df[obs_df.param == "HEIGHTCM"]
    weights = obs_df[obs_df.param == "WEIGHTKG"]
    merged = heights.merge(weights, on=["subjid", "age", "sex"], how="outer")
    only_needed_columns = merged.drop(
        columns=[
            "param_x",
            "measurement_x",
            "clean_value_x",
            "weight_x",
            "id_y",
            "param_y",
            "measurement_y",
            "clean_value_y",
            "height_y",
        ]
    )
    if mode == "adults":
        only_needed_columns.drop(columns=["reason_x"], inplace=True)
    clean_column_names = only_needed_columns.rename(
        columns={
            "clean_cat_x": "height_cat",
            "include_x": "include_height",
            "height_x": "height",
            "clean_cat_y": "weight_cat",
            "include_y": "include_weight",
            "weight_y": "weight",
            "reason_y": "reason",
            "id_x": "id",
        }
    )
    clean_column_names["bmi"] = clean_column_names["weight"] / (
        (clean_column_names["height"] / 100) ** 2
    )
    clean_column_names["rounded_age"] = np.around(clean_column_names.age)
    clean_column_names["include_both"] = (
        clean_column_names["include_height"] & clean_column_names["include_weight"]
    )
    return clean_column_names


def exclusion_information(obs):
    """
    Provides a count and percentage of growthcleanr categories by measurement type (param).

    Parameters:
    obs: a DataFrame, in the format output by setup_individual_obs_df

    Returns:
    A DataFrame with the counts and percentages
    """
    exc = (
        obs.groupby(["param", "clean_cat"])
        .agg({"id": "count"})
        .reset_index()
        .pivot(index="clean_cat", columns="param", values="id")
    )
    exc["height percent"] = exc["HEIGHTCM"] / exc["HEIGHTCM"].sum() * 100
    exc["weight percent"] = exc["WEIGHTKG"] / exc["WEIGHTKG"].sum() * 100
    exc = exc.fillna(0)
    exc["total"] = exc["HEIGHTCM"] + exc["WEIGHTKG"]
    exc = exc[["HEIGHTCM", "height percent", "WEIGHTKG", "weight percent", "total"]]
    exc = exc.sort_values("total", ascending=False)
    return exc.style.format(
        {
            "HEIGHTCM": "{:.0f}".format,
            "height percent": "{:.2f}%",
            "WEIGHTKG": "{:.0f}".format,
            "weight percent": "{:.2f}%",
        }
    )


def label_incl(row):
    """
    Categorizes BMI calculations as Include, Implausible, or unable to calculate (Only Wt or Ht)
    """
    if row["include_both"] == True:
        return "Include"
    elif (row["weight_cat"] == "Implausible") | (row["height_cat"] == "Implausible"):
        return "Implausible"
    else:
        return "Only Wt or Ht"


def setup_bmi_adults(merged_df, obs):
    """
    Appends BMI data onto adults weight and height observations
    """
    data = merged_df[
        [
            "id",
            "subjid",
            "sex",
            "age",
            "rounded_age",
            "bmi",
            "weight_cat",
            "height_cat",
            "include_both",
        ]
    ]
    incl_col = data.apply(lambda row: label_incl(row), axis=1)
    data = data.assign(clean_cat=incl_col.values)
    data["param"] = "BMI"
    data["clean_value"] = data["clean_cat"]
    data.rename(columns={"bmi": "measurement"}, inplace=True)
    return pd.concat([obs, data])


def data_frame_names(da_locals):
    """
    Returns a list of dataframe names
    """
    frames = []
    for key, value in da_locals.items():
        if isinstance(value, pd.DataFrame):
            if key.startswith("_") is False:
                frames.append(key)
    return frames


def export_to_csv(da_locals, selection_widget, out):
    """
    Saves out csv file of dataframe
    """
    df_name = selection_widget.value
    da_locals[df_name].to_csv(
        "growthviz-data/output/{}.csv".format(df_name), index=False
    )
    out.clear_output()
    out.append_display_data(FileLinks("growthviz-data/output"))


def clean_swapped_values(merged_df):
    """
    This function will look in a DataFrame for rows where the height_cat and weight_cat are set to
    "Swapped-Measurements". It will then swap the height and weight values for those rows.
    It will also create two new columns: postprocess_height_cat and postprocess_weight_cat.
    The values for these columns is copied from the original categories except in the case where
    swaps are fixed when it is set to "Include-Fixed-Swap".

    Parameters:
    merged_df: (DataFrame) with subjid, height, weight, include_height and include_weight columns

    Returns:
    The cleaned DataFrame
    """
    merged_df["postprocess_height_cat"] = merged_df["height_cat"]
    merged_df["postprocess_height_cat"] = merged_df[
        "postprocess_height_cat"
    ].cat.add_categories(["Include-Fixed-Swap"])
    merged_df["postprocess_weight_cat"] = merged_df["weight_cat"]
    merged_df["postprocess_weight_cat"] = merged_df[
        "postprocess_weight_cat"
    ].cat.add_categories(["Include-Fixed-Swap"])
    merged_df.loc[
        merged_df["height_cat"] == "Swapped-Measurements", ["height", "weight"]
    ] = merged_df.loc[
        merged_df["height_cat"] == "Swapped-Measurements", ["weight", "height"]
    ].values
    merged_df.loc[
        merged_df["height_cat"] == "Swapped-Measurements", "postprocess_height_cat"
    ] = "Include-Fixed-Swap"
    merged_df.loc[
        merged_df["weight_cat"] == "Swapped-Measurements", "postprocess_weight_cat"
    ] = "Include-Fixed-Swap"
    merged_df["bmi"] = merged_df["weight"] / ((merged_df["height"] / 100) ** 2)
    return merged_df


def clean_unit_errors(merged_df):
    """
    This function will look in a DataFrame for rows where the height_cat and weight_cat are set to
    "Unit-Error-High" or "Unit-Error-Low". It will then multiply / divide the height and weight values to convert them.
    It will also create two new columns: postprocess_height_cat and postprocess_weight_cat.
    The values for these columns are copied from the original categories except in the case where
    unit errors are fixed when it is set to "Include-UH" or "Include-UL" respectively.

    Parameters:
    merged_df: (DataFrame) with subjid, height, weight, include_height and include_weight columns

    Returns:
    The cleaned DataFrame
    """
    merged_df["postprocess_height_cat"] = merged_df["height_cat"]
    merged_df["postprocess_height_cat"] = merged_df[
        "postprocess_height_cat"
    ].cat.add_categories(["Include-UH", "Include-UL"])
    merged_df["postprocess_weight_cat"] = merged_df["weight_cat"]
    merged_df["postprocess_weight_cat"] = merged_df[
        "postprocess_weight_cat"
    ].cat.add_categories(["Include-UH", "Include-UL"])
    merged_df.loc[merged_df["height_cat"] == "Unit-Error-Low", "height"] = (
        merged_df.loc[merged_df["height_cat"] == "Unit-Error-Low", "height"] * 2.54
    )
    merged_df.loc[merged_df["height_cat"] == "Unit-Error-High", "height"] = (
        merged_df.loc[merged_df["height_cat"] == "Unit-Error-High", "height"] / 2.54
    )
    merged_df.loc[merged_df["weight_cat"] == "Unit-Error-Low", "weight"] = (
        merged_df.loc[merged_df["weight_cat"] == "Unit-Error-Low", "weight"] * 2.2046
    )
    merged_df.loc[merged_df["weight_cat"] == "Unit-Error-High", "weight"] = (
        merged_df.loc[merged_df["weight_cat"] == "Unit-Error-High", "weight"] / 2.2046
    )
    merged_df.loc[
        merged_df["height_cat"] == "Unit-Error-Low", "postprocess_height_cat"
    ] = "Include-UL"
    merged_df.loc[
        merged_df["height_cat"] == "Unit-Error-High", "postprocess_height_cat"
    ] = "Include-UH"
    merged_df.loc[
        merged_df["weight_cat"] == "Unit-Error-Low", "postprocess_weight_cat"
    ] = "Include-UL"
    merged_df.loc[
        merged_df["weight_cat"] == "Unit-Error-High", "postprocess_weight_cat"
    ] = "Include-UH"
    merged_df["bmi"] = merged_df["weight"] / ((merged_df["height"] / 100) ** 2)
    return merged_df
