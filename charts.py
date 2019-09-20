import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from IPython.display import FileLink, FileLinks

def setup_individual_obs_df(obs_df):
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
  # Values by CDC (1=male; 2=female) differ from growthcleanr
  # which uses a numeric value of 0 (male) or 1 (female).
  # This aligns things to the growthcleanr values
  percentiles['Sex'] = percentiles['Sex']  - 1
  return percentiles

def setup_merged_df(obs_df):
  obs_df['height'] = np.where(obs_df['param'] == 'HEIGHTCM', obs_df['measurement'], np.NaN)
  obs_df['weight'] = np.where(obs_df['param'] == 'WEIGHTKG', obs_df['measurement'], np.NaN)
  heights = obs_df[obs_df.param == 'HEIGHTCM']
  weights = obs_df[obs_df.param == 'WEIGHTKG']
  merged = heights.merge(weights, on=['subjid', 'agedays', 'sex'], how='outer')
  only_needed_columns = merged.drop(columns=['param_x', 'measurement_x', 'clean_value_x',
                                             'age_x', 'weight_x', 'id_y', 'param_y',
                                             'measurement_y', 'clean_value_y', 'height_y'])
  clean_column_names = only_needed_columns.rename(columns={'clean_cat_x': 'height_cat',
                                                           'include_x': 'include_height',
                                                           'height_x': 'height',
                                                           'clean_cat_y': 'weight_cat',
                                                           'age_y': 'age',
                                                           'include_y': 'include_weight',
                                                           'weight_y': 'weight'})
  clean_column_names['bmi'] = clean_column_names['weight'] / ((clean_column_names['height'] / 100) ** 2)
  clean_column_names['rounded_age'] = np.around(clean_column_names.age)
  clean_column_names['include_both'] = clean_column_names['include_height'] & clean_column_names['include_weight']
  return clean_column_names

def bmi_stats(merged_df, out=None, include_min=True, include_mean=True, include_max=True,
              include_std=True, include_median=True, include_mean_diff=True,
              include_count=True, age_range=[2, 20]):
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
  include_median: (Boolean) Whether to include the median value column
  include_mean_diff: (Boolean) Whether to include the difference between the raw and
                     clean mean value column
  include_count: (Boolean) Whether to include the count column
  age_range (List) Two elements containing the minimum and maximum ages that should be
            included in the statistics

  Returns:
  If out is None, it will return a DataFrame. If out is provided, results will be displayed
  in the notebook.
  """
  agg_functions = []
  if include_min:
    agg_functions.append('min')
  if include_mean:
    agg_functions.append('mean')
  if include_max:
    agg_functions.append('max')
  if include_std:
    agg_functions.append('std')
  if include_median:
    agg_functions.append('median')
  if include_count:
    agg_functions.append('count')
  clean_groups = merged_df[merged_df.include_both].groupby(['rounded_age',
                                                            'sex'])['bmi'].agg(agg_functions)
  raw_groups = merged_df.groupby(['rounded_age', 'sex'])['bmi'].agg(agg_functions)
  merged_stats = clean_groups.merge(raw_groups, on=['rounded_age', 'sex'], suffixes=('_clean', '_raw'))
  if include_mean & include_mean_diff:
    merged_stats['mean_diff'] = merged_stats['mean_raw'] - merged_stats['mean_clean']
  age_filtered = merged_stats.loc[(age_range[0]):(age_range[1])]
  if out == None:
    return age_filtered
  else:
    out.clear_output()
    out.append_display_data(age_filtered.style.format("{:.2f}"))

def overlap_view(obs_df, subjid, param, include_carry_forward, include_percentiles, wt_df, ht_df):
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
    percentile_df = wt_df if param == 'WEIGHTKG' else ht_df
    percentile_window = percentile_df.loc[(percentile_df.Sex == individual.sex.min()) &
                                          (percentile_df.age > individual.age.min()) &
                                          (percentile_df.age < individual.age.max())]
    selected_param_plot.plot(percentile_window.age, percentile_window.P5, color='k')
    selected_param_plot.plot(percentile_window.age, percentile_window.P95, color='k')
  return selected_param_plot

def five_by_five_view(obs_df, subjids, param):
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
      ax[x, y].set(title=subjid)
  fig.set_size_inches(20, 12)
  return plt

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
  percentile_window = bmi_percentiles.loc[(bmi_percentiles.Sex == individual.sex.min()) &
                                          (bmi_percentiles.age > individual.age.min()) &
                                          (bmi_percentiles.age < individual.age.max())]
  ax[0].plot(individual.age, individual.bmi)
  ax[0].plot(percentile_window.age, percentile_window.P5, color='k')
  ax[0].plot(percentile_window.age, percentile_window.P95, color='k')

  ax[0].set(xlabel='age (y)', ylabel='BMI',
        title='BMI All Values')
  ax[0].grid()

  ax[1].plot(individual[individual.include_height & individual.include_weight].age, individual.loc[individual.include_height & individual.include_weight].bmi)
  ax[1].plot(percentile_window.age, percentile_window.P5, color='k')
  ax[1].plot(percentile_window.age, percentile_window.P95, color='k')

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
  if order == 'largest':
    working_set = working_set.nlargest(10, field)
  else:
    working_set = working_set.nsmallest(10, field)
  if out == None:
    return working_set
  else:
    out.clear_output()
    out.append_display_data(working_set.drop(columns=['id_x', 'agedays', 'include_height', 'include_weight', 'include_both']))

def data_frame_names(da_locals):
  frames = []
  for key, value in da_locals.items():
    if isinstance(value, pd.DataFrame):
      frames.append(key)
  return frames

def export_to_csv(da_locals, selection_widget, out):
  df_name = selection_widget.value
  da_locals[df_name].to_csv('output/{}.csv'.format(df_name), index=False)
  out.clear_output()
  out.append_display_data(FileLinks('output'))