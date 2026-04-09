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

            # Окно 20 минут (1200 сек) - надёжно для крона каждые 5 мин
            if age < 1200:
                print(f"📥 Обработка поста #{pid} (возраст: {age//60} мин)")
                text = (post.get('text') or '')[:1000]
                link = f"https://vk.com/wall{VK_GROUP_ID}_{pid}"
                caption = f"{text}\n\n🔗 <a href='{link}'>Источник</a>" if text else f"🔗 <a href='{link}'>Пост ВК</a>"

                # Ищем картинку
                photo_url = None
                for att in post.get('attachments', []):
                    if att['type'] == 'photo':
                        photo_url = att['photo']['sizes'][-1]['url']
                        break

                # 3. Отправка в Telegram
                if photo_url:
                    tg_resp = requests.post(f"https://api.telegram.org/bot{TG_BOT_TOKEN}/sendPhoto", data={
                        "chat_id": TG_CHANNEL_ID, "photo": photo_url, "caption": caption, "parse_mode": "HTML"
                    }, timeout=10)
                else:
                    tg_resp = requests.post(f"https://api.telegram.org/bot{TG_BOT_TOKEN}/sendMessage", data={
                        "chat_id": TG_CHANNEL_ID, "text": caption, "parse_mode": "HTML"
                    }, timeout=10)

                res = tg_resp.json()
                if res.get('ok'):
                    print(f"✅ Пост #{pid} успешно отправлен!")
                else:
                    print(f"⚠️ Ошибка Telegram: {res}")
            else:
                print(f"⏭️ Пост #{pid} старый ({age//60} мин), пропускаем.")
                
    except Exception as e:
        print(f"💥 Критическая ошибка: {e}")

if __name__ == "__main__":
    main()
