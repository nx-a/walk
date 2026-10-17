import { el, Toast, confirmAction } from '../ui.js';

/** Базовый экран: загрузка данных, отрисовка, перерисовка после изменений. */
export class View {
  title = '';

  constructor(app) {
    this.app = app;
    this.api = app.api;
    this.root = el('section');
  }

  /** Загрузить данные для экрана. Переопределяется. */
  async load() {}

  /** Построить содержимое экрана (массив узлов). Переопределяется. */
  build() { return []; }

  async refresh() {
    try {
      await this.load();
      this.root.replaceChildren(...[this.build()].flat());
    } catch (err) {
      Toast.error(err.message);
    }
  }

  async mount(container) {
    container.replaceChildren(this.root);
    document.title = `${this.title} — Приют`;
    await this.refresh();
  }

  toolbar(title, ...controls) {
    return el('div', { class: 'toolbar' }, el('h1', {}, title), el('div', { class: 'filters' }, controls));
  }

  /** Выполнить изменение, показать результат и перерисовать экран. */
  async mutate(action, successMessage) {
    try {
      await action();
      if (successMessage) Toast.show(successMessage);
      await this.refresh();
    } catch (err) {
      Toast.error(err.message);
    }
  }

  async removeWithConfirm(question, action, successMessage) {
    if (confirmAction(question)) await this.mutate(action, successMessage);
  }

  table(headers, rows, emptyText) {
    if (!rows.length) return el('div', { class: 'table-wrap' }, el('div', { class: 'empty' }, emptyText));
    return el('div', { class: 'table-wrap' },
      el('table', {},
        el('thead', {}, el('tr', {}, headers.map(h => el('th', {}, h)))),
        el('tbody', {}, rows)));
  }
}
