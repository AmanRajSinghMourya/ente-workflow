import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

SCRIPT = Path(__file__).with_name('queue.py')
SPEC = importlib.util.spec_from_file_location('queue_shared', SCRIPT)
QUEUE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(QUEUE)
EMPTY = '# Internal queue\n<!-- queue:start -->\n| ID | Task | Status | Codex task | Context |\n| --- | --- | --- | --- | --- |\n<!-- queue:end -->\n'
THREAD = '12345678-1234-1234-1234-123456789abc'

class SharedQueueTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root/'.workflow/queues').mkdir(parents=True)
        self.config = self.root/'.workflow/local.json'
        self.config.write_text(json.dumps({'machine':'macbook-air'}))
        for machine in ('macbook-air','mac-mini'):
            (self.root/f'.workflow/queues/{machine}.md').write_text(EMPTY)
        self.todo=self.root/'TODO.md'
        self.todo.write_text('# Generated display\n')

    def runq(self,*args,ok=True,file=None):
        r=subprocess.run([sys.executable,str(SCRIPT),'--file',str(file or self.todo),*args],capture_output=True,text=True)
        if ok: self.assertEqual(r.returncode,0,r.stderr)
        else: self.assertNotEqual(r.returncode,0)
        return json.loads(r.stdout) if ok else r.stderr

    def test_only_local_machine_claims_and_preserves_other_queue(self):
        self.runq('add','--title','Air task','--context','a')
        self.config.write_text(json.dumps({'machine':'mac-mini'}))
        self.runq('add','--title','Mini task','--context','b')
        mini=(self.root/'.workflow/queues/mac-mini.md').read_bytes()
        self.config.write_text(json.dumps({'machine':'macbook-air'}))
        claim=self.runq('claim')
        self.assertEqual(claim['task'],'Air task')
        self.assertIsNone(self.runq('claim'))
        self.assertEqual((self.root/'.workflow/queues/mac-mini.md').read_bytes(),mini)
        rows=self.runq('list','--all')
        self.assertEqual({(r['machine'],r['id']) for r in rows},{('macbook-air','Q001'),('mac-mini','Q001')})

    def test_foreign_file_cannot_bypass_owner_and_bad_machine_fails(self):
        foreign=self.root/'.workflow/queues/mac-mini.md'
        before=foreign.read_bytes()
        self.runq('add','--title','Intruder','--context','x',file=foreign,ok=False)
        self.assertEqual(foreign.read_bytes(),before)
        self.config.write_text(json.dumps({'machine':'unknown'}))
        self.runq('claim',ok=False)

    def test_view_has_machine_and_real_links_without_context_dump(self):
        folder=self.root/'tasks/B-auth-example';folder.mkdir(parents=True)
        (folder/'PRD.md').write_text(f'# Test\n[Chat](codex://threads/{THREAD})\n')
        (folder/'BOARD.md').write_text(f'[Chat](codex://threads/{THREAD})\n[PR](https://github.com/AmanRajSinghMourya/ente/pull/5)\n[Claude review](reviews/claude-design.md)\n')
        (folder/'reviews').mkdir();(folder/'reviews/claude-design.md').write_text('Review')
        self.runq('add','--title','Auth test','--context','SECRET_INTERNAL_CONTEXT','--thread',THREAD)
        self.runq('view')
        content=self.todo.read_text()
        self.assertIn('Auth test',content)
        self.assertIn('MacBook Air',content)
        self.assertIn(f'codex://threads/{THREAD}',content)
        self.assertIn('tasks/B-auth-example/PRD.md',content)
        self.assertIn('tasks/B-auth-example/reviews/claude-design.md',content)
        self.assertNotIn('SECRET_INTERNAL_CONTEXT',content)
        self.assertNotIn('| ID |',content)
        self.assertEqual(len(self.runq('list')),1)

    def test_duplicate_shared_thread_is_not_added_twice(self):
        self.runq('add','--title','Existing','--context','x','--thread',THREAD)
        self.config.write_text(json.dumps({'machine':'mac-mini'}))
        self.runq('add','--title','Repeat','--context','x','--thread',THREAD,ok=False)
        self.assertEqual(self.runq('list'),[])

    def test_sync_conflict_blocks_mutations_but_allows_reading(self):
        self.runq('add','--title','Task','--context','x')
        (self.root/'.workflow/sync-status.json').write_text(json.dumps({'status':'conflict'}))
        self.assertEqual(len(self.runq('list')),1)
        self.runq('claim',ok=False)
        self.assertEqual(self.runq('list')[0]['status'],'queued')

    def test_git_conflict_blocks_mutation_even_if_status_was_overwritten(self):
        self.runq('add','--title','Task','--context','x')
        (self.root/'.git').mkdir()
        (self.root/'.git/MERGE_HEAD').write_text('in-progress merge')
        (self.root/'.workflow/sync-status.json').write_text(json.dumps({'status':'pending'}))
        self.runq('claim',ok=False)
        self.assertEqual(self.runq('list')[0]['status'],'queued')

    def test_new_clone_can_render_without_existing_todo(self):
        self.todo.unlink()
        self.runq('view')
        self.assertIn('No tasks yet.',self.todo.read_text())

    def test_pending_sync_is_visible_without_internal_error_dump(self):
        (self.root/'.workflow/sync-status.json').write_text(json.dumps({'status':'pending','error':'Fetch failed internal trace'}))
        self.runq('view')
        content=self.todo.read_text()
        self.assertIn('Sync is waiting',content)
        self.assertNotIn('internal trace',content)

if __name__=='__main__': unittest.main()
