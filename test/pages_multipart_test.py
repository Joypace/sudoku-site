import email.policy
import json
from email.parser import BytesParser
from pathlib import Path
import subprocess
import tempfile
import unittest


def worker_is_file(packet):
    message = BytesParser(policy=email.policy.default).parsebytes(
        ("Content-Type: " + packet["contentType"] + "\r\nMIME-Version: 1.0\r\n\r\n" + packet["body"]).encode()
    )
    parts = {part.get_param("name", header="content-disposition"): part for part in message.iter_parts()}
    bundle = parts.get("_worker.bundle")
    if bundle is None or bundle.get_filename() != "_worker.bundle" or not bundle.is_multipart():
        return False
    modules = {part.get_param("name", header="content-disposition"): part for part in bundle.iter_parts()}
    return (
        modules["_worker.js"].get_filename() == "_worker.js"
        and modules["_worker.js"].get_content_type() == "application/javascript+module"
        and json.loads(modules["metadata"].get_payload(decode=True)) == {"main_module": "_worker.js"}
        and parts["_routes.json"].get_filename() == "_routes.json"
        and parts["_headers"].get_filename() == "_headers"
    )


class PagesUploadRegression(unittest.TestCase):
    def test_worker_is_uploaded_as_file_not_silently_ignored_text(self):
        with tempfile.TemporaryDirectory(prefix="sudoku-pages-multipart-") as directory:
            root = Path(directory)
            for name, content in {
                "_worker.js": 'export default {fetch(){return new Response("probe")}}',
                "_routes.json": '{"version":1,"include":["/*"],"exclude":[]}',
                "_headers": "/probe\n  Cache-Control: no-store\n",
            }.items():
                (root / name).write_text(content)
            receipt = root / "assets.json"
            receipt.write_text(json.dumps({"summary": {"project": "sudoku-joypace", "missing": 0}, "manifest": {}}))
            output = root / "request.json"
            subprocess.run(["node", str(Path(__file__).parents[1] / "tools/prepare_pages_deploy.mjs"),
                            str(root), str(receipt), "probe", str(output)], check=True, capture_output=True)
            self.assertTrue(worker_is_file(json.loads(output.read_text())))
            # Original failing request: successful static deployment, no Worker File.
            original = {"contentType": "multipart/form-data; boundary=original", "body":
                        '--original\r\nContent-Disposition: form-data; name="_worker.js"\r\n'
                        'Content-Type: application/javascript+module\r\n\r\n'
                        'export default {}\r\n--original--\r\n'}
            self.assertFalse(worker_is_file(original))


if __name__ == "__main__":
    unittest.main()
