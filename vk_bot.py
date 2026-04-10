import requests
import time
import os

VK_TOKEN = os.environ.get('VK_TOKEN')
VK_GROUP_ID = os.environ.get('VK_GROUP_ID')
TG_BOT_TOKEN = os.environ.get('TG_BOT_TOKEN')
TG_CHANNEL_ID = os.environ.get('TG_CHANNEL_ID')

def main():
    try:
        vk_resp = requests.get("https://api.vk.com/method/wall.get", params={
            "owner_id": VK_GROUP_ID, "count": 5, "access_token": VK_TOKEN, "v": "5.131"
        }, timeout=10).json()

        posts = vk_resp.get('response', {}).get('items', [])
        now = int(time.time())

        for post in reversed(posts):
            pid = post['id']
            age = now - post['date']

            if age < 3600:
                text = (post.get('text') or '')[:1000]
                link = f"https://vk.com/wall{VK_GROUP_ID}_{pid}"
                caption = f"{text}\n\n🔗 <a href='{link}'>Источник</a>" if text else f"🔗 <a href='{link}'>Пост ВК</a>"

                photos = []
                for att in post.get('attachments', []):
                    if att['type'] == 'photo':
                        photos.append(att['photo']['sizes'][-1]['url'])

                if photos:
                    if len(photos) == 1:
                        requests.post(f"https://api.telegram.org/bot{TG_BOT_TOKEN}/sendPhoto", data={
                            "chat_id": TG_CHANNEL_ID, "photo": photos[0], "caption": caption, "parse_mode": "HTML"
                        }, timeout=15)
                    else:
                        media = [{"type": "photo", "media": url, "caption": caption if i==0 else "", "parse_mode": "HTML"} 
                                for i, url in enumerate(photos)]
                        requests.post(f"https://api.telegram.org/bot{TG_BOT_TOKEN}/sendMediaGroup", json={
                            "chat_id": TG_CHANNEL_ID, "media": media
                        }, timeout=15)
                elif text:
                    requests.post(f"https://api.telegram.org/bot{TG_BOT_TOKEN}/sendMessage", data={
                        "chat_id": TG_CHANNEL_ID, "text": caption, "parse_mode": "HTML"
                    }, timeout=10)
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
