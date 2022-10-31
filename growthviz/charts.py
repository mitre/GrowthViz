import math
import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

def weight_distr(df, mode):
    """
    Create charts with overall and outlier weight distributions (included values only)
    """
    wgt_grp = df[(df["param"] == "WEIGHTKG") & (df["include"] == True)]
    if mode == "high":
        wgt_grp = wgt_grp.loc[wgt_grp["measurement"] >= 135]
        plt.title("Weights At or Above 135kg")
    else:
        plt.title("All Weights")
    if len(wgt_grp.index) == 0:
        print("No included observations with weight (kg) >= 135")
        plt.close()
    else:
        round_col = wgt_grp.apply(
            lambda row: np.around(row.measurement, decimals=0), axis=1
        )
        wgt_grp = wgt_grp.assign(round_weight=round_col.values)
        wgt_grp_sum = wgt_grp.groupby("round_weight")["subjid"].count().reset_index()
        plt.rcParams["figure.figsize"] = [7, 5]
        wgt_grp_sum_plot = plt.bar(wgt_grp_sum["round_weight"], wgt_grp_sum["subjid"])
        # Assure there is some breadth to the x-axis in case of just a few observations
        if wgt_grp["measurement"].max() - wgt_grp["measurement"].min() < 10:
            plt.xlim(wgt_grp["measurement"].min() - 5, wgt_grp["measurement"].max() + 5)
        plt.ylabel("Total Patient Observations")
        plt.xlabel("Recorded Weight (Kg)")
        plt.grid()
        plt.show()
        
def make_age_charts(df, mode):
    
    obs_grp = df
    # Create reference frames for adults and pediatrics
    label_frame = pd.DataFrame({})
   
    if mode == "adults":
        label_frame = pd.DataFrame({
            "min": np.array([0, 18, 30, 40, 50, 60, 65, 80]),
            "max": np.array([18, 30, 40, 50, 60, 65, 80, 150]),
            "label": pd.Categorical(["<18", "18-30", "30-40", "40-50", "50-60", "60-65",
                                "65-80", "80-"]),
            "sort_order": pd.Series(["A", "B", "C", "D", "E", "F", "G", "H"], dtype="string"),
            "color": pd.Series(["C3", "C0", "C0", "C0", "C0", "C0", "orange", "C3"], dtype="string"),
            "symbol": pd.Series(["x", "", "", "", "", "", "/", "x"], dtype="string"),
        })
        
    elif mode == "pediatrics":
        label_frame = pd.DataFrame({
            "min": np.array([0, 2, 5, 8, 11, 14, 17, 20, 25]),
            "max": np.array([2, 5, 8, 11, 14, 17, 20, 25, 150]),
            "label": pd.Categorical(["0-2", "2-5", "5-8", "8-11", "11-14", "14-17",
                                   "17-20", "20-25", "25-"]),
            "sort_order": pd.Series(["A", "B", "C", "D", "E", "F", "G", "H", "I"], dtype="string"),
            "color": pd.Series(["C0", "C0", "C0", "C0", "C0", "C0", "C0", "orange", "C3"], dtype="string"),
            "symbol": pd.Series(["", "", "", "", "", "", "", "/", "x"], dtype="string"),
        })
    
    # New Categorizing function which adds label, color, pattern and sort order columns to the dataframe
    # Adds these categories based on the age of each row in the dataframe
    def add_categories_to_frame(df_data, df_reference):
        categories = []
        colors = []
        patterns = []
        sort_order = []
        for j in range(len(df_data)):
            for i in range(len(df_reference)):
                minVal = df_reference['min'][i]
                maxVal = df_reference['max'][i]
                if df_data['age'][j] >= minVal and df_data['age'][j] < maxVal:
                    categories.append(df_reference['label'][i])
                    colors.append(df_reference['color'][i])
                    patterns.append(df_reference['symbol'][i])
                    sort_order.append(df_reference['sort_order'][i])
        df_data['category'] = categories  
        df_data['colors'] = colors  
        df_data['patterns'] = patterns
        df_data['sort_order'] = sort_order
        return df_data
    
    # Call the categorizing function on the data
    obs_grp = add_categories_to_frame(obs_grp, label_frame)
    
    # Groups the new dataframe by category, sort order, colors and patterns. It then counts the number of subject ids 
    # in each group and sorts the values by sort order. 
    obs_grp = (
        obs_grp.groupby(["category", "sort_order", "colors", "patterns"])["subjid"]
        .count()
        .reset_index()
        .sort_values(by=['sort_order'])
    )
    
    # create chart
    fig, ax1 = plt.subplots()
    obs_grp_plot = plt.bar(
        obs_grp["category"],
        obs_grp["subjid"],
        color=obs_grp["colors"],
    )
    
    # Sets the pattern for each bar in the graph. 
    for bar, pattern in zip(obs_grp_plot, obs_grp["patterns"]):
        bar.set_hatch(pattern)
    plt.xticks(rotation=45, ha="right")
    ax1.get_yaxis().set_major_formatter(
        mpl.ticker.FuncFormatter(lambda x, p: format(int(x), ","))
    )
    
    plt.ylabel("Number of Subjects")
    plt.xlabel("Age Ranges")
    if mode == "pediatrics":
        plt.title("Age Chart for Pediatrics")
    elif mode == "adults":
        plt.title("Age Chart for Adults")
    

def overlap_view_adults(
    obs_df,
    subjid,
    param,
    include_carry_forward,
    include_percentiles,
    wt_df,
    bmi_df,
    ht_df,
):
    """
    Creates a chart showing the trajectory for an individual with all values present. All values will
    be plotted with a blue line. Excluded values will be represented by a red x. A yellow dashed line
    shows the resulting trajectory when excluded values are removed.

    Parameters:
    obs_df: (DataFrame) with subjid, sex, age, measurement, param and clean_value columns
    subjid: (String) Id of the individuals to be plotted
    param: (String) Whether to plot heights or weights. Expected values are "HEIGHTCM" or "WEIGHTKG"
    include_carry_forward: (Boolean) If True, it will show carry forward values as a triangle and the
                           yellow dashed line will include carry forward values. If False, carry
                           forwards are excluded and will be shown as red x's.
    include_percentiles: (Boolean) Controls whether the 5th and 95th percentile bands are displayed
                         on the chart
    wt_df: (DataFrame) with the CDC growth charts by age for weight
    ht_df: (DataFrame) with the CDC growth charts by age for height
    """
    individual = obs_df[obs_df.subjid == subjid]
    selected_param = individual[individual.param == param]
    filter_excl = (
        selected_param.clean_cat.isin(["Include", "Exclude-Carried-Forward"])
        if include_carry_forward
        else selected_param.clean_value == "Include"
    )
    excluded_selected_param = selected_param[~filter_excl]
    included_selected_param = selected_param[filter_excl]
    plt.rcParams["figure.figsize"] = [6, 4]
    selected_param_plot = selected_param.plot.line(
        x="age", y="measurement", label="All Measurements", lw=3
    )  # could instead have the marker on the all measurements line, a little messier
    selected_param_plot.plot(
        included_selected_param["age"],
        included_selected_param["measurement"],
        c="y",
        linestyle="-.",
        lw=3,
        marker="o",
        label="Included Only",
    )  # could also try violet
    selected_param_plot.scatter(
        x=excluded_selected_param.age,
        y=excluded_selected_param.measurement,
        c="r",
        marker="x",
        zorder=3,
    )
    xmin = math.floor(individual.age.min())
    xmax = math.ceil(individual.age.max())
    selected_param_plot.set_xlim(xmin, xmax)
    if include_carry_forward == True:
        carry_forward = selected_param[
            selected_param.clean_value == "Exclude-Carried-Forward"
        ]
        selected_param_plot.scatter(
            x=carry_forward.age, y=carry_forward.measurement, c="c", marker="^"
        )
    if include_percentiles == True:
        if param == "WEIGHTKG":
            percentile_df = wt_df
        elif param == "BMI":
            percentile_df = bmi_df
        else:
            percentile_df = ht_df
        percentile_window = percentile_df.loc[
            (percentile_df.Sex == individual.sex.min())
            & (percentile_df.age >= xmin)
            & (percentile_df.age <= xmax)
        ]
        if (param == "HEIGHTCM") | (param == "WEIGHTKG"):
            selected_param_plot.plot(
                percentile_window.age,
                percentile_window.P5,
                color="grey",
                label="5th Percentile",
                linestyle="--",
                marker="_",
                zorder=1,
            )
            selected_param_plot.plot(
                percentile_window.age,
                percentile_window.P95,
                color="grey",
                label="95th Percentile",
                linestyle="dotted",
                zorder=1,
            )
        if param == "BMI":
            edge = (xmax - xmin) / 30
            x = 25
            selected_param_plot.axhline(x, color="tan", zorder=1)
            selected_param_plot.text(
                xmax + edge, x, "Overweight (25-30 BMI)", ha="left"
            )
            y = 30
            selected_param_plot.axhline(y, color="tan", zorder=1)
            selected_param_plot.text(xmax + edge, y, "Obesity (30+ BMI)", ha="left")
            if (
                included_selected_param["measurement"].min() < 25
            ):  # might want to make lower with more data
                z = 18.5
                selected_param_plot.axhline(z, color="pink", zorder=1)
                selected_param_plot.text(
                    xmax + edge, z, "Underweight (<18.5 BMI)", ha="left"
                )
    selected_param_plot.legend(loc="upper left", bbox_to_anchor=(1.05, 1))
    plt.title(param)
    return selected_param_plot


def overlap_view_adults_show(
    obs_df,
    subjid,
    param,
    include_carry_forward,
    include_percentiles,
    wt_df,
    bmi_df,
    ht_df,
):
    """
    Wraps overlap_view_adult with plt.show().
    """
    plot = overlap_view_adults(
        obs_df,
        subjid,
        param,
        include_carry_forward,
        include_percentiles,
        wt_df,
        bmi_df,
        ht_df,
    )
    plt.show()


def overlap_view_pediatrics(
    obs_df, subjid, param, include_carry_forward, include_percentiles, wt_df, ht_df
):
    """
    Creates a chart showing the trajectory for an individual with all values present. All values will
    be plotted with a blue line. Excluded values will be represented by a red x. A yellow dashed line
    shows the resulting trajectory when excluded values are removed.
    Parameters:
    obs_df: (DataFrame) with subjid, sex, age, measurement, param and clean_value columns
    subjid: (String) Id of the individuals to be plotted
    param: (String) Whether to plot heights or weights. Expected values are "HEIGHTCM" or "WEIGHTKG"
    include_carry_forward: (Boolean) If True, it will show carry forward values as a triangle and the
                           yellow dashed line will include carry forward values. If False, carry
                           forwards are excluded and will be shown as red x's.
    include_percentiles: (Boolean) Controls whether the 5th and 95th percentile bands are displayed
                         on the chart
    wt_df: (DataFrame) with the CDC growth charts by age for weight
    ht_df: (DataFrame) with the CDC growth charts by age for height
    """
    individual = obs_df[obs_df.subjid == subjid]
    selected_param = individual[individual.param == param]
    filter_excl = (
        selected_param.clean_value.isin(["Include", "Exclude-Carried-Forward"])
        if include_carry_forward
        else selected_param.clean_value == "Include"
    )
    excluded_selected_param = selected_param[~filter_excl]
    included_selected_param = selected_param[filter_excl]
    selected_param_plot = selected_param.plot.line(x="age", y="measurement")
    selected_param_plot.plot(
        included_selected_param["age"],
        included_selected_param["measurement"],
        c="y",
        linestyle="-.",
    )
    selected_param_plot.scatter(
        x=excluded_selected_param.age,
        y=excluded_selected_param.measurement,
        c="r",
        marker="x",
    )
    if include_carry_forward == True:
        carry_forward = selected_param[
            selected_param.clean_value == "Exclude-Carried-Forward"
        ]
        selected_param_plot.scatter(
            x=carry_forward.age, y=carry_forward.measurement, c="c", marker="^"
        )
    if include_percentiles == True:
        percentile_df = wt_df if param == "WEIGHTKG" else ht_df
        percentile_window = percentile_df.loc[
            (percentile_df.Sex == individual.sex.min())
            & (percentile_df.age > individual.age.min())
            & (percentile_df.age < individual.age.max())
        ]
        selected_param_plot.plot(
            percentile_window.age, percentile_window.P5, color="k", zorder=1
        )
        selected_param_plot.plot(
            percentile_window.age, percentile_window.P95, color="k", zorder=1
        )
    return selected_param_plot


def overlap_view_pediatrics_show(
    obs_df, subjid, param, include_carry_forward, include_percentiles, wt_df, ht_df
):
    """
    Wraps overlap_view_pediatrics with plt.show().
    """
    plot = overlap_view_pediatrics(
        obs_df, subjid, param, include_carry_forward, include_percentiles, wt_df, ht_df
    )
    plt.show()


def overlap_view_double_pediatrics(
    obs_df,
    subjid,
    show_all_measurements,
    show_excluded_values,
    show_trajectory_with_exclusions,
    include_carry_forward,
    include_percentiles,
    wt_df,
    ht_df,
):
    """
    Creates a chart showing the trajectory for an individual with all values present. All values will
    be plotted with a blue line. Excluded values will be represented by a red x. A yellow dashed line
    shows the resulting trajectory when excluded values are removed.

    Parameters:
    obs_df: (DataFrame) with subjid, sex, age, measurement, param and clean_value columns
    subjid: (String) Id of the individuals to be plotted
    include_carry_forward: (Boolean) If True, it will show carry forward values as a triangle and the
                           yellow dashed line will include carry forward values. If False, carry
                           forwards are excluded and will be shown as red x's.
    include_percentiles: (Boolean) Controls whether the percentile bands are displayed
                         on the chart
    wt_df: (DataFrame) with the CDC growth charts by age for weight
    ht_df: (DataFrame) with the CDC growth charts by age for height
    """
    individual = obs_df[obs_df.subjid == subjid]
    height = individual[individual.param == "HEIGHTCM"]
    weight = individual[individual.param == "WEIGHTKG"]
    filter_excl = (
        height.clean_value.isin(["Include", "Exclude-Carried-Forward"])
        if include_carry_forward
        else height.clean_value == "Include"
    )
    filter_excl_weight = (
        weight.clean_value.isin(["Include", "Exclude-Carried-Forward"])
        if include_carry_forward
        else weight.clean_value == "Include"
    )
    excluded_height = height[~filter_excl]
    excluded_weight = weight[~filter_excl_weight]
    included_height = height[filter_excl]
    included_weight = weight[filter_excl_weight]
    plt.rcParams["figure.figsize"] = [8, 10]
    fig, ax1 = plt.subplots()
    color = "tab:red"
    color_secondary = "tab:blue"
    ax1.set_ylim([50, 180])
    ax1.set_xlim([2, 20])
    ax1.set_xlabel("age (years)")
    ax1.set_ylabel("stature (cm)", color=color)

    ax2 = ax1.twinx()  # instantiate a second axes that shares the same x-axis

    ax2.set_ylim([0, 160])
    ax2.set_ylabel(
        "weight (kg)", color=color_secondary
    )  # we already handled the x-label with ax1
    if include_percentiles == True:
        percentile_window = wt_df.loc[wt_df.Sex == individual.sex.min()]
        ax2.plot(percentile_window.age, percentile_window.P5, color="lightblue")
        ax2.plot(
            percentile_window.age, percentile_window.P10, color="lightblue", alpha=0.5
        )
        ax2.plot(
            percentile_window.age, percentile_window.P25, color="lightblue", alpha=0.5
        )
        ax2.plot(percentile_window.age, percentile_window.P50, color="lightblue")
        ax2.plot(
            percentile_window.age, percentile_window.P75, color="lightblue", alpha=0.5
        )
        ax2.plot(
            percentile_window.age, percentile_window.P90, color="lightblue", alpha=0.5
        )
        ax2.plot(percentile_window.age, percentile_window.P95, color="lightblue")
        percentile_window_ht = ht_df.loc[ht_df.Sex == individual.sex.min()]
        ax1.plot(percentile_window_ht.age, percentile_window_ht.P5, color="pink")
        ax1.plot(
            percentile_window_ht.age, percentile_window_ht.P10, color="pink", alpha=0.5
        )
        ax1.plot(
            percentile_window_ht.age, percentile_window_ht.P25, color="pink", alpha=0.5
        )
        ax1.plot(percentile_window_ht.age, percentile_window_ht.P50, color="pink")
        ax1.plot(
            percentile_window_ht.age, percentile_window_ht.P75, color="pink", alpha=0.5
        )
        ax1.plot(
            percentile_window_ht.age, percentile_window_ht.P90, color="pink", alpha=0.5
        )
        ax1.plot(percentile_window_ht.age, percentile_window_ht.P95, color="pink")

    if show_all_measurements == True:
        ax1.plot(height["age"], height["measurement"], color=color, label="stature")
        ax2.plot(
            weight["age"], weight["measurement"], color=color_secondary, label="weight"
        )

    if show_excluded_values == True:
        ax1.scatter(
            excluded_height.age, excluded_height.measurement, c="black", marker="x"
        )
        ax2.scatter(
            excluded_weight.age, excluded_weight.measurement, c="black", marker="x"
        )

    if show_trajectory_with_exclusions == True:
        ax1.plot(
            included_height["age"],
            included_height["measurement"],
            c="y",
            linestyle="-.",
        )
        ax2.plot(
            included_weight["age"],
            included_weight["measurement"],
            c="y",
            linestyle="-.",
        )

    ax1.tick_params(axis="y", labelcolor=color)
    ax2.tick_params(axis="y", labelcolor=color_secondary)

    fig.tight_layout()  # otherwise the right y-label is slightly clipped

    if include_carry_forward == True:
        carry_forward_height = height[height.clean_value == "Exclude-Carried-Forward"]
        carry_forward_weight = weight[weight.clean_value == "Exclude-Carried-Forward"]
        ax1.scatter(
            x=carry_forward_height.age,
            y=carry_forward_height.measurement,
            c="c",
            marker="^",
        )
        ax2.scatter(
            x=carry_forward_weight.age,
            y=carry_forward_weight.measurement,
            c="c",
            marker="^",
        )

    # Reset figsize to default
    plt.rcParams["figure.figsize"] = [6.4, 4.8]
    plt.show()


def mult_obs(obs):
    """
    Removes individuals from consideration for five_by_five_view() charts that only have one observation in the data
    """
    obs["cat_count"] = obs.groupby(["subjid", "param"])["age"].transform("count")
    obs["one_rec"] = np.where(obs["cat_count"] == 1, 1, 0)
    obs["any_ones"] = obs.groupby(["subjid"])["one_rec"].transform("max")
    obs["max"] = obs.groupby("subjid")["age"].transform("max")
    obs["min"] = obs.groupby("subjid")["age"].transform("min")
    obs["range"] = np.ceil(obs["max"]) - np.floor(obs["min"])
    return obs[obs["any_ones"] == 0]


def five_by_five_shape(n):
    """
    Determines shape of five by five view, allowing for fewer than 25 observations.

    Parameters:
    n: length of subject list to display

    Returns:
    Dimensions of grid/subplots as (nrows, ncols)
    """
    if n // 5 == 0:
        return (1, n % 5)
    elif n % 5 > 0:
        return ((n // 5) + 1, 5)
    else:
        return (n // 5, 5)


def five_by_five_view(obs_df, subjids, param, wt_df, ht_df, bmi_df, linestyle):
    """
    Creates a small multiples plot showing the growth trend for 25 individuals

    Parameters:
    obs_df: (DataFrame) with subjid, measurement, param and clean_value columns
    subjids: An list of the ids of the individuals to be plotted
    param: (String) Whether to plot heights or weights. Expected values are "HEIGHTCM" or "WEIGHTKG"
    """
    if len(subjids) == 0:
        print("No matching subjects found.")
        return
    nrows, ncols = five_by_five_shape(len(subjids))
    fig, ax = plt.subplots(nrows, ncols)
    for y in range(ncols):
        for x in range(nrows):
            try:
                subjid = subjids[x * 5 + y]
            except IndexError as ie:
                # No more subjects to render
                break
            individual = obs_df[obs_df.subjid == subjid]
            selected_param = individual[individual.param == param]
            # Indexing varies by dimensionality, so simplify
            if nrows > 1:
                tgt = ax[x, y]
            elif len(subjids) == 1:
                tgt = ax
            else:
                tgt = ax[y]
            tgt.plot(selected_param.age, selected_param.measurement, marker=".")
            excluded_selected_param = selected_param[
                selected_param.clean_value != "Include"
            ]
            tgt.scatter(
                excluded_selected_param.age,
                excluded_selected_param.measurement,
                c="r",
                marker="x",
            )
            if param == "WEIGHTKG":
                percentile_df = wt_df
            elif param == "BMI":
                percentile_df = bmi_df
            else:
                percentile_df = ht_df
            percentile_window = percentile_df.loc[
                (percentile_df.Sex == individual.sex.min())
                & (percentile_df.age >= math.floor(individual.age.min()))
                & (percentile_df.age <= math.ceil(individual.age.max()))
            ]
            tgt.plot(
                percentile_window.age,
                percentile_window.P5,
                color="k",
                linestyle=linestyle,
                zorder=1,
            )
            tgt.plot(
                percentile_window.age,
                percentile_window.P95,
                color="k",
                linestyle=linestyle,
                zorder=1,
            )
            tgt.set(title=subjid)
    # Set size dynamically to average out about the same
    fig.set_size_inches(4 * ncols, 2.4 * nrows)
    return plt.tight_layout()


def bmi_with_percentiles(merged_df, bmi_percentiles, subjid):
    """
    Displays two charts showing BMI trajectory. The chart on the left will include all
    values, while the chart on the right will only show values categorized as "Include"
    by growthcleanr.

    Parameters:
    merged_df: (DataFrame) with subjid, bmi, include_height, include_weight, rounded_age
               and sex columns
    bmi_percentiles: (DataFrame) CDC growth chart containing BMI percentiles for age
    subjid: (String) Id of the individual to plot
    """
    individual = merged_df[merged_df.subjid == subjid]
    fig, ax = plt.subplots(1, 2)
    percentile_window = bmi_percentiles.loc[
        (bmi_percentiles.Sex == individual.sex.min())
        & (bmi_percentiles.age > individual.age.min())
        & (bmi_percentiles.age < individual.age.max())
    ]
    ax[0].plot(individual.age, individual.bmi)
    ax[0].plot(percentile_window.age, percentile_window.P5, color="k")
    ax[0].plot(percentile_window.age, percentile_window.P95, color="k")

    ax[0].set(xlabel="age (y)", ylabel="BMI", title="BMI All Values")
    ax[0].grid()

    ax[1].plot(
        individual[individual.include_height & individual.include_weight].age,
        individual.loc[individual.include_height & individual.include_weight].bmi,
    )
    ax[1].plot(percentile_window.age, percentile_window.P5, color="k")
    ax[1].plot(percentile_window.age, percentile_window.P95, color="k")

    ax[1].set(xlabel="age (y)", ylabel="BMI", title="BMI Cleaned")
    ax[1].grid()
    plt.show()


def param_with_percentiles(merged_df, subjid, param, wt_df, ht_df, bmi_df):
    """
    A version of bmi_with_percentiles() that provides the option of looking at wt or ht as well
    """
    individual = merged_df[(merged_df.subjid == subjid) & (merged_df.param == param)]
    fig, ax = plt.subplots(1, 2, sharey="row")
    if param == "WEIGHTKG":
        percentile_df = wt_df
    elif param == "BMI":
        percentile_df = bmi_df
    else:
        percentile_df = ht_df
    percentile_window = percentile_df.loc[
        (percentile_df.Sex == individual.sex.min())
        & (percentile_df.age > individual.age.min())
        & (percentile_df.age < individual.age.max())
    ]
    ax[0].plot(individual.age, individual.measurement)
    ax[0].plot(percentile_window.age, percentile_window.P5, color="k")
    ax[0].plot(percentile_window.age, percentile_window.P95, color="k")

    ax[0].set(xlabel="age (y)", ylabel=param, title=(param + " All Values"))
    ax[0].grid()

    included_individual = individual[individual.clean_cat.isin(["Include"])]
    ax[1].plot(included_individual.age, included_individual.measurement)
    ax[1].plot(percentile_window.age, percentile_window.P5, color="k")
    ax[1].plot(percentile_window.age, percentile_window.P95, color="k")

    ax[1].set(xlabel="age (y)", ylabel="", title=(param + " Cleaned"))
    ax[1].grid()
    plt.show()


def top_ten(
    merged_df,
    field,
    age=None,
    sex=None,
    wexclusion=None,
    hexclusion=None,
    order="largest",
    out=None,
):
    """
    Displays the top ten records depending on the criteria passed in

    Parameters:
    merged_df: (DataFrame) with subjid, bmi, height, weight, include_height, include_weight, rounded_age
               and sex columns
    field: (String) What field to sort on. Expected values are "height", "weight" and "bmi"
    age: (List) Two elements containing the minimum and maximum ages that should be
         included in the statistics. None if no age filtering desired.
    sex: (Integer) 1 - Female, 0 - Male, None - no sex filtering
    wexclusion: (List) of weight exclusions to filter on. None - no weight exclusion filtering
    hexclusion: (List) of height exclusions to filter on. None - no height exclusion filtering
    order: (String) Sort order - Expected values are "smallest" and "largest"
    out: (ipywidgets.Output) displays the resilrs

    Returns:
    If out is None, it will return a DataFrame. If out is provided, results will be displayed
    in the notebook.
    """
    working_set = merged_df
    if age != None:
        working_set = working_set.loc[
            working_set.rounded_age.ge(age[0]) & working_set.rounded_age.le(age[1])
        ]
    if sex != None:
        working_set = working_set[working_set.sex == sex]
    if wexclusion != None:
        working_set = working_set[working_set.weight_cat.isin(wexclusion)]
    if hexclusion != None:
        working_set = working_set[working_set.height_cat.isin(hexclusion)]
    # if order == 'largest':
    #   working_set = working_set.nlargest(10, field)
    # else:
    #   working_set = working_set.nsmallest(10, field)
    working_set = working_set.drop(
        columns=["include_height", "include_weight", "include_both", "rounded_age"]
    )
    working_set["sex"] = working_set.sex.replace(0, "M").replace(1, "F")
    working_set["age"] = working_set.age.round(decimals=2)
    working_set["height"] = working_set.height.round(decimals=1)
    working_set["weight"] = working_set.weight.round(decimals=1)
    working_set["weight_cat"] = working_set.weight_cat.str.replace("Exclude-", "")
    working_set["height_cat"] = working_set.height_cat.str.replace("Exclude-", "")
    working_set = working_set[
        [
            "subjid",
            "sex",
            "age",
            "height",
            "height_cat",
            "htz",
            "weight",
            "weight_cat",
            "wtz",
            "bmi",
            "BMIz",
        ]
    ]
    if out == None:
        return working_set
    else:
        out.clear_output()
        out.append_display_data(working_set)
