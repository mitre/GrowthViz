#!/usr/bin/env python
# coding: utf-8

# # GrowthViz - Pediatrics
# 
# ## Background - growthcleanr
# 
# [growthcleanr](https://github.com/carriedaymont/growthcleanr) is an automated method for identifying implausible values in anthropometric data from EHRs. It is available as open source software. It was originally designed with a focus on pediatric growth data, as stated in [Automated identification of implausible values in growth data from pediatric electronic health records](https://academic.oup.com/jamia/article/24/6/1080/3767271):
# 
# > In pediatrics, evaluation of growth is fundamental, and many pediatric research studies include some aspect of growth as an outcome or other variable. The clinical growth measurements obtained in day-to-day care are susceptible to error beyond the imprecision inherent in any anthropometric measurement. Some errors result from minor problems with measurement technique. While these errors can be important in certain analyses, they are often small and generally impossible to detect after measurements are recorded. Larger measurement technique errors can result in values that are biologically implausible and can cause problems for many analyses. 
# 
# This notebook supports review of `growthcleanr` results when working with data from **pediatric** subjects. The `growthcleanr` package has been expanded to identify implausible height and weight observations among adult subjects, from 18 up to age 65. If you are primarily working with adult subjects, please use the `GrowthViz-adults.ipynb` notebook instead.
# 
# ## GrowthViz Purpose
# 
# The objective of this tool is to allow users to conduct post-processing and data visualization of growthcleanr output. GrowthViz is to be used **after** a data set has been run through growthcleanr.
# 
# GrowthViz is a [Juypter Notebook](https://jupyter.org/). It provides an environment that includes graphical user interfaces as well as interactive software development to explore data. To achieve this, GrowthViz references different software languages and packages:
#  - [Python programming language](https://www.python.org/) is used to import, transform, visualize and analyze the output of growthcleanr. Some of the code for the tool is directly included in this notebook. Other functions have been placed in external files to minimize the amount of code that users see in order to let them focus on the actual data.
#  - Data analysis is performed using [NumPy](https://numpy.org/) and [Pandas](https://pandas.pydata.org/). The output of growthcleanr will be loaded into a [pandas DataFrame](https://pandas.pydata.org/pandas-docs/stable/reference/api/pandas.DataFrame.html). GrowthViz provides functions for transforming DataFrames to support calculation of some values, such as BMI, as well as supporting visualizations. It is expected that users will create views into or copies of the DataFrames built initially by this tool. Adding columns to the DataFrames created by this tool is unlikely to cause problems. Removing columns is likely to break some of the tool's functionality.
#  - Visualization in the tool is provided by [Matplotlib](https://matplotlib.org/) and [Seaborn](http://seaborn.pydata.org/). Users may generate their own charts with these utilities.
# 
# ---
# # Setting Up the Environment
# 
# Jupyter Notebooks have documentation cells, such as this one, and code cells like the one below. The notebook server runs the code and provides results (if applicable) back in the notebook. The following code cell loads the libraries necessary for the tool to work. If you would like to incorporate other Python libraries to assist in data exploration, they can be added here. Removing libraries from this cell will very likely break the tool.

# In[1]:


import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import seaborn as sns

from ipywidgets import interact, interactive, fixed, interact_manual
import ipywidgets as widgets
from IPython.display import FileLink, FileLinks
import qgrid


# The next two code cells tell the notebook server to automatically reload the externally defined Python functions created to assist in data analysis.

# In[2]:


get_ipython().run_line_magic('load_ext', 'autoreload')


# In[3]:


get_ipython().run_line_magic('autoreload', '2')


# This code cell instructs the notebook to automatically display plots inline.

# In[4]:


get_ipython().run_line_magic('matplotlib', 'inline')


# This code cell tells the notebook to output plots for high DPI displays, such as 4K monitors, many smartphones or a retina display on Apple hardware. This cell does not need to be run and can be safely removed. If removed, charts will look more "blocky" or "pixelated" on high DPI displays.

# In[5]:


get_ipython().run_line_magic('config', "InlineBackend.figure_format = 'retina'")


# # Loading Data
# 
# The following cell imports functions created for the tool to assist in data analysis. Some of the functions generate charts used in this tool. The chart code may be modified to change the appearance of plots without too much risk of breaking things. Other functions transform DataFrames and changing those will very likely cause things to break. If you are unable to tell the difference in the functions by looking at the code, it is probably best to leave them unmodified.

# In[6]:


from growthviz import charts
from growthviz import check_data
from growthviz import compare
from growthviz import processdata
from growthviz import sumstats


# This cell reads in a data set that has been run through the [growthcleanr](https://github.com/carriedaymont/growthcleanr) algorithm. Details of the algorithm can be found in [Automated identification of implausible values in growth data from pediatric electronic health records](https://academic.oup.com/jamia/article/24/6/1080/3767271)
# 
# <a id="input_structure"></a>
# Data is expected to be in a CSV file with the following structure:
# 
# | Column | Description |
# |--------|-------------|
# | id | A unique identifier for an observation |
# | subjid | An identifier for the individual from which the observation was obtained |
# | sex | A numeric value of 0 (male) or 1 (female). Note that this differs from the CDC Growth Chart Data Tables. |
# | agedays | Number representing the age of the patient in days when the observation was obtained |
# | param | The type of observation along with units. Expected values are *HEIGHTCM* and *WEIGHTKG* |
# | measurement | A decimal number that represents the observation value. |
# | clean_res | The categorization of the observation by growthcleanr. |
# 
# This information will be loaded into a [pandas DataFrame](https://pandas.pydata.org/pandas-docs/stable/reference/api/pandas.DataFrame.html) called `cleaned_obs`

# In[7]:


cleaned_obs = pd.read_csv("growthviz-data/sample-pediatrics-data.csv")


# The following cell shows what the first five rows look like in the CSV file

# In[8]:


cleaned_obs.head()


# This next cell runs through a series of data checks on the original data file, such as making sure all values of `sex` are either 0 or 1, or no age values are negative.

# In[9]:


warnings = check_data.check_patient_data("growthviz-data/sample-pediatrics-data.csv")
if warnings:
    for warning in warnings:
        print(warning)
else:
    print("Data looks good!")


# Next, the `processdata.setup_individual_obs_df` function performs transformations on the `cleaned_obs` DataFrame. This will create an `age` column, which is a decimal column that represents the patient's age in years at the time of the observation. It changes the `clean_value` column into a [pandas categorical type](https://pandas.pydata.org/pandas-docs/stable/user_guide/categorical.html). It also create an `include` column which contains a boolean value indicating whether growthcleanr states to include (true) or exclude (false) the observation. The resulting DataFrame is assigned to `obs_full`.

# In[10]:


obs_full = processdata.setup_individual_obs_df(cleaned_obs)


# In[11]:


obs_full.head()


# In the following cell, the `charts.make_age_charts` function visually displays the range of ages in the dataset, with those to be excluded identified by the red bars with the **x** pattern, and those that are outside the optimal range of the notebook identified by the orange bars with the **/** pattern. As noted above, if the population in the dataset is primarily adults, you will want to switch to the adults notebook.

# In[12]:


charts.make_age_charts(obs_full, 'pediatrics')


# The chart above shows pediatric age ranges supported by the rest of this notebook, any observations that fall outside of those ranges.
# 
# Now, we will filter the age ranges to match the supported pediatric ranges.

# In[13]:


obs = processdata.keep_age_range(obs_full, 'pediatrics')


# In[14]:


obs.head()


# After that, `charts.weight_distr` creates two visualizations. The first shows a distribution of all of the included weights in the dataset. The second shows weights above a certain threshold to see whether there are spikes at a certain *Included* weights that might indicate that a commonly used scale maxes out at a certain value. This chart is restricted to values of 135kg or higher (rounded to the nearest KG) to make patterns in higher weights easier to identify. This potential issue is important to keep in mind when conducting an analysis.

# In[15]:


charts.weight_distr(obs, 'all')


# In[16]:


charts.weight_distr(obs, 'high')


# The following cell loads in the [CDC Growth Chart Percentile Data Files](https://www.cdc.gov/growthcharts/percentile_data_files.htm). Functions coerce some values into numeric types. It also add an `age` column which is a decimal value representing age in years. Finally, `Sex` is transformed so that the values align with the values used in growthcleanr, 0 (male) or 1 (female). This data is used to plot percentile bands in visualizations in the tool. 

# In[17]:


bmi_percentiles = processdata.setup_percentiles_pediatrics("bmiagerev.csv")
wt_percentiles = processdata.setup_percentiles_pediatrics("wtage.csv")
ht_percentiles = processdata.setup_percentiles_pediatrics("statage.csv")


# In a previous cell, the tool creates the `obs` DataFrame. In that structure there is one measurement, either height or weight, per row. In this cell, the `processdata.setup_merged_df` function will create a DataFrame where a height observation and weight observation for the same `subjid` on the same `agedays` are combined into a single row. Several new columns are added to the resulting DataFrame:
# 
# | Column | Description |
# |--------|-------------|
# | weight | The `measurement` value for observations that had the `param` of *WEIGHTKG* |
# | height | The `measurement` value for observations that had the `param` of *HEIGHTCM* |
# | bmi | The BMI calculated from `weight` and `height` |
# | weight_cat | The value previously stored in `clean_value` for the weight observation |
# | include_weight | The value previously stored in `include` for the weight observation |
# | height_cat | The value previously stored in `clean_value` for the height observation |
# | include_height | The value previously stored in `include` for the height observation |
# | include_both | Logical AND of `include_weight` and `include_height` |
# 
# The result is stored in `merged_df`.

# In[18]:


merged_df = processdata.setup_merged_df(obs)
merged_df.head()


# ## Exclusion Information
# 
# The following shows the counts of the values for inclusion/exclusion along with the percentages of total.

# In[19]:


processdata.exclusion_information(obs)


# # Finding Individuals
# 
# This next cell creates interactive tool can be used to explore patients. The `sumstats.add_mzscored_to_merged_df` function will add modified Z Scores for height, weight and BMI to `merged_df`. The tool uses [Qgrid](https://github.com/quantopian/qgrid) to create the interactive table. Clicking on a row will create a plot for the individual below the table.

# In[20]:


mdf = sumstats.add_mzscored_to_merged_df_pediatrics(merged_df, wt_percentiles, ht_percentiles, bmi_percentiles)
col_opt = {
    'width': 20,
}
col_def = {
    'subjid': { 'width': 80 },
    'sex': { 'width': 30 },
    'age': { 'width': 30 },
    'height': { 'width': 50 },
    'height_cat': { 'width': 80 },
    'htz': { 'width': 50 },
    'weight': { 'width': 50 },
    'weight_cat': { 'width': 80 },
    'wtz': { 'width': 50 },
    'bmi': { 'width': 40 },
    'BMIz': { 'width': 30 },
}
g = qgrid.show_grid(charts.top_ten(mdf, 'weight'), precision=3, column_options=col_opt, column_definitions=col_def)
ind_out = widgets.Output()
def handle_selection_change(_event, _widget):
    sdf = g.get_selected_df()
    ind_out.clear_output()
    if sdf.shape[0] >= 1:
        subjid = sdf.subjid.iloc[0]
        with ind_out:
            charts.overlap_view_pediatrics(obs, subjid, 'WEIGHTKG', True, True, wt_percentiles, ht_percentiles)
            display(plt.show())
g.on('selection_changed', handle_selection_change)    
widgets.VBox([g, ind_out])


# It can be useful to copy values from the `subjid` column in the results above for use in visualizations in the rest of the tool.
# 
# ---
# 
# # Visualizing an Individual Trajectory
# 
# The cell below creates a plot for an individual. It shows either the weight trajectory or height tragectory depending on the `param` value that is selected. The black bands in the diagram represent the 5th and 95th percentile values for age and sex for the given measurement type.
# 
# In this chart, the blue line represents all measurements for an individual. Any values marked for exclusion are represented with a red x. The yellow dashed line represents the trajectory with exclusions removed. Any carried forward values are represented by a blue triangle, unless `include_carry_forward` is set to False, when they will also be represented as a red x.

# In[21]:


all_ids = obs['subjid'].unique()
val = 5450 if 5450 in all_ids else np.random.choice(all_ids, size=1, replace=False)
interactive(charts.overlap_view_pediatrics_show, 
            obs_df=fixed(obs), 
            subjid=widgets.Dropdown(options=all_ids, value=val, description='Subject ID:', disabled=False), 
            param=['HEIGHTCM', 'WEIGHTKG'], 
            include_carry_forward=widgets.Checkbox(value=True,description='Include Carry Forward',disabled=False,indent=False), 
            include_percentiles=widgets.Checkbox(value=True,description='Include Measurement Percentile Bands',disabled=False,indent=False),
            wt_df=fixed(wt_percentiles), 
            ht_df=fixed(ht_percentiles), 
            bmi_df=fixed(bmi_percentiles)
           )


# The cell below also creates a plot for an individual modeled after the [CDC paper growth charts](https://www.cdc.gov/growthcharts/data/set1clinical/cj41c021.pdf). It shows both the weight trajectory and height trajectory. The lighter bands in the diagram background represent the 5th through 95th percentile values for age and sex for the given measurement type.
# 
# In this chart, the dark blue line represents all weight measurements for an individual and the dark red represents all height measurements for an individual. Any values marked for exclusion are represented with a black x. The yellow dashed line represents the trajectory with exclusions removed. Any carried forward values are represented by a blue triangle. All lines and symbols can be excluded by unchecking the checkboxes above the chart.

# In[22]:


all_ids = obs['subjid'].unique()
val = 5446 if 5446 in all_ids else np.random.choice(all_ids, size=1, replace=False)
interactive(charts.overlap_view_double_pediatrics, 
            obs_df=fixed(obs), 
            subjid=widgets.Dropdown(options=all_ids, value=val, description='Subject ID:', disabled=False),
            show_all_measurements=widgets.Checkbox(value=True,description='Show All Measurements',disabled=False,indent=False),
            show_excluded_values=widgets.Checkbox(value=True,description='Show Excluded Values (x)',disabled=False,indent=False),
            show_trajectory_with_exclusions=widgets.Checkbox(value=True,description='Show Trajectory with Exclusions',disabled=False,indent=False),
            include_carry_forward=widgets.Checkbox(value=True,description='Include Carry Forward',disabled=False,indent=False), 
            include_percentiles=widgets.Checkbox(value=True,description='Include Measurement Percentile Bands',disabled=False,indent=False),
            wt_df=fixed(wt_percentiles), ht_df=fixed(ht_percentiles))


# # Visualizing Multiple Trajectories at Once
# 
# Next, the tool creates a series that contains the unique set of `subjid`s and stores that in `uniq_ids`.

# In[23]:


uniq_ids = obs['subjid'].unique()


# From the series of unique subjids, the following cell randomly selects 25 individuals and assigns them to `sample`. A random seed, which specifies the start point when a computer generates a random number sequence, is then set so that the random sample is reproducible. The random seed can be changed to change the sample generated.

# In[24]:


np.random.seed(1)
sample = np.random.choice(uniq_ids, size=25, replace=False)


# In[25]:


sample


# The `sample` can be passed into the `charts.five_by_five_view` function which will create a [small multiple](https://en.wikipedia.org/wiki/Small_multiple) plot for each of the individuals. Exclusions, including carry forwards, will be represented by a red x.

# In[26]:


charts.five_by_five_view(obs, sample, 'HEIGHTCM', wt_percentiles, ht_percentiles, bmi_percentiles, 'solid')


# # Building a Different Sample
# 
# This tool can be used to create samples that are tailored to specific interests. Views can easily be created on existing DataFrames and be used to generate different samples. Functionality available is described in the [Pandas DataFrame documentation](https://pandas.pydata.org/pandas-docs/stable/reference/frame.html).
# 
# The cell below selects all observations with a weight exclusion of "Exclude-EWMA-Extreme". It then sorts by weight in descending order. The code then takes the top 50 values and selects 25 random, unique `subjids` from that set. Finally it plots the results. If there are fewer than 25 examples, but at least one, each example is shown. 

# In[27]:


top_weight_extreme_ewma_ids = merged_df[merged_df.weight_cat == 'Exclude-EWMA-Extreme'].sort_values('weight', ascending=False).head(50)['subjid'].unique()
if len(top_weight_extreme_ewma_ids) >= 1:
    ewma_sample = np.random.choice(top_weight_extreme_ewma_ids, size=len(top_weight_extreme_ewma_ids), replace=False)
    charts.five_by_five_view(obs, ewma_sample, 'WEIGHTKG', wt_percentiles, ht_percentiles, bmi_percentiles, 'solid')


# ## Visualizing the Top/Bottom 25 for a Given Category
# 
# The following cell uses the same function as above to create a 5 x 5 set of small multiple charts, but selects the top/bottom 25 individuals by growthcleanr category.

# In[28]:


def edge25(obs, category, sort_order, param):
    filtered_by_cat = obs[(obs.clean_cat == category) & (obs.param == param)]
    if sort_order == 'largest':
        filtered_by_cat = filtered_by_cat.nlargest(25, 'measurement')
    else:
        filtered_by_cat = filtered_by_cat.nsmallest(25, 'measurement')
    fig = charts.five_by_five_view(obs, filtered_by_cat.subjid.values, param, wt_percentiles, ht_percentiles, bmi_percentiles, 'solid')
    plt.show()
    
interact(edge25, obs = fixed(obs), category = obs.clean_cat.unique(), 
         sort_order = ['largest', 'smallest'], param = ['WEIGHTKG', 'HEIGHTCM'])


# # Visualizing Changes in Trajectory
# 
# The `charts.bmi_with_percentiles` function displays a chart showing BMI for an individual over time. Black bands representing the 5th and 95th BMI percentile for age and sex are shown with the individual's BMI shown in blue. The plot on the left represents all values. The plot on the right is only included values.

# In[29]:


all_ids = obs['subjid'].unique()
val = 46717134 if 46717134 in all_ids else np.random.choice(all_ids, size=1, replace=False)
interact(charts.bmi_with_percentiles, merged_df = fixed(merged_df), 
                                      bmi_percentiles = fixed(bmi_percentiles),
                                      subjid = widgets.BoundedIntText(value=val,
                                                                      min=0,
                                                                      max=10000000000,
                                                                      description='Subject ID:',
                                                                      disabled=False
))


# # Summary Statistics
# 
# The next cell generates summary statistics for the data set. The `sumstats.bmi_stats` function uses the `merged_df` DataFrame to compute values on the "clean" data, which means only included values as well as the "raw" values, which is all values for individuals.
# 
# | Column Name | Definition |
# |--------|-------------|
# | min_clean | Minimum Clean BMI Value |
# | mean_clean | Average Clean BMI Value |
# | max_clean | Maximum Clean BMI Value |
# | sd_clean | Standard Deviation of Clean BMI Values |
# | count_clean | Count of Patient Records with Clean BMI Values |
# | min_raw | Minimum Raw BMI Value |
# | mean_raw | Average Raw BMI Value |
# | max_raw | Maximum Raw BMI Value |
# | sd_raw | Standard Deviation of Raw BMI Values |
# | count_raw | Count of All Patient Records |
# | count_diff | Count of Patient Records with Excluded BMI Values |
# 
# The buttons can be used to add or remove columns from the table (all columns are shown by default - clicking a button will remove that column from the table).
# The checkbox includes "missing" values (note: this will impact the raw columns as missing values may cause BMI values of infinity since they divide by 0 when missing). Missing values are not included by default.

# In[30]:


min_toggle = widgets.ToggleButton(value=True, description='Minimum BMI', 
                                  tooltip="Click to hide or show the minimum BMI columns")
mean_toggle = widgets.ToggleButton(value=True, description='Mean BMI', 
                                   tooltip="Click to hide or show the mean BMI columns")
max_toggle = widgets.ToggleButton(value=True, description='Maximum BMI', 
                                  tooltip="Click to hide or show the maximum BMI columns")
std_toggle = widgets.ToggleButton(value=True, description='BMI Standard Deviation',
                                  tooltip="Click to hide or show the BMI standard deviation columns")
count_toggle = widgets.ToggleButton(value=True, description='Count',
                                    tooltip="Click to hide or show the count columns")
diff_toggle = widgets.ToggleButton(value=True, description='Count Difference',
                                   tooltip="Click to hide or show the count difference column")
age_range = widgets.IntRangeSlider(value=[0, 20], min=0, max=20, step=1, description='Age:', continuous_update=False,
                                   orientation='horizontal', readout=True, readout_format='d')
include_missing_values = widgets.Checkbox(value=False,description='Include Missing / Zero Heights and Weights',disabled=False,indent=False)
hbox = widgets.HBox([min_toggle, mean_toggle, max_toggle, std_toggle, count_toggle, diff_toggle])
ui = widgets.VBox([age_range, hbox, include_missing_values])
sum_out = widgets.Output()
widgets.interactive_output(sumstats.bmi_stats, {'merged_df': fixed(merged_df), 'include_min': min_toggle, 
         'include_mean': mean_toggle, 'include_max': max_toggle, 'include_std': std_toggle, 
         'include_mean_diff': diff_toggle, 'include_count': count_toggle,
         'out': fixed(sum_out), 'age_range': age_range, 'include_missing': include_missing_values})
display(ui, sum_out)


# # Exporting Data
# 
# The following code allows you to export a DataFrame as a CSV file. When the cell below is run, the drop down will contain all DataFrames stored in variables in this notebook. Select the desired DataFrame and click Generate CSV. This will create the CSV file and provide a link to download it.
# 
# | DataFrame | Description |
# |--------|-------------|
# | cleaned_obs | Original growthcleanr output read in from csv file |
# | obs_full | Slightly modified version of `cleaned_obs` in format needed for use in notebook |
# | obs | Patient observations within age range allowed for this notebook (18-80) |
# | bmi_percentiles | BMI percentiles data for use in charts |
# | wt_percentiles | Weight percentiles data for use in charts |
# | ht_percentiles | Height percentiles data for use in charts |
# | merged_df | Data by subject and age that contains height, weight, and BMI on one row |
# | mdf | Version of `merged_df` with added z-scores |

# In[31]:


df_selector = widgets.Dropdown(options=processdata.data_frame_names(locals()), description='Data Frames')
generate_button = widgets.Button(description='Generate CSV')
ui = widgets.VBox([df_selector, generate_button])
csv_out = widgets.Output()

l = locals()
def on_button_clicked(b):
    processdata.export_to_csv(l, df_selector, csv_out)

generate_button.on_click(on_button_clicked)
    
display(ui, csv_out)


# # Post Processing Data
# 
# This tool provides functions that allow the post processing of data. `processdata.clean_swapped_values` will look in a DataFrame for rows where the `height_cat` and `weight_cat` are set to "Swapped-Measurements". It will then swap the `height` and `weight` values for those rows. It will also create two new columns: `postprocess_height_cat` and `postprocess_weight_cat`. The values for these columns is copied from the original categories except in the case where swaps are fixed when it is set to "Include-Fixed-Swap".
# 
# `processdata.clean_unit_errors` will look in a data frame for rows where the `height_cat` and `weight_cat` are set to "Unit-Error-High". It will divide or multiply the value to convert it to metric.
# 
# The cell below copies the merged DataFrame and then cleans the swapped values.

# In[32]:


cleaned = merged_df.copy()
cleaned = processdata.clean_swapped_values(cleaned)
cleaned[cleaned.height_cat == 'Swapped-Measurements'].head()


# The cell below copies the merged DataFrame and then cleans the unit errors. Note: To see results in the table below with the example data you may need to swap "clean_with_swaps.csv" for "clean_with_uswaps.csv" and rerun the cells in the "Loading Data" section above. The default example set has swaps but not unit errors.

# In[33]:


cleaned = merged_df.copy()
cleaned = processdata.clean_unit_errors(cleaned)
cleaned[cleaned.height_cat == 'Unit-Error-High'].head()


# # Developing New Visualizations
# 
# Users may take advantage of the predefined `sumstats.bmi_stats`, `charts.bmi_with_percentiles`, `charts.five_by_five_view`, `charts.overlap_view_pediatrics` and `charts.top_ten` functions. For more information on these functions, execute the function name ending with a "?", which will bring up the inline help window. For example, `charts.five_by_five_view`

# In[34]:


get_ipython().run_line_magic('pinfo', 'sumstats.bmi_stats')


# In addition, users can take advantage of all of the plotting capabilities of [Matplotlib](https://matplotlib.org/3.1.1/tutorials/index.html) and [Seaborn](https://seaborn.pydata.org/tutorial.html)

# ## Comparing different runs of growthcleanr
# 
# This tool contains code to compare different runs of growthcleanr. The following code will load two separate runs of growthcleanr. The first is a data set that includes the data used above, but with additional subjects that have swapped measurements. The second run looks at the same data, but turns on growthcleanr's ability to detect unit errors.

# In[35]:


cws = pd.read_csv("growthviz-data/sample-data-cleaned.csv")
cws = processdata.setup_individual_obs_df(cws)
cwus = pd.read_csv("growthviz-data/sample-data-cleaned-with-ue.csv")
cwus = processdata.setup_individual_obs_df(cwus)


# The next cell uses the `prepare_for_comparison` function to combine the two loaded and prepared DataFrames into a single DataFrame that tags the rows with the name of the run.

# In[36]:


combined = compare.prepare_for_comparison({'default': cws, 'unit errors': cwus})


# With this `combined` DataFrame, several functions are available to display differences between the runs. `category_counts` shows the raw number of measurements for each category. It also shows the difference between the runs and percentage change in the number of raw measurements. This function and other comparison functions can be used with more than two separate runs. In these cases, the functions will not compute difference or percentage change.

# In[37]:


compare.count_comparison(combined)


# The following cell uses the `subject_comparison_category_counts` to display the count of subjects who have a measurement with at least one of the measurement categories.

# In[38]:


compare.subject_comparison_category_counts(combined)


# The following cell uses `subject_comparison_percentage` to show a percentage of subjects who have at least one measurement in the category

# In[39]:


compare.subject_comparison_percentage(combined)


# ## Looking at exclusion prevalence between data sets
# 
# The following visualizations show exclusions at age. Each plot shows a single exclusion type with the different runs shown in different colors.

# In[40]:


combined['rounded_age'] = np.around(combined.age).astype(int)


# In[41]:


count_by_age = combined.groupby(['run_name', 'clean_value', 'rounded_age']).agg({'id': 'count'}).reset_index()


# In[42]:


p = sns.catplot(x='rounded_age', y='id', col='clean_value', data=count_by_age[count_by_age.clean_value != 'Include'], hue='run_name', col_wrap=3, kind="bar")
p


# In[43]:


compare.subject_stats_comparison(combined)

