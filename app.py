# -*- coding: utf-8 -*-
# ============================================================
# LAYERTECH 3D — Магазин премиальных 3D-моделей
# Весь сайт в одном файле: бэкенд + шаблоны + стили
#
# ЗАПУСК:      python app.py
# АДРЕС:       http://127.0.0.1:5000
# АДМИН:       admin / admin123
# TELEGRAM:    @managerLAYERTECH3D
# ============================================================

# --- Импорты библиотек ---
from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from datetime import datetime
import os

# --- Создаём Flask-приложение ---
app = Flask(__name__)

# Секретный ключ — нужен для работы сессий (шифрование cookie)
app.config['SECRET_KEY'] = 'layertech3d-secret-key-2025-change-me-please'

# База данных — SQLite-файл рядом с проектом
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///models.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Настройки магазина
MANAGER_TELEGRAM = "@managerLAYERTECH3D"   # Telegram менеджера
ADMIN_USERNAME = "admin"                    # Имя админа

# Инициализация БД

db = SQLAlchemy(app)

@app.context_processor
def inject_globals():
    user = User.query.get(session.get('user_id')) if session.get('user_id') else None
    cart = session.get('cart', {})
    return {
        "current_user": session.get("username"),
        "is_admin": bool(session.get("is_admin")),
        "cart_count_global": sum(cart.values()) if cart else 0,
        "manager_telegram": MANAGER_TELEGRAM,
    }



# ============================================================
# БЛОК 1: МОДЕЛИ БАЗЫ ДАННЫХ (таблицы)
# ============================================================

class User(db.Model):
    """Пользователь сайта"""
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)      # Логин
    email = db.Column(db.String(120), unique=True, nullable=False)        # Email
    password = db.Column(db.String(200), nullable=False)                  # Хеш пароля
    is_admin = db.Column(db.Boolean, default=False)                       # Админ?
    is_approved = db.Column(db.Boolean, default=False)                    # Одобрен админом?
    created_at = db.Column(db.DateTime, default=datetime.utcnow)          # Дата регистрации


class Model3D(db.Model):
    """3D-модель в каталоге"""
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)                     # Название
    description = db.Column(db.Text, nullable=False)                      # Описание
    price = db.Column(db.Float, nullable=False)                           # Цена
    category = db.Column(db.String(50), nullable=False)                   # Категория
    emoji = db.Column(db.String(10), default='🎨')                       # Иконка
    polygon = db.Column(db.String(20), default='Low-poly')                # Тип полигонов
    format = db.Column(db.String(20), default='.obj')                     # Формат файла


class Order(db.Model):
    """Заказ пользователя"""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, nullable=False)                       # Кто заказал
    username = db.Column(db.String(80))                                   # Имя
    email = db.Column(db.String(120))                                     # Email
    total = db.Column(db.Float, nullable=False)                           # Итого
    items_summary = db.Column(db.Text)                                    # Состав
    status = db.Column(db.String(20), default='new')                      # new / in_progress / done
    created_at = db.Column(db.DateTime, default=datetime.utcnow)          # Дата


# ============================================================
# БЛОК 2: ДЕКОРАТОРЫ ДОСТУПА
# ============================================================

def login_required(f):
    """Пускать только авторизованных + одобренных пользователей"""
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            flash('Сначала войдите в аккаунт', 'error')
            return redirect(url_for('login'))
        user = User.query.get(session['user_id'])
        if user and not user.is_approved and not user.is_admin:
            flash('Ваш аккаунт ещё не одобрен администратором', 'error')
            session.clear()
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated


def admin_required(f):
    """Пускать только админа"""
    @wraps(f)
    def decorated(*args, **kwargs):
        user = User.query.get(session.get('user_id'))
        if not user or not user.is_admin:
            flash('Доступ только для администратора', 'error')
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated


# ============================================================
# БЛОК 3: CSS-СТИЛИ (тёмная неоновая тема)
# ============================================================



# HTML templates are stored in templates/ and CSS/JS in static/.

def init_db():
    """Создаёт таблицы, админа и стартовые модели"""
    with app.app_context():
        db.create_all()

        # Создаём админа (если нет)
        if not User.query.filter_by(username=ADMIN_USERNAME).first():
            admin = User(
                username=ADMIN_USERNAME,
                email='admin@layertech3d.io',
                password=generate_password_hash('admin123'),
                is_admin=True,
                is_approved=True
            )
            db.session.add(admin)
            db.session.commit()
            print("✅ Админ создан: admin / admin123")

        # Заполняем каталог 8 моделями (если пусто)
        if Model3D.query.count() == 0:
            models = [
                Model3D(title='Кибер-череп', description='Детализированный футуристический череп с неоновой подсветкой. Идеален для игр и рендеров.', price=799, category='Персонажи', emoji='💀', polygon='High-poly', format='.fbx'),
                Model3D(title='Космический корабль', description='Многофункциональный шаттл с UV-развёрткой и PBR текстурами.', price=1290, category='Транспорт', emoji='🚀', polygon='Mid-poly', format='.blend'),
                Model3D(title='Неоновый меч', description='Энергетический клинок с анимированными эффектами свечения.', price=450, category='Оружие', emoji='⚔️', polygon='Low-poly', format='.obj'),
                Model3D(title='Робот-помощник', description='Дружелюбный робот, готовый к риггингу и анимации.', price=990, category='Персонажи', emoji='🤖', polygon='Mid-poly', format='.fbx'),
                Model3D(title='Город будущего', description='Модульный сет зданий для киберпанк-сцен.', price=2490, category='Окружение', emoji='🏙️', polygon='High-poly', format='.blend'),
                Model3D(title='Кристалл энергии', description='Анимированный кристалл с шейдерами свечения.', price=350, category='Эффекты', emoji='💎', polygon='Low-poly', format='.fbx'),
                Model3D(title='Дрон-разведчик', description='Компактный квадрокоптер с детализированной электроникой.', price=640, category='Транспорт', emoji='🛸', polygon='Mid-poly', format='.obj'),
                Model3D(title='Дракон-страж', description='Эпичный дракон в боевой стойке. Анатомически корректный.', price=1890, category='Существа', emoji='🐉', polygon='High-poly', format='.blend'),
            ]
            db.session.add_all(models)
            db.session.commit()
            print("✅ Каталог заполнен 8 моделями")


# ============================================================
# БЛОК 7: МАРШРУТЫ (URL-адреса сайта)
# ============================================================

@app.route('/')
def index():
    """Главная страница — каталог с поиском и фильтрами"""
    category = request.args.get('category')
    search = request.args.get('search', '').strip()

    query = Model3D.query
    if category:
        query = query.filter_by(category=category)
    if search:
        query = query.filter(Model3D.title.ilike(f'%{search}%'))
    models = query.all()

    # Список категорий
    categories = [c[0] for c in db.session.query(Model3D.category).distinct().all()]
    cart = session.get('cart', {})

    return render_template('index.html',
        models=models, categories=categories,
        cart_count=sum(cart.values()) if cart else 0,
        current_category=category, search=search)


@app.route('/model/<int:model_id>')
def model_detail(model_id):
    """Страница одной модели"""
    model = Model3D.query.get_or_404(model_id)
    cart = session.get('cart', {})
    return render_template('model_detail.html', model=model,
        cart_count=sum(cart.values()) if cart else 0)


@app.route('/register', methods=['GET', 'POST'])
def register():
    """Регистрация нового пользователя (требует одобрения админа)"""
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')

        # Проверки
        if not username or not email or not password:
            flash('Заполните все поля', 'error')
            return redirect(url_for('register'))
        if len(password) < 6:
            flash('Пароль минимум 6 символов', 'error')
            return redirect(url_for('register'))
        if User.query.filter_by(username=username).first():
            flash('Такое имя уже занято', 'error')
            return redirect(url_for('register'))
        if User.query.filter_by(email=email).first():
            flash('Email уже зарегистрирован', 'error')
            return redirect(url_for('register'))

        # Создаём пользователя (is_approved=False по умолчанию)
        user = User(username=username, email=email,
                    password=generate_password_hash(password), is_approved=False)
        db.session.add(user)
        db.session.commit()

        flash('✅ Аккаунт создан! Ожидайте одобрения администратора.', 'success')
        return redirect(url_for('login'))

    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    """Вход в систему"""
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        user = User.query.filter_by(username=username).first()

        if user and check_password_hash(user.password, password):
            # Проверка одобрения
            if not user.is_approved and not user.is_admin:
                flash('⏳ Ваш аккаунт ещё не одобрен администратором', 'error')
                return redirect(url_for('login'))

            # Сохраняем сессию
            session['user_id'] = user.id
            session['username'] = user.username
            session['is_admin'] = user.is_admin
            flash(f'С возвращением, {username}!', 'success')

            return redirect(url_for('admin_panel') if user.is_admin else url_for('index'))

        flash('Неверное имя или пароль', 'error')

    return render_template('login.html')


@app.route('/logout')
def logout():
    """Выход из аккаунта"""
    session.clear()
    flash('Вы вышли из аккаунта', 'success')
    return redirect(url_for('index'))


@app.route('/add_to_cart/<int:model_id>', methods=['POST'])
@login_required
def add_to_cart(model_id):
    """AJAX-добавление товара в корзину"""
    model = Model3D.query.get_or_404(model_id)
    cart = session.get('cart', {})
    cart[str(model_id)] = cart.get(str(model_id), 0) + 1
    session['cart'] = cart
    return jsonify({
        'success': True,
        'cart_count': sum(cart.values()),
        'message': f'«{model.title}» в корзине'
    })


@app.route('/remove_from_cart/<int:model_id>', methods=['POST'])
@login_required
def remove_from_cart(model_id):
    """Удаление товара из корзины"""
    cart = session.get('cart', {})
    if str(model_id) in cart:
        del cart[str(model_id)]
        session['cart'] = cart
    return redirect(url_for('cart'))


@app.route('/cart')
@login_required
def cart():
    """Страница корзины"""
    cart_data = session.get('cart', {})
    items = []
    total = 0
    for mid, qty in cart_data.items():
        model = Model3D.query.get(int(mid))
        if model:
            subtotal = model.price * qty
            total += subtotal
            items.append({'model': model, 'qty': qty, 'subtotal': subtotal})
    return render_template('cart.html', items=items, total=total,
        cart_count=sum(cart_data.values()), manager=MANAGER_TELEGRAM)


@app.route('/checkout', methods=['POST'])
@login_required
def checkout():
    """Оформление заказа — создаёт запись Order и показывает страницу с Telegram-менеджером"""
    user = User.query.get(session['user_id'])
    cart_data = session.get('cart', {})

    if not cart_data:
        flash('Корзина пуста', 'error')
        return redirect(url_for('cart'))

    # Собираем состав заказа
    items_list = []
    total = 0
    for mid, qty in cart_data.items():
        model = Model3D.query.get(int(mid))
        if model:
            total += model.price * qty
            items_list.append(f"{model.title} ×{qty} — {model.price * qty}₽")

    # Создаём заказ
    order = Order(user_id=user.id, username=user.username, email=user.email,
                  total=total, items_summary=" | ".join(items_list))
    db.session.add(order)
    db.session.commit()

    # Очищаем корзину
    session.pop('cart', None)

    return render_template('success.html',
        order=order, items=items_list,
        manager=MANAGER_TELEGRAM, total=total)


# ---------- АДМИН-МАРШРУТЫ ----------

@app.route('/admin')
@admin_required
def admin_panel():
    """Админ-панель со статистикой, заявками и заказами"""
    pending_users = User.query.filter_by(is_approved=False, is_admin=False).all()
    all_users = User.query.filter_by(is_admin=False).order_by(User.created_at.desc()).all()
    orders = Order.query.order_by(Order.created_at.desc()).all()

    stats = {
        'pending': len(pending_users),
        'users': User.query.filter_by(is_admin=False).count(),
        'orders': Order.query.count(),
        'models': Model3D.query.count()
    }

    return render_template('admin.html',
        pending_users=pending_users, all_users=all_users,
        orders=orders, stats=stats, manager=MANAGER_TELEGRAM)


@app.route('/admin/approve/<int:user_id>', methods=['POST'])
@admin_required
def approve_user(user_id):
    """Одобрить регистрацию пользователя"""
    user = User.query.get_or_404(user_id)
    user.is_approved = True
    db.session.commit()
    flash(f'✅ Пользователь {user.username} одобрен', 'success')
    return redirect(url_for('admin_panel'))


@app.route('/admin/reject/<int:user_id>', methods=['POST'])
@admin_required
def reject_user(user_id):
    """Удалить пользователя"""
    user = User.query.get_or_404(user_id)
    if user.is_admin:
        flash('Нельзя удалить администратора', 'error')
        return redirect(url_for('admin_panel'))
    db.session.delete(user)
    db.session.commit()
    flash('❌ Пользователь удалён', 'success')
    return redirect(url_for('admin_panel'))


@app.route('/admin/order/<int:order_id>/<status>', methods=['POST'])
@admin_required
def update_order_status(order_id, status):
    """Смена статуса заказа"""
    order = Order.query.get_or_404(order_id)
    if status in ('new', 'in_progress', 'done'):
        order.status = status
        db.session.commit()
        flash('Статус обновлён', 'success')
    return redirect(url_for('admin_panel'))


# ---------- ГЛОБАЛЬНЫЕ ПЕРЕМЕННЫЕ ДЛЯ ШАБЛОНОВ ----------

@app.context_processor
def inject_user():
    """Передаёт общие данные во все шаблоны автоматически"""
    return {
        'current_user': session.get('username'),
        'is_admin': session.get('is_admin', False),
        'cart_count_global': sum(session.get('cart', {}).values()),
        'manager_telegram': MANAGER_TELEGRAM
    }


# ============================================================
# БЛОК 8: ЗАПУСК САЙТА
# ============================================================

if __name__ == '__main__':
    init_db()  # Инициализация БД при первом запуске

    print("=" * 55)
    print("🚀 LAYERTECH 3D запущен: http://127.0.0.1:5000")
    print("👑 Админ:  admin / admin123")
    print(f"💬 Telegram: {MANAGER_TELEGRAM}")
    print("=" * 55)

    # Запуск сервера
    app.run(debug=False, host='127.0.0.1', port=5000)
