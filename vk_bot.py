import requests
import time
import os

VK_TOKEN = os.environ.get('VK_TOKEN')
VK_GROUP_ID = os.environ.get('VK_GROUP_ID')
TG_BOT_TOKEN = os.environ.get('TG_BOT_TOKEN')
TG_CHANNEL_ID = os.environ.get('TG_CHANNEL_ID')

def main():
    print("🚀 Запуск бота...")
    try:
        # 1. Забираем посты из ВК
        vk_resp = requests.get("https://api.vk.com/method/wall.get", params={
            "owner_id": VK_GROUP_ID, "count": 5, "access_token": VK_TOKEN, "v": "5.131"
        }, timeout=10).json()

        if 'response' not in vk_resp or 'items' not in vk_resp['response']:
            print("❌ Ошибка VK API:", vk_resp)
            return

        posts = vk_resp['response']['items']
        now = int(time.time())
        print(f"📊 Получено постов: {len(posts)}")

        # 2. Проходим от старых к новым
        for post in reversed(posts):
            pid = post['id']
            age = now - post['date']

            if age < 1200:  # 20 минут
                print(f"📥 Обработка поста #{pid} (возраст: {age//60} мин)")
                
                text = (post.get('text') or '')[:1000]
                link = f"https://vk.com/wall{VK_GROUP_ID}_{pid}"
                caption = f"{text}\n\n🔗 <a href='{link}'>Источник</a>" if text else f"🔗 <a href='{link}'>Пост ВК</a>"

                # Собираем ВСЕ фото из поста
                photos = []
                for att in post.get('attachments', []):
                    if att['type'] == 'photo':
                        photo_url = att['photo']['sizes'][-1]['url']
                        photos.append(photo_url)
                    elif att['type'] == 'clip':
                        # Клипы (короткие видео)
                        files = att['clip'].get('files', {})
                        for q in ["mp4_720", "mp4_480", "mp4_360"]:
                            if q in files:
                                print(f"🎬 Найдено видео-клип")
                                # Отправляем как видео
                                tg_resp = requests.post(f"https://api.telegram.org/bot{TG_BOT_TOKEN}/sendVideo", data={
                                    "chat_id": TG_CHANNEL_ID, "video": files[q], "caption": caption, "parse_mode": "HTML"
                                }, timeout=15)
                                if tg_resp.json().get('ok'):
                                    print(f"✅ Видео отправлено!")
                                break
                        continue
                    elif att['type'] == 'video':
                        # Обычные видео (пропускаем, т.к. они длинные)
                        print(f"⏭️ Пропускаем длинное видео")
                        continue

                # 3. Отправка в Telegram
                if photos:
                    if len(photos) == 1:
                        # Одно фото — отправляем как фото
                        tg_resp = requests.post(f"https://api.telegram.org/bot{TG_BOT_TOKEN}/sendPhoto", data={
                            "chat_id": TG_CHANNEL_ID, "photo": photos[0], "caption": caption, "parse_mode": "HTML"
                        }, timeout=15)
                    else:
                        # Несколько фото — отправляем как АЛЬБОМ
                        print(f"📸 Отправляю альбом из {len(photos)} фото")
                        media = []
                        for i, photo_url in enumerate(photos):
                            if i == 0:
                                # Первое фото с подписью
                                media.append({"type": "photo", "media": photo_url, "caption": caption, "parse_mode": "HTML"})
                            else:
                                # Остальные без подписи
                                media.append({"type": "photo", "media": photo_url})
                        
                        tg_resp = requests.post(f"https://api.telegram.org/bot{TG_BOT_TOKEN}/sendMediaGroup", json={
                            "chat_id": TG_CHANNEL_ID,
                            "media": media
                        }, timeout=15)
                    
                    res = tg_resp.json()
                    if res.get('ok'):
                        print(f"✅ Альбом из {len(photos)} фото отправлен!")
                    else:
                        print(f"⚠️ Ошибка Telegram: {res}")
                else:
                    # Только текст
                    tg_resp = requests.post(f"https://api.telegram.org/bot{TG_BOT_TOKEN}/sendMessage", data={
                        "chat_id": TG_CHANNEL_ID, "text": caption, "parse_mode": "HTML"
                    }, timeout=10)
                    if tg_resp.json().get('ok'):
                        print(f"✅ Текст отправлен!")
            else:
                print(f"⏭️ Пост #{pid} старый ({age//60} мин), пропускаем.")
                
    except Exception as e:
        print(f"💥 Критическая ошибка: {e}")

if __name__ == "__main__":
    main()
