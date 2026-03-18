// TaskMarket — Main JS

document.addEventListener('DOMContentLoaded', () => {
  // ── Auto-dismiss messages ──
  document.querySelectorAll('.message').forEach(msg => {
    setTimeout(() => msg.remove(), 6000);
  });

  // ── Animate stat counters ──
  document.querySelectorAll('[data-count]').forEach(el => {
    const target = parseFloat(el.dataset.count);
    const prefix = el.dataset.prefix || '';
    const suffix = el.dataset.suffix || '';
    const duration = 1400;
    const start = performance.now();
    const isFloat = el.dataset.float === 'true';

    const tick = (now) => {
      const elapsed = now - start;
      const progress = Math.min(elapsed / duration, 1);
      const eased = 1 - Math.pow(1 - progress, 3);
      const current = target * eased;
      el.textContent = prefix + (isFloat ? current.toFixed(1) : Math.round(current).toLocaleString()) + suffix;
      if (progress < 1) requestAnimationFrame(tick);
    };

    requestAnimationFrame(tick);
  });

  // ── Progress bars (animate width) ──
  document.querySelectorAll('.progress-fill[data-width]').forEach(bar => {
    const width = bar.dataset.width;
    setTimeout(() => { bar.style.width = width + '%'; }, 100);
  });

  // ── Confirm dangerous actions ──
  document.querySelectorAll('[data-confirm]').forEach(el => {
    el.addEventListener('click', (e) => {
      if (!confirm(el.dataset.confirm)) e.preventDefault();
    });
  });

  // ── Character count for textareas ──
  document.querySelectorAll('textarea[data-minlength]').forEach(ta => {
    const min = parseInt(ta.dataset.minlength);
    const countEl = document.createElement('div');
    countEl.className = 'char-count text-xs text-muted mt-8';
    ta.parentNode.insertBefore(countEl, ta.nextSibling);

    const update = () => {
      const len = ta.value.length;
      countEl.textContent = `${len} chars ${len < min ? `(${min - len} more needed)` : '✓'}`;
      countEl.style.color = len >= min ? 'var(--green)' : 'var(--text-3)';
    };
    ta.addEventListener('input', update);
    update();
  });

  // ── Role selector (show company name field) ──
  const roleInputs = document.querySelectorAll('input[name="role"]');
  const companyNameGroup = document.getElementById('company-name-group');

  if (roleInputs.length && companyNameGroup) {
    const toggle = () => {
      const selected = document.querySelector('input[name="role"]:checked');
      companyNameGroup.style.display = selected && selected.value === 'company' ? 'block' : 'none';
    };
    roleInputs.forEach(r => r.addEventListener('change', toggle));
    toggle();
  }

  // ── Submission form toggle ──
  const submitBtn = document.getElementById('show-submit-form');
  const submitForm = document.getElementById('submit-form');
  if (submitBtn && submitForm) {
    submitBtn.addEventListener('click', () => {
      submitForm.style.display = submitForm.style.display === 'none' ? 'block' : 'none';
      submitBtn.style.display = 'none';
    });
  }

  // ── Tab system ──
  document.querySelectorAll('.tabs').forEach(tabGroup => {
    const buttons = tabGroup.querySelectorAll('.tab-btn');
    const panels = document.querySelectorAll('.tab-panel');

    buttons.forEach(btn => {
      btn.addEventListener('click', () => {
        buttons.forEach(b => b.classList.remove('tab-btn--active'));
        panels.forEach(p => p.style.display = 'none');
        btn.classList.add('tab-btn--active');
        const target = document.getElementById(btn.dataset.tab);
        if (target) target.style.display = 'block';
      });
    });

    // activate first
    if (buttons[0]) buttons[0].click();
  });
});
