import unittest
from scripts.discover_sources import build_report, github_repo, normalized_path, safe_path

class DiscoveryTests(unittest.TestCase):
    def test_github_url_is_strict(self):
        self.assertEqual(github_repo("https://github.com/Owner/Repo"),("Owner","Repo"))
        for url in ("http://github.com/a/b","https://github.com/a/b/tree/main","https://example.com/a/b"):
            with self.subTest(url=url), self.assertRaises(ValueError): github_repo(url)
    def test_unsafe_paths(self):
        for path in ("../secret/SKILL.md","/absolute/SKILL.md","safe/../SKILL.md","safe\\SKILL.md"):
            self.assertFalse(safe_path(path))
    def test_normalization(self):
        self.assertEqual(normalized_path("Skills/My-Skill/SKILL.md"),"skills/my-skill/skill.md")
    def test_metadata_only_and_no_approval(self):
        rev="a"*40
        data={
          "https://api.github.com/repos/owner/repo":{"default_branch":"main"},
          "https://api.github.com/repos/owner/repo/commits/main":{"sha":rev},
          f"https://api.github.com/repos/owner/repo/git/trees/{rev}?recursive=1":{"truncated":False,"tree":[
            {"path":"skills/demo/SKILL.md","type":"blob","mode":"100644","size":100,"sha":"b"*40},
            {"path":"docs/readme.md","type":"blob","mode":"100644","size":20,"sha":"c"*40},
            {"path":"bad/../SKILL.md","type":"blob","mode":"100644","size":10,"sha":"d"*40},
            {"path":"large/SKILL.md","type":"blob","mode":"100644","size":999999,"sha":"e"*40}]}}
        report=build_report({"sources":[{"id":"demo","url":"https://github.com/owner/repo"}]},lambda url:data[url])
        self.assertEqual(report["summary"]["candidates_found"],1)
        item=report["candidates"][0]
        self.assertEqual(item["review_status"],"unreviewed_candidate")
        self.assertFalse(item["content_fetched"])
        self.assertFalse(item["code_executed"])
        self.assertEqual(report["summary"]["approval_count"],0)
if __name__=="__main__": unittest.main()
