"""Levels distinguish available lessons from the full HoDoKu roadmap."""
from pathlib import Path
import copy,json,importlib.util,unittest
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('catalogue',ROOT/'tools/lesson_catalogue.py');p=importlib.util.module_from_spec(spec);spec.loader.exec_module(p)
class Catalogue(unittest.TestCase):
 def setUp(self):
  self.c=json.loads((ROOT/'learn/curriculum.json').read_text());self.m=json.loads((ROOT/'learn/manifest.json').read_text())
 def test_four_level_sections_and_navigation_cover_every_published_lesson_once(self):
  body=p.body(self.c,self.m)
  for level in p.LEVELS:
   self.assertIn(f'href="#{level}"',body);self.assertIn(f'id="{level}" aria-labelledby="{level}-heading"',body)
  for lesson in self.m['lessons']:self.assertEqual(body.count(f'href="/learn/{lesson["slug"]}/"'),1)
  self.assertLess(body.index('id="basic"'),body.index('id="intermediate"'));self.assertLess(body.index('id="intermediate"'),body.index('id="advanced"'));self.assertLess(body.index('id="advanced"'),body.index('id="expert"'))
 def test_unpublished_topics_are_labeled_preparation_and_have_no_dead_lesson_links(self):
  body=p.body(self.c,self.m);ready={x['slug'] for x in self.m['lessons']};pending=[x for x in self.c['techniques'] if x['slug'] not in ready];self.assertTrue(pending);self.assertIn('in preparation',body)
  for topic in pending:self.assertIn(topic['title'].replace('&','&amp;'),body);self.assertNotIn(f'href="/learn/{topic["slug"]}/"',body)
 def test_invalid_or_duplicate_classification_or_foreign_references_cannot_be_published(self):
  for key,value in [('level','unknown'),('family','unknown'),('sourceURL','https://example.com/tech.php'),('sourceURL','javascript:alert(1)')]:
   with self.subTest(key=key):
    c=copy.deepcopy(self.c);c['techniques'][0][key]=value
    with self.assertRaises(ValueError):p.validate_curriculum(c,self.m)
  for mode in ['duplicate','missing','levels']:
   c=copy.deepcopy(self.c)
   if mode=='duplicate':c['techniques'].append(c['techniques'][0])
   if mode=='missing':c['techniques']=[x for x in c['techniques'] if x['slug']!=self.m['lessons'][0]['slug']]
   if mode=='levels':c['levels'].reverse()
   with self.subTest(mode=mode),self.assertRaises(ValueError):p.validate_curriculum(c,self.m)
if __name__=='__main__':unittest.main()
