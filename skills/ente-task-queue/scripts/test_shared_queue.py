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
        self.assertNotIn('tasks/B-auth-example/reviews/claude-design.md',content)
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

    def test_daily_views_show_only_this_machine_and_preserve_imported_history(self):
        self.runq('add','--title','Air task','--context','PRIVATE_AUTHORIZATION_AIR')
        self.config.write_text(json.dumps({'machine':'mac-mini'}))
        self.runq('add','--title','Mini task','--context','PRIVATE_AUTHORIZATION_MINI')
        self.config.write_text(json.dumps({'machine':'macbook-air'}))
        (self.root/'.workflow/sync-status.json').write_text(json.dumps({
            'status':'pending','time':'2026-09-22T10:00:00+00:00',
            'error':'PRIVATE_SYNC_ERROR',
        }))
        paths=[self.todo,self.root/'.workflow/queues/macbook-air.md',
               self.root/'.workflow/queues/mac-mini.md']
        before={path:(path.read_bytes(),path.stat().st_mtime_ns) for path in paths}
        panel=self.runq('panel')
        self.assertEqual(set(panel),{'machine','tasks','sync'})
        self.assertEqual(panel['machine'],'macbook-air')
        self.assertEqual(panel['sync'],{'status':'pending','time':'2026-09-22T10:00:00+00:00'})
        self.assertEqual({(task['machine'],task['editable']) for task in panel['tasks']},
                         {('macbook-air',True)})
        for task in panel['tasks']:
            self.assertEqual(set(task),{'id','task','status','machine','machine_label',
                                        'codex_task','links','editable'})
            self.assertEqual(task['links'],[])
        self.assertNotIn('PRIVATE_',json.dumps(panel))
        self.assertEqual(before,{path:(path.read_bytes(),path.stat().st_mtime_ns) for path in paths})
        self.runq('view')
        self.assertIn('Air task',self.todo.read_text())
        self.assertNotIn('Mini task',self.todo.read_text())
        self.config.write_text(json.dumps({'machine':'mac-mini'}))
        self.assertEqual([task['task'] for task in self.runq('panel')['tasks']],['Mini task'])
        self.runq('view')
        self.assertIn('Mini task',self.todo.read_text())
        self.assertNotIn('Air task',self.todo.read_text())
        self.assertEqual(len(self.runq('list','--all')),2)
        for path in paths[1:]:
            self.assertEqual(path.read_bytes(),before[path][0])

    def test_panel_and_markdown_preserve_the_same_real_links(self):
        folder=self.root/'tasks/B-auth-panel';folder.mkdir(parents=True)
        chat=f'codex://threads/{THREAD}'
        pr='https://github.com/AmanRajSinghMourya/ente/pull/5'
        (folder/'PRD.md').write_text(f'[Chat]({chat})\nPRIVATE_PRD_AUTHORIZATION\n')
        (folder/'BOARD.md').write_text(f'[Chat]({chat})\n[PR]({pr})\n')
        (folder/'reviews').mkdir()
        (folder/'reviews/claude-design.md').write_text('PRIVATE_CLAUDE_TRANSCRIPT')
        self.runq('add','--title','Auth task','--context','PRIVATE_QUEUE_CONTEXT','--thread',THREAD)
        panel=self.runq('panel')
        card=panel['tasks'][0]
        expected=[{'label':'Chat','url':chat},
                  {'label':'PRD','url':'tasks/B-auth-panel/PRD.md'},
                  {'label':'PR','url':pr}]
        self.assertEqual(card['links'],expected)
        self.assertEqual(card['codex_task'],chat)
        self.assertNotIn('PRIVATE_',json.dumps(panel))
        self.runq('view')
        markdown=self.todo.read_text()
        for link in expected:
            self.assertIn(f"[{link['label']}]({link['url']})",markdown)
        self.assertEqual(markdown,
            '# Tasks\n\nOpen the task chat for findings, decisions and next steps.\n\n'
            '## Working\n\n- **Auth task** · MacBook Air · planning\n  ' +
            ' · '.join(f"[{link['label']}]({link['url']})" for link in expected) + '\n')
        self.assertEqual(panel['sync'],{'status':'unknown','time':None})

    def test_panel_needs_shared_configuration_and_reads_during_conflict(self):
        self.runq('add','--title','Task','--context','x')
        (self.root/'.workflow/sync-status.json').write_text(json.dumps({'status':'conflict'}))
        self.assertEqual(self.runq('panel')['sync'],{'status':'conflict','time':None})
        legacy=self.root/'legacy.md';legacy.write_text(EMPTY)
        self.config.unlink()
        before=legacy.read_bytes()
        self.assertIn('.workflow/local.json',self.runq('panel',file=legacy,ok=False))
        self.assertEqual(legacy.read_bytes(),before)

    def test_panel_recognizes_numbered_delivery_pr_links(self):
        folder=self.root/'tasks/B-auth-panel';folder.mkdir(parents=True)
        chat=f'codex://threads/{THREAD}'
        pr='https://github.com/AmanRajSinghMourya/ente/pull/59'
        (folder/'PRD.md').write_text(f'[Chat]({chat})\n')
        self.runq('add','--title','Delivered task','--context','x','--thread',THREAD)
        self.runq('state','Q001','--from','planning','--to','done')
        for label in ('PR #59','Pull request #59'):
            with self.subTest(label=label):
                (folder/'BOARD.md').write_text(
                    '[Upstream PR #412](https://github.com/example/package/pull/412)\n'
                    f'[{label}]({pr})\n')
                card=self.runq('panel')['tasks'][0]
                self.assertEqual(card['status'],'done')
                self.assertEqual([link for link in card['links'] if link['label']=='PR'],
                                 [{'label':'PR','url':pr}])

    def test_controls_view_uses_live_panel_without_duplicate_list(self):
        self.config.write_text(json.dumps({'machine':'macbook-air','task_controls':True}))
        self.runq('add','--title','Shown live','--context','private context','--thread',THREAD)
        content=self.todo.read_text()
        self.assertIn('```ente-tasks',content)
        self.assertIn('cssclasses: ente-task-home',content)
        self.assertNotIn('Shown live',content)
        self.assertNotIn('[!info]',content)
        self.assertNotIn('private context',content)
        self.assertEqual(self.runq('panel')['tasks'][0]['task'],'Shown live')
        self.runq('state','Q001','--from','planning','--to','done')
        self.assertEqual(self.todo.read_text(),content)
        self.assertEqual(self.runq('panel')['tasks'][0]['status'],'done')

    def test_empty_controls_view_has_no_duplicate_empty_state(self):
        self.config.write_text(json.dumps({'machine':'macbook-air','task_controls':True}))
        self.runq('view')
        self.assertIn('```ente-tasks',self.todo.read_text())
        self.assertNotIn('No tasks yet.',self.todo.read_text())
        self.assertEqual(self.runq('panel')['tasks'],[])

    def test_archived_row_disappears_from_daily_views_but_retains_history(self):
        self.runq('add','--title','Retired task','--context','Keep original context','--thread',THREAD)
        retired=self.runq('state','Q001','--from','planning','--to','archived')
        self.assertEqual(retired['status'],'archived')
        self.assertEqual(retired['context'],'Keep original context')
        self.assertEqual(retired['codex_task'],f'codex://threads/{THREAD}')
        self.assertEqual(self.runq('list'),[retired])
        self.assertEqual(self.runq('list','--all')[0]['status'],'archived')
        self.assertEqual(self.runq('panel')['tasks'],[])
        self.assertEqual(self.runq('view')['tasks'],0)
        self.assertIn('No tasks yet.',self.todo.read_text())
        self.assertNotIn('Retired task',self.todo.read_text())
        same=self.runq('add','--title','Changed title','--context','New context','--thread',THREAD)
        self.assertEqual(same,retired)
        self.assertEqual(self.runq('panel')['tasks'],[])

    def test_archived_ids_are_not_reused_and_claim_skips_retired_work(self):
        self.runq('add','--title','Retired queue item','--context','x')
        self.runq('state','Q001','--from','queued','--to','archived')
        self.assertIsNone(self.runq('claim'))
        added=self.runq('add','--title','New task','--context','y')
        self.assertEqual(added['id'],'Q002')
        self.assertEqual(self.runq('claim')['id'],'Q002')
        self.assertEqual(self.runq('list')[0]['status'],'archived')

    def test_archived_state_cannot_be_reactivated(self):
        self.runq('add','--title','Retired task','--context','x','--thread',THREAD)
        self.runq('state','Q001','--from','planning','--to','archived')
        owned=self.root/'.workflow/queues/macbook-air.md'
        before=owned.read_bytes()
        for target in QUEUE.STATES:
            if target == 'archived':
                continue
            with self.subTest(target=target):
                self.assertIn('archived',self.runq('state','Q001','--from','archived','--to',target,ok=False))
                self.assertEqual(owned.read_bytes(),before)
        self.assertEqual(self.runq('state','Q001','--from','archived','--to','archived')['status'],'archived')
        self.assertEqual(owned.read_bytes(),before)

    def test_archive_uses_observed_state_and_existing_host_and_sync_guards(self):
        self.runq('add','--title','Current task','--context','x','--thread',THREAD)
        owned=self.root/'.workflow/queues/macbook-air.md'
        before=owned.read_bytes()
        error=self.runq('state','Q001','--from','queued','--to','archived',ok=False)
        self.assertIn("expected 'queued'",error)
        self.assertEqual(owned.read_bytes(),before)
        self.config.write_text(json.dumps({'machine':'mac-mini'}))
        self.runq('state','Q001','--from','planning','--to','archived',file=owned,ok=False)
        self.assertEqual(owned.read_bytes(),before)
        self.config.write_text(json.dumps({'machine':'macbook-air'}))
        (self.root/'.workflow/sync-status.json').write_text(json.dumps({'status':'conflict'}))
        self.runq('state','Q001','--from','planning','--to','archived',ok=False)
        self.assertEqual(owned.read_bytes(),before)

if __name__=='__main__': unittest.main()
