import unittest

import pandas as pd

from growthviz import processdata


class DataTestCase:
    SAMPLE_DATA = "path/to/sample/data.csv"
    MODE = "adults or pediatrics"

    def setUp(self):
        self.df = pd.read_csv(self.SAMPLE_DATA)

    def test_setup_individual_obs(self):
        setup_df = processdata.setup_individual_obs_df(self.df)
        self.assertEqual(
            set(
                [
                    "id",
                    "subjid",
                    "param",
                    "measurement",
                    "agedays",
                    "ageyears",
                    "sex",
                    "clean_value",
                    "clean_cat",
                    "include",
                ]
            ),
            set(setup_df.columns),
        )

    def test_keep_age_range(self):
        setup_df = processdata.setup_individual_obs_df(self.df)
        keep_df = processdata.keep_age_range(setup_df, self.MODE)
        self.assertTrue(len(setup_df) >= len(keep_df))

    def setup_keep_merge(self, df):
        setup_df = processdata.setup_individual_obs_df(df)
        keep_df = processdata.keep_age_range(setup_df, self.MODE)
        merge_df = processdata.setup_merged_df(keep_df)
        return merge_df

    def test_no_nans(self):
        merge_df = self.setup_keep_merge(self.df)
        self.assertEqual(0, merge_df["ageyears"].isnull().sum())
        self.assertEqual(0, merge_df["sex"].isnull().sum())

    def test_cols(self):
        merge_df = self.setup_keep_merge(self.df)
        self.assertEqual(
            set(
                [
                    "id",
                    "subjid",
                    "agedays",
                    "ageyears",
                    "sex",
                    "include_height",
                    "height",
                    "height_cat",
                    "include_weight",
                    "weight",
                    "weight_cat",
                    "bmi",
                    "include_both",
                    "rounded_age",
                ]
            ),
            set(merge_df.columns),
        )

    def test_sex(self):
        merge_df = self.setup_keep_merge(self.df)
        self.assertTrue(merge_df["sex"].isin([0, 1]).all())


class AdultDataTestCase(DataTestCase, unittest.TestCase):
    SAMPLE_DATA = "growthviz-data/sample-adults-data.csv"
    MODE = "adults"


class PediatricDataTestCase(DataTestCase, unittest.TestCase):
    SAMPLE_DATA = "growthviz-data/sample-pediatrics-data.csv"
    MODE = "pediatrics"


class PctAdultTestCase(unittest.TestCase):
    def setUp(self):
        self.df = pd.read_csv("growthviz-data/ext/vdsmeasures.csv", encoding="latin1")

    def test_vdsmeasures_data(self):
        self.assertEqual(0, self.df["Number of examined persons"].isnull().sum())
        self.assertEqual(0, self.df["Standard error of the mean"].isnull().sum())

    def test_setup_percentiles_adults(self):
        setup_df = processdata.setup_percentiles_adults(self.df)
        self.assertTrue(setup_df["age"].between(18, 110, inclusive="both").all())
        self.assertEqual(0, setup_df["sd"].isnull().sum())
        self.assertEqual(0, setup_df["P5"].isnull().sum())
        self.assertEqual(0, setup_df["P95"].isnull().sum())


class PctPedBMITestCase(unittest.TestCase):
    def setUp(self):
        self.fns = ["bmiagerev.csv", "wtage.csv", "statage.csv"]

    def test_setup_percentiles_peds_bmi(self):
        for fn in self.fns:
            setup_df = processdata.setup_percentiles_pediatrics(fn)
            self.assertTrue(setup_df["age"].between(2, 20.1, inclusive="both").all())
            self.assertEqual(setup_df["P50"].all(), setup_df["M"].all())

    def test_setup_percentiles_peds_ht_wt(self):
        df_percentiles = processdata.setup_percentiles_pediatrics_new()
        df_ht, df_wt, _ = processdata.split_percentiles_pediatrics(df_percentiles)
        self.assertTrue(df_ht["age"].between(0, 21.1, inclusive="both").all())
        self.assertTrue(df_wt["age"].between(0, 21.1, inclusive="both").all())
