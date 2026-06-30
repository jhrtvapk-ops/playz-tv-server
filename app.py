from flask import Flask, request, Response
import requests
import concurrent.futures
import threading

app = Flask(__name__)

master_links = []
VALID_PLAYLIST = "#EXTM3U\n\n"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

def check_single_link(link):
    try:
        clean_url = link.split("|")[0] if "|" in link else link
        res = requests.head(clean_url, headers=HEADERS, timeout=3, allow_redirects=True)
        if res.status_code in [200, 206, 302, 403]:
            return link
    except:
        pass
    return None

# 🌟 ব্যাকগ্রাউন্ড প্রসেসর (র‍্যাম ও টাইমআউট বাঁচানোর জন্য)
def background_processor(new_links):
    global master_links, VALID_PLAYLIST
    
    for link in new_links:
        if link not in master_links:
            master_links.append(link)

    alive_links = []
    # 🌟 র‍্যাম বাঁচানোর জন্য max_workers=5 করে দেওয়া হয়েছে
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        results = executor.map(check_single_link, master_links)
        for res in results:
            if res:
                alive_links.append(res)
    
    master_links = alive_links

    playlist = "#EXTM3U\n\n"
    for i, link in enumerate(master_links):
        clean_url = link.split("|")[0] if "|" in link else link
        user_agent = HEADERS["User-Agent"]
        referer = ""
        
        if "|" in link:
            try:
                parts = link.split("|")[1].split("&")
                for p in parts:
                    if p.startswith("User-Agent="): user_agent = p.split("=")[1]
                    elif p.startswith("Referer="): referer = p.split("=")[1]
            except:
                pass

        playlist += f'#EXTINF:-1 tvg-logo="https://raw.githubusercontent.com/jhrtvapk-ops/JHRNOTEapp-logos/refs/heads/main/ic_launcher.png", VIP Channel {i+1}\n'
        playlist += f'#EXTVLCOPT:http-user-agent={user_agent}\n'
        if referer:
            playlist += f'#EXTVLCOPT:http-referrer={referer}\n'
        playlist += f"{clean_url}\n\n"
    
    VALID_PLAYLIST = playlist

@app.route('/add-link', methods=['POST'])
def add_link():
    data = request.json
    if not data or 'links' not in data:
        return {"status": "error", "message": "No links found"}, 400
    
    # 🌟 অ্যাপ থেকে লিংক আসামাত্রই ব্যাকগ্রাউন্ড থ্রেড চালু হয়ে যাবে (কোনো TIMEOUT হবে না)
    threading.Thread(target=background_processor, args=(data['links'],)).start()
    
    return {"status": "success", "message": "Processing safely in background"}

@app.route('/live.m3u', methods=['GET'])
def get_playlist():
    resp = Response(VALID_PLAYLIST, mimetype='application/vnd.apple.mpegurl')
    # 🌟 যেকোনো প্লেয়ারে (ExoPlayer/VLC) চলার জন্য CORS হেডার
    resp.headers["Access-Control-Allow-Origin"] = "*"
    return resp

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
