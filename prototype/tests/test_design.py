"""Static regression checks for the ONECALL Design Studio.
No browser dependency; the functional interaction test remains a Codex task.
"""
import re
import unittest
from pathlib import Path

WEB=Path(__file__).resolve().parents[1]/'web'

class DesignStudioTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.html=(WEB/'index.html').read_text(encoding='utf-8')
        cls.css=(WEB/'styles.css').read_text(encoding='utf-8')
        cls.app=(WEB/'app.js').read_text(encoding='utf-8')
        cls.design=(WEB/'design.js').read_text(encoding='utf-8')
    def test_external_assets(self):
        for asset in ('/styles.css','/app.js','/design.js'):
            self.assertIn(f'"{asset}"',self.html)
        self.assertNotIn('<style>',self.html)
        self.assertNotRegex(self.html,r'\sstyle=')
    def test_design_controls(self):
        for key in ('theme','shape','density','type'):
            self.assertIn(f'name="{key}"',self.html)
        self.assertIn('id="designForm"',self.html)
        self.assertIn('id="resetDesign"',self.html)
    def test_theme_tokens(self):
        for theme in ('midnight','violet','forest'):
            self.assertIn(f'[data-theme="{theme}"]',self.css)
        self.assertIn('--primary:',self.css)
        self.assertIn('--radius:',self.css)
    def test_navigation(self):
        self.assertIn('id="showAppearance"',self.html)
        self.assertIn('id="appearance"',self.html)
        self.assertIn("'appearance'",self.app)
    def test_styling_isolated_from_pricing(self):
        self.assertNotIn('/api/rates',self.design)
        self.assertNotIn('/api/enquiries',self.design)
        self.assertNotIn('estimate(',self.design)
    def test_no_duplicate_ids(self):
        ids=re.findall(r'\bid="([^"]+)"',self.html)
        self.assertEqual(len(ids),len(set(ids)))
    def test_csp_served_assets(self):
        server=(WEB.parent/'server.py').read_text(encoding='utf-8')
        self.assertIn("style-src 'self'",server)
        self.assertIn("script-src 'self'",server)

if __name__=='__main__':
    unittest.main()
