import logging
import sqlite3
import requests
from bs4 import BeautifulSoup
import re
import json
from datetime import datetime, time as dt_time
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters, ConversationHandler

# Настройка логирования для отслеживания работы бота
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Константы для состояний диалога
AWAITING_URL, AWAITING_REMOVE_INDEX = range(2)

# Инициализация базы данных
def init_db():
    """Создаем SQLite базу данных и таблицу для хранения информации о товарах"""
    conn = sqlite3.connect('price_tracker.db')
    cursor = conn.cursor()
    # Структура таблицы:
    # - id: уникальный идентификатор записи
    # - user_id: Telegram ID пользователя
    # - url: ссылка на товар
    # - current_price: текущая цена товара
    # - last_checked: время последней проверки цены
    # - added_on: время добавления товара в отслеживание
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS products (
        id INTEGER PRIMARY KEY,
        user_id INTEGER,
        url TEXT,
        current_price REAL,
        last_checked TEXT,
        added_on TEXT
    )
    ''')
    conn.commit()
    conn.close()
    logger.info("База данных инициализирована")

# Обработчик команды /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Приветствуем пользователя и показываем доступные команды"""
    await update.message.reply_text(
        "👋 Привет! Я бот, который отслеживает цены на товары.\n\n"
        "Используйте следующие команды:\n"
        "/add - добавить ссылку на товар для отслеживания\n"
        "/list - показать все ваши отслеживаемые товары\n"
        "/remove - удалить ссылку из отслеживания\n\n"
        "Я буду проверять цены раз в день и сообщу, если что-то изменится."
    )

# Обработчик команды /add (шаг 1)
async def add_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Запрашиваем у пользователя ссылку на товар"""
    await update.message.reply_text(
        "Отправьте ссылку на товар, цену которого вы хотите отслеживать:\n"
        "(или /cancel для отмены)"
    )
    return AWAITING_URL

# Обработчик команды /add (шаг 2)
async def process_url(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обрабатываем полученную ссылку, добавляем товар в базу данных"""
    url = update.message.text
    user_id = update.effective_user.id
    
    # Валидация URL - проверяем, что ссылка выглядит правдоподобно
    if not url.startswith(('http://', 'https://')):
        await update.message.reply_text("❌ Некорректная ссылка. Пожалуйста, отправьте действительную ссылку, начинающуюся с http:// или https://")
        return ConversationHandler.END
    
    try:
        # Пытаемся получить текущую цену товара
        await update.message.reply_text("⏳ Проверяю ссылку и получаю информацию о цене...")
        price = get_price(url)
        
        if price is None:
            await update.message.reply_text(
                "❌ Не удалось получить цену с этой страницы.\n"
                "Возможно, сайт не поддерживается или структура страницы необычна.\n"
                "Попробуйте другую ссылку или другой магазин."
            )
            return ConversationHandler.END
        
        # Сохраняем информацию в базу данных
        conn = sqlite3.connect('price_tracker.db')
        cursor = conn.cursor()
        
        # Проверяем, не отслеживается ли эта ссылка уже
        cursor.execute("SELECT id FROM products WHERE user_id = ? AND url = ?", (user_id, url))
        if cursor.fetchone():
            await update.message.reply_text("⚠️ Эта ссылка уже отслеживается.")
            conn.close()
            return ConversationHandler.END
        
        # Добавляем новую запись
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cursor.execute(
            "INSERT INTO products (user_id, url, current_price, last_checked, added_on) VALUES (?, ?, ?, ?, ?)",
            (user_id, url, price, now, now)
        )
        conn.commit()
        conn.close()
        
        await update.message.reply_text(
            f"✅ Ссылка добавлена в отслеживание!\n"
            f"💰 Текущая цена: {price}.\n"
            f"🔄 Я буду проверять цену каждый день и уведомлю вас об изменениях."
        )
    except Exception as e:
        logger.error(f"Ошибка при обработке URL: {e}")
        await update.message.reply_text(
            "❌ Произошла ошибка при обработке ссылки.\n"
            "Пожалуйста, убедитесь, что ссылка корректна и попробуйте снова."
        )
    
    return ConversationHandler.END

# Обработчик команды /list
async def list_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показываем пользователю список всех отслеживаемых товаров"""
    user_id = update.effective_user.id
    
    conn = sqlite3.connect('price_tracker.db')
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, url, current_price, last_checked FROM products WHERE user_id = ? ORDER BY added_on DESC",
        (user_id,)
    )
    products = cursor.fetchall()
    conn.close()
    
    if not products:
        await update.message.reply_text(
            "🔍 У вас пока нет отслеживаемых товаров.\n"
            "Добавьте их с помощью команды /add"
        )
        return
    
    message = "📋 Ваши отслеживаемые товары:\n\n"
    for i, (prod_id, url, price, checked) in enumerate(products, 1):
        # Укорачиваем URL, если он слишком длинный
        display_url = url if len(url) < 40 else url[:37] + "..."
        message += f"{i}. {display_url}\n   💰 Текущая цена: {price}\n   🕒 Последняя проверка: {checked}\n\n"
    
    await update.message.reply_text(message)

# Обработчик команды /remove (шаг 1)
async def remove_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показываем список товаров и запрашиваем номер для удаления"""
    user_id = update.effective_user.id
    
    conn = sqlite3.connect('price_tracker.db')
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, url FROM products WHERE user_id = ? ORDER BY added_on DESC",
        (user_id,)
    )
    products = cursor.fetchall()
    conn.close()
    
    if not products:
        await update.message.reply_text("🔍 У вас нет отслеживаемых товаров.")
        return ConversationHandler.END
    
    # Сохраняем список товаров в контексте пользователя для дальнейшей обработки
    context.user_data['products'] = products
    
    message = "🗑️ Выберите номер товара для удаления:\n\n"
    for i, (prod_id, url) in enumerate(products, 1):
        # Укорачиваем URL, если он слишком длинный
        display_url = url if len(url) < 40 else url[:37] + "..."
        message += f"{i}. {display_url}\n"
    
    message += "\nОтправьте номер или /cancel для отмены"
    
    await update.message.reply_text(message)
    return AWAITING_REMOVE_INDEX

# Обработчик команды /remove (шаг 2)
async def process_remove(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обрабатываем выбор пользователя и удаляем товар из базы данных"""
    try:
        # Преобразуем ввод пользователя в индекс списка (с поправкой на нумерацию с 1)
        index = int(update.message.text) - 1
        products = context.user_data.get('products', [])
        
        if 0 <= index < len(products):
            product_id = products[index][0]
            product_url = products[index][1]
            
            # Удаляем запись из базы данных
            conn = sqlite3.connect('price_tracker.db')
            cursor = conn.cursor()
            cursor.execute("DELETE FROM products WHERE id = ?", (product_id,))
            conn.commit()
            conn.close()
            
            display_url = product_url if len(product_url) < 40 else product_url[:37] + "..."
            await update.message.reply_text(f"✅ Товар удален из отслеживания: {display_url}")
        else:
            await update.message.reply_text("❌ Неверный номер. Пожалуйста, выберите существующий номер товара.")
    except ValueError:
        await update.message.reply_text("❌ Пожалуйста, введите числовой номер товара.")
    except Exception as e:
        logger.error(f"Ошибка при удалении товара: {e}")
        await update.message.reply_text("❌ Произошла ошибка при удалении товара.")
    
    # Очищаем данные из контекста пользователя
    if 'products' in context.user_data:
        del context.user_data['products']
    
    return ConversationHandler.END

# Функция отмены диалога
async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /cancel для прерывания диалога"""
    # Очищаем данные из контекста пользователя, если они там есть
    if 'products' in context.user_data:
        del context.user_data['products']
    
    await update.message.reply_text("✅ Операция отменена.")
    return ConversationHandler.END

# Функции для работы с ценами
def get_price(url):
    """
    Извлекаем цену товара со страницы магазина.
    
    Эта функция пытается найти цену на странице товара с поддержкой разных форматов
    и различных интернет-магазинов.
    
    Args:
        url (str): URL страницы товара
        
    Returns:
        float: Цена товара или None, если цену не удалось найти
    """
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    try:
        # Делаем запрос к странице с имитацией браузера
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()  # Проверяем, что запрос успешен
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Логируем URL для отладки
        logger.info(f"Поиск цены для URL: {url}")
        
        # Определяем домен сайта для применения специфичных правил
        domain = extract_domain(url)
        logger.info(f"Определен домен: {domain}")
        
        # Специфичные правила для известных сайтов
        if domain == 'rozetka.ua' or domain == 'rozetka.com.ua' or 'rozetka' in domain:
            price = get_rozetka_price(soup)
            if price is not None:
                return price
        
        elif domain == 'intertop.ua' or 'intertop' in domain:
            price = get_intertop_price(soup)
            if price is not None:
                return price
        
        # Общий алгоритм для всех остальных сайтов
        price = get_generic_price(soup, domain)
        if price is not None:
            return price
        
        logger.warning(f"Не удалось найти цену для {url}")
        return None
            
    except Exception as e:
        logger.error(f"Ошибка при получении цены: {e}")
        return None

def extract_domain(url):
    """Извлекает доменное имя из URL"""
    try:
        # Удаляем http:// или https://
        if '://' in url:
            url = url.split('://')[1]
        
        # Берем только часть до первого слеша или вопросительного знака
        url = url.split('/')[0]
        url = url.split('?')[0]
        
        # Удаляем www. если есть
        if url.startswith('www.'):
            url = url[4:]
            
        return url
    except:
        return url

def get_rozetka_price(soup):
    """Извлекает цену с сайта Розетка"""
    rozetka_selectors = [
        'p.product-prices__big',          # Основная цена
        'span.product-prices__big',       # Альтернативный селектор
        '.product-price__big',            # Еще один вариант
        '.product-price__value',          # Старые страницы
        '.product-carriage__price'        # Ещё один вариант
    ]
    
    for selector in rozetka_selectors:
        price_element = soup.select_one(selector)
        if price_element:
            price_text = price_element.get_text().strip()
            # Логируем для отладки
            logger.info(f"Найдена цена на Розетке: {price_text}")
            # Извлекаем числа из текста
            price_nums = re.findall(r'\d+', price_text)
            if price_nums:
                # Соединяем цифры для формирования числа (игнорируя пробелы, знаки валюты и т.д.)
                price_str = ''.join(price_nums)
                # Конвертируем в число (без деления, так как цена в Розетке уже указана в гривнах)
                price = float(price_str)
                return price
    return None

def get_intertop_price(soup):
    """Извлекает цену с сайта Интертоп"""
    intertop_selectors = [
        '.product-price',                # Основная цена
        '.price-current',                # Текущая цена
        '.product-price__current',       # Еще один вариант
        '.product-price-current',        # Альтернативный селектор
    ]
    
    for selector in intertop_selectors:
        price_element = soup.select_one(selector)
        if price_element:
            price_text = price_element.get_text().strip()
            # Логируем для отладки
            logger.info(f"Найдена цена на Интертопе: {price_text}")
            
            # Извлекаем числа из текста, игнорируя различные разделители
            price_str = re.sub(r'[^\d.,]', '', price_text)
            
            # Заменяем запятые на точки для корректного преобразования в float
            price_str = price_str.replace(',', '.')
            
            # Если несколько точек, то все кроме последней - разделители тысяч
            if price_str.count('.') > 1:
                parts = price_str.split('.')
                price_str = ''.join(parts[:-1]) + '.' + parts[-1]
            
            try:
                price = float(price_str)
                logger.info(f"Извлечена цена с Интертопа: {price}")
                return price
            except ValueError:
                logger.warning(f"Не удалось преобразовать строку в число: {price_str}")
    
    # Пробуем найти цену в JSON-данных (часто используется в современных магазинах)
    scripts = soup.find_all('script', type='application/ld+json')
    for script in scripts:
        try:
            data = json.loads(script.string)
            # Рекурсивно ищем цену в JSON
            def find_price(obj):
                if isinstance(obj, dict):
                    for key in ['price', 'Price', 'currentPrice', 'CurrentPrice']:
                        if key in obj:
                            try:
                                return float(obj[key])
                            except (ValueError, TypeError):
                                pass
                    
                    # Ищем в подобъектах
                    for value in obj.values():
                        price = find_price(value)
                        if price is not None:
                            return price
                
                elif isinstance(obj, list):
                    for item in obj:
                        price = find_price(item)
                        if price is not None:
                            return price
                
                return None
            
            price = find_price(data)
            if price is not None:
                logger.info(f"Найдена цена в JSON-данных: {price}")
                return price
        except:
            pass
    
    return None

def get_generic_price(soup, domain):
    """Универсальный алгоритм извлечения цены для любого сайта"""
    
    # 1. Пробуем ищем через schema.org микроданные
    items_with_price = soup.find_all(attrs={'itemprop': 'price'})
    for item in items_with_price:
        content = item.get('content')
        if content:
            try:
                return float(content)
            except (ValueError, TypeError):
                pass
    
    # 2. Ищем по распространенным селекторам цен
    price_selectors = [
        'span.price', 'div.price', 'p.price', '.price-box', '.product-price', '.current-price',
        '.price-current', '.price_num', '.price-value', '.actual-price', '.special-price',
        '[data-price]', '[itemprop="price"]', '.main-price', '.new-price', '.sale-price',
        '.our_price', '.price-container', '.now-price', '.card-price', '.price-pdp',
        '.promo-price', '.item-price', '.product-card-price', '.product__price',
        '.money', '.final-price', '.current_price', '.amount', '.price-amount',
        '.product_price', '.price-label', '.product-cost', '.offer-price', 
        '.regular-price', '.price-number', '.price__current'
    ]
    
    for selector in price_selectors:
        price_elements = soup.select(selector)
        if price_elements:
            price_text = price_elements[0].get_text().strip()
            logger.info(f"Найдена цена по селектору {selector}: {price_text}")
            
            # Извлекаем числовую часть из текста
            price_value = extract_price_from_text(price_text, domain)
            if price_value is not None:
                return price_value
    
    # 3. Ищем через meta теги, часто используемые для цен
    meta_price_props = ['og:price:amount', 'product:price:amount', 'price', 'product:price']
    
    for prop in meta_price_props:
        meta_element = soup.find('meta', property=prop) or soup.find('meta', attrs={'name': prop})
        if meta_element and meta_element.get('content'):
            content = meta_element.get('content').strip()
            try:
                price = float(content)
                logger.info(f"Найдена цена в мета-теге {prop}: {price}")
                return price
            except (ValueError, TypeError):
                pass
    
    # 4. Ищем цену в JSON-данных (часто в скриптах)
    scripts = soup.find_all('script')
    price_patterns = [
        r'"price"\s*:\s*(\d+\.?\d*)',  # "price": 1234.56
        r'"price":\s*"(\d+\.?\d*)"',   # "price": "1234.56"
        r'price\s*:\s*(\d+\.?\d*)',    # price: 1234.56
        r'price\s*=\s*(\d+\.?\d*)',    # price = 1234.56
    ]
    
    for script in scripts:
        if script.string:
            for pattern in price_patterns:
                matches = re.search(pattern, script.string)
                if matches and matches.group(1):
                    try:
                        price = float(matches.group(1))
                        logger.info(f"Найдена цена в скрипте: {price}")
                        return price
                    except (ValueError, TypeError):
                        pass
    
    # 5. Последняя попытка: ищем что угодно, что похоже на цену
    # Смотрим только теги, которые могут содержать цену, чтобы не было ложных срабатываний
    price_containers = soup.find_all(['div', 'span', 'p', 'strong', 'b', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
    
    # Ищем содержимое похожее на формат цены с валютой
    currency_pattern = re.compile(r'(\d[\d\s,.]*[\d,.])(?:\s*(?:грн|₴|\$|€|руб|₽|UAH|USD|EUR))', re.IGNORECASE)
    
    for container in price_containers:
        if container.string:
            match = currency_pattern.search(container.string)
            if match:
                price_str = match.group(1)
                price_value = extract_price_from_text(price_str, domain)
                if price_value is not None:
                    logger.info(f"Найдена цена через поиск по валюте: {price_value}")
                    return price_value
    
    # Не нашли цену
    return None

def extract_price_from_text(price_text, domain):
    """
    Извлекает числовое значение цены из текстового представления
    с учетом различных форматов разделителей.
    """
    try:
        # Удаляем все символы, кроме цифр, точек и запятых
        price_str = re.sub(r'[^\d.,]', '', price_text)
        
        # Если строка пустая, значит не нашли цифр
        if not price_str:
            return None
        
        # Определяем, как обрабатывать разделители
        # Если несколько запятых - скорее всего разделители тысяч
        if price_str.count(',') > 1:
            price_str = price_str.replace(',', '')
        
        # Если точек несколько - они также разделители тысяч, кроме последней
        if price_str.count('.') > 1:
            parts = price_str.split('.')
            price_str = ''.join(parts[:-1]) + '.' + parts[-1]
        
        # Если есть и запятая, и точка - используем контекст
        if ',' in price_str and '.' in price_str:
            # В большинстве европейских стран запятая - десятичный разделитель
            # В США и Великобритании точка - десятичный разделитель
            # Определим по домену или контексту
            ua_domains = ['ua', 'укр', 'рф', 'ru']
            if any(d in domain for d in ua_domains):
                # Для украинских, русских сайтов запятая - десятичный разделитель
                price_str = price_str.replace('.', '').replace(',', '.')
            else:
                # Для остальных - убираем запятые (как разделители тысяч)
                price_str = price_str.replace(',', '')
        elif ',' in price_str:
            # Заменяем запятую на точку для корректного преобразования
            price_str = price_str.replace(',', '.')
        
        # Преобразуем в число
        price = float(price_str)
        
        # Интеллектуальное определение масштаба цены
        # Если цена слишком маленькая для товара, возможно это указано в копейках/центах
        # Например, 14.98 может быть 14.98 грн, но 1498 скорее всего 14.98 грн
        if price < 1 and len(price_str.replace('.', '')) > 2:
            price *= 100
        elif price < 5 and len(price_str.replace('.', '')) > 3:
            # Очень низкая цена с большим количеством цифр - скорее ошибка масштаба
            price *= 100
            
        return price
    except Exception as e:
        logger.error(f"Ошибка при извлечении цены из текста '{price_text}': {e}")
        return None

async def check_prices(context):
    """
    Проверяем цены всех товаров и уведомляем пользователей об изменениях.
    
    Эта функция запускается по расписанию раз в день и проходит по всем
    записям в базе данных. Для каждого товара получаем текущую цену и,
    если она изменилась по сравнению с сохраненной, уведомляем пользователя.
    """
    logger.info("Начинаем ежедневную проверку цен...")
    
    conn = sqlite3.connect('price_tracker.db')
    cursor = conn.cursor()
    cursor.execute("SELECT id, user_id, url, current_price FROM products")
    products = cursor.fetchall()
    
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    updated_count = 0
    failed_count = 0
    
    for prod_id, user_id, url, old_price in products:
        try:
            # Получаем текущую цену
            new_price = get_price(url)
            
            if new_price is None:
                logger.warning(f"Не удалось получить цену для {url}")
                failed_count += 1
                continue
            
            # Обновляем время последней проверки
            cursor.execute(
                "UPDATE products SET last_checked = ? WHERE id = ?",
                (now, prod_id)
            )
            
            # Если цена изменилась, обновляем и уведомляем
            # Используем небольшой порог для учета проблем с плавающей точкой
            if abs(new_price - old_price) > 0.01:
                cursor.execute(
                    "UPDATE products SET current_price = ? WHERE id = ?",
                    (new_price, prod_id)
                )
                
                # Определяем, выросла или упала цена
                change = new_price - old_price
                change_pct = (change / old_price) * 100
                
                if change > 0:
                    emoji = "📈"
                    change_text = f"увеличилась на {change_pct:.1f}%"
                else:
                    emoji = "📉" 
                    change_text = f"снизилась на {abs(change_pct):.1f}%"
                
                # Уведомляем пользователя
                display_url = url if len(url) < 40 else url[:37] + "..."
                message = (
                    f"{emoji} Изменение цены!\n\n"
                    f"Товар: {display_url}\n"
                    f"Старая цена: {old_price}\n"
                    f"Новая цена: {new_price}\n"
                    f"Цена {change_text}"
                )
                
                try:
                    await context.bot.send_message(chat_id=user_id, text=message)
                    updated_count += 1
                except Exception as e:
                    logger.error(f"Не удалось отправить уведомление пользователю {user_id}: {e}")
        
        except Exception as e:
            logger.error(f"Ошибка при проверке цены для {url}: {e}")
            failed_count += 1
    
    conn.commit()
    conn.close()
    logger.info(f"Ежедневная проверка цен завершена. Обновлено: {updated_count}, ошибок: {failed_count}")

def main():
    """Запускаем бота и регистрируем обработчики команд"""
    # Инициализируем базу данных
    init_db()
    
    # Создаем приложение и передаем токен телеграм-бота
    application = Application.builder().token("YOUR_TELEGRAM_BOT_TOKEN").build()
    
    # Регистрируем обработчики простых команд
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("list", list_command))
    
    # Регистрируем обработчик диалога для добавления товаров
    add_conv_handler = ConversationHandler(
        entry_points=[CommandHandler("add", add_command)],
        states={
            AWAITING_URL: [MessageHandler(filters.TEXT & ~filters.COMMAND, process_url)]
        },
        fallbacks=[CommandHandler("cancel", cancel)]
    )
    application.add_handler(add_conv_handler)
    
    # Регистрируем обработчик диалога для удаления товаров
    remove_conv_handler = ConversationHandler(
        entry_points=[CommandHandler("remove", remove_command)],
        states={
            AWAITING_REMOVE_INDEX: [MessageHandler(filters.TEXT & ~filters.COMMAND, process_remove)]
        },
        fallbacks=[CommandHandler("cancel", cancel)]
    )
    application.add_handler(remove_conv_handler)
    
    # Настраиваем ежедневную проверку цен (в 9:00 утра)
    job_queue = application.job_queue
    job_queue.run_daily(check_prices, time=dt_time(hour=9, minute=0))
    
    # Запускаем бота
    logger.info("Бот запущен и готов к работе!")
    application.run_polling()

if __name__ == '__main__':
    main()