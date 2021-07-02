import unittest

import pandas as pd

from growthviz import processdata
from growthviz import sumstats


class StatAdultTestCase(unittest.TestCase):
    def setUp(self):
        self.df = pd.read_csv("growthviz-data/ext/vdsmeasures.csv")

    def test_setup_percentiles_adults(self):
        setup_df = processdata.setup_percentiles_adults(self.df)
        long_df = sumstats.setup_percentile_zscore_adults(setup_df)
        self.assertTrue(len(setup_df) > len(long_df))
        self.assertIn(18, long_df["age"].values)
