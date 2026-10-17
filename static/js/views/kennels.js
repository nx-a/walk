import { el, FormDialog, Toast } from '../ui.js';
import { View } from './base.js';

export class KennelsView extends View {
  title = 'Будки';

  async load() {
    [this.kennels, this.dogs] = await Promise.all([this.api.kennels.list(), this.api.dogs.list()]);
  }

  build() {
    return [
      this.toolbar('Будки', el('button', { class: 'primary', onclick: () => this.openForm() }, '+ Будка')),
      this.table(['Номер', 'Занято', 'Собаки', ''], this.kennels.map(k => this.row(k)), 'Будок пока нет'),
    ];
  }

  row(k) {
    const residents = this.dogs.filter(d => d.kennel_id === k.id);
    return el('tr', {},
      el('td', {}, `№${k.number}`),
      el('td', {}, `${k.dogs_count} / ${k.capacity}`),
      el('td', {}, residents.length
        ? residents.map(d => el('span', { class: `badge status-${d.status.code}`, style: 'margin-right:4px' }, d.name))
        : '—'),
      el('td', { class: 'actions' },
        el('button', { class: 'small', onclick: () => this.openForm(k) }, 'Изменить'),
        el('button', {
          class: 'small danger',
          onclick: () => this.removeWithConfirm(`Удалить будку №${k.number}? Собаки останутся без будки.`,
            () => this.api.kennels.remove(k.id), 'Будка удалена'),
        }, 'Удалить')));
  }

  openForm(kennel = null) {
    new FormDialog({
      title: kennel ? `Будка №${kennel.number}` : 'Новая будка',
      fields: [
        { name: 'number', label: 'Номер', required: true, maxlength: 20, value: kennel?.number },
        { name: 'capacity', label: 'Вместимость', type: 'number', min: 1, max: 20, required: true,
          value: kennel?.capacity ?? 1 },
      ],
      onSubmit: async values => {
        if (kennel) await this.api.kennels.update(kennel.id, values);
        else await this.api.kennels.create(values);
        Toast.show('Сохранено');
        await this.refresh();
      },
    }).open();
  }
}
