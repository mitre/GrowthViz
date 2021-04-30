import os
import sys


def check_for_file(file_name, not_found_message):
    if not os.path.exists(file_name):
        sys.exit(file_name + ": " + not_found_message)


# Make sure an output directory exists to allow for the export of
# data frames in the notebook
if not os.path.exists("output"):
    print("Did not find output directoty, creating one")
    os.mkdir("output")

# Check for the notebooks
check_for_file(
    "GrowthViz-pediatrics.ipynb",
    "Unable to find the GrowthViz Pediatrics Jupyter Notebook.",
)
check_for_file(
    "GrowthViz-adults.ipynb", "Unable to find the GrowthViz Adults Jupyter Notebook."
)

# Check for the function library
check_for_file(
    "processdata.py", "Unable to find data processing library functions for GrowthViz."
)
check_for_file(
    "sumstats.py", "Unable to find summary statistics library functions for GrowthViz."
)
check_for_file(
    "charts.py", "Unable to find visualization library functions for GrowthViz."
)
check_for_file(
    "compare.py", "Unable to find comparison library functions for GrowthViz."
)
check_for_file(
    "check_data.py", "Unable to find data checks library functions for GrowthViz."
)

# Check for tests
check_for_file(
    "tests/test_processdata.py",
    "Unable to find unit tests for GrowthViz data processing library functions.",
)
check_for_file(
    "tests/test_sumstats.py",
    "Unable to find unit tests for GrowthViz summary statistics library functions.",
)

# Check for the CDC growth charts
check_for_file(
    "bmiagerev.csv", "Unable to find pediatric CDC growth charts for BMI at age."
)
check_for_file(
    "statage.csv",
    "Unable to find pediatric CDC growth charts for height / stature at age.",
)
check_for_file(
    "wtage.csv", "Unable to find pediatric CDC growth charts for weight at age."
)
check_for_file(
    "vdsmeasures.csv",
    "Unable to find CDC growth charts for adult weight, height and BMI.",
)

# Check for the example csv files
check_for_file(
    "growthviz-data/sample-data-cleaned.csv",
    "Unable to find example pediatrics growthcleanr output for comparison.",
)
check_for_file(
    "growthviz-data/sample-data-cleaned-with-ue.csv",
    "Unable to find example pediatrics growthcleanr output with unit errors turned on for comparison.",
)
check_for_file(
    "growthviz-data/sample-adults-data.csv",
    "Unable to example adults growthcleanr output.",
)
check_for_file(
    "growthviz-data/sample-pediatrics-data.csv",
    "Unable to example pediatrics growthcleanr output.",
)

print("GrowthViz appears to be properly set up.")
