import os
import sys

def check_for_file(file_name, not_found_message):
  if not os.path.exists(file_name):
    sys.exit(file_name + ": " + not_found_message)

# Make sure an output directory exists to allow for the export of
# data frames in the notebook
if not os.path.exists('output'):
  print('Did not find output directoty, creating one')
  os.mkdir('output')

# Check for the notebook
check_for_file('GrowthViz.ipynb', 'Unable to find the GrowthViz Jupyter Notebook.')

# Check for the function library
check_for_file('charts.py', 'Unable to find library functions for GrowthViz.')

# Check for the CDC growth charts
check_for_file('bmiagerev.csv', 'Unable to find CDC growth charts for BMI at age.')
check_for_file('statage.csv', 'Unable to find CDC growth charts for height / stature at age.')
check_for_file('wtage.csv', 'Unable to find CDC growth charts for weight at age.')

# Check for the example csv files
check_for_file('clean_with_swaps.csv', 'Unable to example growthcleanr output.')
check_for_file('clean_with_uswaps.csv', 'Unable to example growthcleanr output with unit swaps turned on.')

print('GrowthViz appears to be properly set up.')