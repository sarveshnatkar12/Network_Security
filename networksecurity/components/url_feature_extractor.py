import re
import socket
from urllib.parse import urlparse
from datetime import datetime
import whois
import requests

class URLFeatureExtractor:
    def __init__(self, url: str, timeout: float = 1.5):
        self.url = url
        self.parsed = urlparse(url)
        self.timeout = timeout
        self._html = None  # Will be populated on first request
        self._get_html()

    def _get_html(self):
        try:
            resp = requests.get(self.url, timeout=self.timeout)
            self._html = resp.text
        except:
            self._html = ""

    # WHOIS lookups reused
    def _whois_data(self):
        try:
            return whois.whois(self.parsed.netloc)
        except:
            return None

    def Domain_registeration_length(self):
        try:
            w = self._whois_data()
            expiry = w.expiration_date
            if isinstance(expiry, list):
                expiry = expiry[0]
            days = (expiry - datetime.now()).days
            return int(days >= 365)
        except:
            return 0

    def age_of_domain(self):
        try:
            w = self._whois_data()
            created = w.creation_date
            if isinstance(created, list):
                created = created[0]
            age_days = (datetime.now() - created).days
            return int(age_days >= 180)
        except:
            return 0

    def web_traffic(self):
        # TODO: Replace with real Alexa/SimilarWeb logic
        return 0

    def Page_Rank(self):
        # TODO: Replace with real Google PR or Moz API
        return 0

    def Links_pointing_to_page(self):
        # TODO: Replace with backlink checker API
        return 0

    def Statistical_report(self):
        # TODO: Replace with URL reputation API
        return 0

    def having_IP_Address(self):
        try:
            socket.inet_aton(self.parsed.netloc)
            return 1
        except:
            return 0

    def URL_Length(self):
        return int(len(self.url) >= 54)

    def Shortining_Service(self):
        pattern = re.compile(r"(bit\.ly|goo\.gl|t\.co|tinyurl|is\.gd|buff\.ly|ow\.ly)")
        return int(bool(pattern.search(self.url)))

    def having_At_Symbol(self):
        return int("@" in self.url)

    def double_slash_redirecting(self):
        return int(self.url.find("//", 7) != -1)

    def Prefix_Suffix(self):
        return int("-" in self.parsed.netloc)

    def having_Sub_Domain(self):
        return int(len(self.parsed.netloc.split(".")) > 3)

    def SSLfinal_State(self):
        return int(self.parsed.scheme == "https")

    def Favicon(self):
        try:
            icons = re.findall(r'<link[^>]*rel=["\']icon["\'][^>]*>', self._html, re.IGNORECASE)
            for tag in icons:
                m = re.search(r'href=["\']([^"\']+)["\']', tag)
                if m and urlparse(m.group(1)).netloc != self.parsed.netloc:
                    return 1
            return 0
        except:
            return 1

    def port(self):
        return int(self.parsed.port not in (None, 80, 443))

    def HTTPS_token(self):
        return int("https" in self.parsed.netloc.lower())

    def Request_URL(self):
        try:
            externals = re.findall(r'src=["\'](http[^"\']+)["\']', self._html, re.IGNORECASE)
            total = len(re.findall(r'src=', self._html, re.IGNORECASE))
            return int(total > 0 and len(externals)/total > 0.5)
        except:
            return 0

    def URL_of_Anchor(self):
        try:
            anchors = re.findall(r'<a[^>]*href=["\']([^"\']+)["\']', self._html, re.IGNORECASE)
            if not anchors:
                return 0
            external = [a for a in anchors if urlparse(a).netloc not in (self.parsed.netloc, "")]
            return int(len(external)/len(anchors) > 0.5)
        except:
            return 0

    def Links_in_tags(self):
        try:
            tags = re.findall(r'<link[^>]*href=["\']([^"\']+)["\']', self._html, re.IGNORECASE)
            if not tags:
                return 0
            external = [t for t in tags if urlparse(t).netloc not in (self.parsed.netloc, "")]
            return int(len(external)/len(tags) > 0.5)
        except:
            return 0

    def SFH(self):
        try:
            sfh = re.search(r'<form[^>]*action=["\']([^"\']+)["\']', self._html, re.IGNORECASE)
            if not sfh:
                return 0
            return int(urlparse(sfh.group(1)).netloc not in (self.parsed.netloc, ""))
        except:
            return 0

    def Submitting_to_email(self):
        return int(bool(re.search(r'mailto:', self._html, re.IGNORECASE)))

    def Abnormal_URL(self):
        return int(self.parsed.netloc not in self.url)

    def Redirect(self):
        return int(bool(re.search(r'http-equiv=["\']refresh["\']', self._html, re.IGNORECASE)))

    def on_mouseover(self):
        return int(bool(re.search(r'onmouseover', self._html, re.IGNORECASE)))

    def RightClick(self):
        return int(bool(re.search(r'event.button ?== ?2', self._html)))

    def popUpWidnow(self):
        return int(bool(re.search(r'window\.open\(', self._html)))

    def Iframe(self):
        return int(bool(re.search(r'<iframe', self._html, re.IGNORECASE)))

    def DNSRecord(self):
        try:
            socket.gethostbyname(self.parsed.netloc)
            return 1
        except:
            return 0

    def Google_Index(self):
        try:
            resp = requests.get(f"https://www.google.com/search?q=site:{self.parsed.netloc}", timeout=self.timeout)
            return int(resp.status_code == 200 and "did not match any documents" not in resp.text.lower())
        except:
            return 0

    def get_feature_vector(self):
        return [
            self.Domain_registeration_length(),
            self.age_of_domain(),
            self.web_traffic(),
            self.Page_Rank(),
            self.Links_pointing_to_page(),
            self.Statistical_report(),
            self.having_IP_Address(),
            self.URL_Length(),
            self.Shortining_Service(),
            self.having_At_Symbol(),
            self.double_slash_redirecting(),
            self.Prefix_Suffix(),
            self.having_Sub_Domain(),
            self.SSLfinal_State(),
            self.Favicon(),
            self.port(),
            self.HTTPS_token(),
            self.Request_URL(),
            self.URL_of_Anchor(),
            self.Links_in_tags(),
            self.SFH(),
            self.Submitting_to_email(),
            self.Abnormal_URL(),
            self.Redirect(),
            self.on_mouseover(),
            self.RightClick(),
            self.popUpWidnow(),
            self.Iframe(),
            self.DNSRecord(),
            self.Google_Index()
        ]
