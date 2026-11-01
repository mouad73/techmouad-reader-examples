import importlib.util
from pathlib import Path
import unittest
spec=importlib.util.spec_from_file_location('launch_check',Path(__file__).resolve().parents[1]/'hostinger-wordpress-checklist/check.py')
check=importlib.util.module_from_spec(spec);spec.loader.exec_module(check)
class LaunchCheckTests(unittest.TestCase):
    def test_lowercase_header_noindex_is_detected(self):
        self.assertTrue(check.analyze('<title>Test</title>',{'x-robots-tag':'noindex'})['explicitNoindex'])
    def test_none_directive_and_canonical_are_preserved(self):
        result=check.analyze('<title>عنوان</title><link rel="canonical" href="https://example.com/"><meta name="robots" content="follow, none">')
        self.assertTrue(result['explicitNoindex']);self.assertEqual(result['canonical'],['https://example.com/'])
    def test_missing_noindex_is_not_an_indexing_claim(self):
        result=check.analyze('<title>عنوان</title>');self.assertFalse(result['explicitNoindex']);self.assertIn('does not prove Google indexing',result['note'])
if __name__=='__main__':unittest.main()
