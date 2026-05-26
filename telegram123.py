import telebot
from telebot import types
import random
import re
import traceback
import time
from collections import Counter
import json
import os


# НАЛАШТУВАННЯ

TOKEN = "8785080988:AAFmbNUgjp6nyIZ7W1pMFwAHMR7toya_LPA"  
bot = telebot.TeleBot(TOKEN)

orders = {}  # {chat_id: [item1, item2, ...]}
reserved_tables = set()
TABLES_FILE = "reserved_tables.json"


# ФУНКЦІЇ ДЛЯ БРОНЮВАННЯ СТОЛИКІВ 

def load_reserved_tables():
    global reserved_tables
    if os.path.exists(TABLES_FILE):
        try:
            with open(TABLES_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                reserved_tables = set(int(x) for x in data if str(x).isdigit())
            print(f"Завантажено {len(reserved_tables)} заброньованих столиків")
        except Exception as e:
            print(f"Помилка завантаження бронювань: {e}. Починаємо з порожнього.")
            reserved_tables = set()
    else:
        print("Файл бронювань не знайдено — починаємо з чистого аркуша")
        reserved_tables = set()


def save_reserved_tables():
    try:
        with open(TABLES_FILE, 'w', encoding='utf-8') as f:
            json.dump(list(reserved_tables), f, ensure_ascii=False, indent=2)
        print(f"Збережено {len(reserved_tables)} столиків")
    except Exception as e:
        print(f"Не вдалося зберегти бронювання: {e}")
        
# ДАНІ

MENU = {
    "Еспресо": 45,
    "Подвійний еспресо": 65,
    "Рістретто": 50,
    "Американо": 55,
    "Капучино": 65,
    "Капучино великий": 85,
    "Латте": 70,
    "Латте великий": 90,
    "Флет вайт": 75,
    "Мокко": 85,
    "Фільтр-кава": 60,
    "Аеропрес": 70,
    "V60": 75,
    "Колд брю": 95,
    "Латте на вівсяному": 95,
    "Капучино на мигдальному": 90,
    "Матча латте": 110,
    "Матча на кокосовому": 125,
    "Айс-латте": 85,
    "Айс-американо": 65,
    "Еспресо тонік": 95,
    "Мохіто класичний": 85,
    "Мохіто полуничний": 95,
    "Лимонад м'ятний": 75,
    "Лимонад обліпиховий": 80,
    "Комбуча": 90,
    "Айс-ти": 70,
    "Чорний чай": 50,
    "Зелений чай": 55,
    "Фруктовий чай": 60,
    "Трав'яний чай": 60,
    "Обліпиховий чай": 75,
    "Імбирний лимонний чай": 70,
    "Чізкейк Нью-Йорк": 95,
    "Чізкейк фісташка-малина": 125,
    "Чізкейк солона карамель": 115,
    "Тірамісу класичний": 95,
    "Тірамісу полуничний": 110,
    "Брауні класичний": 70,
    "Брауні з горіхами": 85,
    "Медовик": 90,
    "Наполеон": 85,
    "Морквяний торт": 95,
    "Тарт малина-м'ята": 110,
    "Тарт лимонний": 100,
    "Еклер ваніль": 65,
    "Еклер шоколад": 70,
    "Мафін чорниця": 60,
    "Круасан мигдалевий": 75,
    "Сінабон": 95,
    "Донат шоколад": 65,
    "Трайфл Чорний ліс": 120,
    "Мусс груша": 115,
}
KAWA = [
    "Еспресо", "Подвійний еспресо", "Рістретто", "Американо", "Капучино", "Капучино великий",
    "Латте", "Латте великий", "Флет вайт", "Мокко", "Фільтр-кава", "Аеропрес", "V60", "Колд брю",
    "Латте на вівсяному", "Капучино на мигдальному", "Матча латте", "Матча на кокосовому"
]

COLD_DRINKS = [
    "Айс-латте", "Айс-американо", "Еспресо тонік", "Мохіто класичний", "Мохіто полуничний",
    "Лимонад м'ятний", "Лимонад обліпиховий", "Комбуча", "Айс-ти"
]

TEA = [
    "Чорний чай", "Зелений чай", "Фруктовий чай", "Трав'яний чай", "Обліпиховий чай", "Імбирний лимонний чай"
] 

PHOTOS = {
    "Еспресо": "https://st.depositphotos.com/1491329/4023/i/380/depositphotos_40235245-stock-photo-coffee-espresso-cup-of-coffee.jpg",
    "Капучино": "https://st2.depositphotos.com/5355656/7813/i/380/depositphotos_78138608-stock-photo-a-cup-of-cappuccino.jpg",
    "Латте": "https://st5.depositphotos.com/39857320/79898/i/380/depositphotos_798981234-stock-photo-beautifully-layered-latte-macchiato-served.jpg",
    "Матча латте": "https://st2.depositphotos.com/5083063/11760/i/380/depositphotos_117602808-stock-photo-hot-green-tea-set-on.jpg",
    "Айс-латте": "https://st2.depositphotos.com/58753348/86223/i/380/depositphotos_862231116-stock-photo-ice-coffee-glass-wooden-table.jpg",
    "Мохіто": "https://st.depositphotos.com/1004221/1956/i/380/depositphotos_19569537-stock-photo-mojito-cocktail-over-black-background.jpg",
    "Чізкейк Нью-Йорк": "https://images.pexels.com/photos/1126359/pexels-photo-1126359.jpeg",
    "Тірамісу": "https://st4.depositphotos.com/1998601/22163/i/380/depositphotos_221637596-stock-photo-portion-tiramisu-dessert.jpg",
    "Брауні": "https://st2.depositphotos.com/1468291/6451/i/380/depositphotos_64515203-stock-photo-appetizing-chocolate-brownie.jpg",
    "Медовик": "https://st5.depositphotos.com/1236705/84324/i/380/depositphotos_843247660-stock-photo-honey-cake-white-plate-gray.jpg",
    "Подвійний еспресо": "https://st2.depositphotos.com/1006463/10169/i/380/depositphotos_101696466-stock-photo-close-up-image-of-espresso.jpg",
    "Рістретто": "https://st2.depositphotos.com/3410019/5413/i/380/depositphotos_54134907-stock-photo-ristretto-and-espresso-isolated-on.jpg",
    "Американо": "https://media.istockphoto.com/id/2158812697/ru/%D1%84%D0%BE%D1%82%D0%BE/%D0%B2%D0%B8%D0%B4-%D0%BF%D0%BE%D0%B4-%D0%B2%D1%8B%D1%81%D0%BE%D0%BA%D0%B8%D0%BC-%D1%83%D0%B3%D0%BB%D0%BE%D0%BC-%D0%BD%D0%B0-%D1%87%D0%B0%D1%88%D0%BA%D1%83-%D1%87%D0%B5%D1%80%D0%BD%D0%BE%D0%B3%D0%BE-%D0%BA%D0%BE%D1%84%D0%B5-%D0%BD%D0%B0-%D0%B4%D0%B5%D1%80%D0%B5%D0%B2%D1%8F%D0%BD%D0%BD%D0%BE%D0%BC-%D1%81%D1%82%D0%BE%D0%BB%D0%B5-%D1%83-%D0%BE%D0%BA%D0%BD%D0%B0.jpg?s=612x612&w=0&k=20&c=-OQX6SYowY1zp-DtSEjGG2RN1HHuywTDTTzU2j3nkS8=",
    "Капучино великий": "https://st3.depositphotos.com/1011158/37631/i/380/depositphotos_376319184-stock-photo-beautifully-decorated-cup-cappuccino-chocolate.jpg",
    "Латте великий": "https://st3.depositphotos.com/19503322/35752/i/380/depositphotos_357529204-stock-photo-table-bright-cafe-latte-freelancer.jpg",
    "Флет вайт": "https://st.depositphotos.com/1395167/3142/i/380/depositphotos_31424251-stock-photo-coffee-with-latte-art.jpg",
    "Мокко": "https://st.depositphotos.com/66249562/57292/i/380/depositphotos_572928064-stock-photo-latte-art-coffee-cardboard-cup.jpg",
    "Фільтр-кава": "https://st4.depositphotos.com/13768208/20720/i/380/depositphotos_207204528-stock-photo-man-pouring-hot-water-to.jpg",
    "Аеропрес": "https://st3.depositphotos.com/13194036/31671/i/380/depositphotos_316710010-stock-photo-cropped-view-barista-preparing-coffee.jpg",
    "V60": "https://st.depositphotos.com/12402830/58132/i/380/depositphotos_581321838-stock-photo-morning-coffee-alternative-method-making.jpg",
    "Колд брю": "https://st4.depositphotos.com/6644020/31090/i/380/depositphotos_310909594-stock-photo-pouring-cold-brew-iced-coffee.jpg",
    "Латте на вівсяному": "https://st4.depositphotos.com/1773130/28838/i/380/depositphotos_288387726-stock-photo-oat-milk-latte-with-thick.jpg",
    "Капучино на мигдальному": "https://st2.depositphotos.com/1177973/9189/i/380/depositphotos_91896942-stock-photo-cup-of-hot-cacao-on.jpg",
    "Матча на кокосовому": "https://st4.depositphotos.com/18508348/23003/i/380/depositphotos_230031564-stock-photo-vegan-coconut-matcha-latte-powdered.jpg",
    "Айс-американо": "https://st2.depositphotos.com/9379126/12282/i/380/depositphotos_122827626-stock-photo-ice-of-americano-on-white.jpg",
    "Еспресо тонік": "https://st2.depositphotos.com/3714791/43760/i/380/depositphotos_437606768-stock-photo-espresso-tonic-cold-alcoholic-cocktail.jpg",
    "Мохіто класичний": "https://st5.depositphotos.com/12982378/67595/i/380/depositphotos_675959410-stock-photo-thirst-quenching-cold-mojito-garnished.jpg",
    "Мохіто полуничний": "https://st3.depositphotos.com/11433342/15276/i/380/depositphotos_152761446-stock-photo-strawberry-lemonade-with-ice-cubes.jpg",
    "Лимонад м'ятний": "https://st.depositphotos.com/1027198/2867/i/380/depositphotos_28675483-stock-photo-ice-cold-lemonade.jpg",
    "Лимонад обліпиховий": "https://st2.depositphotos.com/9133450/46147/i/380/depositphotos_461476738-stock-photo-sea-buckthorn-lemonade-oranges-mint.jpg",
    "Комбуча": "https://st2.depositphotos.com/1692343/10499/i/380/depositphotos_104991664-stock-photo-homemade-fermented-raw-kombucha-tea.jpg",
    "Айс-ти": "https://upload.wikimedia.org/wikipedia/commons/thumb/e/e1/NCI_iced_tea.jpg/250px-NCI_iced_tea.jpg",
    "Чорний чай": "https://static8.depositphotos.com/1038226/982/i/380/depositphotos_9820017-stock-photo-cup-of-tea-black-background.jpg",
    "Зелений чай": "https://static6.depositphotos.com/1144352/636/i/380/depositphotos_6362450-stock-photo-herbal-tea.jpg",
    "Фруктовий чай": "https://st.depositphotos.com/1177973/4919/i/380/depositphotos_49191013-stock-photo-fruit-tea-with-wild-berries.jpg",
    "Трав'яний чай": "https://static8.depositphotos.com/1273864/938/i/380/depositphotos_9388480-stock-photo-tea-and-honey-on-background.jpg",
    "Обліпиховий чай": "https://st.depositphotos.com/1177973/3879/i/380/depositphotos_38790701-stock-photo-branches-of-sea-buckthorn-with.jpg",
    "Імбирний лимонний чай": "https://st2.depositphotos.com/5489530/8429/i/380/depositphotos_84292634-stock-photo-herb-tea-with-ginger-and.jpg",
    
    "Чізкейк фісташка-малина": "https://st2.depositphotos.com/1017251/9231/i/380/depositphotos_92314942-stock-photo-berry-cheesecake-with-pistachio-nuts.jpg",
    "Чізкейк солона карамель": "https://st5.depositphotos.com/16122460/62000/i/380/depositphotos_620006034-stock-photo-tasty-cheesecake-caramel-nuts-served.jpg",
    "Тірамісу класичний": "https://st2.depositphotos.com/10614052/43133/i/380/depositphotos_431334550-stock-photo-sweet-tasty-tiramisu-table.jpg",
    "Тірамісу полуничний": "https://st4.depositphotos.com/20376588/41832/i/380/depositphotos_418321284-stock-photo-strawberry-tiramisu-mascarpone-summer-dessert.jpg",
    "Брауні класичний": "https://st5.depositphotos.com/72516704/82626/i/380/depositphotos_826264792-stock-photo-chocolate-brownie-rich-dense-fudgy.jpg",
    "Брауні з горіхами": "https://st5.depositphotos.com/64200226/79151/i/380/depositphotos_791515494-stock-photo-homemade-chocolate-brownies-topping-almond.jpg",
    "Наполеон": "https://st2.depositphotos.com/5099597/9844/i/380/depositphotos_98440908-stock-photo-mille-feuilles-milhojas-napoleon-cake.jpg",
    "Морквяний торт": "https://st.depositphotos.com/1428014/3484/i/380/depositphotos_34846723-stock-photo-carrot-cake.jpg",
    "Тарт малина-м'ята": "https://st3.depositphotos.com/14670260/18995/i/380/depositphotos_189958972-stock-photo-raspberry-cake-and-many-fresh.jpg",
    "Тарт лимонний": "https://st3.depositphotos.com/10614052/33370/i/380/depositphotos_333704924-stock-photo-slice-of-tasty-lemon-pie.jpg",
    "Еклер ваніль": "https://st.depositphotos.com/1027198/3629/i/380/depositphotos_36295437-stock-photo-vanilla-eclair.jpg",
    "Еклер шоколад": "https://st2.depositphotos.com/4231139/8590/i/380/depositphotos_85901956-stock-photo-eclairs-with-chocolate.jpg",
    "Мафін чорниця": "https://static4.depositphotos.com/1008041/351/i/380/depositphotos_3510246-stock-photo-blueberry-muffins.jpg",
    "Круасан мигдалевий": "https://st3.depositphotos.com/17874660/31757/i/380/depositphotos_317576586-stock-photo-almond-croissant-with-custard-filling.jpg",
    "Сінабон": "https://st3.depositphotos.com/2095609/35972/i/380/depositphotos_359723968-stock-photo-tasty-fresh-cinnamon-rolls-close.jpg",
    "Донат шоколад": "https://st4.depositphotos.com/13349494/23901/i/380/depositphotos_239010678-stock-photo-glazed-chocotale-doughnut-sprinkles-white.jpg",
    "Трайфл Чорний ліс": "https://st3.depositphotos.com/5664962/18125/i/380/depositphotos_181253606-stock-photo-dessert-black-forest-in-a.jpg",
    "Мусс груша": "https://thumbs.dreamstime.com/b/%D0%B3%D1%80%D1%83%D1%88%D0%B0-%D0%B4%D0%B5%D1%81%D0%B5%D1%80%D1%82%D0%B0-choko-11026884.jpg?w=768",
}



PROMOTIONS = [
    "🎁 Ранкова кава: з 08:00 до 11:00 — капучино/латте -20%",
    "🎁 Кожна 6-а кава в подарунок",
    "🎁 Десерт до кави +30 грн (замість +60 грн)",
    "🎁 Іменинникам — безкоштовний напій від 150 грн",
    "🎁 Комбо: латте + чізкейк = 140 грн",
]


# КЛАВІАТУРИ

def main_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add("☕ Напої", "🍰 Десерти")
    markup.add("🛒 Моє замовлення", "📍 Адреса")
    markup.add("🪑 Столики", "ℹ️ Графік")
    markup.add("🎁 Акції")
    return markup


def payment_menu():
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(types.InlineKeyboardButton("💳 Оплатити карткою", callback_data="pay_card"))
    markup.add(types.InlineKeyboardButton("💵 Готівкою", callback_data="pay_cash"))
    markup.add(types.InlineKeyboardButton("🗑 Очистити кошик", callback_data="clear_order"))
    return markup


# ДОПОМІЖНІ ФУНКЦІЇ

def safe_send_photo(chat_id, photo_url, caption, reply_markup=None):
    try:
        bot.send_photo(
            chat_id,
            photo_url,
            caption=caption,
            reply_markup=reply_markup,
            parse_mode="Markdown" if "*" in caption else None
        )
    except Exception as e:
        if "Bad Request" in str(e) or "wrong type" in str(e):
            bot.send_message(chat_id, caption, reply_markup=reply_markup, parse_mode="Markdown" if "*" in caption else None)
        else:
            bot.send_message(chat_id, caption + "\n(фото тимчасово недоступне)")


def normalize_text(text: str) -> str:
    return re.sub(r'[^\w\s]', '', text.lower().strip())


def add_to_order(chat_id: int, item: str):
    if chat_id not in orders:
        orders[chat_id] = []
    orders[chat_id].append(item)


def get_order_text(chat_id: int) -> str:
    if chat_id not in orders or not orders[chat_id]:
        return "🛒 Ваш кошик порожній."

    cnt = Counter(orders[chat_id])
    total = sum(MENU.get(it, 0) * c for it, c in cnt.items())

    lines = ["📋 *Ваше замовлення*:\n"]
    for it, c in cnt.items():
        p = MENU.get(it, 0)
        lines.append(f"• {it} ×{c} — {p * c} грн  ({p} грн/шт)")
    lines.append(f"\n💰 *Разом*: {total} грн")
    return "\n".join(lines)


def show_items(chat_id, title, keywords):
    bot.send_message(chat_id, title)
    for item, price in MENU.items():
        item_lower = item.lower()
        if any(kw in item_lower for kw in keywords):
            caption = f"*{item}* — {price} грн"
            markup = types.InlineKeyboardMarkup(row_width=1)
            markup.add(types.InlineKeyboardButton("🛒 Додати", callback_data=f"add_{item}"))

            photo = PHOTOS.get(item)
            if photo and "стаф фото" not in photo:
                safe_send_photo(chat_id, photo, caption, markup)
            else:
                bot.send_message(chat_id, caption, reply_markup=markup, parse_mode="Markdown")


def show_drinks(chat_id):
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(types.InlineKeyboardButton("☕ Кава та альтернативи", callback_data="cat_kawa"))
    markup.add(types.InlineKeyboardButton("❄️ Холодні напої", callback_data="cat_cold"))
    markup.add(types.InlineKeyboardButton("🍵 Чай", callback_data="cat_tea"))
    
    bot.send_message(chat_id, "Оберіть категорію напоїв:", reply_markup=markup)


def show_category(chat_id, category, title):
    bot.send_message(chat_id, title)
    
    keywords_map = {
        "kawa": ["еспресо", "американо", "капуч", "латте", "матча", "фільтр", "аеропрес", "v60", "колд", "флет", "мокко", "рістретто", "тонік"],
        "cold": ["айс", "мохіто", "лимонад", "комбуча"],
        "tea": ["чай"]
    }
    
    keywords = keywords_map.get(category, [])
    
    for item, price in MENU.items():
        item_lower = item.lower()
        if any(kw in item_lower for kw in keywords):
            caption = f"*{item}* — {price} грн"
            markup = types.InlineKeyboardMarkup(row_width=1)
            markup.add(types.InlineKeyboardButton("🛒 Додати", callback_data=f"add_{item}"))

            photo = PHOTOS.get(item)
            if photo and "стаф фото" not in photo:
                safe_send_photo(chat_id, photo, caption, markup)
            else:
                bot.send_message(chat_id, caption, reply_markup=markup, parse_mode="Markdown")


def show_desserts(chat_id):
    bot.send_message(chat_id, "Оберіть десерт:")
    for item, price in MENU.items():
        if any(kw in item.lower() for kw in ["чізкейк", "тірамісу", "брауні", "медовик", "наполеон", "тарт", "еклер", "мафін", "круасан", "сінабон", "донат", "трайфл", "мус", "торт"]):
            caption = f"*{item}* — {price} грн"
            markup = types.InlineKeyboardMarkup(row_width=1)
            markup.add(types.InlineKeyboardButton("🛒 Додати", callback_data=f"add_{item}"))

            photo = PHOTOS.get(item)
            if photo and "стаф фото" not in photo:
                safe_send_photo(chat_id, photo, caption, markup)
            else:
                bot.send_message(chat_id, caption, reply_markup=markup, parse_mode="Markdown")


def show_promotions(chat_id):
    text = "🎁 *Акції Кавового Кота*:\n\n" + "\n".join(f"→ {p}" for p in PROMOTIONS)
    text += "\n\nДіють до кінця місяця або поки є запаси 😉"
    bot.send_message(chat_id, text, parse_mode="Markdown", reply_markup=main_menu())


# ХЕНДЛЕРИ

@bot.message_handler(commands=["start"])
def cmd_start(message):
    welcome = (
        "🐱 *Вітаємо в Кавовий Кот*! ☕\n"
        "Найкраща кава та затишок у місті!\n\n"
        "*Акції зараз:*\n" + "\n".join(f"→ {p}" for p in PROMOTIONS[:3]) +
        "\n\nОберіть розділ 👇"
    )
    safe_send_photo(
        message.chat.id,
        "https://st4.depositphotos.com/15312520/25368/i/380/depositphotos_253680782-stock-photo-tabby-color-kitten-on-the.jpg",
        welcome,
        main_menu()
    )


@bot.message_handler(func=lambda m: True)
def handle_text(message):
    cid = message.chat.id
    txt = normalize_text(message.text)

    if any(w in txt for w in ["привіт", "добрий", "hi", "hello"]):
        bot.send_message(cid, "Привіт! 🐾 Чим здивувати сьогодні? ☕", reply_markup=main_menu())
        return

    if any(w in txt for w in ["столик", "столики", "забронювати", "бронь", "місце"]):
        free = [i for i in range(1, 16) if i not in reserved_tables]
        if not free:
            bot.send_message(cid, "😿 Усі столики зайняті наразі...")
            return
        
        tbl = random.choice(free)
        reserved_tables.add(tbl)
        save_reserved_tables()  # ЗБЕРІГАЄМО в файл
        
        bot.send_message(cid, f"🎉 Ваш столик №{tbl} заброньовано!")
        safe_send_photo(cid, "https://images.pexels.com/photos/260922/pexels-photo-260922.jpeg", "Затишне місце для тебе 🐱")
        return

    if any(w in txt for w in ["напій", "напої", "кава", "кав", "еспресо", "латте", "капуч", "мохіто", "чай", "матча", "айс"]):
        show_drinks(cid)
        return

    if any(w in txt for w in ["десерт", "десерти", "солодке", "чізкейк", "тірамісу", "брауні", "торт", "еклер", "мафін"]):
        show_desserts(cid)
        return

    if any(w in txt for w in ["акція", "акції", "промо", "знижка"]):
        show_promotions(cid)
        return

    if any(w in txt for w in ["замовлення", "кошик", "моє замовл", "що замовив"]):
        text = get_order_text(cid)
        mk = payment_menu() if cid in orders and orders[cid] else None
        bot.send_message(cid, text, parse_mode="Markdown", reply_markup=mk)
        return

    if any(w in txt for w in ["адреса", "де ви", "де кафе", "вулиця"]):
        bot.send_location(cid, 46.9750, 31.9950)
        bot.send_message(cid, "📍 вул. Центральна, 15\nЧекаємо тебе! 🐱")
        return

    if any(w in txt for w in ["графік", "коли працюєте", "години"]):
        bot.send_message(cid, "⏰ Пн–Нд: 08:00 – 21:00\nБез вихідних ☕")
        return

    if any(w in txt for w in ["очистити", "скасувати", "видалити"]):
        if cid in orders:
            orders[cid].clear()
        bot.send_message(cid, "Замовлення очищено 🗑️", reply_markup=main_menu())
        return

    bot.send_message(cid,
        "Не дуже зрозумів... 😿\n\nСпробуй наприклад:\n"
        "• хочу латте на вівсяному\n"
        "• чізкейк фісташка\n"
        "• акції\n"
        "• столик",
        reply_markup=main_menu())

@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    cid = call.message.chat.id
    data = call.data.strip()

    if data.startswith("add_"):
        raw_item = data[4:].strip()
        
        # Пошук без урахування регістру
        found_item = None
        for menu_item in MENU:
            if menu_item.strip().lower() == raw_item.lower():
                found_item = menu_item
                break

        if found_item:
            add_to_order(cid, found_item)
            bot.answer_callback_query(call.id, f"+ {found_item}", show_alert=False)
            # Показуємо оновлений кошик
            bot.send_message(cid, get_order_text(cid), parse_mode="Markdown", reply_markup=payment_menu())
        else:
            bot.answer_callback_query(call.id, f"Не знайдено: {raw_item} 😿", show_alert=True)
            print(f"[DEBUG] Не знайдено: '{raw_item}' (callback: {data})")

    elif data == "cat_kawa":
        show_category(cid, "kawa", "Оберіть каву та альтернативи:")
    elif data == "cat_cold":
        show_category(cid, "cold", "Оберіть холодні напої:")
    elif data == "cat_tea":
        show_category(cid, "tea", "Оберіть чай:")

    elif data == "pay_card":
        bot.send_message(cid, "Оплата карткою успішна! Дякуємо ❤️\nСкоро готуємо ваше замовлення!")
        orders.pop(cid, None)
        bot.answer_callback_query(call.id)

    elif data == "pay_cash":
        bot.send_message(cid, "Оплата готівкою — офіціант уже йде 😺")
        bot.answer_callback_query(call.id)

    elif data == "clear_order":
        orders.pop(cid, None)
        bot.send_message(cid, "Кошик очищено 🗑️")
        bot.answer_callback_query(call.id)

# ЗАПУСК

if __name__ == "__main__":
    print("Запускаємо Кавовий Кот... ☕🐱")
    load_reserved_tables()
    
    print("Перевіряємо підключення до Telegram...")
    try:
        bot.get_me()  
        print("OK! Токен валідний, бот онлайн.")
    except telebot.apihelper.ApiTelegramException as e:
        print(f"ПОМИЛКА ТОКЕНА: {e}")
        print("Перевір токен у @BotFather або інтернет.")
        exit(1)
    except Exception as e:
        print(f"Не можу підключитися: {e}")
        print("Перевір інтернет / firewall / VPN")
        exit(1)

    print("Бот стартує polling... (зачекай 20–60 сек)")
    print("Напиши боту в Telegram: /start або 'столик'")
    
    while True:
        try:
            bot.remove_webhook()
            bot.infinity_polling(
                timeout=10,
                long_polling_timeout=5,
                skip_pending=True,
                allowed_updates=["message", "callback_query"]
            )
        except KeyboardInterrupt:
            print("\nЗупинено користувачем (Ctrl+C)")
            break
        except telebot.apihelper.ApiTelegramException as e:
            print(f"Помилка API: {e}")
            time.sleep(10)
        except Exception as e:
            print(f"Критична помилка: {type(e).__name__} - {e}")
            traceback.print_exc()
            time.sleep(10)
