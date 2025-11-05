from flask import *
import yaml, copy
import os, sys, subprocess
import ipaddress
import logging

app = Flask(__name__)

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)

def get_client_ip():
    if 'CF-Connecting-IP' in request.headers:
        return request.headers['CF-Connecting-IP']
    forwarded_for = request.headers.get('X-Forwarded-For')
    if forwarded_for:
        return forwarded_for.split(',')[0]
    return request.remote_addr

def detectEndpoint(ipaddr):
    if isinstance(ipaddr, ipaddress.IPv4Address) or isinstance(ipaddr, ipaddress.IPv6Address):
        return True
    else:
        return False

def restartaxtm():
    try:
        subprocess.run(['sudo', 'systemctl', 'restart', 'axtm'], check=True)
        return True
    except Exception as e:
        app.logger.error(f"Error when restarting axtm: {e}")
        return False

def readConf(file):
    if not os.path.exists(file):
        return None
    with open(file, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    return data

if os.path.exists(os.path.join("config.yml")):
    data = readConf(os.path.join("config.yml"))
else:
    app.logger.error("Cannot find config.yml")
    sys.exit(1)

def dumpConf(key,srcaddr):
    try:
        data["configs"][key]["dst"] = srcaddr
        with open('config.yml', 'w') as file:
            yaml.dump(data, file, default_flow_style=False, allow_unicode=True, indent=4)
        return True
    except (IOError, yaml.YAMLError) as e:
        app.logger.error(f"Error dumping config: {e}")
        return False

@app.route("/")
def home():
    return jsonify({"status": 400, "detail": "Unsupported Request Method"})

@app.route('/updatedst', methods=["GET"])
def uploadHandle():
    insertkey = request.args.get("key",default=None)
    src = request.args.get("src",default=get_client_ip())
    if insertkey is None:
        return jsonify({"status": 400, "detail": "No API Key provided."}), 400

    configs = copy.deepcopy(data.get("configs", {}))
    if len(configs) == 0:
        return jsonify({"status": 400, "detail": "No valid config."}), 400

    if not detectEndpoint(src):
        return jsonify({"status": 400, "detail": "Given endpoint address is not valid."}), 400

    for key, value in configs.items():
        correct_api_key = value.get("apikey", None)
        if correct_api_key:
            if key and insertkey == correct_api_key:
                try:
                    dumpConf(key, src)
                    app.logger.info(f"Src address for {key} successfully update to {src}.")
                    restartaxtm()
                    return jsonify({"status": 200, "detail": "Source address Update successfully."})
                except Exception as e:
                    app.logger.error(f"Update Error from {key}: {e}")
                    return jsonify({"status": 500, "detail": "System Error Occurred."}), 500
        else:
            continue
    return jsonify({"status": 400, "detail": "Invalid API key."}), 400

@app.route('/robots.txt')
def robots():
    robots_content = '''User-agent: *
Disallow: /'''
    return Response(robots_content, mimetype='text/plain')
# Do not crawl by search engine

if __name__ == '__main__':
    if not data.get("api",{}).get("enable", False):
        app.logger.error("Error: API interface is not enabled.")
        sys.exit(1)
    app.logger.info("AXTM API Interface Started.")
    app.run(debug=True)