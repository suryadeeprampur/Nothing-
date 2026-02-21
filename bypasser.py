import base64
import hashlib
import json
import re
import time
from urllib.parse import quote, unquote, urlparse

import cloudscraper
import PyBypass
import requests
from bs4 import BeautifulSoup, NavigableString, Tag
from dotenv import load_dotenv
from lxml import etree
import os
from cfscrape import create_scraper

import ddl

load_dotenv()

GDTot_Crypt = os.environ.get("CRYPT","b0lDek5LSCt6ZjVRR2EwZnY4T1EvVndqeDRtbCtTWmMwcGNuKy8wYWpDaz0%3D")
Laravel_Session = os.environ.get("Laravel_Session","")
XSRF_TOKEN = os.environ.get("XSRF_TOKEN","")
DCRYPT = os.environ.get("DRIVEFIRE_CRYPT","cnhXOGVQNVlpeFZlM2lvTmN6Z2FPVWJiSjVBbWdVN0dWOEpvR3hHbHFLVT0%3D")
KCRYPT = os.environ.get("KOLOP_CRYPT","a1V1ZWllTnNNNEZtbkU4Y0RVd3pkRG5UREFJZFlUaC9GRko5NUNpTHNFcz0%3D")
HCRYPT = os.environ.get("HUBDRIVE_CRYPT","N25hV1pxMXZWUTdFWEh6L2Q2WFJyQWo2NGJEcWN6R2E5ci91aG8zSFF5Zz0%3D")
KATCRYPT = os.environ.get("KATDRIVE_CRYPT","bzQySHVKSkY0bEczZHlqOWRsSHZCazBkOGFDak9HWXc1emRTL1F6Rm9ubz0%3D")

############################################################
# Lists

linkvertise_list = [
    "linkvertise.com",
    "link-target.net",
    "link-center.net",
    "link-hub.net",
    "direct-link.net",
]

gdlist = [
    "appdrive",
    "driveapp",
    "drivehub",
    "gdflix",
    "drivesharer",
    "drivebit",
    "drivelinks",
    "driveace",
    "drivepro",
    "driveseed",
]

###############################################################

# index scrapper


def scrapeIndex(url, username="none", password="none"):
    def authorization_token(username, password):
        user_pass = f"{username}:{password}"
        return f"Basic {base64.b64encode(user_pass.encode()).decode()}"

    def decrypt(string):
        return base64.b64decode(string[::-1][24:-20]).decode("utf-8")

    def func(payload_input, url, username, password):
        next_page = False
        next_page_token = ""

        url = f"{url}/" if url[-1] != "/" else url

        try:
            headers = {"authorization": authorization_token(username, password)}
        except BaseException:
            return "username/password combination is wrong", None, None

        encrypted_response = requests.post(url, data=payload_input, headers=headers)
        if encrypted_response.status_code == 401:
            return "username/password combination is wrong", None, None

        try:
            decrypted_response = json.loads(decrypt(encrypted_response.text))
        except BaseException:
            return (
                "something went wrong. check index link/username/password field again",
                None,
                None,
            )

        page_token = decrypted_response["nextPageToken"]
        if page_token is None:
            next_page = False
        else:
            next_page = True
            next_page_token = page_token

        if list(decrypted_response.get("data").keys())[0] != "error":
            file_length = len(decrypted_response["data"]["files"])
            result = ""

            for i, _ in enumerate(range(file_length)):
                files_type = decrypted_response["data"]["files"][i]["mimeType"]
                if files_type != "application/vnd.google-apps.folder":
                    files_name = decrypted_response["data"]["files"][i]["name"]

                    direct_download_link = url + quote(files_name)
                    result += f"• {files_name} :\n{direct_download_link}\n\n"
            return result, next_page, next_page_token

    def format(result):
        long_string = "".join(result)
        new_list = []

        while len(long_string) > 0:
            if len(long_string) > 4000:
                split_index = long_string.rfind("\n\n", 0, 4000)
                if split_index == -1:
                    split_index = 4000
            else:
                split_index = len(long_string)

            new_list.append(long_string[:split_index])
            long_string = long_string[split_index:].lstrip("\n\n")

        return new_list

    # main
    x = 0
    next_page = False
    next_page_token = ""
    result = []

    payload = {"page_token": next_page_token, "page_index": x}
    print(f"Index Link: {url}\n")
    temp, next_page, next_page_token = func(payload, url, username, password)
    if temp is not None:
        result.append(temp)

    while next_page:
        payload = {"page_token": next_page_token, "page_index": x}
        temp, next_page, next_page_token = func(payload, url, username, password)
        if temp is not None:
            result.append(temp)
        x += 1

    if len(result) == 0:
        return None
    return format(result)


################################################################
def shortner_fpage_api(link):
    link_pattern = r"https?://[\w.-]+/full\?api=([^&]+)&url=([^&]+)(?:&type=(\d+))?"
    match = re.match(link_pattern, link)
    if match:
        try:
            url_enc_value = match.group(2)
            url_value = base64.b64decode(url_enc_value).decode("utf-8")
            return url_value
        except BaseException:
            return None
    else:
        return None

# Shortner Quick Link API

def shortner_quick_api(link):
    link_pattern = r"https?://[\w.-]+/st\?api=([^&]+)&url=([^&]+)"
    match = re.match(link_pattern, link)
    if match:
        try:
            url_value = match.group(2)
            return url_value
        except BaseException:
            return None
    else:
        return None
# AppDrive or DriveApp etc. Look-Alike Link and as well as the Account
# Details (Required for Login Required Links only)


def unified(url):
    if ddl.is_share_link(url):
        if "https://gdtot" in url:
            return ddl.gdtot(url)
        else:
            return ddl.sharer_scraper(url)

    try:
        Email = "OPTIONAL"
        Password = "OPTIONAL"

        account = {"email": Email, "passwd": Password}
        client = cloudscraper.create_scraper(allow_brotli=False)
        client.headers.update(
            {
                "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/97.0.4692.99 Safari/537.36"
            }
        )
        data = {"email": account["email"], "password": account["passwd"]}
        client.post(f"https://{urlparse(url).netloc}/login", data=data)
        res = client.get(url)
        key = re.findall('"key",\s+"(.*?)"', res.text)[0]
        ddl_btn = etree.HTML(res.content).xpath("//button[@id='drc']")
        info = re.findall(">(.*?)<\/li>", res.text)
        info_parsed = {}
        for item in info:
            kv = [s.strip() for s in item.split(":", maxsplit=1)]
            info_parsed[kv[0].lower()] = kv[1]
        info_parsed = info_parsed
        info_parsed["error"] = False
        info_parsed["link_type"] = "login"
        headers = {
            "Content-Type": f"multipart/form-data; boundary={'-'*4}_",
        }
        data = {"type": 1, "key": key, "action": "original"}
        if len(ddl_btn):
            info_parsed["link_type"] = "direct"
            data["action"] = "direct"
        while data["type"] <= 3:
            boundary = f'{"-"*6}_'
            data_string = ""
            for item in data:
                data_string += f"{boundary}\r\n"
                data_string += f'Content-Disposition: form-data; name="{item}"\r\n\r\n{data[item]}\r\n'
            data_string += f"{boundary}--\r\n"
            gen_payload = data_string
            try:
                response = client.post(url, data=gen_payload, headers=headers).json()
                break
            except BaseException:
                data["type"] += 1
        if "url" in response:
            info_parsed["gdrive_link"] = response["url"]
        elif "error" in response and response["error"]:
            info_parsed["error"] = True
            info_parsed["error_message"] = response["message"]
        else:
            info_parsed["error"] = True
            info_parsed["error_message"] = "Something went wrong :("
        if info_parsed["error"]:
            return info_parsed
        if "driveapp" in urlparse(url).netloc and not info_parsed["error"]:
            res = client.get(info_parsed["gdrive_link"])
            drive_link = etree.HTML(res.content).xpath(
                "//a[contains(@class,'btn')]/@href"
            )[0]
            info_parsed["gdrive_link"] = drive_link
        info_parsed["src_url"] = url
        if "drivehub" in urlparse(url).netloc and not info_parsed["error"]:
            res = client.get(info_parsed["gdrive_link"])
            drive_link = etree.HTML(res.content).xpath(
                "//a[contains(@class,'btn')]/@href"
            )[0]
            info_parsed["gdrive_link"] = drive_link
        if "gdflix" in urlparse(url).netloc and not info_parsed["error"]:
            res = client.get(info_parsed["gdrive_link"])
            drive_link = etree.HTML(res.content).xpath(
                "//a[contains(@class,'btn')]/@href"
            )[0]
            info_parsed["gdrive_link"] = drive_link

        if "drivesharer" in urlparse(url).netloc and not info_parsed["error"]:
            res = client.get(info_parsed["gdrive_link"])
            drive_link = etree.HTML(res.content).xpath(
                "//a[contains(@class,'btn')]/@href"
            )[0]
            info_parsed["gdrive_link"] = drive_link
        if "drivebit" in urlparse(url).netloc and not info_parsed["error"]:
            res = client.get(info_parsed["gdrive_link"])
            drive_link = etree.HTML(res.content).xpath(
                "//a[contains(@class,'btn')]/@href"
            )[0]
            info_parsed["gdrive_link"] = drive_link
        if "drivelinks" in urlparse(url).netloc and not info_parsed["error"]:
            res = client.get(info_parsed["gdrive_link"])
            drive_link = etree.HTML(res.content).xpath(
                "//a[contains(@class,'btn')]/@href"
            )[0]
            info_parsed["gdrive_link"] = drive_link
        if "driveace" in urlparse(url).netloc and not info_parsed["error"]:
            res = client.get(info_parsed["gdrive_link"])
            drive_link = etree.HTML(res.content).xpath(
                "//a[contains(@class,'btn')]/@href"
            )[0]
            info_parsed["gdrive_link"] = drive_link
        if "drivepro" in urlparse(url).netloc and not info_parsed["error"]:
            res = client.get(info_parsed["gdrive_link"])
            drive_link = etree.HTML(res.content).xpath(
                "//a[contains(@class,'btn')]/@href"
            )[0]
            info_parsed["gdrive_link"] = drive_link
        if info_parsed["error"]:
            return "Faced an Unknown Error!"
        return info_parsed["gdrive_link"]
    except BaseException:
        return "Unable to Extract GDrive Link"


# appdrive/pack


def appdrivepack(url):
    r = requests.get(url)
    htmlContent = r.content
    soup = BeautifulSoup(htmlContent, "html.parser")
    appdrive = soup.find_all("a")
    all_links = set()
    for i in appdrive:
        if i.get("href") not in ["/", "#", ""] and "/file/" in i.get("href"):
            if i.get("href").startswith("http"):
                link = i.get("href")
            else:
                link = "https://appdrive.me" + i.get("href")
            all_links.add(link)
    url = ""
    for l in all_links:
        link = unified(l)
        url += link + "\n\n"
    return url


################################################################


def try2link_bypass(url):
    client = cloudscraper.create_scraper(allow_brotli=False)

    url = url[:-1] if url[-1] == "/" else url

    params = (("d", int(time.time()) + (60 * 4)),)
    r = client.get(url, params=params, headers={"Referer": "https://newforex.online/"})

    soup = BeautifulSoup(r.text, "html.parser")
    inputs = soup.find(id="go-link").find_all(name="input")
    data = {input.get("name"): input.get("value") for input in inputs}
    time.sleep(7)

    headers = {
        "Host": "try2link.com",
        "X-Requested-With": "XMLHttpRequest",
        "Origin": "https://try2link.com",
        "Referer": url,
    }

    bypassed_url = client.post(
        "https://try2link.com/links/go", headers=headers, data=data
    )
    return bypassed_url.json()["url"]


def try2link_scrape(url):
    client = cloudscraper.create_scraper(allow_brotli=False)
    h = {
        "upgrade-insecure-requests": "1",
        "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/105.0.0.0 Safari/537.36",
    }
    res = client.get(url, cookies={}, headers=h)
    url = "https://try2link.com/" + re.findall("try2link\.com\/(.*?) ", res.text)[0]
    return try2link_bypass(url)


def psa_bypasser(psa_url):
    client = cloudscraper.create_scraper(allow_brotli=False)
    r = client.get(psa_url)
    soup = BeautifulSoup(r.text, "html.parser").find_all(
        class_="dropshadowboxes-drop-shadow dropshadowboxes-rounded-corners dropshadowboxes-inside-and-outside-shadow dropshadowboxes-lifted-both dropshadowboxes-effect-default"
    )
    links = ""
    for link in soup:
        try:
            exit_gate = link.a.get("href")
            links = links + try2link_scrape(exit_gate) + "\n"
        except BaseException:
            pass
    return links


##########################################################################
# rocklinks


def rocklinks(url):
    client = cloudscraper.create_scraper(allow_brotli=False)
    DOMAIN = "https://lnks.primarchweb.in/"
    url = url[:-1] if url[-1] == "/" else url
    code = url.split("/")[-1]
    final_url = f"{DOMAIN}/{code}"
    ref = "https://blog.disheye.com/"
    h = {"referer": ref}
    resp = client.get(final_url, headers=h)
    soup = BeautifulSoup(resp.content, "html.parser")
    try:
        inputs = soup.find_all("input")
    except BaseException:
        return "Incorrect Link"
    data = {input.get("name"): input.get("value") for input in inputs}
    h = {"x-requested-with": "XMLHttpRequest"}
    time.sleep(8)
    r = client.post(f"{DOMAIN}/links/go", data=data, headers=h)
    try:
        return r.json()["url"]
    except BaseException:
        return "Something went wrong :("


################################################
# igg games


def decodeKey(encoded):
    key = ""

    i = len(encoded) // 2 - 5
    while i >= 0:
        key += encoded[i]
        i = i - 2

    i = len(encoded) // 2 + 4
    while i < len(encoded):
        key += encoded[i]
        i = i + 2

    return key


def bypassBluemediafiles(url, torrent=False):
    headers = {
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:103.0) Gecko/20100101 Firefox/103.0",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
        "Alt-Used": "bluemediafiles.com",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "none",
        "Sec-Fetch-User": "?1",
    }

    res = requests.get(url, headers=headers)
    soup = BeautifulSoup(res.text, "html.parser")
    script = str(soup.findAll("script")[3])
    encodedKey = script.split('Create_Button("')[1].split('");')[0]

    headers = {
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:103.0) Gecko/20100101 Firefox/103.0",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
        "Referer": url,
        "Alt-Used": "bluemediafiles.com",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "same-origin",
        "Sec-Fetch-User": "?1",
    }

    params = {"url": decodeKey(encodedKey)}

    if torrent:
        res = requests.get(
            "https://dl.pcgamestorrents.org/get-url.php", params=params, headers=headers
        )
        soup = BeautifulSoup(res.text, "html.parser")
        furl = soup.find("a", class_="button").get("href")

    else:
        res = requests.get(
            "https://bluemediafiles.com/get-url.php", params=params, headers=headers
        )
        furl = res.url
        if "mega.nz" in furl:
            furl = furl.replace("mega.nz/%23!", "mega.nz/file/").replace("!", "#")

    # print(furl)
    return furl


def igggames(url):
    res = requests.get(url)
    soup = BeautifulSoup(res.text, "html.parser")
    soup = soup.find("div", class_="uk-margin-medium-top").findAll("a")

    bluelist = []
    for ele in soup:
        bluelist.append(ele.get("href"))
    bluelist = bluelist[6:-1]

    links = ""
    for ele in bluelist:
        if "bluemediafiles" in ele:
            links = links + bypassBluemediafiles(ele) + "\n"
        elif "pcgamestorrents.com" in ele:
            res = requests.get(ele)
            soup = BeautifulSoup(res.text, "html.parser")
            turl = (
                soup.find(
                    "p", class_="uk-card uk-card-body uk-card-default uk-card-hover"
                )
                .find("a")
                .get("href")
            )
            links = links + bypassBluemediafiles(turl, True) + "\n"
        else:
            links = links + ele + "\n"

    return links[:-1]


###################################################
# script links


def getfinal(domain, url, sess):
    # sess = requests.session()
    res = sess.get(url)
    soup = BeautifulSoup(res.text, "html.parser")
    soup = soup.find("form").findAll("input")
    datalist = []
    for ele in soup:
        datalist.append(ele.get("value"))

    data = {
        "_method": datalist[0],
        "_csrfToken": datalist[1],
        "ad_form_data": datalist[2],
        "_Token[fields]": datalist[3],
        "_Token[unlocked]": datalist[4],
    }

    sess.headers = {
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:103.0) Gecko/20100101 Firefox/103.0",
        "Accept": "application/json, text/javascript, */*; q=0.01",
        "Accept-Language": "en-US,en;q=0.5",
        "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
        "X-Requested-With": "XMLHttpRequest",
        "Origin": domain,
        "Connection": "keep-alive",
        "Referer": url,
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "same-origin",
    }

    # print("waiting 10 secs")
    time.sleep(10)  # important
    response = sess.post(domain + "/links/go", data=data).json()
    furl = response["url"]
    return furl


def getfirst(url):
    sess = requests.session()
    res = sess.get(url)

    soup = BeautifulSoup(res.text, "html.parser")
    soup = soup.find("form")
    action = soup.get("action")
    soup = soup.findAll("input")
    datalist = []
    for ele in soup:
        datalist.append(ele.get("value"))
    sess.headers = {
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:103.0) Gecko/20100101 Firefox/103.0",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
        "Origin": action,
        "Connection": "keep-alive",
        "Referer": action,
        "Upgrade-Insecure-Requests": "1",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "same-origin",
        "Sec-Fetch-User": "?1",
    }

    data = {"newwpsafelink": datalist[1], "g-recaptcha-response": RecaptchaV3()}
    response = sess.post(action, data=data)
    soup = BeautifulSoup(response.text, "html.parser")
    soup = soup.findAll("div", class_="wpsafe-bottom text-center")
    for ele in soup:
        rurl = ele.find("a").get("onclick")[13:-12]

    res = sess.get(rurl)
    furl = res.url
    # print(furl)
    return getfinal(f'https://{furl.split("/")[-2]}/', furl, sess)


##########################################################################
# ez4short


def ez4(url):
    client = cloudscraper.create_scraper(allow_brotli=False)
    DOMAIN = "https://ez4short.com"
    ref = "https://tech5s.co/"
    h = {"referer": ref}
    resp = client.get(url, headers=h)
    soup = BeautifulSoup(resp.content, "html.parser")
    inputs = soup.find_all("input")
    data = {input.get("name"): input.get("value") for input in inputs}
    h = {"x-requested-with": "XMLHttpRequest"}
    time.sleep(8)
    r = client.post(f"{DOMAIN}/links/go", data=data, headers=h)
    try:
        return r.json()["url"]
    except BaseException:
        return "Something went wrong :("


##################################################
# mediafire


def mediafire(url):
    res = requests.get(url, stream=True)
    contents = res.text

    for line in contents.splitlines():
        m = re.search(r'href="((http|https)://download[^"]+)', line)
        if m:
            return m.groups()[0]


####################################################
# zippyshare


def zippyshare(url):
    resp = requests.get(url).text
    surl = resp.split("document.getElementById('dlbutton').href = ")[1].split(";")[0]
    parts = surl.split("(")[1].split(")")[0].split(" ")
    val = str(int(parts[0]) % int(parts[2]) + int(parts[4]) % int(parts[6]))
    surl = surl.split('"')
    burl = url.split("zippyshare.com")[0]
    furl = burl + "zippyshare.com" + surl[1] + val + surl[-2]
    return furl


####################################################
# filercrypt


def getlinks(dlc, client):
    headers = {
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:103.0) Gecko/20100101 Firefox/103.0",
        "Accept": "application/json, text/javascript, */*",
        "Accept-Language": "en-US,en;q=0.5",
        "X-Requested-With": "XMLHttpRequest",
        "Origin": "http://dcrypt.it",
        "Connection": "keep-alive",
        "Referer": "http://dcrypt.it/",
    }

    data = {
        "content": dlc,
    }

    response = client.post(
        "http://dcrypt.it/decrypt/paste", headers=headers, data=data
    ).json()["success"]["links"]
    links = ""
    for link in response:
        links = links + link + "\n"
    return links[:-1]


def filecrypt(url):
    client = cloudscraper.create_scraper(allow_brotli=False)
    headers = {
        "authority": "filecrypt.co",
        "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
        "accept-language": "en-US,en;q=0.9",
        "cache-control": "max-age=0",
        "content-type": "application/x-www-form-urlencoded",
        "origin": "https://filecrypt.co",
        "referer": url,
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/105.0.0.0 Safari/537.36",
    }

    resp = client.get(url, headers=headers)
    soup = BeautifulSoup(resp.content, "html.parser")

    buttons = soup.find_all("button")
    for ele in buttons:
        line = ele.get("onclick")
        if line is not None and "DownloadDLC" in line:
            dlclink = (
                "https://filecrypt.co/DLC/"
                + line.split("DownloadDLC('")[1].split("'")[0]
                + ".html"
            )
            break

    resp = client.get(dlclink, headers=headers)
    return getlinks(resp.text)


#####################################################
# dropbox


def dropbox(url):
    return (
        url.replace("www.", "")
        .replace("dropbox.com", "dl.dropboxusercontent.com")
        .replace("?dl=0", "")
    )


######################################################
# shareus


def shareus(url):
    headers = {'user-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36',}
    DOMAIN = "https://us-central1-my-apps-server.cloudfunctions.net"
    sess = requests.session()

    code = url.split("/")[-1]
    params = {'shortid': code, 'initial': 'true', 'referrer': 'https://shareus.io/',}
    response = requests.get(f'{DOMAIN}/v', params=params, headers=headers)

    for i in range(1,4):
        json_data = {'current_page': i,}
        response = sess.post(f'{DOMAIN}/v', headers=headers, json=json_data)

    response = sess.get(f'{DOMAIN}/get_link', headers=headers).json()
    return response["link_info"]["destination"]

def shrslink(url):
    client = cloudscraper.create_scraper(allow_brotli=False)
    DOMAIN = "https://shrs.link"
    url = url[:-1] if url[-1] == "/" else url
    code = url.split("/")[-1]
    final_url = f"{DOMAIN}/{code}"
    ref = "https://jobform.in/"
    h = {"referer": ref}
    resp = client.get(final_url, headers=h)
    soup = BeautifulSoup(resp.content, "html.parser")
    inputs = soup.find_all("input")
    data = {input.get("name"): input.get("value") for input in inputs}
    h = {"x-requested-with": "XMLHttpRequest"}
    time.sleep(5)
    r = client.post(f"{DOMAIN}/links/go", data=data, headers=h)
    try:
        return r.json()["url"]
    except BaseException:
        return "Something went wrong :("

#######################################################
# shortingly


def shortingly(url):
    client = cloudscraper.create_scraper(allow_brotli=False)
    DOMAIN = "https://shortingly.in"
    url = url[:-1] if url[-1] == "/" else url
    code = url.split("/")[-1]
    final_url = f"{DOMAIN}/{code}"
    ref = "https://tech.gyanitheme.com/"
    h = {"referer": ref}
    resp = client.get(final_url, headers=h)
    soup = BeautifulSoup(resp.content, "html.parser")
    inputs = soup.find_all("input")
    data = {input.get("name"): input.get("value") for input in inputs}
    h = {"x-requested-with": "XMLHttpRequest"}
    time.sleep(5)
    r = client.post(f"{DOMAIN}/links/go", data=data, headers=h)
    try:
        return r.json()["url"]
    except BaseException:
        return "Something went wrong :("

def shortinglyclick(url):
    client = cloudscraper.create_scraper(allow_brotli=False)
    DOMAIN = "https://pass.gyanitheme.com/"
    url = url[:-1] if url[-1] == "/" else url
    code = url.split("/")[-1]
    final_url = f"{DOMAIN}/{code}"
    ref = "https://www.techkhulasha.com/"
    h = {"referer": ref}
    resp = client.get(final_url, headers=h)
    soup = BeautifulSoup(resp.content, "html.parser")
    inputs = soup.find_all("input")
    data = {input.get("name"): input.get("value") for input in inputs}
    h = {"x-requested-with": "XMLHttpRequest"}
    time.sleep(5)
    r = client.post(f"{DOMAIN}/links/go", data=data, headers=h)
    try:
        return r.json()["url"]
    except BaseException:
        return "Something went wrong :("


#######################################################
# Gyanilinks - gtlinks.me


#def gyanilinks(url):
#    DOMAIN = "https://go.hipsonyc.com/"
#    client = cloudscraper.create_scraper(allow_brotli=False)
#    url = url[:-1] if url[-1] == '/' else url
#    code = url.split("/")[-1]
#    final_url = f"{DOMAIN}/{code}"
#    resp = client.get(final_url)
#    soup = BeautifulSoup(resp.content, "html.parser")
#    try: inputs = soup.find(id="go-link").find_all(name="input")
#    except: return "Incorrect Link"
#    data = { input.get('name'): input.get('value') for input in inputs }
#    h = { "x-requested-with": "XMLHttpRequest" }
#    time.sleep(10)
#    r = client.post(f"{DOMAIN}/links/go", data=data, headers=h)
#    try: return r.json()['url']
#    except: return "Something went wrong :("

def gyanilinks(url):
    client = cloudscraper.create_scraper(allow_brotli=False)
    DOMAIN = "https://golink.gyanitheme.com/"
    url = url[:-1] if url[-1] == "/" else url
    code = url.split("/")[-1]
    final_url = f"{DOMAIN}/{code}"
    ref = "https://tech.hipsonyc.com/"
    h = {"referer": ref}
    resp = client.get(final_url, headers=h)
    soup = BeautifulSoup(resp.content, "html.parser")
    inputs = soup.find_all("input")
    data = {input.get("name"): input.get("value") for input in inputs}
    h = {"x-requested-with": "XMLHttpRequest"}
    time.sleep(8)
    r = client.post(f"{DOMAIN}/links/go", data=data, headers=h)
    try:
        return str(r.json()["url"])
    except BaseException:
        return "Something went wrong :("

def destined(url):
    DOMAIN = "https://destined.editionx.online"
    client = cloudscraper.create_scraper(allow_brotli=False)
    url = url[:-1] if url[-1] == '/' else url
    code = url.split("/")[-1]
    final_url = f"{DOMAIN}/{code}"
    resp = client.get(final_url)
    soup = BeautifulSoup(resp.content, "html.parser")
    try: inputs = soup.find(id="go-link").find_all(name="input")
    except: return "Incorrect Link"
    data = { input.get('name'): input.get('value') for input in inputs }
    h = { "x-requested-with": "XMLHttpRequest" }
    time.sleep(5)
    r = client.post(f"{DOMAIN}/links/go", data=data, headers=h)
    try: return r.json()['url']
    except: return "Something went wrong :("




# Flashlink


def flashlink(url):
    DOMAIN = "https://files.cordtpoint.co.in"
    url = url[:-1] if url[-1] == "/" else url
    code = url.split("/")[-1]
    final_url = f"{DOMAIN}/{code}"
    client = cloudscraper.create_scraper(allow_brotli=False)
    resp = client.get(final_url)
    soup = BeautifulSoup(resp.content, "html.parser")
    inputs = soup.find(id="go-link").find_all(name="input")
    data = {input.get("name"): input.get("value") for input in inputs}
    h = {"x-requested-with": "XMLHttpRequest"}
    time.sleep(15)
    r = client.post(f"{DOMAIN}/links/go", data=data, headers=h)
    return r.json()["url"]


# short2url

def short2url(url):
    client = cloudscraper.create_scraper(allow_brotli=False)
    DOMAIN = "https://techyuth.xyz/blog/"
    url = url[:-1] if url[-1] == "/" else url
    code = url.split("/")[-1]
    final_url = f"{DOMAIN}/{code}"
    ref = "https://blog.mphealth.online/"
    h = {"referer": ref}
    resp = client.get(final_url, headers=h)
    soup = BeautifulSoup(resp.content, "html.parser")
    inputs = soup.find_all("input")
    data = {input.get("name"): input.get("value") for input in inputs}
    h = {"x-requested-with": "XMLHttpRequest"}
    time.sleep(8)
    r = client.post(f"{DOMAIN}/links/go", data=data, headers=h)
    try:
        return str(r.json()["url"])
    except BaseException:
        return "Something went wrong :("

#######################################################
# anonfiles


def anonfile(url):
    headersList = {"Accept": "*/*"}
    payload = ""

    response = requests.request(
        "GET", url, data=payload, headers=headersList
    ).text.split("\n")
    for ele in response:
        if (
            "https://cdn" in ele
            and "anonfiles.com" in ele
            and url.split("/")[-2] in ele
        ):
            break

    return ele.split('href="')[1].split('"')[0]


##########################################################
# pixl


def pixl(url):
    count = 1
    dl_msg = ""
    currentpage = 1
    settotalimgs = True
    totalimages = ""
    client = cloudscraper.create_scraper(allow_brotli=False)
    resp = client.get(url)
    if resp.status_code == 404:
        return "File not found/The link you entered is wrong!"
    soup = BeautifulSoup(resp.content, "html.parser")
    if "album" in url and settotalimgs:
        totalimages = soup.find("span", {"data-text": "image-count"}).text
        settotalimgs = False
    thmbnailanch = soup.findAll(attrs={"class": "--media"})
    links = soup.findAll(attrs={"data-pagination": "next"})
    try:
        url = links[0].attrs["href"]
    except BaseException:
        url = None
    for ref in thmbnailanch:
        imgdata = client.get(ref.attrs["href"])
        if not imgdata.status_code == 200:
            time.sleep(5)
            continue
        imghtml = BeautifulSoup(imgdata.text, "html.parser")
        downloadanch = imghtml.find(attrs={"class": "btn-download"})
        currentimg = downloadanch.attrs["href"]
        currentimg = currentimg.replace(" ", "%20")
        dl_msg += f"{count}. {currentimg}\n"
        count += 1
    currentpage += 1
    fld_msg = f"Your provided Pixl.is link is of Folder and I've Found {count - 1} files in the folder.\n"
    fld_link = f"\nFolder Link: {url}\n"
    final_msg = fld_link + "\n" + fld_msg + "\n" + dl_msg
    return final_msg


############################################################
# sirigan  ( unused )


def siriganbypass(url):
    client = requests.Session()
    res = client.get(url)
    url = res.url.split("=", maxsplit=1)[-1]

    while True:
        try:
            url = base64.b64decode(url).decode("utf-8")
        except BaseException:
            break

    return url.split("url=")[-1]


############################################################
# shorte


def sh_st_bypass(url):
    client = requests.Session()
    client.headers.update({"referer": url})
    p = urlparse(url)

    res = client.get(url)

    sess_id = re.findall("""sessionId(?:\s+)?:(?:\s+)?['|"](.*?)['|"]""", res.text)[0]

    final_url = f"{p.scheme}://{p.netloc}/shortest-url/end-adsession"
    params = {"adSessionId": sess_id, "callback": "_"}
    time.sleep(5)  # !important

    res = client.get(final_url, params=params)
    dest_url = re.findall('"(.*?)"', res.text)[1].replace("\/", "/")

    return {"src": url, "dst": dest_url}["dst"]


#############################################################
# gofile


def gofile_dl(url, password=""):
    api_uri = "https://api.gofile.io"
    client = requests.Session()
    res = client.get(api_uri + "/createAccount").json()

    data = {
        "contentId": url.split("/")[-1],
        "token": res["data"]["token"],
        "websiteToken": "12345",
        "cache": "true",
        "password": hashlib.sha256(password.encode("utf-8")).hexdigest(),
    }
    res = client.get(api_uri + "/getContent", params=data).json()

    content = []
    for item in res["data"]["contents"].values():
        content.append(item)

    return {"accountToken": data["token"], "files": content}["files"][0]["link"]


################################################################
# sharer pw


def parse_info_sharer(res):
    f = re.findall(">(.*?)<\/td>", res.text)
    info_parsed = {}
    for i in range(0, len(f), 3):
        info_parsed[f[i].lower().replace(" ", "_")] = f[i + 2]
    return info_parsed


##################################################################
# adfly


def decrypt_url(code):
    a, b = "", ""
    for i in range(0, len(code)):
        if i % 2 == 0:
            a += code[i]
        else:
            b = code[i] + b
    key = list(a + b)
    i = 0
    while i < len(key):
        if key[i].isdigit():
            for j in range(i + 1, len(key)):
                if key[j].isdigit():
                    u = int(key[i]) ^ int(key[j])
                    if u < 10:
                        key[i] = str(u)
                    i = j
                    break
        i += 1
    key = "".join(key)
    decrypted = base64.b64decode(key)[16:-16]
    return decrypted.decode("utf-8")


def adfly(url):
    client = cloudscraper.create_scraper(allow_brotli=False)
    res = client.get(url).text
    out = {"error": False, "src_url": url}
    try:
        ysmm = re.findall("ysmm\s+=\s+['|\"](.*?)['|\"]", res)[0]
    except BaseException:
        out["error"] = True
        return out
    url = decrypt_url(ysmm)
    if re.search(r"go\.php\?u\=", url):
        url = base64.b64decode(re.sub(r"(.*?)u=", "", url)).decode()
    elif "&dest=" in url:
        url = unquote(re.sub(r"(.*?)dest=", "", url))
    out["bypassed_url"] = url
    return out


##########################################################################
# gplinks
def gplinks(url: str):
    client = cloudscraper.create_scraper(allow_brotli=False)
    token = url.split("/")[-1]
    domain ="https://gplinks.co/"
    referer = "https://revadvert.com/"
    vid = client.get(url, allow_redirects= False).headers["Location"].split("=")[-1]
    url = f"{url}/?{vid}"
    response = client.get(url, allow_redirects=False)
    soup = BeautifulSoup(response.content, "html.parser")
    inputs = soup.find(id="go-link").find_all(name="input")
    data = { input.get('name'): input.get('value') for input in inputs }
    time.sleep(10)
    headers={"x-requested-with": "XMLHttpRequest"}
    bypassed_url = client.post(domain+"links/go", data=data, headers=headers).json()["url"]
    try: return bypassed_url
    except: return 'Something went wrong :('


##########################################################################
# droplink


def droplink(url):
    client = cloudscraper.create_scraper(allow_brotli=False)
    res = client.get(url, timeout=5)

    ref = re.findall("action[ ]{0,}=[ ]{0,}['|\"](.*?)['|\"]", res.text)[0]
    h = {"referer": ref}
    res = client.get(url, headers=h)

    bs4 = BeautifulSoup(res.content, "html.parser")
    inputs = bs4.find_all("input")
    data = {input.get("name"): input.get("value") for input in inputs}
    h = {
        "content-type": "application/x-www-form-urlencoded",
        "x-requested-with": "XMLHttpRequest",
    }

    p = urlparse(url)
    final_url = f"{p.scheme}://{p.netloc}/links/go"
    time.sleep(3.1)
    res = client.post(final_url, data=data, headers=h).json()

    if res["status"] == "success":
        return res["url"]
    return "Something went wrong :("


##########################################################################
# link vertise


def linkvertise(url):
    params = {
        "url": url,
    }
    response = requests.get("https://bypass.pm/bypass2", params=params).json()
    if response["success"]:
        return response["destination"]
    else:
        return response["msg"]


##########################################################################
# others

# api from https://github.com/bypass-vip/bypass.vip


def others(url):
    try:
        payload = {"url": url}
        url_bypass = requests.post("https://api.bypass.vip/", data=payload).json()
        bypassed = url_bypass["destination"]
        return bypassed
    except BaseException:
        return "Could not Bypass your URL :("


##########################################################################
# ouo

# RECAPTCHA v3 BYPASS
# code from https://github.com/xcscxr/Recaptcha-v3-bypass


def RecaptchaV3(
    ANCHOR_URL="https://www.google.com/recaptcha/api2/anchor?ar=1&k=6Lcr1ncUAAAAAH3cghg6cOTPGARa8adOf-y9zv2x&co=aHR0cHM6Ly9vdW8uaW86NDQz&hl=en&v=1B_yv3CBEV10KtI2HJ6eEXhJ&size=invisible&cb=4xnsug1vufyr",
):
    url_base = "https://www.google.com/recaptcha/"
    post_data = "v={}&reason=q&c={}&k={}&co={}"
    client = requests.Session()
    client.headers.update({"content-type": "application/x-www-form-urlencoded"})
    matches = re.findall("([api2|enterprise]+)\/anchor\?(.*)", ANCHOR_URL)[0]
    url_base += matches[0] + "/"
    params = matches[1]
    res = client.get(url_base + "anchor", params=params)
    token = re.findall(r'"recaptcha-token" value="(.*?)"', res.text)[0]
    params = dict(pair.split("=") for pair in params.split("&"))
    post_data = post_data.format(params["v"], token, params["k"], params["co"])
    res = client.post(url_base + "reload", params=f'k={params["k"]}', data=post_data)
    answer = re.findall(r'"rresp","(.*?)"', res.text)[0]
    return answer


# code from https://github.com/xcscxr/ouo-bypass/
def ouo(url):
    client = requests.Session()
    tempurl = url.replace("ouo.press", "ouo.io")
    p = urlparse(tempurl)
    id = tempurl.split("/")[-1]

    res = client.get(tempurl)
    next_url = f"{p.scheme}://{p.hostname}/go/{id}"

    for _ in range(2):
        if res.headers.get("Location"):
            break
        bs4 = BeautifulSoup(res.content, "lxml")
        inputs = bs4.form.findAll("input", {"name": re.compile(r"token$")})
        data = {input.get("name"): input.get("value") for input in inputs}

        ans = RecaptchaV3()
        data["x-token"] = ans
        h = {"content-type": "application/x-www-form-urlencoded"}
        res = client.post(next_url, data=data, headers=h, allow_redirects=False)
        next_url = f"{p.scheme}://{p.hostname}/xreallcygo/{id}"

    return res.headers.get("Location")


##########################################################################
# mdisk


def mdisk(url):
    header = {
        "Accept": "*/*",
        "Accept-Language": "en-US,en;q=0.5",
        "Accept-Encoding": "gzip, deflate, br",
        "Referer": "https://mdisk.me/",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/93.0.4577.82 Safari/537.36",
    }

    inp = url
    fxl = inp.split("/")
    cid = fxl[-1]

    URL = f"https://diskuploader.entertainvideo.com/v1/file/cdnurl?param={cid}"
    res = requests.get(url=URL, headers=header).json()
    return res["download"] + "\n\n" + res["source"]


##########################################################################
# pixeldrain


def pixeldrain(url):
    api = "https://api.emilyx.in/api"
    client = cloudscraper.create_scraper(allow_brotli=False)
    resp = client.get(url)
    if resp.status_code == 404:
        return "File not found/The link you entered is wrong!"
    try:
        resp = client.post(api, json={"type": "pixeldrain", "url": url})
        res = resp.json()
    except BaseException:
        return "API UnResponsive / Invalid Link !"
    if res["success"] is True:
        return res["url"]
    else:
        return res["msg"]


##########################################################################
# we transfer


def wetransfer(url):
    api = "https://api.emilyx.in/api"
    client = cloudscraper.create_scraper(allow_brotli=False)
    resp = client.get(url)
    if resp.status_code == 404:
        return "File not found/The link you entered is wrong!"
    try:
        resp = client.post(api, json={"type": "wetransfer", "url": url})
        res = resp.json()
    except BaseException:
        return "API UnResponsive / Invalid Link !"
    if res["success"] is True:
        return res["url"]
    else:
        return res["msg"]


##########################################################################
# megaup


def megaup(url):
    api = "https://api.emilyx.in/api"
    client = cloudscraper.create_scraper(allow_brotli=False)
    resp = client.get(url)
    if resp.status_code == 404:
        return "File not found/The link you entered is wrong!"
    try:
        resp = client.post(api, json={"type": "megaup", "url": url})
        res = resp.json()
    except BaseException:
        return "API UnResponsive / Invalid Link !"
    if res["success"] is True:
        return res["url"]
    else:
        return res["msg"]


##########################################################################

##########################################################################
# urlsopen


def urlsopen(url):
    client = cloudscraper.create_scraper(allow_brotli=False)
    DOMAIN = "https://blogpost.viewboonposts.com/ssssssagasdgeardggaegaqe"
    url = url[:-1] if url[-1] == "/" else url
    code = url.split("/")[-1]
    final_url = f"{DOMAIN}/{code}"
    ref = "https://blog.textpage.xyz/"
    h = {"referer": ref}
    resp = client.get(final_url, headers=h)
    soup = BeautifulSoup(resp.content, "html.parser")
    inputs = soup.find_all("input")
    data = {input.get("name"): input.get("value") for input in inputs}
    h = {"x-requested-with": "XMLHttpRequest"}
    time.sleep(2)
    r = client.post(f"{DOMAIN}/links/go", data=data, headers=h)
    try:
        return r.json()["url"]
    except BaseException:
        return "Something went wrong :("


##########################################################################
# xpshort


def xpshort(url):
    client = cloudscraper.create_scraper(allow_brotli=False)
    DOMAIN = "https://xpshort.com"
    url = url[:-1] if url[-1] == "/" else url
    code = url.split("/")[-1]
    final_url = f"{DOMAIN}/{code}"
    ref = "https://www.newspadj.in/"
    #ref = "https://www.twinthrottlers.xyz/"
    #ref = "https://www.animalwallpapers.online/"
    h = {"referer": ref}
    resp = client.get(final_url, headers=h)
    soup = BeautifulSoup(resp.content, "html.parser")
    inputs = soup.find_all("input")
    data = {input.get("name"): input.get("value") for input in inputs}
    h = {"x-requested-with": "XMLHttpRequest"}
    time.sleep(8)
    r = client.post(f"{DOMAIN}/links/go", data=data, headers=h)
    try:
        return r.json()["url"]
    except BaseException:
        return "Something went wrong :("


##########################################################################
# dulink


def dulink(url):
    client = cloudscraper.create_scraper(allow_brotli=False)
    DOMAIN = "https://du-link.in"
    url = url[:-1] if url[-1] == "/" else url
    ref = "https://profitshort.com/"
    h = {"referer": ref}
    resp = client.get(url, headers=h)
    soup = BeautifulSoup(resp.content, "html.parser")
    inputs = soup.find_all("input")
    data = {input.get("name"): input.get("value") for input in inputs}
    h = {"x-requested-with": "XMLHttpRequest"}
    r = client.post(f"{DOMAIN}/links/go", data=data, headers=h)
    try:
        return r.json()["url"]
    except BaseException:
        return "Something went wrong :("


# nanolinks


def nanolinks(url):
    client = cloudscraper.create_scraper(allow_brotli=False)
    DOMAIN = "https://nanolinks.in"
    url = url[:-1] if url[-1] == "/" else url
    ref = "https://computerpedia.in/"
    h = {"referer": ref}
    resp = client.get(url, headers=h)
    soup = BeautifulSoup(resp.content, "html.parser")
    inputs = soup.find_all("input")
    data = {input.get("name"): input.get("value") for input in inputs}
    h = {"x-requested-with": "XMLHttpRequest"}
    r = client.post(f"{DOMAIN}/links/go", data=data, headers=h)
    try:
        return r.json()["url"]
    except BaseException:
        return "Something went wrong :("


# mdiskinnet


def mdiskinnet(url):
    client = cloudscraper.create_scraper(allow_brotli=False)
    DOMAIN = "https://mdisk.in.net/convertor/160x67"
    url = url[:-1] if url[-1] == "/" else url
    ref = "https://www.yotrickslog.tech/"
    h = {"referer": ref}
    resp = client.get(url, headers=h)
    soup = BeautifulSoup(resp.content, "html.parser")
    inputs = soup.find_all("input")
    data = {input.get("name"): input.get("value") for input in inputs}
    h = {"x-requested-with": "XMLHttpRequest"}
    r = client.post(f"{DOMAIN}/links/go", data=data, headers=h)
    try:
        return r.json()["url"]
    except BaseException:
        return "Something went wrong :("


# mdiskshortner

def mdiskshortner(url):
    client = cloudscraper.create_scraper(allow_brotli=False)
    DOMAIN = "https://mdiskshortner.link"
    url = url[:-1] if url[-1] == "/" else url
    ref = "https://apps.proappapk.com/"
    h = {"referer": ref}
    resp = client.get(url, headers=h)
    soup = BeautifulSoup(resp.content, "html.parser")
    inputs = soup.find_all("input")
    data = {input.get("name"): input.get("value") for input in inputs}
    h = {"x-requested-with": "XMLHttpRequest"}
    r = client.post(f"{DOMAIN}/links/go", data=data, headers=h)
    try:
        return r.json()["url"]
    except BaseException:
        return "Something went wrong :("


# mdiskpro


def mdiskpro(url):
    client = cloudscraper.create_scraper(allow_brotli=False)
    DOMAIN = "https://mdisk.pro"
    url = url[:-1] if url[-1] == "/" else url
    ref = "https://www.meclipstudy.in/"
    h = {"referer": ref}
    resp = client.get(url, headers=h)
    soup = BeautifulSoup(resp.content, "html.parser")
    inputs = soup.find_all("input")
    data = {input.get("name"): input.get("value") for input in inputs}
    h = {"x-requested-with": "XMLHttpRequest"}
    r = client.post(f"{DOMAIN}/links/go", data=data, headers=h)
    try:
        return r.json()["url"]
    except BaseException:
        return "Something went wrong :("


# oggylink


def oggylink(url):
    client = cloudscraper.create_scraper(allow_brotli=False)
    DOMAIN = "https://oggylink.com"
    url = url[:-1] if url[-1] == "/" else url
    ref = "https://www.meclipstudy.in/"
    h = {"referer": ref}
    resp = client.get(url, headers=h)
    soup = BeautifulSoup(resp.content, "html.parser")
    inputs = soup.find_all("input")
    data = {input.get("name"): input.get("value") for input in inputs}
    h = {"x-requested-with": "XMLHttpRequest"}
    r = client.post(f"{DOMAIN}/links/go", data=data, headers=h)
    try:
        return r.json()["url"]
    except BaseException:
        return "Something went wrong :("


##########################################################################



##########################################################################
# adrinolink


def adrinolink(url):
    if "https://adrinolinks.in/" not in url:
        url = "https://adrinolinks.in/" + url.split("/")[-1]
    client = cloudscraper.create_scraper(allow_brotli=False)
    DOMAIN = "https://adrinolinks.in"
    ref = "https://myprivatejobs.com/"
    h = {"referer": ref}
    resp = client.get(url, headers=h)
    soup = BeautifulSoup(resp.content, "html.parser")
    inputs = soup.find_all("input")
    data = {input.get("name"): input.get("value") for input in inputs}
    h = {"x-requested-with": "XMLHttpRequest"}
    time.sleep(8)
    r = client.post(f"{DOMAIN}/links/go", data=data, headers=h)
    try:
        return r.json()["url"]
    except BaseException:
        return "Something went wrong :("


def cyberurl(url):
    client = cloudscraper.create_scraper(allow_brotli=False)
    DOMAIN = "https://cyberurl.me"
    url = url[:-1] if url[-1] == "/" else url
    code = url.split("/")[-1]
    final_url = f"{DOMAIN}/{code}"
    resp = client.get(final_url)
    soup = BeautifulSoup(resp.content, "html.parser")
    try:
        inputs = soup.find(id="go-link").find_all(name="input")
    except BaseException:
        return "Incorrect Link"
    data = {input.get("name"): input.get("value") for input in inputs}
    h = {"x-requested-with": "XMLHttpRequest"}
    time.sleep(5)
    r = client.post(f"{DOMAIN}/links/go", data=data, headers=h)
    try:
        return r.json()["url"]
    except BaseException:
        return "Something went wrong :("



# rslinks


def rslinks(url):
    download = requests.get(url, stream=True, allow_redirects=False)
    v = download.headers["location"]
    code = v.split("ms9")[-1]
    final = f"http://techyproio.blogspot.com/p/short.html?{code}=="
    try:
        return final
    except BaseException:
        return "Something went wrong :("


# tinyfy

def tinyfy(url):
    client = cloudscraper.create_scraper(allow_brotli=False)
    DOMAIN = "https://tinyfy.in/"
    url = url[:-1] if url[-1] == "/" else url
    code = url.split("/")[-1]
    final_url = f"{DOMAIN}/{code}"
    ref = "https://www.meclipstudy.in/"
    h = {"referer": ref}
    resp = client.get(final_url, headers=h)
    soup = BeautifulSoup(resp.content, "html.parser")
    inputs = soup.find_all("input")
    data = {input.get("name"): input.get("value") for input in inputs}
    h = {"x-requested-with": "XMLHttpRequest"}
    time.sleep(8)
    r = client.post(f"{DOMAIN}/links/go", data=data, headers=h)
    try:
        return r.json()["url"]
    except BaseException:
        return "Something went wrong :("

def tiny(url):
    client = requests.session()
    DOMAIN = "https://tinyfy.in"
    url = url[:-1] if url[-1] == "/" else url
    code = url.split("/")[-1]
    final_url = f"{DOMAIN}/{code}"
    ref = "https://www.meclipstudy.in/"
    h = {"referer": ref}
    resp = client.get(final_url, headers=h)
    soup = BeautifulSoup(resp.content, "html.parser")
    inputs = soup.find_all("input")
    data = {input.get("name"): input.get("value") for input in inputs}
    h = {"x-requested-with": "XMLHttpRequest"}
    r = client.post(f"{DOMAIN}/links/go", data=data, headers=h)
    try:
        return r.json()["url"]
    except BaseException:
        return "Something went wrong :("


# easysky


def easysky(url):
    client = cloudscraper.create_scraper(allow_brotli=False)
    DOMAIN = "https://techy.veganab.co/"
    url = url[:-1] if url[-1] == "/" else url
    code = url.split("/")[-1]
    final_url = f"{DOMAIN}/{code}"
    ref = "https://oceanofdiscount.com/"
    h = {"referer": ref}
    resp = client.get(final_url, headers=h)
    soup = BeautifulSoup(resp.content, "html.parser")
    inputs = soup.find_all("input")
    data = {input.get("name"): input.get("value") for input in inputs}
    h = {"x-requested-with": "XMLHttpRequest"}
    time.sleep(8)
    r = client.post(f"{DOMAIN}/links/go", data=data, headers=h)
    try:
        return r.json()["url"]
    except BaseException:
        return "Something went wrong :("


# indiurl


def indi(url):
    client = requests.session()
    DOMAIN = "https://file.earnash.com/"
    url = url[:-1] if url[-1] == "/" else url
    code = url.split("/")[-1]
    final_url = f"{DOMAIN}/{code}"
    ref = "https://indiurl.cordtpoint.co.in/"
    h = {"referer": ref}
    resp = client.get(final_url, headers=h)
    soup = BeautifulSoup(resp.content, "html.parser")
    inputs = soup.find_all("input")
    data = {input.get("name"): input.get("value") for input in inputs}
    h = {"x-requested-with": "XMLHttpRequest"}
    time.sleep(10)
    r = client.post(f"{DOMAIN}/links/go", data=data, headers=h)
    try:
        return r.json()["url"]
    except BaseException:
        return "Something went wrong :("


# linkbnao


def linkbnao(url):
    client = cloudscraper.create_scraper(allow_brotli=False)
    DOMAIN = "https://vip.linkbnao.com"
    url = url[:-1] if url[-1] == "/" else url
    code = url.split("/")[-1]
    final_url = f"{DOMAIN}/{code}"
    ref = "https://ffworld.xyz/"
    h = {"referer": ref}
    resp = client.get(final_url, headers=h)
    soup = BeautifulSoup(resp.content, "html.parser")
    inputs = soup.find_all("input")
    data = {input.get("name"): input.get("value") for input in inputs}
    h = {"x-requested-with": "XMLHttpRequest"}
    time.sleep(2)
    r = client.post(f"{DOMAIN}/links/go", data=data, headers=h)
    try:
        return r.json()["url"]
    except BaseException:
        return "Something went wrong :("


# indianshortner


def indshort(url):
    client = cloudscraper.create_scraper(allow_brotli=False)
    DOMAIN = "https://indianshortner.com/"
    url = url[:-1] if url[-1] == "/" else url
    code = url.split("/")[-1]
    final_url = f"{DOMAIN}/{code}"
    #ref = "https://moddingzone.in/"
    ref = "https://apkupload.in/"
    h = {"referer": ref}
    resp = client.get(final_url, headers=h)
    soup = BeautifulSoup(resp.content, "html.parser")
    inputs = soup.find_all("input")
    data = {input.get("name"): input.get("value") for input in inputs}
    h = {"x-requested-with": "XMLHttpRequest"}
    time.sleep(8)
    r = client.post(f"{DOMAIN}/links/go", data=data, headers=h)
    try:
        return r.json()["url"]
    except BaseException:
        return "Something went wrong :("


# indianshortner


def indshort(url):
    client = cloudscraper.create_scraper(allow_brotli=False)
    DOMAIN = "https://indianshortner.com/"
    url = url[:-1] if url[-1] == "/" else url
    code = url.split("/")[-1]
    final_url = f"{DOMAIN}/{code}"
    ref = "https://moddingzone.in/"
    h = {"referer": ref}
    resp = client.get(final_url, headers=h)
    soup = BeautifulSoup(resp.content, "html.parser")
    inputs = soup.find_all("input")
    data = {input.get("name"): input.get("value") for input in inputs}
    h = {"x-requested-with": "XMLHttpRequest"}
    time.sleep(5)
    r = client.post(f"{DOMAIN}/links/go", data=data, headers=h)
    try:
        return r.json()["url"]
    except BaseException:
        return "Something went wrong :("


# atglinks


def atglinks(url):
    DOMAIN = "https://atglinks.com"
    url = url[:-1] if url[-1] == "/" else url
    code = url.split("/")[-1]
    final_url = f"{DOMAIN}/{code}"
    return final_url


def atglinkss(url):
    atg = ""
    if "&url=" in url:
        atg = str(url).split("&url=")[+1]
        atg = base64.b64decode(str(atg).replace("&type=2","")).decode("utf-8")
    return str(atg)


#def greylink(url):
#    client = cloudscraper.create_scraper(allow_brotli=False)
#    DOMAIN = "https://go.greymatterslinks.in/"
#    url = url[:-1] if url[-1] == "/" else url
#    code = url.split("/")[-1]
#    final_url = f"{DOMAIN}/{code}"
#    ref = "https://djqunjab.in/"
#    h = {"referer": ref}
#    response = client.get(final_url, headers=h)
#    soup = BeautifulSoup(response.text, "html.parser")
#    inputs = soup.find_all("input")
#    data = {input.get("name"): input.get("value") for input in inputs}
#    h = {"x-requested-with": "XMLHttpRequest"}
#    time.sleep(13)
#    r = client.post(f"{DOMAIN}/links/go", data=data, headers=h)
#    try:
#        return r.json()["url"]
#    except BaseException:
#        return "Something went wrong :("


def greylink(url):
    DOMAIN = "https://go.greymatterslinks.in"
    url = url[:-1] if url[-1] == "/" else url
    code = url.split("/")[-1]
    final_url = f"{DOMAIN}/{code}"
    return final_url


def greylinks(url):
    grey = ""
    if "&url=" in url:
        grey = str(url).split("&url=")[+1]
        grey = base64.b64decode(str(grey).replace("&type=2","")).decode("utf-8")
    return str(grey)

def shrinke(url):
    client = cloudscraper.create_scraper(allow_brotli=False)
    DOMAIN = "https://en.shrinke.me/"
    url = url[:-1] if url[-1] == "/" else url
    code = url.split("/")[-1]
    final_url = f"{DOMAIN}/{code}"
    ref = "https://mrproblogger.com/"
    h = {"referer": ref}
    resp = client.get(final_url, headers=h)
    soup = BeautifulSoup(resp.content, "html.parser")
    inputs = soup.find_all("input")
    data = {input.get("name"): input.get("value") for input in inputs}
    h = {"x-requested-with": "XMLHttpRequest"}
    time.sleep(12)
    r = client.post(f"{DOMAIN}/links/go", data=data, headers=h)
    try:
        return r.json()["url"]
    except BaseException:
        return "Something went wrong :("


# kpslink
def earn2me(url):
    client = cloudscraper.create_scraper(allow_brotli=False)
    DOMAIN = "https://blog.filepresident.com/"
    url = url[:-1] if url[-1] == "/" else url
    code = url.split("/")[-1]
    final_url = f"{DOMAIN}/{code}"
    ref = "https://nichapk.com/"
    h = {"referer": ref}
    resp = client.get(final_url, headers=h)
    soup = BeautifulSoup(resp.content, "html.parser")
    inputs = soup.find_all("input")
    data = {input.get("name"): input.get("value") for input in inputs}
    h = {"x-requested-with": "XMLHttpRequest"}
    time.sleep(8)
    r = client.post(f"{DOMAIN}/links/go", data=data, headers=h)
    try:
        return r.json()["url"]
    except BaseException:
        return "Something went wrong :("

def streemin(url):
    client = cloudscraper.create_scraper(allow_brotli=False)
    DOMAIN = "https://last.moneycase.link/"
    url = url[:-1] if url[-1] == "/" else url
    code = url.split("/")[-1]
    final_url = f"{DOMAIN}/{code}"
    ref = "https://www.infokeeda.xyz/"
    h = {"referer": ref}
    resp = client.get(final_url, headers=h)
    soup = BeautifulSoup(resp.content, "html.parser")
    inputs = soup.find_all("input")
    data = {input.get("name"): input.get("value") for input in inputs}
    h = {"x-requested-with": "XMLHttpRequest"}
    time.sleep(8)
    r = client.post(f"{DOMAIN}/links/go", data=data, headers=h)
    try:
        return r.json()["url"]
    except BaseException:
        return "Something went wrong :("


# earnlink

def earnlink(url):
    client = cloudscraper.create_scraper(allow_brotli=False)
    response = client.get(url)
    soup = BeautifulSoup(response.content, "html.parser")
    script_tag = str(soup.find("script"))
    url_regex = r"""(?i)\b((?:https?://|www\d{0,3}[.]|[a-z0-9.\-]+[.][a-z]{2,4}/)(?:[^\s()<>]+|\(([^\s()<>]+|(\([^\s()<>]+\)))*\))+(?:\(([^\s()<>]+|(\([^\s()<>]+\)))*\)|[^\s`!()\[\]{};:'\".,<>?«»“”‘’]))"""
    a_href_tag = re.findall(url_regex, script_tag)
    return str(a_href_tag[0][0])


# greylink


    
# link1s

def link1s(url):
    client = cloudscraper.create_scraper(allow_brotli=False)
    DOMAIN = "https://link1s.com"
    url = url[:-1] if url[-1] == "/" else url
    code = url.split("/")[-1]
    final_url = f"{DOMAIN}/{code}"
    ref = "https://anhdep24.com/"
    h = {"referer": ref}
    response = client.get(final_url, headers=h)
    soup = BeautifulSoup(response.text, "html.parser")
    inputs = soup.find_all("input")
    data = {input.get("name"): input.get("value") for input in inputs}
    h = {"x-requested-with": "XMLHttpRequest"}
    time.sleep(9)
    r = client.post(f"{DOMAIN}/links/go", data=data, headers=h)
    try:
        return str(r.json()["url"])
    except BaseException:
        return "Something went wrong :("

# pdisks

def pdisks(url):
    r = rget(url).text
    try: return r.split("<!-- ")[-1].split(" -->")[0]
    except:
        try:return BeautifulSoup(r,"html.parser").find('video').find("source").get("src")
        except: return None

#mdiskpro.in

def mdiskproin(url):
    client = requests.session()
    DOMAIN = "https://main.mdiskpro.xyz/"
    url = url[:-1] if url[-1] == '/' else url
    code = url.split("/")[-1]
    final_url = f"{DOMAIN}/{code}"
    ref = "https://babynamesmeanings.net/"
    h = {"referer": ref}
    while len(client.cookies) == 0:
        resp = client.get(final_url,headers=h)
        time.sleep(10)
    soup = BeautifulSoup(resp.content, "html.parser")
    inputs = soup.find_all("input")
    data = { input.get('name'): input.get('value') for input in inputs }
    h = { "x-requested-with": "XMLHttpRequest" }
    time.sleep(8)
    r = client.post(f"{DOMAIN}/links/go", data=data, headers=h)
    try: return str(r.json()["url"])
    except BaseException:
        return "Something went wrong :("

#mplaylink
def mplaylink(url):
    client = cloudscraper.create_scraper(allow_brotli=False)
    DOMAIN = "https://xtreamdisk.com/test/"
    url = url[:-1] if url[-1] == "/" else url
    code = url.split("/")[-1]
    final_url = f"{DOMAIN}/{code}"
    ref = "https://zisnews.com/"
    h = {"referer": ref}
    resp = client.get(final_url, headers=h)
    soup = BeautifulSoup(resp.content, "html.parser")
    inputs = soup.find_all("input")
    data = {input.get("name"): input.get("value") for input in inputs}
    h = {"x-requested-with": "XMLHttpRequest"}
    time.sleep(5)
    r = client.post(f"{DOMAIN}/links/go", data=data, headers=h)
    try:
        return str(r.json()["url"])
    except BaseException:
        return "Something went wrong :("

def tnvalue(url):
    client = cloudscraper.create_scraper(allow_brotli=False)
    DOMAIN = "https://gadgets.webhostingtips.club/"
    url = url[:-1] if url[-1] == "/" else url
    code = url.split("/")[-1]
    final_url = f"{DOMAIN}/{code}"
    ref = "https://ladkibahin.com/"
    h = {"referer": ref}
    resp = client.get(final_url, headers=h)
    soup = BeautifulSoup(resp.content, "html.parser")
    inputs = soup.find_all("input")
    data = {input.get("name"): input.get("value") for input in inputs}
    h = {"x-requested-with": "XMLHttpRequest"}
    time.sleep(12)
    r = client.post(f"{DOMAIN}/links/go", data=data, headers=h)
    try:
        return str(r.json()["url"])
    except BaseException:
        return "Something went wrong :("

def urlshorten(url):
    client = requests.session()
    DOMAIN = "https://dl.urlshorten.in/"
    url = url[:-1] if url[-1] == '/' else url
    code = url.split("/")[-1]
    final_url = f"{DOMAIN}/{code}"
    ref = "https://Islink.in/"
    h = {"referer": ref}
    while len(client.cookies) == 0:
        resp = client.get(final_url,headers=h)
        time.sleep(5)
    soup = BeautifulSoup(resp.content, "html.parser")
    inputs = soup.find_all("input")
    data = { input.get('name'): input.get('value') for input in inputs }
    h = { "x-requested-with": "XMLHttpRequest" }
    time.sleep(8)
    r = client.post(f"{DOMAIN}/links/go", data=data, headers=h)
    try: return str(r.json()["url"])
    except BaseException:
        return "Something went wrong :("

def urlshortens(url):
    client = requests.session()
    DOMAIN = "https://play.urlshorten.in/"
    url = url[:-1] if url[-1] == '/' else url
    code = url.split("/")[-1]
    final_url = f"{DOMAIN}/{code}"
    ref = "https://Islink.in/"
    h = {"referer": ref}
    while len(client.cookies) == 0:
        resp = client.get(final_url,headers=h)
        time.sleep(9)
    soup = BeautifulSoup(resp.content, "html.parser")
    inputs = soup.find_all("input")
    data = { input.get('name'): input.get('value') for input in inputs }
    h = { "x-requested-with": "XMLHttpRequest" }
    time.sleep(8)
    r = client.post(f"{DOMAIN}/links/go", data=data, headers=h)
    try: return str(r.json()["url"])
    except BaseException:
        return "Something went wrong :("


def tamizhmasters(url):
    client = requests.session()
    DOMAIN = "https://tamizhmasters.net/"
    url = url[:-1] if url[-1] == '/' else url
    code = url.split("/")[-1]
    final_url = f"{DOMAIN}/{code}"
    ref = "https://azhealthlife.com/"
    h = {"referer": ref}
    while len(client.cookies) == 0:
        resp = client.get(final_url,headers=h)
        time.sleep(5)
    soup = BeautifulSoup(resp.content, "html.parser")
    inputs = soup.find_all("input")
    data = { input.get('name'): input.get('value') for input in inputs }
    h = { "x-requested-with": "XMLHttpRequest" }
    time.sleep(8)
    r = client.post(f"{DOMAIN}/links/go", data=data, headers=h)
    try: return str(r.json()["url"])
    except BaseException:
        return "Something went wrong :("

def krownlinks(url):
    client = cloudscraper.create_scraper(allow_brotli=False)
    DOMAIN = "https://go.hostadviser.net/"
    url = url[:-1] if url[-1] == "/" else url
    code = url.split("/")[-1]
    final_url = f"{DOMAIN}/{code}"
    ref = "https://www.gyanitheme.com/"
    h = {"referer": ref}
    resp = client.get(final_url, headers=h)
    soup = BeautifulSoup(resp.content, "html.parser")
    inputs = soup.find_all("input")
    data = {input.get("name"): input.get("value") for input in inputs}
    h = {"x-requested-with": "XMLHttpRequest"}
    time.sleep(12)
    r = client.post(f"{DOMAIN}/links/go", data=data, headers=h)
    try:
        return str(r.json()["url"])
    except BaseException:
        return "Fixed Soon :("


def seturl(url):
    client = cloudscraper.create_scraper(allow_brotli=False)
    DOMAIN = "https://set.seturl.in"
    url = url[:-1] if url[-1] == "/" else url
    code = url.split("/")[-1]
    final_url = f"{DOMAIN}/{code}"
    #ref = "https://shortner.mphealth.online/"
    ref = "https://petrainer.in/"
    h = {"referer": ref}
    resp = client.get(final_url, headers=h)
    soup = BeautifulSoup(resp.content, "html.parser")
    inputs = soup.find_all("input")
    data = {input.get("name"): input.get("value") for input in inputs}
    h = {"x-requested-with": "XMLHttpRequest"}
    time.sleep(8)
    r = client.post(f"{DOMAIN}/links/go", data=data, headers=h)
    try:
        return str(r.json()["url"])
    except BaseException:
        return "Something went wrong :("


def pkinme(url):
    client = cloudscraper.create_scraper(allow_brotli=False)
    DOMAIN = "https://go.paisakamalo.in"
    url = url[:-1] if url[-1] == "/" else url
    code = url.split("/")[-1]
    final_url = f"{DOMAIN}/{code}"
    ref = "https://healthtips.techkeshri.com/"
    h = {"referer": ref}
    response = client.get(final_url, headers=h)
    soup = BeautifulSoup(response.text, "html.parser")
    inputs = soup.find_all("input")
    data = {input.get("name"): input.get("value") for input in inputs}
    h = {"x-requested-with": "XMLHttpRequest"}
    time.sleep(9)
    r = client.post(f"{DOMAIN}/links/go", data=data, headers=h)
    try:
        return r.json()["url"]
    except BaseException:
        return "Something went wrong :("


 #tnshort.net
def tnshort(url):
    client = cloudscraper.create_scraper(allow_brotli=False)
    #DOMAIN = "https://news.speedynews.xyz/"
    DOMAIN = "https://news.sagenews.in/"
    url = url[:-1] if url[-1] == "/" else url
    code = url.split("/")[-1]
    final_url = f"{DOMAIN}/{code}"
    ref = "https://movies.djnonstopmusic.in/"
    h = {"referer": ref}
    resp = client.get(final_url, headers=h)
    soup = BeautifulSoup(resp.content, "html.parser")
    inputs = soup.find_all("input")
    data = {input.get("name"): input.get("value") for input in inputs}
    h = {"x-requested-with": "XMLHttpRequest"}
    time.sleep(9)
    r = client.post(f"{DOMAIN}/links/go", data=data, headers=h)
    try:
        return str(r.json()["url"])
    except BaseException:
        return "Something went wrong :("

 #mdisky
def mdisky(url):
    client = cloudscraper.create_scraper(allow_brotli=False)
    DOMAIN = "https://go.bloggingaro.com/"
    url = url[:-1] if url[-1] == "/" else url
    code = url.split("/")[-1]
    final_url = f"{DOMAIN}/{code}"
    ref = "https://www.bloggingaro.com/"
    h = {"referer": ref}
    resp = client.get(final_url, headers=h)
    soup = BeautifulSoup(resp.content, "html.parser")
    inputs = soup.find_all("input")
    data = {input.get("name"): input.get("value") for input in inputs}
    h = {"x-requested-with": "XMLHttpRequest"}
    time.sleep(6)
    r = client.post(f"{DOMAIN}/links/go", data=data, headers=h)
    try:
        return str(r.json()["url"])
    except BaseException:
        return "Something went wrong :("

def link2paisa(url):
    client = cloudscraper.create_scraper(allow_brotli=False)
    DOMAIN = "https://link2paisa.com/"
    url = url[:-1] if url[-1] == "/" else url
    code = url.split("/")[-1]
    final_url = f"{DOMAIN}/{code}"
    ref = "https://infinityskull.com/"
    h = {"referer": ref}
    resp = client.get(final_url, headers=h)
    soup = BeautifulSoup(resp.content, "html.parser")
    inputs = soup.find_all("input")
    data = {input.get("name"): input.get("value") for input in inputs}
    h = {"x-requested-with": "XMLHttpRequest"}
    time.sleep(9)
    r = client.post(f"{DOMAIN}/links/go", data=data, headers=h)
    try:
        return str(r.json()["url"])
    except BaseException:
        return "Something went wrong :("

def lksfycom(url):
    client = cloudscraper.create_scraper(allow_brotli=False)
    DOMAIN = "https://lksfy.site/"
    url = url[:-1] if url[-1] == "/" else url
    code = url.split("/")[-1]
    final_url = f"{DOMAIN}/{code}"
    ref = "https://sportswordz.com"
    h = {"referer": ref}
    resp = client.get(final_url, headers=h)
    soup = BeautifulSoup(resp.content, "html.parser")
    inputs = soup.find_all("input")
    data = {input.get("name"): input.get("value") for input in inputs}
    h = {"x-requested-with": "XMLHttpRequest"}
    time.sleep(13)
    r = client.post(f"{DOMAIN}/links/go", data=data, headers=h)
    try:
        return str(r.json()["url"])
    except BaseException:
        return "Something went wrong :("


def dalink(url):
    client = cloudscraper.create_scraper(allow_brotli=False)
    DOMAIN = "https://www.tamilhit.tech/blog//"
    url = url[:-1] if url[-1] == "/" else url
    code = url.split("/")[-1]
    final_url = f"{DOMAIN}/{code}"
    ref = "https://www.tamilhit.tech/"
    h = {"referer": ref}
    response = client.get(final_url, headers=h)
    soup = BeautifulSoup(response.text, "html.parser")
    inputs = soup.find_all("input")
    data = {input.get("name"): input.get("value") for input in inputs}
    h = {"x-requested-with": "XMLHttpRequest"}
    time.sleep(9)
    r = client.post(f"{DOMAIN}/links/go", data=data, headers=h)
    try:
        return r.json()["url"]
    except BaseException:
        return "Something went wrong :("


def onepagelinkin(url):
    client = cloudscraper.create_scraper(allow_brotli=False)
    DOMAIN = "https://go.onepagelink.in/"
    url = url[:-1] if url[-1] == "/" else url
    code = url.split("/")[-1]
    final_url = f"{DOMAIN}/{code}"
    ref = "https://gorating.in/"
    h = {"referer": ref}
    response = client.get(final_url, headers=h)
    soup = BeautifulSoup(response.text, "html.parser")
    inputs = soup.find_all("input")
    data = {input.get("name"): input.get("value") for input in inputs}
    h = {"x-requested-with": "XMLHttpRequest"}
    time.sleep(5)
    r = client.post(f"{DOMAIN}/links/go", data=data, headers=h)
    try:
        return r.json()["url"]
    except BaseException:
        return "Something went wrong :("



def zxlink(url):
    client = cloudscraper.create_scraper(allow_brotli=False)
    DOMAIN = "https://zxlink.in"
    url = url[:-1] if url[-1] == "/" else url
    code = url.split("/")[-1]
    final_url = f"{DOMAIN}/{code}"
    ref = "https://info.gorating.in/"
    h = {"referer": ref}
    response = client.get(final_url, headers=h)
    soup = BeautifulSoup(response.text, "html.parser")
    inputs = soup.find_all("input")
    data = {input.get("name"): input.get("value") for input in inputs}
    h = {"x-requested-with": "XMLHttpRequest"}
    time.sleep(13)
    r = client.post(f"{DOMAIN}/links/go", data=data, headers=h)
    try:
        return r.json()["url"]
    except BaseException:
        return "Something went wrong :("


def vipurl(url):
    client = cloudscraper.create_scraper(allow_brotli=False)
    DOMAIN = "https://count.vipurl.in/"
    url = url[:-1] if url[-1] == "/" else url
    code = url.split("/")[-1]
    final_url = f"{DOMAIN}/{code}"
    ref = "https://ezeviral.com/"
    h = {"referer": ref}
    response = client.get(final_url, headers=h)
    soup = BeautifulSoup(response.text, "html.parser")
    inputs = soup.find_all("input")
    data = {input.get("name"): input.get("value") for input in inputs}
    h = {"x-requested-with": "XMLHttpRequest"}
    time.sleep(9)
    r = client.post(f"{DOMAIN}/links/go", data=data, headers=h)
    try:
        return r.json()["url"]
    except BaseException:
        return "Something went wrong :("

# owllinknet


def owllinknet(url):
    client = cloudscraper.create_scraper(allow_brotli=False)
    DOMAIN = "https://owllink.net"
    url = url[:-1] if url[-1] == "/" else url
    code = url.split("/")[-1]
    final_url = f"{DOMAIN}/{code}"
    ref = "https://uptechnologys.com/"
    h = {"referer": ref}
    response = client.get(final_url, headers=h)
    soup = BeautifulSoup(response.text, "html.parser")
    inputs = soup.find_all("input")
    data = {input.get("name"): input.get("value") for input in inputs}
    h = {"x-requested-with": "XMLHttpRequest"}
    time.sleep(10)
    r = client.post(f"{DOMAIN}/links/go", data=data, headers=h)
    try:
        return r.json()["url"]
    except BaseException:
        return "Something went wrong :("


# linksfireco


def linksfireco(url):
    client = cloudscraper.create_scraper(allow_brotli=False)
    DOMAIN = "https://blog.linksfire.co"
    url = url[:-1] if url[-1] == "/" else url
    code = url.split("/")[-1]
    final_url = f"{DOMAIN}/{code}"
    ref = "https://bartendingexpert.com/"
    h = {"referer": ref}
    response = client.get(final_url, headers=h)
    soup = BeautifulSoup(response.text, "html.parser")
    inputs = soup.find_all("input")
    data = {input.get("name"): input.get("value") for input in inputs}
    h = {"x-requested-with": "XMLHttpRequest"}
    time.sleep(10)
    r = client.post(f"{DOMAIN}/links/go", data=data, headers=h)
    try:
        return r.json()["url"]
    except BaseException:
        return "Something went wrong :("

# powerlinks

def powerlinks(url):
    client = cloudscraper.create_scraper(allow_brotli=False)
    DOMAIN = "http://powerlinks.site"
    url = url[:-1] if url[-1] == "/" else url
    code = url.split("/")[-1]
    final_url = f"{DOMAIN}/{code}"
    ref = "http://powerlinks.site/"
    h = {"referer": ref}
    resp = client.get(final_url, headers=h)
    soup = BeautifulSoup(resp.content, "html.parser")
    inputs = soup.find_all("input")
    data = {input.get("name"): input.get("value") for input in inputs}
    h = {"x-requested-with": "XMLHttpRequest"}
    time.sleep(5)
    r = client.post(f"{DOMAIN}/links/go", data=data, headers=h)
    try:
        return r.json()["url"]
    except BaseException:
        return "Something went wrong :("

# tulinks

def tulinks(url):
    client = cloudscraper.create_scraper(allow_brotli=False)
    DOMAIN = "https://tulinks.one"
    url = url[:-1] if url[-1] == "/" else url
    code = url.split("/")[-1]
    final_url = f"{DOMAIN}/{code}"
    ref = "https://www.blogger.com/"
    h = {"referer": ref}
    resp = client.get(final_url, headers=h)
    soup = BeautifulSoup(resp.content, "html.parser")
    inputs = soup.find_all("input")
    data = {input.get("name"): input.get("value") for input in inputs}
    h = {"x-requested-with": "XMLHttpRequest"}
    time.sleep(8)
    r = client.post(f"{DOMAIN}/links/go", data=data, headers=h)
    try:
        return r.json()["url"]
    except BaseException:
        return "Something went wrong :("

# go tulinks

def gotulinks(url):
    client = cloudscraper.create_scraper(allow_brotli=False)
    DOMAIN = "https://go.tulinks.online"
    url = url[:-1] if url[-1] == "/" else url
    code = url.split("/")[-1]
    final_url = f"{DOMAIN}/{code}"
    ref = "https://tutelugu.co/"
    h = {"referer": ref}
    resp = client.get(final_url, headers=h)
    soup = BeautifulSoup(resp.content, "html.parser")
    inputs = soup.find_all("input")
    data = {input.get("name"): input.get("value") for input in inputs}
    h = {"x-requested-with": "XMLHttpRequest"}
    time.sleep(8)
    r = client.post(f"{DOMAIN}/links/go", data=data, headers=h)
    try:
        return r.json()["url"]
    except BaseException:
        return "Something went wrong :("

# powerlinkz

def powerlinkz(url):
    client = cloudscraper.create_scraper(allow_brotli=False)
    DOMAIN = "https://powerlinkz.in"
    url = url[:-1] if url[-1] == "/" else url
    code = url.split("/")[-1]
    final_url = f"{DOMAIN}/{code}"
    ref = "https://powerlinkz.in/"
    h = {"referer": ref}
    resp = client.get(final_url, headers=h)
    soup = BeautifulSoup(resp.content, "html.parser")
    inputs = soup.find_all("input")
    data = {input.get("name"): input.get("value") for input in inputs}
    h = {"x-requested-with": "XMLHttpRequest"}
    time.sleep(8)
    r = client.post(f"{DOMAIN}/links/go", data=data, headers=h)
    try:
        return r.json()["url"]
    except BaseException:
        return "Something went wrong :("

# powerdisk

def powerdisk(url):
    client = cloudscraper.create_scraper(allow_brotli=False)
    DOMAIN = "https://powerdisk.pro"
    url = url[:-1] if url[-1] == "/" else url
    code = url.split("/")[-1]
    final_url = f"{DOMAIN}/{code}"
    ref = "https://powerdisk.pro/"
    h = {"referer": ref}
    resp = client.get(final_url, headers=h)
    soup = BeautifulSoup(resp.content, "html.parser")
    inputs = soup.find_all("input")
    data = {input.get("name"): input.get("value") for input in inputs}
    h = {"x-requested-with": "XMLHttpRequest"}
    time.sleep(5)
    r = client.post(f"{DOMAIN}/links/go", data=data, headers=h)
    try:
        return r.json()["url"]
    except BaseException:
        return "Something went wrong :("

# kwik
    
def kwik(link):
    def get_string(content: str, s1: int, s2: int) -> str:
        CHARACTER_MAP = "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ+/"
        slice_2 = CHARACTER_MAP[0:s2]
        acc = 0
        for n, i in enumerate(content[::-1]):
            acc += int(i if i.isdigit() else 0) * s1**n
        k = ''
        while acc > 0:
            k = slice_2[int(acc % s2)] + k
            acc = (acc - (acc % s2)) / s2
        return k or '0'
    def decrypt(full_string: str, key: str, v1: int, v2: int) -> str:
        v1, v2 = int(v1), int(v2)
        r, i = "", 0
        while i < len(full_string):
            s = ""
            while (full_string[i] != key[v2]):
                s += full_string[i]
                i += 1
            j = 0
            while j < len(key):
                s = s.replace(key[j], str(j))
                j += 1
            r += chr(int(get_string(s, v2, 10)) - v1)
            i += 1
        return r
    def get_stream_url_from_kwik(url):
        session = requests.session()
        f_content = requests.get(
            url,
            headers={
                'referer': 'https://kwik.cx/'
            }
        )
        KWIK_PARAMS_RE =re.compile(r'\("(\w+)",\d+,"(\w+)",(\d+),(\d+),\d+\)')
        decrypted = decrypt(
            *
            KWIK_PARAMS_RE.search(
                f_content.text
            ).group(
                1, 2,
                3, 4
            )
        )
        code = 419
        KWIK_D_URL = re.compile(r'action="([^"]+)"')
        KWIK_D_TOKEN = re.compile(r'value="([^"]+)"')
        while code != 302:
            content = session.post(
                KWIK_D_URL.search(decrypted).group(1),
                allow_redirects=False,
                data={'_token': KWIK_D_TOKEN.search(decrypted).group(1)},
                headers={'referer': str(f_content.url),'cookie': f_content.headers.get('set-cookie')})
            code = content.status_code
        return content.headers.get('location')
    return get_stream_url_from_kwik(link)

# viplinks.io
def viplinks(url):
    client = cloudscraper.create_scraper(allow_brotli=False)
    DOMAIN = "https://m.vip-link.net/"
    url = url[:-1] if url[-1] == "/" else url
    code = url.split("/")[-1]
    final_url = f"{DOMAIN}/{code}"
    #ref = "https://tracktotech.in/"
    ref = "https://lyricsbaazaar.com/"
    #ref = "https://thebloggerspoint.in/"
    h = {"referer": ref}
    resp = client.get(final_url, headers=h)
    soup = BeautifulSoup(resp.content, "html.parser")
    inputs = soup.find_all("input")
    data = {input.get("name"): input.get("value") for input in inputs}
    h = {"x-requested-with": "XMLHttpRequest"}
    time.sleep(3)
    r = client.post(f"{DOMAIN}/links/go", data=data, headers=h)
    try:
        return str(r.json()["url"])
    except BaseException:
        return "Something went wrong :("


def mdisklink(url):
    client = requests.session()
    DOMAIN = "https://gas.yosite.net/"
    url = url[:-1] if url[-1] == '/' else url
    code = url.split("/")[-1]
    final_url = f"{DOMAIN}/{code}"
    ref = "https://yosite.net/"
    h = {"referer": ref}
    while len(client.cookies) == 0:
        resp = client.get(final_url,headers=h)
        time.sleep(7)
    soup = BeautifulSoup(resp.content, "html.parser")
    inputs = soup.find_all("input")
    data = { input.get('name'): input.get('value') for input in inputs }
    h = { "x-requested-with": "XMLHttpRequest" }
    time.sleep(10)
    r = client.post(f"{DOMAIN}/links/go", data=data, headers=h)
    try: return str(r.json()["url"])
    except BaseException:
        return "Something went wrong :("

def happyfile(url):
    client = requests.session()
    DOMAIN = "https://happyfiles.dtglinks.in/"
    url = url[:-1] if url[-1] == '/' else url
    code = url.split("/")[-1]
    final_url = f"{DOMAIN}/{code}"
    ref = "https://tech.filohappy.in/"
    h = {"referer": ref}
    while len(client.cookies) == 0:
        resp = client.get(final_url,headers=h)
        time.sleep(7)
    soup = BeautifulSoup(resp.content, "html.parser")
    inputs = soup.find_all("input")
    data = { input.get('name'): input.get('value') for input in inputs }
    h = { "x-requested-with": "XMLHttpRequest" }
    time.sleep(8)
    r = client.post(f"{DOMAIN}/links/go", data=data, headers=h)
    try: return str(r.json()["url"])
    except BaseException:
        return "Something went wrong :("


def omnifly(url):
    client = requests.session()
    DOMAIN = "https://f.omnifly.in.net/"
    url = url[:-1] if url[-1] == '/' else url
    code = url.split("/")[-1]
    final_url = f"{DOMAIN}/{code}"
    ref = "https://allserviceindia.in/archives/"
    h = {"referer": ref}
    while len(client.cookies) == 0:
        resp = client.get(final_url,headers=h)
        time.sleep(7)
    soup = BeautifulSoup(resp.content, "html.parser")
    inputs = soup.find_all("input")
    data = { input.get('name'): input.get('value') for input in inputs }
    h = { "x-requested-with": "XMLHttpRequest" }
    time.sleep(8)
    r = client.post(f"{DOMAIN}/links/go", data=data, headers=h)
    try: return str(r.json()["url"])
    except BaseException:
        return "Something went wrong :("


def bindaas(url):
    client = requests.session()
    DOMAIN = "https://thebindaas.com/blog/"
    url = url[:-1] if url[-1] == '/' else url
    code = url.split("/")[-1]
    final_url = f"{DOMAIN}/{code}"
    ref = "https://blog.appsinsta.com/"
    h = {"referer": ref}
    while len(client.cookies) == 0:
        resp = client.get(final_url,headers=h)
        time.sleep(7)
    soup = BeautifulSoup(resp.content, "html.parser")
    inputs = soup.find_all("input")
    data = { input.get('name'): input.get('value') for input in inputs }
    h = { "x-requested-with": "XMLHttpRequest" }
    time.sleep(8)
    r = client.post(f"{DOMAIN}/links/go", data=data, headers=h)
    try: return str(r.json()["url"])
    except BaseException:
        return "Something went wrong :("


# Vnshortner- 

def vnshortener(url):
    sess = requests.session()
    DOMAIN = "https://vnshortener.com/"
    org = "https://nishankhatri.xyz"
    PhpAcc = DOMAIN + "link/new.php"
    ref = "https://sugarona.com/"
    go = DOMAIN + "links/go"

    code = url.split("/")[3]
    final_url = f"{DOMAIN}/{code}/"
    headers = {'authority': DOMAIN, 'origin': org}

    data = {'step_1': code,}
    response = sess.post(PhpAcc, headers=headers, data=data).json()
    id = response["inserted_data"]["id"]
    data = {'step_2': code, 'id': id,}
    response = sess.post(PhpAcc, headers=headers, data=data).json()
    
    headers['referer'] = ref
    params = {'sid': str(id)}
    resp = sess.get(final_url, params=params, headers=headers)
    soup = BeautifulSoup(resp.content, "html.parser")
    inputs = soup.find_all("input")
    data = { input.get('name'): input.get('value') for input in inputs }

    time.sleep(1)
    headers['x-requested-with'] = 'XMLHttpRequest'
    try:
        r = sess.post(go, data=data, headers=headers).json()
        if r["status"] == "success": return r["url"]
        else: raise
    except: return "Something went wrong :("

# moneykamalo

def moneykamalo(url):
    client = requests.session()
    DOMAIN = "https://go.moneykamalo.com"
    url = url[:-1] if url[-1] == '/' else url
    code = url.split("/")[-1]
    final_url = f"{DOMAIN}/{code}"
    ref = "https://bloging.techkeshri.com/"
    h = {"referer": ref}
    resp = client.get(final_url,headers=h)
    soup = BeautifulSoup(resp.content, "html.parser")
    inputs = soup.find_all("input")
    data = { input.get('name'): input.get('value') for input in inputs }
    h = { "x-requested-with": "XMLHttpRequest" }
    time.sleep(5)
    r = client.post(f"{DOMAIN}/links/go", data=data, headers=h)
    try:
        return r.json()['url']
    except: return "Something went wrong :("
	    

##################################################################################################### 
# lolshort

def lolshort(url):
    client = requests.session()
    DOMAIN = "https://get.lolshort.tech/"
    url = url[:-1] if url[-1] == '/' else url
    code = url.split("/")[-1]
    final_url = f"{DOMAIN}/{code}"
    ref = "https://tech.animezia.com/"
    h = {"referer": ref}
    resp = client.get(final_url,headers=h)
    soup = BeautifulSoup(resp.content, "html.parser")
    inputs = soup.find_all("input")
    data = { input.get('name'): input.get('value') for input in inputs }
    h = { "x-requested-with": "XMLHttpRequest" }
    time.sleep(5)
    r = client.post(f"{DOMAIN}/links/go", data=data, headers=h)
    try:
        return r.json()['url']
    except: return "Something went wrong :("

def indy(url):
    client = requests.session()
    DOMAIN = "https://download.indyshare.net/"
    url = url[:-1] if url[-1] == '/' else url
    code = url.split("/")[-1]
    final_url = f"{DOMAIN}/{code}"
    ref = "https://bestdjsong.com/"
    h = {"referer": ref}
    resp = client.get(final_url,headers=h)
    soup = BeautifulSoup(resp.content, "html.parser")
    inputs = soup.find_all("input")
    data = { input.get('name'): input.get('value') for input in inputs }
    h = { "x-requested-with": "XMLHttpRequest" }
    time.sleep(5)
    r = client.post(f"{DOMAIN}/links/go", data=data, headers=h)
    try:
        return r.json()['url']
    except: return "Something went wrong :("

def urlspay(url):
    client = cloudscraper.create_scraper(allow_brotli=False)
    DOMAIN = "https://finance.smallinfo.in/"
    url = url[:-1] if url[-1] == "/" else url
    code = url.split("/")[-1]
    final_url = f"{DOMAIN}/{code}"
    ref = "https://loans.techyinfo.in/"
    h = {"referer": ref}
    resp = client.get(final_url, headers=h)
    soup = BeautifulSoup(resp.content, "html.parser")
    inputs = soup.find_all("input")
    data = {input.get("name"): input.get("value") for input in inputs}
    h = {"x-requested-with": "XMLHttpRequest"}
    time.sleep(7)
    r = client.post(f"{DOMAIN}/links/go", data=data, headers=h)
    try:
        return str(r.json()["url"])
    except BaseException:
        return "Something went wrong :("

def modijiurl(url):
    client = cloudscraper.create_scraper(allow_brotli=False)
    DOMAIN = "https://modijiurl.com/"
    url = url[:-1] if url[-1] == "/" else url
    code = url.split("/")[-1]
    final_url = f"{DOMAIN}/{code}"
    ref = "https://djmp3world.in/"
    h = {"referer": ref}
    resp = client.get(final_url, headers=h)
    soup = BeautifulSoup(resp.content, "html.parser")
    inputs = soup.find_all("input")
    data = {input.get("name"): input.get("value") for input in inputs}
    h = {"x-requested-with": "XMLHttpRequest"}
    time.sleep(7)
    r = client.post(f"{DOMAIN}/links/go", data=data, headers=h)
    try:
        return str(r.json()["url"])
    except BaseException:
        return "Something went wrong :("

def kingurl1(url):
    client = cloudscraper.create_scraper(allow_brotli=False)
    DOMAIN = "https://go.kingurl.in/"
    url = url[:-1] if url[-1] == "/" else url
    code = url.split("/")[-1]
    final_url = f"{DOMAIN}/{code}"
    ref = "https://earnbox.bankshiksha.in/"
    h = {"referer": ref}
    resp = client.get(final_url, headers=h)
    soup = BeautifulSoup(resp.content, "html.parser")
    inputs = soup.find_all("input")
    data = {input.get("name"): input.get("value") for input in inputs}
    h = {"x-requested-with": "XMLHttpRequest"}
    time.sleep(7)
    r = client.post(f"{DOMAIN}/links/go", data=data, headers=h)
    try:
        return str(r.json()["url"])
    except BaseException:
        return "Something went wrong :("

#Jai Add Later


def kingurl(url):
    DOMAIN = "https://earn.bankshiksha.in/click.php?LinkShortUrlID="
    url = url[:-1] if url[-1] == "/" else url
    code = url.split("/")[-1]
    final_url = f"{DOMAIN}{code}"
    return final_url




##########################################################################
# helpers


# check if present in list
def ispresent(inlist, url):
    for ele in inlist:
        if ele in url:
            return True
    return False


# shortners
#def shortners(url):
    # igg games
    #if "https://igg-games.com/" in url:
        #print("entered igg:", url)
        #return igggames(url)
def shortners(url):
    # Shortner Full Page API
    if val := shortner_fpage_api(url):
        return val

    # Shortner Quick Link API
    elif val := shortner_quick_api(url):
        return val

    # filecrypt
    elif ("https://filecrypt.co/") in url or ("https://filecrypt.cc/" in url):
        print("entered filecrypt:", url)
        return filecrypt(url)

    # shareus
    elif "https://shareus." in url or "https://shrs.link/" in url:
        print("entered shareus: ",url)
        return shareus(url)
    
    # shortingly
    elif "https://shortingly.in/" in url:
        print("entered shortingly:", url)
        return shortingly(url)

    elif "https://shortingly.click/" in url or "https://pass.gyanitheme.com/" in url:
        print("entered shortinglyclick:", url)
        return shortinglyclick(url)

    # moneykamalo
    elif "earn.moneykamalo.com" in url:
        print("entered moneykamalo: ",url)
        return moneykamalo(url)
	    
    # lolshort
    elif "http://go.lolshort.tech/" in url or "https://go.lolshort.tech/" in url:
        print("entered lolshort: ",url)
        return lolshort(url)


    # gyanilinks
    elif "https://gtlinks.me/" in url:
        print("entered gyanilinks:", url)
        return gyanilinks(url)

    # flasklink
    elif "https://go.flashlink.in/" in url:
        print("entered flashlink:", url)
        return flashlink(url)

    # short2url
    elif "https://link.short2url.in/" in url or "https://techyuth.xyz/blog/" in url:
        print("entered short2url:", url)
        return short2url(url)

    # pkinme
    elif "https://pkin.me/" in url or "https://go.paisakamalo.in/" in url:
        print("entered pkinme:", url)
        return pkinme(url)

    # shorte
    elif "https://shorte.st/" in url:
        print("entered shorte:", url)
        return sh_st_bypass(url)

    # psa
    elif "https://psa.pm/" in url:
        print("entered psa:", url)
        return psa_bypasser(url)

    # adfly
    elif "https://adf.ly/" in url:
        print("entered adfly:", url)
        out = adfly(url)
        return out["bypassed_url"]

    # gplinks
    elif "https://gplinks.co/" in url:
        print("entered gplink:", url)
        return gplinks(url)

    # droplink
    elif "https://droplink.co/" in url:
        print("entered droplink:", url)
        return droplink(url)

    # rocklinks
    elif "https://go.rocklinks.net/" in url or "https://rocklinks.net/" in url:
        print("entered rocklinks:", url)
        return rocklinks(url)

    # ouo
    elif "https://ouo.press/" in url:
        print("entered ouo:", url)
        return ouo(url)

    # try2link
    elif "https://try2link.com/" in url:
        print("entered try2links:", url)
        return try2link_bypass(url)

    # urlsopen
    elif "https://urlsopen.net/" in url:
        print("entered urlsopen:", url)
        return urlsopen(url)

    # xpshort
    elif (
        "https://xpshort.com/" in url
        or "https://push.bdnewsx.com/" in url
        or "https://techymozo.com/" in url
    ):
        print("entered xpshort:", url)
        return xpshort(url)

    # dulink
    elif "https://du-link.in/" in url:
        print("entered dulink:", url)
        return dulink(url)

    # nanolinks
    elif "https://nanolinks.in/" in url:
        print("entered nanolinks:", url)
        return nanolinks(url)

    # mdiskinnet
    elif "https://mdisk.in.net/" in url:
        print("entered mdiskinnet:", url)
        return mdiskinnet(url)

    # mdiskshortner
    elif "https://mdiskshortner.link/" in url:
        print("entered mdiskshortner:", url)
        return mdiskshortner(url)

    # mdiskpro
    elif "https://mdisk.pro/" in url or "https://omegalinks.in" in url:
        print("entered mdiskpro:", url)
        return mdiskpro(url)

    # oggylink
    elif "https://oggylink.com/" in url:
        print("entered oggylink:", url)
        return oggylink(url)

    # ez4short
    elif "https://ez4short.com/" in url:
        print("entered ez4short:", url)
        return ez4(url)

    # adrinolink
    elif "https://adrinolinks." in url:
        print("entered adrinolink:", url)
        return adrinolink(url)

    # cyberurl
    elif "https://url.cyberurl.me/" in url:
        print("entered cyberurl:", url)
        return cyberurl(url)

    # rslinks
    elif "rslinks.net" in url:
        print("entered rslinks:", url)
        return rslinks(url)

    # tinyfy
    elif "tinyfy.in" in url:
        print("entered tinyfy:", url)
        return tiny(url)

    elif "https://tinyfy.in/" in url or "https://TinyFy.in/" in url:
        print("entered tinyfy:", url)
        return tinyfy(url)

    # easysky
    elif "m.easysky.in" in url:
        print("entered easysky:", url)
        return easysky(url)

    # indiurl
    elif "go.indiurl.in.net" in url:
        print("entered indiurl:", url)
        return indi(url)

    # linkbnao
    elif "linkbnao.com" in url:
        print("entered linkbnao:", url)
        return linkbnao(url)

    # tnshort
    elif "https://link.tnshort.net/" in url or "https://tnseries.com/" in url or "https://link.tnseries.com/" in url:
        print("entered tnshort:", url)
        return tnshort(url)

    # modijiurl
    elif "https://modijiurl.com/" in url:
        print("entered modijiurl:", url)
        return modijiurl(url)

    # kingurl
    elif "https://kingurl.in/" in url:
        print("entered kingurl:", url)
        return kingurl(url)

    elif "mdisky.link" in url:
        print("entered mdisky:", url)
        return mdisky(url)

    elif "https://link2paisa.com/" in url:
        print("entered link2paisa:", url)
        return link2paisa(url)

    elif "https://lksfy.com/" in url or "https://lksfy.site/" in url:
        print("entered lksfy:", url)
        return lksfycom(url)

    # ole
    elif "https://onepagelink.in" in url or "https://go.onepagelink.in" in url:
        print("entered onepagelinkin:", url)
        return onepagelinkin(url)

    # indianshortner
    elif "indianshortner.in" in url:
        print("entered indianshortner:", url)
        return indshort(url)

        # atglinks
    elif "https://files.technicalatg.com/" in url or "https://f.technicalatg.in/" in url:
        print("entered atglinks:", url)
        return atglinks(url)

    # atglinks
    elif "https://atglinks.com/" in url:
        print("entered atglinks:", url)
        return atglinkss(url)
        
    # tnshort.net
    elif "https://link.tnshort.net/" in url or "https://tnseries.com/" in url or "https://link.tnseries.com/" in url:
        print("entered tnshortnet:", url)
        return tnshortnet(url)

    # kpslink
    elif "https://streaam.in/" in url:
        print("entered streemin:", url)
        return streemin(url)

    elif "https://link.earn2me.com/" in url or "https://earn2me.com/" in url:
        print("entered earn2me:", url)
        return earn2me(url)


    # earnlink
    elif "https://earnlink.io/" in url:
        print("entered earnlink:", url)
        return earnlink(url)

#    # greylink
#    elif "https://greylinks.in/" in url or "https://go.greymatterslinks.in/" in url:
#        print("entered greylink:", url)
#        return greylink(url)

        # greylink
    elif "https://greylinks.in/" in url:
        print("entered greylink:", url)
        return greylink(url)

    # greylinks
    elif "https://go.greymatterslinks.in/" in url:
        print("entered greylinks:", url)
        return greylinks(url)


        
    elif "https://gas.yosite.net/" in url or "https://mdisklink.link/" in url or "https://download.mdisklink.link/" in url:
        print("entered mdisklink:", url)
        return mdisklink(url)

    elif "https://dalink.in/" in url or "https://www.tamilhit.tech/" in url:
        print("entered dalink:", url)
        return dalink(url)
    
    elif "https://link1s.com/" in url:
        print("entered link1s:", url)
        return link1s(url)

    # linkvertise
    elif ispresent(linkvertise_list, url):
        print("entered linkvertise:", url)
        return linkvertise(url)

    elif "https://appdrive.me/pack" in url:
        print("entered appdrive pack:", url)
        return appdrivepack(url)

    # gdrive look alike
    elif ispresent(gdlist, url):
        print("entered gdrive look alike:", url)
        return unified(url)

    elif "mdiskpro.in/" in url or "main.mdiskpro.xyz/" in url:
        print("entered mdiskproin:",url)
        return mdiskproin(url)

    elif "mplaylink.com" in url or "https://xtreamdisk.com/test/" in url:
        print("entered mplaylink:",url)
        return mplaylink(url)

# tnvalue
    elif "https://link.tnvalue.in/" in url or "https://short.tnvalue.in/" in url or "https://tnvalue.in/" in url:
        print("entered tnvalue:", url)
        return tnvalue(url)

#pdisks
    elif "pdisk.pro" in url:
        print("entered PDisk:",url)
        return pdisks(url)

#urlshorten
    elif "urlshorten.in" in url or "link.urlshorten.in" in url:
        print("entered urlshorten:",url)
        return urlshorten(url)
    elif "link.urlshorten.in" in url or "play.urlshorten.in" in url or "us.urlshorten.in" in url:
        print("entered urlshortens:",url)
        return urlshortens(url)

    # tamizhmasters
    elif "tamizhmasters.net/" in url:
        print("entered tamizhmasters:",url)
        return tamizhmasters(url)

    # shrinkme
    elif "shrinke.me/" in url:
        print("entered shrinke:",url)
        return shrinke(url)

#krownlinks
    elif "krownlinks.me" in url or "link.gyanitheme.com" in url:
        print("entered krownlinks:",url)
        return krownlinks(url)

#seturl
    elif "seturl.in" in url or "link.seturl.in" in url or "set.seturl.in" in url:
        print("entered krownlinks:",url)
        return krownlinks(url)

    elif "link.vipurl.in" in url or "count.vipurl.in" in url or "vipurl.in" in url:
        print("entered vipurl:",url)
        return vipurl(url)

    # owllink.net
    elif "https://go.owllink.net/" in url:
        print("entered owllinknet:", url)
        return owllinknet(url)

    # linksfire.co
    elif "https://link.linksfire.co/" in url:
        print("entered linksfireco:", url)
        return linksfireco(url)
    
    elif "https://kwik.cx/" in url:
        print("entered kwik:", url)
        return kwik(url)

    elif "http://powerlinks.site" in url:
        print("entered powerlinks:",url)
        return powerlinks(url)

    elif "https://tulinks.one" in url:
        print("entered tulinks:",url)
        return tulinks(url)

    elif "https://go.tulinks.online" in url or "https://tulinks.online" in url:
        print("entered go tulinks:",url)
        return gotulinks(url)

    elif "https://powerlinkz.in" in url:
        print("entered powerlinkz:",url)
        return powerlinkz(url)

    elif "https://powerdisk.pro" in url:
        print("entered powerlinkz:",url)
        return powerdisk(url)

    elif "https://vnshortener.com/" in url:
        print("entered vnshortener:",url)
        return vnshortener(url)

    elif "https://indyshare.net/" in url:
        print("entered IndyShare:",url)
        return indy(url)

    elif "https://urlspay.in/" in url:
        print("entered Urlspay:",url)
        return urlspay(url)
	    
    elif "https://destined.editionx.online/" in url:
        print("entered Destined:",url)
        return destined(url)
	    
    elif "https://zxlink.in/" in url:
        print("entered Zxlink:",url)
        return zxlink(url)
	
    elif "https://l.omnifly.in.net/" in url or "https://f.omnifly.in.net/" in url:
        print("entered Omnifly:",url)
        return omnifly(url)

    elif "https://happyfiles.dtglinks.in/" in url or "https://happyfile.dtglinks.in/" in url:
        print("entered happyfile:",url)
        return happyfile(url)

    elif "https://thebindaas.com/" in url or "https://bindaaslinks.com/" in url:
        print("entered bindaas:",url)
        return bindaas(url)

    elif "https://viplinks.io" in url or "https://m.vip-link.net" in url:
        print("entered viplinks:",url)
        return viplinks(url)

    # else
    else:
        temp = PyBypass.bypass(url)
        if temp is not None:
            return temp
        else:
            return "Not in Supported Links"


##########################################################################


