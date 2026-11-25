"""Page integration: readers see the data admitted by the lesson contract."""
import json,unittest
from pathlib import Path
from html.parser import HTMLParser
ROOT=Path(__file__).resolve().parents[1]
class Page(HTMLParser):
 def __init__(self):super().__init__();self.figures=[];self.plays=[];self.canonical=[];self.scripts=[];self.pres=[];self.ld=[];self.in_pre=False;self.in_ld=False
 def handle_starttag(self,tag,attrs):
  a=dict(attrs)
  if tag=='figure' and 'data-example-animation' in a:self.figures.append(a['data-example-animation'])
  if tag=='a' and 'play-example' in a.get('class','').split():self.plays.append(a['href'])
  if tag=='link' and a.get('rel')=='canonical':self.canonical.append(a['href'])
  if tag=='script':
   if 'src' in a:self.scripts.append(a['src'])
   self.in_ld=a.get('type')=='application/ld+json'
  if tag=='pre' and 'grid-text' in a.get('class','').split():self.in_pre=True
 def handle_endtag(self,tag):
  if tag=='pre':self.in_pre=False
  if tag=='script':self.in_ld=False
 def handle_data(self,text):
  if self.in_pre:self.pres.append(text)
  if self.in_ld:self.ld.append(text)
class Lessons(unittest.TestCase):
 def test_each_article_links_and_readable_digits_match_its_approved_examples(self):
  manifest=json.loads((ROOT/'learn/manifest.json').read_text())
  for lesson in manifest['lessons']:
   folder=ROOT/'learn'/lesson['slug'];text=(folder/'index.html').read_text();page=Page();page.feed(text);cases=json.loads((folder/'examples.json').read_text());count=len(cases)
   self.assertEqual(page.figures,[c['animation'] for c in cases]);self.assertEqual(page.plays,[c['shareURL'] for c in cases]);self.assertEqual([''.join(p.split()) for p in page.pres],[c['grid'] for c in cases]);self.assertEqual(page.canonical,['https://sudoku.joypace.com/learn/'+lesson['slug']+'/']);self.assertEqual(page.scripts,['/learn/learn.js']);self.assertEqual(json.loads(''.join(page.ld))['datePublished'],lesson['published'])
   for control in ['data-play','data-replay','data-enlarge','Read the starting puzzle digits']:self.assertEqual(text.count(control),count)
   self.assertNotIn('Li Zhang',text)
 def test_catalogue_and_homepage_expose_every_published_article(self):
  manifest=json.loads((ROOT/'learn/manifest.json').read_text());index=(ROOT/'learn/index.html').read_text();home=(ROOT/'index.html').read_text();sitemap=(ROOT/'sitemap.xml').read_text();self.assertIn('href="/learn/"',home)
  for lesson in manifest['lessons']:
   url='/learn/'+lesson['slug']+'/';self.assertIn('href="'+url+'"',index);self.assertIn('https://sudoku.joypace.com'+url,sitemap)
  if any(x['slug']=='naked-pair' for x in manifest['lessons']):
   self.assertLess(index.index('href="/learn/naked-pair/"'),index.index('href="/learn/hidden-single/"'))
if __name__=='__main__':unittest.main()
