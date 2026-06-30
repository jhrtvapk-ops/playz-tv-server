from flask import Flask, request, Response
import requests
import concurrent.futures

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

@app.route('/add-link', methods=['POST'])
def add_link():
    global master_links, VALID_PLAYLIST
    data = request.json
    if not data or 'links' not in data:
        return {"status": "error", "message": "No links found"}, 400
    
    for link in data['links']:
        if link not in master_links:
            master_links.append(link)

    alive_links = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        results = executor.map(check_single_link, master_links)
        for res in results:
            if res:
                alive_links.append(res)
    
    master_links = alive_links

    playlist = "#EXTM3U\n\n"
    for i, link in enumerate(master_links):
        clean_url = link.split("|")[0] if "|" in link else link
        
        # 🌟 হেডার এক্সট্রাক্ট করা (VLC এর জন্য)
        user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
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
        
        # 🌟 VLC এর ভাষায় সিকিউরিটি হেডার বসানো
        playlist += f'#EXTVLCOPT:http-user-agent={user_agent}\n'
        if referer:
            playlist += f'#EXTVLCOPT:http-referrer={referer}\n'
        
        # 🌟 একদম ফ্রেশ লিংক (VLC এর জন্য কোনো পাইপ | ছাড়াই)
        playlist += f"{clean_url}\n\n"
    
    VALID_PLAYLIST = playlist
    return {"status": "success", "alive_count": len(master_links)}

@app.route('/live.m3u', methods=['GET'])
def get_playlist():
    resp = Response(VALID_PLAYLIST, mimetype='application/vnd.apple.mpegurl')
    resp.headers["Access-Control-Allow-Origin"] = "*"
    return resp

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
