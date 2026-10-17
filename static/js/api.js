export class ApiError extends Error {
  constructor(status, message) {
    super(message);
    this.status = status;
  }
}

/** Тонкий клиент REST API; ресурсы — отдельные объекты с единым интерфейсом. */
export class ApiClient {
  constructor(baseUrl = '/api') {
    this.baseUrl = baseUrl;
    this.kennels = new Resource(this, 'kennels');
    this.dogs = new Resource(this, 'dogs');
    this.helpers = new Resource(this, 'helpers');
    this.walks = new WalksResource(this, 'walks');
  }

  async request(method, path, body) {
    const options = { method, headers: {} };
    if (body !== undefined) {
      options.headers['Content-Type'] = 'application/json';
      options.body = JSON.stringify(body);
    }
    const response = await fetch(this.baseUrl + path, options);
    if (response.status === 204) return null;
    const data = await response.json().catch(() => null);
    if (!response.ok) throw new ApiError(response.status, ApiClient.errorMessage(data, response));
    return data;
  }

  static errorMessage(data, response) {
    const detail = data?.detail;
    if (typeof detail === 'string') return detail;
    if (Array.isArray(detail)) {
      // Ошибки валидации FastAPI: [{loc, msg}, ...]
      return detail.map(e => `${e.loc?.slice(1).join('.') || ''}: ${e.msg}`).join('; ');
    }
    return `Ошибка ${response.status}`;
  }
}

class Resource {
  constructor(client, name) {
    this.client = client;
    this.path = `/${name}`;
  }

  list(params = {}) {
    const query = new URLSearchParams(
      Object.entries(params).filter(([, v]) => v !== '' && v !== null && v !== undefined)
    ).toString();
    return this.client.request('GET', this.path + (query ? `?${query}` : ''));
  }

  get(id) { return this.client.request('GET', `${this.path}/${id}`); }
  create(data) { return this.client.request('POST', this.path, data); }
  update(id, data) { return this.client.request('PUT', `${this.path}/${id}`, data); }
  remove(id) { return this.client.request('DELETE', `${this.path}/${id}`); }
}

class WalksResource extends Resource {
  finish(id, endedAt = null) {
    return this.client.request('POST', `${this.path}/${id}/finish`, { ended_at: endedAt });
  }
}
