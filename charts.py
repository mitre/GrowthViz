import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from IPython.display import FileLink, FileLinks, Markdown

def setup_individual_obs_df(obs_df):
  obs_df.rename(columns={'result':'clean_value'}, inplace=True)
  obs_df['clean_cat'] = obs_df['clean_value'].astype('category')
  obs_df['age'] = obs_df['agedays'] / 365
  obs_df['include'] = obs_df.clean_value.eq("Include")
  return obs_df

def setup_percentiles(percentiles):
  percentiles['Agemos'] = pd.to_numeric(percentiles['Agemos'], errors='coerce')
  percentiles['P5'] = pd.to_numeric(percentiles['P5'], errors='coerce')
  percentiles['P95'] = pd.to_numeric(percentiles['P95'], errors='coerce')
  percentiles['age'] = percentiles['Agemos'] / 12
  percentiles['Sex'] = pd.to_numeric(percentiles['Sex'], errors='coerce')
  percentiles['L'] = pd.to_numeric(percentiles['L'], errors='coerce')
  percentiles['M'] = pd.to_numeric(percentiles['M'], errors='coerce')
  percentiles['S'] = pd.to_numeric(percentiles['S'], errors='coerce')
  # Values by CDC (1=male; 2=female) differ from growthcleanr
  # which uses a numeric value of 0 (male) or 1 (female).
  # This aligns things to the growthcleanr values
  percentiles['Sex'] = percentiles['Sex'] - 1
  return percentiles

def setup_merged_df(obs_df):
  obs_df['height'] = np.where(obs_df['param'] == 'HEIGHTCM', obs_df['measurement'], np.NaN)
  obs_df['weight'] = np.where(obs_df['param'] == 'WEIGHTKG', obs_df['measurement'], np.NaN)
  heights = obs_df[obs_df.param == 'HEIGHTCM']
  weights = obs_df[obs_df.param == 'WEIGHTKG']
  merged = heights.merge(weights, on=['subjid', 'agedays', 'sex'], how='outer')
  only_needed_columns = merged.drop(columns=['param_x', 'measurement_x', 'clean_value_x',
                                             'age_x', 'weight_x', 'id_y', 'param_y',
                                             'measurement_y', 'clean_value_y', 'height_y',
                                             'ethnicity_x', 'ethnicity_y', 'event_date_x', 'event_date_y', 'site_key_x', 'site_key_y',
                                             'site_location_x', 'site_location_y', 'age_years_x', 'reason_x'])
  clean_column_names = only_needed_columns.rename(columns={'clean_cat_x': 'height_cat',
                                                           'include_x': 'include_height',
                                                           'height_x': 'height',
                                                           'clean_cat_y': 'weight_cat',
                                                           'age_y': 'age',
                                                           'include_y': 'include_weight',
                                                           'weight_y': 'weight',
                                                           'age_years_y':'age_years', 
                                                           'reason_y':'reason', 
                                                           'id_x':'id'})
  clean_column_names['bmi'] = clean_column_names['weight'] / ((clean_column_names['height'] / 100) ** 2)
  clean_column_names['rounded_age'] = np.around(clean_column_names.age)
  clean_column_names['include_both'] = clean_column_names['include_height'] & clean_column_names['include_weight']
  return clean_column_names

def add_mzscored_to_merged_df(merged_df, pctls): #merged_df, wt_percentiles, ht_percentiles, bmi_percentiles):
  #merged_df = calculate_modified_zscore(merged_df, wt_percentiles, 'weight')
  #merged_df = calculate_modified_zscore(merged_df, ht_percentiles, 'height')
  #merged_df = calculate_modified_zscore(merged_df, bmi_percentiles, 'bmi')
  merged_df = merged_df.merge(pctls, on=['sex', 'age_years'], how='left')
  return merged_df

def bmi_stats(merged_df, out=None, include_min=True, include_mean=True, include_max=True,
              include_std=True, include_mean_diff=True,
              include_count=True, age_range=[20, 65], include_missing=False):
  """
  Computes summary statistics for BMI. Clean values are for BMIs computed when both the height
  and weight values are categorized by growthcleanr as "Include". Raw values are computed for
  all observations. Information is provided by age and sex.

  Parameters:
  merged_df: (DataFrame) with bmi, rounded_age and sex columns
  out: (ipywidgets.Output) to display the results, if provided
  include_min: (Boolean) Whether to include the minimum value column
  include_mean: (Boolean) Whether to include the mean value column
  include_max: (Boolean) Whether to include the maximum value column
  include_std: (Boolean) Whether to include the standard deviation column
  include_mean_diff: (Boolean) Whether to include the difference between the raw and
            clean mean value column
  include_count: (Boolean) Whether to include the count column
  age_range: (List) Two elements containing the minimum and maximum ages that should be
            included in the statistics
  include_missing: (Boolean) Whether to include the missing (0) heights and weights that impact
            raw columns

  Returns:
  If out is None, it will return a DataFrame. If out is provided, results will be displayed
  in the notebook.
  """
  if include_missing:
    age_filtered = merged_df[(merged_df.rounded_age >= age_range[0]) & (merged_df.rounded_age <= age_range[1])]
  else:
    age_filtered = merged_df[(merged_df.rounded_age >= age_range[0]) & (merged_df.rounded_age <= age_range[1]) & (merged_df.weight > 0) & (merged_df.height > 0)]
  age_filtered['sex'] = age_filtered.sex.replace(0, 'M').replace(1, 'F')
  agg_functions = []
  formatters = {}
  # if not include_missing:
  #   age_filtered = age_filtered
  if include_min:
    agg_functions.append('min')
    formatters['min_clean'] = "{:.2f}".format
    formatters['min_raw'] = "{:.2f}".format
  if include_mean:
    agg_functions.append('mean')
    formatters['mean_clean'] = "{:.2f}".format
    formatters['mean_raw'] = "{:.2f}".format
  if include_max:
    agg_functions.append('max')
    formatters['max_clean'] = "{:.2f}".format
    formatters['max_raw'] = "{:.2f}".format
  if include_std:
    agg_functions.append('std')
    formatters['sd_clean'] = "{:.2f}".format
    formatters['sd_raw'] = "{:.2f}".format
  if include_count:
    agg_functions.append('count')
  clean_groups = age_filtered[age_filtered.include_both].groupby(['sex',
                                                            'rounded_age'])['bmi'].agg(agg_functions)
  raw_groups = age_filtered.groupby(['sex', 'rounded_age'])['bmi'].agg(agg_functions)
  merged_stats = clean_groups.merge(raw_groups, on=['sex', 'rounded_age'], suffixes=('_clean', '_raw'))
  if include_mean & include_count & include_mean_diff:
    merged_stats['count_diff'] = merged_stats['count_raw'] - merged_stats['count_clean']
  if include_std:
    merged_stats = merged_stats.rename(columns={'std_raw': 'sd_raw', 'std_clean': 'sd_clean'})
  if out == None:
    return merged_stats
  else:
    out.clear_output()
    out.append_display_data(Markdown("## Female"))
    out.append_display_data(merged_stats.loc['F'].style.format(formatters))
    out.append_display_data(Markdown("## Male"))
    out.append_display_data(merged_stats.loc['M'].style.format(formatters))

def overlap_view(obs_df, subjid, param, include_carry_forward, include_percentiles, wt_df, bmi_df, ht_df):
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
  filter = selected_param.clean_value.isin(['Include', 'Exclude-Carried-Forward']) if include_carry_forward else selected_param.clean_value == 'Include'
  excluded_selected_param = selected_param[~filter]
  included_selected_param = selected_param[filter]
  selected_param_plot = selected_param.plot.line(x='age', y='measurement')
  selected_param_plot.plot(included_selected_param['age'],
                           included_selected_param['measurement'], c='y', linestyle='-.')
  selected_param_plot.scatter(x=excluded_selected_param.age,
                              y=excluded_selected_param.measurement, c='r', marker="x")
  if include_carry_forward == True:
    carry_forward = selected_param[selected_param.clean_value == 'Exclude-Carried-Forward']
    selected_param_plot.scatter(x=carry_forward.age,
                                y=carry_forward.measurement, c='c', marker="^")
  if include_percentiles == True:
    if param == 'WEIGHTKG': percentile_df = wt_df 
    elif param == 'BMI': percentile_df = bmi_df 
    else: percentile_df = ht_df
    percentile_window = percentile_df.loc[(percentile_df.sex == individual.sex.min()) &
                                          (percentile_df.age_years > individual.age.min()) &
                                          (percentile_df.age_years < individual.age.max())]
    selected_param_plot.plot(percentile_window.age_years, percentile_window.P5, color='k', label='5th Percentile', linestyle='--') 
    selected_param_plot.plot(percentile_window.age_years, percentile_window.P95, color='k', label='95th Percentile', linestyle='-.')
    if param == 'BMI':
      selected_param_plot.axhspan(25, 30, color='#FEFE62', alpha=0.5, lw=0, label='Overweight (25-30 BMI)')
      selected_param_plot.axhspan(30, 50, color='#D35FB7', alpha=0.5, lw=0, label='Obese (30-50 BMI)')
  selected_param_plot.legend(loc="upper left", bbox_to_anchor=(1.05, 1))

  return selected_param_plot

def overlap_view_all(obs_df, id, param, include_carry_forward, include_percentiles, wt_df, bmi_df, ht_df):
  """
  FILL IN HERE
  """
  individual = obs_df[obs_df.subjid == id]
  selected_param = individual[individual.param == param]
  filter = selected_param.clean_value.isin(['Include', 'Exclude-Carried-Forward']) if include_carry_forward else selected_param.clean_value == 'Include'
  excluded_selected_param = selected_param[~filter]
  included_selected_param = selected_param[filter]
  selected_param_plot = selected_param.plot.line(x='age', y='measurement')
  selected_param_plot.plot(included_selected_param['age'],
                           included_selected_param['measurement'], c='y', linestyle='-.', marker='o')
  selected_param_plot.scatter(x=excluded_selected_param.age,
                              y=excluded_selected_param.measurement, c='r', marker="x")
  if include_carry_forward == True:
    carry_forward = selected_param[selected_param.clean_value == 'Exclude-Carried-Forward']
    selected_param_plot.scatter(x=carry_forward.age,
                                y=carry_forward.measurement, c='c', marker="^")
  if include_percentiles == True:
    if param == 'WEIGHTKG': percentile_df = wt_df 
    elif param == 'BMI': percentile_df = bmi_df 
    else: percentile_df = ht_df
    percentile_window = percentile_df.loc[(percentile_df.sex == individual.sex.min()) &
                                          (percentile_df.age_years > individual.age.min()) &
                                          (percentile_df.age_years < individual.age.max())]
    selected_param_plot.plot(percentile_window.age_years, percentile_window.P5, color='k', label='5th Percentile', linestyle='--') 
    selected_param_plot.plot(percentile_window.age_years, percentile_window.P95, color='k', label='95th Percentile', linestyle='-.')
    if param == 'BMI':
      selected_param_plot.axhspan(25, 30, color='#FEFE62', alpha=0.5, lw=0, label='Overweight (25-30 BMI)')
      selected_param_plot.axhspan(30, 50, color='#D35FB7', alpha=0.5, lw=0, label='Obese (30-50 BMI)')
  selected_param_plot.legend(loc="upper left", bbox_to_anchor=(1.05, 1))
  plt.title(param)

  return selected_param_plot

def overlap_view_double(obs_df, subjid, show_all_measurements, show_excluded_values, show_trajectory_with_exclusions, include_carry_forward, include_percentiles, wt_df, ht_df):
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
  height = individual[individual.param == 'HEIGHTCM']
  weight = individual[individual.param == 'WEIGHTKG']
  filter = height.clean_value.isin(['Include', 'Exclude-Carried-Forward']) if include_carry_forward else height.clean_value == 'Include'
  filter_weight = weight.clean_value.isin(['Include', 'Exclude-Carried-Forward']) if include_carry_forward else weight.clean_value == 'Include'
  excluded_height = height[~filter]
  excluded_weight = weight[~filter_weight]
  included_height = height[filter]
  included_weight = weight[filter_weight]
  plt.rcParams['figure.figsize'] = [8, 10]
  fig, ax1 = plt.subplots()
  color = 'tab:red'
  color_secondary = 'tab:blue'
  ax1.set_ylim([50,180])
  ax1.set_xlim([20,65])
  ax1.set_xlabel('age (years)')
  ax1.set_ylabel('stature (cm)', color=color)

  ax2 = ax1.twinx()  # instantiate a second axes that shares the same x-axis

  ax2.set_ylim([40,160])
  ax2.set_ylabel('weight (kg)', color=color_secondary)  # we already handled the x-label with ax1
  if include_percentiles == True:
    percentile_window = wt_df.loc[wt_df.sex == individual.sex.min()]
    ax2.plot(percentile_window.age_years, percentile_window.P5, color='lightblue')
    ax2.plot(percentile_window.age_years, percentile_window.P10, color='lightblue', alpha=0.5)
    ax2.plot(percentile_window.age_years, percentile_window.P25, color='lightblue', alpha=0.5)
    ax2.plot(percentile_window.age_years, percentile_window.P50, color='lightblue')
    ax2.plot(percentile_window.age_years, percentile_window.P75, color='lightblue', alpha=0.5)
    ax2.plot(percentile_window.age_years, percentile_window.P90, color='lightblue', alpha=0.5)
    ax2.plot(percentile_window.age_years, percentile_window.P95, color='lightblue')
    percentile_window_ht = ht_df.loc[ht_df.sex == individual.sex.min()]
    ax1.plot(percentile_window_ht.age_years, percentile_window_ht.P5, color='pink')
    ax1.plot(percentile_window_ht.age_years, percentile_window_ht.P10, color='pink', alpha=0.5)
    ax1.plot(percentile_window_ht.age_years, percentile_window_ht.P25, color='pink', alpha=0.5)
    ax1.plot(percentile_window_ht.age_years, percentile_window_ht.P50, color='pink')
    ax1.plot(percentile_window_ht.age_years, percentile_window_ht.P75, color='pink', alpha=0.5)
    ax1.plot(percentile_window_ht.age_years, percentile_window_ht.P90, color='pink', alpha=0.5)
    ax1.plot(percentile_window_ht.age_years, percentile_window_ht.P95, color='pink')

  if show_all_measurements == True:
    ax1.plot(height['age'], height['measurement'], color=color, label='stature')
    ax2.plot(weight['age'], weight['measurement'], color=color_secondary, label='weight')

  if show_excluded_values == True:
    ax1.scatter(excluded_height.age, excluded_height.measurement, c='black', marker='x')
    ax2.scatter(excluded_weight.age, excluded_weight.measurement, c='black', marker='x')

  if show_trajectory_with_exclusions == True:
    ax1.plot(included_height['age'], included_height['measurement'], c='y', linestyle='-.')
    ax2.plot(included_weight['age'], included_weight['measurement'], c='y', linestyle='-.')

  ax1.tick_params(axis='y', labelcolor=color)
  ax2.tick_params(axis='y', labelcolor=color_secondary)

  fig.tight_layout()  # otherwise the right y-label is slightly clipped

  if include_carry_forward == True:
    carry_forward_height = height[height.clean_value == 'Exclude-Carried-Forward']
    carry_forward_weight = weight[weight.clean_value == 'Exclude-Carried-Forward']
    ax1.scatter(x=carry_forward_height.age, y=carry_forward_height.measurement, c='c', marker="^")
    ax2.scatter(x=carry_forward_weight.age, y=carry_forward_weight.measurement, c='c', marker="^")

  # Reset figsize to default
  plt.rcParams['figure.figsize'] = [6.4, 4.8]
  return fig

def five_by_five_view(obs_df, subjids, param, wt_df, ht_df, bmi_percentiles):
  """
  Creates a small multiples plot showing the growth trend for 25 individuals

  Parameters:
  obs_df: (DataFrame) with subjid, measurement, param and clean_value columns
  subjids: An list of the ids of the individuals to be plotted
  param: (String) Whether to plot heights or weights. Expected values are "HEIGHTCM" or "WEIGHTKG"
  """

  fig, ax = plt.subplots(5, 5)
  for y in range(5):
    for x in range(5):
      subjid = subjids[x + y*5]
      individual = obs_df[obs_df.subjid == subjid]
      selected_param = individual[individual.param == param]
      ax[x, y].plot(selected_param.age, selected_param.measurement, marker='.')
      excluded_selected_param = selected_param[selected_param.clean_value != 'Include']
      ax[x, y].scatter(excluded_selected_param.age, excluded_selected_param.measurement, c='r', marker='x')
      percentile_df = wt_df if param == 'WEIGHTKG' else ht_df
      percentile_window = percentile_df.loc[(percentile_df.sex == individual.sex.min()) &
                                            (percentile_df.age_years >= (individual.age_years.min() - 1)) &
                                            (percentile_df.age_years <= (individual.age_years.max() + 1))]
      ax[x, y].plot(percentile_window.age_years, percentile_window.P5, color='k')
      ax[x, y].plot(percentile_window.age_years, percentile_window.P95, color='k')
      ax[x, y].set(title=subjid)
  fig.set_size_inches(20, 12)
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
  percentile_window = bmi_percentiles.loc[(bmi_percentiles.sex == individual.sex.min()) &
                                          (bmi_percentiles.age_years > individual.age.min()) &
                                          (bmi_percentiles.age_years < individual.age.max())]
  ax[0].plot(individual.age, individual.bmi)
  ax[0].plot(percentile_window.age_years, percentile_window.P5, color='k')
  ax[0].plot(percentile_window.age_years, percentile_window.P95, color='k')

  ax[0].set(xlabel='age (y)', ylabel='BMI',
        title='BMI All Values')
  ax[0].grid()

  ax[1].plot(individual[individual.include_height & individual.include_weight].age, individual.loc[individual.include_height & individual.include_weight].bmi)
  ax[1].plot(percentile_window.age_years, percentile_window.P5, color='k')
  ax[1].plot(percentile_window.age_years, percentile_window.P95, color='k')

  ax[1].set(xlabel='age (y)', ylabel='BMI',
        title='BMI Cleaned')
  ax[1].grid()
  return plt

def top_ten(merged_df, field, age=None, sex=None, wexclusion=None, hexclusion=None, order='largest', out=None):
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
    working_set = working_set.loc[working_set.rounded_age.ge(age[0]) & working_set.rounded_age.le(age[1])]
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
  working_set = working_set.drop(columns=['agedays', 'include_height',
      'include_weight', 'include_both', 'rounded_age'])
  working_set['sex'] = working_set.sex.replace(0, 'M').replace(1, 'F')
  working_set['age'] = working_set.age.round(decimals=2)
  working_set['height'] = working_set.height.round(decimals=1)
  working_set['weight'] = working_set.weight.round(decimals=1)
  working_set['weight_cat'] = working_set.weight_cat.str.replace('Exclude-', '')
  working_set['height_cat'] = working_set.height_cat.str.replace('Exclude-', '')
  working_set = working_set[['subjid', 'sex', 'age', 'height', 'height_cat', 'htz',
    'weight', 'weight_cat', 'wtz', 'bmi', 'BMIz']]
  if out == None:
    return working_set
  else:
    out.clear_output()
    out.append_display_data(working_set)

def data_frame_names(da_locals):
  frames = []
  for key, value in da_locals.items():
    if isinstance(value, pd.DataFrame):
      frames.append(key)
  return frames

def export_to_csv(da_locals, selection_widget, out):
  df_name = selection_widget.value
  da_locals[df_name].to_csv('growthviz-data/output/{}.csv'.format(df_name), index=False)
  out.clear_output()
  out.append_display_data(FileLinks('growthviz-data/output'))

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
  merged_df['postprocess_height_cat'] = merged_df['height_cat']
  merged_df['postprocess_height_cat'] = merged_df['postprocess_height_cat'].cat.add_categories(['Include-Fixed-Swap'])
  merged_df['postprocess_weight_cat'] = merged_df['weight_cat']
  merged_df['postprocess_weight_cat'] = merged_df['postprocess_weight_cat'].cat.add_categories(['Include-Fixed-Swap'])
  merged_df.loc[merged_df['height_cat'] == 'Swapped-Measurements', ['height', 'weight']] = merged_df.loc[merged_df['height_cat'] == 'Swapped-Measurements', ['weight', 'height']].values
  merged_df.loc[merged_df['height_cat'] == 'Swapped-Measurements', 'postprocess_height_cat'] = 'Include-Fixed-Swap'
  merged_df.loc[merged_df['weight_cat'] == 'Swapped-Measurements', 'postprocess_weight_cat'] = 'Include-Fixed-Swap'
  merged_df['bmi'] = merged_df['weight'] / ((merged_df['height'] / 100) ** 2)
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
  merged_df['postprocess_height_cat'] = merged_df['height_cat']
  merged_df['postprocess_height_cat'] = merged_df['postprocess_height_cat'].cat.add_categories(['Include-UH','Include-UL'])
  merged_df['postprocess_weight_cat'] = merged_df['weight_cat']
  merged_df['postprocess_weight_cat'] = merged_df['postprocess_weight_cat'].cat.add_categories(['Include-UH','Include-UL'])
  merged_df.loc[merged_df['height_cat'] == 'Unit-Error-Low', 'height'] = (merged_df.loc[merged_df['height_cat'] == 'Unit-Error-Low', 'height'] * 2.54)
  merged_df.loc[merged_df['height_cat'] == 'Unit-Error-High', 'height'] = (merged_df.loc[merged_df['height_cat'] == 'Unit-Error-High', 'height'] / 2.54)
  merged_df.loc[merged_df['weight_cat'] == 'Unit-Error-Low', 'weight'] = (merged_df.loc[merged_df['weight_cat'] == 'Unit-Error-Low', 'weight'] * 2.2046)
  merged_df.loc[merged_df['weight_cat'] == 'Unit-Error-High', 'weight'] = (merged_df.loc[merged_df['weight_cat'] == 'Unit-Error-High', 'weight'] / 2.2046)
  merged_df.loc[merged_df['height_cat'] == 'Unit-Error-Low', 'postprocess_height_cat'] = 'Include-UL'
  merged_df.loc[merged_df['height_cat'] == 'Unit-Error-High', 'postprocess_height_cat'] = 'Include-UH'
  merged_df.loc[merged_df['weight_cat'] == 'Unit-Error-Low', 'postprocess_weight_cat'] = 'Include-UL'
  merged_df.loc[merged_df['weight_cat'] == 'Unit-Error-High', 'postprocess_weight_cat'] = 'Include-UH'
  merged_df['bmi'] = merged_df['weight'] / ((merged_df['height'] / 100) ** 2)
  return merged_df

def calculate_modified_weight_zscore(merged_df, wt_percentiles):
  """
  Adds a column to the provided DataFrame with the modified Z score for weight

  Parameters:
  merged_df: (DataFrame) with subjid, sex, weight and age columns
  wt_percentiles: (DataFrame) CDC weight growth chart DataFrame with L, M, S values

  Returns
  The dataframe with a new wtz column
  """
  return calculate_modified_zscore(merged_df, wt_percentiles, 'weight')

def cutoff_view(merged_df, subjid, cutoff, wt_df):
  individual = merged_df[merged_df.subjid == subjid]
  selected_param = individual[individual.include_weight == True]
  selected_param_plot = selected_param.plot.line(x='age', y='weight', marker='.', color='k')
  cutoffs = individual[np.absolute(individual.wtz) > cutoff]
  selected_param_plot.scatter(x=cutoffs.age,
                              y=cutoffs.weight, c='b', marker="o")
  # percentile_window = wt_df.loc[(wt_df.Sex == individual.sex.min()) &
  #                               (wt_df.age > individual.age.min()) &
  #                               (wt_df.age < individual.age.max())]
  # selected_param_plot.plot(percentile_window.age, percentile_window.P5, color='k')
  # selected_param_plot.plot(percentile_window.age, percentile_window.P95, color='k')
  return selected_param_plot

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
  grouped = combined_df.groupby(['run_name', 'clean_value']).agg({'id': 'count'}).reset_index().pivot(index='clean_value', columns='run_name', values='id')
  grouped = grouped.fillna(0)
  if grouped.columns.size == 2:
    grouped['diff'] = grouped[grouped.columns[1]] - grouped[grouped.columns[0]]
    grouped['tmp_sort'] = grouped['diff'].replace(0, np.NINF)
    grouped = grouped.sort_values('tmp_sort', ascending=False)
    grouped = grouped.drop(columns=['tmp_sort'])
  return grouped.style.format("{:.0f}")

def subject_comparison_category_counts(combined_df):
  """
  Provides a DataFrame that counts the number of subjects with at least one measurement in one of the
  growthcleanr categories, by run.

  Parameters:
  combined_df: A DataFrame in the format provided by prepare_for_comparison

  Returns:
  A DataFrame where the categories are the index and the columns are the run names.
  """
  grouped = combined_df.groupby(['run_name', 'clean_value']).agg({'subjid': 'nunique'}).reset_index().pivot(index='clean_value', columns='run_name', values='subjid')
  grouped = grouped.fillna(0)
  if grouped.columns.size == 2:
    grouped['diff'] = grouped[grouped.columns[1]] - grouped[grouped.columns[0]]
    grouped['population percent change'] = ((grouped[grouped.columns[1]] - grouped[grouped.columns[0]]) / grouped[grouped.columns[1]].sum()) * 100
    grouped['tmp_sort'] = grouped['diff'].replace(0, np.NINF)
    grouped = grouped.sort_values('tmp_sort', ascending=False)
    grouped = grouped.drop(columns=['tmp_sort'])
    grouped = grouped.style.format({grouped.columns[0]: "{:.0f}", grouped.columns[1]: "{:.0f}",
                                    'diff': "{:.0f}", 'population percent change': "{:.2f}%"})
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
  grouped = combined_df.groupby(['run_name', 'clean_value']).agg({'subjid': 'nunique'}).reset_index().pivot(index='clean_value', columns='run_name', values='subjid')
  grouped = grouped.fillna(0)
  for c in grouped.columns:
    grouped[c] = (grouped[c] / combined_df[combined_df.run_name == c].subjid.nunique()) * 100
  if grouped.columns.size == 2:
    grouped['diff'] = grouped[grouped.columns[1]] - grouped[grouped.columns[0]]
    grouped['tmp_sort'] = grouped['diff'].replace(0, np.NINF)
    grouped = grouped.sort_values('tmp_sort', ascending=False)
    grouped = grouped.drop(columns=['tmp_sort'])
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
    only_exclusions = combined_df[(combined_df.run_name == rn) & (combined_df.include == False)]
    percent_with_exclusion = (only_exclusions.subjid.nunique() / total_subjects) * 100
    exclusion_per = only_exclusions.shape[0] / total_subjects
    stats.append({'run name': rn, 'percent with exclusion': percent_with_exclusion, 'exclusions per patient': exclusion_per})
  return pd.DataFrame.from_records(stats, index='run name')

def exclusion_information(obs):
  """
  Provides a count and percentage of growthcleanr categories by measurement type (param).

  Parameters:
  obs: a DataFrame, in the format output by setup_individual_obs_df

  Returns:
  A DataFrame with the counts and percentages
  """
  exc = obs.groupby(['param', 'clean_cat']).agg({'id': 'count'}).reset_index().pivot(index="clean_cat", columns='param', values='id')
  exc['height percent'] = exc['HEIGHTCM'] / exc['HEIGHTCM'].sum() * 100
  exc['weight percent'] = exc['WEIGHTKG'] / exc['WEIGHTKG'].sum() * 100
  exc = exc.fillna(0)
  exc['total'] = exc['HEIGHTCM'] + exc['WEIGHTKG']
  exc = exc[['HEIGHTCM', 'height percent', 'WEIGHTKG', 'weight percent', 'total']]
  exc = exc.sort_values('total', ascending=False)
  return exc.style.format({'HEIGHTCM': "{:.0f}".format, 'height percent': "{:.2f}%",
                           'WEIGHTKG': "{:.0f}".format, 'weight percent': "{:.2f}%"})

def calculate_modified_zscore(merged_df, percentiles, category):
  """
  Adds a column to the provided DataFrame with the modified Z score for the provided category

  Parameters:
  merged_df: (DataFrame) with subjid, sex, weight and age columns
  percentiles: (DataFrame) CDC growth chart DataFrame with L, M, S values for the desired category

  Returns
  The dataframe with a new zscore column mapped with the z_column_name list
  """
  pct_cpy = percentiles.copy()
  pct_cpy['half_of_two_z_scores'] = (pct_cpy['M'] * np.power((1 + pct_cpy['L'] * pct_cpy['S'] * 2), (1 / pct_cpy['L']))) - pct_cpy['M']
  # Calculate an age in months by rounding and then adding 0.5 to have values that match the growth chart
  merged_df['agemos'] = np.around(merged_df['age'] * 12) + 0.5
  mswpt = merged_df.merge(pct_cpy[['Agemos', 'M', 'Sex', 'half_of_two_z_scores']], how='left', left_on=['sex', 'agemos'], right_on=['Sex', 'Agemos'])
  z_column_name = {
   'weight': 'wtz',
   'height': 'htz',
   'bmi': 'BMIz'
  }
  mswpt[z_column_name[category]] = (mswpt[category] - mswpt['M']) / mswpt['half_of_two_z_scores']
  return mswpt.drop(columns=['Agemos', 'Sex', 'M', 'half_of_two_z_scores'])
