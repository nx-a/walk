import { ApiClient } from './api.js';
import { DogsView } from './views/dogs.js';
import { HelpersView } from './views/helpers.js';
import { KennelsView } from './views/kennels.js';
import { WalksView } from './views/walks.js';

/** Hash-роутер: #/route?param=value */
class Router {
  constructor(routes, defaultRoute, onChange) {
    this.routes = routes;
    this.defaultRoute = defaultRoute;
    this.onChange = onChange;
    window.addEventListener('hashchange', () => this.resolve());
  }

  parse() {
    const [path, query = ''] = location.hash.replace(/^#\/?/, '').split('?');
    const name = path in this.routes ? path : this.defaultRoute;
    return { name, params: Object.fromEntries(new URLSearchParams(query)) };
  }

  static hash(name, params = {}) {
    const query = new URLSearchParams(Object.entries(params).filter(([, v]) => v !== '' && v != null)).toString();
    return `#/${name}${query ? `?${query}` : ''}`;
  }

  go(name, params) { location.hash = Router.hash(name, params); }

  /** Обновить параметры в адресе без перерисовки экрана. */
  replaceParams(params) {
    history.replaceState(null, '', Router.hash(this.parse().name, params));
  }

  resolve() {
    this.onChange(this.parse().name);
  }
}

class App {
  constructor() {
    this.api = new ApiClient();
    this.viewContainer = document.getElementById('view');
    this.nav = document.getElementById('nav');
    this.router = new Router(
      { dogs: DogsView, walks: WalksView, kennels: KennelsView, helpers: HelpersView },
      'dogs',
      name => this.show(name),
    );
  }

  show(name) {
    const { params } = this.router.parse();
    const ViewClass = this.router.routes[name];
    this.view = new ViewClass(this, params);
    for (const link of this.nav.querySelectorAll('a')) {
      link.classList.toggle('active', link.dataset.route === name);
    }
    this.view.mount(this.viewContainer);
  }

  start() {
    this.router.resolve();
  }
}

new App().start();
