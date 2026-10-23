// Hero demo: sre-agent walks its tool calls to the gate and Warden decides each one.
// Allow opens the gate, ask waits for the visitor to approve as Sara, deny bounces it back.
(() => {
  const courier = document.getElementById('courier');
  if (!courier) return;

  const facing = document.getElementById('facing');
  const gate = document.getElementById('portcullis');
  const bell = document.getElementById('bell');
  const bubble = document.getElementById('bubble');
  const bubbleText = document.getElementById('bubble-text');
  const feed = document.getElementById('decisions');
  const approval = document.getElementById('approval');
  const approve = document.getElementById('approve');
  const status = document.getElementById('run-status');
  const replay = document.getElementById('replay');

  const reduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  const HOME = 116, GATE = 411, OUT = 470, GROUND = 262;
  const PX_PER_SEC = 190;

  let runId = 0;
  let x = HOME;

  class Aborted extends Error {}
  const live = (id) => { if (id !== runId) throw new Aborted(); };
  const sleep = (ms, id) => new Promise((r) => setTimeout(r, reduced ? Math.min(ms, 150) : ms)).then(() => live(id));

  async function walk(to, id) {
    const secs = Math.abs(to - x) / PX_PER_SEC;
    facing.setAttribute('transform', to < x ? 'scale(-1 1)' : '');
    courier.style.setProperty('--walk', `${secs}s`);
    courier.classList.add('walking');
    courier.style.transform = `translate(${to}px, ${GROUND}px)`;
    x = to;
    await sleep(secs * 1000, id);
    courier.classList.remove('walking');
  }

  function say(text, kind) {
    bubbleText.textContent = text;
    bubble.setAttribute('class', `bubble show ${kind}`);
  }
  const hush = () => bubble.setAttribute('class', 'bubble');

  function record(verdict, call, why) {
    const li = document.createElement('li');
    li.className = 'decision';
    li.innerHTML = `<span class="verdict ${verdict}">${verdict}</span><span class="call"></span><span class="why"></span>`;
    li.querySelector('.call').textContent = call;
    li.querySelector('.why').textContent = why;
    feed.append(li);
  }

  function waitForApproval(id) {
    return new Promise((resolve, reject) => {
      approval.hidden = false;
      const onClick = () => { approval.hidden = true; resolve(); };
      approve.addEventListener('click', onClick, { once: true });
      // A replay while waiting abandons this run.
      replay.addEventListener('click', () => {
        approve.removeEventListener('click', onClick);
        reject(new Aborted());
      }, { once: true });
    }).then(() => live(id));
  }

  // Through the open gate to the tool servers and back with the result.
  async function fetchThroughGate(id) {
    gate.classList.add('open');
    await sleep(500, id);
    hush();
    await walk(OUT, id);
    courier.dataset.carry = 'scroll';
    await sleep(500, id);
    await walk(GATE - 40, id);
    gate.classList.remove('open');
    await walk(HOME, id);
    facing.setAttribute('transform', '');
    courier.dataset.carry = '';
  }

  async function run() {
    const id = ++runId;
    reset();
    try {
      await sleep(900, id);

      status.textContent = 'sre-agent reads the checkout logs';
      courier.dataset.carry = 'letter';
      await walk(GATE, id);
      say('Allowed', 'allow');
      record('allow', 'get_logs  namespace=checkout', 'rule ops-read#reads');
      await fetchThroughGate(id);
      await sleep(600, id);

      status.textContent = 'sre-agent wants to restart the api';
      courier.dataset.carry = 'letter';
      await walk(GATE, id);
      say('Asking Sara…', 'ask');
      bell.classList.add('ringing');
      record('ask', 'restart_deployment  checkout/api', 'held for approval · rule sre-agent#remediation');
      status.textContent = 'Warden is waiting for Sara. You are Sara.';
      replay.hidden = false;
      await waitForApproval(id);
      bell.classList.remove('ringing');
      say('Approved, once', 'allow');
      record('allow', 'restart_deployment  checkout/api', 'retry with Sara’s grant · step-up confirmed');
      status.textContent = 'Sara signed in again and approved this exact call, once';
      await fetchThroughGate(id);
      await sleep(600, id);

      status.textContent = 'sre-agent tries to delete the deployment';
      courier.dataset.carry = 'letter';
      await walk(GATE, id);
      say('Denied', 'deny');
      record('deny', 'delete_deployment  checkout/api', 'not a declared tool');
      courier.classList.add('bounce');
      await sleep(1000, id);
      courier.classList.remove('bounce');
      hush();
      await walk(HOME, id);
      facing.setAttribute('transform', '');
      courier.dataset.carry = '';

      status.textContent = 'Ledger: 4 entries, chain intact';
      status.classList.add('done');
      replay.hidden = false;
    } catch (err) {
      if (!(err instanceof Aborted)) throw err;
    }
  }

  function reset() {
    feed.replaceChildren();
    approval.hidden = true;
    replay.hidden = true;
    status.classList.remove('done');
    status.textContent = 'Starting…';
    bell.classList.remove('ringing');
    gate.classList.remove('open');
    courier.classList.remove('walking', 'bounce');
    courier.dataset.carry = '';
    facing.setAttribute('transform', '');
    courier.style.setProperty('--walk', '0s');
    courier.style.transform = `translate(${HOME}px, ${GROUND}px)`;
    x = HOME;
    hush();
  }

  replay.addEventListener('click', run);

  // Start when the demo is on screen, once.
  const demo = document.querySelector('.demo');
  const io = new IntersectionObserver((entries) => {
    if (entries.some((e) => e.isIntersecting)) {
      io.disconnect();
      run();
    }
  }, { threshold: 0.35 });
  io.observe(demo);
})();
