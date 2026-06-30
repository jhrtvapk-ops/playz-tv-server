from flask import Flask, request, Response

app = Flask(__name__)

master_links = []
VALID_PLAYLIST = "#EXTM3U\n\n"

# 🌟 প্লেলিস্ট বিল্ডার (কোনো স্লো টেস্টিং ছাড়া ইনস্ট্যান্ট কাজ করবে)
def build_playlist():
    global master_links, VALID_PLAYLIST
    playlist = "#EXTM3U\n\n"
    
    for i, link in enumerate(master_links):
        clean_url = link.split("|")[0] if "|" in link else link
        user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        referer = ""
        
        # অ্যাপের পাঠানো সিকিউরিটি হেডারগুলো আলাদা করা
        if "|" in link:
            try:
                parts = link.split("|")[1].split("&")
                for p in parts:
                    if p.startswith("User-Agent="): user_agent = p.split("=")[1]
                    elif p.startswith("Referer="): referer = p.split("=")[1]
            except:
                pass

        playlist += f'#EXTINF:-1 tvg-logo="https://raw.githubusercontent.com/jhrtvapk-ops/JHRNOTEapp-logos/refs/heads/main/ic_launcher.png", VIP Live Channel {i+1}\n'
        
        # VLC এবং অন্যান্য প্লেয়ারের জন্য হেডার সেটআপ
        playlist += f'#EXTVLCOPT:http-user-agent={user_agent}\n'
        if referer:
            playlist += f'#EXTVLCOPT:http-referrer={referer}\n'
            
        playlist += f"{clean_url}\n\n"
    
    VALID_PLAYLIST = playlist

@app.route('/add-link', methods=['POST'])
def add_link():
    global master_links
    data = request.json
    if not data or 'links' not in data:
        return {"status": "error", "message": "No links found"}, 400
    
    added_new = False
    for link in data['links']:
        if link not in master_links:
            # 🌟 নতুন লিংক আসামাত্রই লিস্টের একদম ওপরে (1st position) বসিয়ে দিচ্ছি
            master_links.insert(0, link)
            added_new = True
            
    if added_new:
        # সাথে সাথে প্লেলিস্ট আপডেট!
        build_playlist()
        
    return {"status": "success", "total_links": len(master_links)}

@app.route('/live.m3u', methods=['GET'])
def get_playlist():
    # 🌟 যেকোনো প্লেয়ারে (ExoPlayer/VLC/TiviMate) সাপোর্ট করার জন্য
    resp = Response(VALID_PLAYLIST, mimetype='application/vnd.apple.mpegurl')
    resp.headers["Access-Control-Allow-Origin"] = "*"
    return resp

if __name__ == '__main__':
    # 🌟 রেন্ডারের পোর্ট অনুযায়ী রান করবে
    app.run(host='0.0.0.0', port=10000)
