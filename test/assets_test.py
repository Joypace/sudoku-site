"""Website artifacts must remain complete when the App tip catalogue changes."""
import json
from pathlib import Path
import re
import unittest
import xml.etree.ElementTree as ET
from html.parser import HTMLParser

ROOT = Path(__file__).resolve().parents[1]


class Stages(HTMLParser):
    def __init__(self):
        super().__init__()
        self.sources = []
    def handle_starttag(self, tag, attrs):
        values = dict(attrs)
        if 'data-tip' in values:
            self.sources.append(values.get('data-src', 'home-assets/' + values['data-tip'] + '.svg'))
            if values.get('data-mobile-src'):
                self.sources.append(values['data-mobile-src'])


class Artifacts(unittest.TestCase):
    def check_svg(self, file):
        self.assertTrue(file.is_file(), str(file))
        svg = ET.parse(file).getroot()
        self.assertEqual('{http://www.w3.org/2000/svg}svg', svg.tag)
        duration = float(svg.attrib['data-duration'])
        self.assertGreaterEqual(duration, 0)
        if duration == 0:
            self.assertFalse(svg.findall('.//{http://www.w3.org/2000/svg}set'), 'A static illustration must not contain a broken timeline')
        self.assertFalse(svg.findall('.//{http://www.w3.org/2000/svg}script'))
        return svg

    def test_every_homepage_animation_and_responsive_variant_exists(self):
        stages = Stages()
        stages.feed((ROOT / 'index.html').read_text())
        self.assertGreaterEqual(len(stages.sources), 10)
        for source in stages.sources:
            self.check_svg(ROOT / source)

    def test_help_is_the_complete_catalogue_without_broken_or_mismatched_tips(self):
        catalog = json.loads((ROOT / 'home-assets/tips.json').read_text())
        ids = set()
        for tip in catalog['tips']:
            self.assertRegex(tip['id'], r'^[a-z0-9-]+$')
            self.assertNotIn(tip['id'], ids)
            ids.add(tip['id'])
            svg = self.check_svg(ROOT / 'home-assets' / (tip['id'] + '.svg'))
            self.assertEqual(tip['title']['en'], svg.find('{http://www.w3.org/2000/svg}title').text)
            self.assertTrue(tip['description'])
        self.assertGreater(len(ids), 1)


if __name__ == '__main__':
    unittest.main()
