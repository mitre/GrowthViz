# GrowthViz

The real code for this is in Latest Demo Code.ipynb. Other notebooks contain previous attempts at
getting things working.

Requires Python 3, Jupyter Notebook, Pandas, Matplotlib and Seaborn. Also requires the Qgrid extension
enabled in Jupyter. Expected CSV files are committed to the repo.

There is some R code and related files. They are not used by the notebook, but were used to generate the data in the CSV files.

## Contents

- [Background](#background)
- [Growthcleanr](#growthcleanr)
- [Data Exploration Tool](#data-exploration-tool)
- [Simple Install (Anaconda)](#simple-install)
- [Sample data and first run testing](#sample-data-and-first-run-testing)

## Background

As stated in [Automated identification of implausible values in growth data from pediatric electronic health records](https://academic.oup.com/jamia/article/24/6/1080/3767271):

> In pediatrics, evaluation of growth is fundamental, and many pediatric research studies include some aspect of growth as an outcome or other variable. The clinical growth measurements obtained in day-to-day care are susceptible to error beyond the imprecision inherent in any anthropometric measurement. Some errors result from minor problems with measurement technique. While these errors can be important in certain analyses, they are often small and generally impossible to detect after measurements are recorded. Larger measurement technique errors can result in values that are biologically implausible and can cause problems for many analyses.

## Growthcleanr

[growthcleanr](https://github.com/carriedaymont/growthcleanr) is an automated method for cleaning longitudinal pediatric growth data from EHRs. It is available as open source software.

## GrowthViz Purpose

The objective of this tool is to allow users to analyze how growthcleanr is performing on a data set. This tool is to be used **after** a data set has been run through growthcleanr.

This tool is a [Juypter Notebook](https://jupyter.org/). It provides an environment that includes graphical user interfaces as well as interactive software development to explore data. This notebook uses the [Python programming language](https://www.python.org/). The Python code is used to import, transform, visualize and analyze the output of growthcleanr. Some of the code for the tool is directly included in this notebook. Other functions have been placed in an external file to minimize the amount of code that users see in order to let them focus on the actual data.

Data analysis is performed using [NumPy](https://numpy.org/) and [Pandas](https://pandas.pydata.org/). The output of growthcleanr will be loaded into a [pandas DataFrame](https://pandas.pydata.org/pandas-docs/stable/reference/api/pandas.DataFrame.html). This tool expects the output to be in a [CSV format that is described later on in the notebook](#input_structure). This tool provides functions for transforming DataFrames to support calculation of some values, such as BMI, as well as supporting visualizations. It is expected that users will create views into or copies of the DataFrames built initially by this tool. Adding columns to the DataFrames created by this tool is unlikely to cause problems. Removing columns is likely to break some of the tool's functionality.

Visualization in the tool is provided by [Matplotlib](https://matplotlib.org/) and [Seaborn](http://seaborn.pydata.org/). Users may generate their own charts with these utilities.

## Simple Install

Anaconda is a all in one package installer for setting up dependencies needed to run and view GrowthViz.

1. Follow install instructions [found here](https://docs.anaconda.com/anaconda/install/) to install anaconda. The [windows install instructions](https://docs.anaconda.com/anaconda/install/windows/) are step-by-step and will get everything setup properly for the project.
2. Download the [bmi-demo project](https://gitlab.mitre.org/codi/bmi-demo) and unzip it to have access to all of the source files for the Jupyter notebook. The download button is on the top right corner of the page next to the Find File button.
3. Once the above dependencies are downloaded run the Anaconda Navigator that was installed during Step 1.
4. In Anaconda navigator you should see Jupyter Notebook as one of the default applications installed. Click Launch under the Jupyter icon. This will open the Jupyter interface in your default browser.
5. Within the browser, navigate to the `bmi-demo` folder you downloaded and unzipped in step 2. Select the `Latest Demo Code.ipynb` to run the Python notebook.
6. Once the notebook is open you can click on the "Run" button to step through the various blocks (cells) of the document.

## Sample data and first run testing

By default when you reach step 6 of the [Simple Install](#simple-install) instructions above the notebook will use sample data loaded from the .csv files located in the bmi-demo project.
