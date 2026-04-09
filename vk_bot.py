import requests
import time
import os

# ================= НАСТРОЙКИ =================
VK_TOKEN = os.environ.get('VK_TOKEN')
VK_GROUP_ID = os.environ.get('VK_GROUP_ID')
TG_BOT_TOKEN = os.environ.get('TG_BOT_TOKEN')
TG_CHANNEL_ID = os.environ.get('TG_CHANNEL_ID')
MAX_VIDEO_SEC = 60
# =============================================

VK_WALL = "https://api.vk.com/method/wall.get"
VK_VIDEO = "https://api.vk.com/method/video.get"
TG_API = f"https://api.telegram.org/bot{TG_BOT_TOKEN}"

def get_video_url(owner_id, vid_id, access_key=""):
    params = {"videos": f"{owner_id}_{vid_id}{access_key}", "access_token": VK_TOKEN, "v": "5.131"}
    try:
        r = requests.get(VK_VIDEO, params=params).json()
        files = r.get("response", {}).get("items", [{}])[0].get("files", {})
        for q in ["mp4_1080", "mp4_720", "mp4_480", "mp4_360"]:
            if q in files: return files[q]
    except: pass
    return None

def send_to_telegram(text, photo_url=None, video_url=None):
    try:
        if photo_url:
            data = {"chat_id": TG_CHANNEL_ID, "caption": text, "parse_mode": "HTML"}
            files = {"photo": requests.get(photo_url).content}
            return requests.post(f"{TG_API}/sendPhoto", files=files, data=data).json()
        elif video_url:
            data = {"chat_id": TG_CHANNEL_ID, "caption": text, "parse_mode": "HTML"}
            files = {"video": requests.get(video_url).content}
            return requests.post(f"{TG_API}/sendVideo", files=files, data=data).json()
        else:
            data = {"chat_id": TG_CHANNEL_ID, "text": text, "parse_mode": "HTML"}
            return requests.post(f"{TG_API}/sendMessage", json=data).json()
    except Exception as e:
        print(f"❌ Ошибка ТГ: {e}")
        return None

def process_post(post):
    text = (post.get("text") or "")[:1000]
    link = f"https://vk.com/wall{VK_GROUP_ID}_{post['id']}"
    caption = f"{text}\n\n🔗 <a href='{link}'>Источник</a>" if text else f"🔗 <a href='{link}'>Пост ВК</a>"

    for att in post.get("attachments", []):
        t = att["type"]
        if t == "photo":
            sizes = att["photo"].get("sizes", [])
            if sizes: return caption, sizes[-1]["url"], None
        elif t == "clip":
            files = att["clip"].get("files", {})
            for q in ["mp4_720", "mp4_480", "mp4_360"]:
                if q in files: return caption, None, files[q]
        elif t == "video":
            v = att["video"]
            if v.get("duration", 999) <= MAX_VIDEO_SEC:
                url = get_video_url(v["owner_id"], v["id"], v.get("access_key", ""))
                if url: return caption, None, url
    return caption, None, None

def main():
    current_time = int(time.time())
    params = {"owner_id": VK_GROUP_ID, "count": 10, "access_token": VK_TOKEN, "v": "5.131"}
    r = requests.get(VK_WALL, params=params).json()
    posts = r.get("response", {}).get("items", [])
    
    print(f"⏰ Текущее время: {time.strftime('%H:%M:%S')}")
    
    for post in reversed(posts):
        post_time = post["date"]
        age_seconds = current_time - post_time
        
        if age_seconds < 900:
            print(f"📥 Свежий пост #{post['id']} (возраст: {age_seconds} сек)")
            text, photo, video = process_post(post)
            res = send_to_telegram(text, photo, video)
            
            if res and res.get("ok"):
                print("✅ Отправлено в Telegram!")
            else:
                print(f"⚠️ Ошибка: {res}")
        else:
            print(f"⏭️ Пост #{post['id']} старше 15 мин, пропускаем.")

if __name__ == "__main__":
    main()
