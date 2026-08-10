import os
import tempfile
import unittest
import zipfile

from scripts.garmin.garmin_sync_global import extract_fit_files, sync_zip_files


class FakeUploader:
    def __init__(self, outcomes):
        self.outcomes = list(outcomes)
        self.paths = []

    def upload_activity(self, path):
        self.paths.append(path)
        outcome = self.outcomes.pop(0)
        if isinstance(outcome, Exception):
            raise outcome
        return outcome


class GarminGlobalSyncTests(unittest.TestCase):
    def make_zip(self, directory, name, members):
        zip_path = os.path.join(directory, name)
        with zipfile.ZipFile(zip_path, "w") as archive:
            for member_name, content in members.items():
                archive.writestr(member_name, content)
        return zip_path

    def test_extract_fit_files_ignores_non_fit_members(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            zip_path = self.make_zip(
                temp_dir,
                "activity.zip",
                {
                    "123.fit": b"fit-one",
                    "nested/456.FIT": b"fit-two",
                    "notes.txt": b"ignore-me",
                },
            )
            output_dir = os.path.join(temp_dir, "out")

            extracted = extract_fit_files(zip_path, output_dir)

            self.assertEqual(2, len(extracted))
            self.assertTrue(all(path.lower().endswith(".fit") for path in extracted))
            self.assertEqual(
                {b"fit-one", b"fit-two"},
                {open(path, "rb").read() for path in extracted},
            )

    def test_sync_zip_files_treats_duplicate_as_success_and_isolates_errors(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            self.make_zip(temp_dir, "1.zip", {"1.fit": b"one"})
            self.make_zip(temp_dir, "2.zip", {"2.fit": b"two"})
            self.make_zip(temp_dir, "3.zip", {"3.fit": b"three"})
            uploader = FakeUploader(
                ["SUCCESS", "DUPLICATE_ACTIVITY", RuntimeError("upload failed")]
            )

            result = sync_zip_files(temp_dir, uploader)

            self.assertEqual(3, result["total"])
            self.assertEqual(2, result["succeeded"])
            self.assertEqual(1, result["failed"])
            self.assertEqual(3, len(uploader.paths))


if __name__ == "__main__":
    unittest.main()
