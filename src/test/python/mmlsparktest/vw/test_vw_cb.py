# Prepare training and test data.
import os
import unittest
import tempfile
import pyspark

from mmlspark.vw.VowpalWabbitClassifier import VowpalWabbitContextualBandit
from mmlspark.vw.VowpalWabbitRegressor import VowpalWabbitRegressor
from mmlspark.vw.VowpalWabbitFeaturizer import VowpalWabbitFeaturizer
from mmlspark.vw.ColumnVectorSequencer import ColumnVectorSequencer

from pyspark.sql.types import *
from mmlsparktest.spark import *
from pyspark.ml import Pipeline

class VowpalWabbitSpec(unittest.TestCase):

    def get_data(self):
        # create sample data
        schema = StructType([StructField("shared", StringType()),
            StructField("action1", StringType()),
            StructField("action2_feat1", StringType()),
            StructField("action2_feat2", StringType()),
            StructField("action2_feat2", StringType()),
            StructField("cost", DoubleType()),
            StructField("prob", DoubleType())])

        data = pyspark.sql.SparkSession.builder.getOrCreate().createDataFrame([
            ("shared_f", "action1_f", "action2_f", "action2_f2=0", 1, 1, 0.8),
            ("shared_f", "action1_f", "action2_f", "action2_f2=1", 2, 1, 0.8),
            ("shared_f", "action1_f", "action2_f", "action2_f2=1", 2, 4, 0.8),
            ("shared_f", "action1_f", "action2_f", "action2_f2=0", 1, 0, 0.8)], schema)

        # featurize data
        shared_featurizer = VowpalWabbitFeaturizer(inputCols=['shared'], outputCol='shared_features')
        action_one_featurizer = VowpalWabbitFeaturizer(inputCols=['action1'], outputCol='action1_features')
        action_two_featurizer = VowpalWabbitFeaturizer(inputCols=['action2_feat1','action2_feat2'], outputCol='action2_features')
        action_merger = ColumnVectorSequencer(inputCols=['action1_features','action2_features'], outputCol='action_features')
        pipeline = Pipeline(stages=[shared_featurizer, action_one_featurizer, action_two_featurizer, action_merger])
        tranformation_pipeline = pipeline.fit(data)

        return tranformation_pipeline.transform(data)

    def save_model(self, estimator):
        model = estimator.fit(self.get_data())

        # write model to file and validate it's there
        with tempfile.TemporaryDirectory() as tmpdirname:
            modelFile = '{}/model'.format(tmpdirname)

            model.saveNativeModel(modelFile)

            self.assertTrue(os.stat(modelFile).st_size > 0)

    def test_save_model(self):
        self.save_model(VowpalWabbitContextualBandit())

    def test_initial_model(self):
        featurized_data = self.get_data()
        estimator1 = VowpalWabbitContextualBandit()

        model1 = estimator1.fit(featurized_data)

        estimator2 = VowpalWabbitContextualBandit()
        estimator2.setInitialModel(model1)

        model2 = estimator2.fit(featurized_data)

if __name__ == "__main__":
    result = unittest.main()