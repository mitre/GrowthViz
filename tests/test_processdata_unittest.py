import unittest
import pandas as pd
import processdata


class DataTestCase(unittest.TestCase):
    def setUp(self):
        self.df = pd.read_csv("growthviz-data/sample-adults-cleaned.csv")

    def test_setup_individual_obs(self):
        setup_df = processdata.setup_individual_obs_df(self.df, "adults")
        self.assertEqual(
            set(
                [
                    "id",
                    "subjid",
                    "param",
                    "measurement",
                    "age",
                    "sex",
                    "clean_value",
                    "reason",
                    "clean_cat",
                    "include",
                ]
            ),
            set(setup_df.columns),
        )

    def test_keep_age_range(self):
        setup_df = processdata.setup_individual_obs_df(self.df, "adults")
        keep_df = processdata.keep_age_range(setup_df, "adults")
        self.assertTrue(len(setup_df) >= len(keep_df))

    def setup_keep_merge(self, df, mode):
        setup_df = processdata.setup_individual_obs_df(df, mode)
        keep_df = processdata.keep_age_range(setup_df, mode)
        merge_df = processdata.setup_merged_df(keep_df, mode)
        return merge_df

    def test_no_nans(self):
        merge_df = self.setup_keep_merge(self.df, "adults")
        self.assertEqual(0, merge_df["age"].isnull().sum())
        self.assertEqual(0, merge_df["sex"].isnull().sum())

    def test_cols(self):
        merge_df = self.setup_keep_merge(self.df, "adults")
        self.assertEqual(
            set(
                [
                    "id",
                    "subjid",
                    "age",
                    "sex",
                    "height_cat",
                    "include_height",
                    "height",
                    "reason",
                    "weight_cat",
                    "include_weight",
                    "weight",
                    "bmi",
                    "include_both",
                    "rounded_age",
                ]
            ),
            set(list(merge_df.columns)),
        )

    def test_sex(self):
        merge_df = self.setup_keep_merge(self.df, "adults")
        self.assertTrue(merge_df["sex"].isin([0, 1]).all())


class PctAdultTestCase(unittest.TestCase):
    def setUp(self):
        self.df = pd.read_csv("vdsmeasures.csv", encoding="latin1")

    # fill in
    def test_vdsmeasures_data(self):
        self.assertEqual(0, self.df["Number of examined persons"].isnull().sum())
        self.assertEqual(0, self.df["Standard error of the mean"].isnull().sum())

    def test_setup_percentiles_adults(self):
        setup_df = processdata.setup_percentiles_adults(self.df)
        self.assertTrue(setup_df["age"].between(18, 110, inclusive=True).all())
        self.assertEqual(0, setup_df["sd"].isnull().sum())
        self.assertEqual(0, setup_df["P5"].isnull().sum())
        self.assertEqual(0, setup_df["P95"].isnull().sum())


class PctPedBMITestCase(unittest.TestCase):
    def setUp(self):
        self.fns = ["bmiagerev.csv", "wtage.csv", "statage.csv"]

    def test_setup_percentiles_peds_bmi(self):
        for fn in self.fns:
            setup_df = processdata.setup_percentiles_pediatrics(fn)
            self.assertTrue(setup_df["age"].between(2, 20.1, inclusive=True).all())
            self.assertEqual(setup_df["P50"].all(), setup_df["M"].all())
