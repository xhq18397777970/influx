##mixed-port: 7890
allow-lan: true
bind-address: '*'
mode: rule
log-level: info
external-controller: '127.0.0.1:9090'
dns:
    enable: true
    ipv6: false
    default-nameserver: [223.5.5.5, 119.29.29.29]
    enhanced-mode: fake-ip
    fake-ip-range: 198.18.0.1/16
    use-hosts: true
    nameserver: [223.5.5.5, 119.29.29.29, 'https://223.5.5.5/dns-query', 'https://120.53.53.53/dns-query', 'https://dns.alidns.com/dns-query', 'https://doh.pub/dns-query']
    proxy-server-nameserver: [223.5.5.5, 119.29.29.29, 'https://223.5.5.5/dns-query', 'https://120.53.53.53/dns-query', 'https://dns.alidns.com/dns-query', 'https://doh.pub/dns-query']
proxies:
    - { name: '🇸🇬|新加坡-IEPL 01', type: trojan, server: T4c8BXS8kj.catcat321.com, port: 20036, password: 7216533d-c209-4537-a621-f9ac589caa8e, udp: true, sni: SG.catxstar.com, skip-cert-verify: true }
    - { name: '🇸🇬|新加坡-IEPL 02', type: trojan, server: T4c8BXS8kj.catcat321.com, port: 20039, password: 7216533d-c209-4537-a621-f9ac589caa8e, udp: true, sni: SG.catxstar.com, skip-cert-verify: true }
    - { name: '🇸🇬|新加坡-IEPL 03', type: trojan, server: ORc8TY6kc.catcat321.com, port: 20083, password: 7216533d-c209-4537-a621-f9ac589caa8e, udp: true, sni: SG.catxstar.com, skip-cert-verify: true }
    - { name: '🇸🇬|新加坡-进阶IEPL 01', type: trojan, server: ORc8TY6kc.catcat321.com, port: 20060, password: 7216533d-c209-4537-a621-f9ac589caa8e, udp: true, sni: SG.catxstar.com, skip-cert-verify: true }
    - { name: '🇸🇬|新加坡-进阶IEPL 02', type: trojan, server: ORc8TY6kc.catcat321.com, port: 20070, password: 7216533d-c209-4537-a621-f9ac589caa8e, udp: true, sni: SG.catxstar.com, skip-cert-verify: true }
    - { name: '🇸🇬|新加坡-进阶IEPL 03', type: trojan, server: T4c8BXS8kj.catcat321.com, port: 20089, password: 7216533d-c209-4537-a621-f9ac589caa8e, udp: true, sni: SG.catxstar.com, skip-cert-verify: true }
    - { name: '🇸🇬|新加坡-进阶IEPL 04', type: trojan, server: T4c8BXS8kj.catcat321.com, port: 20072, password: 7216533d-c209-4537-a621-f9ac589caa8e, udp: true, sni: SG.catxstar.com, skip-cert-verify: true }
    - { name: 🇸🇬|新加坡-直连, type: trojan, server: d1.catcat321.com, port: 49419, password: 7216533d-c209-4537-a621-f9ac589caa8e, udp: true, sni: d.sgj1.cat.bilibili.com, skip-cert-verify: true }
    - { name: '🇸🇬|新加坡-中转 01', type: trojan, server: R2.tube-cat.com, port: 9210, password: 7216533d-c209-4537-a621-f9ac589caa8e, udp: true, sni: sg.weixin.qq.com, skip-cert-verify: true }
    - { name: '🇸🇬|新加坡-中转 02', type: trojan, server: R1.tube-cat.com, port: 9195, password: 7216533d-c209-4537-a621-f9ac589caa8e, udp: true, sni: sg.weixin.qq.com, skip-cert-verify: true }
    - { name: '🇸🇬|新加坡-中转 03', type: trojan, server: R1.tube-cat.com, port: 9220, password: 7216533d-c209-4537-a621-f9ac589caa8e, udp: true, sni: sg.weixin.qq.com, skip-cert-verify: true }
    - { name: '🇸🇬|新加坡-中转 04', type: trojan, server: R2.tube-cat.com, port: 9205, password: 7216533d-c209-4537-a621-f9ac589caa8e, udp: true, sni: sg.weixin.qq.com, skip-cert-verify: true }
    - { name: '🇯🇵|日本-IEPL 01', type: trojan, server: T4c8BXS8kj.catcat321.com, port: 20080, password: 7216533d-c209-4537-a621-f9ac589caa8e, udp: true, sni: JP.catxstar.com, skip-cert-verify: true }
    - { name: '🇯🇵|日本-IEPL 02', type: trojan, server: ORc8TY6kc.catcat321.com, port: 20076, password: 7216533d-c209-4537-a621-f9ac589caa8e, udp: true, sni: JP.catxstar.com, skip-cert-verify: true }
    - { name: '🇯🇵|日本-中转 01', type: trojan, server: R1.tube-cat.com, port: 9410, password: 7216533d-c209-4537-a621-f9ac589caa8e, udp: true, sni: jp.weixin.qq.com, skip-cert-verify: true }
    - { name: '🇯🇵|日本-中转 02', type: trojan, server: R2.tube-cat.com, port: 9410, password: 7216533d-c209-4537-a621-f9ac589caa8e, udp: true, sni: jp.weixin.qq.com, skip-cert-verify: true }
    - { name: '🇯🇵|日本原生-IEPL 01', type: trojan, server: T4c8BXS8kj.catcat321.com, port: 20030, password: 7216533d-c209-4537-a621-f9ac589caa8e, udp: true, sni: JP.catxstar.com, skip-cert-verify: true }
    - { name: '🇯🇵|日本原生-IEPL 02', type: trojan, server: ORc8TY6kc.catcat321.com, port: 20061, password: 7216533d-c209-4537-a621-f9ac589caa8e, udp: true, sni: JP.catxstar.com, skip-cert-verify: true }
    - { name: '🇯🇵|日本星链家宽-IEPL 01', type: trojan, server: T4c8BXS8kj.catcat321.com, port: 20004, password: 7216533d-c209-4537-a621-f9ac589caa8e, udp: true, sni: JP.catxstar.com, skip-cert-verify: true }
    - { name: '🇯🇵|日本星链家宽-IEPL 02', type: trojan, server: ORc8TY6kc.catcat321.com, port: 20004, password: 7216533d-c209-4537-a621-f9ac589caa8e, udp: true, sni: JP.catxstar.com, skip-cert-verify: true }
    - { name: '🇯🇵|日本原生-中转 01', type: trojan, server: R1.tube-cat.com, port: 9420, password: 7216533d-c209-4537-a621-f9ac589caa8e, udp: true, sni: jp.weixin.qq.com, skip-cert-verify: true }
    - { name: '🇯🇵|日本原生-中转 02', type: trojan, server: R2.tube-cat.com, port: 9425, password: 7216533d-c209-4537-a621-f9ac589caa8e, udp: true, sni: jp.weixin.qq.com, skip-cert-verify: true }
    - { name: 🇯🇵|日本原生-直连, type: trojan, server: d1.catcat321.com, port: 47749, password: 7216533d-c209-4537-a621-f9ac589caa8e, udp: true, sni: d.jpj1.cat.bilibili.com, skip-cert-verify: true }
proxy-groups:
    - { name: 节点选择, type: select, proxies: [自动选择, '🇸🇬|新加坡-IEPL 01', '🇸🇬|新加坡-IEPL 02', '🇸🇬|新加坡-IEPL 03', '🇸🇬|新加坡-进阶IEPL 01', '🇸🇬|新加坡-进阶IEPL 02', '🇸🇬|新加坡-进阶IEPL 03', '🇸🇬|新加坡-进阶IEPL 04', 🇸🇬|新加坡-直连, '🇸🇬|新加坡-中转 01', '🇸🇬|新加坡-中转 02', '🇸🇬|新加坡-中转 03', '🇸🇬|新加坡-中转 04', '🇯🇵|日本-IEPL 01', '🇯🇵|日本-IEPL 02', '🇯🇵|日本-中转 01', '🇯🇵|日本-中转 02', '🇯🇵|日本原生-IEPL 01', '🇯🇵|日本原生-IEPL 02', '🇯🇵|日本星链家宽-IEPL 01', '🇯🇵|日本星链家宽-IEPL 02', '🇯🇵|日本原生-中转 01', '🇯🇵|日本原生-中转 02', 🇯🇵|日本原生-直连] }
    - { name: 自动选择, type: url-test, proxies: ['🇸🇬|新加坡-IEPL 01', '🇸🇬|新加坡-IEPL 02', '🇸🇬|新加坡-IEPL 03', '🇸🇬|新加坡-进阶IEPL 01', '🇸🇬|新加坡-进阶IEPL 02', '🇸🇬|新加坡-进阶IEPL 03', '🇸🇬|新加坡-进阶IEPL 04', 🇸🇬|新加坡-直连, '🇸🇬|新加坡-中转 01', '🇸🇬|新加坡-中转 02', '🇸🇬|新加坡-中转 03', '🇸🇬|新加坡-中转 04', '🇯🇵|日本-IEPL 01', '🇯🇵|日本-IEPL 02', '🇯🇵|日本-中转 01', '🇯🇵|日本-中转 02', '🇯🇵|日本原生-IEPL 01', '🇯🇵|日本原生-IEPL 02', '🇯🇵|日本星链家宽-IEPL 01', '🇯🇵|日本星链家宽-IEPL 02', '🇯🇵|日本原生-中转 01', '🇯🇵|日本原生-中转 02', 🇯🇵|日本原生-直连], url: 'http://cp.cloudflare.com', interval: 7200 }
    - { name: 国际媒体, type: select, proxies: [节点选择, '🇸🇬|新加坡-IEPL 01', '🇸🇬|新加坡-IEPL 02', '🇸🇬|新加坡-IEPL 03', '🇸🇬|新加坡-进阶IEPL 01', '🇸🇬|新加坡-进阶IEPL 02', '🇸🇬|新加坡-进阶IEPL 03', '🇸🇬|新加坡-进阶IEPL 04', 🇸🇬|新加坡-直连, '🇸🇬|新加坡-中转 01', '🇸🇬|新加坡-中转 02', '🇸🇬|新加坡-中转 03', '🇸🇬|新加坡-中转 04', '🇯🇵|日本-IEPL 01', '🇯🇵|日本-IEPL 02', '🇯🇵|日本-中转 01', '🇯🇵|日本-中转 02', '🇯🇵|日本原生-IEPL 01', '🇯🇵|日本原生-IEPL 02', '🇯🇵|日本星链家宽-IEPL 01', '🇯🇵|日本星链家宽-IEPL 02', '🇯🇵|日本原生-中转 01', '🇯🇵|日本原生-中转 02', 🇯🇵|日本原生-直连] }
    - { name: 电报代理, type: select, proxies: [节点选择, '🇸🇬|新加坡-IEPL 01', '🇸🇬|新加坡-IEPL 02', '🇸🇬|新加坡-IEPL 03', '🇸🇬|新加坡-进阶IEPL 01', '🇸🇬|新加坡-进阶IEPL 02', '🇸🇬|新加坡-进阶IEPL 03', '🇸🇬|新加坡-进阶IEPL 04', 🇸🇬|新加坡-直连, '🇸🇬|新加坡-中转 01', '🇸🇬|新加坡-中转 02', '🇸🇬|新加坡-中转 03', '🇸🇬|新加坡-中转 04', '🇯🇵|日本-IEPL 01', '🇯🇵|日本-IEPL 02', '🇯🇵|日本-中转 01', '🇯🇵|日本-中转 02', '🇯🇵|日本原生-IEPL 01', '🇯🇵|日本原生-IEPL 02', '🇯🇵|日本星链家宽-IEPL 01', '🇯🇵|日本星链家宽-IEPL 02', '🇯🇵|日本原生-中转 01', '🇯🇵|日本原生-中转 02', 🇯🇵|日本原生-直连] }
    - { name: 蒸汽平台, type: select, proxies: [DIRECT, '🇸🇬|新加坡-IEPL 01', '🇸🇬|新加坡-IEPL 02', '🇸🇬|新加坡-IEPL 03', '🇸🇬|新加坡-进阶IEPL 01', '🇸🇬|新加坡-进阶IEPL 02', '🇸🇬|新加坡-进阶IEPL 03', '🇸🇬|新加坡-进阶IEPL 04', 🇸🇬|新加坡-直连, '🇸🇬|新加坡-中转 01', '🇸🇬|新加坡-中转 02', '🇸🇬|新加坡-中转 03', '🇸🇬|新加坡-中转 04', '🇯🇵|日本-IEPL 01', '🇯🇵|日本-IEPL 02', '🇯🇵|日本-中转 01', '🇯🇵|日本-中转 02', '🇯🇵|日本原生-IEPL 01', '🇯🇵|日本原生-IEPL 02', '🇯🇵|日本星链家宽-IEPL 01', '🇯🇵|日本星链家宽-IEPL 02', '🇯🇵|日本原生-中转 01', '🇯🇵|日本原生-中转 02', 🇯🇵|日本原生-直连] }
rules:
    - 'DOMAIN-SUFFIX,t.me,电报代理'
    - 'DOMAIN-SUFFIX,tdesktop.com,电报代理'
    - 'DOMAIN-SUFFIX,telegra.ph,电报代理'
    - 'DOMAIN-SUFFIX,telegram.me,电报代理'
    - 'DOMAIN-SUFFIX,telegram.org,电报代理'
    - 'DOMAIN-SUFFIX,telesco.pe,电报代理'
    - 'IP-CIDR,91.108.4.0/22,电报代理'
    - 'IP-CIDR,91.108.8.0/22,电报代理'
    - 'IP-CIDR,91.108.12.0/22,电报代理'
    - 'IP-CIDR,91.108.16.0/22,电报代理'
    - 'IP-CIDR,91.108.20.0/22,电报代理'
    - 'IP-CIDR,91.108.56.0/22,电报代理'
    - 'IP-CIDR,91.105.192.0/23,电报代理'
    - 'IP-CIDR,149.154.160.0/20,电报代理'
    - 'IP-CIDR,185.76.151.0/24,电报代理'
    - 'IP-CIDR,2001:b28:f23d::/48,电报代理'
    - 'IP-CIDR,2001:b28:f23f::/48,电报代理'
    - 'IP-CIDR,2001:67c:4e8::/48,电报代理'
    - 'IP-CIDR,2001:b28:f23c::/48,电报代理'
    - 'IP-CIDR,2a0a:f280::/32,电报代理'
    - 'DOMAIN-SUFFIX,steam-chat.com,蒸汽平台'
    - 'DOMAIN-SUFFIX,steamcontent.com,蒸汽平台'
    - 'DOMAIN-SUFFIX,steamgames.com,蒸汽平台'
    - 'DOMAIN-SUFFIX,steampowered.com,蒸汽平台'
    - 'DOMAIN-SUFFIX,steamstat.us,蒸汽平台'
    - 'DOMAIN-SUFFIX,steamstatic.com,蒸汽平台'
    - 'DOMAIN-SUFFIX,steamusercontent.com,蒸汽平台'
    - 'DOMAIN,steambroadcast.akamaized.net,蒸汽平台'
    - 'DOMAIN,steamcdn-a.akamaihd.net,蒸汽平台'
    - 'DOMAIN,steamcommunity-a.akamaihd.net,蒸汽平台'
    - 'DOMAIN,steamstore-a.akamaihd.net,蒸汽平台'
    - 'DOMAIN,steamusercontent-a.akamaihd.net,蒸汽平台'
    - 'DOMAIN,steamuserimages-a.akamaihd.net,蒸汽平台'
    - 'DOMAIN-SUFFIX,safebrowsing.urlsec.qq.com,DIRECT'
    - 'DOMAIN,safebrowsing.googleapis.com,DIRECT'
    - 'DOMAIN-SUFFIX,local,DIRECT'
    - 'IP-CIDR,127.0.0.0/8,DIRECT'
    - 'IP-CIDR,172.16.0.0/12,DIRECT'
    - 'IP-CIDR,192.168.0.0/16,DIRECT'
    - 'IP-CIDR,10.0.0.0/8,DIRECT'
    - 'IP-CIDR,17.0.0.0/8,DIRECT'
    - 'IP-CIDR,100.64.0.0/10,DIRECT'
    - 'IP-CIDR,224.0.0.0/4,DIRECT'
    - 'IP-CIDR6,fe80::/10,DIRECT'
    - 'GEOIP,CN,DIRECT'
    - 'MATCH,节点选择'