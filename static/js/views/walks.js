import { DateFmt, el, Toast } from '../ui.js';
import { View } from './base.js';
import { WalkDialog } from './walk-dialog.js';

export class WalksView extends View {
  title = 'Прогулки';

  constructor(app, params = {}) {
    super(app);
    this.filters = { dog_id: params.dog_id ?? '', helper_id: params.helper_id ?? '' };
  }

  async load() {
    [this.walks, this.dogs, this.helpers] = await Promise.all([
      this.api.walks.list(this.filters), this.api.dogs.list(), this.api.helpers.list(),
    ]);
  }

  build() {
    const active = this.walks.filter(w => w.is_active);
    const finished = this.walks.filter(w => !w.is_active);
    return [
      this.toolbar('Прогулки',
        this.filterSelect('dog_id', 'Все собаки', this.dogs),
        this.filterSelect('helper_id', 'Все помощники', this.helpers),
        el('button', { class: 'primary', onclick: () => this.openForm() }, '+ Прогулка')),
      el('div', { class: 'section-title' }, `Сейчас гуляют (${active.length})`),
      this.table(['Собака', 'Помощник', 'Начало', ''], active.map(w => this.activeRow(w)), 'Никто не гуляет'),
      el('div', { class: 'section-title' }, `История (${finished.length})`),
      this.table(['Собака', 'Помощник', 'Начало', 'Конец', 'Длительность', ''],
        finished.map(w => this.finishedRow(w)), 'Завершённых прогулок нет'),
    ];
  }

  filterSelect(name, allLabel, items) {
    const select = el('select', {
      onchange: e => {
        this.filters[name] = e.target.value;
        this.app.router.replaceParams(this.filters);
        this.refresh();
      },
    }, el('option', { value: '' }, allLabel), items.map(i => el('option', { value: i.id }, i.name)));
    select.value = String(this.filters[name]);
    return select;
  }

  activeRow(w) {
    return el('tr', { class: 'active-walk' },
      el('td', {}, w.dog_name), el('td', {}, w.helper_name), el('td', {}, DateFmt.display(w.started_at)),
      el('td', { class: 'actions' },
        el('button', { class: 'small primary', onclick: () => this.finish(w) }, 'Завершить'),
        this.deleteButton(w)));
  }

  finishedRow(w) {
    return el('tr', {},
      el('td', {}, w.dog_name), el('td', {}, w.helper_name),
      el('td', {}, DateFmt.display(w.started_at)), el('td', {}, DateFmt.display(w.ended_at)),
      el('td', {}, DateFmt.duration(w.duration_minutes)),
      el('td', { class: 'actions' }, this.deleteButton(w)));
  }

  deleteButton(w) {
    return el('button', {
      class: 'small danger',
      onclick: () => this.removeWithConfirm(`Удалить прогулку ${w.dog_name}?`, () => this.api.walks.remove(w.id), 'Прогулка удалена'),
    }, 'Удалить');
  }

  finish(walk) {
    this.mutate(() => this.api.walks.finish(walk.id), `${walk.dog_name} вернулась с прогулки`);
  }

  openForm() {
    if (!this.dogs.length || !this.helpers.length) {
      Toast.error('Нужны хотя бы одна собака и один помощник');
      return;
    }
    new WalkDialog(this.api, {
      dogs: this.dogs, helpers: this.helpers, dogId: this.filters.dog_id,
      onSaved: () => { Toast.show('Прогулка добавлена'); this.refresh(); },
    }).open();
  }
}
