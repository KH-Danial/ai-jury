#!/usr/bin/env python3
import requests
import base64
import os
import time
import json
import socket
import random
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, List, Set, Tuple, Optional
from urllib.parse import urlparse
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# ============================================================
# لیست لینک‌های جمع‌کننده کانفیگ (کامل، از فایل قبلی شما)
# ============================================================
urls = [
    'https://github.com/ALIILAPRO/v2rayNG-Config/raw/refs/heads/main/server.txt',
    'https://raw.githubusercontent.com/ALIILAPRO/v2rayNG-Config/refs/heads/main/server.txt',
    'https://raw.githubusercontent.com/Epodonios/v2ray-configs/refs/heads/main/Sub1.txt',
    'https://raw.githubusercontent.com/Epodonios/v2ray-configs/refs/heads/main/Sub2.txt',
    'https://raw.githubusercontent.com/Epodonios/v2ray-configs/refs/heads/main/Splitted-By-Protocol/trojan.txt',
    'https://raw.githubusercontent.com/Epodonios/v2ray-configs/refs/heads/main/All_Configs_base64_Sub.txt',
    'https://raw.githubusercontent.com/Epodonios/v2ray-configs/refs/heads/main/All_Configs_Sub.txt',
    'https://raw.githubusercontent.com/mahdibland/ShadowsocksAggregator/master/Eternity',
    'https://raw.githubusercontent.com/mahdibland/V2RayAggregator/master/sub/sub_merge.txt',
    'https://raw.githubusercontent.com/mahdibland/V2RayAggregator/master/sub/splitted/ss.txt',
    'https://raw.githubusercontent.com/roosterkid/openproxylist/refs/heads/main/V2RAY_RAW.txt',
    'https://raw.githubusercontent.com/roosterkid/openproxylist/refs/heads/main/V2RAY_BASE64.txt',
    'https://raw.githubusercontent.com/AvenCores/goida-vpn-configs/refs/heads/main/githubmirror/1.txt',
    'https://raw.githubusercontent.com/AvenCores/goida-vpn-configs/refs/heads/main/githubmirror/2.txt',
    'https://raw.githubusercontent.com/AvenCores/goida-vpn-configs/refs/heads/main/githubmirror/3.txt',
    'https://raw.githubusercontent.com/AvenCores/goida-vpn-configs/refs/heads/main/githubmirror/4.txt',
    'https://raw.githubusercontent.com/AvenCores/goida-vpn-configs/refs/heads/main/githubmirror/5.txt',
    'https://raw.githubusercontent.com/AvenCores/goida-vpn-configs/refs/heads/main/githubmirror/6.txt',
    'https://raw.githubusercontent.com/AvenCores/goida-vpn-configs/refs/heads/main/githubmirror/7.txt',
    'https://raw.githubusercontent.com/AvenCores/goida-vpn-configs/refs/heads/main/githubmirror/8.txt',
    'https://raw.githubusercontent.com/AvenCores/goida-vpn-configs/refs/heads/main/githubmirror/9.txt',
    'https://raw.githubusercontent.com/AvenCores/goida-vpn-configs/refs/heads/main/githubmirror/10.txt',
    'https://raw.githubusercontent.com/Firmfox/proxify/main/v2ray_configs/seperated_by_protocol/shadowsocks.txt',
    'https://raw.githubusercontent.com/F0rc3Run/F0rc3Run/refs/heads/main/splitted-by-protocol/shadowsocks.txt',
    'https://raw.githubusercontent.com/xyfqzy/free-nodes/main/nodes/shadowsocks.txt',
    'https://raw.githubusercontent.com/mehran1404/Sub_Link/refs/heads/main/V2RAY-Sub.txt',
    'https://raw.githubusercontent.com/shabane/kamaji/master/hub/merged.txt',
    'https://raw.githubusercontent.com/wuqb2i4f/xray-config-toolkit/main/output/base64/mix-uri',
    'https://raw.githubusercontent.com/ARMANERGAN/V2RAYCONFIGSPOOL/refs/heads/main/V2RAY_SUB.txt',
    'https://raw.githubusercontent.com/SoliSpirit/v2ray-configs/refs/heads/main/all_configs.txt',
    'https://raw.githubusercontent.com/Kwinshadow/TelegramV2rayCollector/refs/heads/main/sublinks/mix.txt',
    'https://raw.githubusercontent.com/Surfboardv2ray/v2ray-worker-sub/refs/heads/master/providers/providers',
    'https://raw.githubusercontent.com/Surfboardv2ray/v2ray-worker-sub/refs/heads/master/providers/ir',
    'https://raw.githubusercontent.com/Surfboardv2ray/v2ray-worker-sub/refs/heads/master/providers/configshubIR',
    'https://raw.githubusercontent.com/dpangestuw/Free-Proxy/refs/heads/main/All_proxies.txt',
    'https://raw.githubusercontent.com/trio666/proxy-checker/refs/heads/main/all.txt',
    'https://raw.githubusercontent.com/mheidari98/.proxy/refs/heads/main/all',
    'https://raw.githubusercontent.com/Surfboardv2ray/Proxy-sorter/main/submerge/converted.txt',
    'https://raw.githubusercontent.com/LoneKingCode/free-proxy-db/refs/heads/main/proxies/all.txt',
    'https://raw.githubusercontent.com/lagzian/SS-Collector/refs/heads/main/mix.txt',
    'https://raw.githubusercontent.com/acymz/AutoVPN/refs/heads/main/data/V2.txt',
    'https://raw.githubusercontent.com/ermaozi01/free_clash_vpn/refs/heads/main/subscribe/v2ray.txt',
    'https://raw.githubusercontent.com/free18/v2ray/refs/heads/main/v.txt',
    'https://raw.githubusercontent.com/Edudotnexx/multi-proxy-config-fetcher/refs/heads/main/configs/proxy_configs.txt',
    'https://raw.githubusercontent.com/Firmfox/proxify/main/v2ray_configs/seperated_by_protocol/other.txt',
    'https://raw.githubusercontent.com/barry-far/V2ray-Config/refs/heads/main/All_Configs_Sub.txt',
    'https://raw.githubusercontent.com/monosans/proxy-list/refs/heads/main/proxies/all.txt',
    'https://raw.githubusercontent.com/LoneKingCode/free-proxy-db/refs/heads/main/proxies/all.txt',
    'https://raw.githubusercontent.com/iplocate/free-proxy-list/refs/heads/main/all-proxies.txt',
    'https://raw.githubusercontent.com/chengaopan/AutoMergePublicNodes/refs/heads/master/list_raw.txt',
    'https://raw.githubusercontent.com/sakha1370/OpenRay/refs/heads/main/output/all_valid_proxies.txt',
    'https://raw.githubusercontent.com/prxchk/proxy-list/refs/heads/main/all.txt',
    'https://raw.githubusercontent.com/mahsanet/MahsaFreeConfig/refs/heads/main/mci/sub_1.txt',
    'https://raw.githubusercontent.com/mahsanet/MahsaFreeConfig/refs/heads/main/mci/sub_2.txt',
    'https://raw.githubusercontent.com/mahsanet/MahsaFreeConfig/refs/heads/main/mci/sub_3.txt',
    'https://raw.githubusercontent.com/mahsanet/MahsaFreeConfig/refs/heads/main/app/sub.txt',
    'https://raw.githubusercontent.com/mahsanet/MahsaFreeConfig/refs/heads/main/mtn/sub_1.txt',
    'https://raw.githubusercontent.com/mahsanet/MahsaFreeConfig/refs/heads/main/mtn/sub_2.txt',
    'https://raw.githubusercontent.com/mahsanet/MahsaFreeConfig/refs/heads/main/mtn/sub_3.txt',
    'https://raw.githubusercontent.com/mahsanet/MahsaFreeConfig/refs/heads/main/mtn/sub_4.txt',
    'https://raw.githubusercontent.com/yebekhe/vpn-fail/refs/heads/main/sub-link',
    'https://raw.githubusercontent.com/Surfboardv2ray/TGParse/main/splitted/mixed',
    'https://raw.githubusercontent.com/itsyebekhe/PSG/main/lite/subscriptions/xray/normal/mix',
    'https://raw.githubusercontent.com/HosseinKoofi/GO_V2rayCollector/main/mixed_iran.txt',
    'https://raw.githubusercontent.com/arshiacomplus/v2rayExtractor/refs/heads/main/mix/sub.html',
    'https://raw.githubusercontent.com/Rayan-Config/C-Sub/refs/heads/main/configs/proxy.txt',
    'https://raw.githubusercontent.com/mahdibland/ShadowsocksAggregator/master/Eternity.txt',
    'https://raw.githubusercontent.com/Everyday-VPN/Everyday-VPN/main/subscription/main.txt',
    'https://raw.githubusercontent.com/MahsaNetConfigTopic/config/refs/heads/main/xray_final.txt',
    'https://raw.githubusercontent.com/yitong2333/proxy-minging/refs/heads/main/v2ray.txt',
    'https://github.com/LalatinaHub/Mineral/raw/refs/heads/master/result/nodes',
    'https://github.com/4n0nymou3/multi-proxy-config-fetcher/raw/refs/heads/main/configs/proxy_configs.txt',
    'https://github.com/freefq/free/raw/refs/heads/master/v2',
    'https://github.com/MhdiTaheri/V2rayCollector_Py/raw/refs/heads/main/sub/Mix/mix.txt',
    'https://github.com/Pawdroid/Free-servers/raw/refs/heads/main/sub',
    'https://github.com/vxiaov/free_proxies/raw/refs/heads/main/links.txt',
    'https://github.com/Surfboardv2ray/Proxy-sorter/raw/refs/heads/main/submerge/converted.txt',
    'https://github.com/mrvcoder/V2rayCollector/raw/refs/heads/main/ss_iran.txt',
    'https://github.com/MhdiTaheri/V2rayCollector/raw/refs/heads/main/sub/mix',
    'https://github.com/nyeinkokoaung404/V2ray-Configs/raw/refs/heads/main/All_Configs_Sub.txt',
    'https://raw.githubusercontent.com/vsvavan2/vpn-config-rkn/refs/heads/main/output/WHITE_CIDR_RU_checked_working.txt',
    'https://raw.githubusercontent.com/vsvavan2/vpn-config-rkn/refs/heads/main/output/WHITE_Reality_Mobile_2_working.txt',
    'https://raw.githubusercontent.com/SoliSpirit/v2ray-configs/refs/heads/main/Protocols/vless.txt',
    'https://raw.githubusercontent.com/SoliSpirit/v2ray-configs/refs/heads/main/Protocols/ss.txt',
    'https://raw.githubusercontent.com/AvenCores/goida-vpn-configs/refs/heads/main/githubmirror/1.txt',
    'https://raw.githubusercontent.com/AvenCores/goida-vpn-configs/refs/heads/main/githubmirror/2.txt',
    'https://raw.githubusercontent.com/barry-far/V2ray-config/main/Sub4.txt',
    'https://raw.githubusercontent.com/barry-far/V2ray-config/main/Sub6.txt',
    'https://raw.githubusercontent.com/barry-far/V2ray-config/main/Splitted-By-Protocol/trojan.txt',
    'https://raw.githubusercontent.com/barry-far/V2ray-config/main/Splitted-By-Protocol/ss.txt',
    'https://raw.githubusercontent.com/Surfboardv2ray/TGParse/main/python/hysteria2',
    'https://raw.githubusercontent.com/Surfboardv2ray/TGParse/main/splitted/trojan',
    'https://raw.githubusercontent.com/Maskkost93/kizyak-vpn-4.0/refs/heads/main/kizyakbeta6.txt',
    'https://raw.githubusercontent.com/Maskkost93/kizyak-vpn-4.0/refs/heads/main/kizyakbeta6BL.txt',
    'https://raw.githubusercontent.com/prominbro/KfWL/refs/heads/main/KfWL.txt',
    'https://raw.githubusercontent.com/prominbro/KfWL/refs/heads/main/KfWLcheck.txt',
    'https://raw.githubusercontent.com/hamedcode/port-based-v2ray-configs/main/sub/port_2053.txt',
    'https://raw.githubusercontent.com/hamedcode/port-based-v2ray-configs/main/sub/port_8443.txt',
    'https://raw.githubusercontent.com/hamedcode/port-based-v2ray-configs/main/sub/vless.txt',
    'https://raw.githubusercontent.com/Firmfox/Proxify/refs/heads/main/v2ray_configs/mixed/subscription-1.txt',
    'https://raw.githubusercontent.com/Firmfox/Proxify/refs/heads/main/v2ray_configs/mixed/subscription-2.txt',
    'https://raw.githubusercontent.com/ssavnayt/AWCFG-CONFIG-LIST/refs/heads/main/Configs-all-country.txt',
    'https://raw.githubusercontent.com/ssavnayt/AWCFG-CONFIG-LIST/refs/heads/main/Configs-AUTO.txt',
    'https://raw.githubusercontent.com/ksenkovsolo/HardVPN-bypass-WhiteLists-/refs/heads/main/vpn-lte/subscriptions/1sub.txt',
    'https://raw.githubusercontent.com/ksenkovsolo/HardVPN-bypass-WhiteLists-/refs/heads/main/vpn-lte/good_keys.txt',
    'https://raw.githubusercontent.com/ksenkovsolo/HardVPN-bypass-WhiteLists-/refs/heads/main/vpn-lte/best_keys.txt',
    'https://raw.githubusercontent.com/Kirillo4ka/eavevpn-configs/refs/heads/main/BLACK_SS%2BAll_RUS.txt',
    'https://raw.githubusercontent.com/Kirillo4ka/eavevpn-configs/refs/heads/main/Vless-Reality-White-Lists-Rus-Mobile.txt',
    'https://raw.githubusercontent.com/Kirillo4ka/eavevpn-configs/refs/heads/main/WHITE-CIDR-RU-checked.txt',
    'https://raw.githubusercontent.com/Kirillo4ka/eavevpn-configs/refs/heads/main/WHITE-SNI-RU-all.txt',
    'https://raw.githubusercontent.com/Kirillo4ka/eavevpn-configs/refs/heads/main/BLACK_VLESS_RUS.txt',
    'https://raw.githubusercontent.com/Kirillo4ka/eavevpn-configs/refs/heads/main/BLACK_VLESS_RUS_mobile.txt',
    'https://raw.githubusercontent.com/igareck/vpn-configs-for-russia/refs/heads/main/WHITE-CIDR-RU-all.txt',
    'https://raw.githubusercontent.com/igareck/vpn-configs-for-russia/main/WHITE-CIDR-RU-checked.txt',
    'https://raw.githubusercontent.com/igareck/vpn-configs-for-russia/main/WHITE-SNI-RU-all.txt',
    'https://raw.githubusercontent.com/igareck/vpn-configs-for-russia/main/BLACK_VLESS_RUS.txt',
    'https://raw.githubusercontent.com/kort0881/vpn-vless-configs-russia/refs/heads/main/subscriptions/all.part1.txt',
    'https://raw.githubusercontent.com/kort0881/vpn-vless-configs-russia/refs/heads/main/subscriptions/all.txt',
    'https://raw.githubusercontent.com/kort0881/sbornik-vless/refs/heads/main/subs/ss_001.txt',
    'https://raw.githubusercontent.com/kort0881/sbornik-vless/refs/heads/main/subs/ss_002.txt',
    'https://raw.githubusercontent.com/kort0881/sbornik-vless/refs/heads/main/subs/hysteria2_001.txt',
    'https://raw.githubusercontent.com/whoahaow/rjsxrd/refs/heads/main/githubmirror/split-by-protocols/tuic.txt',
    'https://raw.githubusercontent.com/whoahaow/rjsxrd/refs/heads/main/githubmirror/split-by-protocols/hy2-secure.txt',
    'https://raw.githubusercontent.com/whoahaow/rjsxrd/refs/heads/main/githubmirror/split-by-protocols/hysteria-secure.txt',
    'https://raw.githubusercontent.com/whoahaow/rjsxrd/refs/heads/main/githubmirror/split-by-protocols/hysteria2-secure.txt',
    'https://raw.githubusercontent.com/whoahaow/rjsxrd/refs/heads/main/githubmirror/bypass/bypass-all.txt',
    'https://raw.githubusercontent.com/whoahaow/rjsxrd/refs/heads/main/githubmirror/bypass-unsecure/bypass-unsecure-2.txt',
    'https://raw.githubusercontent.com/whoahaow/rjsxrd/refs/heads/main/githubmirror/bypass-unsecure/bypass-unsecure-3.txt',
    'https://raw.githubusercontent.com/whoahaow/rjsxrd/refs/heads/main/githubmirror/bypass-unsecure/bypass-unsecure-4.txt',
    'https://raw.githubusercontent.com/whoahaow/rjsxrd/refs/heads/main/githubmirror/bypass-unsecure/bypass-unsecure-5.txt',
    'https://raw.githubusercontent.com/whoahaow/rjsxrd/refs/heads/main/githubmirror/bypass-unsecure/bypass-unsecure-6.txt',
    'https://raw.githubusercontent.com/whoahaow/rjsxrd/refs/heads/main/githubmirror/bypass-unsecure/bypass-unsecure-7.txt',
    'https://raw.githubusercontent.com/whoahaow/rjsxrd/refs/heads/main/githubmirror/bypass-unsecure/bypass-unsecure-9.txt',
    'https://raw.githubusercontent.com/whoahaow/rjsxrd/refs/heads/main/githubmirror/bypass-unsecure/bypass-unsecure-10.txt',
    'https://raw.githubusercontent.com/whoahaow/rjsxrd/refs/heads/main/githubmirror/bypass-unsecure/bypass-unsecure-12.txt',
    'https://raw.githubusercontent.com/whoahaow/rjsxrd/refs/heads/main/githubmirror/bypass-unsecure/bypass-unsecure-13.txt',
    'https://raw.githubusercontent.com/whoahaow/rjsxrd/refs/heads/main/githubmirror/bypass-unsecure/bypass-unsecure-15.txt',
    'https://raw.githubusercontent.com/whoahaow/rjsxrd/refs/heads/main/githubmirror/bypass-unsecure/bypass-unsecure-16.txt',
    'https://raw.githubusercontent.com/whoahaow/rjsxrd/refs/heads/main/githubmirror/bypass-unsecure/bypass-unsecure-all.txt',
    'https://raw.githubusercontent.com/zieng2/wl/refs/heads/main/vless_universal.txt',
    'https://raw.githubusercontent.com/ALIILAPRO/v2rayNG-Config/main/sub.txt',
    'https://raw.githubusercontent.com/mfuu/v2ray/master/v2ray',
    'https://raw.githubusercontent.com/ts-sf/fly/main/v2',
    'https://raw.githubusercontent.com/sevcator/5ubscrpt10n/main/protocols/vl.txt',
    'https://raw.githubusercontent.com/yitong2333/proxy-minging/refs/heads/main/v2ray.txt',
    'https://raw.githubusercontent.com/Hidashimora/free-vpn-anti-rkn/main/configs/1.2.txt',
    'https://raw.githubusercontent.com/miladtahanian/V2RayCFGDumper/refs/heads/main/sub.txt',
    'https://raw.githubusercontent.com/roosterkid/openproxylist/main/V2RAY_RAW.txt',
    'https://raw.githubusercontent.com/Hidashimora/free-vpn-anti-rkn/main/configs/1.txt',
    'https://raw.githubusercontent.com/CidVpn/cid-vpn-config/refs/heads/main/general.txt',
    'https://raw.githubusercontent.com/mohamadfg-dev/telegram-v2ray-configs-collector/refs/heads/main/category/vless.txt',
    'https://raw.githubusercontent.com/youfoundamin/V2rayCollector/main/mixed_iran.txt',
    'https://raw.githubusercontent.com/nikita29a/FreeProxyList/refs/heads/main/mirror/26.txt',
    'https://raw.githubusercontent.com/R3ZARAHIMI/tg-v2ray-configs-every2h/refs/heads/main/conf-week.txt',
    'https://raw.githubusercontent.com/FSystem88/vless-keys/refs/heads/main/keys.txt',
    'https://raw.githubusercontent.com/nikita29a/FreeProxyList/refs/heads/main/mirror/26.txt',
    'https://raw.githubusercontent.com/shabane/kamaji/master/hub/merged.txt',
    'https://raw.githubusercontent.com/wuqb2i4f/xray-config-toolkit/main/output/base64/mix-uri',
    'https://raw.githubusercontent.com/nikita29a/FreeProxyList/refs/heads/main/mirror/23.txt',
    'https://raw.githubusercontent.com/igareck/vpn-configs-for-russia/refs/heads/main/BLACK_VLESS_RUS_mobile.txt',
    'https://raw.githubusercontent.com/V2RayRoot/V2RayConfig/refs/heads/main/Config/vless.txt',
    'https://raw.githubusercontent.com/Epodonios/v2ray-configs/refs/heads/main/All_Configs_Sub.txt',
    'https://raw.githubusercontent.com/yitong2333/proxy-minging/refs/heads/main/v2ray.txt',
    'https://raw.githubusercontent.com/acymz/AutoVPN/refs/heads/main/data/V2.txt',
    'https://raw.githubusercontent.com/miladtahanian/V2RayCFGDumper/refs/heads/main/sub.txt',
    'https://raw.githubusercontent.com/Temnuk/naabuzil/refs/heads/main/wifi',
    'https://raw.githubusercontent.com/CidVpn/cid-vpn-config/refs/heads/main/general.txt',
    'https://raw.githubusercontent.com/mohamadfg-dev/telegram-v2ray-configs-collector/refs/heads/main/category/vless.txt',
    'https://raw.githubusercontent.com/mheidari98/.proxy/refs/heads/main/vless',
    'https://raw.githubusercontent.com/youfoundamin/V2rayCollector/main/mixed_iran.txt',
    'https://raw.githubusercontent.com/expressalaki/ExpressVPN/refs/heads/main/configs3.txt',
    'https://raw.githubusercontent.com/MahsaNetConfigTopic/config/refs/heads/main/xray_final.txt',
    'https://raw.githubusercontent.com/miladtahanian/Config-Collector/refs/heads/main/mixed_iran.txt',
    'https://raw.githubusercontent.com/Pawdroid/Free-servers/refs/heads/main/sub',
    'https://raw.githubusercontent.com/shabane/kamaji/master/hub/merged.txt',
    'https://raw.githubusercontent.com/Maskkost93/kizyak-vpn-4.0/refs/heads/main/kizyakbeta7.txt',
    'https://raw.githubusercontent.com/vsvavan2/vpn-config-rkn/refs/heads/main/output/WHITE_CIDR_RU_all_working.txt',
    'https://raw.githubusercontent.com/opti4riponty-arch/VLESS-Co/refs/heads/main/VLESS%20%26%20Co',
    'https://raw.githubusercontent.com/luxxuria/harvester/refs/heads/main/non_ru.txt',
    'https://raw.githubusercontent.com/Temnuk/naabuzil/refs/heads/main/wifi',
    'https://raw.githubusercontent.com/V2RayRoot/V2RayConfig/refs/heads/main/Config/vless.txt',
    'https://raw.githubusercontent.com/zieng2/wl/refs/heads/main/vless_universal.txt',
    'https://raw.githubusercontent.com/EtoNeYaProject/etoneyaproject.github.io/refs/heads/main/2',
    'https://raw.githubusercontent.com/ByeWhiteLists/ByeWhiteLists2/refs/heads/main/ByeWhiteLists2.txt',
    'https://raw.githubusercontent.com/Hidashimora/free-vpn-anti-rkn/main/configs/31.txt',
    'https://raw.githubusercontent.com/AvenCores/goida-vpn-configs/refs/heads/main/githubmirror/26.txt',
    'https://raw.githubusercontent.com/Temnuk/naabuzil/refs/heads/main/whitelist_full',
    'https://raw.githubusercontent.com/prominbro/sub/refs/heads/main/212.txt',
    'https://raw.githubusercontent.com/tankist939-afk/Obhod-WL/refs/heads/main/Obhod%20WL',
    'https://raw.githubusercontent.com/Vovo4ka000/V4kVPN/main/v4kVPN.txt',
    'https://raw.githubusercontent.com/Ilyacom4ik/free-v2ray-2026/refs/heads/main/subscriptions/FreeCFGHub1.txt',
    'https://raw.githubusercontent.com/HikaruApps/WhiteLattice/refs/heads/main/subscriptions/config.txt',
    'https://raw.githubusercontent.com/F0rc3Run/F0rc3Run/main/splitted-by-protocol/vless.txt',
    'https://raw.githubusercontent.com/mshojaei77/v2rayAuto/refs/heads/main/telegram/popular_channels_1',
    'https://raw.githubusercontent.com/MatinGhanbari/v2ray-configs/main/subscriptions/v2ray/subs/sub1.txt',
    'https://raw.githubusercontent.com/barry-far/V2ray-config/main/Splitted-By-Protocol/vless.txt',
    'https://raw.githubusercontent.com/ksenkovsolo/HardVPN-bypass-WhiteLists-/refs/heads/main/vpn-lte/WHITELIST-ALL.txt',
    'https://raw.githubusercontent.com/Danialsamadi/v2go/refs/heads/main/AllConfigsSub.txt',
    'https://raw.githubusercontent.com/mbelspb-gif/ffsfsfssdf/refs/heads/main/TG-swordware',
    'https://raw.githubusercontent.com/V2RayRoot/V2Root-ConfigPilot/refs/heads/main/output/BestConfigs.txt',
    'https://raw.githubusercontent.com/sakha1370/OpenRay/refs/heads/main/output/all_valid_proxies.txt',
    'https://raw.githubusercontent.com/mmaksim9191/my-vpn-configs/refs/heads/main/configs/mobile-whitelist-1.txt',
    'https://raw.githubusercontent.com/EtoNeYaProject/etoneyaproject.github.io/refs/heads/main/1',
    'https://raw.githubusercontent.com/tankist939-afk/Obhod-WL/refs/heads/main/Obhod%20WL',
    'https://raw.githubusercontent.com/LimeHi/LimeVPNGenerator/main/Keys.txt',
    'https://raw.githubusercontent.com/ByeWhiteLists/ByeWhiteLists2/refs/heads/main/ByeWhiteLists2.txt',
    'https://raw.githubusercontent.com/Rayan-Config/C-Sub/refs/heads/main/configs/proxy.txt',
    'https://raw.githubusercontent.com/amindzlvess-boop/SlashVPN/refs/heads/main/vpn.txt',
    'https://raw.githubusercontent.com/sevcator/5ubscrpt10n/main/protocols/vl.txt',
    'https://raw.githubusercontent.com/sevcator/5ubscrpt10n/main/mini/m1n1-5ub-1.txt',
    'https://raw.githubusercontent.com/sevcator/5ubscrpt10n/main/mini/m1n1-5ub-2.txt',
    'https://raw.githubusercontent.com/sevcator/5ubscrpt10n/main/mini/m1n1-5ub-3.txt',
    'https://raw.githubusercontent.com/sevcator/5ubscrpt10n/main/mini/m1n1-5ub-4.txt',
    'https://raw.githubusercontent.com/sevcator/5ubscrpt10n/main/mini/m1n1-5ub-5.txt',
    'https://raw.githubusercontent.com/sevcator/5ubscrpt10n/main/mini/m1n1-5ub-6.txt',
    'https://raw.githubusercontent.com/sevcator/5ubscrpt10n/main/mini/m1n1-5ub-7.txt',
    'https://raw.githubusercontent.com/sevcator/5ubscrpt10n/main/mini/m1n1-5ub-8.txt',
    'https://raw.githubusercontent.com/sevcator/5ubscrpt10n/main/mini/m1n1-5ub-9.txt',
    'https://raw.githubusercontent.com/sevcator/5ubscrpt10n/main/mini/m1n1-5ub-10.txt',
    'https://raw.githubusercontent.com/sevcator/5ubscrpt10n/main/mini/m1n1-5ub-11.txt',
    'https://raw.githubusercontent.com/sevcator/5ubscrpt10n/main/mini/m1n1-5ub-12.txt',
    'https://raw.githubusercontent.com/sevcator/5ubscrpt10n/main/mini/m1n1-5ub-13.txt',
    'https://raw.githubusercontent.com/sevcator/5ubscrpt10n/main/mini/m1n1-5ub-15.txt',
    'https://raw.githubusercontent.com/sevcator/5ubscrpt10n/main/mini/m1n1-5ub-16.txt',
    'https://raw.githubusercontent.com/sevcator/5ubscrpt10n/main/mini/m1n1-5ub-17.txt',
    'https://raw.githubusercontent.com/sevcator/5ubscrpt10n/main/mini/m1n1-5ub-18.txt',
    'https://raw.githubusercontent.com/sevcator/5ubscrpt10n/main/mini/m1n1-5ub-21.txt',
    'https://raw.githubusercontent.com/sevcator/5ubscrpt10n/main/mini/m1n1-5ub-22.txt',
    'https://raw.githubusercontent.com/sevcator/5ubscrpt10n/main/mini/m1n1-5ub-23.txt',
    'https://raw.githubusercontent.com/sevcator/5ubscrpt10n/main/mini/m1n1-5ub-24.txt',
    'https://raw.githubusercontent.com/sevcator/5ubscrpt10n/main/mini/m1n1-5ub-33.txt',
    'https://raw.githubusercontent.com/sevcator/5ubscrpt10n/main/mini/m1n1-5ub-35.txt',
    'https://raw.githubusercontent.com/AvenCores/goida-vpn-configs/refs/heads/main/githubmirror/4.txt',
    'https://raw.githubusercontent.com/AvenCores/goida-vpn-configs/refs/heads/main/githubmirror/6.txt',
    'https://raw.githubusercontent.com/AvenCores/goida-vpn-configs/refs/heads/main/githubmirror/7.txt',
    'https://raw.githubusercontent.com/AvenCores/goida-vpn-configs/refs/heads/main/githubmirror/8.txt',
    'https://raw.githubusercontent.com/AvenCores/goida-vpn-configs/refs/heads/main/githubmirror/9.txt',
    'https://raw.githubusercontent.com/AvenCores/goida-vpn-configs/refs/heads/main/githubmirror/10.txt',
    'https://raw.githubusercontent.com/AvenCores/goida-vpn-configs/refs/heads/main/githubmirror/12.txt',
    'https://raw.githubusercontent.com/AvenCores/goida-vpn-configs/refs/heads/main/githubmirror/14.txt',
    'https://raw.githubusercontent.com/AvenCores/goida-vpn-configs/refs/heads/main/githubmirror/15.txt',
    'https://raw.githubusercontent.com/AvenCores/goida-vpn-configs/refs/heads/main/githubmirror/17.txt',
    'https://raw.githubusercontent.com/AvenCores/goida-vpn-configs/refs/heads/main/githubmirror/18.txt',
    'https://raw.githubusercontent.com/AvenCores/goida-vpn-configs/refs/heads/main/githubmirror/19.txt',
    'https://raw.githubusercontent.com/AvenCores/goida-vpn-configs/refs/heads/main/githubmirror/21.txt',
    'https://raw.githubusercontent.com/AvenCores/goida-vpn-configs/refs/heads/main/githubmirror/24.txt',
    'https://raw.githubusercontent.com/AvenCores/goida-vpn-configs/refs/heads/main/githubmirror/25.txt',
    'https://raw.githubusercontent.com/zieng2/wl/main/vless_universal.txt',
    'https://raw.githubusercontent.com/SoliSpirit/v2ray-configs/refs/heads/main/all_configs.txt',
    'https://raw.githubusercontent.com/SilentGhostCodes/WhiteListVpn/refs/heads/main/Whitelist.txt',
    'https://raw.githubusercontent.com/MatinGhanbari/v2ray-configs/25bb2a9ec2721b62dd3ce3e5b0e12fbacf041f67/subscriptions/v2ray/subs/sub10.txt',
    'https://raw.githubusercontent.com/nikita29a/FreeProxyList/refs/heads/main/mirror/25.txt',
    'https://raw.githubusercontent.com/igareck/vpn-configs-for-russia/refs/heads/main/WHITE-CIDR-RU-checked.txt',
    'https://raw.githubusercontent.com/SoliSpirit/v2ray-configs/refs/heads/main/Protocols/trojan.txt',
    'https://raw.githubusercontent.com/MhdiTaheri/V2rayCollector/refs/heads/main/sub/trojan',
    'https://raw.githubusercontent.com/Argh94/V2RayAutoConfig/refs/heads/main/configs/Hysteria2.txt',
    'https://raw.githubusercontent.com/Farid-Karimi/Config-Collector/main/vless_iran.txt',
    'https://raw.githubusercontent.com/hamedp-71/Sub_Checker_Creator/refs/heads/main/final.txt',
    'https://raw.githubusercontent.com/MatinGhanbari/v2ray-configs/main/subscriptions/filtered/subs/vless.txt',
    'https://raw.githubusercontent.com/Kwinshadow/TelegramV2rayCollector/main/sublinks/vless.txt',
    'https://raw.githubusercontent.com/Kwinshadow/TelegramV2rayCollector/main/sublinks/trojan.txt',
    'https://raw.githubusercontent.com/Epodonios/v2ray-configs/refs/heads/main/Sub1.txt',
    'https://raw.githubusercontent.com/roosterkid/openproxylist/main/V2RAY_RAW.txt',
    'https://raw.githubusercontent.com/Epodonios/v2ray-configs/main/All_Configs_Sub.txt',
    'https://raw.githubusercontent.com/zieng2/wl/main/vless_lite.txt',
    'https://raw.githubusercontent.com/Farid-Karimi/Config-Collector/main/trojan_iran.txt',
    'https://raw.githubusercontent.com/Epodonios/v2ray-configs/refs/heads/main/Sub47.txt',
    'https://raw.githubusercontent.com/Epodonios/v2ray-configs/refs/heads/main/Sub48.txt',
    'https://raw.githubusercontent.com/Epodonios/v2ray-configs/refs/heads/main/Sub49.txt',
    'https://raw.githubusercontent.com/Epodonios/v2ray-configs/refs/heads/main/Sub50.txt',
    'https://raw.githubusercontent.com/Epodonios/v2ray-configs/refs/heads/main/Sub52.txt',
    'https://raw.githubusercontent.com/Epodonios/v2ray-configs/refs/heads/main/Sub53.txt',
    'https://raw.githubusercontent.com/igareck/vpn-configs-for-russia/refs/heads/main/Vless-Reality-White-Lists-Rus-Mobile.txt',
    'https://raw.githubusercontent.com/igareck/vpn-configs-for-russia/refs/heads/main/BLACK_SS%2BAll_RUS.txt',
    'https://raw.githubusercontent.com/igareck/vpn-configs-for-russia/refs/heads/main/BLACK_VLESS_RUS.txt',
    'https://raw.githubusercontent.com/kort0881/vpn-vless-configs-russia/refs/heads/main/githubmirror/new/all_new.txt',
    'https://raw.githubusercontent.com/crackbest/V2ray-Config/refs/heads/main/config.txt',
    'https://raw.githubusercontent.com/AvenCores/goida-vpn-configs/refs/heads/main/githubmirror/26.txt',
    'https://raw.githubusercontent.com/EtoNeYaProject/etoneyaproject.github.io/refs/heads/main/other',
    'https://raw.githubusercontent.com/igareck/vpn-configs-for-russia/main/Vless-Reality-White-Lists-Rus-Mobile-2.txt',
    'https://raw.githubusercontent.com/igareck/vpn-configs-for-russia/main/BLACK_VLESS_RUS_mobile.txt',
    'https://raw.githubusercontent.com/F0rc3Run/F0rc3Run/refs/heads/main/Best-Results/proxies.txt',
    'https://raw.githubusercontent.com/kemfie/whitelistrussua/main/RussiaCIDR.txt',
    'https://raw.githubusercontent.com/SoliSpirit/v2ray-configs/refs/heads/main/Subscriptions/Sub1.txt',
    'https://raw.githubusercontent.com/RKPchannel/RKP_bypass_configs/refs/heads/main/configs/url_work.txt',
    'https://raw.githubusercontent.com/whoahaow/rjsxrd/refs/heads/main/githubmirror/bypass/bypass-1.txt',
    'https://raw.githubusercontent.com/whoahaow/rjsxrd/refs/heads/main/githubmirror/bypass/bypass-2.txt',
    'https://raw.githubusercontent.com/whoahaow/rjsxrd/refs/heads/main/githubmirror/bypass/bypass-3.txt',
    'https://raw.githubusercontent.com/whoahaow/rjsxrd/refs/heads/main/githubmirror/bypass/bypass-4.txt',
    'https://raw.githubusercontent.com/whoahaow/rjsxrd/refs/heads/main/githubmirror/bypass/bypass-5.txt',
    'https://raw.githubusercontent.com/whoahaow/rjsxrd/refs/heads/main/githubmirror/bypass/bypass-6.txt',
    'https://raw.githubusercontent.com/ALIILAPRO/v2rayNG-Config/main/server.txt',
    'https://raw.githubusercontent.com/AB-84-AB/Free-Shadowsocks/refs/heads/main/Telegram-id-AB_841',
    'https://raw.githubusercontent.com/47AgEnT-47/vpn-configs/refs/heads/main/configs.txt',
    'https://gitverse.ru/api/repos/bywarm/rser/raw/branch/master/wl.txt',
    'https://gitverse.ru/api/repos/kfwlru/sub/raw/branch/main/212.txt',
    'https://gitverse.ru/api/repos/RUVIPIEN/russian-white-bolt/raw/branch/master/VPNMIRRORS/nekobox/Alley_Config_1_d0212d.txt',
    'https://gitverse.ru/api/repos/ru-wbl/wl/raw/branch/master/Igareck/WL-CIDR-RU-Checked.txt',
    'https://gitverse.ru/api/repos/ru-wbl/wl/raw/branch/master/Igareck/WL-RU-Mobile.txt',
    'https://gitverse.ru/api/repos/ru-wbl/wl/raw/branch/master/RkpVPN/RKP_work.txt',
    'https://gitverse.ru/api/repos/ru-wbl/wl/raw/branch/master/EtoNeYa/EtoNeYa_wl.txt',
    'https://gitverse.ru/api/repos/RUVIPIEN/russian-white-bolt/raw/branch/master/VPNMIRRORS/nekobox/ByWarm_Merged_b37672.txt',
    'https://gitverse.ru/api/repos/RUVIPIEN/russian-white-bolt/raw/branch/master/VPNMIRRORS/nekobox/ByWarm_Selected_6ac883.txt',
    'https://gitverse.ru/api/repos/RUVIPIEN/russian-white-bolt/raw/branch/master/VPNMIRRORS/nekobox/ByWarm_WL_db4c3f.txt',
    'https://gitverse.ru/api/repos/RUVIPIEN/russian-white-bolt/raw/branch/master/VPNMIRRORS/nekobox/ByeWhiteLists_2_fda813.txt',
    'https://gitverse.ru/api/repos/RUVIPIEN/russian-white-bolt/raw/branch/master/VPNMIRRORS/v2ray/Bypass_Config_7_d33b54.txt',
    'https://gitverse.ru/api/repos/RUVIPIEN/russian-white-bolt/raw/branch/master/VPNMIRRORS/happ/SER38_Happ_Sub1_ddd131.txt',
    'https://gitverse.ru/api/repos/cid-uskoritel/cid-white/raw/branch/master/whitelist.txt',
    'https://gitverse.ru/api/repos/RUVIPIEN/russian-white-bolt/raw/branch/master/VPNMIRRORS/nekobox/Alley_Config_1_d0212d.txt',
    'https://gitverse.ru/api/repos/RUVIPIEN/russian-white-bolt/raw/branch/master/VPNMIRRORS/nekobox/Alley_Config_2_862576.txt',
    'https://gitverse.ru/api/repos/RUVIPIEN/russian-white-bolt/raw/branch/master/VPNMIRRORS/nekobox/ByWarm_Merged_b37672.txt',
    'https://gitverse.ru/api/repos/RUVIPIEN/russian-white-bolt/raw/branch/master/VPNMIRRORS/nekobox/ByWarm_Selected_6ac883.txt',
    'https://gitverse.ru/api/repos/RUVIPIEN/russian-white-bolt/raw/branch/master/VPNMIRRORS/nekobox/ByWarm_WL_db4c3f.txt',
    'https://gitverse.ru/api/repos/RUVIPIEN/russian-white-bolt/raw/branch/master/VPNMIRRORS/nekobox/ByeWhiteLists_2_fda813.txt',
    'https://gitverse.ru/api/repos/RUVIPIEN/russian-white-bolt/raw/branch/master/VPNMIRRORS/nekobox/CID_VPN_General_5d53c1.txt',
    'https://gitverse.ru/api/repos/RUVIPIEN/russian-white-bolt/raw/branch/master/VPNMIRRORS/nekobox/CID_VPN_General_c34df6.txt',
    'https://gitverse.ru/api/repos/RUVIPIEN/russian-white-bolt/raw/branch/master/VPNMIRRORS/nekobox/CID_White_List_d3eab4.txt',
    'https://gitverse.ru/api/repos/RUVIPIEN/russian-white-bolt/raw/branch/master/VPNMIRRORS/nekobox/EtoNeYa_CDN_1_67cece.txt',
    'https://gitverse.ru/api/repos/RUVIPIEN/russian-white-bolt/raw/branch/master/VPNMIRRORS/nekobox/EtoNeYa_Raw_1_57f5f4.txt',
    'https://gitverse.ru/api/repos/RUVIPIEN/russian-white-bolt/raw/branch/master/VPNMIRRORS/nekobox/EtoNeYa_Raw_2_67857e.txt',
    'https://gitverse.ru/api/repos/RUVIPIEN/russian-white-bolt/raw/branch/master/VPNMIRRORS/nekobox/GPU_Cloud_Merged_bbadbd.txt',
    'https://gitverse.ru/api/repos/RUVIPIEN/russian-white-bolt/raw/branch/master/VPNMIRRORS/nekobox/Kirya_White_Lists_25_3d42d7.txt',
    'https://gitverse.ru/api/repos/RUVIPIEN/russian-white-bolt/raw/branch/master/VPNMIRRORS/nekobox/Kirya_White_Lists_25_7c3d65.txt',
    'https://gitverse.ru/api/repos/RUVIPIEN/russian-white-bolt/raw/branch/master/VPNMIRRORS/nekobox/NowMeow_Whitelist_4a7181.txt',
    'https://gitverse.ru/api/repos/RUVIPIEN/russian-white-bolt/raw/branch/master/VPNMIRRORS/nekobox/OBWL_Sub_157838.txt',
    'https://gitverse.ru/api/repos/RUVIPIEN/russian-white-bolt/raw/branch/master/VPNMIRRORS/nekobox/SilentGhost_Whitelist_1_cd7096.txt',
    'https://gitverse.ru/api/repos/RUVIPIEN/russian-white-bolt/raw/branch/master/VPNMIRRORS/nekobox/SilentGhost_Whitelist_2_3f826f.txt',
    'https://gitverse.ru/api/repos/RUVIPIEN/russian-white-bolt/raw/branch/master/VPNMIRRORS/nekobox/Subros_Tunnel_WL_8186d5.txt',
    'https://gitverse.ru/api/repos/RUVIPIEN/russian-white-bolt/raw/branch/master/VPNMIRRORS/nekobox/WHITE_CIDR_RU_All_234b34.txt',
    'https://gitverse.ru/api/repos/RUVIPIEN/russian-white-bolt/raw/branch/master/VPNMIRRORS/nekobox/WHITE_CIDR_RU_All_611028.txt',
    'https://gitverse.ru/api/repos/RUVIPIEN/russian-white-bolt/raw/branch/master/VPNMIRRORS/nekobox/WHITE_CIDR_RU_Checked_982a29.txt',
    'https://gitverse.ru/api/repos/RUVIPIEN/russian-white-bolt/raw/branch/master/VPNMIRRORS/nekobox/WHITE_CIDR_RU_Checked_d94b99.txt',
    'https://gitverse.ru/api/repos/RUVIPIEN/russian-white-bolt/raw/branch/master/VPNMIRRORS/nekobox/WHITE_SNI_RU_All_2b3f49.txt',
    'https://gitverse.ru/api/repos/RUVIPIEN/russian-white-bolt/raw/branch/master/VPNMIRRORS/nekobox/WHITE_SNI_RU_All_dd9b8c.txt',
    'https://gitverse.ru/api/repos/RUVIPIEN/russian-white-bolt/raw/branch/master/VPNMIRRORS/v2ray/BLACK_SS_All_316a8b.txt',
    'https://gitverse.ru/api/repos/RUVIPIEN/russian-white-bolt/raw/branch/master/VPNMIRRORS/v2ray/BLACK_SS_All_44fad8.txt',
    'https://gitverse.ru/api/repos/RUVIPIEN/russian-white-bolt/raw/branch/master/VPNMIRRORS/v2ray/BLACK_SS_All_f5e486.txt',
    'https://gitverse.ru/api/repos/RUVIPIEN/russian-white-bolt/raw/branch/master/VPNMIRRORS/v2ray/BLACK_VLESS_RUS_11add6.txt',
    'https://gitverse.ru/api/repos/RUVIPIEN/russian-white-bolt/raw/branch/master/VPNMIRRORS/v2ray/BLACK_VLESS_RUS_b2debe.txt',
    'https://gitverse.ru/api/repos/RUVIPIEN/russian-white-bolt/raw/branch/master/VPNMIRRORS/v2ray/Bypass_Config_7_93ced8.txt',
    'https://gitverse.ru/api/repos/RUVIPIEN/russian-white-bolt/raw/branch/master/VPNMIRRORS/v2ray/Bypass_Config_7_d33b54.txt',
    'https://gitverse.ru/api/repos/RUVIPIEN/russian-white-bolt/raw/branch/master/VPNMIRRORS/v2ray/Goida_Config_1_2753cf.txt',
    'https://gitverse.ru/api/repos/RUVIPIEN/russian-white-bolt/raw/branch/master/VPNMIRRORS/v2ray/Goida_Config_1_f7c635.txt',
    'https://gitverse.ru/api/repos/RUVIPIEN/russian-white-bolt/raw/branch/master/VPNMIRRORS/v2ray/Goida_Config_26_9d0474.txt',
    'https://gitverse.ru/api/repos/RUVIPIEN/russian-white-bolt/raw/branch/master/VPNMIRRORS/v2ray/Goida_Config_3_b4689a.txt',
    'https://gitverse.ru/api/repos/RUVIPIEN/russian-white-bolt/raw/branch/master/VPNMIRRORS/v2ray/Goida_Config_3_f64e4d.txt',
    'https://gitverse.ru/api/repos/RUVIPIEN/russian-white-bolt/raw/branch/master/VPNMIRRORS/v2ray/Kort_SS_Clean_2a8980.txt',
    'https://gitverse.ru/api/repos/RUVIPIEN/russian-white-bolt/raw/branch/master/VPNMIRRORS/v2ray/Kort_Trojan_Clean_f30cdf.txt',
    'https://gitverse.ru/api/repos/RUVIPIEN/russian-white-bolt/raw/branch/master/VPNMIRRORS/v2ray/Kort_VLESS_Clean_fa7d47.txt',
    'https://gitverse.ru/api/repos/RUVIPIEN/russian-white-bolt/raw/branch/master/VPNMIRRORS/v2ray/Kort_VMess_Clean_94367a.txt',
    'https://gitverse.ru/api/repos/RUVIPIEN/russian-white-bolt/raw/branch/master/VPNMIRRORS/v2ray/MahsaNet_Xray_Final_0c54c3.txt',
    'https://gitverse.ru/api/repos/RUVIPIEN/russian-white-bolt/raw/branch/master/VPNMIRRORS/v2ray/MahsaNet_Xray_Final_1f5ce9.txt',
    'https://gitverse.ru/api/repos/RUVIPIEN/russian-white-bolt/raw/branch/master/VPNMIRRORS/v2ray/OpenRay_All_Proxies_39ce9f.txt',
    'https://gitverse.ru/api/repos/RUVIPIEN/russian-white-bolt/raw/branch/master/VPNMIRRORS/v2ray/OpenRay_All_Proxies_39e55f.txt',
    'https://gitverse.ru/api/repos/RUVIPIEN/russian-white-bolt/raw/branch/master/VPNMIRRORS/v2ray/Pawdroid_Free_Servers_6d71e8.txt',
    'https://gitverse.ru/api/repos/RUVIPIEN/russian-white-bolt/raw/branch/master/VPNMIRRORS/v2ray/Pawdroid_Free_Servers_ea68d1.txt',
    'https://gitverse.ru/api/repos/RUVIPIEN/russian-white-bolt/raw/branch/master/VPNMIRRORS/v2ray/Roosterkid_V2Ray_2e2cfa.txt',
    'https://gitverse.ru/api/repos/RUVIPIEN/russian-white-bolt/raw/branch/master/VPNMIRRORS/v2ray/Sevcator_VLESS_ffd7b3.txt',
    'https://gitverse.ru/api/repos/RUVIPIEN/russian-white-bolt/raw/branch/master/VPNMIRRORS/v2ray/SilentGhost_Blacklist_676750.txt',
    'https://gitverse.ru/api/repos/RUVIPIEN/russian-white-bolt/raw/branch/master/VPNMIRRORS/v2ray/V2RayRoot_VLESS_ece140.txt',
    'https://gitverse.ru/api/repos/RUVIPIEN/russian-white-bolt/raw/branch/master/VPNMIRRORS/v2ray/V2RayRoot_VLESS_feed6f.txt',
    'https://gitverse.ru/api/repos/RUVIPIEN/russian-white-bolt/raw/branch/master/VPNMIRRORS/v2ray/VLESS_Reality_White_221373.txt',
    'https://gitverse.ru/api/repos/RUVIPIEN/russian-white-bolt/raw/branch/master/VPNMIRRORS/v2ray/VLESS_Reality_White_3eac2d.txt',
    'https://gitverse.ru/api/repos/RUVIPIEN/russian-white-bolt/raw/branch/master/VPNMIRRORS/v2ray/Vify_VLESS_7f9765.txt',
    'https://gitverse.ru/api/repos/RUVIPIEN/russian-white-bolt/raw/branch/master/VPNMIRRORS/v2ray/WLRUS_Black_List_4617cb.txt',
    'https://gitverse.ru/api/repos/RUVIPIEN/russian-white-bolt/raw/branch/master/VPNMIRRORS/v2ray/Xray_Mix_URI_c4598b.txt',
    'https://gitverse.ru/api/repos/RUVIPIEN/russian-white-bolt/raw/branch/master/VPNMIRRORS/v2ray/Yitong_V2Ray_11218f.txt',
    'https://gitverse.ru/api/repos/RUVIPIEN/russian-white-bolt/raw/branch/master/VPNMIRRORS/happ/SER38_Happ_Sub1_ddd131.txt',
    'https://github.com/Epodonios/v2ray-configs/raw/main/All_Configs_Sub.txt',
    'https://github.com/LalatinaHub/Mineral/raw/refs/heads/master/result/nodes',
    'https://github.com/sakha1370/OpenRay/raw/refs/heads/main/output/all_valid_proxies.txt',
    'https://github.com/Epodonios/v2ray-configs/raw/main/Splitted-By-Protocol/trojan.txt',
    'https://github.com/LalatinaHub/Mineral/raw/refs/heads/master/result/nodes',
    'https://github.com/igareck/vpn-configs-for-russia/raw/refs/heads/main/BLACK_VLESS_RUS_mobile.txt',
    'https://github.com/Mr-Meshky/vify/raw/refs/heads/main/configs/vless.txt',
    'https://github.com/rtwo2/FastNodes/raw/refs/heads/main/sub/protocols/hysteria2.txt',
    'https://github.com/Argh94/Proxy-List/raw/refs/heads/main/All_Config.txt',
    'https://gist.github.com/DestroyST6767/50af50221ca1858ba2084efc0f524fbc.txt',
    'https://github.com/MhdiTaheri/V2rayCollector_Py/raw/refs/heads/main/sub/Mix/mix.txt',
    'https://github.com/MhdiTaheri/V2rayCollector/raw/refs/heads/main/sub/mix',
    'https://github.com/FLEXIY0/matryoshka-vpn/raw/main/configs/russia_whitelist.txt',
    'https://gbr.mydan.online/configs',
    'https://subrostunnel.vercel.app/gen.txt',
    'https://ety.twinkvibe.gay/whitelist',
    'https://subrostunnel.vercel.app/gen.txt',
    'https://msnake.serv00.net/666.txt',
    'https://msnake.serv00.net/sub10.txt',
    'https://msnake.serv00.net/sub9.txt',
    'https://subrostunnel.vercel.app/wl.txt',
    'https://v2.alicivil.workers.dev/',
    'https://rostunnel.vercel.app/mega.txt',
    'https://alley.serv00.net/whitelist/',
    'https://gitflic.ru/project/sigil/my-new-cool-project/blob/raw?file=whitelist',
    'https://gist.githubusercontent.com/sevushyamamoto-stack/9341be7a058e132154d407d082a60fb1/raw/mysub.txt',
    'https://gist.githubusercontent.com/cvedcvpn/e7221e7f54944f2611c3c0460f3afd30/raw/90bbd746ef545e49ef7e408969c031ae211fdc03/CVEDCVPN',
    'https://cdn.jsdelivr.net/gh/xiaoji235/airport-free/v2ray.txt',
    'https://gistpad.com/raw/lumar-vpn-all-tg-reverse-engineer-s-basement',
    'https://gbr.mydan.online/configs',
    'http://allvpn.x10.mx/sub.php',
    'https://subrostunnel.vercel.app/gen.txt',
    'https://gist.githubusercontent.com/Syavar/3e76222fc05fde9abcb35c2f24572021/raw/e2f7ef901ae4ba5bab7bef20adef41bead7ba626/gistfile1.txt',
    'https://www.v2nodes.com/subscriptions/country/all/?key=E8FF7329C918147'
]

OUTPUT_FILES = {
    'vless': 'vless.txt',
    'reality': 'reality.txt',
    'vmess': 'vmess.txt',
    'trojan': 'trojan.txt',
    'hysteria2': 'hysteria2.txt',
    'shadowsocks': 'ss.txt',
    'socks': 'socks.txt',
    'wireguard': 'wireguard.txt'
}

# ------------------------------------------------------------
# توابع کمکی (بدون تغییر)
# ------------------------------------------------------------
def decode_if_base64(content: str) -> str:
    try:
        return base64.b64decode(content).decode('utf-8', errors='ignore')
    except:
        return content

def extract_configs_from_line(line: str) -> Tuple[Optional[str], Optional[str]]:
    line = line.strip()
    if not line:
        return None, None
    if line.startswith('vless://'):
        if 'security=reality' in line:
            return 'reality', line
        return 'vless', line
    elif line.startswith('vmess://'):
        return 'vmess', line
    elif line.startswith('trojan://'):
        return 'trojan', line
    elif line.startswith('hysteria2://') or line.startswith('hy2://'):
        return 'hysteria2', line
    elif line.startswith('ss://'):
        return 'shadowsocks', line
    elif line.startswith('socks4://') or line.startswith('socks5://'):
        return 'socks', line
    elif line.startswith('wireguard://') or '[interface]' in line.lower():
        return 'wireguard', line
    return None, None

def get_host_port_from_config(protocol: str, config: str) -> Tuple[Optional[str], Optional[int]]:
    try:
        if protocol in ('vless', 'reality', 'trojan'):
            parsed = urlparse(config)
            return parsed.hostname, parsed.port
        elif protocol == 'vmess':
            import json
            encoded = config[8:]
            decoded = base64.b64decode(encoded).decode('utf-8', errors='ignore')
            data = json.loads(decoded)
            return data.get('add'), data.get('port')
        elif protocol == 'socks':
            parsed = urlparse(config)
            return parsed.hostname, parsed.port
        elif protocol == 'shadowsocks':
            if '@' in config:
                after_at = config.split('@')[1].split('#')[0]
                host, port = after_at.split(':')
                return host, int(port)
            else:
                encoded = config[5:].split('#')[0]
                decoded = base64.b64decode(encoded).decode('utf-8', errors='ignore')
                if '@' in decoded:
                    host_port = decoded.split('@')[1]
                    host, port = host_port.split(':')
                    return host, int(port)
        else:
            return None, None
    except:
        return None, None
    return None, None

def tcp_ping(host: str, port: int, timeout: float = 1.0) -> bool:
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        sock.connect((host, port))
        sock.close()
        return True
    except:
        return False

def fetch_url_with_retry(url: str, max_retries: int = 2, timeout: Tuple[int, int] = (10, 25)) -> Tuple[str, List[str]]:
    session = requests.Session()
    retries = Retry(
        total=max_retries,
        backoff_factor=0.5,
        status_forcelist=[500, 502, 503, 504],
        allowed_methods=["GET"]
    )
    adapter = HTTPAdapter(max_retries=retries)
    session.mount('http://', adapter)
    session.mount('https://', adapter)
    try:
        resp = session.get(url, timeout=timeout)
        if resp.status_code == 200:
            decoded = decode_if_base64(resp.text.strip())
            lines = [line.strip() for line in decoded.splitlines() if line.strip()]
            return url, lines
        else:
            print(f"   ⚠️ {url} returned {resp.status_code}")
            return url, []
    except Exception as e:
        print(f"   ❌ Failed after retries: {url} - {e}")
        return url, []

def fetch_all_parallel(urls: List[str], max_workers: int = 8) -> Dict[str, List[str]]:
    results = {}
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_url = {executor.submit(fetch_url_with_retry, url): url for url in urls}
        for future in as_completed(future_to_url):
            url, lines = future.result()
            results[url] = lines
            print(f"   ✅ {url} -> {len(lines)} lines")
    return results

def sample_health_check(configs: Set[str], protocol: str, sample_size: int = 300) -> dict:
    if protocol in ('hysteria2', 'wireguard'):
        return {'sampled': 0, 'alive': 0, 'percent': 0}
    config_list = list(configs)
    if len(config_list) <= sample_size:
        sample = config_list
    else:
        sample = random.sample(config_list, sample_size)
    alive = 0
    for cfg in sample:
        host, port = get_host_port_from_config(protocol, cfg)
        if host and port and tcp_ping(host, port, timeout=1.0):
            alive += 1
    return {'sampled': len(sample), 'alive': alive, 'percent': (alive/len(sample))*100 if sample else 0}

def main():
    print("🚀 Starting fetch with retry, parallel, health stats...")
    start_total = time.perf_counter()
    
    print("📡 Fetching from all sources concurrently (with retry)...")
    url_to_lines = fetch_all_parallel(urls, max_workers=8)
    
    configs_by_protocol: Dict[str, Set[str]] = {key: set() for key in OUTPUT_FILES.keys()}
    for url, lines in url_to_lines.items():
        for line in lines:
            proto, cfg = extract_configs_from_line(line)
            if proto and cfg:
                configs_by_protocol[proto].add(cfg)
    
    stats = {}
    print("\n🩺 Running health check sampling...")
    for proto, cfg_set in configs_by_protocol.items():
        raw_count = len(cfg_set)
        health = sample_health_check(cfg_set, proto, sample_size=300)
        stats[proto] = {
            'raw_count': raw_count,
            'final_count': raw_count,
            'health_sample': health
        }
        print(f"   {proto}: total={raw_count:,}, sample={health['sampled']}, alive={health['alive']} ({health['percent']:.1f}%)")
    
    for proto, cfg_set in configs_by_protocol.items():
        if cfg_set:
            text = "\n".join(sorted(cfg_set))
            encoded = base64.b64encode(text.encode('utf-8')).decode('utf-8')
            filename = OUTPUT_FILES[proto]
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(encoded)
            print(f"✅ {filename}: {len(cfg_set)} configs saved.")
        else:
            print(f"⚠️ {OUTPUT_FILES[proto]}: no configs found.")
    
    total_configs = sum(stats[p]['final_count'] for p in stats)
    summary = {
        'total_configs': total_configs,
        'total_sources': len(urls),
        'execution_time_sec': time.perf_counter() - start_total,
        'timestamp': time.strftime('%Y-%m-%d %H:%M:%S UTC', time.gmtime()),
        'successful_sources': len([u for u, lines in url_to_lines.items() if lines]),
        'failed_sources': len([u for u, lines in url_to_lines.items() if not lines])
    }
    stats['summary'] = summary
    with open('stats.json', 'w', encoding='utf-8') as f:
        json.dump(stats, f, indent=2)
    print(f"\n📊 Stats saved to stats.json")
    print(f"   Total configs: {total_configs:,}")
    print(f"   Execution time: {summary['execution_time_sec']:.2f}s")
    print(f"   Successful sources: {summary['successful_sources']} / {summary['total_sources']}")

if __name__ == "__main__":
    main()