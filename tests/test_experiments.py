import copy
import json
import tempfile
import unittest
from pathlib import Path

from scripts.experiments import age_group, prepare, read_jsonl, score, validate_prediction


class ExperimentsTest(unittest.TestCase):
    def test_age_boundaries(self):
        self.assertEqual([age_group(a) for a in (17,18,24,25,34,35,44,45,54,55,64,65)],
                         ['under_18','18-24','18-24','25-34','25-34','35-44',
                          '35-44','45-54','45-54','55-64','55-64','65+'])

    def test_grouping_nested_samples_and_no_label_leak(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / 'source.jsonl'
            rows = [{'author': author, 'id': f'{author}{i}', 'text': f'Unique comment {author}{i}',
                     'profile': {'age': 37, 'sex': 'female', 'city_country': 'SecretCity, SecretCountry'}}
                    for author in ('a','b') for i in range(5)]
            source.write_text('\n'.join(json.dumps(row) for row in rows))
            prepare(source, root/'one', 2)
            prepare(source, root/'two', 2)
            requests = read_jsonl(root/'one/requests.jsonl')
            labels = read_jsonl(root/'one/labels.jsonl')
            self.assertEqual(requests, read_jsonl(root/'two/requests.jsonl'))
            self.assertEqual(len(requests), 6)
            self.assertNotIn('SecretCity', json.dumps(requests))
            for offset in (0,3):
                a,b,c = labels[offset:offset+3]
                self.assertEqual(a['comment_ids'], c['comment_ids'][:1])
                self.assertEqual(b['comment_ids'], c['comment_ids'][:3])
                self.assertEqual(len(set(c['comment_ids'])), 5)

    def test_scoring_abstentions_partial_and_duplicates(self):
        actual = {'age_group':'35-44', 'gender':'female', 'location':'Rome, Italy'}
        labels = [{'sample_id':str(i), 'comment_count':1, 'actual_attributes':actual} for i in range(3)]
        prediction = {key: {'value':value, 'confidence':0.8} for key,value in actual.items()}
        rows = [{'sample_id':str(i), 'model':'claude', 'model_version':'recorded-version',
                 'collected_at':'2026-10-22', 'prediction':copy.deepcopy(prediction)} for i in range(2)]
        rows[1]['prediction']['location'] = {'value':None, 'confidence':0}
        location = next(row for row in score(labels, rows) if row['attribute']=='location')
        self.assertEqual(location['accuracy'], 0.5)
        self.assertEqual(location['coverage'], 0.5)
        self.assertFalse(location['complete'])
        self.assertAlmostEqual(location['confidence_mse'], 0.04)
        with self.assertRaises(ValueError):
            score(labels, rows + rows[:1])
        for confidence in (True, float('nan'), 1.1, -0.1):
            bad = copy.deepcopy(prediction)
            bad['gender']['confidence'] = confidence
            with self.assertRaises(ValueError):
                validate_prediction(bad)


if __name__ == '__main__':
    unittest.main()
