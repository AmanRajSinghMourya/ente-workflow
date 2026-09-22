const { Plugin, MarkdownRenderChild, Notice } = require('obsidian');
const { execFile } = require('node:child_process');
const path = require('node:path');

const LABELS = {
  queued: 'Queued', starting: 'Starting', planning: 'Planning',
  'needs decision': 'Needs you', implementing: 'In progress',
  'ready for review': 'Review', done: 'Done', deferred: 'Later', blocked: 'Blocked',
};

module.exports = class TaskControls extends Plugin {
  onload() {
    this.registerMarkdownCodeBlockProcessor('ente-tasks', (_source, element, context) => {
      if (context.sourcePath !== 'TODO.md') return;
      context.addChild(new TaskPanel(element, this.app));
    });
  }
};

class TaskPanel extends MarkdownRenderChild {
  constructor(element, app) {
    super(element);
    this.app = app;
    this.filter = 'all';
    this.last = '';
    this.busy = false;
    this.loading = false;
    this.pendingRefresh = false;
    this.revision = 0;
  }

  onload() {
    this.containerEl.classList.add('ente-task-panel');
    this.refresh();
    this.registerInterval(window.setInterval(() => this.refresh(), 5000));
  }

  async refresh(force = false) {
    if (force) this.pendingRefresh = true;
    if (this.loading || this.busy) return;
    this.loading = true;
    const revision = this.revision;
    const forceRender = this.pendingRefresh;
    this.pendingRefresh = false;
    try {
      const data = await this.queue('panel');
      if (this.busy || revision !== this.revision) return;
      const current = JSON.stringify({ ...data, sync: { status: data.sync.status } });
      if (forceRender || current !== this.last) {
        this.data = data;
        this.last = current;
        this.render();
      }
    } catch (error) {
      if (this.busy || revision !== this.revision) return;
      this.containerEl.replaceChildren();
      this.containerEl.createEl('p', { text: 'Could not load tasks. ' + error.message });
      this.last = '';
    } finally {
      this.loading = false;
      if (this.pendingRefresh && !this.busy) await this.refresh();
    }
  }

  render() {
    const element = this.containerEl;
    element.replaceChildren();
    const tasks = this.data.tasks;
    const top = element.createDiv({ cls: 'ente-task-heading' });
    top.createEl('h1', { text: 'Tasks' });
    top.createSpan({ cls: 'ente-task-count', text: String(tasks.length) });
    const navigation = element.createDiv({ cls: 'ente-task-filters', attr: { 'aria-label': 'Filter tasks' } });
    for (const [key, label] of [['all', 'All'], ['active', 'Active'], ['attention', 'Needs you'], ['done', 'Done']]) {
      const count = tasks.filter(task => matches(task, key)).length;
      const button = navigation.createEl('button', {
        text: label + ' ' + count, cls: this.filter === key ? 'is-selected' : '',
        attr: { 'aria-pressed': String(this.filter === key) },
      });
      button.onclick = () => { this.filter = key; this.render(); };
    }
    if (this.data.sync.status === 'pending' || this.data.sync.status === 'conflict') {
      element.createEl('p', { cls: 'ente-task-sync-warning', text: this.data.sync.status === 'conflict'
        ? 'Sync needs attention. Both versions are saved; ask the workflow chat to resolve the conflict.'
        : 'Sync is waiting. Your changes are saved on this Mac.' });
    }
    const list = element.createDiv({ cls: 'ente-task-list', attr: { role: 'list' } });
    const selected = tasks.filter(task => matches(task, this.filter));
    for (const task of selected) this.row(list, task);
    if (!selected.length) list.createEl('p', { cls: 'ente-task-empty', text: this.filter === 'all' ? 'Give Codex a task to get started.' : 'No tasks here.' });
  }

  row(list, task) {
    const row = list.createDiv({ cls: 'ente-task-row', attr: { role: 'listitem' } });
    const waiting = this.data.sync.status === 'conflict' || !task.editable || task.status === 'starting';
    const reason = this.data.sync.status === 'conflict' ? 'Resolve the sync conflict first.'
      : !task.editable ? 'Update this task in its chat on ' + task.machine_label + '.'
      : task.status === 'starting' ? 'The task chat is being created.' : '';
    const checkbox = row.createEl('input', { type: 'checkbox', cls: 'ente-task-checkbox' });
    checkbox.checked = task.status === 'done';
    checkbox.disabled = waiting || !task.codex_task;
    checkbox.setAttribute('aria-label', (checkbox.checked ? 'Reopen for review: ' : 'Mark done: ') + task.task);
    checkbox.title = reason || (!task.codex_task ? 'Available once this task has a chat.'
      : checkbox.checked ? 'Reopen for review' : 'Mark done');
    checkbox.onchange = () => this.update(task, checkbox.checked ? 'done' : 'ready for review');
    const content = row.createDiv({ cls: 'ente-task-content' });
    content.createDiv({ cls: 'ente-task-title', text: task.task });
    const meta = content.createDiv({ cls: 'ente-task-meta' });
    meta.createSpan({ cls: 'ente-machine-chip', text: task.machine_label });
    for (const link of task.links) {
      const anchor = meta.createEl('a', { text: link.label, href: link.url });
      if (!/^(codex:\/\/threads\/|https:\/\/github\.com\/)/.test(link.url)) {
        anchor.onclick = event => { event.preventDefault(); this.app.workspace.openLinkText(link.url, 'TODO.md', false); };
      }
    }
    const status = row.createEl('select', {
      cls: 'ente-status-chip status-' + task.status.replaceAll(' ', '-'),
      attr: { 'aria-label': 'Status: ' + task.task },
    });
    const options = new Set([task.status, 'deferred', 'blocked']);
    if (task.codex_task) for (const value of ['needs decision', 'ready for review', 'done']) options.add(value);
    for (const value of options) status.createEl('option', { value, text: LABELS[value] });
    status.value = task.status;
    status.disabled = waiting;
    status.title = reason || 'Change list status. This does not approve code changes or start work.';
    status.onchange = () => this.update(task, status.value);
  }

  async update(task, target) {
    if (this.busy || !task.editable || target === task.status) return;
    this.busy = true;
    this.revision++;
    for (const control of this.containerEl.querySelectorAll('input, select, button')) control.disabled = true;
    const progress = this.containerEl.createEl('p', { cls: 'ente-task-saving', text: 'Saving…', attr: { role: 'status' } });
    try {
      await this.queue('state', task.id, '--from', task.status, '--to', target);
    } catch (error) {
      new Notice('Status was not saved. ' + error.message, 7000);
    } finally {
      progress.remove();
      this.busy = false;
      await this.refresh(true);
    }
  }

  queue(...args) {
    const root = this.app.vault.adapter.getBasePath();
    const helper = path.join(root, 'skills/ente-task-queue/scripts/queue.py');
    return new Promise((resolve, reject) => {
      execFile('/usr/bin/python3', ['-B', helper, '--file', path.join(root, 'TODO.md'), ...args],
        { timeout: 30000, maxBuffer: 2 * 1024 * 1024 }, (error, stdout, stderr) => {
          if (error) return reject(new Error(stderr.startsWith('queue:') ? stderr.trim().slice(7) : 'The task helper is unavailable or busy.'));
          try { resolve(JSON.parse(stdout)); } catch { reject(new Error('The task helper returned an unreadable response.')); }
        });
    });
  }
}

function matches(task, filter) {
  if (filter === 'attention') return ['needs decision', 'blocked'].includes(task.status);
  if (filter === 'active') return !['done', 'deferred'].includes(task.status);
  if (filter === 'done') return task.status === 'done';
  return true;
}
