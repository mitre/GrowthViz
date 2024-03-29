from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import norm
from IPython.display import FileLinks


def setup_individual_obs_df(obs_df):
    """
    Standardizes adults and pediatrics files for clean processing in GrowthViz notebooks

    Parameters:
    obs_df: (DataFrame) with subjid, sex, age, measurement, param and clean_value
        columns

    Returns:
    DataFrame with updated columns
    """
    df = obs_df.copy()
    df.rename(columns={"clean_res": "clean_value"}, inplace=True)
    df["ageyears"] = df["agedays"] / 365.25
    df["clean_cat"] = df["clean_value"].astype("category")
    df["include"] = df.clean_value.eq("Include")
    col_list = [
        "id",
        "subjid",
        "agedays",
        "ageyears",
        "sex",
        "param",
        "measurement",
        "clean_value",
        "clean_cat",
        "include",
    ]
    return df[col_list]


def setup_percentiles_adults(percentiles):
    """
    Processes adults percentiles from CDC

    Parameters:
    percentiles: (str) CDC Growth Chart Percentile Data File

    Returns:
    DataFrame with adult percentiles
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


def setup_percentiles_pediatrics_new():
    """
    Process pediatrics growth data and return one big DataFrames with each of
    height, weight, and BMI percentiles as well as weighting values to support
    smoothing z scores for pediatric subjects between 2-4.

    Returns:
    Combined DataFrame with all (BMI, height, weight) percentiles and weighting
        values
    """
    df_cdc = pd.read_csv(Path("growthviz-data/ext/growthfile_cdc_ext.csv.gz"))
    df_who = pd.read_csv(Path("growthviz-data/ext/growthfile_who.csv.gz"))
    df = df_cdc.merge(df_who, on=["agedays", "sex"], how="left")

    # Add weighting columns to support smoothing between 2-4yo
    df = df.assign(ageyears=lambda r: (r["agedays"] / 365.25))
    df["cdcweight"] = 0
    df.loc[df["ageyears"].between(2, 4, inclusive="left"), "cdcweight"] = (
        df["ageyears"] - 2
    )
    df["whoweight"] = 0
    df.loc[df["ageyears"].between(2, 4, inclusive="left"), "whoweight"] = (
        4 - df["ageyears"]
    )

    PERCENTILES = [0.03, 0.05, 0.10, 0.25, 0.50, 0.75, 0.85, 0.90, 0.95, 0.97]

    # Compute percentiles for the full set of vars
    for s in ["who", "cdc"]:
        pvars = ["ht", "wt"]
        if s == "cdc":
            pvars.append("bmi")
        for p in pvars:
            for pct in PERCENTILES:
                lvar = f"{s}_{p}_l"
                mvar = f"{s}_{p}_m"
                svar = f"{s}_{p}_s"
                tvar = f"{s}_{p}_p{int(pct * 100)}"
                df.loc[df[lvar] == 0, tvar] = df[mvar] * (df[svar] ** norm.ppf(pct))
                df.loc[df[lvar] != 0, tvar] = df[mvar] * (
                    1 + (df[lvar] * df[svar] * norm.ppf(pct))
                ) ** (1 / df[lvar])

    # Add smoothed percentiles
    for p in ["ht", "wt"]:
        for pct in PERCENTILES:
            cdc_var = f"cdc_{p}_p{int(pct * 100)}"
            who_var = f"who_{p}_p{int(pct * 100)}"
            s_var = f"s_{p}_p{int(pct * 100)}"
            df.loc[df["ageyears"] <= 2, s_var] = df[who_var]
            df.loc[df["ageyears"].between(2, 4, inclusive="neither"), s_var] = (
                (df[who_var] * df["whoweight"]) + (df[cdc_var] * df["cdcweight"])
            ) / 2
            df.loc[df["ageyears"] >= 4, s_var] = df[cdc_var]

    return df


def split_percentiles_pediatrics(df):
    """
    Return (height, weight, BMI) percentile DataFrames, with column names
    aligned to chart var names.

    Parameters:
    DataFrame produced by setup_percentiles_pediatrics_new()

    Returns:
    Tuple of (height, weight, BMI) percentile DataFrames with columns renamed
    """
    df.rename(columns={"ageyears": "age", "sex": "Sex"}, inplace=True)
    cols = ["Sex", "agedays", "age"]

    ht_cols = cols.copy()
    ht_cols.extend([col for col in df.columns if "s_ht_p" in col])
    df_ht = df[ht_cols]
    df_ht.columns = [c.replace("s_ht_p", "P") for c in df_ht]

    wt_cols = cols.copy()
    wt_cols.extend([col for col in df.columns if "s_wt_p" in col])
    df_wt = df[wt_cols]
    df_wt.columns = [c.replace("s_wt_p", "P") for c in df_wt]

    bmi_cols = cols.copy()
    bmi_cols.extend([col for col in df.columns if "s_bmi_p" in col])
    df_bmi = df[bmi_cols]
    df_bmi.columns = [c.replace("s_bmi_p", "P") for c in df_bmi]

    return (df_ht, df_wt, df_bmi)


def setup_percentiles_pediatrics(percentiles_file):
    """
    Processes pediatrics percentiles from CDC

    Parameters:
    percentiles: (str) CDC Growth Chart Percentile Data File

    Returns:
    DataFrame with pediatrics percentiles
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
    """
    Returns specified range of ages in years, removing extraneous columns as well

    Parameters:
    df: (DataFrame) with subjid, param, measurement, ageyears, agedays, sex,
        clean_value, and include columns
    mode: (str) indicates whether you want the "adults" (18-80) or "pediatrics" (0-25)
        values

    Returns:
    DataFrame with filtered ages, unchanged if invalid mode is specified
    """
    # Note: this is a side effect; just the simplest place to remove these
    cols_to_drop = []
    for extra_col in ["category", "colors", "patterns", "sort_order"]:
        if extra_col in df.columns:
            cols_to_drop.append(extra_col)
    df = df.drop(columns=cols_to_drop)
    if mode == "adults":
        return df[df["ageyears"].between(18, 80, inclusive="both")]
    elif mode == "pediatrics":
        return df[df["ageyears"].between(0, 25, inclusive="both")]
    else:
        return df


def setup_merged_df(obs_df):
    """
    Merges together weight and height data for calculating BMI

    Parameters:
    obs_df: (DataFrame) with subjid, sex, agedays, ageyears, measurement, param and
        clean_value columns

    Returns:
    DataFrame with merged data
    """
    obs_df = obs_df.assign(height=obs_df["measurement"], weight=obs_df["measurement"])
    obs_df.loc[obs_df.param == "WEIGHTKG", "height"] = np.NaN
    obs_df.loc[obs_df.param == "HEIGHTCM", "weight"] = np.NaN
    heights = obs_df[obs_df.param == "HEIGHTCM"]
    weights = obs_df[obs_df.param == "WEIGHTKG"]
    merged = heights.merge(
        weights, on=["subjid", "agedays", "ageyears", "sex"], how="outer"
    )
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
    clean_column_names["rounded_age"] = np.around(clean_column_names.ageyears)
    clean_column_names["include_both"] = (
        clean_column_names["include_height"] & clean_column_names["include_weight"]
    )
    return clean_column_names


def exclusion_information(obs):
    """
    Provides a count and percentage of growthcleanr categories by measurement type
    (param).

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
    Categorizes BMI calculations as Include, Implausible, or unable to calculate (Only
    Wt or Ht)

    Parameters:
    row: (Series) dataframe row

    Returns:
    Category (str) for BMI calculation
    """
    if row["include_both"] is True:
        return "Include"
    elif (row["weight_cat"] == "Implausible") | (row["height_cat"] == "Implausible"):
        return "Implausible"
    else:
        return "Only Wt or Ht"


def setup_bmi_adults(merged_df, obs):
    """
    Appends BMI data onto adults weight and height observations

    Parameters:
    merged_df: (DataFrame) with subjid, bmi, include_height, include_weight, rounded_age
               and sex columns
    obs: (DataFrame) with subjid, param, measurement, age, sex, clean_value, clean_cat,
        include, category, colors, patterns, and sort_order columns

    Returns:
    DataFrame with appended values
    """
    data = merged_df[
        [
            "id",
            "subjid",
            "sex",
            "ageyears",
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

    Parameters:
    da_locals: (dict) all the local variables

    Returns:
    list of the dataframe names
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

    Parameters:
    da_locals: (dict) all the local variables
    selection_widget: (Widget) interactive object used
    out: (Widgets.Outputs) output from widget

    """
    df_name = selection_widget.value
    da_locals[df_name].to_csv("output/{}.csv".format(df_name), index=False)
    out.clear_output()
    out.append_display_data(FileLinks("output"))


def clean_swapped_values(merged_df):
    """
    This function will look in a DataFrame for rows where the height_cat and weight_cat
    are set to "Swapped-Measurements" (or the adult equivalent). It will then swap the
    height and weight values for those rows, and recalculate BMIs based on these
    changes.  It will also create two new columns: postprocess_height_cat and
    postprocess_weight_cat. The values for these columns are copied from the original
    categories except in the case where swaps are fixed when it is set to
    "Include-Fixed-Swap".

    Parameters:
    merged_df: (DataFrame) with subjid, height, weight, include_height and
        include_weight columns

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
    This function will look in a DataFrame for rows where the height_cat and weight_cat
    are set to "Unit-Error-High" or "Unit-Error-Low". It will then multiply / divide
    the height and weight values to convert them.  It will also create two new columns:
    postprocess_height_cat and postprocess_weight_cat.  The values for these columns
    are copied from the original categories except in the case where unit errors are
    fixed when it is set to "Include-UH" or "Include-UL" respectively.

    At present, the adult algorithm does not specify high or low unit errors, rather it
    only flags "Exclude-Adult-Unit-Errors", so this function only works with pediatrics
    data. If growthcleanr adds high and low designations for adult unit errors, a
    comparable set of conditions could be added here to accommodate adult data.

    Parameters:
    merged_df: (DataFrame) with subjid, height, weight, include_height and
        include_weight columns

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
