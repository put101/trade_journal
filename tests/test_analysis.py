import unittest
from src.analysis import perform_anova
import pandas as pd

class TestAnalysis(unittest.TestCase):
    
    def test_anova(self):
        # Setup test data
        sample_data = {
            'group': ['A', 'A', 'B', 'B', 'C', 'C'],
            'value': [5, 7, 8, 6, 7, 9]
        }
        df = pd.DataFrame(sample_data)
        
        # Execute ANOVA
        result = perform_anova(df, 'value', 'group')
        
        # Assert the ANOVA table contains expected columns
        expected_columns = {'sum_sq', 'df', 'F', 'PR(>F)'}
        self.assertTrue(expected_columns.issubset(result.columns))
        
        # Assert that p-value is less than 0.05
        p_value = result['PR(>F)'][0]
        self.assertLess(p_value, 0.05)

if __name__ == '__main__':
    unittest.main()
