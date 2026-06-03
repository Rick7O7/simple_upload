from io import BytesIO
from pathlib import Path
import tempfile
import unittest
import zipfile

from app import app


class UploadAppTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        app.config["TESTING"] = True
        app.config["UPLOAD_DIR"] = Path(self.temp_dir.name)
        self.client = app.test_client()

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_upload_multiple_files_and_download_zip(self):
        response = self.client.post(
            "/upload",
            data={
                "files": [
                    (BytesIO(b"alpha"), "a.txt"),
                    (BytesIO(b"beta"), "b.txt"),
                ]
            },
            content_type="multipart/form-data",
        )
        self.assertEqual(response.status_code, 302)

        index_response = self.client.get("/")
        self.assertEqual(index_response.status_code, 200)
        self.assertIn(b"a.txt", index_response.data)
        self.assertIn(b"b.txt", index_response.data)

        zip_response = self.client.get("/download")
        self.assertEqual(zip_response.status_code, 200)

        with zipfile.ZipFile(BytesIO(zip_response.data)) as archive:
            self.assertEqual(sorted(archive.namelist()), ["a.txt", "b.txt"])


if __name__ == "__main__":
    unittest.main()
