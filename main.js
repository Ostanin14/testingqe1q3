// Автоскрытие flash-сообщений через 4 секунды
setTimeout(() => {
  document.querySelectorAll('.flash').forEach(el => {
    el.style.opacity = '0';
    setTimeout(() => el.remove(), 400);
  });
}, 4000);

// AJAX-добавление товара в корзину (без перезагрузки страницы)
document.querySelectorAll('.add-to-cart-btn').forEach(btn => {
  btn.addEventListener('click', async (e) => {
    e.preventDefault();
    e.stopPropagation();
    const id = btn.dataset.id;
    try {
      const res = await fetch('/add_to_cart/' + id, { method: 'POST' });
      const data = await res.json();
      if (data.success) {
        showToast(data.message);
        // Обновляем счётчик на иконке корзины
        const badge = document.querySelector('.cart-badge');
        if (badge) badge.textContent = data.cart_count;
        else {
          const cl = document.querySelector('.cart-link');
          if (cl) {
            const s = document.createElement('span');
            s.className = 'cart-badge';
            s.textContent = data.cart_count;
            cl.appendChild(s);
          }
        }
      }
    } catch (err) {
      showToast('Сначала войдите в аккаунт', 'error');
      setTimeout(() => window.location.href = '/login', 1200);
    }
  });
});

// Всплывающее уведомление снизу
function showToast(text, type) {
  type = type || 'success';
  const t = document.createElement('div');
  t.className = 'toast toast-' + type;
  t.textContent = text;
  document.body.appendChild(t);
  setTimeout(() => t.classList.add('show'), 10);
  setTimeout(() => {
    t.classList.remove('show');
    setTimeout(() => t.remove(), 400);
  }, 2800);
}
