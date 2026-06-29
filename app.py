from flask import Flask, request, Response
import requests
import concurrent.futures

app = Flask(__name__)

# আমাদের গ্লোবাল প্লেলিস্ট মেমোরি
master_links = []
VALID_PLAYLIST = "#EXTM3U\n\n"

# ফেক ব্রাউজার হেডার (যাতে স্পোর্টস সাইটগুলো আমাদের পাইথনকে ব্লক করতে না পারে)
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

# সিঙ্গেল লিংক চেকার (ডেড নাকি সচল)
def check_single_link(link):
    try:
        clean_url = link.split("|")[0] if "|" in link else link
        # HEAD রিকোয়েস্ট দিয়ে শুধু স্ট্যাটাস চেক করবে, তাই স্পিড হবে সুপার-ফাস্ট
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
    
    # অ্যাপ থেকে আসা নতুন লিংকগুলো রিসিভ করা
    for link in data['links']:
        if link not in master_links:
            master_links.append(link)

    # মাল্টি-থ্রেডিং দিয়ে একসাথে ১০টা করে লিংক চেক করা
    alive_links = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        results = executor.map(check_single_link, master_links)
        for res in results:
            if res:
                alive_links.append(res)
    
    # ডেড লিংক বাদ দিয়ে শুধু সচল লিংকগুলো মাস্টার লিস্টে রাখা
    master_links = alive_links

    # প্লেলিস্ট ফাইল জেনারেট করা
    playlist = "#EXTM3U\n\n"
    for i, link in enumerate(master_links):
        playlist += f'#EXTINF:-1 tvg-logo="https://raw.githubusercontent.com/jhrtvapk-ops/JHRNOTEapp-logos/refs/heads/main/ic_launcher.png", VIP Server Channel {i+1}\n'
        playlist += f"{link}\n\n"
    
    VALID_PLAYLIST = playlist
    return {"status": "success", "alive_count": len(master_links)}

@app.route('/live.m3u', methods=['GET'])
def get_playlist():
    # এই লিংকটাই বন্ধুদের দেবেন (যেকোনো প্লেয়ারে সাপোর্ট করবে)
    resp = Response(VALID_PLAYLIST, mimetype='application/vnd.apple.mpegurl')
    resp.headers["Access-Control-Allow-Origin"] = "*"
    return resp

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
