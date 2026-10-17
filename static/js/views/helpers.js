import { el, FormDialog, Toast } from '../ui.js';
import { View } from './base.js';

export class HelpersView extends View {
  title = 'Помощники';

  async load() {
    this.helpers = await this.api.helpers.list();
  }

  build() {
    return [
      this.toolbar('Помощники', el('button', { class: 'primary', onclick: () => this.openForm() }, '+ Помощник')),
      this.table(['Имя', 'Телефон', 'Прогулок', 'Статус', ''], this.helpers.map(h => this.row(h)), 'Помощников пока нет'),
    ];
  }

  row(h) {
    return el('tr', {},
      el('td', {}, h.name),
      el('td', {}, h.phone || '—'),
      el('td', {}, h.walks_count),
      el('td', {}, h.on_walk ? el('span', { class: 'badge on-walk' }, 'На прогулке') : 'Свободен'),
      el('td', { class: 'actions' },
        el('button', { class: 'small', onclick: () => this.app.router.go('walks', { helper_id: h.id }) }, 'Прогулки'),
        el('button', { class: 'small', onclick: () => this.openForm(h) }, 'Изменить'),
        el('button', {
          class: 'small danger',
          onclick: () => this.removeWithConfirm(`Удалить ${h.name}?`, () => this.api.helpers.remove(h.id), 'Помощник удалён'),
        }, 'Удалить')));
  }

  openForm(helper = null) {
    new FormDialog({
      title: helper ? `Изменить: ${helper.name}` : 'Новый помощник',
      fields: [
        { name: 'name', label: 'Имя', required: true, maxlength: 100, value: helper?.name },
        { name: 'phone', label: 'Телефон', type: 'tel', maxlength: 30, value: helper?.phone },
      ],
      onSubmit: async values => {
        if (helper) await this.api.helpers.update(helper.id, values);
        else await this.api.helpers.create(values);
        Toast.show('Сохранено');
        await this.refresh();
      },
    }).open();
  }
}
