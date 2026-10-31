// static/js/navigation.js — раскрытие меню услуг мышью, касанием и клавиатурой.
(() => {
  const groups = [...document.querySelectorAll('.nav__group')];
  const setOpen = (group, open) => {
    group.querySelector('.nav__toggle').setAttribute('aria-expanded', String(open));
    group.querySelector('.nav__dropdown').hidden = !open;
  };
  const closeOthers = (current) => groups.forEach(group => {
    if (group !== current) setOpen(group, false);
  });
  groups.forEach(group => {
    const button = group.querySelector('.nav__toggle');
    button.addEventListener('click', () => {
      const open = button.getAttribute('aria-expanded') !== 'true';
      closeOthers(group);
      setOpen(group, open);
    });
    group.addEventListener('focusout', event => {
      if (!group.contains(event.relatedTarget)) setOpen(group, false);
    });
    group.addEventListener('keydown', event => {
      if (event.key === 'Escape') {
        setOpen(group, false);
        button.focus();
        event.stopPropagation();
      }
      if (event.key === 'ArrowDown' && event.target.closest('.nav__heading')) {
        event.preventDefault();
        closeOthers(group);
        setOpen(group, true);
        group.querySelector('.nav__dropdown a').focus();
      }
    });
  });
  document.addEventListener('click', event => {
    if (!event.target.closest('.nav__group')) closeOthers(null);
  });
})();
