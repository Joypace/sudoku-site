import hashlib
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]


class AndroidAssociation(unittest.TestCase):
    def test_play_signed_app_has_an_exact_static_json_association(self):
        certificate = (ROOT / 'test/fixtures/play-signing.der').read_bytes()
        fingerprint = ':'.join(f'{b:02X}' for b in hashlib.sha256(certificate).digest())
        association = json.loads((ROOT / '.well-known/assetlinks.json').read_text())
        self.assertEqual(association, [{
            'relation': ['delegate_permission/common.handle_all_urls'],
            'target': {
                'namespace': 'android_app',
                'package_name': 'com.joypace.sudokuletstry',
                'sha256_cert_fingerprints': [fingerprint],
            },
        }])
        headers = (ROOT / '_headers').read_text()
        block = headers.split('/.well-known/assetlinks.json\n', 1)[1].split('\n\n', 1)[0]
        self.assertIn('Content-Type: application/json', block)
        routes = json.loads((ROOT / '_routes.json').read_text())
        self.assertEqual(['/share', '/share/'], routes['include'])


if __name__ == '__main__':
    unittest.main()
