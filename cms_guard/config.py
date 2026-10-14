"""Validated inputs. No credentials or company URLs belong in configuration."""
import copy
import ipaddress
import math
import os
import re
from urllib.parse import urlsplit

class ConfigError(ValueError): pass

LIMITS = {'max_requests': 100, 'total_seconds': 120, 'timeout': 5, 'max_bytes': 65536, 'rps': 2}
BOUNDS = {'max_requests': 500, 'total_seconds': 600, 'timeout': 15, 'max_bytes': 262144, 'rps': 50}
ID = re.compile(r'^[a-zA-Z0-9_-]{1,64}$')

def origin(url):
    p = urlsplit(url)
    return f'{p.scheme}://{p.netloc}'

def check_url(url, mode):
    if not isinstance(url, str) or len(url) > 4096 or any(ord(c)<33 or ord(c)>126 for c in url) or '\\' in url:
        raise ConfigError('URL must be ASCII with percent-encoded path, without whitespace')
    try:
        p = urlsplit(url); port = p.port
    except ValueError:
        raise ConfigError('Invalid URL') from None
    if p.username or p.password or p.fragment or not p.hostname:
        raise ConfigError('URL credentials/fragments are not allowed')
    if mode == 'lab':
        if p.scheme != 'http' or p.hostname != '127.0.0.1':
            raise ConfigError('Lab accepts http://127.0.0.1 only')
    elif p.scheme != 'https': raise ConfigError('Remote checks require HTTPS')
    if port is not None and not 1 <= port <= 65535: raise ConfigError('Invalid port')
    return url

def validate(raw):
    if not isinstance(raw, dict): raise ConfigError('Configuration must be a JSON object')
    c = copy.deepcopy(raw)
    if c.get('version') != 1 or c.get('mode') not in ('lab','remote'): raise ConfigError('version=1 and mode=lab/remote required')
    limits = c.get('limits', {})
    if not isinstance(limits, dict) or set(limits)-set(LIMITS): raise ConfigError('Unknown limit')
    c['limits'] = LIMITS | limits
    for k,v in c['limits'].items():
        if isinstance(v,bool) or not isinstance(v,(int,float)) or not math.isfinite(v) or not 0<v<=BOUNDS[k]: raise ConfigError('Invalid limit: '+k)
        if k in ('max_requests','max_bytes') and not isinstance(v,int): raise ConfigError(k+' must be an integer')
    if c['mode']=='remote' and c['limits']['rps'] > 2: raise ConfigError('Remote rate is capped at 2 requests/sec')
    networks=c.setdefault('allowed_networks',[])
    if not isinstance(networks,list): raise ConfigError('allowed_networks must be a list')
    try:
        for n in networks: ipaddress.ip_network(n)
    except (ValueError,TypeError): raise ConfigError('Invalid network CIDR') from None
    roles=c.get('roles')
    if not isinstance(roles,dict) or not roles or len(roles)>20: raise ConfigError('1..20 roles required')
    for name,r in roles.items():
        if not isinstance(name,str) or not ID.fullmatch(name) or not isinstance(r,dict): raise ConfigError('Invalid role')
        if not r: continue
        if set(r)!= {'header','env','origin'} or r['header'] not in ('Authorization','Cookie'): raise ConfigError('Role requires header, env, origin')
        if not isinstance(r['env'],str) or not re.fullmatch(r'[A-Z][A-Z0-9_]{0,100}',r['env']): raise ConfigError('Invalid environment variable name')
        check_url(r['origin'],c['mode'])
        if origin(r['origin']) != r['origin']: raise ConfigError('Credential origin must be scheme://host[:port]')
    targets=c.setdefault('targets',[])
    if not isinstance(targets,list) or len(targets)>100: raise ConfigError('At most 100 targets')
    seen=set(); urls=set()
    for t in targets:
        if not isinstance(t,dict) or not isinstance(t.get('id'),str) or not ID.fullmatch(t.get('id','')) or t['id'] in seen: raise ConfigError('Unique target id required')
        seen.add(t['id']); check_url(t.get('url'),c['mode']); urls.add(t['url'])
        kind=t.setdefault('kind','access')
        if kind not in ('access','session','headers','lab_upload','lab_render'): raise ConfigError('Unknown target kind')
        if kind.startswith('lab_'):
            if c['mode']!='lab' or urlsplit(t['url']).path != {'lab_upload':'/lab/upload','lab_render':'/lab/render'}[kind] or urlsplit(t['url']).query: raise ConfigError('Lab POST path only')
            continue
        if kind=='headers': continue
        marker=t.get('canary')
        if not isinstance(marker,str) or not 16<=len(marker.encode())<=256: raise ConfigError('Synthetic canary must be 16..256 bytes')
        access=t.get('access')
        if not isinstance(access,dict) or not access or 'allow' not in access.values(): raise ConfigError('A positive allow control is required')
        for role,expect in access.items():
            if role not in roles or expect not in ('allow','deny'): raise ConfigError('Invalid role expectation')
            if roles[role] and roles[role]['origin']!=origin(t['url']): raise ConfigError('Credential origin mismatch')
        if kind=='session':
            if any(not roles[r] for r in access) or 'deny' not in access.values() or t.get('revocation_confirmed') is not True: raise ConfigError('Session requires confirmed revoked credential and allow/deny controls')
    c['_urls']=urls
    return c

def credentials(config):
    result={}
    for name,role in config['roles'].items():
        if not role: result[name]={}; continue
        value=os.environ.get(role['env'])
        if not value or len(value)>16384 or any(ord(x)<32 or ord(x)==127 for x in value): raise ConfigError('Missing or invalid credential environment variable: '+role['env'])
        result[name]={role['header']: value}
    for target in config['targets']:
        if target['kind'] == 'session':
            active=[result[r] for r,e in target['access'].items() if e=='allow']
            if any(result[r] in active for r,e in target['access'].items() if e=='deny'):
                raise ConfigError('Active and revoked credentials must be distinct')
    return result
