import unittest
import pandas as pd
import processdata
import sumstats


class StatAdultTestCase(unittest.TestCase):
    def setUp(self):
        self.df = pd.read_csv("vdsmeasures.csv")

    def test_setup_percentiles_adults(self):
        setup_df = processdata.setup_percentiles_adults(self.df)
        long_df = sumstats.setup_percentile_zscore_adults(setup_df)
        self.assertTrue(len(setup_df) > len(long_df))
        self.assertIn(18, long_df["age"].values)
