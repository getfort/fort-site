(() => {
  const demo = document.querySelector('.warden-demo');
  const tabs = [...demo.querySelectorAll('[data-scenario]')];
  const label = document.querySelector('#decision-label');
  const reason = document.querySelector('#decision-reason');
  const outcome = document.querySelector('#request-outcome');
  const evidence = document.querySelector('#evidence-status');
  const speech = document.querySelector('#guard-speech');
  const approval = document.querySelector('.human-approval');
  const pause = document.querySelector('#warden-pause');
  const reduce = matchMedia('(prefers-reduced-motion: reduce)');
  const scenarios = {
    allow: {call:'read_logs',title:'Warden allows the request.',reason:'The policy permits this read. Only the request leaves the sandbox.'},
    ask: {call:'restart_deployment',title:'Warden asks for approval.',reason:'The restart waits for a named person. Nothing executes yet.'},
    deny: {call:'delete_namespace',title:'Warden denies the request.',reason:'Outside the agent’s policy. The request never reaches the tool.'}
  };
  let token = 0, selected = 'allow', timers = [], started = false;
  let paused = false, auto = !reduce.matches, heldAnimations = [];
  function schedule(fn, ms, id = token) {
    const timer = {fn,remaining:reduce.matches ? Math.min(ms,80) : ms,id,start:0,handle:null};
    timers.push(timer);
    arm(timer);
  }
  function arm(timer) {
    if (paused) return;
    timer.start = performance.now();
    timer.handle = setTimeout(() => {
      timers = timers.filter(item => item !== timer);
      if (timer.id === token) timer.fn();
    },timer.remaining);
  }
  function setPaused(value) {
    paused = value;
    demo.dataset.paused = String(value);
    pause.textContent = value ? 'Resume' : 'Pause';
    pause.setAttribute('aria-pressed',String(value));
    if (value) {
      timers.forEach(timer => {clearTimeout(timer.handle);timer.remaining = Math.max(0,timer.remaining-(performance.now()-timer.start));});
      heldAnimations = demo.getAnimations({subtree:true});
      heldAnimations.forEach(animation => animation.pause());
    } else {
      heldAnimations.forEach(animation => animation.play()); heldAnimations = [];
      timers.forEach(arm);
    }
  }
  function phase(value) {demo.dataset.phase = value;}
  function finish() {
    phase('returning');
    schedule(() => {
      phase('complete');
      if (auto && !reduce.matches) schedule(() => play(selected === 'allow' ? 'deny' : 'allow',false),2400);
    },1700);
  }
  function allow(human = false) {
    demo.dataset.result = 'allow';
    speech.textContent = human ? 'Approved once' : 'Allowed';
    label.textContent = human ? 'Approved. Just this once.' : scenarios.allow.title;
    reason.textContent = human ? 'A person’s one-time grant lets this exact request proceed.' : scenarios.allow.reason;
    outcome.textContent = human ? 'Approved once' : 'Allowed';
    evidence.textContent = 'Warden sends the allowed request to the tool.';
    phase('passing');
    schedule(() => {
      evidence.textContent = human ? 'Approval and allowed call recorded in the ledger.' : 'Allowed call recorded in the ledger.';
      finish();
    },2100);
  }
  function decide() {
    if (selected === 'allow') return allow();
    const scene = scenarios[selected];
    label.textContent = scene.title; reason.textContent = scene.reason;
    if (selected === 'deny') {
      demo.dataset.result = 'deny'; phase('denied');
      speech.textContent = 'Denied'; outcome.textContent = 'Denied';
      evidence.textContent = 'Denied call recorded. No action reached the tool.';
      schedule(finish,1500);
    } else {
      phase('waiting'); speech.textContent = 'Ask a person'; outcome.textContent = 'Awaiting approval';
      approval.hidden = false; evidence.textContent = 'Request held by Warden. Nothing has executed.';
    }
  }
  function play(kind,manual = true) {
    started = true;
    if (manual) auto = false;
    if (paused) setPaused(false);
    timers.forEach(timer => clearTimeout(timer.handle));timers = [];
    ++token; selected = kind;
    approval.hidden = true;demo.dataset.kind = kind;demo.dataset.result = '';
    phase('ready');
    tabs.forEach(tab => tab.setAttribute('aria-pressed',String(tab.dataset.scenario === kind)));
    document.querySelector('#request-call').textContent = scenarios[kind].call;
    document.querySelector('.request-scope').textContent = kind === 'deny' ? 'checkout' : 'checkout / api';
    label.textContent = 'An agent has a job to do.';
    reason.textContent = 'It prepares a tool request inside its sandbox.';
    outcome.textContent = 'Preparing request'; speech.textContent = 'Checking…';
    evidence.textContent = 'The agent works inside its sandbox.';
    if (reduce.matches) {decide();return;}
    schedule(() => {
      phase('working');
      schedule(() => {
        phase('travel'); label.textContent = 'The agent brings a request.';
        reason.textContent = 'Warden is the checkpoint at the sandbox boundary.';
        outcome.textContent = 'Request sent';
        schedule(() => {
          phase('checking');label.textContent = 'Warden checks your policy.';
          reason.textContent = 'This tool, this action, and these arguments.';
          outcome.textContent = 'Checking';evidence.textContent = 'Warden reads the request before anything leaves.';
          schedule(decide,1500);
        },1700);
      },1500);
    },180);
  }
  tabs.forEach(tab => tab.addEventListener('click',()=>play(tab.dataset.scenario)));
  document.querySelector('#warden-replay').addEventListener('click',()=>play(selected));
  pause.addEventListener('click',()=>setPaused(!paused));
  document.querySelector('#approve-request').addEventListener('click',()=> {
    if (demo.dataset.phase !== 'waiting') return;
    if (paused) setPaused(false);
    approval.hidden = true;allow(true);
    document.querySelector('#warden-replay').focus({preventScroll:true});
  });
  const observer = new IntersectionObserver(entries => {
    if (entries.some(entry => entry.isIntersecting)) {
      observer.disconnect();if (!started) play('allow',false);
    }
  },{threshold:.3});
  observer.observe(demo);
})();
