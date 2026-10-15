import importlib.util
from pathlib import Path
import unittest

spec = importlib.util.spec_from_file_location('check_app_update', Path(__file__).resolve().parents[1] / 'tools/check_app_update.py')
check = importlib.util.module_from_spec(spec)
spec.loader.exec_module(check)


class UpdateReview(unittest.TestCase):
    def test_tip_changes_review_help_and_demo_sections(self):
        self.assertIn('Touch controls, boards, history, hints and Help', check.sections_for(['lib/widgets/tips/tip_player.dart']))
        self.assertIn('Touch controls, boards, history, hints and Help', check.sections_for(['docs/ued/tips/capture.dart']))

    def test_other_features_and_unknown_behavior_are_not_silently_ignored(self):
        self.assertIn('Create, import and share', check.sections_for(['lib/widgets/sharing/puzzle_preview_page.dart']))
        self.assertTrue(check.sections_for(['lib/engine/new_feature.dart']))
        self.assertIn('App identity, opening links, privacy and platform support', check.sections_for(['ios/Runner/Runner.entitlements']))
        self.assertIn('App identity, opening links, privacy and platform support', check.sections_for(['android/app/build.gradle.kts']))
        for asset in ['assets/google_fonts/Inter-Regular.ttf', 'assets/ui/icon.webp', 'assets/flake/sprite.png']:
            self.assertIn('Other shipped artwork, fonts and effects: review rendered sections', check.sections_for([asset]))
        self.assertEqual([], check.sections_for(['test/widget/example_test.dart', 'docs/internal_note.md']))


if __name__ == '__main__':
    unittest.main()
