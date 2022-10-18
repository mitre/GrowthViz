from IPython.display import FileLinks
import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


def setup_individual_obs_df(obs_df):
    """
    Standardizes adults and pediatrics files for clean processing in GrowthViz notebooks
    """
    df = obs_df.copy()
    df.rename(columns={"clean_res": "clean_value"}, inplace=True)
    df["age"] = df["agedays"] / 365.25
    df.drop(columns=["agedays"], inplace=True)
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
        f"growthviz-data/ext/{percentiles_file}",
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
    # return specified age range
    if mode == "adults":
        return df[df["age"].between(18, 80, inclusive=True)]
    elif mode == "pediatrics":
        return df[df["age"].between(2, 25, inclusive=True)]


def setup_merged_df(obs_df):
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
    da_locals[df_name].to_csv("output/{}.csv".format(df_name), index=False)
    out.clear_output()
    out.append_display_data(FileLinks("output"))


def clean_swapped_values(merged_df):
    """
    This function will look in a DataFrame for rows where the height_cat and weight_cat are set to
    "Swapped-Measurements" (or the adult equivalent). It will then swap the height and weight values
    for those rows, and recalculate BMIs based on these changes. It will also create two new columns:
    postprocess_height_cat and postprocess_weight_cat. The values for these columns are copied from
    the original categories except in the case where swaps are fixed when it is set to
    "Include-Fixed-Swap".

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

    # Allow for both pediatric and adult exclusion forms
    exclusions = ["Swapped-Measurements", "Exclude-Adult-Swapped-Measurements"]
    # Condition: both must be flagged as swaps
    cond = merged_df["height_cat"].isin(exclusions) & merged_df["weight_cat"].isin(
        exclusions
    )

    # Swap height and weight
    merged_df.loc[cond, ["height", "weight"]] = merged_df.loc[
        cond, ["weight", "height"]
    ].values

    # Record that they were swapped
    merged_df.loc[cond, "postprocess_height_cat"] = "Include-Fixed-Swap"
    merged_df.loc[cond, "postprocess_weight_cat"] = "Include-Fixed-Swap"

    merged_df["bmi"] = merged_df["weight"] / ((merged_df["height"] / 100) ** 2)
    return merged_df


def clean_unit_errors(merged_df):
    """
    This function will look in a DataFrame for rows where the height_cat and weight_cat are set to
    "Unit-Error-High" or "Unit-Error-Low". It will then multiply / divide the height and weight
    values to convert them.  It will also create two new columns: postprocess_height_cat and
    postprocess_weight_cat.  The values for these columns are copied from the original categories
    except in the case where unit errors are fixed when it is set to "Include-UH" or "Include-UL"
    respectively.

    At present, the adult algorithm does not specify high or low unit errors, rather it only flags
    "Exclude-Adult-Unit-Errors", so this function only works with pediatrics data. If growthcleanr
    adds high and low designations for adult unit errors, a comparable set of conditions could be
    added here to accommodate adult data.

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
