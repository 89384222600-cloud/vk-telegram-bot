import requests
import time
import os

print("🚀 ЗАПУСК БОТА...")

try:
    VK_TOKEN = os.environ.get('VK_TOKEN')
    VK_GROUP_ID = os.environ.get('VK_GROUP_ID')
    TG_BOT_TOKEN = os.environ.get('TG_BOT_TOKEN')
    TG_CHANNEL_ID = os.environ.get('TG_CHANNEL_ID')
    
    print(f"✅ Токены загружены")
    print(f"📊 VK_GROUP_ID: {VK_GROUP_ID}")
    print(f"📊 TG_CHANNEL_ID: {TG_CHANNEL_ID}")

    print("📡 Запрос к VK API...")
    vk_resp = requests.get(
        "https://api.vk.com/method/wall.get", 
        params={
            "owner_id": VK_GROUP_ID, 
            "count": 5, 
            "access_token": VK_TOKEN, 
            "v": "5.131"
        }, 
        timeout=10
    )
    
    print(f"📥 Ответ VK: {vk_resp.status_code}")
    
    vk_json = vk_resp.json()
    print(f"📦 JSON: {vk_json}")
    
    if 'response' not in vk_json:
        print(f"❌ Ошибка VK API: {vk_json}")
        exit(1)
    
    posts = vk_json['response'].get('items', [])
    print(f"📊 Получено постов: {len(posts)}")
    
    if not posts:
        print("⚠️ Постов нет!")
        exit(0)
    
    now = int(time.time())
    print(f"⏰ Текущее время: {time.strftime('%H:%M:%S')} (timestamp: {now})")

    for post in reversed(posts):
        pid = post['id']
        post_time = post['date']
        age = now - post_time
        
        print(f"\n📌 Пост #{pid}:")
        print(f"   Время поста: {time.strftime('%H:%M:%S', time.localtime(post_time))}")
        print(f"   Возраст: {age} сек ({age//60} мин)")

        if age < 3600:  # 60 минут
            print(f"   ✅ Пост свежий, обрабатываю...")
            
            text = (post.get('text') or '')[:1000]
            link = f"https://vk.com/wall{VK_GROUP_ID}_{pid}"
            caption = f"{text}\n\n🔗 <a href='{link}'>Источник</a>" if text else f"🔗 <a href='{link}'>Пост ВК</a>"
            
            print(f"   📝 Текст: {text[:50]}...")
            
            # Собираем фото
            photos = []
            for att in post.get('attachments', []):
                if att['type'] == 'photo':
                    url = att['photo']['sizes'][-1]['url']
                    photos.append(url)
                    print(f"   📸 Найдено фото: {url[:50]}...")
            
            # Отправка
            if photos:
                print(f"   📤 Отправляю {len(photos)} фото в Telegram...")
                if len(photos) == 1:
                    tg_resp = requests.post(
                        f"https://api.telegram.org/bot{TG_BOT_TOKEN}/sendPhoto", 
                        data={
                            "chat_id": TG_CHANNEL_ID, 
                            "photo": photos[0], 
                            "caption": caption, 
                            "parse_mode": "HTML"
                        }, 
                        timeout=15
                    )
                else:
                    media = []
                    for i, url in enumerate(photos):
                        media.append({
                            "type": "photo", 
                            "media": url, 
                            "caption": caption if i==0 else "", 
                            "parse_mode": "HTML"
                        })
                    tg_resp = requests.post(
                        f"https://api.telegram.org/bot{TG_BOT_TOKEN}/sendMediaGroup", 
                        json={"chat_id": TG_CHANNEL_ID, "media": media}, 
                        timeout=15
                    )
                
                if tg_resp.json().get('ok'):
                    print(f"   ✅ ОТПРАВЛЕНО В TELEGRAM!")
                else:
                    print(f"   ❌ Ошибка Telegram: {tg_resp.json()}")
            elif text:
                print(f"   📤 Отправляю текст в Telegram...")
                tg_resp = requests.post(
                    f"https://api.telegram.org/bot{TG_BOT_TOKEN}/sendMessage", 
                    data={
                        "chat_id": TG_CHANNEL_ID, 
                        "text": caption, 
                        "parse_mode": "HTML"
                    }, 
                    timeout=10
                )
                if tg_resp.json().get('ok'):
                    print(f"   ✅ ТЕКСТ ОТПРАВЛЕН!")
                else:
                    print(f"   ❌ Ошибка Telegram: {tg_resp.json()}")
        else:
            print(f"   ⏭️ Пост старый, пропускаю")
            
except Exception as e:
    print(f"💥 КРИТИЧЕСКАЯ ОШИБКА: {e}")
    import traceback
    traceback.print_exc()
