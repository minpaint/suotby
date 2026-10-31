// static/js/metrika.js — подключение Яндекс.Метрики без инлайн-скрипта (совместимо с CSP)
// Номер счётчика берётся из data-id тега <script> (настройка YANDEX_METRIKA_ID в .env)
(function () {
  var tag = document.currentScript;
  var id = tag && tag.getAttribute("data-id");
  if (!id) return;
  window.ym = window.ym || function () { (window.ym.a = window.ym.a || []).push(arguments); };
  window.ym.l = Date.now();
  var s = document.createElement("script");
  s.async = true;
  s.src = "https://mc.yandex.ru/metrika/tag.js";
  document.head.appendChild(s);
  window.ym(Number(id), "init", { clickmap: true, trackLinks: true, accurateTrackBounce: true });
})();
