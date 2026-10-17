import { el, FormDialog, Toast } from '../ui.js';
import { View } from './base.js';
import { WalkDialog } from './walk-dialog.js';

const STATUSES = [
  { code: 'not_walked', label: 'Не выгулена' },
  { code: 'walked_once', label: 'Был выгул' },
  { code: 'walked', label: 'Погуляла' },
];

export class DogsView extends View {
  title = 'Собаки';
  filter = null; // код статуса или null

  async load() {
    [this.dogs, this.kennels, this.helpers] = await Promise.all([
      this.api.dogs.list(), this.api.kennels.list(), this.api.helpers.list(),
    ]);
  }

  build() {
    const visible = this.filter ? this.dogs.filter(d => d.status.code === this.filter) : this.dogs;
    return [
      this.toolbar('Собаки', el('button', { class: 'primary', onclick: () => this.openForm() }, '+ Собака')),
      this.legend(),
      visible.length
        ? el('div', { class: 'grid' }, visible.map(d => this.card(d)))
        : el('div', { class: 'empty' }, this.dogs.length ? 'Нет собак с таким статусом' : 'Собак пока нет — добавьте первую'),
    ];
  }

  legend() {
    const count = code => this.dogs.filter(d => d.status.code === code).length;
    const item = (code, label, n) => el('div', {
      class: `legend-item ${this.filter === code ? 'active' : ''}`,
      onclick: () => { this.filter = this.filter === code ? null : code; this.refresh(); },
    }, el('span', { class: `dot status-${code}` }), label, el('b', {}, n));
    return el('div', { class: 'legend' },
      item(null, 'Все', this.dogs.length),
      STATUSES.map(s => item(s.code, s.label, count(s.code))));
  }

  card(dog) {
    const details = [dog.breed, dog.age !== null ? `${dog.age} г.` : null].filter(Boolean).join(', ');
    return el('article', { class: `card status-${dog.status.code}` },
      el('h3', {}, dog.name),
      el('span', { class: 'badge' }, `${dog.status.label} · ${dog.walks_count}`),
      dog.on_walk && el('span', { class: 'badge on-walk' }, 'Сейчас на прогулке'),
      el('div', { class: 'meta' }, details || 'Порода не указана'),
      el('div', { class: 'meta' }, dog.kennel_number ? `Будка №${dog.kennel_number}` : 'Без будки'),
      el('div', { class: 'actions' },
        el('button', { class: 'small primary', disabled: dog.on_walk, onclick: () => this.startWalk(dog) }, 'Выгулять'),
        el('button', { class: 'small', onclick: () => this.app.router.go('walks', { dog_id: dog.id }) }, 'История'),
        el('button', { class: 'small', onclick: () => this.openForm(dog) }, 'Изменить'),
        el('button', {
          class: 'small danger',
          onclick: () => this.removeWithConfirm(`Удалить ${dog.name}?`, () => this.api.dogs.remove(dog.id), 'Собака удалена'),
        }, 'Удалить')));
  }

  startWalk(dog) {
    if (!this.helpers.length) {
      Toast.error('Сначала добавьте помощника');
      return;
    }
    new WalkDialog(this.api, {
      dogs: this.dogs, helpers: this.helpers, dogId: dog.id,
      onSaved: walk => { Toast.show(`${walk.dog_name} гуляет с ${walk.helper_name}`); this.refresh(); },
    }).open();
  }

  openForm(dog = null) {
    const kennelOptions = this.kennels.map(k => ({
      value: k.id,
      label: `№${k.number} (${k.dogs_count}/${k.capacity})`,
      disabled: k.free_places === 0 && k.id !== dog?.kennel_id,
    }));
    new FormDialog({
      title: dog ? `Изменить: ${dog.name}` : 'Новая собака',
      fields: [
        { name: 'name', label: 'Кличка', required: true, maxlength: 100, value: dog?.name },
        { name: 'breed', label: 'Порода', maxlength: 100, value: dog?.breed },
        { name: 'age', label: 'Возраст, лет', type: 'number', min: 0, max: 30, value: dog?.age },
        { name: 'kennel_id', label: 'Будка', type: 'select', numeric: true, value: dog?.kennel_id ?? '',
          options: [{ value: '', label: '— без будки —' }, ...kennelOptions] },
      ],
      onSubmit: async values => {
        if (dog) await this.api.dogs.update(dog.id, values);
        else await this.api.dogs.create(values);
        Toast.show(dog ? 'Сохранено' : 'Собака добавлена');
        await this.refresh();
      },
    }).open();
  }
}
