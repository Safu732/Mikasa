
# Day 9 Networking & Observability Bootcamp - Ultra Simplified, Zero Dependencies

code = '''#!/usr/bin/env python3
"""
MIKASA OS v4.1.0 - DAY 9: NETWORKING, OBSERVABILITY & PRODUCTION INCIDENTS
Single file, zero dependencies, Termux ready.
"""

import os
import sys
import json
import time
import random
from datetime import datetime

# ========== COLORS ==========
class C:
    CYAN = "\\033[96m"
    GREEN = "\\033[92m"
    YELLOW = "\\033[93m"
    RED = "\\033[91m"
    MAGENTA = "\\033[95m"
    BLUE = "\\033[94m"
    BOLD = "\\033[1m"
    DIM = "\\033[2m"
    END = "\\033[0m"

def pc(text, color=""):
    print(f"{color}{text}{C.END}")

# ========== INCIDENTS ==========
INCIDENTS = [
    {
        "id": "INC-D9-001",
        "title": "DNS Outage - All API Calls Failing",
        "severity": "CRITICAL",
        "desc": "All external API calls are failing with 'Name or service not known'. Internal services work fine. Users cannot reach any external domain. DNS resolution is completely broken.",
        "symptoms": ["curl google.com fails with 'Could not resolve host'", "ping 8.8.8.8 works fine", "ping google.com fails", "nslookup google.com times out", "Internal IP-to-IP communication works"],
        "root_causes": ["DNS server (8.8.8.8) unreachable or blocked", "/etc/resolv.conf missing or corrupted", "Local DNS cache (systemd-resolved/nscd) crashed", "Firewall blocking UDP port 53", "VPN/DNS hijacking interfering"],
        "expected": ["cat /etc/resolv.conf", "nslookup google.com 8.8.8.8", "dig @8.8.8.8 google.com", "ss -lun | grep 53", "iptables -L | grep 53", "systemctl status systemd-resolved"],
        "hints": ["If ping 8.8.8.8 works but ping google.com fails, it's DNS, not network", "Check /etc/resolv.conf first - it's the DNS config file", "Try specifying DNS server explicitly: dig @8.8.8.8 google.com", "Check if UDP 53 is blocked by firewall"],
    },
    {
        "id": "INC-D9-002",
        "title": "Website Returning 502 Bad Gateway",
        "severity": "HIGH",
        "desc": "Users report the website shows '502 Bad Gateway'. The reverse proxy (nginx) is up. Backend application logs show no requests. Need to find the disconnect between proxy and backend.",
        "symptoms": ["Browser shows 502 Bad Gateway", "nginx error log shows 'connect() failed (111: Connection refused)'", "Backend process is running", "Backend listening on wrong port or interface", "No backend errors in application logs"],
        "root_causes": ["Backend listening on 127.0.0.1:5000 but proxy connecting to 0.0.0.0:5000 mismatch", "Backend crashed and restarted on different port", "SELinux/AppArmor blocking proxy-to-backend connection", "Backend socket file permissions wrong (Unix socket)", "Proxy timeout too short for slow backend startup"],
        "expected": ["ss -tlnp | grep 5000", "curl -I http://127.0.0.1:5000/health", "cat /var/log/nginx/error.log | tail", "ps aux | grep backend", "curl -v http://localhost/ 2>&1 | grep -E '(Connected|Failed)'", "getenforce (check SELinux)"],
        "hints": ["502 means proxy received invalid response from upstream - OR couldn't connect at all", "Check what the backend is ACTUALLY listening on: ss -tlnp", "Check nginx upstream config matches backend port", "Test backend directly: curl localhost:PORT/health"],
    },
    {
        "id": "INC-D9-003",
        "title": "API Timeout - 30s Delay on Every Request",
        "severity": "HIGH",
        "desc": "API responses that normally take 200ms now take 30+ seconds. Then they succeed. No errors in logs. Need to identify the network-level bottleneck.",
        "symptoms": ["curl -w '%{time_total}' shows 30.1s", "First packet delay is 30s (curl -w '%{time_connect}')", "After connection, data transfers fast", "Happens on NEW connections only", "Established connections are fast"],
        "root_causes": ["Reverse DNS lookup timeout (sshd, ident, or application doing PTR lookup)", "DNS resolution of client IP taking 30s then timing out", "TCP SYN queue full (SYN flood or backlog too small)", "Firewall doing deep packet inspection on first packet", "Load balancer health check interfering with new connections"],
        "expected": ["curl -w '@curl-format.txt' http://api/", "ss -tan | grep SYN-RECV | wc -l", "tcpdump -i any port 80 -n | head -20", "dig -x CLIENT_IP", "sysctl net.ipv4.tcp_max_syn_backlog", "strace -e connect,write curl http://api/ 2>&1 | head"],
        "hints": ["30 seconds is a classic timeout value - look for timeouts in DNS, TCP, or application", "Check if it's connection time vs transfer time: curl -w '%{time_connect} %{time_total}'", "Reverse DNS (PTR) lookups are a common 30s delay culprit", "tcpdump will show you WHERE the delay happens"],
    },
    {
        "id": "INC-D9-004",
        "title": "SSL Certificate Expired - HTTPS Failing",
        "severity": "CRITICAL",
        "desc": "All HTTPS traffic failing. Browsers show 'Your connection is not private'. Mobile apps cannot sync. Certificate expired 2 days ago. Need to diagnose and fix immediately.",
        "symptoms": ["curl -I https://site shows 'SSL certificate problem: certificate has expired'", "openssl s_client -connect site:443 shows 'verify error:num=10:certificate has expired'", "Certificate expiry date in past", "HTTP (non-SSL) works fine", "Certificate file exists and is readable"],
        "root_causes": ["Let's Encrypt auto-renewal cron job failed silently", "Certbot renewal requires port 80 which is blocked", "Wrong certificate file path in nginx config", "Certificate renewed but service not reloaded (nginx -s reload)", "Clock skew - system time is wrong, making valid cert appear expired"],
        "expected": ["openssl s_client -connect site:443 -servername site </dev/null 2>/dev/null | openssl x509 -noout -dates", "echo | openssl s_client -servername site -connect site:443 2>/dev/null | openssl x509 -noout -subject -dates", "certbot certificates", "date (check system time)", "nginx -t && nginx -s reload", "systemctl list-timers | grep certbot"],
        "hints": ["Always check system clock FIRST - wrong time makes valid certs look expired", "openssl x509 -noout -dates shows Not Before and Not After", "certbot certificates lists all managed certs", "nginx must be reloaded (not restarted) to pick up new certs"],
    },
    {
        "id": "INC-D9-005",
        "title": "Port Already in Use - Service Won't Start",
        "severity": "MEDIUM",
        "desc": "MIKASA OS backend fails to start with 'Address already in use'. The port is supposedly free. Need to find what's actually using it and why.",
        "symptoms": ["Error: 'OSError: [Errno 98] Address already in use'", "ss -tlnp shows nothing on that port", "lsof -i :PORT shows no output", "Process still fails to bind", "Happens after unclean shutdown"],
        "root_causes": ["Socket in TIME_WAIT state from previous connection", "Process in zombie state still holding socket", "Another process using same port on different interface", "SO_REUSEADDR not set in application code", "IPv6 vs IPv4 binding conflict (:::port vs 0.0.0.0:port)"],
        "expected": ["ss -tan | grep TIME-WAIT | grep PORT", "ss -tlnp | grep PORT", "lsof -i :PORT", "fuser PORT/tcp", "cat /proc/sys/net/ipv4/tcp_tw_reuse", "sysctl net.ipv4.tcp_tw_reuse"],
        "hints": ["TIME_WAIT sockets block new binds for 2*MSL (typically 60s)", "SO_REUSEADDR socket option allows reusing TIME_WAIT sockets", "Check both IPv4 and IPv6: ss -tlnp shows both", "fuser is a quick way to find what uses a port"],
    },
    {
        "id": "INC-D9-006",
        "title": "Firewall Blocking Traffic - Intermittent Drops",
        "severity": "HIGH",
        "desc": "Some users can access the API, others cannot. No pattern by geography. Works on WiFi, fails on mobile data. Suspect firewall or rate limiting.",
        "symptoms": ["curl works from office WiFi, fails from 4G", "Error: 'Connection timed out' (not refused)", "No server-side logs for failed requests", "tcpdump shows SYN packets arriving but no SYN-ACK", "iptables -L shows rules but complex chain"],
        "root_causes": ["iptables DROP rule for certain IP ranges or rate limits", "Cloud provider security group blocking mobile carrier IPs", "fail2ban banned legitimate IPs after failed auth attempts", "Conntrack table full, dropping new connections", "MTU mismatch causing packet fragmentation issues on mobile networks"],
        "expected": ["iptables -L -n -v | head -30", "iptables -L INPUT -n --line-numbers", "conntrack -L | wc -l", "cat /proc/sys/net/netfilter/nf_conntrack_max", "tcpdump -i any host CLIENT_IP and port 443", "ip route get CLIENT_IP"],
        "hints": ["'Connection timed out' = packet dropped (firewall), 'Connection refused' = no listener", "iptables -v shows packet counts - rules with high DROP counts are active", "conntrack table full is common on busy servers - check nf_conntrack_count", "tcpdump on both sides to see where packets disappear"],
    },
    {
        "id": "INC-D9-007",
        "title": "High Latency - 500ms+ on Local Network",
        "severity": "MEDIUM",
        "desc": "Ping to localhost takes 500ms. Local API calls are slow. CPU and memory are fine. Need to find why local network stack is slow.",
        "symptoms": ["ping 127.0.0.1 shows 500ms latency", "ss -tan shows many connections in CLOSE_WAIT", "High interrupt count on network interface", "ethtool shows errors or dropped packets", "No CPU or memory pressure"],
        "root_causes": ["DNS resolution of localhost (IPv6 vs IPv4 delay)", "iptables logging every packet (LOG target)", "TCP offloading disabled causing CPU overhead", "Network interface driver bug or outdated firmware", "Loopback interface misconfigured (MTU, etc.)"],
        "expected": ["ping -c 10 -i 0.2 127.0.0.1", "ss -tan | grep CLOSE-WAIT | wc -l", "ethtool -S eth0 | grep -i error", "cat /proc/interrupts | grep eth", "iptables -L | grep LOG", "sysctl net.ipv4.tcp_slow_start_after_idle"],
        "hints": ["Localhost should be <1ms. If it's slow, it's NOT physical network - it's software.", "CLOSE_WAIT sockets indicate application not closing connections properly", "iptables LOG target can add massive latency", "Check ethtool for hardware errors"],
    },
    {
        "id": "INC-D9-008",
        "title": "Broken Health Checks - False Positive Downtime",
        "severity": "HIGH",
        "desc": "Load balancer marks all backends as DOWN. Services are actually healthy. Health checks are failing. Users getting 503 Service Unavailable.",
        "symptoms": ["Load balancer health check returns 404", "Backend /health endpoint works with curl", "Health check uses wrong HTTP method (GET vs HEAD)", "Health check expects 200 but backend returns 204", "Health check timeout too short for slow startup"],
        "root_causes": ["Health check URL changed but LB config not updated", "Health check hits wrong port (management vs application)", "Health check lacks required Host header", "Backend health check requires authentication", "LB health check uses HTTP/1.0 but backend requires HTTP/1.1"],
        "expected": ["curl -I http://backend/health", "curl -v -H 'Host: example.com' http://backend/health", "curl -X HEAD http://backend/health", "curl -w '%{http_code} %{time_total}' http://backend/health", "ss -tlnp | grep backend", "grep health /etc/nginx/nginx.conf"],
        "hints": ["Always test health checks EXACTLY as the LB sends them", "curl -I (HEAD) vs curl (GET) can return different responses", "Check if Host header is required", "Check LB logs for exact request/response"],
    },
]

QUESTIONS = [
    {
        "q": "Explain the difference between TCP and UDP. When would you choose each for a service?",
        "cat": "Networking",
        "diff": "Mid",
        "keywords": ["connection-oriented", "connectionless", "reliable", "unordered", "handshake", "streaming", "datagram", "latency"],
        "followup": "Why is DNS primarily UDP? When does DNS switch to TCP?",
        "answer": "TCP: connection-oriented, reliable, ordered delivery, flow control, congestion control, 3-way handshake. Use for: HTTP/HTTPS, file transfers, databases, anything needing reliability. UDP: connectionless, unreliable, unordered, low latency, no handshake. Use for: DNS, VoIP, gaming, streaming, anything needing speed over reliability. DNS uses UDP for small queries (<512 bytes) because it's faster. Switches to TCP for: responses >512 bytes, zone transfers, DNSSEC (larger records).",
    },
    {
        "q": "What happens when you type 'curl https://google.com' in your terminal? Explain every step from DNS to TCP to TLS to HTTP.",
        "cat": "Networking",
        "diff": "Senior",
        "keywords": ["DNS resolution", "TCP handshake", "TLS handshake", "HTTP request", "SYN", "ACK", "certificate", "cipher", "GET", "response"],
        "followup": "What is the difference between a TCP SYN and a TCP SYN-ACK? What happens if SYN-ACK never arrives?",
        "answer": "1. DNS: Resolve google.com to IP via /etc/resolv.conf. 2. TCP: 3-way handshake (SYN -> SYN-ACK -> ACK). 3. TLS: ClientHello (cipher suites) -> ServerHello (chosen cipher) -> Certificate -> Key Exchange -> Finished. 4. HTTP: Send GET / HTTP/1.1 with Host header. 5. Server responds with HTTP response. 6. Connection may persist (Keep-Alive) or close. SYN is the initial connection request. SYN-ACK is the server's acknowledgment + its own SYN. If SYN-ACK never arrives, client retransmits SYN (typically 3-5 times, exponential backoff), then times out.",
    },
    {
        "q": "What is the difference between a 502 Bad Gateway and a 503 Service Unavailable? What about 504 Gateway Timeout?",
        "cat": "HTTP",
        "diff": "Mid",
        "keywords": ["upstream", "invalid response", "overloaded", "timeout", "proxy", "backend", "unavailable", "gateway"],
        "followup": "If you see 502 in nginx logs but the backend is running, what are 3 things to check?",
        "answer": "502 Bad Gateway: Proxy received INVALID response from upstream (backend sent malformed response, or connection refused, or backend crashed mid-response). 503 Service Unavailable: Server is OVERLOADED or intentionally unavailable (maintenance mode, rate limiting, circuit breaker). 504 Gateway Timeout: Proxy did NOT receive ANY response from upstream within timeout period (backend too slow, deadlocked, or network partition). For 502 with running backend: 1. Check backend port matches proxy config (ss -tlnp). 2. Check backend is listening on correct interface (127.0.0.1 vs 0.0.0.0). 3. Check SELinux/AppArmor blocking proxy-to-backend.",
    },
    {
        "q": "Explain how DNS resolution works. What is the difference between recursive and iterative queries?",
        "cat": "DNS",
        "diff": "Senior",
        "keywords": ["resolver", "root", "TLD", "authoritative", "recursive", "iterative", "cache", "TTL", "A record", "CNAME"],
        "followup": "What is DNS poisoning and how do you prevent it?",
        "answer": "DNS Resolution: 1. Check local cache (hosts file, nscd, systemd-resolved). 2. Query configured resolver (recursive). 3. Resolver queries root servers (.). 4. Root refers to TLD servers (.com). 5. TLD refers to authoritative servers (google.com). 6. Authoritative server returns A/AAAA record. Recursive query: Client asks resolver to do ALL the work and return final answer. Iterative query: Server returns best answer it has (referral if not authoritative). DNS poisoning: Attacker injects false DNS records into cache. Prevention: DNSSEC (cryptographic validation), DNS over HTTPS/TLS (encrypted queries), validate TTLs, use trusted resolvers.",
    },
    {
        "q": "What is the purpose of /etc/hosts, /etc/resolv.conf, and /etc/nsswitch.conf? In what order are they consulted?",
        "cat": "Linux",
        "diff": "Senior",
        "keywords": ["hosts", "resolv.conf", "nsswitch", "dns", "files", "order", "glibc", "resolver"],
        "followup": "If you add an entry to /etc/hosts but it doesn't work, what could be wrong?",
        "answer": "/etc/hosts: Static hostname-to-IP mappings. Checked first (usually). /etc/resolv.conf: DNS resolver configuration (nameservers, search domains, options). /etc/nsswitch.conf: Name Service Switch - defines ORDER of resolution sources (files, dns, mdns, etc.). Default order: files dns (check hosts first, then DNS). If /etc/hosts entry doesn't work: 1. nsswitch.conf has dns before files. 2. systemd-resolved is caching old DNS result. 3. nscd is caching. 4. Wrong format (needs IP hostname, not hostname IP). 5. IPv6 address taking precedence over IPv4.",
    },
    {
        "q": "Explain the difference between netstat and ss. Why is ss preferred on modern Linux?",
        "cat": "Linux",
        "diff": "Mid",
        "keywords": ["netstat", "ss", "/proc/net/tcp", "netlink", "performance", "deprecated", "iproute2", "socket"],
        "followup": "What information can ss show that netstat cannot?",
        "answer": "netstat: Reads /proc/net/* files sequentially. Slower on systems with many sockets. Part of net-tools (legacy, mostly deprecated). ss: Uses netlink socket interface (kernel-native). Much faster, especially with many connections. Part of iproute2 (modern, actively maintained). ss can show: TCP internal information (tcp_info), memory usage per socket, cgroup information, packet counters, timer information. On production systems with 100k+ connections, ss is orders of magnitude faster.",
    },
    {
        "q": "What is a TCP TIME_WAIT state? Why does it exist? When can it cause problems?",
        "cat": "Networking",
        "diff": "Senior",
        "keywords": ["TIME_WAIT", "2MSL", "connection", "delayed packets", "port exhaustion", "SO_REUSEADDR", "socket"],
        "followup": "How do you safely reduce TIME_WAIT sockets without breaking TCP?",
        "answer": "TIME_WAIT: State entered after active close. Waits 2*MSL (Maximum Segment Lifetime, typically 60s) before fully closing. Purpose: 1. Ensure remote end received final ACK. 2. Prevent delayed packets from old connection interfering with new connection using same port. Problems: Port exhaustion on busy servers (only 65535 ports, many in TIME_WAIT). Can block service restart. Solutions: SO_REUSEADDR socket option (allows reusing TIME_WAIT sockets for same local address). tcp_tw_reuse=1 (safe, only for outgoing connections). tcp_tw_recycle=0 (DANGEROUS, removed in kernel 4.12 - breaks NAT). NEVER use tcp_tw_recycle in production.",
    },
    {
        "q": "Design a monitoring system for MIKASA OS that detects network issues before users do. What metrics, alerts, and tools?",
        "cat": "Observability",
        "diff": "Staff",
        "keywords": ["metrics", "alerts", "SLI", "SLO", "latency", "throughput", "error rate", "blackbox", "whitebox", "prometheus", "grafana"],
        "followup": "What is the difference between black-box and white-box monitoring? When do you use each?",
        "answer": "Monitoring system design: Metrics: Latency (p50, p95, p99), throughput (req/s), error rate (%), DNS resolution time, TCP connection time, TLS handshake time, certificate expiry. Tools: Blackbox: ping, curl synthetic checks, DNS resolution tests from multiple locations. Whitebox: Application metrics (Prometheus), server metrics (node_exporter), log aggregation. Alerts: Latency p99 > 500ms for 5min, Error rate > 1% for 2min, Certificate expiry < 7 days, DNS resolution failure. Black-box: Tests from outside (user perspective). Use for: uptime, reachability, end-to-end latency. White-box: Internal application metrics. Use for: root cause analysis, capacity planning, business metrics.",
    },
]

# ========== SCORING ==========
class Scores:
    def __init__(self):
        self.linux = 0
        self.dns = 0
        self.http = 0
        self.incident = 0
        self.debug = 0
        self.cmd_quality = 0
        self.interview = 0
        self.commands = 0
        self.questions = 0
        self.incidents = 0
        self.start = datetime.now().isoformat()
        self.cmd_scores = []
        self.q_scores = []

    def overall(self):
        return int((self.linux + self.dns + self.http + self.incident + self.debug + self.cmd_quality + self.interview) / 7)

    def add_cmd(self, score, category):
        self.commands += 1
        self.cmd_scores.append((score, category))
        if category in ["Linux", "Networking"]:
            self.linux = int((self.linux * (len(self.cmd_scores)-1) + score) / len(self.cmd_scores))
        elif category == "DNS":
            self.dns = int((self.dns * (len(self.cmd_scores)-1) + score) / len(self.cmd_scores))
        elif category == "HTTP":
            self.http = int((self.http * (len(self.cmd_scores)-1) + score) / len(self.cmd_scores))
        elif category == "Incident":
            self.incident = int((self.incident * (len(self.cmd_scores)-1) + score) / len(self.cmd_scores))
        else:
            self.debug = int((self.debug * (len(self.cmd_scores)-1) + score) / len(self.cmd_scores))
        self.cmd_quality = int(sum(s for s, _ in self.cmd_scores) / len(self.cmd_scores))

    def add_q(self, score):
        self.questions += 1
        self.q_scores.append(score)
        self.interview = int((self.interview * (len(self.q_scores)-1) + score) / len(self.q_scores))

    def add_incident(self, resolved, bonus):
        if resolved:
            self.incidents += 1
            self.incident = min(100, self.incident + bonus)
            self.debug = min(100, self.debug + bonus // 2)

# ========== COMMAND REVIEW ==========
GOOD_PATTERNS = {
    "ss -tlnp": (20, "Excellent: ss is modern, fast, -tlnp shows TCP listening with processes. Senior choice over netstat."),
    "ss -tan": (15, "Good: Shows all TCP sockets with state. Good for finding CLOSE_WAIT, TIME_WAIT."),
    "ss -lun": (15, "Good: Shows UDP listening sockets. Essential for DNS debugging."),
    "ip addr": (15, "Good: Modern replacement for ifconfig. Shows all interfaces and IPs."),
    "ip route": (15, "Good: Shows routing table. Essential for connectivity debugging."),
    "dig ": (20, "Excellent: Full DNS query control. Shows query path, timing, all records. Senior tool."),
    "dig +trace": (25, "Excellent: Traces full DNS resolution path. Deep DNS debugging."),
    "nslookup": (10, "Acceptable: Basic DNS lookup. dig is preferred for detailed debugging."),
    "curl -I": (15, "Good: HEAD request for quick status check."),
    "curl -v": (20, "Excellent: Verbose mode shows full request/response + TLS handshake. Essential for HTTP debugging."),
    "curl -w": (20, "Excellent: Custom output format for timing metrics. Production-grade monitoring."),
    "curl --connect-timeout": (15, "Good: Sets connection timeout. Prevents hanging on network issues."),
    "ping -c": (10, "Good: Controlled ping count. Better than infinite ping."),
    "traceroute": (15, "Good: Shows path/route taken. Essential for routing issues."),
    "tcpdump": (25, "Excellent: Packet-level analysis. The ultimate network debugging tool."),
    "tcpdump -i any": (20, "Good: Captures on all interfaces. Useful when unsure which interface."),
    "lsof -i": (20, "Excellent: Shows network files/connections per process."),
    "lsof -i :": (20, "Excellent: Shows what process uses a specific port."),
    "openssl s_client": (25, "Excellent: Full TLS/SSL debugging. Shows certificate chain, cipher, handshake."),
    "openssl x509": (20, "Good: Certificate inspection. Check dates, subject, issuer."),
    "iptables -L": (15, "Good: List firewall rules. -v shows packet counts (active rules)."),
    "iptables -L -n -v": (20, "Excellent: Numeric, verbose listing. Shows actual packet hits per rule."),
    "conntrack -L": (15, "Good: Lists connection tracking table. Check for table full issues."),
    "ethtool": (20, "Excellent: Interface statistics, offload settings, driver info."),
    "sysctl net.": (15, "Good: Check kernel network parameters."),
    "nc -zv": (15, "Good: Port connectivity test. Quick and lightweight."),
    "nc -l": (15, "Good: Start listener for testing. Useful for firewall testing."),
    "fuser": (15, "Good: Find process using file/socket/port."),
    "host ": (10, "Acceptable: Simple DNS lookup. dig is more powerful."),
    "whois": (10, "Good: Domain/IP registration info."),
    "mtr": (20, "Excellent: Combined ping + traceroute with statistics. Real-time path analysis."),
    "nmap -p": (15, "Good: Port scanning. Use carefully in production."),
    "certbot": (15, "Good: Certificate management. Check expiry and renewal."),
    "journalctl -u": (15, "Good: Service-specific logs. Systemd integration."),
    "cat /etc/resolv.conf": (15, "Good: First check for DNS issues. Shows configured nameservers."),
    "cat /etc/hosts": (10, "Good: Check static host mappings."),
    "cat /etc/nsswitch.conf": (15, "Good: Check name resolution order."),
}

BAD_PATTERNS = {
    "netstat": (-5, "Legacy tool. Use ss instead. netstat reads /proc sequentially and is slow."),
    "ifconfig": (-5, "Deprecated. Use ip addr instead."),
    "route": (-5, "Deprecated. Use ip route instead."),
    "kill -9": (-20, "SIGKILL is last resort. Try SIGTERM first."),
    "chmod 777": (-25, "Violates least privilege. Use 755/644."),
    "rm -rf /": (-100, "DANGER: Will destroy system. Never run this."),
    "iptables -F": (-30, "Flushes ALL rules. Will lock you out if remote. Always backup first."),
    "systemctl restart networking": (-15, "Blunt restart. May disconnect your SSH session. Use ip commands instead."),
    "tcpdump -w /dev/null": (-10, "Wasting disk I/O. Use -c for limited capture or proper filter."),
}

def review_command(cmd):
    score = 50
    feedback = []
    category = "General"
    base = cmd.split()[0] if cmd.split() else ""
    
    if base in ["ss", "ip", "ethtool", "sysctl", "iptables", "conntrack"]:
        category = "Linux"
    elif base in ["dig", "nslookup", "host", "whois"]:
        category = "DNS"
    elif base in ["curl", "wget", "openssl"]:
        category = "HTTP"
    elif base in ["ping", "traceroute", "mtr", "tcpdump", "nc", "lsof"]:
        category = "Networking"
    elif base in ["cat"] and any(x in cmd for x in ["resolv", "hosts", "nsswitch"]):
        category = "DNS"
    elif base in ["journalctl", "systemctl", "service"]:
        category = "Incident"
    
    for pattern, (delta, msg) in GOOD_PATTERNS.items():
        if pattern in cmd:
            score += delta
            feedback.append(f"[GOOD] {msg}")
    
    for pattern, (delta, msg) in BAD_PATTERNS.items():
        if pattern in cmd:
            score += delta
            feedback.append(f"[BAD] {msg}")
    
    score = max(0, min(100, score))
    
    if score >= 80:
        verdict = "SENIOR-LEVEL"
    elif score >= 60:
        verdict = "ACCEPTABLE"
    elif score >= 40:
        verdict = "NEEDS IMPROVEMENT"
    else:
        verdict = "JUNIOR MISTAKE"
    
    return score, verdict, category, " | ".join(feedback) if feedback else "No specific feedback."

# ========== INTERVIEW ==========
def evaluate_answer(q, ans):
    ans_lower = ans.lower()
    score = 30
    feedback = []
    
    matched = [kw for kw in q["keywords"] if kw.lower() in ans_lower]
    score += len(matched) * 10
    if matched:
        feedback.append(f"Good keywords: {', '.join(matched)}")
    
    depth = ["because", "therefore", "however", "for example", "specifically", "furthermore", "additionally"]
    dc = sum(1 for d in depth if d in ans_lower)
    score += dc * 5
    if dc >= 2:
        feedback.append("Strong explanatory depth")
    
    score = max(0, min(100, score))
    
    if score >= 80:
        grade = "STAFF-LEVEL"
    elif score >= 60:
        grade = "SENIOR-LEVEL"
    elif score >= 40:
        grade = "ACCEPTABLE"
    else:
        grade = "NEEDS STUDY"
    
    return score, f"[{grade}] " + " | ".join(feedback)

# ========== UI ==========
def banner():
    print()
    pc("=" * 60, C.CYAN)
    pc("  MIKASA OS v4.1.0 - DAY 9", C.BOLD + C.CYAN)
    pc("  NETWORKING, OBSERVABILITY & PRODUCTION INCIDENTS", C.CYAN)
    pc("=" * 60, C.CYAN)
    print()

def show_menu():
    print("1. Start Incident Simulation")
    print("2. Review My Command")
    print("3. Interview Question")
    print("4. View Current Scores")
    print("5. Networking Cheatsheet")
    print("6. End Session & Generate Report")
    print()

def show_scores(scores):
    print()
    pc("SESSION SCORES", C.BOLD + C.CYAN)
    print(f"  Linux Net:   {scores.linux:>3}/100  {'█' * (scores.linux // 5)}{'░' * (20 - scores.linux // 5)}")
    print(f"  DNS:         {scores.dns:>3}/100  {'█' * (scores.dns // 5)}{'░' * (20 - scores.dns // 5)}")
    print(f"  HTTP Debug:  {scores.http:>3}/100  {'█' * (scores.http // 5)}{'░' * (20 - scores.http // 5)}")
    print(f"  Incident:    {scores.incident:>3}/100  {'█' * (scores.incident // 5)}{'░' * (20 - scores.incident // 5)}")
    print(f"  Debug:       {scores.debug:>3}/100  {'█' * (scores.debug // 5)}{'░' * (20 - scores.debug // 5)}")
    print(f"  Cmd Quality: {scores.cmd_quality:>3}/100  {'█' * (scores.cmd_quality // 5)}{'░' * (20 - scores.cmd_quality // 5)}")
    print(f"  Interview:   {scores.interview:>3}/100  {'█' * (scores.interview // 5)}{'░' * (20 - scores.interview // 5)}")
    print(f"  OVERALL:     {scores.overall():>3}/100  {'█' * (scores.overall() // 5)}{'░' * (20 - scores.overall() // 5)}")
    print()

def show_cheatsheet():
    print()
    pc("NETWORKING CHEATSHEET", C.BOLD + C.CYAN)
    print("""
SOCKET & CONNECTION INSPECTION
  ss -tlnp              TCP listening + processes
  ss -tan               All TCP sockets with states
  ss -lun               UDP listening sockets
  ss -s                 Socket statistics summary
  lsof -i :PORT         What uses this port
  lsof -i -P -n | grep LISTEN   All listening sockets

IP & ROUTING
  ip addr               Show all interfaces and IPs
  ip route              Show routing table
  ip route get IP       Which route would be used
  ip neigh              ARP table
  ip link set eth0 up   Enable interface

DNS
  dig google.com        Full DNS query
  dig +trace google.com   Trace full resolution
  dig @8.8.8.8 google.com  Query specific server
  nslookup google.com   Basic lookup
  host google.com       Simple lookup
  cat /etc/resolv.conf  DNS config
  cat /etc/hosts        Static mappings
  cat /etc/nsswitch.conf    Resolution order

HTTP/HTTPS
  curl -I http://site   HEAD request
  curl -v http://site   Verbose (full exchange)
  curl -w '%{time_connect} %{time_total}' URL   Timing
  curl -o /dev/null -s -w '%{http_code}' URL    Status only
  openssl s_client -connect site:443    TLS debug
  openssl x509 -noout -dates -in cert.pem   Check dates

CONNECTIVITY
  ping -c 4 IP          Basic reachability
  traceroute IP         Route path
  mtr IP                Combined ping+traceroute
  nc -zv IP PORT        Port connectivity test
  nc -l PORT            Start listener

PACKET CAPTURE
  tcpdump -i any port 80    Capture HTTP
  tcpdump -i any host IP    Capture specific host
  tcpdump -c 100 -w file.pcap   Save to file
  tcpdump -r file.pcap      Read from file

FIREWALL
  iptables -L -n -v     List rules with counts
  iptables -L INPUT --line-numbers   Numbered rules
  conntrack -L | wc -l  Connection count
  cat /proc/sys/net/netfilter/nf_conntrack_count

CERTIFICATES
  certbot certificates    List certs
  openssl x509 -in cert.pem -noout -text   Full info
  echo | openssl s_client -servername site -connect site:443 2>/dev/null | openssl x509 -noout -dates

PERFORMANCE
  ethtool -S eth0       Interface stats
  ethtool eth0          Link speed/duplex
  sysctl net.ipv4.tcp_tw_reuse    TIME_WAIT reuse
  sysctl net.core.somaxconn       Max backlog
""")

def run_incident(incident, scores):
    print()
    pc(f"INCIDENT: {incident['id']}", C.BOLD + C.RED)
    pc(f"Title: {incident['title']}", C.YELLOW)
    pc(f"Severity: {incident['severity']}", C.RED)
    print(f"Description: {incident['desc']}")
    print()
    print("Symptoms:")
    for s in incident["symptoms"]:
        print(f"  - {s}")
    print()
    print("Time Limit: 15 minutes")
    print("Commands: done=resolved | hint=help | giveup=solution | postmortem=template")
    print()
    
    start = time.time()
    while True:
        cmd = input("> shell: ").strip()
        if cmd.lower() == "done":
            elapsed = time.time() - start
            found = input("Did you identify the root cause? (yes/no): ").lower().startswith("y")
            resolved = elapsed < 900 and found
            bonus = max(0, int((900 - elapsed) / 900 * 20))
            scores.add_incident(resolved, bonus)
            if resolved:
                pc("Incident RESOLVED. Good work, SRE.", C.GREEN)
            else:
                pc("Incident NOT fully resolved.", C.YELLOW)
                print("Root causes:")
                for rc in incident["root_causes"]:
                    print(f"  - {rc}")
            break
        elif cmd.lower() == "hint":
            pc(f"HINT: {random.choice(incident['hints'])}", C.YELLOW)
        elif cmd.lower() == "giveup":
            pc("SOLUTION:", C.RED)
            for rc in incident["root_causes"]:
                print(f"  - {rc}")
            print("Expected commands:")
            for ec in incident["expected"]:
                print(f"  $ {ec}")
            break
        elif cmd.lower() == "postmortem":
            print()
            print("POST-MORTEM TEMPLATE:")
            print(f"Incident: {incident['id']} - {incident['title']}")
            print("Timeline: T+0 Alert -> T+2 Triage -> T+5 Root Cause -> T+10 Fix -> T+15 Verify")
            print("Root Cause: [Your analysis]")
            print("Fix Applied: [Your commands]")
            print("Prevention: [How to avoid recurrence]")
        elif cmd:
            score, verdict, category, feedback = review_command(cmd)
            scores.add_cmd(score, category)
            print()
            pc(f"Command: {cmd}", C.CYAN)
            pc(f"Score: {score}/100 | Verdict: {verdict} | Category: {category}", C.BOLD)
            print(f"Feedback: {feedback}")
            print()

def run_interview(scores):
    q = random.choice(QUESTIONS)
    print()
    pc(f"INTERVIEW QUESTION [{q['diff']}] [{q['cat']}]", C.BOLD + C.MAGENTA)
    print(q["q"])
    print(f"Follow-up: {q['followup']}")
    print()
    print("Type your answer (empty line to submit):")
    lines = []
    while True:
        line = input()
        if line == "" and lines:
            break
        lines.append(line)
    answer = "\\n".join(lines)
    score, feedback = evaluate_answer(q, answer)
    scores.add_q(score)
    print()
    pc(f"Score: {score}/100", C.BOLD)
    print(feedback)
    print()
    pc("MODEL ANSWER:", C.GREEN)
    print(q["answer"])
    print()

def generate_report(scores):
    print()
    pc("=" * 60, C.CYAN)
    pc("DAY 9 SESSION REPORT", C.BOLD + C.CYAN)
    pc("=" * 60, C.CYAN)
    show_scores(scores)
    print(f"Commands Reviewed: {scores.commands}")
    print(f"Questions Answered: {scores.questions}")
    print(f"Incidents Resolved: {scores.incidents}")
    print()
    pc("INTERVIEWER NOTES", C.BOLD)
    if scores.linux >= 75:
        print("Strong Linux networking knowledge.")
    else:
        print("Linux networking needs reinforcement. Practice ss, ip, iptables.")
    if scores.dns >= 75:
        print("Excellent DNS debugging skills.")
    else:
        print("DNS knowledge needs work. Master dig, resolv.conf, nsswitch.")
    if scores.http >= 75:
        print("Strong HTTP/TLS debugging.")
    else:
        print("HTTP debugging needs practice. Use curl -v and openssl s_client more.")
    if scores.incident >= 75:
        print("Good incident response instincts.")
    else:
        print("Incident response is reactive. Practice structured debugging.")
    if scores.interview >= 70:
        print("Interview answers show depth and trade-off awareness.")
    else:
        print("Interview answers need more depth. Explain the WHY, not just WHAT.")
    
    # Find biggest strength and weakness
    cats = [("Linux Networking", scores.linux), ("DNS", scores.dns), ("HTTP Debug", scores.http),
            ("Incident Response", scores.incident), ("Debugging", scores.debug), 
            ("Command Quality", scores.cmd_quality), ("Interview", scores.interview)]
    cats.sort(key=lambda x: x[1])
    
    print()
    pc("BIGGEST STRENGTH", C.BOLD + C.GREEN)
    print(f"  {cats[-1][0]}: {cats[-1][1]}/100")
    pc("BIGGEST WEAKNESS", C.BOLD + C.RED)
    print(f"  {cats[0][0]}: {cats[0][1]}/100")
    
    print()
    pc("DAY 10 ROADMAP", C.BOLD + C.YELLOW)
    if scores.linux < 70:
        print("- Linux Networking: eBPF, XDP, kernel networking stack")
    if scores.dns < 70:
        print("- DNS Mastery: DNSSEC, DoH/DoT, BIND configuration")
    if scores.http < 70:
        print("- HTTP Deep Dive: HTTP/2, HTTP/3, QUIC, load balancing algorithms")
    if scores.incident < 70:
        print("- Incident Command: Runbooks, post-mortems, blameless culture")
    if scores.debug < 70:
        print("- Advanced Debugging: Wireshark, eBPF networking, tc (traffic control)")
    if scores.overall() >= 80:
        print("- Advanced: SDN, BGP, Anycast, DDoS mitigation")
        print("- Leadership: Network architecture design, mentor juniors")
    
    print()
    pc("STAFF-LEVEL INTERVIEW QUESTION", C.BOLD + C.RED)
    print(random.choice([
        "Design a globally distributed load balancing system for MIKASA OS. How do you handle failover, latency, and consistency across regions?",
        "A DDoS attack is hitting your API. Walk me through your response: detection, mitigation, communication, and recovery.",
        "Explain how you would debug a 1% packet loss that only affects a specific mobile carrier's users.",
        "Design a zero-trust network architecture for MIKASA OS running on 10,000 Android devices.",
        "You need to migrate MIKASA OS from IPv4-only to dual-stack IPv4/IPv6. What are the risks, and how do you roll back if needed?",
    ]))
    print()
    
    # Save report
    os.makedirs("reports", exist_ok=True)
    fname = f"reports/day9_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    with open(fname, "w") as f:
        f.write(f"MIKASA OS DAY 9 REPORT\\n")
        f.write(f"Linux: {scores.linux}/100\\n")
        f.write(f"DNS: {scores.dns}/100\\n")
        f.write(f"HTTP: {scores.http}/100\\n")
        f.write(f"Incident: {scores.incident}/100\\n")
        f.write(f"Debug: {scores.debug}/100\\n")
        f.write(f"Cmd Quality: {scores.cmd_quality}/100\\n")
        f.write(f"Interview: {scores.interview}/100\\n")
        f.write(f"Overall: {scores.overall()}/100\\n")
    pc(f"Report saved to: {fname}", C.GREEN)

# ========== MAIN ==========
def main():
    banner()
    scores = Scores()
    
    while True:
        show_menu()
        choice = input("> Select: ").strip()
        
        if choice == "1":
            print()
            for i, inc in enumerate(INCIDENTS, 1):
                print(f"[{i}] [{inc['severity']}] {inc['title']}")
            idx = int(input("> Select incident: ")) - 1
            if 0 <= idx < len(INCIDENTS):
                run_incident(INCIDENTS[idx], scores)
        elif choice == "2":
            print()
            cmd = input("> Enter command: ").strip()
            if cmd:
                score, verdict, category, feedback = review_command(cmd)
                scores.add_cmd(score, category)
                print()
                pc(f"Score: {score}/100 | {verdict}", C.BOLD)
                print(f"Feedback: {feedback}")
        elif choice == "3":
            run_interview(scores)
        elif choice == "4":
            show_scores(scores)
        elif choice == "5":
            show_cheatsheet()
        elif choice in ("6", "exit", "quit"):
            generate_report(scores)
            pc("Goodbye, pilot. See you on Day 10.", C.CYAN)
            break
        else:
            pc("Invalid choice. Use 1-6.", C.RED)

if __name__ == "__main__":
    main()
'''

output_path = "/mnt/agents/output/mikasa_day9_networking.py"
with open(output_path, "w", encoding="utf-8") as f:
    f.write(code)

print(f"File written: {output_path}")
print(f"Size: {len(code):,} chars | {len(code.splitlines()):,} lines")
# 2. Path ko automatic Termux friendly set karo
sed -i 's|/mnt/agents/output/mikasa_day9_networking.py|mikasa_day9_report.txt|g' mikasa_day9.py
