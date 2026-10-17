import { DateFmt, FormDialog } from '../ui.js';

/** Диалог новой прогулки; используется на экранах «Собаки» и «Прогулки». */
export class WalkDialog {
  constructor(api, { dogs, helpers, dogId = '', onSaved }) {
    this.api = api;
    this.dogs = dogs;
    this.helpers = helpers;
    this.dogId = dogId;
    this.onSaved = onSaved;
  }

  open() {
    const dogOptions = this.dogs.map(d => ({
      value: d.id,
      label: d.on_walk ? `${d.name} — гуляет` : `${d.name} (${d.status.label.toLowerCase()})`,
    }));
    const helperOptions = this.helpers.map(h => ({
      value: h.id,
      label: h.on_walk ? `${h.name} — на прогулке` : h.name,
    }));

    // Поле времени с точностью до минуты: если начало не меняли, пусть сервер возьмёт точное «сейчас»,
    // иначе прогулка сразу после предыдущей пересечётся с ней на несколько секунд
    const defaultStart = DateFmt.toLocalInput();

    return new FormDialog({
      title: 'Новая прогулка',
      submitLabel: 'Сохранить',
      fields: [
        { name: 'dog_id', label: 'Собака', type: 'select', numeric: true, required: true, value: this.dogId,
          options: [{ value: '', label: '— выберите —' }, ...dogOptions] },
        { name: 'helper_id', label: 'Помощник', type: 'select', numeric: true, required: true, value: '',
          options: [{ value: '', label: '— выберите —' }, ...helperOptions] },
        { name: 'started_at', label: 'Начало', type: 'datetime-local', required: true,
          value: defaultStart },
        { name: 'ended_at', label: 'Конец', type: 'datetime-local',
          hint: 'Оставьте пустым, если прогулка только началась' },
      ],
      onSubmit: async values => {
        if (!values.ended_at && values.started_at === DateFmt.fromLocalInput(defaultStart)) {
          values.started_at = null;
        }
        const walk = await this.api.walks.create(values);
        this.onSaved?.(walk);
      },
    }).open();
  }
}
