const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const { test } = require('node:test');

function load(execFile = () => {}) {
  const notices = [];
  const context = {
    module: { exports: {} },
    require(name) {
      if (name === 'obsidian') return {
        Plugin: class {}, MarkdownRenderChild: class {},
        Notice: class { constructor(message) { notices.push(message); } },
      };
      if (name === 'node:child_process') return { execFile };
      if (name === 'node:path') return path;
      throw new Error('Unexpected dependency');
    },
  };
  vm.runInNewContext(fs.readFileSync(path.join(__dirname, 'main.js'), 'utf8') + '\nglobalThis.Panel = TaskPanel;', context);
  return { Plugin: context.module.exports, Panel: context.Panel, notices };
}

function view(Panel, queue) {
  const controls = [{ disabled: false }, { disabled: false }];
  const panel = Object.create(Panel.prototype);
  Object.assign(panel, { busy: false, queue, refreshed: false,
    containerEl: { querySelectorAll: () => controls, createEl: () => ({ remove() {} }) },
    refresh: async function(force) { this.refreshed = force; },
  });
  return { panel, controls };
}

function deferred() {
  let resolve, reject;
  const promise = new Promise((yes, no) => { resolve = yes; reject = no; });
  return { promise, resolve, reject };
}

function pollingView(Panel) {
  const firstRead = deferred(), secondRead = deferred(), mutation = deferred();
  const local = { id: 'Q001', task: 'Local task', status: 'planning', editable: true };
  const foreign = { id: 'Q002', task: 'Other Mac task', status: 'planning', editable: false };
  const data = { tasks: [local, foreign], sync: { status: 'ok' } };
  const controls = [{ disabled: false }, { disabled: true }];
  const panel = new Panel(null, {});
  panel.filter = 'active';
  panel.data = data;
  panel.last = JSON.stringify(data);
  let reads = 0, renders = 0;
  panel.queue = command => command === 'state' ? mutation.promise
    : (++reads === 1 ? firstRead.promise : secondRead.promise);
  panel.containerEl = { querySelectorAll: () => controls, createEl: () => ({ remove() {} }) };
  panel.render = function() {
    renders++;
    controls[0].disabled = false;
    controls[1].disabled = true;
  };
  return { panel, controls, local, data, firstRead, secondRead, mutation,
    reads: () => reads, renders: () => renders };
}

test('failed mutation during a pending poll forces a fresh render after that read settles', async () => {
  const { Panel, notices } = load();
  const fixture = pollingView(Panel);
  const { panel, local, data, firstRead, secondRead, mutation, controls } = fixture;
  const polling = panel.refresh();
  const updating = panel.update(local, 'done');
  mutation.reject(new Error('state changed'));
  await updating;
  assert.ok(controls.every(control => control.disabled));
  firstRead.resolve(data);
  await Promise.resolve();
  await Promise.resolve();
  assert.equal(fixture.reads(), 2, 'A skipped forced refresh must run after the pending poll');
  secondRead.resolve(data);
  await polling;
  assert.equal(fixture.renders(), 1);
  assert.equal(controls[0].disabled, false);
  assert.equal(controls[1].disabled, true);
  assert.equal(panel.filter, 'active');
  assert.equal(notices.length, 1);
});

test('a stale poll cannot repaint or re-enable controls while a mutation is pending', async () => {
  const { Panel } = load();
  const fixture = pollingView(Panel);
  const { panel, local, data, firstRead, secondRead, mutation, controls } = fixture;
  const polling = panel.refresh();
  const updating = panel.update(local, 'done');
  firstRead.resolve({ ...data, tasks: [{ ...local, status: 'blocked' }] });
  await polling;
  assert.equal(fixture.renders(), 0, 'A response started before the mutation is stale');
  assert.ok(controls.every(control => control.disabled));
  mutation.resolve();
  await Promise.resolve();
  await Promise.resolve();
  secondRead.resolve({ ...data, tasks: [{ ...local, status: 'done' }] });
  await updating;
  assert.equal(fixture.renders(), 1);
  assert.equal(panel.data.tasks[0].status, 'done');
  assert.equal(panel.filter, 'active');
});

test('status change carries the observed state and refreshes saved data', async () => {
  const { Panel } = load();
  const calls = [];
  const { panel, controls } = view(Panel, async (...args) => calls.push(args));
  await panel.update({ id: 'Q004', status: 'ready for review', editable: true }, 'done');
  assert.deepEqual(calls[0], ['state', 'Q004', '--from', 'ready for review', '--to', 'done']);
  assert.ok(controls.every(control => control.disabled));
  assert.equal(panel.refreshed, true);
  assert.equal(panel.busy, false);
});

test('a stale-state rejection is reported and refreshes instead of pretending success', async () => {
  const { Panel, notices } = load();
  const { panel } = view(Panel, async () => { throw new Error('task changed'); });
  await panel.update({ id: 'Q004', status: 'planning', editable: true }, 'done');
  assert.equal(notices.length, 1);
  assert.match(notices[0], /not saved.*task changed/);
  assert.equal(panel.refreshed, true);
  assert.equal(panel.busy, false);
});

test('foreign and duplicate submissions never invoke the mutation helper', async () => {
  const { Panel } = load();
  let calls = 0;
  const { panel } = view(Panel, async () => calls++);
  await panel.update({ id: 'Q001', status: 'planning', editable: false }, 'done');
  panel.busy = true;
  await panel.update({ id: 'Q001', status: 'planning', editable: true }, 'done');
  assert.equal(calls, 0);
});

test('helper uses a fixed executable and separate path arguments, never a shell command', async () => {
  let invocation;
  const { Panel } = load((...args) => { invocation = args; args[3](null, '{"tasks":[]}', ''); });
  const panel = Object.create(Panel.prototype);
  panel.app = { vault: { adapter: { getBasePath: () => '/tmp/workflow with spaces' } } };
  const result = await panel.queue('panel');
  assert.equal(invocation[0], '/usr/bin/python3');
  assert.deepEqual(Array.from(invocation[1]), ['-B', '/tmp/workflow with spaces/skills/ente-task-queue/scripts/queue.py', '--file', '/tmp/workflow with spaces/TODO.md', 'panel']);
  assert.equal(invocation[2].shell, undefined);
  assert.equal(result.tasks.length, 0);
});

test('code blocks outside TODO cannot activate task controls or alternate helpers', () => {
  const { Plugin } = load();
  let handler, childCount = 0;
  const plugin = new Plugin();
  plugin.registerMarkdownCodeBlockProcessor = (_language, callback) => { handler = callback; };
  plugin.onload();
  handler('/untrusted/script.py', {}, { sourcePath: 'tasks/untrusted.md', addChild: () => childCount++ });
  assert.equal(childCount, 0);
});
