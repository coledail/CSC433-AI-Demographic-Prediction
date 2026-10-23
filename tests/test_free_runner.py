import json
from pathlib import Path
import tempfile
import unittest
from run_free_experiments import MODELS, export, parse_prediction


class RunnerTests(unittest.TestCase):
    def test_fenced_json_and_no_invented_repairs(self):
        p={a:{'value':None,'confidence':0} for a in ('age_group','gender','location')}
        self.assertEqual(parse_prediction('```json\n'+json.dumps(p)+'\n```'),p)
        with self.assertRaises(ValueError):
            parse_prediction('I think the person is 30.')

    def test_partial_export_preserves_missing_status(self):
        labels=[{'sample_id':'a:1','profile_id':'a','comment_count':1,
                 'actual_attributes':{'age_group':'25-34','gender':'male','location':'Rome, Italy'}}]
        with tempfile.TemporaryDirectory() as tmp:
            directory=Path(tmp)
            export(directory,labels)
            result=json.loads((directory/'comparison_results.json').read_text())
            self.assertEqual(result['valid_predictions'],0)
            self.assertEqual(result['status'],'partial')
            self.assertEqual(result['expected_predictions'],len(MODELS))
            for record in result['comparisons'][0]['ai_results'].values():
                self.assertEqual(record['status'],'pending')
                self.assertIsNone(record['matches_actual']['age_group'])


if __name__=='__main__':
    unittest.main()
