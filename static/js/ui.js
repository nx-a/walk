/**
 * Создаёт DOM-элемент. Дочерние строки вставляются как текст (без innerHTML),
 * поэтому пользовательские данные безопасны.
 */
export function el(tag, attrs = {}, ...children) {
  const node = document.createElement(tag);
  for (const [key, value] of Object.entries(attrs)) {
    if (value === undefined || value === null || value === false) continue;
    if (key.startsWith('on')) node.addEventListener(key.slice(2).toLowerCase(), value);
    else if (key === 'class') node.className = value;
    else if (key in node && typeof value !== 'string') node[key] = value;
    else node.setAttribute(key, value === true ? '' : value);
  }
  for (const child of children.flat()) {
    if (child === null || child === undefined || child === false) continue;
    node.append(child instanceof Node ? child : String(child));
  }
  return node;
}

export const DateFmt = {
  /** Date → значение для <input type="datetime-local"> в локальном времени. */
  toLocalInput(date = new Date()) {
    const d = new Date(date);
    d.setMinutes(d.getMinutes() - d.getTimezoneOffset());
    return d.toISOString().slice(0, 16);
  },
  /** Значение datetime-local (локальное) → ISO в UTC для API. */
  fromLocalInput(value) {
    return value ? new Date(value).toISOString() : null;
  },
  display(iso) {
    return iso ? new Date(iso).toLocaleString('ru-RU', { dateStyle: 'short', timeStyle: 'short' }) : '—';
  },
  duration(minutes) {
    if (minutes === null || minutes === undefined) return '—';
    const h = Math.floor(minutes / 60);
    return h ? `${h} ч ${minutes % 60} мин` : `${minutes} мин`;
  },
};

export class Toast {
  static container = null;

  static show(message, type = 'info', timeout = 3500) {
    Toast.container ??= document.getElementById('toasts');
    const node = el('div', { class: `toast ${type}` }, message);
    Toast.container.append(node);
    setTimeout(() => node.remove(), timeout);
  }

  static error(message) { Toast.show(message, 'error', 6000); }
}

/** Модальное окно; закрывается по Esc и клику по фону. */
export class Modal {
  constructor(title, content) {
    this.backdrop = el('div', { class: 'modal-backdrop', onclick: e => { if (e.target === this.backdrop) this.close(); } },
      el('div', { class: 'modal', role: 'dialog', 'aria-modal': 'true' }, el('h2', {}, title), content));
    this.onKey = e => { if (e.key === 'Escape') this.close(); };
    this.onClose = () => {};
  }

  open() {
    document.body.append(this.backdrop);
    document.addEventListener('keydown', this.onKey);
    this.backdrop.querySelector('input, select')?.focus();
  }

  close() {
    document.removeEventListener('keydown', this.onKey);
    this.backdrop.remove();
    this.onClose();
  }
}

/**
 * Форма в модальном окне по описанию полей.
 * field: {name, label, type: text|number|select|datetime-local, required, options:[{value,label}], value, hint}
 * onSubmit(values) может бросить ошибку — она показывается в форме, окно остаётся открытым.
 */
export class FormDialog {
  constructor({ title, fields, submitLabel = 'Сохранить', onSubmit }) {
    this.fields = fields;
    this.onSubmit = onSubmit;
    this.errorBox = el('div', { class: 'error' });
    this.submitBtn = el('button', { type: 'submit', class: 'primary' }, submitLabel);
    this.form = el('form', { onsubmit: e => this.submit(e) },
      fields.map(f => this.renderField(f)),
      this.errorBox,
      el('div', { class: 'buttons' },
        el('button', { type: 'button', onclick: () => this.modal.close() }, 'Отмена'),
        this.submitBtn));
    this.modal = new Modal(title, this.form);
  }

  renderField(f) {
    let input;
    if (f.type === 'select') {
      input = el('select', { name: f.name, required: f.required },
        f.options.map(o => el('option', { value: o.value, disabled: o.disabled }, o.label)));
      input.value = f.value ?? '';
    } else {
      input = el('input', {
        name: f.name, type: f.type ?? 'text', required: f.required,
        min: f.min, max: f.max, maxlength: f.maxlength, placeholder: f.placeholder,
      });
      input.value = f.value ?? '';
    }
    return el('label', {}, f.label, input, f.hint && el('span', { class: 'hint' }, f.hint));
  }

  values() {
    const data = new FormData(this.form);
    const result = {};
    for (const f of this.fields) {
      const raw = String(data.get(f.name) ?? '').trim();
      if (f.type === 'number' || f.numeric) result[f.name] = raw === '' ? null : Number(raw);
      else if (f.type === 'datetime-local') result[f.name] = DateFmt.fromLocalInput(raw);
      else result[f.name] = raw;
    }
    return result;
  }

  async submit(event) {
    event.preventDefault();
    this.submitBtn.disabled = true;
    this.errorBox.textContent = '';
    try {
      await this.onSubmit(this.values());
      this.modal.close();
    } catch (err) {
      this.errorBox.textContent = err.message;
    } finally {
      this.submitBtn.disabled = false;
    }
  }

  open() { this.modal.open(); return this; }
}

export function confirmAction(message) {
  return window.confirm(message);
}
