import math
import numpy as np
from IPython.display import Markdown


def setup_percentile_zscore_adults(percentiles_clean):
    """
    Creates mean/sd values to merge to adult data for z-score calculations

    Parameters:
    percentiles_clean: (DataFrame) with adult percentiles

    Returns:
    Dataframe with mean/sd values
    """
    dta_forz_long = percentiles_clean[["Mean", "Sex", "param", "age", "sd"]]

    def label_param(row):
        if row["param"] == "WEIGHTKG":
            return "weight"
        if row["param"] == "BMI":
            return "bmi"
        if row["param"] == "HEIGHTCM":
            return "height"

    param_col = dta_forz_long.apply(lambda row: label_param(row), axis=1)
    dta_forz_long = dta_forz_long.assign(param2=param_col.values)
    # preserving some capitalization to maintain compatibility with pediatric
    # percentiles data
    dta_forz = dta_forz_long.pivot_table(
        index=["Sex", "age"], columns="param2", values=["Mean", "sd"], aggfunc="first"
    )
    dta_forz = dta_forz.sort_index(axis=1, level=1)
    dta_forz.columns = [f"{x}_{y}" for x, y in dta_forz.columns]
    dta_forz = dta_forz.reset_index()
    dta_forz["rounded_age"] = dta_forz["age"]
    dta_forz.rename(columns={"Sex": "sex"}, inplace=True)
    return dta_forz


def add_mzscored_to_merged_df_adults(merged_df, pctls):
    """
    Merges mean/sd values onto adult data for z-score calculations

    Parameters:
    merged_df: (DataFrame) with subjid, bmi, include_height, include_weight, rounded_age
               and sex columns
    pctls: (DataFrame) with mean/sd values for adults

    Returns:
    merged Dataframe
    """
    pct_df = pctls.drop(columns={"age"})
    merged_df = merged_df.merge(pct_df, on=["sex", "rounded_age"], how="left")
    return merged_df


def add_mzscored_to_merged_df_pediatrics(
    merged_df, wt_percentiles, ht_percentiles, bmi_percentiles
):
    """
    Merges mean/sd values onto pediatrics data for z-score calculations

    Parameters:
    merged_df: (DataFrame) with subjid, bmi, include_height, include_weight, rounded_age
               and sex columns
    wt_percentiles: (DataFrame) with weight percentiles
    ht_percentiles: (DataFrame) with height percentiles
    bmi_percentiles: (DataFrame) with bmi percentiles

    Returns:
    merged Dataframe
    """

    merged_df = calculate_modified_zscore_pediatrics(
        merged_df, wt_percentiles, "weight"
    )
    merged_df = calculate_modified_zscore_pediatrics(
        merged_df, ht_percentiles, "height"
    )
    merged_df = calculate_modified_zscore_pediatrics(merged_df, bmi_percentiles, "bmi")

    return merged_df


def add_smoothed_zscore_to_merged_df_pediatrics(df_merged, df_percentiles):
    """
    Adds smoothed Z score calculations to pediatrics data

    Parameters:
    df_merged: (DataFrame) merged subject observations including height, weight,
        and bmi
    df_percentiles: (DataFrame) combined WHO and CDC percentiles
    """
    df_merged = calculate_smoothed_zscore_pediatrics(df_merged, df_percentiles)
    return df_merged


def bmi_stats(
    merged_df,
    out=None,
    include_min=True,
    include_mean=True,
    include_max=True,
    include_std=True,
    include_mean_diff=True,
    include_count=True,
    age_range=[20, 65],
    include_missing=False,
):
    """
    Computes summary statistics for BMI. Clean values are for BMIs computed when both
    the height and weight values are categorized by growthcleanr as "Include". Raw
    values are computed for all observations. Information is provided by age and sex.

    Parameters:
    merged_df: (DataFrame) with bmi, rounded_age and sex columns
    out: (ipywidgets.Output) to display the results, if provided
    include_min: (bool) Whether to include the minimum value column
    include_mean: (bool) Whether to include the mean value column
    include_max: (bool) Whether to include the maximum value column
    include_std: (bool) Whether to include the standard deviation column
    include_mean_diff: (bool) Whether to include the difference between the raw and
              clean mean value column
    include_count: (bool) Whether to include the count column
    age_range: (list) Two elements containing the minimum and maximum ages that should
        be included in the statistics
    include_missing: (bool) Whether to include the missing (0) heights and weights that
        impact raw columns

    Returns:
    If out is None, it will return a DataFrame. If out is provided, results will be
        displayed in the notebook.
    """
    # Incoming data is float, not int
    merged_df["rounded_age"] = merged_df["rounded_age"].astype(int)

    if include_missing:
        age_filtered = merged_df[
            (merged_df.rounded_age >= age_range[0])
            & (merged_df.rounded_age <= age_range[1])
        ]
    else:
        age_filtered = merged_df[
            (merged_df.rounded_age >= age_range[0])
            & (merged_df.rounded_age <= age_range[1])
            & (merged_df.weight > 0)
            & (merged_df.height > 0)
        ]
    age_filtered["sex"] = age_filtered.sex.replace(0, "M").replace(1, "F")
    agg_functions = []
    formatters = {}

    if include_min:
        agg_functions.append("min")
        formatters["min_clean"] = "{:.2f}".format
        formatters["min_raw"] = "{:.2f}".format
    if include_mean:
        agg_functions.append("mean")
        formatters["mean_clean"] = "{:.2f}".format
        formatters["mean_raw"] = "{:.2f}".format
    if include_max:
        agg_functions.append("max")
        formatters["max_clean"] = "{:.2f}".format
        formatters["max_raw"] = "{:.2f}".format
    if include_std:
        agg_functions.append("std")
        formatters["sd_clean"] = "{:.2f}".format
        formatters["sd_raw"] = "{:.2f}".format
    if include_count:
        agg_functions.append("count")
    clean_groups = (
        age_filtered[age_filtered.include_both]
        .groupby(["sex", "rounded_age"])["bmi"]
        .agg(agg_functions)
    )
    raw_groups = age_filtered.groupby(["sex", "rounded_age"])["bmi"].agg(agg_functions)
    merged_stats = clean_groups.merge(
        raw_groups, on=["sex", "rounded_age"], suffixes=("_clean", "_raw")
    )
    if include_mean & include_count & include_mean_diff:
        merged_stats["count_diff"] = (
            merged_stats["count_raw"] - merged_stats["count_clean"]
        )
    if include_std:
        merged_stats = merged_stats.rename(
            columns={"std_raw": "sd_raw", "std_clean": "sd_clean"}
        )
    if out is None:
        return merged_stats
    else:
        # Clear output on first update and all subsequent updates, see
        # https://github.com/jupyter-widgets/ipywidgets/issues/3260#issuecomment-907715980
        # Without out.outputs = (), will append only on first update
        out.outputs = ()
        out.append_display_data(Markdown("## Female"))
        out.append_display_data(merged_stats.loc["F"].style.format(formatters))
        out.append_display_data(Markdown("## Male"))
        out.append_display_data(merged_stats.loc["M"].style.format(formatters))


def calculate_modified_zscore_pediatrics(merged_df, percentiles, category):
    """
    Adds a column to the provided DataFrame with the modified Z score for the provided
    category

    Parameters:
    merged_df: (DataFrame) with subjid, sex, weight and age columns
    percentiles: (DataFrame) CDC growth chart DataFrame with L, M, S values for the
        desired category
    category: (str) name of category

    Returns
    The dataframe with a new zscore column mapped with the z_column_name list
    """
    pct_cpy = percentiles.copy()
    pct_cpy["half_of_two_z_scores"] = (
        pct_cpy["M"]
        * np.power((1 + pct_cpy["L"] * pct_cpy["S"] * 2), (1 / pct_cpy["L"]))
    ) - pct_cpy["M"]
    # Calculate an age in months by rounding and then adding 0.5 to have values that
    # match the growth chart
    merged_df["agemos"] = np.around(merged_df["ageyears"] * 12) + 0.5
    mswpt = merged_df.merge(
        pct_cpy[["Agemos", "M", "Sex", "half_of_two_z_scores"]],
        how="left",
        left_on=["sex", "agemos"],
        right_on=["Sex", "Agemos"],
    )
    z_column_name = {"weight": "wtz", "height": "htz", "bmi": "bmiz"}
    mswpt[z_column_name[category]] = (mswpt[category] - mswpt["M"]) / mswpt[
        "half_of_two_z_scores"
    ]
    return mswpt.drop(columns=["Agemos", "Sex", "M", "half_of_two_z_scores"])


def calculate_smoothed_zscore_pediatrics(df_merged, df_percentiles):
    """
    Add column to provided DataFrame with smoothed Z scores

    Parameters:
    df_merged: (DataFrame) with subjid, sex, weight, and age columns
    df_percentiles: (DataFrame) growth chart w/WHO and CDC L, M, S values for
        each measurement type

    Returns:
    DataFrame with smoothed zscore column for each measurement type
    """
    df_pct = df_percentiles.copy()

    # Merge z scores into observations
    df = df_merged.merge(
        df_pct,
        how="left",
        left_on=["agedays", "ageyears", "sex"],
        right_on=["agedays", "age", "Sex"],
    )

    for p, param in (("ht", "height"), ("wt", "weight"), ("bmi", "bmi")):
        cdc_l_var = f"cdc_{p}_l"
        cdc_m_var = f"cdc_{p}_m"
        cdc_s_var = f"cdc_{p}_s"
        cdc_csd_pos_var = f"cdc_{p}_csd_pos"
        cdc_csd_neg_var = f"cdc_{p}_csd_neg"
        cdc_z_var = f"cdc_{p}_z"
        who_z_var = f"who_{p}_z"
        s_z_var = f"{p}z"

        # Assign CDC z scores
        df[cdc_z_var] = np.where(
            df[cdc_l_var] != 0,
            (
                (((df[param] / df[cdc_m_var]) ** df[cdc_l_var]) - 1)
                / (df[cdc_l_var] * df[cdc_s_var])
            ),
            (np.log(df[param] / df[cdc_m_var]) / df[cdc_s_var]),
        )

        # Assign WHO z scores
        df.loc[df[param] == df[cdc_m_var], who_z_var] = 0
        df.loc[df[param] > df[cdc_m_var], who_z_var] = (df[param] - df[cdc_m_var]) / (
            df[cdc_csd_pos_var] / 2
        )
        df.loc[df[param] < df[cdc_m_var], who_z_var] = (df[param] - df[cdc_m_var]) / (
            df[cdc_csd_neg_var] / 2
        )

        # Assign z scores, smoothing between 2-4
        df.loc[df["ageyears"] <= 2, s_z_var] = df[who_z_var]
        df.loc[df["ageyears"].between(2, 4, inclusive="neither"), s_z_var] = (
            (df[who_z_var] * df["whoweight"]) + (df[cdc_z_var] * df["cdcweight"])
        ) / 2
        df.loc[df["ageyears"] >= 4, s_z_var] = df[cdc_z_var]

    return df
