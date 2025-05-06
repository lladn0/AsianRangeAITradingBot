import unittest
from modules.model import Model

# Basic test to check if saved model works properly
class TestModel(unittest.TestCase):

    def setUp(self):
        # Load existing model and its metadata
        self.model = Model("EURUSD")
        self.model.load_model()

    def test_prediction_shape(self):
        x = self.model.x.iloc[:5]  # Take first 5 rows of features
        x_scaled = self.model.scaler.transform(x)  # Scale it
        preds = self.model.model.predict(x_scaled)  # Predict
        self.assertEqual(len(preds), 5)  # Check that we got 5 results


    def test_evaluation_output(self):
        # Evaluation should return classification report as string
        report = self.model.evaluate()
        self.assertIn("precision", report)  # just check some key metric exists

if __name__ == '__main__':
    unittest.main()
