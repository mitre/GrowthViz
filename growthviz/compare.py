import numpy as np
import pandas as pd


def prepare_for_comparison(frame_dict):
    """
    This is the function that should be used when planning on comparing multiple runs to one another.
    It takes in a dictionary of run names to run DataFrames. It outputs a single DataFrame with an
    additional run_name column. This is the format expected by other functions that perform run
    comparison.

    Parameters:
    frame_dict: A dictionary where the keys are the user specified name of a particular growthcleanr
      run and the values are DataFrames, in the format output by setup_individual_obs_df.

    Returns:
    A single DataFrame in the same format as returned by setup_individual_obs_df but with an additional
    run_name column.
    """
    frames = list(map(lambda i: i[1].assign(run_name=i[0]), frame_dict.items()))
    return pd.concat(frames)


def count_comparison(combined_df):
    """
    Provides a DataFrame that compares counts of growthcleanr categories between runs.

    Parameters:
    combined_df: A DataFrame in the format provided by prepare_for_comparison

    Returns:
    A DataFrame where the categories are the index and the columns are the run names.
    """
    grouped = (
        combined_df.groupby(["run_name", "clean_value"])
        .agg({"id": "count"})
        .reset_index()
        .pivot(index="clean_value", columns="run_name", values="id")
    )
    grouped = grouped.fillna(0)
    if grouped.columns.size == 2:
        grouped["diff"] = grouped[grouped.columns[1]] - grouped[grouped.columns[0]]
        grouped["tmp_sort"] = grouped["diff"].replace(0, np.NINF)
        grouped = grouped.sort_values("tmp_sort", ascending=False)
        grouped = grouped.drop(columns=["tmp_sort"])
    return grouped.style.format("{:.0f}")


def subject_comparison_category_counts(combined_df):
    """
    Provides a DataFrame that counts the number of subjects with at least one measurement in one of
    the growthcleanr categories, by run.

    Parameters:
    combined_df: A DataFrame in the format provided by prepare_for_comparison

    Returns:
    A DataFrame where the categories are the index and the columns are the run names.
    """
    grouped = (
        combined_df.groupby(["run_name", "clean_value"])
        .agg({"subjid": "nunique"})
        .reset_index()
        .pivot(index="clean_value", columns="run_name", values="subjid")
    )
    grouped = grouped.fillna(0)
    if grouped.columns.size == 2:
        grouped["diff"] = grouped[grouped.columns[1]] - grouped[grouped.columns[0]]
        grouped["population percent change"] = (
            (grouped[grouped.columns[1]] - grouped[grouped.columns[0]])
            / grouped[grouped.columns[1]].sum()
        ) * 100
        grouped["tmp_sort"] = grouped["diff"].replace(0, np.NINF)
        grouped = grouped.sort_values("tmp_sort", ascending=False)
        grouped = grouped.drop(columns=["tmp_sort"])
        grouped = grouped.style.format(
            {
                grouped.columns[0]: "{:.0f}",
                grouped.columns[1]: "{:.0f}",
                "diff": "{:.0f}",
                "population percent change": "{:.2f}%",
            }
        )
    return grouped


def subject_comparison_percentage(combined_df):
    """
    Provides a DataFrame that computes the percentage of subjects with at least one measurement in one of the
    growthcleanr categories, by run.

    Parameters:
    combined_df: A DataFrame in the format provided by prepare_for_comparison

    Returns:
    A DataFrame where the categories are the index and the columns are the run names.
    """
    grouped = (
        combined_df.groupby(["run_name", "clean_value"])
        .agg({"subjid": "nunique"})
        .reset_index()
        .pivot(index="clean_value", columns="run_name", values="subjid")
    )
    grouped = grouped.fillna(0)
    for c in grouped.columns:
        grouped[c] = (
            grouped[c] / combined_df[combined_df.run_name == c].subjid.nunique()
        ) * 100
    if grouped.columns.size == 2:
        grouped["diff"] = grouped[grouped.columns[1]] - grouped[grouped.columns[0]]
        grouped["tmp_sort"] = grouped["diff"].replace(0, np.NINF)
        grouped = grouped.sort_values("tmp_sort", ascending=False)
        grouped = grouped.drop(columns=["tmp_sort"])
    return grouped.style.format("{:.2f}%")


def subject_stats_comparison(combined_df):
    """
    Calculates the percentage of subjects with an exclusion and the rate of exclusions per
    patient.

    Parameters:
    combined_df: A DataFrame in the format provided by prepare_for_comparison

    Returns:
    A DataFrame with run names as the index and the columns of percentages of subjects and
    rates of exclusion.
    """
    stats = []
    for rn in combined_df.run_name.unique():
        total_subjects = combined_df[combined_df.run_name == rn].subjid.nunique()
        only_exclusions = combined_df[
            (combined_df.run_name == rn) & (combined_df.include is False)
        ]
        percent_with_exclusion = (
            only_exclusions.subjid.nunique() / total_subjects
        ) * 100
        exclusion_per = only_exclusions.shape[0] / total_subjects
        stats.append(
            {
                "run name": rn,
                "percent with exclusion": percent_with_exclusion,
                "exclusions per patient": exclusion_per,
            }
        )
    return pd.DataFrame.from_records(stats, index="run name")
