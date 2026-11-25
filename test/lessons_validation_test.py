"""Regression cases for the public learning namespace and export admission."""
from pathlib import Path
import importlib.util,unittest,tempfile,json,shutil,hashlib
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('lesson_contract',ROOT/'tools/validate_lessons.py');module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
class Contract(unittest.TestCase):
 def setUp(self):
  self.temp=tempfile.TemporaryDirectory(prefix='lesson-contract-');self.root=Path(self.temp.name);self.learn=self.root/'learn';self.folder=self.learn/'x-wing';self.folder.mkdir(parents=True)
  for name in ['index.html','learn.css','learn.js']:(self.learn/name).write_text('test')
  (self.folder/'index.html').write_text('test');self.manifest=json.loads((ROOT/'learn/manifest.json').read_text());self.cases=json.loads((ROOT/'learn/x-wing/examples.json').read_text())
  for n,c in enumerate(self.cases,1):
   data=(ROOT/f'learn/x-wing/example-{n}.json').read_bytes();(self.folder/f'example-{n}.json').write_bytes(data)
   # Minimal non-executable SVG fixture tests this parser contract, not UI fidelity.
   meta={'app':'1d3fa459e04d2ddbc5fcba8344fec78474af8c93','content':'b7794cfad7e427e85d4a302130dee5a98b9f4b90','productDirty':False,'story':{'sha256':hashlib.sha256(data).hexdigest()}}
   (self.folder/f'example-{n}.svg').write_text('<svg xmlns="http://www.w3.org/2000/svg" data-duration="1"><metadata>'+json.dumps(meta)+'</metadata><g id="frame" display="none"><set attributeName="display" to="inline" begin="0s" dur="1s" fill="remove"/></g></svg>')
  self.write()
 def tearDown(self):self.temp.cleanup()
 def write(self):
  (self.learn/'manifest.json').write_text(json.dumps(self.manifest));(self.folder/'examples.json').write_text(json.dumps(self.cases))
 def reject(self,text):
  with self.assertRaisesRegex(ValueError,text):module.validate(self.root)
 def test_valid_native_format_and_current_real_exports(self):
  self.assertEqual(len(module.validate(self.root)),12);self.assertEqual(len(module.validate(ROOT)),12)
 def test_root_and_descendant_symlinks_rejected_before_reads(self):
  self.learn.rename(self.root/'real');self.learn.symlink_to(self.root/'real',target_is_directory=True);self.reject('symlink');self.learn.unlink();(self.root/'real').rename(self.learn);p=self.folder/'example-1.json';p.rename(self.root/'outside.json');p.symlink_to(self.root/'outside.json');self.reject('symlinks')
 def test_wrong_share_grid_and_provenance_rejected(self):
  original=self.cases[0]['shareURL'];self.cases[0]['shareURL']=self.cases[1]['shareURL'];self.write();self.reject('Share link');self.cases[0]['shareURL']=original;self.cases[0]['scenarioSHA256']='0'*64;self.write();self.reject('provenance')
 def test_hidden_or_malformed_setup_rejected(self):
  p=self.folder/'example-1.json';d=json.loads(p.read_text());d['setup']='';p.write_text(json.dumps(d));self.reject('hidden setup')
 def test_svg_css_and_animation_url_bypasses_rejected(self):
  p=self.folder/'example-1.svg';original=p.read_text()
  for fragment in ['<style>@im\\70ort "https://example.test/a.css";</style>','<image href="#frame"><set attributeName="href" to="https://example.test/a.svg" begin="0s" fill="freeze"/></image>','<image href="https://example.test/a.png"/>','<g onload="alert(1)"/>','<rect fill="URL(https://example.test/a.svg#paint)"/>','<g style="fill:u\\72l(https://example.test/a.svg#x)"/>','<use xml:base="https://example.test/a.svg" href="#frame"/>','<?xml-stylesheet type="text/css" href="https://example.test/a.css"?>']:
   with self.subTest(fragment=fragment):p.write_text(original.replace('</svg>',fragment+'</svg>'));self.reject('Unsupported|External|forbidden')
 def test_reserved_slugs_ids_and_extra_files_rejected(self):
  self.manifest['lessons'][0]['slug']='index';self.write();self.reject('slug');self.manifest['lessons'][0]['slug']='x-wing';self.manifest['lessons'][0]['examples'][0]['id']='different';self.write();self.reject('ID');self.manifest['lessons'][0]['examples'][0]['id']='example-1';self.write();(self.learn/'private.key').write_text('harmless-test-marker');self.reject('Unapproved')
 def test_duplicate_and_unproved_examples_rejected(self):
  self.cases[1]['grid']=self.cases[0]['grid'];self.write();self.reject('different');self.cases=json.loads((ROOT/'learn/x-wing/examples.json').read_text());self.cases[0]['targets']=[self.cases[0]['corners'][0]];self.write();self.reject('eliminations')
if __name__=='__main__':unittest.main()
