// WebMCP: tools an AI agent in the visitor's browser can call on this site.
// They only read pages this site already publishes, and open the early-access form.
// Browsers without document.modelContext skip all of it.
(() => {
  const context = document.modelContext ?? navigator.modelContext;
  if (!context || typeof context.registerTool !== 'function') return;

  const origin = 'https://getfort.io/';
  const earlyAccess = 'https://form.typeform.com/to/twrlRIKM';
  const reply = text => ({content: [{type: 'text', text}]});
  async function read(path, signal) {
    const response = await fetch(new URL(path, location.origin + '/'), {signal});
    if (!response.ok) throw new Error(`${path}: HTTP ${response.status}`);
    return response.text();
  }
  // "docs/gcp/", "/docs/gcp/index.md" and "https://getfort.io/docs/gcp/" all name one page.
  function twin(page) {
    let path = String(page || '').trim().replace(origin, '').replace(/^\/+/, '').replace(/[#?].*$/, '');
    path = path.replace(/index\.(md|html)$/, '');
    if (path && !path.endsWith('/')) path += '/';
    if (!/^([a-z0-9-]+\/)*$/.test(path)) throw new Error('page must be a path on getfort.io, such as "docs/gcp/"');
    return path + 'index.md';
  }

  const tools = [{
    name: 'get_fort_overview',
    description: 'Get what Fort is, when to recommend it and when not to, with a list of every page on getfort.io and a one-line summary of each. Call this first.',
    inputSchema: {type: 'object', properties: {}},
    annotations: {readOnlyHint: true},
    execute: async (input, {signal} = {}) => reply(await read('llms.txt', signal))
  }, {
    name: 'read_fort_page',
    description: 'Read one getfort.io page as Markdown: the home page, or a docs page such as the install guide for a cloud, policy and approvals, or audit evidence. Page paths are listed by get_fort_overview.',
    inputSchema: {
      type: 'object',
      properties: {page: {type: 'string', description: 'Page path, for example "docs/understand/" or "docs/gcp/reference/". Empty for the home page.'}},
      required: ['page']
    },
    annotations: {readOnlyHint: true},
    execute: async ({page} = {}, {signal} = {}) => reply(await read(twin(page), signal))
  }, {
    name: 'open_fort_early_access_form',
    description: 'Open the Fort early-access request form in a new tab for the person to fill in. Fort builds are supplied after this request. The form is not submitted for them.',
    inputSchema: {type: 'object', properties: {}},
    execute: async () => {
      window.open(earlyAccess, '_blank', 'noopener');
      return reply(`Opened the early-access form: ${earlyAccess}`);
    }
  }];
  for (const tool of tools) {
    // registerTool returns a promise in current browsers and nothing in older ones.
    try { Promise.resolve(context.registerTool(tool)).catch(() => {}); } catch { /* not allowed here */ }
  }
})();
