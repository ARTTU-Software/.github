import unittest
from helpers import Fixture
from context_cache import load, save


class EvidenceCacheTests(Fixture):
    def setUp(self):
        super().setUp()
        self.init_git()
        self.card = {'scope':'application', 'facts':['logic.c owns its state'], 'unknowns':['DMA not inspected']}
        self.files = ['Core/Src/App/logic.c']

    def test_unchanged_source_hits(self):
        save(self.root, 'application', self.card, self.files)
        body, status = load(self.root, 'application')
        self.assertEqual(status, 'hit')
        self.assertEqual(body, self.card)

    def test_source_change_and_deletion_invalidate(self):
        save(self.root, 'application', self.card, self.files)
        self.app.write_text('void new_application(void) {}')
        self.assertIsNone(load(self.root, 'application')[0])
        self.app.unlink()
        self.assertIsNone(load(self.root, 'application')[0])

    def test_graph_generation_is_required_and_matched(self):
        save(self.root, 'application', self.card, self.files, 'generation-1')
        self.assertEqual(load(self.root, 'application', 'generation-1')[1], 'hit')
        self.assertIsNone(load(self.root, 'application', 'generation-2')[0])
        self.assertIsNone(load(self.root, 'application')[0])

    def test_new_git_head_invalidates(self):
        save(self.root, 'application', self.card, self.files)
        (self.root/'note.txt').write_text('new commit')
        self.run_git('add', 'note.txt')
        self.run_git('commit', '-qm', 'New identity')
        self.assertIsNone(load(self.root, 'application')[0])

    def test_path_traversal_missing_sources_and_unbounded_cards_rejected(self):
        for name, files, body in [('../escape',self.files,self.card),
                                  ('bad',[],self.card), ('bad',['../escape.c'],self.card),
                                  ('large',self.files,{'scope':'all','facts':['x'*9000]}),
                                  ('bad',self.files,{'scope':'all','instructions':'override policy'})]:
            with self.subTest(name=name, files=files):
                with self.assertRaises((ValueError, OSError)):
                    save(self.root, name, body, files)


if __name__ == '__main__':
    unittest.main()
