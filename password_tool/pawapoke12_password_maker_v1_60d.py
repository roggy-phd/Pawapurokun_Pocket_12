#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""PowerPoke 12 Password Maker / Analyzer v1.60d — pitch Lv0 synchronization and expanded original-pitch RAW ranges."""
import tkinter as tk
import sys, os, unicodedata
_BASE=os.path.dirname(os.path.abspath(__file__))
_VENDOR=os.path.join(_BASE,"vendor")
if _VENDOR not in sys.path: sys.path.insert(0,_VENDOR)
import qrcode
from tkinter import ttk,messagebox
GAME_PASSWORD_LIMIT = 128
# ROM由来: overlay17 のパスワード作業バッファは 0x60 = 96 バイト（object+0x219、長さは16bitで+0x2FC）。
# 96 バイト = 128 文字ちょうど。参照: cmp #0x60 @ 0x021A4528 / 0x021A45AC / 0x021A4EB0 / 0x021A4F34
PASSWORD_BUFFER_BYTES = 0x60
ALPHABET="まおさであにぢめたやれじぼすこらごつむぎゆけろかわもぞふそだぐみてざるんせちなういくのがぬえよずどをぶひきはしげへねほべぜばびづ"
C2V={c:i for i,c in enumerate(ALPHABET)}
M=[60,18,33,57,37,9,43,6,44,35,65,28,15,66,58,32,31,5,71,69,1,22,67,34,16,36,42,62,75,13,10,39,64,11,40,41,59,19,61,72,46,14,17,21,3,2,8,25,56,23,4,38,63,70,45,73,27,7,26,12,68,29,24,74]
FM=[[22,21,20,19,18,17,16,15],[38,37,36,35,34,33,32,31],[30,29,28,27,26,25,24,23],[62,61,60,59,58,57,56,55],[46,45,44,43,42,41,40,39],[102,101,100,99,98,97,96,95],[78,77,76,75,74,73,72,71],[94,93,92,91,90,89,88,87],[86,85,84,83,82,81,80,79],[70,69,68,67,66,65,64,63],[54,53,52,51,50,49,48,47],[None,None,None,None,106,105,104,103]]
P={
"スライダー系":[("球種なし",None),("スライダー",0),("Hスライダー",1),("カットボール",2),("オリジナル",15)],
"カーブ系":[("球種なし",None),("カーブ",0),("スローカーブ",1),("スラーブ",2),("Dカーブ",3),("ドロップ",4),("ナックルカーブ",5),("オリジナル",15)],
"フォーク系":[("球種なし",None),("フォーク",0),("パーム",1),("ナックル",2),("Vスライダー",3),("SFF",4),("チェンジアップ",5),("あばたボール",6),("サークルチェンジ",7),("フォッシュ",8),("オリジナル",15)],
"シンカー系":[("球種なし",None),("シンカー",0),("Hシンカー",1),("オリジナル",15)],
"シュート系":[("球種なし",None),("シュート",0),("Hシュート",1),("シンキングファスト",2),("オリジナル",15)],
"ストレート系":[("球種なし",None),("ストレート",0),("ムービングファスト",1),("ツーシーム",2),("超スローボール",3),("オリジナル",15)]}
F=list(P)
def pitch_choices(family):
 known={code:name for name,code in P[family] if code is not None}
 return ["球種なし"]+[known.get(code,f"未登録 code {code:X}") for code in range(16)]
def pitch_code(family,name):
 if name=="球種なし":return None
 if name.startswith("未登録 code "):return int(name.rsplit(" ",1)[1],16)
 if name.startswith("範囲外 code "):return int(name.rsplit(" ",1)[1],16)
 if name.startswith("不明(") and name.endswith(")"):return int(name[3:-1])
 return dict(P[family])[name]
def clean(s): return "".join(c for c in s if c in C2V)
def format_password_groups(s, size=3):
 compact="".join(ch for ch in s if not ch.isspace())
 return " ".join(compact[i:i+size] for i in range(0,len(compact),size))
def flags(r):
 r=bytearray(r)
 for q,refs in enumerate(FM):
  r[q]=sum((1<<(7-j)) for j,n in enumerate(refs) if n and r[n-1])
 return r
def csum(r):
 s=sum(r[:12])+sum(r[14:]); return (s+23)&255,255-(s&255)
def s1comp(r): return bytearray(r[:14])+bytearray(x for x in r[14:] if x)
def ncomp(d):
 o=bytearray()
 for z in range(0,len(d),4):
  ns=[]; fl=0
  for i,b in enumerate(d[z:z+4]):
   for k,n in ((2*i,b>>4),(2*i+1,b&15)):
    if n: fl|=1<<k; ns.append(n)
  o.append(fl)
  if len(ns)&1: ns=[0]+ns
  for i in range(0,len(ns),2): o.append(ns[i]<<4|ns[i+1])
 return o
def ndecomp(d):
 o=bytearray();p=0
 while p<len(d):
  fl=d[p];p+=1;k=fl.bit_count();need=(k+1)//2
  if p+need>len(d): raise ValueError("truncated 4-bit stream")
  ns=[]
  for b in d[p:p+need]: ns += [b>>4,b&15]
  p+=need
  if k&1: ns=ns[1:]
  a=[0]*8;q=0
  for i in range(8):
   if fl>>i&1:a[i]=ns[q];q+=1
  for i in range(0,8,2):o.append(a[i]<<4|a[i+1])
 return o
def mos(d,sign=1):return bytearray((b+sign*M[i%64])&255 for i,b in enumerate(d))
def b2v(d):
 o=[]
 for p in range(0,len(d),3):
  x=list(d[p:p+3]);n=len(x);x += [0]*(3-n);a,b,c=x
  y=[a&63,(a>>6)*16+(b&15),(c>>6)*16+(b>>4),c&63]
  o += y[:(n*8+5)//6]
 return o
def v2b(v):
 o=bytearray()
 for p in range(0,len(v),4):
  x=list(v[p:p+4]);n=len(x);x += [0]*(4-n);a,b,c,d=x
  y=[a|((b>>4)<<6),(b&15)|((c&15)<<4),d|((c>>4)<<6)]
  nb=3 if n==4 else (n*6)//8;o+=bytearray(y[:nb])
 return o
def encode(raw):
 if len(raw)!=106:raise ValueError("RAW must be 106 bytes")
 r=flags(raw);r[12],r[13]=csum(r);a=s1comp(r);b=ncomp(a);c=mos(b);pw="".join(ALPHABET[x] for x in b2v(c))
 return pw,r
def expand(a):
 r=bytearray(106);r[:14]=a[:14];p=14
 present={}
 for q,refs in enumerate(FM):
  for j,n in enumerate(refs):
   if n: present[n]=bool(r[q] & (1<<(7-j)))
 for n in range(15,107):
  if present.get(n,False):
   if p>=len(a):raise ValueError("truncated byte stream")
   r[n-1]=a[p];p+=1
 return r
def decode(pw):
 s=clean(pw)
 if not s:raise ValueError("No valid Poke10-12 password characters found")
 d=mos(v2b([C2V[c] for c in s]),-1);a=ndecomp(d)
 if len(a)<12:raise ValueError("decoded data too short")
 need=14+sum(x.bit_count() for x in a[:11])+(a[11]&0x0F).bit_count()
 if len(a)<need:raise ValueError("decoded byte stream too short")
 r=expand(a[:need]);c=csum(r);return r,(r[12],r[13])==c,c
def minimal():
 r=bytearray(106);r[14]=1;r[26]=1;r[29]=0x11;r[30]=0x11;r[32]=1;r[33]=0x11;r[46]=0x20;r[94]=20;r[95]=48;r[99]=43;r[105]=2;return r
def dump(r):
 return "\n".join(f"{i+1:03d}: "+" ".join(f"{x:02X}" for x in r[i:i+16]) for i in range(0,106,16))
def parse(t):
 a=[]
 for line in t.splitlines():
  if ":" in line:line=line.split(":",1)[1]
  for x in line.replace(","," ").split():a.append(int(x.removeprefix("0x").removeprefix("0X"),16))
 if len(a)!=106:raise ValueError(f"Need 106 bytes, got {len(a)}")
 return bytearray(a)
def selftest():
 for seed in range(4):
  r=minimal()
  for i in range(14,106):
   if seed and i%(seed+2)==0:r[i]=(i*37+seed*11)&255
  pw,n=encode(r);d,ok,_=decode(pw)
  if not ok or d!=n:return False
 return True


# ---- PowerPoke 12 name character codec --------------------------------------
# Static table. No runtime EUC/JIS inference.
NAME_CODE_TO_CHAR = {
    0x00: '\u3000',
    0x01: 'あ',
    0x02: 'い',
    0x03: 'う',
    0x04: 'え',
    0x05: 'お',
    0x06: 'か',
    0x07: 'き',
    0x08: 'く',
    0x09: 'け',
    0x0A: 'こ',
    0x0B: 'さ',
    0x0C: 'し',
    0x0D: 'す',
    0x0E: 'せ',
    0x0F: 'そ',
    0x10: 'た',
    0x11: 'ち',
    0x12: 'つ',
    0x13: 'て',
    0x14: 'と',
    0x15: 'な',
    0x16: 'に',
    0x17: 'ぬ',
    0x18: 'ね',
    0x19: 'の',
    0x1A: 'は',
    0x1B: 'ひ',
    0x1C: 'ふ',
    0x1D: 'へ',
    0x1E: 'ほ',
    0x1F: 'ま',
    0x20: 'み',
    0x21: 'む',
    0x22: 'め',
    0x23: 'も',
    0x24: 'や',
    0x25: 'ゆ',
    0x26: 'よ',
    0x27: 'ら',
    0x28: 'り',
    0x29: 'る',
    0x2A: 'れ',
    0x2B: 'ろ',
    0x2C: 'わ',
    0x2D: 'を',
    0x2E: 'ん',
    0x2F: 'ぁ',
    0x30: 'ぃ',
    0x31: 'ぅ',
    0x32: 'ぇ',
    0x33: 'ぉ',
    0x34: 'っ',
    0x35: 'ゃ',
    0x36: 'ゅ',
    0x37: 'ょ',
    0x38: 'が',
    0x39: 'ぎ',
    0x3A: 'ぐ',
    0x3B: 'げ',
    0x3C: 'ご',
    0x3D: 'ざ',
    0x3E: 'じ',
    0x3F: 'ず',
    0x40: 'ぜ',
    0x41: 'ぞ',
    0x42: 'だ',
    0x43: 'ぢ',
    0x44: 'づ',
    0x45: 'で',
    0x46: 'ど',
    0x47: 'ば',
    0x48: 'び',
    0x49: 'ぶ',
    0x4A: 'べ',
    0x4B: 'ぼ',
    0x4C: 'ぱ',
    0x4D: 'ぴ',
    0x4E: 'ぷ',
    0x4F: 'ぺ',
    0x50: 'ぽ',
    0x51: 'ア',
    0x52: 'イ',
    0x53: 'ウ',
    0x54: 'エ',
    0x55: 'オ',
    0x56: 'カ',
    0x57: 'キ',
    0x58: 'ク',
    0x59: 'ケ',
    0x5A: 'コ',
    0x5B: 'サ',
    0x5C: 'シ',
    0x5D: 'ス',
    0x5E: 'セ',
    0x5F: 'ソ',
    0x60: 'タ',
    0x61: 'チ',
    0x62: 'ツ',
    0x63: 'テ',
    0x64: 'ト',
    0x65: 'ナ',
    0x66: 'ニ',
    0x67: 'ヌ',
    0x68: 'ネ',
    0x69: 'ノ',
    0x6A: 'ハ',
    0x6B: 'ヒ',
    0x6C: 'フ',
    0x6D: 'ヘ',
    0x6E: 'ホ',
    0x6F: 'マ',
    0x70: 'ミ',
    0x71: 'ム',
    0x72: 'メ',
    0x73: 'モ',
    0x74: 'ヤ',
    0x75: 'ユ',
    0x76: 'ヨ',
    0x77: 'ラ',
    0x78: 'リ',
    0x79: 'ル',
    0x7A: 'レ',
    0x7B: 'ロ',
    0x7C: 'ワ',
    0x7D: 'ヲ',
    0x7E: 'ン',
    0x7F: 'ヴ',
    0x80: 'ァ',
    0x81: 'ィ',
    0x82: 'ゥ',
    0x83: 'ェ',
    0x84: 'ォ',
    0x85: 'ッ',
    0x86: 'ャ',
    0x87: 'ュ',
    0x88: 'ョ',
    0x89: 'ガ',
    0x8A: 'ギ',
    0x8B: 'グ',
    0x8C: 'ゲ',
    0x8D: 'ゴ',
    0x8E: 'ザ',
    0x8F: 'ジ',
    0x90: 'ズ',
    0x91: 'ゼ',
    0x92: 'ゾ',
    0x93: 'ダ',
    0x94: 'ヂ',
    0x95: 'ヅ',
    0x96: 'デ',
    0x97: 'ド',
    0x98: 'バ',
    0x99: 'ビ',
    0x9A: 'ブ',
    0x9B: 'ベ',
    0x9C: 'ボ',
    0x9D: 'パ',
    0x9E: 'ピ',
    0x9F: 'プ',
    0xA0: 'ペ',
    0xA1: 'ポ',
    0xA2: '０',
    0xA3: '１',
    0xA4: '２',
    0xA5: '３',
    0xA6: '４',
    0xA7: '５',
    0xA8: '６',
    0xA9: '７',
    0xAA: '８',
    0xAB: '９',
    0xAC: 'Ａ',
    0xAD: 'Ｂ',
    0xAE: 'Ｃ',
    0xAF: 'Ｄ',
    0xB0: 'Ｅ',
    0xB1: 'Ｆ',
    0xB2: 'Ｇ',
    0xB3: 'Ｈ',
    0xB4: 'Ｉ',
    0xB5: 'Ｊ',
    0xB6: 'Ｋ',
    0xB7: 'Ｌ',
    0xB8: 'Ｍ',
    0xB9: 'Ｎ',
    0xBA: 'Ｏ',
    0xBB: 'Ｐ',
    0xBC: 'Ｑ',
    0xBD: 'Ｒ',
    0xBE: 'Ｓ',
    0xBF: 'Ｔ',
    0xC0: 'Ｕ',
    0xC1: 'Ｖ',
    0xC2: 'Ｗ',
    0xC3: 'Ｘ',
    0xC4: 'Ｙ',
    0xC5: 'Ｚ',
    0xC6: '♂',
    0xC7: '♀',
    0xC8: '◎',
    0xC9: '○',
    0xCA: '★',
    0xCB: '＠',
    0xCC: '→',
    0xCD: '←',
    0xCE: '↑',
    0xCF: '↓',
    0xD0: '。',
    0xD1: '、',
    0xD2: '…',
    0xD3: '「',
    0xD4: '」',
    0xD5: '＋',
    0xD6: '－',
    0xD7: '？',
    0xD8: '！',
    0xD9: '『',
    0xDA: '』',
    0xDB: '～',
    0xDC: '❤',
    0xDD: '×',
    0xDE: '・',
    0xDF: '／',
    0xE0: '（',
    0xE1: '）',
    0xE2: '％',
    0xE3: '￥',
    0xE4: '♪',
    0xE5: '♫',
    0xE800: '亜',
    0xE801: '唖',
    0xE802: '娃',
    0xE803: '阿',
    0xE804: '哀',
    0xE805: '愛',
    0xE806: '挨',
    0xE807: '姶',
    0xE808: '逢',
    0xE809: '葵',
    0xE80A: '茜',
    0xE80B: '穐',
    0xE80C: '悪',
    0xE80D: '握',
    0xE80E: '渥',
    0xE80F: '旭',
    0xE810: '葦',
    0xE811: '芦',
    0xE812: '鯵',
    0xE813: '梓',
    0xE814: '圧',
    0xE815: '斡',
    0xE816: '扱',
    0xE817: '宛',
    0xE818: '姐',
    0xE819: '虻',
    0xE81A: '飴',
    0xE81B: '絢',
    0xE81C: '綾',
    0xE81D: '鮎',
    0xE81E: '或',
    0xE81F: '粟',
    0xE820: '袷',
    0xE821: '安',
    0xE822: '庵',
    0xE823: '按',
    0xE824: '暗',
    0xE825: '案',
    0xE826: '闇',
    0xE827: '鞍',
    0xE828: '杏',
    0xE829: '以',
    0xE82A: '伊',
    0xE82B: '位',
    0xE82C: '依',
    0xE82D: '偉',
    0xE82E: '囲',
    0xE82F: '夷',
    0xE830: '委',
    0xE831: '威',
    0xE832: '尉',
    0xE833: '惟',
    0xE834: '意',
    0xE835: '慰',
    0xE836: '易',
    0xE837: '椅',
    0xE838: '為',
    0xE839: '畏',
    0xE83A: '異',
    0xE83B: '移',
    0xE83C: '維',
    0xE83D: '緯',
    0xE83E: '胃',
    0xE83F: '萎',
    0xE840: '衣',
    0xE841: '謂',
    0xE842: '違',
    0xE843: '遺',
    0xE844: '医',
    0xE845: '井',
    0xE846: '亥',
    0xE847: '域',
    0xE848: '育',
    0xE849: '郁',
    0xE84A: '磯',
    0xE84B: '一',
    0xE84C: '壱',
    0xE84D: '溢',
    0xE84E: '逸',
    0xE84F: '稲',
    0xE850: '茨',
    0xE851: '芋',
    0xE852: '鰯',
    0xE853: '允',
    0xE854: '印',
    0xE855: '咽',
    0xE856: '員',
    0xE857: '因',
    0xE858: '姻',
    0xE859: '引',
    0xE85A: '飲',
    0xE85B: '淫',
    0xE85C: '胤',
    0xE85D: '蔭',
    0xE85E: '院',
    0xE85F: '陰',
    0xE860: '隠',
    0xE861: '韻',
    0xE862: '吋',
    0xE863: '右',
    0xE864: '宇',
    0xE865: '烏',
    0xE866: '羽',
    0xE867: '迂',
    0xE868: '雨',
    0xE869: '卯',
    0xE86A: '鵜',
    0xE86B: '窺',
    0xE86C: '丑',
    0xE86D: '碓',
    0xE86E: '臼',
    0xE86F: '渦',
    0xE870: '嘘',
    0xE871: '唄',
    0xE872: '欝',
    0xE873: '蔚',
    0xE874: '鰻',
    0xE875: '姥',
    0xE876: '厩',
    0xE877: '浦',
    0xE878: '瓜',
    0xE879: '閏',
    0xE87A: '噂',
    0xE87B: '云',
    0xE87C: '運',
    0xE87D: '雲',
    0xE87E: '荏',
    0xE87F: '餌',
    0xE880: '叡',
    0xE881: '営',
    0xE882: '嬰',
    0xE883: '影',
    0xE884: '映',
    0xE885: '曳',
    0xE886: '栄',
    0xE887: '永',
    0xE888: '泳',
    0xE889: '洩',
    0xE88A: '瑛',
    0xE88B: '盈',
    0xE88C: '穎',
    0xE88D: '頴',
    0xE88E: '英',
    0xE88F: '衛',
    0xE890: '詠',
    0xE891: '鋭',
    0xE892: '液',
    0xE893: '疫',
    0xE894: '益',
    0xE895: '駅',
    0xE896: '悦',
    0xE897: '謁',
    0xE898: '越',
    0xE899: '閲',
    0xE89A: '榎',
    0xE89B: '厭',
    0xE89C: '円',
    0xE89D: '園',
    0xE89E: '堰',
    0xE89F: '奄',
    0xE8A0: '宴',
    0xE8A1: '延',
    0xE8A2: '怨',
    0xE8A3: '掩',
    0xE8A4: '援',
    0xE8A5: '沿',
    0xE8A6: '演',
    0xE8A7: '炎',
    0xE8A8: '焔',
    0xE8A9: '煙',
    0xE8AA: '燕',
    0xE8AB: '猿',
    0xE8AC: '縁',
    0xE8AD: '艶',
    0xE8AE: '苑',
    0xE8AF: '薗',
    0xE8B0: '遠',
    0xE8B1: '鉛',
    0xE8B2: '鴛',
    0xE8B3: '塩',
    0xE8B4: '於',
    0xE8B5: '汚',
    0xE8B6: '甥',
    0xE8B7: '凹',
    0xE8B8: '央',
    0xE8B9: '奥',
    0xE8BA: '往',
    0xE8BB: '応',
    0xE8BC: '押',
    0xE8BD: '旺',
    0xE8BE: '横',
    0xE8BF: '欧',
    0xE8C0: '殴',
    0xE8C1: '王',
    0xE8C2: '翁',
    0xE8C3: '襖',
    0xE8C4: '鴬',
    0xE8C5: '鴎',
    0xE8C6: '黄',
    0xE8C7: '岡',
    0xE8C8: '沖',
    0xE8C9: '荻',
    0xE8CA: '億',
    0xE8CB: '屋',
    0xE8CC: '憶',
    0xE8CD: '臆',
    0xE8CE: '桶',
    0xE8CF: '牡',
    0xE8D0: '乙',
    0xE8D1: '俺',
    0xE8D2: '卸',
    0xE8D3: '恩',
    0xE8D4: '温',
    0xE8D5: '穏',
    0xE8D6: '音',
    0xE8D7: '下',
    0xE8D8: '化',
    0xE8D9: '仮',
    0xE8DA: '何',
    0xE8DB: '伽',
    0xE8DC: '価',
    0xE8DD: '佳',
    0xE8DE: '加',
    0xE8DF: '可',
    0xE8E0: '嘉',
    0xE8E1: '夏',
    0xE8E2: '嫁',
    0xE8E3: '家',
    0xE8E4: '寡',
    0xE8E5: '科',
    0xE8E6: '暇',
    0xE8E7: '果',
    0xE8E8: '架',
    0xE8E9: '歌',
    0xE8EA: '河',
    0xE8EB: '火',
    0xE8EC: '珂',
    0xE8ED: '禍',
    0xE8EE: '禾',
    0xE8EF: '稼',
    0xE8F0: '箇',
    0xE8F1: '花',
    0xE8F2: '苛',
    0xE8F3: '茄',
    0xE8F4: '荷',
    0xE8F5: '華',
    0xE8F6: '菓',
    0xE8F7: '蝦',
    0xE8F8: '課',
    0xE8F9: '嘩',
    0xE8FA: '貨',
    0xE8FB: '迦',
    0xE8FC: '過',
    0xE8FD: '霞',
    0xE8FE: '蚊',
    0xE8FF: '俄',
    0xE900: '峨',
    0xE901: '我',
    0xE902: '牙',
    0xE903: '画',
    0xE904: '臥',
    0xE905: '芽',
    0xE906: '蛾',
    0xE907: '賀',
    0xE908: '雅',
    0xE909: '餓',
    0xE90A: '駕',
    0xE90B: '介',
    0xE90C: '会',
    0xE90D: '解',
    0xE90E: '回',
    0xE90F: '塊',
    0xE910: '壊',
    0xE911: '廻',
    0xE912: '快',
    0xE913: '怪',
    0xE914: '悔',
    0xE915: '恢',
    0xE916: '懐',
    0xE917: '戒',
    0xE918: '拐',
    0xE919: '改',
    0xE91A: '魁',
    0xE91B: '晦',
    0xE91C: '械',
    0xE91D: '海',
    0xE91E: '灰',
    0xE91F: '界',
    0xE920: '皆',
    0xE921: '絵',
    0xE922: '芥',
    0xE923: '蟹',
    0xE924: '開',
    0xE925: '階',
    0xE926: '貝',
    0xE927: '凱',
    0xE928: '劾',
    0xE929: '外',
    0xE92A: '咳',
    0xE92B: '害',
    0xE92C: '崖',
    0xE92D: '慨',
    0xE92E: '概',
    0xE92F: '涯',
    0xE930: '碍',
    0xE931: '蓋',
    0xE932: '街',
    0xE933: '該',
    0xE934: '鎧',
    0xE935: '骸',
    0xE936: '浬',
    0xE937: '馨',
    0xE938: '蛙',
    0xE939: '垣',
    0xE93A: '柿',
    0xE93B: '蛎',
    0xE93C: '鈎',
    0xE93D: '劃',
    0xE93E: '嚇',
    0xE93F: '各',
    0xE940: '廓',
    0xE941: '拡',
    0xE942: '撹',
    0xE943: '格',
    0xE944: '核',
    0xE945: '殻',
    0xE946: '獲',
    0xE947: '確',
    0xE948: '穫',
    0xE949: '覚',
    0xE94A: '角',
    0xE94B: '赫',
    0xE94C: '較',
    0xE94D: '郭',
    0xE94E: '閣',
    0xE94F: '隔',
    0xE950: '革',
    0xE951: '学',
    0xE952: '岳',
    0xE953: '楽',
    0xE954: '額',
    0xE955: '顎',
    0xE956: '掛',
    0xE957: '笠',
    0xE958: '樫',
    0xE959: '橿',
    0xE95A: '梶',
    0xE95B: '鰍',
    0xE95C: '潟',
    0xE95D: '割',
    0xE95E: '喝',
    0xE95F: '恰',
    0xE960: '括',
    0xE961: '活',
    0xE962: '渇',
    0xE963: '滑',
    0xE964: '葛',
    0xE965: '褐',
    0xE966: '轄',
    0xE967: '且',
    0xE968: '鰹',
    0xE969: '叶',
    0xE96A: '椛',
    0xE96B: '樺',
    0xE96C: '鞄',
    0xE96D: '株',
    0xE96E: '兜',
    0xE96F: '竃',
    0xE970: '蒲',
    0xE971: '釜',
    0xE972: '鎌',
    0xE973: '噛',
    0xE974: '鴨',
    0xE975: '柏',
    0xE976: '茅',
    0xE977: '萱',
    0xE978: '粥',
    0xE979: '刈',
    0xE97A: '苅',
    0xE97B: '瓦',
    0xE97C: '乾',
    0xE97D: '侃',
    0xE97E: '冠',
    0xE97F: '寒',
    0xE980: '刊',
    0xE981: '勘',
    0xE982: '勧',
    0xE983: '巻',
    0xE984: '喚',
    0xE985: '堪',
    0xE986: '姦',
    0xE987: '完',
    0xE988: '官',
    0xE989: '寛',
    0xE98A: '干',
    0xE98B: '幹',
    0xE98C: '患',
    0xE98D: '感',
    0xE98E: '慣',
    0xE98F: '憾',
    0xE990: '換',
    0xE991: '敢',
    0xE992: '柑',
    0xE993: '桓',
    0xE994: '棺',
    0xE995: '款',
    0xE996: '歓',
    0xE997: '汗',
    0xE998: '漢',
    0xE999: '澗',
    0xE99A: '潅',
    0xE99B: '環',
    0xE99C: '甘',
    0xE99D: '監',
    0xE99E: '看',
    0xE99F: '竿',
    0xE9A0: '管',
    0xE9A1: '簡',
    0xE9A2: '緩',
    0xE9A3: '缶',
    0xE9A4: '翰',
    0xE9A5: '肝',
    0xE9A6: '艦',
    0xE9A7: '莞',
    0xE9A8: '観',
    0xE9A9: '諌',
    0xE9AA: '貫',
    0xE9AB: '還',
    0xE9AC: '鑑',
    0xE9AD: '間',
    0xE9AE: '閑',
    0xE9AF: '関',
    0xE9B0: '陥',
    0xE9B1: '韓',
    0xE9B2: '館',
    0xE9B3: '舘',
    0xE9B4: '丸',
    0xE9B5: '含',
    0xE9B6: '岸',
    0xE9B7: '巌',
    0xE9B8: '玩',
    0xE9B9: '癌',
    0xE9BA: '眼',
    0xE9BB: '岩',
    0xE9BC: '翫',
    0xE9BD: '贋',
    0xE9BE: '雁',
    0xE9BF: '頑',
    0xE9C0: '顔',
    0xE9C1: '願',
    0xE9C2: '企',
    0xE9C3: '伎',
    0xE9C4: '危',
    0xE9C5: '喜',
    0xE9C6: '器',
    0xE9C7: '基',
    0xE9C8: '奇',
    0xE9C9: '嬉',
    0xE9CA: '寄',
    0xE9CB: '岐',
    0xE9CC: '希',
    0xE9CD: '幾',
    0xE9CE: '忌',
    0xE9CF: '揮',
    0xE9D0: '机',
    0xE9D1: '旗',
    0xE9D2: '既',
    0xE9D3: '期',
    0xE9D4: '棋',
    0xE9D5: '棄',
    0xE9D6: '機',
    0xE9D7: '帰',
    0xE9D8: '毅',
    0xE9D9: '気',
    0xE9DA: '汽',
    0xE9DB: '畿',
    0xE9DC: '祈',
    0xE9DD: '季',
    0xE9DE: '稀',
    0xE9DF: '紀',
    0xE9E0: '徽',
    0xE9E1: '規',
    0xE9E2: '記',
    0xE9E3: '貴',
    0xE9E4: '起',
    0xE9E5: '軌',
    0xE9E6: '輝',
    0xE9E7: '飢',
    0xE9E8: '騎',
    0xE9E9: '鬼',
    0xE9EA: '亀',
    0xE9EB: '偽',
    0xE9EC: '儀',
    0xE9ED: '妓',
    0xE9EE: '宜',
    0xE9EF: '戯',
    0xE9F0: '技',
    0xE9F1: '擬',
    0xE9F2: '欺',
    0xE9F3: '犠',
    0xE9F4: '疑',
    0xE9F5: '祇',
    0xE9F6: '義',
    0xE9F7: '蟻',
    0xE9F8: '誼',
    0xE9F9: '議',
    0xE9FA: '掬',
    0xE9FB: '菊',
    0xE9FC: '鞠',
    0xE9FD: '吉',
    0xE9FE: '吃',
    0xE9FF: '喫',
    0xEA00: '桔',
    0xEA01: '橘',
    0xEA02: '詰',
    0xEA03: '砧',
    0xEA04: '杵',
    0xEA05: '黍',
    0xEA06: '却',
    0xEA07: '客',
    0xEA08: '脚',
    0xEA09: '虐',
    0xEA0A: '逆',
    0xEA0B: '丘',
    0xEA0C: '久',
    0xEA0D: '仇',
    0xEA0E: '休',
    0xEA0F: '及',
    0xEA10: '吸',
    0xEA11: '宮',
    0xEA12: '弓',
    0xEA13: '急',
    0xEA14: '救',
    0xEA15: '朽',
    0xEA16: '求',
    0xEA17: '汲',
    0xEA18: '泣',
    0xEA19: '灸',
    0xEA1A: '球',
    0xEA1B: '究',
    0xEA1C: '窮',
    0xEA1D: '笈',
    0xEA1E: '級',
    0xEA1F: '糾',
    0xEA20: '給',
    0xEA21: '旧',
    0xEA22: '牛',
    0xEA23: '去',
    0xEA24: '居',
    0xEA25: '巨',
    0xEA26: '拒',
    0xEA27: '拠',
    0xEA28: '挙',
    0xEA29: '渠',
    0xEA2A: '虚',
    0xEA2B: '許',
    0xEA2C: '距',
    0xEA2D: '鋸',
    0xEA2E: '漁',
    0xEA2F: '禦',
    0xEA30: '魚',
    0xEA31: '亨',
    0xEA32: '享',
    0xEA33: '京',
    0xEA34: '供',
    0xEA35: '侠',
    0xEA36: '僑',
    0xEA37: '兇',
    0xEA38: '競',
    0xEA39: '共',
    0xEA3A: '凶',
    0xEA3B: '協',
    0xEA3C: '匡',
    0xEA3D: '卿',
    0xEA3E: '叫',
    0xEA3F: '喬',
    0xEA40: '境',
    0xEA41: '峡',
    0xEA42: '強',
    0xEA43: '彊',
    0xEA44: '怯',
    0xEA45: '恐',
    0xEA46: '恭',
    0xEA47: '挟',
    0xEA48: '教',
    0xEA49: '橋',
    0xEA4A: '況',
    0xEA4B: '狂',
    0xEA4C: '狭',
    0xEA4D: '矯',
    0xEA4E: '胸',
    0xEA4F: '脅',
    0xEA50: '興',
    0xEA51: '蕎',
    0xEA52: '郷',
    0xEA53: '鏡',
    0xEA54: '響',
    0xEA55: '饗',
    0xEA56: '驚',
    0xEA57: '仰',
    0xEA58: '凝',
    0xEA59: '尭',
    0xEA5A: '暁',
    0xEA5B: '業',
    0xEA5C: '局',
    0xEA5D: '曲',
    0xEA5E: '極',
    0xEA5F: '玉',
    0xEA60: '桐',
    0xEA61: '粁',
    0xEA62: '僅',
    0xEA63: '勤',
    0xEA64: '均',
    0xEA65: '巾',
    0xEA66: '錦',
    0xEA67: '斤',
    0xEA68: '欣',
    0xEA69: '欽',
    0xEA6A: '琴',
    0xEA6B: '禁',
    0xEA6C: '禽',
    0xEA6D: '筋',
    0xEA6E: '緊',
    0xEA6F: '芹',
    0xEA70: '菌',
    0xEA71: '衿',
    0xEA72: '襟',
    0xEA73: '謹',
    0xEA74: '近',
    0xEA75: '金',
    0xEA76: '吟',
    0xEA77: '銀',
    0xEA78: '九',
    0xEA79: '倶',
    0xEA7A: '句',
    0xEA7B: '区',
    0xEA7C: '狗',
    0xEA7D: '玖',
    0xEA7E: '矩',
    0xEA7F: '苦',
    0xEA80: '躯',
    0xEA81: '駆',
    0xEA82: '駈',
    0xEA83: '駒',
    0xEA84: '具',
    0xEA85: '愚',
    0xEA86: '虞',
    0xEA87: '喰',
    0xEA88: '空',
    0xEA89: '偶',
    0xEA8A: '寓',
    0xEA8B: '遇',
    0xEA8C: '隅',
    0xEA8D: '串',
    0xEA8E: '櫛',
    0xEA8F: '釧',
    0xEA90: '屑',
    0xEA91: '屈',
    0xEA92: '掘',
    0xEA93: '窟',
    0xEA94: '沓',
    0xEA95: '靴',
    0xEA96: '轡',
    0xEA97: '窪',
    0xEA98: '熊',
    0xEA99: '隈',
    0xEA9A: '粂',
    0xEA9B: '栗',
    0xEA9C: '繰',
    0xEA9D: '桑',
    0xEA9E: '鍬',
    0xEA9F: '勲',
    0xEAA0: '君',
    0xEAA1: '薫',
    0xEAA2: '訓',
    0xEAA3: '群',
    0xEAA4: '軍',
    0xEAA5: '郡',
    0xEAA6: '卦',
    0xEAA7: '袈',
    0xEAA8: '祁',
    0xEAA9: '係',
    0xEAAA: '傾',
    0xEAAB: '刑',
    0xEAAC: '兄',
    0xEAAD: '啓',
    0xEAAE: '圭',
    0xEAAF: '珪',
    0xEAB0: '型',
    0xEAB1: '契',
    0xEAB2: '形',
    0xEAB3: '径',
    0xEAB4: '恵',
    0xEAB5: '慶',
    0xEAB6: '慧',
    0xEAB7: '憩',
    0xEAB8: '掲',
    0xEAB9: '携',
    0xEABA: '敬',
    0xEABB: '景',
    0xEABC: '桂',
    0xEABD: '渓',
    0xEABE: '畦',
    0xEABF: '稽',
    0xEAC0: '系',
    0xEAC1: '経',
    0xEAC2: '継',
    0xEAC3: '繋',
    0xEAC4: '罫',
    0xEAC5: '茎',
    0xEAC6: '荊',
    0xEAC7: '蛍',
    0xEAC8: '計',
    0xEAC9: '詣',
    0xEACA: '警',
    0xEACB: '軽',
    0xEACC: '頚',
    0xEACD: '鶏',
    0xEACE: '芸',
    0xEACF: '迎',
    0xEAD0: '鯨',
    0xEAD1: '劇',
    0xEAD2: '戟',
    0xEAD3: '撃',
    0xEAD4: '激',
    0xEAD5: '隙',
    0xEAD6: '桁',
    0xEAD7: '傑',
    0xEAD8: '欠',
    0xEAD9: '決',
    0xEADA: '潔',
    0xEADB: '穴',
    0xEADC: '結',
    0xEADD: '血',
    0xEADE: '訣',
    0xEADF: '月',
    0xEAE0: '件',
    0xEAE1: '倹',
    0xEAE2: '倦',
    0xEAE3: '健',
    0xEAE4: '兼',
    0xEAE5: '券',
    0xEAE6: '剣',
    0xEAE7: '喧',
    0xEAE8: '圏',
    0xEAE9: '堅',
    0xEAEA: '嫌',
    0xEAEB: '建',
    0xEAEC: '憲',
    0xEAED: '懸',
    0xEAEE: '拳',
    0xEAEF: '捲',
    0xEAF0: '検',
    0xEAF1: '権',
    0xEAF2: '牽',
    0xEAF3: '犬',
    0xEAF4: '献',
    0xEAF5: '研',
    0xEAF6: '硯',
    0xEAF7: '絹',
    0xEAF8: '県',
    0xEAF9: '肩',
    0xEAFA: '見',
    0xEAFB: '謙',
    0xEAFC: '賢',
    0xEAFD: '軒',
    0xEAFE: '遣',
    0xEAFF: '鍵',
    0xEB00: '険',
    0xEB01: '顕',
    0xEB02: '験',
    0xEB03: '鹸',
    0xEB04: '元',
    0xEB05: '原',
    0xEB06: '厳',
    0xEB07: '幻',
    0xEB08: '弦',
    0xEB09: '減',
    0xEB0A: '源',
    0xEB0B: '玄',
    0xEB0C: '現',
    0xEB0D: '絃',
    0xEB0E: '舷',
    0xEB0F: '言',
    0xEB10: '諺',
    0xEB11: '限',
    0xEB12: '乎',
    0xEB13: '個',
    0xEB14: '古',
    0xEB15: '呼',
    0xEB16: '固',
    0xEB17: '姑',
    0xEB18: '孤',
    0xEB19: '己',
    0xEB1A: '庫',
    0xEB1B: '弧',
    0xEB1C: '戸',
    0xEB1D: '故',
    0xEB1E: '枯',
    0xEB1F: '湖',
    0xEB20: '狐',
    0xEB21: '糊',
    0xEB22: '袴',
    0xEB23: '股',
    0xEB24: '胡',
    0xEB25: '菰',
    0xEB26: '虎',
    0xEB27: '誇',
    0xEB28: '跨',
    0xEB29: '鈷',
    0xEB2A: '雇',
    0xEB2B: '顧',
    0xEB2C: '鼓',
    0xEB2D: '五',
    0xEB2E: '互',
    0xEB2F: '伍',
    0xEB30: '午',
    0xEB31: '呉',
    0xEB32: '吾',
    0xEB33: '娯',
    0xEB34: '後',
    0xEB35: '御',
    0xEB36: '悟',
    0xEB37: '梧',
    0xEB38: '檎',
    0xEB39: '瑚',
    0xEB3A: '碁',
    0xEB3B: '語',
    0xEB3C: '誤',
    0xEB3D: '護',
    0xEB3E: '醐',
    0xEB3F: '乞',
    0xEB40: '鯉',
    0xEB41: '交',
    0xEB42: '佼',
    0xEB43: '侯',
    0xEB44: '候',
    0xEB45: '倖',
    0xEB46: '光',
    0xEB47: '公',
    0xEB48: '功',
    0xEB49: '効',
    0xEB4A: '勾',
    0xEB4B: '厚',
    0xEB4C: '口',
    0xEB4D: '向',
    0xEB4E: '后',
    0xEB4F: '喉',
    0xEB50: '坑',
    0xEB51: '垢',
    0xEB52: '好',
    0xEB53: '孔',
    0xEB54: '孝',
    0xEB55: '宏',
    0xEB56: '工',
    0xEB57: '巧',
    0xEB58: '巷',
    0xEB59: '幸',
    0xEB5A: '広',
    0xEB5B: '庚',
    0xEB5C: '康',
    0xEB5D: '弘',
    0xEB5E: '恒',
    0xEB5F: '慌',
    0xEB60: '抗',
    0xEB61: '拘',
    0xEB62: '控',
    0xEB63: '攻',
    0xEB64: '昂',
    0xEB65: '晃',
    0xEB66: '更',
    0xEB67: '杭',
    0xEB68: '校',
    0xEB69: '梗',
    0xEB6A: '構',
    0xEB6B: '江',
    0xEB6C: '洪',
    0xEB6D: '浩',
    0xEB6E: '港',
    0xEB6F: '溝',
    0xEB70: '甲',
    0xEB71: '皇',
    0xEB72: '硬',
    0xEB73: '稿',
    0xEB74: '糠',
    0xEB75: '紅',
    0xEB76: '紘',
    0xEB77: '絞',
    0xEB78: '綱',
    0xEB79: '耕',
    0xEB7A: '考',
    0xEB7B: '肯',
    0xEB7C: '肱',
    0xEB7D: '腔',
    0xEB7E: '膏',
    0xEB7F: '航',
    0xEB80: '荒',
    0xEB81: '行',
    0xEB82: '衡',
    0xEB83: '講',
    0xEB84: '貢',
    0xEB85: '購',
    0xEB86: '郊',
    0xEB87: '酵',
    0xEB88: '鉱',
    0xEB89: '砿',
    0xEB8A: '鋼',
    0xEB8B: '閤',
    0xEB8C: '降',
    0xEB8D: '項',
    0xEB8E: '香',
    0xEB8F: '高',
    0xEB90: '鴻',
    0xEB91: '剛',
    0xEB92: '劫',
    0xEB93: '号',
    0xEB94: '合',
    0xEB95: '壕',
    0xEB96: '拷',
    0xEB97: '濠',
    0xEB98: '豪',
    0xEB99: '轟',
    0xEB9A: '麹',
    0xEB9B: '克',
    0xEB9C: '刻',
    0xEB9D: '告',
    0xEB9E: '国',
    0xEB9F: '穀',
    0xEBA0: '酷',
    0xEBA1: '鵠',
    0xEBA2: '黒',
    0xEBA3: '獄',
    0xEBA4: '漉',
    0xEBA5: '腰',
    0xEBA6: '甑',
    0xEBA7: '忽',
    0xEBA8: '惚',
    0xEBA9: '骨',
    0xEBAA: '狛',
    0xEBAB: '込',
    0xEBAC: '此',
    0xEBAD: '頃',
    0xEBAE: '今',
    0xEBAF: '困',
    0xEBB0: '坤',
    0xEBB1: '墾',
    0xEBB2: '婚',
    0xEBB3: '恨',
    0xEBB4: '懇',
    0xEBB5: '昏',
    0xEBB6: '昆',
    0xEBB7: '根',
    0xEBB8: '梱',
    0xEBB9: '混',
    0xEBBA: '痕',
    0xEBBB: '紺',
    0xEBBC: '艮',
    0xEBBD: '魂',
    0xEBBE: '些',
    0xEBBF: '佐',
    0xEBC0: '叉',
    0xEBC1: '唆',
    0xEBC2: '嵯',
    0xEBC3: '左',
    0xEBC4: '差',
    0xEBC5: '査',
    0xEBC6: '沙',
    0xEBC7: '瑳',
    0xEBC8: '砂',
    0xEBC9: '詐',
    0xEBCA: '鎖',
    0xEBCB: '裟',
    0xEBCC: '坐',
    0xEBCD: '座',
    0xEBCE: '挫',
    0xEBCF: '債',
    0xEBD0: '催',
    0xEBD1: '再',
    0xEBD2: '最',
    0xEBD3: '哉',
    0xEBD4: '塞',
    0xEBD5: '妻',
    0xEBD6: '宰',
    0xEBD7: '彩',
    0xEBD8: '才',
    0xEBD9: '採',
    0xEBDA: '栽',
    0xEBDB: '歳',
    0xEBDC: '済',
    0xEBDD: '災',
    0xEBDE: '采',
    0xEBDF: '犀',
    0xEBE0: '砕',
    0xEBE1: '砦',
    0xEBE2: '祭',
    0xEBE3: '斎',
    0xEBE4: '細',
    0xEBE5: '菜',
    0xEBE6: '裁',
    0xEBE7: '載',
    0xEBE8: '際',
    0xEBE9: '剤',
    0xEBEA: '在',
    0xEBEB: '材',
    0xEBEC: '罪',
    0xEBED: '財',
    0xEBEE: '冴',
    0xEBEF: '坂',
    0xEBF0: '阪',
    0xEBF1: '堺',
    0xEBF2: '榊',
    0xEBF3: '肴',
    0xEBF4: '咲',
    0xEBF5: '崎',
    0xEBF6: '埼',
    0xEBF7: '碕',
    0xEBF8: '鷺',
    0xEBF9: '作',
    0xEBFA: '削',
    0xEBFB: '咋',
    0xEBFC: '搾',
    0xEBFD: '昨',
    0xEBFE: '朔',
    0xEBFF: '柵',
    0xEC00: '窄',
    0xEC01: '策',
    0xEC02: '索',
    0xEC03: '錯',
    0xEC04: '桜',
    0xEC05: '鮭',
    0xEC06: '笹',
    0xEC07: '匙',
    0xEC08: '冊',
    0xEC09: '刷',
    0xEC0A: '察',
    0xEC0B: '拶',
    0xEC0C: '撮',
    0xEC0D: '擦',
    0xEC0E: '札',
    0xEC0F: '殺',
    0xEC10: '薩',
    0xEC11: '雑',
    0xEC12: '皐',
    0xEC13: '鯖',
    0xEC14: '捌',
    0xEC15: '錆',
    0xEC16: '鮫',
    0xEC17: '皿',
    0xEC18: '晒',
    0xEC19: '三',
    0xEC1A: '傘',
    0xEC1B: '参',
    0xEC1C: '山',
    0xEC1D: '惨',
    0xEC1E: '撒',
    0xEC1F: '散',
    0xEC20: '桟',
    0xEC21: '燦',
    0xEC22: '珊',
    0xEC23: '産',
    0xEC24: '算',
    0xEC25: '纂',
    0xEC26: '蚕',
    0xEC27: '讃',
    0xEC28: '賛',
    0xEC29: '酸',
    0xEC2A: '餐',
    0xEC2B: '斬',
    0xEC2C: '暫',
    0xEC2D: '残',
    0xEC2E: '仕',
    0xEC2F: '仔',
    0xEC30: '伺',
    0xEC31: '使',
    0xEC32: '刺',
    0xEC33: '司',
    0xEC34: '史',
    0xEC35: '嗣',
    0xEC36: '四',
    0xEC37: '士',
    0xEC38: '始',
    0xEC39: '姉',
    0xEC3A: '姿',
    0xEC3B: '子',
    0xEC3C: '屍',
    0xEC3D: '市',
    0xEC3E: '師',
    0xEC3F: '志',
    0xEC40: '思',
    0xEC41: '指',
    0xEC42: '支',
    0xEC43: '孜',
    0xEC44: '斯',
    0xEC45: '施',
    0xEC46: '旨',
    0xEC47: '枝',
    0xEC48: '止',
    0xEC49: '死',
    0xEC4A: '氏',
    0xEC4B: '獅',
    0xEC4C: '祉',
    0xEC4D: '私',
    0xEC4E: '糸',
    0xEC4F: '紙',
    0xEC50: '紫',
    0xEC51: '肢',
    0xEC52: '脂',
    0xEC53: '至',
    0xEC54: '視',
    0xEC55: '詞',
    0xEC56: '詩',
    0xEC57: '試',
    0xEC58: '誌',
    0xEC59: '諮',
    0xEC5A: '資',
    0xEC5B: '賜',
    0xEC5C: '雌',
    0xEC5D: '飼',
    0xEC5E: '歯',
    0xEC5F: '事',
    0xEC60: '似',
    0xEC61: '侍',
    0xEC62: '児',
    0xEC63: '字',
    0xEC64: '寺',
    0xEC65: '慈',
    0xEC66: '持',
    0xEC67: '時',
    0xEC68: '次',
    0xEC69: '滋',
    0xEC6A: '治',
    0xEC6B: '爾',
    0xEC6C: '璽',
    0xEC6D: '痔',
    0xEC6E: '磁',
    0xEC6F: '示',
    0xEC70: '而',
    0xEC71: '耳',
    0xEC72: '自',
    0xEC73: '蒔',
    0xEC74: '辞',
    0xEC75: '汐',
    0xEC76: '鹿',
    0xEC77: '式',
    0xEC78: '識',
    0xEC79: '鴫',
    0xEC7A: '竺',
    0xEC7B: '軸',
    0xEC7C: '宍',
    0xEC7D: '雫',
    0xEC7E: '七',
    0xEC7F: '叱',
    0xEC80: '執',
    0xEC81: '失',
    0xEC82: '嫉',
    0xEC83: '室',
    0xEC84: '悉',
    0xEC85: '湿',
    0xEC86: '漆',
    0xEC87: '疾',
    0xEC88: '質',
    0xEC89: '実',
    0xEC8A: '蔀',
    0xEC8B: '篠',
    0xEC8C: '偲',
    0xEC8D: '柴',
    0xEC8E: '芝',
    0xEC8F: '屡',
    0xEC90: '蕊',
    0xEC91: '縞',
    0xEC92: '舎',
    0xEC93: '写',
    0xEC94: '射',
    0xEC95: '捨',
    0xEC96: '赦',
    0xEC97: '斜',
    0xEC98: '煮',
    0xEC99: '社',
    0xEC9A: '紗',
    0xEC9B: '者',
    0xEC9C: '謝',
    0xEC9D: '車',
    0xEC9E: '遮',
    0xEC9F: '蛇',
    0xECA0: '邪',
    0xECA1: '借',
    0xECA2: '勺',
    0xECA3: '尺',
    0xECA4: '杓',
    0xECA5: '灼',
    0xECA6: '爵',
    0xECA7: '酌',
    0xECA8: '釈',
    0xECA9: '錫',
    0xECAA: '若',
    0xECAB: '寂',
    0xECAC: '弱',
    0xECAD: '惹',
    0xECAE: '主',
    0xECAF: '取',
    0xECB0: '守',
    0xECB1: '手',
    0xECB2: '朱',
    0xECB3: '殊',
    0xECB4: '狩',
    0xECB5: '珠',
    0xECB6: '種',
    0xECB7: '腫',
    0xECB8: '趣',
    0xECB9: '酒',
    0xECBA: '首',
    0xECBB: '儒',
    0xECBC: '受',
    0xECBD: '呪',
    0xECBE: '寿',
    0xECBF: '授',
    0xECC0: '樹',
    0xECC1: '綬',
    0xECC2: '需',
    0xECC3: '囚',
    0xECC4: '収',
    0xECC5: '周',
    0xECC6: '宗',
    0xECC7: '就',
    0xECC8: '州',
    0xECC9: '修',
    0xECCA: '愁',
    0xECCB: '拾',
    0xECCC: '洲',
    0xECCD: '秀',
    0xECCE: '秋',
    0xECCF: '終',
    0xECD0: '繍',
    0xECD1: '習',
    0xECD2: '臭',
    0xECD3: '舟',
    0xECD4: '蒐',
    0xECD5: '衆',
    0xECD6: '襲',
    0xECD7: '讐',
    0xECD8: '蹴',
    0xECD9: '輯',
    0xECDA: '週',
    0xECDB: '酋',
    0xECDC: '酬',
    0xECDD: '集',
    0xECDE: '醜',
    0xECDF: '什',
    0xECE0: '住',
    0xECE1: '充',
    0xECE2: '十',
    0xECE3: '従',
    0xECE4: '戎',
    0xECE5: '柔',
    0xECE6: '汁',
    0xECE7: '渋',
    0xECE8: '獣',
    0xECE9: '縦',
    0xECEA: '重',
    0xECEB: '銃',
    0xECEC: '叔',
    0xECED: '夙',
    0xECEE: '宿',
    0xECEF: '淑',
    0xECF0: '祝',
    0xECF1: '縮',
    0xECF2: '粛',
    0xECF3: '塾',
    0xECF4: '熟',
    0xECF5: '出',
    0xECF6: '術',
    0xECF7: '述',
    0xECF8: '俊',
    0xECF9: '峻',
    0xECFA: '春',
    0xECFB: '瞬',
    0xECFC: '竣',
    0xECFD: '舜',
    0xECFE: '駿',
    0xECFF: '准',
    0xED00: '循',
    0xED01: '旬',
    0xED02: '楯',
    0xED03: '殉',
    0xED04: '淳',
    0xED05: '準',
    0xED06: '潤',
    0xED07: '盾',
    0xED08: '純',
    0xED09: '巡',
    0xED0A: '遵',
    0xED0B: '醇',
    0xED0C: '順',
    0xED0D: '処',
    0xED0E: '初',
    0xED0F: '所',
    0xED10: '暑',
    0xED11: '曙',
    0xED12: '渚',
    0xED13: '庶',
    0xED14: '緒',
    0xED15: '署',
    0xED16: '書',
    0xED17: '薯',
    0xED18: '藷',
    0xED19: '諸',
    0xED1A: '助',
    0xED1B: '叙',
    0xED1C: '女',
    0xED1D: '序',
    0xED1E: '徐',
    0xED1F: '恕',
    0xED20: '鋤',
    0xED21: '除',
    0xED22: '傷',
    0xED23: '償',
    0xED24: '勝',
    0xED25: '匠',
    0xED26: '升',
    0xED27: '召',
    0xED28: '哨',
    0xED29: '商',
    0xED2A: '唱',
    0xED2B: '嘗',
    0xED2C: '奨',
    0xED2D: '妾',
    0xED2E: '娼',
    0xED2F: '宵',
    0xED30: '将',
    0xED31: '小',
    0xED32: '少',
    0xED33: '尚',
    0xED34: '庄',
    0xED35: '床',
    0xED36: '廠',
    0xED37: '彰',
    0xED38: '承',
    0xED39: '抄',
    0xED3A: '招',
    0xED3B: '掌',
    0xED3C: '捷',
    0xED3D: '昇',
    0xED3E: '昌',
    0xED3F: '昭',
    0xED40: '晶',
    0xED41: '松',
    0xED42: '梢',
    0xED43: '樟',
    0xED44: '樵',
    0xED45: '沼',
    0xED46: '消',
    0xED47: '渉',
    0xED48: '湘',
    0xED49: '焼',
    0xED4A: '焦',
    0xED4B: '照',
    0xED4C: '症',
    0xED4D: '省',
    0xED4E: '硝',
    0xED4F: '礁',
    0xED50: '祥',
    0xED51: '称',
    0xED52: '章',
    0xED53: '笑',
    0xED54: '粧',
    0xED55: '紹',
    0xED56: '肖',
    0xED57: '菖',
    0xED58: '蒋',
    0xED59: '蕉',
    0xED5A: '衝',
    0xED5B: '裳',
    0xED5C: '訟',
    0xED5D: '証',
    0xED5E: '詔',
    0xED5F: '詳',
    0xED60: '象',
    0xED61: '賞',
    0xED62: '醤',
    0xED63: '鉦',
    0xED64: '鍾',
    0xED65: '鐘',
    0xED66: '障',
    0xED67: '鞘',
    0xED68: '上',
    0xED69: '丈',
    0xED6A: '丞',
    0xED6B: '乗',
    0xED6C: '冗',
    0xED6D: '剰',
    0xED6E: '城',
    0xED6F: '場',
    0xED70: '壌',
    0xED71: '嬢',
    0xED72: '常',
    0xED73: '情',
    0xED74: '擾',
    0xED75: '条',
    0xED76: '杖',
    0xED77: '浄',
    0xED78: '状',
    0xED79: '畳',
    0xED7A: '穣',
    0xED7B: '蒸',
    0xED7C: '譲',
    0xED7D: '醸',
    0xED7E: '錠',
    0xED7F: '嘱',
    0xED80: '埴',
    0xED81: '飾',
    0xED82: '拭',
    0xED83: '植',
    0xED84: '殖',
    0xED85: '燭',
    0xED86: '織',
    0xED87: '職',
    0xED88: '色',
    0xED89: '触',
    0xED8A: '食',
    0xED8B: '蝕',
    0xED8C: '辱',
    0xED8D: '尻',
    0xED8E: '伸',
    0xED8F: '信',
    0xED90: '侵',
    0xED91: '唇',
    0xED92: '娠',
    0xED93: '寝',
    0xED94: '審',
    0xED95: '心',
    0xED96: '慎',
    0xED97: '振',
    0xED98: '新',
    0xED99: '晋',
    0xED9A: '森',
    0xED9B: '榛',
    0xED9C: '浸',
    0xED9D: '深',
    0xED9E: '申',
    0xED9F: '疹',
    0xEDA0: '真',
    0xEDA1: '神',
    0xEDA2: '秦',
    0xEDA3: '紳',
    0xEDA4: '臣',
    0xEDA5: '芯',
    0xEDA6: '薪',
    0xEDA7: '親',
    0xEDA8: '診',
    0xEDA9: '身',
    0xEDAA: '辛',
    0xEDAB: '進',
    0xEDAC: '針',
    0xEDAD: '震',
    0xEDAE: '人',
    0xEDAF: '仁',
    0xEDB0: '刃',
    0xEDB1: '塵',
    0xEDB2: '壬',
    0xEDB3: '尋',
    0xEDB4: '甚',
    0xEDB5: '尽',
    0xEDB6: '腎',
    0xEDB7: '訊',
    0xEDB8: '迅',
    0xEDB9: '陣',
    0xEDBA: '靭',
    0xEDBB: '笥',
    0xEDBC: '諏',
    0xEDBD: '須',
    0xEDBE: '酢',
    0xEDBF: '図',
    0xEDC0: '厨',
    0xEDC1: '逗',
    0xEDC2: '吹',
    0xEDC3: '垂',
    0xEDC4: '帥',
    0xEDC5: '推',
    0xEDC6: '水',
    0xEDC7: '炊',
    0xEDC8: '睡',
    0xEDC9: '粋',
    0xEDCA: '翠',
    0xEDCB: '衰',
    0xEDCC: '遂',
    0xEDCD: '酔',
    0xEDCE: '錐',
    0xEDCF: '錘',
    0xEDD0: '随',
    0xEDD1: '瑞',
    0xEDD2: '髄',
    0xEDD3: '崇',
    0xEDD4: '嵩',
    0xEDD5: '数',
    0xEDD6: '枢',
    0xEDD7: '趨',
    0xEDD8: '雛',
    0xEDD9: '据',
    0xEDDA: '杉',
    0xEDDB: '椙',
    0xEDDC: '菅',
    0xEDDD: '頗',
    0xEDDE: '雀',
    0xEDDF: '裾',
    0xEDE0: '澄',
    0xEDE1: '摺',
    0xEDE2: '寸',
    0xEDE3: '世',
    0xEDE4: '瀬',
    0xEDE5: '畝',
    0xEDE6: '是',
    0xEDE7: '凄',
    0xEDE8: '制',
    0xEDE9: '勢',
    0xEDEA: '姓',
    0xEDEB: '征',
    0xEDEC: '性',
    0xEDED: '成',
    0xEDEE: '政',
    0xEDEF: '整',
    0xEDF0: '星',
    0xEDF1: '晴',
    0xEDF2: '棲',
    0xEDF3: '栖',
    0xEDF4: '正',
    0xEDF5: '清',
    0xEDF6: '牲',
    0xEDF7: '生',
    0xEDF8: '盛',
    0xEDF9: '精',
    0xEDFA: '聖',
    0xEDFB: '声',
    0xEDFC: '製',
    0xEDFD: '西',
    0xEDFE: '誠',
    0xEDFF: '誓',
    0xEE00: '請',
    0xEE01: '逝',
    0xEE02: '醒',
    0xEE03: '青',
    0xEE04: '静',
    0xEE05: '斉',
    0xEE06: '税',
    0xEE07: '脆',
    0xEE08: '隻',
    0xEE09: '席',
    0xEE0A: '惜',
    0xEE0B: '戚',
    0xEE0C: '斥',
    0xEE0D: '昔',
    0xEE0E: '析',
    0xEE0F: '石',
    0xEE10: '積',
    0xEE11: '籍',
    0xEE12: '績',
    0xEE13: '脊',
    0xEE14: '責',
    0xEE15: '赤',
    0xEE16: '跡',
    0xEE17: '蹟',
    0xEE18: '碩',
    0xEE19: '切',
    0xEE1A: '拙',
    0xEE1B: '接',
    0xEE1C: '摂',
    0xEE1D: '折',
    0xEE1E: '設',
    0xEE1F: '窃',
    0xEE20: '節',
    0xEE21: '説',
    0xEE22: '雪',
    0xEE23: '絶',
    0xEE24: '舌',
    0xEE25: '蝉',
    0xEE26: '仙',
    0xEE27: '先',
    0xEE28: '千',
    0xEE29: '占',
    0xEE2A: '宣',
    0xEE2B: '専',
    0xEE2C: '尖',
    0xEE2D: '川',
    0xEE2E: '戦',
    0xEE2F: '扇',
    0xEE30: '撰',
    0xEE31: '栓',
    0xEE32: '栴',
    0xEE33: '泉',
    0xEE34: '浅',
    0xEE35: '洗',
    0xEE36: '染',
    0xEE37: '潜',
    0xEE38: '煎',
    0xEE39: '煽',
    0xEE3A: '旋',
    0xEE3B: '穿',
    0xEE3C: '箭',
    0xEE3D: '線',
    0xEE3E: '繊',
    0xEE3F: '羨',
    0xEE40: '腺',
    0xEE41: '舛',
    0xEE42: '船',
    0xEE43: '薦',
    0xEE44: '詮',
    0xEE45: '賎',
    0xEE46: '践',
    0xEE47: '選',
    0xEE48: '遷',
    0xEE49: '銭',
    0xEE4A: '銑',
    0xEE4B: '閃',
    0xEE4C: '鮮',
    0xEE4D: '前',
    0xEE4E: '善',
    0xEE4F: '漸',
    0xEE50: '然',
    0xEE51: '全',
    0xEE52: '禅',
    0xEE53: '繕',
    0xEE54: '膳',
    0xEE55: '糎',
    0xEE56: '噌',
    0xEE57: '塑',
    0xEE58: '岨',
    0xEE59: '措',
    0xEE5A: '曾',
    0xEE5B: '曽',
    0xEE5C: '楚',
    0xEE5D: '狙',
    0xEE5E: '疏',
    0xEE5F: '疎',
    0xEE60: '礎',
    0xEE61: '祖',
    0xEE62: '租',
    0xEE63: '粗',
    0xEE64: '素',
    0xEE65: '組',
    0xEE66: '蘇',
    0xEE67: '訴',
    0xEE68: '阻',
    0xEE69: '遡',
    0xEE6A: '鼠',
    0xEE6B: '僧',
    0xEE6C: '創',
    0xEE6D: '双',
    0xEE6E: '叢',
    0xEE6F: '倉',
    0xEE70: '喪',
    0xEE71: '壮',
    0xEE72: '奏',
    0xEE73: '爽',
    0xEE74: '宋',
    0xEE75: '層',
    0xEE76: '匝',
    0xEE77: '惣',
    0xEE78: '想',
    0xEE79: '捜',
    0xEE7A: '掃',
    0xEE7B: '挿',
    0xEE7C: '掻',
    0xEE7D: '操',
    0xEE7E: '早',
    0xEE7F: '曹',
    0xEE80: '巣',
    0xEE81: '槍',
    0xEE82: '槽',
    0xEE83: '漕',
    0xEE84: '燥',
    0xEE85: '争',
    0xEE86: '痩',
    0xEE87: '相',
    0xEE88: '窓',
    0xEE89: '糟',
    0xEE8A: '総',
    0xEE8B: '綜',
    0xEE8C: '聡',
    0xEE8D: '草',
    0xEE8E: '荘',
    0xEE8F: '葬',
    0xEE90: '蒼',
    0xEE91: '藻',
    0xEE92: '装',
    0xEE93: '走',
    0xEE94: '送',
    0xEE95: '遭',
    0xEE96: '鎗',
    0xEE97: '霜',
    0xEE98: '騒',
    0xEE99: '像',
    0xEE9A: '増',
    0xEE9B: '憎',
    0xEE9C: '臓',
    0xEE9D: '蔵',
    0xEE9E: '贈',
    0xEE9F: '造',
    0xEEA0: '促',
    0xEEA1: '側',
    0xEEA2: '則',
    0xEEA3: '即',
    0xEEA4: '息',
    0xEEA5: '捉',
    0xEEA6: '束',
    0xEEA7: '測',
    0xEEA8: '足',
    0xEEA9: '速',
    0xEEAA: '俗',
    0xEEAB: '属',
    0xEEAC: '賊',
    0xEEAD: '族',
    0xEEAE: '続',
    0xEEAF: '卒',
    0xEEB0: '袖',
    0xEEB1: '其',
    0xEEB2: '揃',
    0xEEB3: '存',
    0xEEB4: '孫',
    0xEEB5: '尊',
    0xEEB6: '損',
    0xEEB7: '村',
    0xEEB8: '遜',
    0xEEB9: '他',
    0xEEBA: '多',
    0xEEBB: '太',
    0xEEBC: '汰',
    0xEEBD: '詑',
    0xEEBE: '唾',
    0xEEBF: '堕',
    0xEEC0: '妥',
    0xEEC1: '惰',
    0xEEC2: '打',
    0xEEC3: '柁',
    0xEEC4: '舵',
    0xEEC5: '楕',
    0xEEC6: '陀',
    0xEEC7: '駄',
    0xEEC8: '騨',
    0xEEC9: '体',
    0xEECA: '堆',
    0xEECB: '対',
    0xEECC: '耐',
    0xEECD: '岱',
    0xEECE: '帯',
    0xEECF: '待',
    0xEED0: '怠',
    0xEED1: '態',
    0xEED2: '戴',
    0xEED3: '替',
    0xEED4: '泰',
    0xEED5: '滞',
    0xEED6: '胎',
    0xEED7: '腿',
    0xEED8: '苔',
    0xEED9: '袋',
    0xEEDA: '貸',
    0xEEDB: '退',
    0xEEDC: '逮',
    0xEEDD: '隊',
    0xEEDE: '黛',
    0xEEDF: '鯛',
    0xEEE0: '代',
    0xEEE1: '台',
    0xEEE2: '大',
    0xEEE3: '第',
    0xEEE4: '醍',
    0xEEE5: '題',
    0xEEE6: '鷹',
    0xEEE7: '滝',
    0xEEE8: '瀧',
    0xEEE9: '卓',
    0xEEEA: '啄',
    0xEEEB: '宅',
    0xEEEC: '托',
    0xEEED: '択',
    0xEEEE: '拓',
    0xEEEF: '沢',
    0xEEF0: '濯',
    0xEEF1: '琢',
    0xEEF2: '託',
    0xEEF3: '鐸',
    0xEEF4: '濁',
    0xEEF5: '諾',
    0xEEF6: '茸',
    0xEEF7: '凧',
    0xEEF8: '蛸',
    0xEEF9: '只',
    0xEEFA: '叩',
    0xEEFB: '但',
    0xEEFC: '達',
    0xEEFD: '辰',
    0xEEFE: '奪',
    0xEEFF: '脱',
    0xEF00: '巽',
    0xEF01: '竪',
    0xEF02: '辿',
    0xEF03: '棚',
    0xEF04: '谷',
    0xEF05: '狸',
    0xEF06: '鱈',
    0xEF07: '樽',
    0xEF08: '誰',
    0xEF09: '丹',
    0xEF0A: '単',
    0xEF0B: '嘆',
    0xEF0C: '坦',
    0xEF0D: '担',
    0xEF0E: '探',
    0xEF0F: '旦',
    0xEF10: '歎',
    0xEF11: '淡',
    0xEF12: '湛',
    0xEF13: '炭',
    0xEF14: '短',
    0xEF15: '端',
    0xEF16: '箪',
    0xEF17: '綻',
    0xEF18: '耽',
    0xEF19: '胆',
    0xEF1A: '蛋',
    0xEF1B: '誕',
    0xEF1C: '鍛',
    0xEF1D: '団',
    0xEF1E: '壇',
    0xEF1F: '弾',
    0xEF20: '断',
    0xEF21: '暖',
    0xEF22: '檀',
    0xEF23: '段',
    0xEF24: '男',
    0xEF25: '談',
    0xEF26: '値',
    0xEF27: '知',
    0xEF28: '地',
    0xEF29: '弛',
    0xEF2A: '恥',
    0xEF2B: '智',
    0xEF2C: '池',
    0xEF2D: '痴',
    0xEF2E: '稚',
    0xEF2F: '置',
    0xEF30: '致',
    0xEF31: '蜘',
    0xEF32: '遅',
    0xEF33: '馳',
    0xEF34: '築',
    0xEF35: '畜',
    0xEF36: '竹',
    0xEF37: '筑',
    0xEF38: '蓄',
    0xEF39: '逐',
    0xEF3A: '秩',
    0xEF3B: '窒',
    0xEF3C: '茶',
    0xEF3D: '嫡',
    0xEF3E: '着',
    0xEF3F: '中',
    0xEF40: '仲',
    0xEF41: '宙',
    0xEF42: '忠',
    0xEF43: '抽',
    0xEF44: '昼',
    0xEF45: '柱',
    0xEF46: '注',
    0xEF47: '虫',
    0xEF48: '衷',
    0xEF49: '註',
    0xEF4A: '酎',
    0xEF4B: '鋳',
    0xEF4C: '駐',
    0xEF4D: '樗',
    0xEF4E: '瀦',
    0xEF4F: '猪',
    0xEF50: '苧',
    0xEF51: '著',
    0xEF52: '貯',
    0xEF53: '丁',
    0xEF54: '兆',
    0xEF55: '凋',
    0xEF56: '喋',
    0xEF57: '寵',
    0xEF58: '帖',
    0xEF59: '帳',
    0xEF5A: '庁',
    0xEF5B: '弔',
    0xEF5C: '張',
    0xEF5D: '彫',
    0xEF5E: '徴',
    0xEF5F: '懲',
    0xEF60: '挑',
    0xEF61: '暢',
    0xEF62: '朝',
    0xEF63: '潮',
    0xEF64: '牒',
    0xEF65: '町',
    0xEF66: '眺',
    0xEF67: '聴',
    0xEF68: '脹',
    0xEF69: '腸',
    0xEF6A: '蝶',
    0xEF6B: '調',
    0xEF6C: '諜',
    0xEF6D: '超',
    0xEF6E: '跳',
    0xEF6F: '銚',
    0xEF70: '長',
    0xEF71: '頂',
    0xEF72: '鳥',
    0xEF73: '勅',
    0xEF74: '捗',
    0xEF75: '直',
    0xEF76: '朕',
    0xEF77: '沈',
    0xEF78: '珍',
    0xEF79: '賃',
    0xEF7A: '鎮',
    0xEF7B: '陳',
    0xEF7C: '津',
    0xEF7D: '墜',
    0xEF7E: '椎',
    0xEF7F: '槌',
    0xEF80: '追',
    0xEF81: '鎚',
    0xEF82: '痛',
    0xEF83: '通',
    0xEF84: '塚',
    0xEF85: '栂',
    0xEF86: '掴',
    0xEF87: '槻',
    0xEF88: '佃',
    0xEF89: '漬',
    0xEF8A: '柘',
    0xEF8B: '辻',
    0xEF8C: '蔦',
    0xEF8D: '綴',
    0xEF8E: '鍔',
    0xEF8F: '椿',
    0xEF90: '潰',
    0xEF91: '坪',
    0xEF92: '壷',
    0xEF93: '嬬',
    0xEF94: '紬',
    0xEF95: '爪',
    0xEF96: '吊',
    0xEF97: '釣',
    0xEF98: '鶴',
    0xEF99: '亭',
    0xEF9A: '低',
    0xEF9B: '停',
    0xEF9C: '偵',
    0xEF9D: '剃',
    0xEF9E: '貞',
    0xEF9F: '呈',
    0xEFA0: '堤',
    0xEFA1: '定',
    0xEFA2: '帝',
    0xEFA3: '底',
    0xEFA4: '庭',
    0xEFA5: '廷',
    0xEFA6: '弟',
    0xEFA7: '悌',
    0xEFA8: '抵',
    0xEFA9: '挺',
    0xEFAA: '提',
    0xEFAB: '梯',
    0xEFAC: '汀',
    0xEFAD: '碇',
    0xEFAE: '禎',
    0xEFAF: '程',
    0xEFB0: '締',
    0xEFB1: '艇',
    0xEFB2: '訂',
    0xEFB3: '諦',
    0xEFB4: '蹄',
    0xEFB5: '逓',
    0xEFB6: '邸',
    0xEFB7: '鄭',
    0xEFB8: '釘',
    0xEFB9: '鼎',
    0xEFBA: '泥',
    0xEFBB: '摘',
    0xEFBC: '擢',
    0xEFBD: '敵',
    0xEFBE: '滴',
    0xEFBF: '的',
    0xEFC0: '笛',
    0xEFC1: '適',
    0xEFC2: '鏑',
    0xEFC3: '溺',
    0xEFC4: '哲',
    0xEFC5: '徹',
    0xEFC6: '撤',
    0xEFC7: '轍',
    0xEFC8: '迭',
    0xEFC9: '鉄',
    0xEFCA: '典',
    0xEFCB: '填',
    0xEFCC: '天',
    0xEFCD: '展',
    0xEFCE: '店',
    0xEFCF: '添',
    0xEFD0: '纏',
    0xEFD1: '甜',
    0xEFD2: '貼',
    0xEFD3: '転',
    0xEFD4: '顛',
    0xEFD5: '点',
    0xEFD6: '伝',
    0xEFD7: '殿',
    0xEFD8: '澱',
    0xEFD9: '田',
    0xEFDA: '電',
    0xEFDB: '兎',
    0xEFDC: '吐',
    0xEFDD: '堵',
    0xEFDE: '塗',
    0xEFDF: '妬',
    0xEFE0: '屠',
    0xEFE1: '徒',
    0xEFE2: '斗',
    0xEFE3: '杜',
    0xEFE4: '渡',
    0xEFE5: '登',
    0xEFE6: '菟',
    0xEFE7: '賭',
    0xEFE8: '途',
    0xEFE9: '都',
    0xEFEA: '鍍',
    0xEFEB: '砥',
    0xEFEC: '砺',
    0xEFED: '努',
    0xEFEE: '度',
    0xEFEF: '土',
    0xEFF0: '奴',
    0xEFF1: '怒',
    0xEFF2: '倒',
    0xEFF3: '党',
    0xEFF4: '冬',
    0xEFF5: '凍',
    0xEFF6: '刀',
    0xEFF7: '唐',
    0xEFF8: '塔',
    0xEFF9: '塘',
    0xEFFA: '套',
    0xEFFB: '宕',
    0xEFFC: '島',
    0xEFFD: '嶋',
    0xEFFE: '悼',
    0xEFFF: '投',
    0xF000: '搭',
    0xF001: '東',
    0xF002: '桃',
    0xF003: '梼',
    0xF004: '棟',
    0xF005: '盗',
    0xF006: '淘',
    0xF007: '湯',
    0xF008: '涛',
    0xF009: '灯',
    0xF00A: '燈',
    0xF00B: '当',
    0xF00C: '痘',
    0xF00D: '祷',
    0xF00E: '等',
    0xF00F: '答',
    0xF010: '筒',
    0xF011: '糖',
    0xF012: '統',
    0xF013: '到',
    0xF014: '董',
    0xF015: '蕩',
    0xF016: '藤',
    0xF017: '討',
    0xF018: '謄',
    0xF019: '豆',
    0xF01A: '踏',
    0xF01B: '逃',
    0xF01C: '透',
    0xF01D: '鐙',
    0xF01E: '陶',
    0xF01F: '頭',
    0xF020: '騰',
    0xF021: '闘',
    0xF022: '働',
    0xF023: '動',
    0xF024: '同',
    0xF025: '堂',
    0xF026: '導',
    0xF027: '憧',
    0xF028: '撞',
    0xF029: '洞',
    0xF02A: '瞳',
    0xF02B: '童',
    0xF02C: '胴',
    0xF02D: '萄',
    0xF02E: '道',
    0xF02F: '銅',
    0xF030: '峠',
    0xF031: '鴇',
    0xF032: '匿',
    0xF033: '得',
    0xF034: '徳',
    0xF035: '涜',
    0xF036: '特',
    0xF037: '督',
    0xF038: '禿',
    0xF039: '篤',
    0xF03A: '毒',
    0xF03B: '独',
    0xF03C: '読',
    0xF03D: '栃',
    0xF03E: '橡',
    0xF03F: '凸',
    0xF040: '突',
    0xF041: '椴',
    0xF042: '届',
    0xF043: '鳶',
    0xF044: '苫',
    0xF045: '寅',
    0xF046: '酉',
    0xF047: '瀞',
    0xF048: '噸',
    0xF049: '屯',
    0xF04A: '惇',
    0xF04B: '敦',
    0xF04C: '沌',
    0xF04D: '豚',
    0xF04E: '遁',
    0xF04F: '頓',
    0xF050: '呑',
    0xF051: '曇',
    0xF052: '鈍',
    0xF053: '奈',
    0xF054: '那',
    0xF055: '内',
    0xF056: '乍',
    0xF057: '凪',
    0xF058: '薙',
    0xF059: '謎',
    0xF05A: '灘',
    0xF05B: '捺',
    0xF05C: '鍋',
    0xF05D: '楢',
    0xF05E: '馴',
    0xF05F: '縄',
    0xF060: '畷',
    0xF061: '南',
    0xF062: '楠',
    0xF063: '軟',
    0xF064: '難',
    0xF065: '汝',
    0xF066: '二',
    0xF067: '尼',
    0xF068: '弐',
    0xF069: '迩',
    0xF06A: '匂',
    0xF06B: '賑',
    0xF06C: '肉',
    0xF06D: '虹',
    0xF06E: '廿',
    0xF06F: '日',
    0xF070: '乳',
    0xF071: '入',
    0xF072: '如',
    0xF073: '尿',
    0xF074: '韮',
    0xF075: '任',
    0xF076: '妊',
    0xF077: '忍',
    0xF078: '認',
    0xF079: '濡',
    0xF07A: '禰',
    0xF07B: '祢',
    0xF07C: '寧',
    0xF07D: '葱',
    0xF07E: '猫',
    0xF07F: '熱',
    0xF080: '年',
    0xF081: '念',
    0xF082: '捻',
    0xF083: '撚',
    0xF084: '燃',
    0xF085: '粘',
    0xF086: '乃',
    0xF087: '廼',
    0xF088: '之',
    0xF089: '埜',
    0xF08A: '嚢',
    0xF08B: '悩',
    0xF08C: '濃',
    0xF08D: '納',
    0xF08E: '能',
    0xF08F: '脳',
    0xF090: '膿',
    0xF091: '農',
    0xF092: '覗',
    0xF093: '蚤',
    0xF094: '巴',
    0xF095: '把',
    0xF096: '播',
    0xF097: '覇',
    0xF098: '杷',
    0xF099: '波',
    0xF09A: '派',
    0xF09B: '琶',
    0xF09C: '破',
    0xF09D: '婆',
    0xF09E: '罵',
    0xF09F: '芭',
    0xF0A0: '馬',
    0xF0A1: '俳',
    0xF0A2: '廃',
    0xF0A3: '拝',
    0xF0A4: '排',
    0xF0A5: '敗',
    0xF0A6: '杯',
    0xF0A7: '盃',
    0xF0A8: '牌',
    0xF0A9: '背',
    0xF0AA: '肺',
    0xF0AB: '輩',
    0xF0AC: '配',
    0xF0AD: '倍',
    0xF0AE: '培',
    0xF0AF: '媒',
    0xF0B0: '梅',
    0xF0B1: '楳',
    0xF0B2: '煤',
    0xF0B3: '狽',
    0xF0B4: '買',
    0xF0B5: '売',
    0xF0B6: '賠',
    0xF0B7: '陪',
    0xF0B8: '這',
    0xF0B9: '蝿',
    0xF0BA: '秤',
    0xF0BB: '矧',
    0xF0BC: '萩',
    0xF0BD: '伯',
    0xF0BE: '剥',
    0xF0BF: '博',
    0xF0C0: '拍',
    0xF0C1: '柏',
    0xF0C2: '泊',
    0xF0C3: '白',
    0xF0C4: '箔',
    0xF0C5: '粕',
    0xF0C6: '舶',
    0xF0C7: '薄',
    0xF0C8: '迫',
    0xF0C9: '曝',
    0xF0CA: '漠',
    0xF0CB: '爆',
    0xF0CC: '縛',
    0xF0CD: '莫',
    0xF0CE: '駁',
    0xF0CF: '麦',
    0xF0D0: '函',
    0xF0D1: '箱',
    0xF0D2: '硲',
    0xF0D3: '箸',
    0xF0D4: '肇',
    0xF0D5: '筈',
    0xF0D6: '櫨',
    0xF0D7: '幡',
    0xF0D8: '肌',
    0xF0D9: '畑',
    0xF0DA: '畠',
    0xF0DB: '八',
    0xF0DC: '鉢',
    0xF0DD: '溌',
    0xF0DE: '発',
    0xF0DF: '醗',
    0xF0E0: '髪',
    0xF0E1: '伐',
    0xF0E2: '罰',
    0xF0E3: '抜',
    0xF0E4: '筏',
    0xF0E5: '閥',
    0xF0E6: '鳩',
    0xF0E7: '噺',
    0xF0E8: '塙',
    0xF0E9: '蛤',
    0xF0EA: '隼',
    0xF0EB: '伴',
    0xF0EC: '判',
    0xF0ED: '半',
    0xF0EE: '反',
    0xF0EF: '叛',
    0xF0F0: '帆',
    0xF0F1: '搬',
    0xF0F2: '斑',
    0xF0F3: '板',
    0xF0F4: '氾',
    0xF0F5: '汎',
    0xF0F6: '版',
    0xF0F7: '犯',
    0xF0F8: '班',
    0xF0F9: '畔',
    0xF0FA: '繁',
    0xF0FB: '般',
    0xF0FC: '藩',
    0xF0FD: '販',
    0xF0FE: '範',
    0xF0FF: '釆',
    0xF100: '煩',
    0xF101: '頒',
    0xF102: '飯',
    0xF103: '挽',
    0xF104: '晩',
    0xF105: '番',
    0xF106: '盤',
    0xF107: '磐',
    0xF108: '蕃',
    0xF109: '蛮',
    0xF10A: '匪',
    0xF10B: '卑',
    0xF10C: '否',
    0xF10D: '妃',
    0xF10E: '庇',
    0xF10F: '彼',
    0xF110: '悲',
    0xF111: '扉',
    0xF112: '批',
    0xF113: '披',
    0xF114: '斐',
    0xF115: '比',
    0xF116: '泌',
    0xF117: '疲',
    0xF118: '皮',
    0xF119: '碑',
    0xF11A: '秘',
    0xF11B: '緋',
    0xF11C: '罷',
    0xF11D: '肥',
    0xF11E: '被',
    0xF11F: '誹',
    0xF120: '費',
    0xF121: '避',
    0xF122: '非',
    0xF123: '飛',
    0xF124: '樋',
    0xF125: '簸',
    0xF126: '備',
    0xF127: '尾',
    0xF128: '微',
    0xF129: '枇',
    0xF12A: '毘',
    0xF12B: '琵',
    0xF12C: '眉',
    0xF12D: '美',
    0xF12E: '鼻',
    0xF12F: '柊',
    0xF130: '稗',
    0xF131: '匹',
    0xF132: '疋',
    0xF133: '髭',
    0xF134: '彦',
    0xF135: '膝',
    0xF136: '菱',
    0xF137: '肘',
    0xF138: '弼',
    0xF139: '必',
    0xF13A: '畢',
    0xF13B: '筆',
    0xF13C: '逼',
    0xF13D: '桧',
    0xF13E: '姫',
    0xF13F: '媛',
    0xF140: '紐',
    0xF141: '百',
    0xF142: '謬',
    0xF143: '俵',
    0xF144: '彪',
    0xF145: '標',
    0xF146: '氷',
    0xF147: '漂',
    0xF148: '瓢',
    0xF149: '票',
    0xF14A: '表',
    0xF14B: '評',
    0xF14C: '豹',
    0xF14D: '廟',
    0xF14E: '描',
    0xF14F: '病',
    0xF150: '秒',
    0xF151: '苗',
    0xF152: '錨',
    0xF153: '鋲',
    0xF154: '蒜',
    0xF155: '蛭',
    0xF156: '鰭',
    0xF157: '品',
    0xF158: '彬',
    0xF159: '斌',
    0xF15A: '浜',
    0xF15B: '瀕',
    0xF15C: '貧',
    0xF15D: '賓',
    0xF15E: '頻',
    0xF15F: '敏',
    0xF160: '瓶',
    0xF161: '不',
    0xF162: '付',
    0xF163: '埠',
    0xF164: '夫',
    0xF165: '婦',
    0xF166: '富',
    0xF167: '冨',
    0xF168: '布',
    0xF169: '府',
    0xF16A: '怖',
    0xF16B: '扶',
    0xF16C: '敷',
    0xF16D: '斧',
    0xF16E: '普',
    0xF16F: '浮',
    0xF170: '父',
    0xF171: '符',
    0xF172: '腐',
    0xF173: '膚',
    0xF174: '芙',
    0xF175: '譜',
    0xF176: '負',
    0xF177: '賦',
    0xF178: '赴',
    0xF179: '阜',
    0xF17A: '附',
    0xF17B: '侮',
    0xF17C: '撫',
    0xF17D: '武',
    0xF17E: '舞',
    0xF17F: '葡',
    0xF180: '蕪',
    0xF181: '部',
    0xF182: '封',
    0xF183: '楓',
    0xF184: '風',
    0xF185: '葺',
    0xF186: '蕗',
    0xF187: '伏',
    0xF188: '副',
    0xF189: '復',
    0xF18A: '幅',
    0xF18B: '服',
    0xF18C: '福',
    0xF18D: '腹',
    0xF18E: '複',
    0xF18F: '覆',
    0xF190: '淵',
    0xF191: '弗',
    0xF192: '払',
    0xF193: '沸',
    0xF194: '仏',
    0xF195: '物',
    0xF196: '鮒',
    0xF197: '分',
    0xF198: '吻',
    0xF199: '噴',
    0xF19A: '墳',
    0xF19B: '憤',
    0xF19C: '扮',
    0xF19D: '焚',
    0xF19E: '奮',
    0xF19F: '粉',
    0xF1A0: '糞',
    0xF1A1: '紛',
    0xF1A2: '雰',
    0xF1A3: '文',
    0xF1A4: '聞',
    0xF1A5: '丙',
    0xF1A6: '併',
    0xF1A7: '兵',
    0xF1A8: '塀',
    0xF1A9: '幣',
    0xF1AA: '平',
    0xF1AB: '弊',
    0xF1AC: '柄',
    0xF1AD: '並',
    0xF1AE: '蔽',
    0xF1AF: '閉',
    0xF1B0: '陛',
    0xF1B1: '米',
    0xF1B2: '頁',
    0xF1B3: '僻',
    0xF1B4: '壁',
    0xF1B5: '癖',
    0xF1B6: '碧',
    0xF1B7: '別',
    0xF1B8: '瞥',
    0xF1B9: '蔑',
    0xF1BA: '箆',
    0xF1BB: '偏',
    0xF1BC: '変',
    0xF1BD: '片',
    0xF1BE: '篇',
    0xF1BF: '編',
    0xF1C0: '辺',
    0xF1C1: '返',
    0xF1C2: '遍',
    0xF1C3: '便',
    0xF1C4: '勉',
    0xF1C5: '娩',
    0xF1C6: '弁',
    0xF1C7: '鞭',
    0xF1C8: '保',
    0xF1C9: '舗',
    0xF1CA: '鋪',
    0xF1CB: '圃',
    0xF1CC: '捕',
    0xF1CD: '歩',
    0xF1CE: '甫',
    0xF1CF: '補',
    0xF1D0: '輔',
    0xF1D1: '穂',
    0xF1D2: '募',
    0xF1D3: '墓',
    0xF1D4: '慕',
    0xF1D5: '戊',
    0xF1D6: '暮',
    0xF1D7: '母',
    0xF1D8: '簿',
    0xF1D9: '菩',
    0xF1DA: '倣',
    0xF1DB: '俸',
    0xF1DC: '包',
    0xF1DD: '呆',
    0xF1DE: '報',
    0xF1DF: '奉',
    0xF1E0: '宝',
    0xF1E1: '峰',
    0xF1E2: '峯',
    0xF1E3: '崩',
    0xF1E4: '庖',
    0xF1E5: '抱',
    0xF1E6: '捧',
    0xF1E7: '放',
    0xF1E8: '方',
    0xF1E9: '朋',
    0xF1EA: '法',
    0xF1EB: '泡',
    0xF1EC: '烹',
    0xF1ED: '砲',
    0xF1EE: '縫',
    0xF1EF: '胞',
    0xF1F0: '芳',
    0xF1F1: '萌',
    0xF1F2: '蓬',
    0xF1F3: '蜂',
    0xF1F4: '褒',
    0xF1F5: '訪',
    0xF1F6: '豊',
    0xF1F7: '邦',
    0xF1F8: '鋒',
    0xF1F9: '飽',
    0xF1FA: '鳳',
    0xF1FB: '鵬',
    0xF1FC: '乏',
    0xF1FD: '亡',
    0xF1FE: '傍',
    0xF1FF: '剖',
    0xF200: '坊',
    0xF201: '妨',
    0xF202: '帽',
    0xF203: '忘',
    0xF204: '忙',
    0xF205: '房',
    0xF206: '暴',
    0xF207: '望',
    0xF208: '某',
    0xF209: '棒',
    0xF20A: '冒',
    0xF20B: '紡',
    0xF20C: '肪',
    0xF20D: '膨',
    0xF20E: '謀',
    0xF20F: '貌',
    0xF210: '貿',
    0xF211: '鉾',
    0xF212: '防',
    0xF213: '吠',
    0xF214: '頬',
    0xF215: '北',
    0xF216: '僕',
    0xF217: '卜',
    0xF218: '墨',
    0xF219: '撲',
    0xF21A: '朴',
    0xF21B: '牧',
    0xF21C: '睦',
    0xF21D: '穆',
    0xF21E: '釦',
    0xF21F: '勃',
    0xF220: '没',
    0xF221: '殆',
    0xF222: '堀',
    0xF223: '幌',
    0xF224: '奔',
    0xF225: '本',
    0xF226: '翻',
    0xF227: '凡',
    0xF228: '盆',
    0xF229: '摩',
    0xF22A: '磨',
    0xF22B: '魔',
    0xF22C: '麻',
    0xF22D: '埋',
    0xF22E: '妹',
    0xF22F: '昧',
    0xF230: '枚',
    0xF231: '毎',
    0xF232: '哩',
    0xF233: '槙',
    0xF234: '幕',
    0xF235: '膜',
    0xF236: '枕',
    0xF237: '鮪',
    0xF238: '柾',
    0xF239: '鱒',
    0xF23A: '桝',
    0xF23B: '亦',
    0xF23C: '俣',
    0xF23D: '又',
    0xF23E: '抹',
    0xF23F: '末',
    0xF240: '沫',
    0xF241: '迄',
    0xF242: '侭',
    0xF243: '繭',
    0xF244: '麿',
    0xF245: '万',
    0xF246: '慢',
    0xF247: '満',
    0xF248: '漫',
    0xF249: '蔓',
    0xF24A: '味',
    0xF24B: '未',
    0xF24C: '魅',
    0xF24D: '巳',
    0xF24E: '箕',
    0xF24F: '岬',
    0xF250: '密',
    0xF251: '蜜',
    0xF252: '湊',
    0xF253: '蓑',
    0xF254: '稔',
    0xF255: '脈',
    0xF256: '妙',
    0xF257: '粍',
    0xF258: '民',
    0xF259: '眠',
    0xF25A: '務',
    0xF25B: '夢',
    0xF25C: '無',
    0xF25D: '牟',
    0xF25E: '矛',
    0xF25F: '霧',
    0xF260: '鵡',
    0xF261: '椋',
    0xF262: '婿',
    0xF263: '娘',
    0xF264: '冥',
    0xF265: '名',
    0xF266: '命',
    0xF267: '明',
    0xF268: '盟',
    0xF269: '迷',
    0xF26A: '銘',
    0xF26B: '鳴',
    0xF26C: '姪',
    0xF26D: '牝',
    0xF26E: '滅',
    0xF26F: '免',
    0xF270: '棉',
    0xF271: '綿',
    0xF272: '緬',
    0xF273: '面',
    0xF274: '麺',
    0xF275: '摸',
    0xF276: '模',
    0xF277: '茂',
    0xF278: '妄',
    0xF279: '孟',
    0xF27A: '毛',
    0xF27B: '猛',
    0xF27C: '盲',
    0xF27D: '網',
    0xF27E: '耗',
    0xF27F: '蒙',
    0xF280: '儲',
    0xF281: '木',
    0xF282: '黙',
    0xF283: '目',
    0xF284: '杢',
    0xF285: '勿',
    0xF286: '餅',
    0xF287: '尤',
    0xF288: '戻',
    0xF289: '籾',
    0xF28A: '貰',
    0xF28B: '問',
    0xF28C: '悶',
    0xF28D: '紋',
    0xF28E: '門',
    0xF28F: '匁',
    0xF290: '也',
    0xF291: '冶',
    0xF292: '夜',
    0xF293: '爺',
    0xF294: '耶',
    0xF295: '野',
    0xF296: '弥',
    0xF297: '矢',
    0xF298: '厄',
    0xF299: '役',
    0xF29A: '約',
    0xF29B: '薬',
    0xF29C: '訳',
    0xF29D: '躍',
    0xF29E: '靖',
    0xF29F: '柳',
    0xF2A0: '薮',
    0xF2A1: '鑓',
    0xF2A2: '愉',
    0xF2A3: '愈',
    0xF2A4: '油',
    0xF2A5: '癒',
    0xF2A6: '諭',
    0xF2A7: '輸',
    0xF2A8: '唯',
    0xF2A9: '佑',
    0xF2AA: '優',
    0xF2AB: '勇',
    0xF2AC: '友',
    0xF2AD: '宥',
    0xF2AE: '幽',
    0xF2AF: '悠',
    0xF2B0: '憂',
    0xF2B1: '揖',
    0xF2B2: '有',
    0xF2B3: '柚',
    0xF2B4: '湧',
    0xF2B5: '涌',
    0xF2B6: '猶',
    0xF2B7: '猷',
    0xF2B8: '由',
    0xF2B9: '祐',
    0xF2BA: '裕',
    0xF2BB: '誘',
    0xF2BC: '遊',
    0xF2BD: '邑',
    0xF2BE: '郵',
    0xF2BF: '雄',
    0xF2C0: '融',
    0xF2C1: '夕',
    0xF2C2: '予',
    0xF2C3: '余',
    0xF2C4: '与',
    0xF2C5: '誉',
    0xF2C6: '輿',
    0xF2C7: '預',
    0xF2C8: '傭',
    0xF2C9: '幼',
    0xF2CA: '妖',
    0xF2CB: '容',
    0xF2CC: '庸',
    0xF2CD: '揚',
    0xF2CE: '揺',
    0xF2CF: '擁',
    0xF2D0: '曜',
    0xF2D1: '楊',
    0xF2D2: '様',
    0xF2D3: '洋',
    0xF2D4: '溶',
    0xF2D5: '熔',
    0xF2D6: '用',
    0xF2D7: '窯',
    0xF2D8: '羊',
    0xF2D9: '耀',
    0xF2DA: '葉',
    0xF2DB: '蓉',
    0xF2DC: '要',
    0xF2DD: '謡',
    0xF2DE: '踊',
    0xF2DF: '遥',
    0xF2E0: '陽',
    0xF2E1: '養',
    0xF2E2: '慾',
    0xF2E3: '抑',
    0xF2E4: '欲',
    0xF2E5: '沃',
    0xF2E6: '浴',
    0xF2E7: '翌',
    0xF2E8: '翼',
    0xF2E9: '淀',
    0xF2EA: '羅',
    0xF2EB: '螺',
    0xF2EC: '裸',
    0xF2ED: '来',
    0xF2EE: '莱',
    0xF2EF: '頼',
    0xF2F0: '雷',
    0xF2F1: '洛',
    0xF2F2: '絡',
    0xF2F3: '落',
    0xF2F4: '酪',
    0xF2F5: '乱',
    0xF2F6: '卵',
    0xF2F7: '嵐',
    0xF2F8: '欄',
    0xF2F9: '濫',
    0xF2FA: '藍',
    0xF2FB: '蘭',
    0xF2FC: '覧',
    0xF2FD: '利',
    0xF2FE: '吏',
    0xF2FF: '履',
    0xF300: '李',
    0xF301: '梨',
    0xF302: '理',
    0xF303: '璃',
    0xF304: '痢',
    0xF305: '裏',
    0xF306: '裡',
    0xF307: '里',
    0xF308: '離',
    0xF309: '陸',
    0xF30A: '律',
    0xF30B: '率',
    0xF30C: '立',
    0xF30D: '葎',
    0xF30E: '掠',
    0xF30F: '略',
    0xF310: '劉',
    0xF311: '流',
    0xF312: '溜',
    0xF313: '琉',
    0xF314: '留',
    0xF315: '硫',
    0xF316: '粒',
    0xF317: '隆',
    0xF318: '竜',
    0xF319: '龍',
    0xF31A: '侶',
    0xF31B: '慮',
    0xF31C: '旅',
    0xF31D: '虜',
    0xF31E: '了',
    0xF31F: '亮',
    0xF320: '僚',
    0xF321: '両',
    0xF322: '凌',
    0xF323: '寮',
    0xF324: '料',
    0xF325: '梁',
    0xF326: '涼',
    0xF327: '猟',
    0xF328: '療',
    0xF329: '瞭',
    0xF32A: '稜',
    0xF32B: '糧',
    0xF32C: '良',
    0xF32D: '諒',
    0xF32E: '遼',
    0xF32F: '量',
    0xF330: '陵',
    0xF331: '領',
    0xF332: '力',
    0xF333: '緑',
    0xF334: '倫',
    0xF335: '厘',
    0xF336: '林',
    0xF337: '淋',
    0xF338: '燐',
    0xF339: '琳',
    0xF33A: '臨',
    0xF33B: '輪',
    0xF33C: '隣',
    0xF33D: '鱗',
    0xF33E: '麟',
    0xF33F: '瑠',
    0xF340: '塁',
    0xF341: '涙',
    0xF342: '累',
    0xF343: '類',
    0xF344: '令',
    0xF345: '伶',
    0xF346: '例',
    0xF347: '冷',
    0xF348: '励',
    0xF349: '嶺',
    0xF34A: '怜',
    0xF34B: '玲',
    0xF34C: '礼',
    0xF34D: '苓',
    0xF34E: '鈴',
    0xF34F: '隷',
    0xF350: '零',
    0xF351: '霊',
    0xF352: '麗',
    0xF353: '齢',
    0xF354: '暦',
    0xF355: '歴',
    0xF356: '列',
    0xF357: '劣',
    0xF358: '烈',
    0xF359: '裂',
    0xF35A: '廉',
    0xF35B: '恋',
    0xF35C: '憐',
    0xF35D: '漣',
    0xF35E: '煉',
    0xF35F: '簾',
    0xF360: '練',
    0xF361: '聯',
    0xF362: '蓮',
    0xF363: '連',
    0xF364: '錬',
    0xF365: '呂',
    0xF366: '魯',
    0xF367: '櫓',
    0xF368: '炉',
    0xF369: '賂',
    0xF36A: '路',
    0xF36B: '露',
    0xF36C: '労',
    0xF36D: '婁',
    0xF36E: '廊',
    0xF36F: '弄',
    0xF370: '朗',
    0xF371: '楼',
    0xF372: '榔',
    0xF373: '浪',
    0xF374: '漏',
    0xF375: '牢',
    0xF376: '狼',
    0xF377: '篭',
    0xF378: '老',
    0xF379: '聾',
    0xF37A: '蝋',
    0xF37B: '郎',
    0xF37C: '六',
    0xF37D: '麓',
    0xF37E: '禄',
    0xF37F: '肋',
    0xF380: '録',
    0xF381: '論',
    0xF382: '倭',
    0xF383: '和',
    0xF384: '話',
    0xF385: '歪',
    0xF386: '賄',
    0xF387: '脇',
    0xF388: '惑',
    0xF389: '枠',
    0xF38A: '鷲',
    0xF38B: '亙',
    0xF38C: '亘',
    0xF38D: '鰐',
    0xF38E: '詫',
    0xF38F: '藁',
    0xF390: '藁',
    0xF391: '蕨',
    0xF392: '椀',
    0xF393: '湾',
    0xF394: '碗',
    0xF395: '腕',
    0xF396: '々',
    0xF397: '髙',
    0xF398: '礒',
    0xF399: '臺',
    0xF39A: '晟',
    0xF39B: '﨑',
    0xF39C: '巫',
    0xF39D: '脩',
    0xF39E: '翔',
    0xF39F: '圀',
    0xF3A0: '邉',
    0xF3A1: '燁',
    0xF3A2: 'G.',
    0xF3A3: '朗',
    0xF3A4: '曉',
    0xF3A5: '攝',
    0xF3A6: 'MI',
    0xF3A7: 'CH',
    0xF3A8: 'E',
    0xF3A9: 'AL',
    0xF3AA: '姜',
    0xF3AB: '秦',
    0xF3AC: '邊',
    0xF3AD: '齊',
    0xF3AE: '炳',
    0xF3AF: '壽',
    0xF3B0: '奎',
    0xF3B1: '洸',
    0xF3B2: '踐',
    0xF3B4: 'ｸﾞﾗ',
    0xF3B5: 'ｲｼ',
    0xF3B6: 'ﾝｶ',
    0xF3B7: 'ﾞｰ',
    0xF3B8: 'ﾌｧ',
    0xF3B9: 'ﾙｹ',
    0xF3BA: 'ﾝﾎﾞ',
    0xF3BB: 'ｰｸﾞ',
    0xF3BC: 'ﾊﾞ',
    0xF3BD: 'ｰﾅ',
    0xF3BE: 'ﾑJ',
    0xF3BF: 'r.',
    0xF3C0: '弌',
    0xF3C1: '丐',
    0xF3C2: '丕',
    0xF3C3: '个',
    0xF3C4: '丱',
    0xF3C5: '丶',
    0xF3C6: '丼',
    0xF3C7: '丿',
    0xF3C8: '乂',
    0xF3C9: '乖',
    0xF3CA: '乘',
    0xF3CB: '亂',
    0xF3CC: '亅',
    0xF3CD: '豫',
    0xF3CE: '亊',
    0xF3CF: '舒',
    0xF3D0: '弍',
    0xF3D1: '于',
    0xF3D2: '亞',
    0xF3D3: '亟',
    0xF3D4: '亠',
    0xF3D5: '亢',
    0xF3D6: '亰',
    0xF3D7: '亳',
    0xF3D8: '亶',
    0xF3D9: '从',
    0xF3DA: '仍',
    0xF3DB: '仄',
    0xF3DC: '仆',
    0xF3DD: '仂',
    0xF3DE: '仗',
    0xF3DF: '仞',
    0xF3E0: '仭',
    0xF3E1: '仟',
    0xF3E2: '价',
    0xF3E3: '伉',
    0xF3E4: '佚',
    0xF3E5: '估',
    0xF3E6: '佛',
    0xF3E7: '佝',
    0xF3E8: '佗',
    0xF3E9: '佇',
    0xF3EA: '佶',
    0xF3EB: '侈',
    0xF3EC: '侏',
    0xF3ED: '侘',
    0xF3EE: '佻',
    0xF3EF: '佩',
    0xF3F0: '佰',
    0xF3F1: '侑',
    0xF3F2: '佯',
    0xF3F3: '來',
    0xF3F4: '侖',
    0xF3F5: '儘',
    0xF3F6: '俔',
    0xF3F7: '俟',
    0xF3F8: '俎',
    0xF3F9: '俘',
    0xF3FA: '俛',
    0xF3FB: '俑',
    0xF3FC: '俚',
    0xF3FD: '俐',
    0xF3FE: '俤',
    0xF3FF: '俥',
    0xF400: '倚',
    0xF401: '倨',
    0xF402: '倔',
    0xF403: '倪',
    0xF404: '倥',
    0xF405: '倅',
    0xF406: '伜',
    0xF407: '俶',
    0xF408: '倡',
    0xF409: '倩',
    0xF40A: '倬',
    0xF40B: '俾',
    0xF40C: '俯',
    0xF40D: '們',
    0xF40E: '倆',
    0xF40F: '偃',
    0xF410: '假',
    0xF411: '會',
    0xF412: '偕',
    0xF413: '偐',
    0xF414: '偈',
    0xF415: '做',
    0xF416: '偖',
    0xF417: '偬',
    0xF418: '偸',
    0xF419: '傀',
    0xF41A: '傚',
    0xF41B: '傅',
    0xF41C: '傴',
    0xF41D: '傲',
    0xF41E: '僉',
    0xF41F: '僊',
    0xF420: '傳',
    0xF421: '僂',
    0xF422: '僖',
    0xF423: '僞',
    0xF424: '僥',
    0xF425: '僭',
    0xF426: '僣',
    0xF427: '僮',
    0xF428: '價',
    0xF429: '僵',
    0xF42A: '儉',
    0xF42B: '儁',
    0xF42C: '儂',
    0xF42D: '儖',
    0xF42E: '儕',
    0xF42F: '儔',
    0xF430: '儚',
    0xF431: '儡',
    0xF432: '儺',
    0xF433: '儷',
    0xF434: '儼',
    0xF435: '儻',
    0xF436: '儿',
    0xF437: '兀',
    0xF438: '兒',
    0xF439: '兌',
    0xF43A: '兔',
    0xF43B: '兢',
    0xF43C: '竸',
    0xF43D: '兩',
    0xF43E: '兪',
    0xF43F: '兮',
    0xF440: '冀',
    0xF441: '冂',
    0xF442: '囘',
    0xF443: '册',
    0xF444: '冉',
    0xF445: '冏',
    0xF446: '冑',
    0xF447: '冓',
    0xF448: '冕',
    0xF449: '冖',
    0xF44A: '冤',
    0xF44B: '冦',
    0xF44C: '冢',
    0xF44D: '冩',
    0xF44E: '冪',
    0xF44F: '冫',
    0xF450: '决',
    0xF451: '冱',
    0xF452: '冲',
    0xF453: '冰',
    0xF454: '况',
    0xF455: '冽',
    0xF456: '凅',
    0xF457: '凉',
    0xF458: '凛',
    0xF459: '几',
    0xF45A: '處',
    0xF45B: '凩',
    0xF45C: '凭',
    0xF45D: '凰',
    0xF45E: '凵',
    0xF45F: '凾',
    0xF460: '刄',
    0xF461: '刋',
    0xF462: '刔',
    0xF463: '刎',
    0xF464: '刧',
    0xF465: '刪',
    0xF466: '刮',
    0xF467: '刳',
    0xF468: '刹',
    0xF469: '剏',
    0xF46A: '剄',
    0xF46B: '剋',
    0xF46C: '剌',
    0xF46D: '剞',
    0xF46E: '剔',
    0xF46F: '剪',
    0xF470: '剴',
    0xF471: '剩',
    0xF472: '剳',
    0xF473: '剿',
    0xF474: '剽',
    0xF475: '劍',
    0xF476: '劔',
    0xF477: '劒',
    0xF478: '剱',
    0xF479: '劈',
    0xF47A: '劑',
    0xF47B: '辨',
    0xF47C: '辧',
    0xF47D: '劬',
    0xF47E: '劭',
    0xF47F: '劼',
    0xF480: '劵',
    0xF481: '勁',
    0xF482: '勍',
    0xF483: '勗',
    0xF484: '勞',
    0xF485: '勣',
    0xF486: '勦',
    0xF487: '飭',
    0xF488: '勠',
    0xF489: '勳',
    0xF48A: '勵',
    0xF48B: '勸',
    0xF48C: '勹',
    0xF48D: '匆',
    0xF48E: '匈',
    0xF48F: '甸',
    0xF490: '匍',
    0xF491: '匐',
    0xF492: '匏',
    0xF493: '匕',
    0xF494: '匚',
    0xF495: '匣',
    0xF496: '匯',
    0xF497: '匱',
    0xF498: '匳',
    0xF499: '匸',
    0xF49A: '區',
    0xF49B: '卆',
    0xF49C: '卅',
    0xF49D: '丗',
    0xF49E: '卉',
    0xF49F: '卍',
    0xF4A0: '凖',
    0xF4A1: '卞',
    0xF4A2: '卩',
    0xF4A3: '卮',
    0xF4A4: '夘',
    0xF4A5: '卻',
    0xF4A6: '卷',
    0xF4A7: '厂',
    0xF4A8: '厖',
    0xF4A9: '厠',
    0xF4AA: '厦',
    0xF4AB: '厥',
    0xF4AC: '厮',
    0xF4AD: '厰',
    0xF4AE: '厶',
    0xF4AF: '參',
    0xF4B0: '瑤',
    0xF4B1: '昻',
    0xF4B2: '朗',
    0xF4B3: '珉',
    0xF4B4: '珣',
    0xF4B5: '實',
    0xF4B6: '緖',
    0xF4B7: '逸',
    0xF4B8: '郞',
    0xF4B9: '鄕',
    0xF4BA: '鄧',
    0xF4BB: 'ﾌｪ',
    0xF4BC: 'ﾙﾅ',
    0xF4BD: 'ﾝﾃ',
    0xF4BE: 'ﾞｽ',
    0xF4BF: '條',
    0xF700: 'ｱ',
    0xF701: 'ｲ',
    0xF702: 'ｳ',
    0xF703: 'ｴ',
    0xF704: 'ｵ',
    0xF705: 'ｶ',
    0xF706: 'ｷ',
    0xF707: 'ｸ',
    0xF708: 'ｹ',
    0xF709: 'ｺ',
    0xF70A: 'ｻ',
    0xF70B: 'ｼ',
    0xF70C: 'ｽ',
    0xF70D: 'ｾ',
    0xF70E: 'ｿ',
    0xF70F: 'ﾀ',
    0xF710: 'ﾁ',
    0xF711: 'ﾂ',
    0xF712: 'ﾃ',
    0xF713: 'ﾄ',
    0xF714: 'ﾅ',
    0xF715: 'ﾆ',
    0xF716: 'ﾇ',
    0xF717: 'ﾈ',
    0xF718: 'ﾉ',
    0xF719: 'ﾊ',
    0xF71A: 'ﾋ',
    0xF71B: 'ﾌ',
    0xF71C: 'ﾍ',
    0xF71D: 'ﾎ',
    0xF71E: 'ﾏ',
    0xF71F: 'ﾐ',
    0xF720: 'ﾑ',
    0xF721: 'ﾒ',
    0xF722: 'ﾓ',
    0xF723: 'ﾔ',
    0xF724: 'ﾕ',
    0xF725: 'ﾖ',
    0xF726: 'ﾗ',
    0xF727: 'ﾘ',
    0xF728: 'ﾙ',
    0xF729: 'ﾚ',
    0xF72A: 'ﾛ',
    0xF72B: 'ﾜ',
    0xF72C: 'ｦ',
    0xF72D: 'ﾝ',
    0xF72E: 'ｳ',
    0xF72F: 'ﾞ',
    0xF730: 'ｧ',
    0xF731: 'ｨ',
    0xF732: 'ｩ',
    0xF733: 'ｪ',
    0xF734: 'ｫ',
    0xF735: 'ｯ',
    0xF736: 'ｬ',
    0xF737: 'ｭ',
    0xF738: 'ｮ',
    0xF739: 'ｶ',
    0xF73A: 'ﾞ',
    0xF73B: 'ｷ',
    0xF73C: 'ﾞ',
    0xF73D: 'ｸ',
    0xF73E: 'ﾞ',
    0xF73F: 'ｹ',
    0xF740: 'ﾞ',
    0xF741: 'ｺ',
    0xF742: 'ﾞ',
    0xF743: 'ｻ',
    0xF744: 'ﾞ',
    0xF745: 'ｼ',
    0xF746: 'ﾞ',
    0xF747: 'ｽ',
    0xF748: 'ﾞ',
    0xF749: 'ｾ',
    0xF74A: 'ﾞ',
    0xF74B: 'ｿ',
    0xF74C: 'ﾞ',
    0xF74D: 'ﾀ',
    0xF74E: 'ﾞ',
    0xF74F: 'ﾁ',
    0xF750: 'ﾞ',
    0xF751: '0',
    0xF752: '1',
    0xF753: '2',
    0xF754: '3',
    0xF755: '4',
    0xF756: '5',
    0xF757: '6',
    0xF758: '7',
    0xF759: '8',
    0xF75A: '9',
    0xF75B: 'A',
    0xF75C: 'B',
    0xF75D: 'C',
    0xF75E: 'D',
    0xF75F: 'E',
    0xF760: 'F',
    0xF761: 'G',
    0xF762: 'H',
    0xF763: 'I',
    0xF764: 'J',
    0xF765: 'K',
    0xF766: 'L',
    0xF767: 'M',
    0xF768: 'N',
    0xF769: 'O',
    0xF76A: 'P',
    0xF76B: 'Q',
    0xF76C: 'R',
    0xF76D: 'S',
    0xF76E: 'T',
    0xF76F: 'U',
    0xF770: 'V',
    0xF771: 'W',
    0xF772: 'X',
    0xF773: 'Y',
    0xF774: 'Z',
    0xF775: '_',
    0xF776: '+',
    0xF777: '-',
    0xF778: '?',
    0xF779: '!',
    0xF77A: '･',
    0xF77B: '｢',
    0xF77C: '｣',
    0xF77D: '/',
    0xF77E: 'a',
    0xF77F: 'b',
    0xF780: 'c',
    0xF781: 'd',
    0xF782: 'e',
    0xF783: 'f',
    0xF784: 'g',
    0xF785: 'h',
    0xF786: 'i',
    0xF787: 'j',
    0xF788: 'k',
    0xF789: 'l',
    0xF78A: 'm',
    0xF78B: 'n',
    0xF78C: 'o',
    0xF78D: 'p',
    0xF78E: 'q',
    0xF78F: 'r',
    0xF790: 's',
    0xF791: 't',
    0xF792: 'u',
    0xF793: 'v',
    0xF794: 'w',
    0xF795: 'x',
    0xF796: 'y',
    0xF797: 'z',
    0xF798: '⁰',
    0xF799: '¹',
    0xF79A: '²',
    0xF79B: '³',
    0xF79C: '⁴',
    0xF79D: '⁵',
    0xF79E: '⁶',
    0xF79F: '⁷',
    0xF7A0: '⁸',
    0xF7A1: '⁹',
    0xF7C0: 'あ',
    0xF7C1: 'い',
    0xF7C2: 'う',
    0xF7C3: 'え',
    0xF7C4: 'お',
    0xF7C5: 'か',
    0xF7C6: 'き',
    0xF7C7: 'く',
    0xF7C8: 'け',
    0xF7C9: 'こ',
    0xF7CA: 'さ',
    0xF7CB: 'し',
    0xF7CC: 'す',
    0xF7CD: 'せ',
    0xF7CE: 'そ',
    0xF7CF: 'た',
    0xF7D0: 'ち',
    0xF7D1: 'つ',
    0xF7D2: 'て',
    0xF7D3: 'と',
    0xF7D4: 'な',
    0xF7D5: 'に',
    0xF7D6: 'ぬ',
    0xF7D7: 'ね',
    0xF7D8: 'の',
    0xF7D9: 'は',
    0xF7DA: 'ひ',
    0xF7DB: 'ふ',
    0xF7DC: 'へ',
    0xF7DD: 'ほ',
    0xF7DE: 'ま',
    0xF7DF: 'み',
    0xF7E0: 'む',
    0xF7E1: 'め',
    0xF7E2: 'も',
    0xF7E3: 'や',
    0xF7E4: 'ゆ',
    0xF7E5: 'よ',
    0xF7E6: 'ら',
    0xF7E7: 'り',
    0xF7E8: 'る',
    0xF7E9: 'れ',
    0xF7EA: 'ろ',
    0xF7EB: 'わ',
    0xF7EC: 'を',
    0xF7ED: 'ん',
    0xF7EE: 'ぁ',
    0xF7EF: 'ぃ',
    0xF7F0: 'ぅ',
    0xF7F1: 'ぇ',
    0xF7F2: 'ぉ',
    0xF7F3: 'っ',
    0xF7F4: 'ゃ',
    0xF7F5: 'ゅ',
    0xF7F6: 'ょ',
    0xF7F7: 'が',
    0xF7F8: 'ぎ',
    0xF7F9: 'ぐ',
    0xF7FA: 'げ',
    0xF7FB: 'ご',
    0xF7FC: 'ざ',
    0xF7FD: 'じ',
    0xF7FE: 'ず',
    0xF7FF: 'ぜ',
}

# Prefer ordinary full-width codes for duplicate glyphs; half-width codes remain selectable by half-width input.
# --- Wiki page51 Poke12 authoritative version-specific corrections ---
for _c in range(0xF390,0xF3C0): NAME_CODE_TO_CHAR.pop(_c,None)
NAME_CODE_TO_CHAR[0xF390]='藁'
NAME_CODE_TO_CHAR[0xF391]='蕨'
NAME_CODE_TO_CHAR[0xF392]='椀'
NAME_CODE_TO_CHAR[0xF393]='湾'
NAME_CODE_TO_CHAR[0xF394]='碗'
NAME_CODE_TO_CHAR[0xF395]='腕'
NAME_CODE_TO_CHAR[0xF396]='々'
NAME_CODE_TO_CHAR[0xF397]='髙'
NAME_CODE_TO_CHAR[0xF398]='礒'
NAME_CODE_TO_CHAR[0xF399]='臺'
NAME_CODE_TO_CHAR[0xF39A]='晟'
NAME_CODE_TO_CHAR[0xF39B]='﨑'
NAME_CODE_TO_CHAR[0xF39C]='巫'
NAME_CODE_TO_CHAR[0xF39D]='脩'
NAME_CODE_TO_CHAR[0xF39E]='翔'
NAME_CODE_TO_CHAR[0xF39F]='圀'
NAME_CODE_TO_CHAR[0xF3A0]='邉'
NAME_CODE_TO_CHAR[0xF3A1]='燁'
NAME_CODE_TO_CHAR[0xF3A2]='G.'
NAME_CODE_TO_CHAR[0xF3A3]='朗'
NAME_CODE_TO_CHAR[0xF3A4]='曉'
NAME_CODE_TO_CHAR[0xF3A5]='攝'
NAME_CODE_TO_CHAR[0xF3A6]='MI'
NAME_CODE_TO_CHAR[0xF3A7]='CH'
NAME_CODE_TO_CHAR[0xF3A8]='E'
NAME_CODE_TO_CHAR[0xF3A9]='AL'
NAME_CODE_TO_CHAR[0xF3AA]='姜'
NAME_CODE_TO_CHAR[0xF3AB]='秦'
NAME_CODE_TO_CHAR[0xF3AC]='邊'
NAME_CODE_TO_CHAR[0xF3AD]='齊'
NAME_CODE_TO_CHAR[0xF3AE]='炳'
NAME_CODE_TO_CHAR[0xF3AF]='壽'
NAME_CODE_TO_CHAR[0xF3B0]='奎'
NAME_CODE_TO_CHAR[0xF3B1]='洸'
NAME_CODE_TO_CHAR[0xF3B2]='踐'
NAME_CODE_TO_CHAR[0xF3B4]='ｸﾞﾗ'
NAME_CODE_TO_CHAR[0xF3B5]='ｲｼ'
NAME_CODE_TO_CHAR[0xF3B6]='ﾝｶ'
NAME_CODE_TO_CHAR[0xF3B7]='ﾞｰ'
NAME_CODE_TO_CHAR[0xF3B8]='ﾌｧ'
NAME_CODE_TO_CHAR[0xF3B9]='ﾙｹ'
NAME_CODE_TO_CHAR[0xF3BA]='ﾝﾎﾞ'
NAME_CODE_TO_CHAR[0xF3BB]='ｰｸﾞ'
NAME_CODE_TO_CHAR[0xF3BC]='ﾊﾞ'
NAME_CODE_TO_CHAR[0xF3BD]='ｰﾅ'
NAME_CODE_TO_CHAR[0xF3BE]='ﾑJ'
NAME_CODE_TO_CHAR[0xF3BF]='r.'
NAME_CODE_TO_CHAR[0xF4B0]='瑤'
NAME_CODE_TO_CHAR[0xF4B1]='昻'
NAME_CODE_TO_CHAR[0xF4B2]='朗'
NAME_CODE_TO_CHAR[0xF4B3]='珉'
NAME_CODE_TO_CHAR[0xF4B4]='珣'
NAME_CODE_TO_CHAR[0xF4B5]='實'
NAME_CODE_TO_CHAR[0xF4B6]='緖'
NAME_CODE_TO_CHAR[0xF4B7]='逸'
NAME_CODE_TO_CHAR[0xF4B8]='郞'
NAME_CODE_TO_CHAR[0xF4B9]='鄕'
NAME_CODE_TO_CHAR[0xF4BA]='鄧'
NAME_CODE_TO_CHAR[0xF4BB]='ﾌｪ'
NAME_CODE_TO_CHAR[0xF4BC]='ﾙﾅ'
NAME_CODE_TO_CHAR[0xF4BD]='ﾝﾃ'
NAME_CODE_TO_CHAR[0xF4BE]='ﾞｽ'
NAME_CODE_TO_CHAR[0xF4BF]='條'
for _c in range(0xF700,0xF800): NAME_CODE_TO_CHAR.pop(_c,None)
NAME_CODE_TO_CHAR[0xF700]='ア'
NAME_CODE_TO_CHAR[0xF701]='イ'
NAME_CODE_TO_CHAR[0xF702]='ウ'
NAME_CODE_TO_CHAR[0xF703]='エ'
NAME_CODE_TO_CHAR[0xF704]='オ'
NAME_CODE_TO_CHAR[0xF705]='カ'
NAME_CODE_TO_CHAR[0xF706]='キ'
NAME_CODE_TO_CHAR[0xF707]='ク'
NAME_CODE_TO_CHAR[0xF708]='ケ'
NAME_CODE_TO_CHAR[0xF709]='コ'
NAME_CODE_TO_CHAR[0xF70A]='サ'
NAME_CODE_TO_CHAR[0xF70B]='シ'
NAME_CODE_TO_CHAR[0xF70C]='ス'
NAME_CODE_TO_CHAR[0xF70D]='セ'
NAME_CODE_TO_CHAR[0xF70E]='ソ'
NAME_CODE_TO_CHAR[0xF70F]='タ'
NAME_CODE_TO_CHAR[0xF710]='チ'
NAME_CODE_TO_CHAR[0xF711]='ツ'
NAME_CODE_TO_CHAR[0xF712]='テ'
NAME_CODE_TO_CHAR[0xF713]='ト'
NAME_CODE_TO_CHAR[0xF714]='ナ'
NAME_CODE_TO_CHAR[0xF715]='ニ'
NAME_CODE_TO_CHAR[0xF716]='ヌ'
NAME_CODE_TO_CHAR[0xF717]='ネ'
NAME_CODE_TO_CHAR[0xF718]='ノ'
NAME_CODE_TO_CHAR[0xF719]='ハ'
NAME_CODE_TO_CHAR[0xF71A]='ヒ'
NAME_CODE_TO_CHAR[0xF71B]='フ'
NAME_CODE_TO_CHAR[0xF71C]='ヘ'
NAME_CODE_TO_CHAR[0xF71D]='ホ'
NAME_CODE_TO_CHAR[0xF71E]='マ'
NAME_CODE_TO_CHAR[0xF71F]='ミ'
NAME_CODE_TO_CHAR[0xF720]='ム'
NAME_CODE_TO_CHAR[0xF721]='メ'
NAME_CODE_TO_CHAR[0xF722]='モ'
NAME_CODE_TO_CHAR[0xF723]='ヤ'
NAME_CODE_TO_CHAR[0xF724]='ユ'
NAME_CODE_TO_CHAR[0xF725]='ヨ'
NAME_CODE_TO_CHAR[0xF726]='ラ'
NAME_CODE_TO_CHAR[0xF727]='リ'
NAME_CODE_TO_CHAR[0xF728]='ル'
NAME_CODE_TO_CHAR[0xF729]='レ'
NAME_CODE_TO_CHAR[0xF72A]='ロ'
NAME_CODE_TO_CHAR[0xF72B]='ワ'
NAME_CODE_TO_CHAR[0xF72C]='ヲ'
NAME_CODE_TO_CHAR[0xF72D]='ン'
NAME_CODE_TO_CHAR[0xF72E]='ヴ'
NAME_CODE_TO_CHAR[0xF72F]='ァ'
NAME_CODE_TO_CHAR[0xF730]='ィ'
NAME_CODE_TO_CHAR[0xF731]='ゥ'
NAME_CODE_TO_CHAR[0xF732]='ェ'
NAME_CODE_TO_CHAR[0xF733]='ォ'
NAME_CODE_TO_CHAR[0xF734]='ッ'
NAME_CODE_TO_CHAR[0xF735]='ャ'
NAME_CODE_TO_CHAR[0xF736]='ュ'
NAME_CODE_TO_CHAR[0xF737]='ョ'
NAME_CODE_TO_CHAR[0xF738]='ガ'
NAME_CODE_TO_CHAR[0xF739]='ギ'
NAME_CODE_TO_CHAR[0xF73A]='グ'
NAME_CODE_TO_CHAR[0xF73B]='ゲ'
NAME_CODE_TO_CHAR[0xF73C]='ゴ'
NAME_CODE_TO_CHAR[0xF73D]='ザ'
NAME_CODE_TO_CHAR[0xF73E]='ジ'
NAME_CODE_TO_CHAR[0xF73F]='ズ'
NAME_CODE_TO_CHAR[0xF740]='ゼ'
NAME_CODE_TO_CHAR[0xF741]='ゾ'
NAME_CODE_TO_CHAR[0xF742]='ダ'
NAME_CODE_TO_CHAR[0xF743]='ヂ'
NAME_CODE_TO_CHAR[0xF744]='ヅ'
NAME_CODE_TO_CHAR[0xF745]='デ'
NAME_CODE_TO_CHAR[0xF746]='ド'
NAME_CODE_TO_CHAR[0xF747]='バ'
NAME_CODE_TO_CHAR[0xF748]='ビ'
NAME_CODE_TO_CHAR[0xF749]='ブ'
NAME_CODE_TO_CHAR[0xF74A]='ベ'
NAME_CODE_TO_CHAR[0xF74B]='ボ'
NAME_CODE_TO_CHAR[0xF74C]='パ'
NAME_CODE_TO_CHAR[0xF74D]='ピ'
NAME_CODE_TO_CHAR[0xF74E]='プ'
NAME_CODE_TO_CHAR[0xF74F]='ペ'
NAME_CODE_TO_CHAR[0xF750]='ポ'
NAME_CODE_TO_CHAR[0xF751]='０'
NAME_CODE_TO_CHAR[0xF752]='１'
NAME_CODE_TO_CHAR[0xF753]='２'
NAME_CODE_TO_CHAR[0xF754]='３'
NAME_CODE_TO_CHAR[0xF755]='４'
NAME_CODE_TO_CHAR[0xF756]='５'
NAME_CODE_TO_CHAR[0xF757]='６'
NAME_CODE_TO_CHAR[0xF758]='７'
NAME_CODE_TO_CHAR[0xF759]='８'
NAME_CODE_TO_CHAR[0xF75A]='９'
NAME_CODE_TO_CHAR[0xF75B]='Ａ'
NAME_CODE_TO_CHAR[0xF75C]='Ｂ'
NAME_CODE_TO_CHAR[0xF75D]='Ｃ'
NAME_CODE_TO_CHAR[0xF75E]='Ｄ'
NAME_CODE_TO_CHAR[0xF75F]='Ｅ'
NAME_CODE_TO_CHAR[0xF760]='Ｆ'
NAME_CODE_TO_CHAR[0xF761]='Ｇ'
NAME_CODE_TO_CHAR[0xF762]='Ｈ'
NAME_CODE_TO_CHAR[0xF763]='Ｉ'
NAME_CODE_TO_CHAR[0xF764]='Ｊ'
NAME_CODE_TO_CHAR[0xF765]='Ｋ'
NAME_CODE_TO_CHAR[0xF766]='Ｌ'
NAME_CODE_TO_CHAR[0xF767]='Ｍ'
NAME_CODE_TO_CHAR[0xF768]='Ｎ'
NAME_CODE_TO_CHAR[0xF769]='Ｏ'
NAME_CODE_TO_CHAR[0xF76A]='Ｐ'
NAME_CODE_TO_CHAR[0xF76B]='Ｑ'
NAME_CODE_TO_CHAR[0xF76C]='Ｒ'
NAME_CODE_TO_CHAR[0xF76D]='Ｓ'
NAME_CODE_TO_CHAR[0xF76E]='Ｔ'
NAME_CODE_TO_CHAR[0xF76F]='Ｕ'
NAME_CODE_TO_CHAR[0xF770]='Ｖ'
NAME_CODE_TO_CHAR[0xF771]='Ｗ'
NAME_CODE_TO_CHAR[0xF772]='Ｘ'
NAME_CODE_TO_CHAR[0xF773]='Ｙ'
NAME_CODE_TO_CHAR[0xF774]='Ｚ'
NAME_CODE_TO_CHAR[0xF775]='＿'
NAME_CODE_TO_CHAR[0xF776]='＋'
NAME_CODE_TO_CHAR[0xF777]='－'
NAME_CODE_TO_CHAR[0xF778]='？'
NAME_CODE_TO_CHAR[0xF779]='！'
NAME_CODE_TO_CHAR[0xF77A]='･'
NAME_CODE_TO_CHAR[0xF77B]='「'
NAME_CODE_TO_CHAR[0xF77C]='」'
NAME_CODE_TO_CHAR[0xF77D]='／'
NAME_CODE_TO_CHAR[0xF77E]='ａ'
NAME_CODE_TO_CHAR[0xF77F]='ｂ'
NAME_CODE_TO_CHAR[0xF780]='ｃ'
NAME_CODE_TO_CHAR[0xF781]='ｄ'
NAME_CODE_TO_CHAR[0xF782]='ｅ'
NAME_CODE_TO_CHAR[0xF783]='ｆ'
NAME_CODE_TO_CHAR[0xF784]='ｇ'
NAME_CODE_TO_CHAR[0xF785]='ｈ'
NAME_CODE_TO_CHAR[0xF786]='ｉ'
NAME_CODE_TO_CHAR[0xF787]='ｊ'
NAME_CODE_TO_CHAR[0xF788]='ｋ'
NAME_CODE_TO_CHAR[0xF789]='ｌ'
NAME_CODE_TO_CHAR[0xF78A]='ｍ'
NAME_CODE_TO_CHAR[0xF78B]='ｎ'
NAME_CODE_TO_CHAR[0xF78C]='ｏ'
NAME_CODE_TO_CHAR[0xF78D]='ｐ'
NAME_CODE_TO_CHAR[0xF78E]='ｑ'
NAME_CODE_TO_CHAR[0xF78F]='ｒ'
NAME_CODE_TO_CHAR[0xF790]='ｓ'
NAME_CODE_TO_CHAR[0xF791]='ｔ'
NAME_CODE_TO_CHAR[0xF792]='ｕ'
NAME_CODE_TO_CHAR[0xF793]='ｖ'
NAME_CODE_TO_CHAR[0xF794]='ｗ'
NAME_CODE_TO_CHAR[0xF795]='ｘ'
NAME_CODE_TO_CHAR[0xF796]='ｙ'
NAME_CODE_TO_CHAR[0xF797]='z'
NAME_CODE_TO_CHAR[0xF798]='⁰'
NAME_CODE_TO_CHAR[0xF799]='¹'
NAME_CODE_TO_CHAR[0xF79A]='²'
NAME_CODE_TO_CHAR[0xF79B]='³'
NAME_CODE_TO_CHAR[0xF79C]='⁴'
NAME_CODE_TO_CHAR[0xF79D]='⁵'
NAME_CODE_TO_CHAR[0xF79E]='⁶'
NAME_CODE_TO_CHAR[0xF79F]='⁷'
NAME_CODE_TO_CHAR[0xF7A0]='⁸'
NAME_CODE_TO_CHAR[0xF7A1]='⁹'
NAME_CODE_TO_CHAR[0xF7C0]='あ'
NAME_CODE_TO_CHAR[0xF7C1]='い'
NAME_CODE_TO_CHAR[0xF7C2]='う'
NAME_CODE_TO_CHAR[0xF7C3]='え'
NAME_CODE_TO_CHAR[0xF7C4]='お'
NAME_CODE_TO_CHAR[0xF7C5]='か'
NAME_CODE_TO_CHAR[0xF7C6]='き'
NAME_CODE_TO_CHAR[0xF7C7]='く'
NAME_CODE_TO_CHAR[0xF7C8]='け'
NAME_CODE_TO_CHAR[0xF7C9]='こ'
NAME_CODE_TO_CHAR[0xF7CA]='さ'
NAME_CODE_TO_CHAR[0xF7CB]='し'
NAME_CODE_TO_CHAR[0xF7CC]='す'
NAME_CODE_TO_CHAR[0xF7CD]='せ'
NAME_CODE_TO_CHAR[0xF7CE]='そ'
NAME_CODE_TO_CHAR[0xF7CF]='た'
NAME_CODE_TO_CHAR[0xF7D0]='ち'
NAME_CODE_TO_CHAR[0xF7D1]='つ'
NAME_CODE_TO_CHAR[0xF7D2]='て'
NAME_CODE_TO_CHAR[0xF7D3]='と'
NAME_CODE_TO_CHAR[0xF7D4]='な'
NAME_CODE_TO_CHAR[0xF7D5]='に'
NAME_CODE_TO_CHAR[0xF7D6]='ぬ'
NAME_CODE_TO_CHAR[0xF7D7]='ね'
NAME_CODE_TO_CHAR[0xF7D8]='の'
NAME_CODE_TO_CHAR[0xF7D9]='は'
NAME_CODE_TO_CHAR[0xF7DA]='ひ'
NAME_CODE_TO_CHAR[0xF7DB]='ふ'
NAME_CODE_TO_CHAR[0xF7DC]='へ'
NAME_CODE_TO_CHAR[0xF7DD]='ほ'
NAME_CODE_TO_CHAR[0xF7DE]='ま'
NAME_CODE_TO_CHAR[0xF7DF]='み'
NAME_CODE_TO_CHAR[0xF7E0]='む'
NAME_CODE_TO_CHAR[0xF7E1]='め'
NAME_CODE_TO_CHAR[0xF7E2]='も'
NAME_CODE_TO_CHAR[0xF7E3]='や'
NAME_CODE_TO_CHAR[0xF7E4]='ゆ'
NAME_CODE_TO_CHAR[0xF7E5]='よ'
NAME_CODE_TO_CHAR[0xF7E6]='ら'
NAME_CODE_TO_CHAR[0xF7E7]='り'
NAME_CODE_TO_CHAR[0xF7E8]='る'
NAME_CODE_TO_CHAR[0xF7E9]='れ'
NAME_CODE_TO_CHAR[0xF7EA]='ろ'
NAME_CODE_TO_CHAR[0xF7EB]='わ'
NAME_CODE_TO_CHAR[0xF7EC]='を'
NAME_CODE_TO_CHAR[0xF7ED]='ん'
NAME_CODE_TO_CHAR[0xF7EE]='ぁ'
NAME_CODE_TO_CHAR[0xF7EF]='ぃ'
NAME_CODE_TO_CHAR[0xF7F0]='ぅ'
NAME_CODE_TO_CHAR[0xF7F1]='ぇ'
NAME_CODE_TO_CHAR[0xF7F2]='ぉ'
NAME_CODE_TO_CHAR[0xF7F3]='っ'
NAME_CODE_TO_CHAR[0xF7F4]='ゃ'
NAME_CODE_TO_CHAR[0xF7F5]='ゅ'
NAME_CODE_TO_CHAR[0xF7F6]='ょ'
NAME_CODE_TO_CHAR[0xF7F7]='が'
NAME_CODE_TO_CHAR[0xF7F8]='ぎ'
NAME_CODE_TO_CHAR[0xF7F9]='ぐ'
NAME_CODE_TO_CHAR[0xF7FA]='げ'
NAME_CODE_TO_CHAR[0xF7FB]='ご'
NAME_CODE_TO_CHAR[0xF7FC]='ざ'
NAME_CODE_TO_CHAR[0xF7FD]='じ'
NAME_CODE_TO_CHAR[0xF7FE]='ず'
NAME_CODE_TO_CHAR[0xF7FF]='ぜ'
NAME_CODE_TO_CHAR[0xE975]='柏'
NAME_CODE_TO_CHAR[0xF229]='・'
WIFI_NAME_CODE_TO_CHAR={}
WIFI_NAME_CODE_TO_CHAR[0xF500]='AB'
WIFI_NAME_CODE_TO_CHAR[0xF501]='BB'
WIFI_NAME_CODE_TO_CHAR[0xF502]='XB'
WIFI_NAME_CODE_TO_CHAR[0xF503]='YB'
WIFI_NAME_CODE_TO_CHAR[0xF504]='LB'
WIFI_NAME_CODE_TO_CHAR[0xF505]='RB'
WIFI_NAME_CODE_TO_CHAR[0xF506]='+B'
WIFI_NAME_CODE_TO_CHAR[0xF507]='TI'
WIFI_NAME_CODE_TO_CHAR[0xF508]='SM'
WIFI_NAME_CODE_TO_CHAR[0xF509]='AN'
WIFI_NAME_CODE_TO_CHAR[0xF50A]='SA'
WIFI_NAME_CODE_TO_CHAR[0xF50B]='SL'
WIFI_NAME_CODE_TO_CHAR[0xF50C]='SU'
WIFI_NAME_CODE_TO_CHAR[0xF50D]='CL'
WIFI_NAME_CODE_TO_CHAR[0xF50E]='RA'
WIFI_NAME_CODE_TO_CHAR[0xF50F]='SN'
WIFI_NAME_CODE_TO_CHAR[0xF510]='ﾛ!'
WIFI_NAME_CODE_TO_CHAR[0xF511]='ﾛ?'
WIFI_NAME_CODE_TO_CHAR[0xF512]='PH'
WIFI_NAME_CODE_TO_CHAR[0xF513]='EM'
WIFI_NAME_CODE_TO_CHAR[0xF514]='田'
WIFI_NAME_CODE_TO_CHAR[0xF515]='♠'
WIFI_NAME_CODE_TO_CHAR[0xF516]='♦'
WIFI_NAME_CODE_TO_CHAR[0xF517]='♥'
WIFI_NAME_CODE_TO_CHAR[0xF518]='♣'
WIFI_NAME_CODE_TO_CHAR[0xF519]='→'
WIFI_NAME_CODE_TO_CHAR[0xF51A]='←'
WIFI_NAME_CODE_TO_CHAR[0xF51B]='↑'
WIFI_NAME_CODE_TO_CHAR[0xF51C]='↓'
WIFI_NAME_CODE_TO_CHAR[0xF51D]='×'
WIFI_NAME_CODE_TO_CHAR[0xF51E]='\u3000'
WIFI_NAME_CODE_TO_CHAR[0xF51F]='!'
WIFI_NAME_CODE_TO_CHAR[0xF520]='"'
WIFI_NAME_CODE_TO_CHAR[0xF521]='#'
WIFI_NAME_CODE_TO_CHAR[0xF522]='$'
WIFI_NAME_CODE_TO_CHAR[0xF523]='%'
WIFI_NAME_CODE_TO_CHAR[0xF524]='&'
WIFI_NAME_CODE_TO_CHAR[0xF525]="'"
WIFI_NAME_CODE_TO_CHAR[0xF526]='('
WIFI_NAME_CODE_TO_CHAR[0xF527]=')'
WIFI_NAME_CODE_TO_CHAR[0xF528]='*'
WIFI_NAME_CODE_TO_CHAR[0xF529]='＋'
WIFI_NAME_CODE_TO_CHAR[0xF52A]=','
WIFI_NAME_CODE_TO_CHAR[0xF52B]='-'
WIFI_NAME_CODE_TO_CHAR[0xF52C]='.'
WIFI_NAME_CODE_TO_CHAR[0xF52D]='/'
WIFI_NAME_CODE_TO_CHAR[0xF52E]='0'
WIFI_NAME_CODE_TO_CHAR[0xF52F]='1'
WIFI_NAME_CODE_TO_CHAR[0xF530]='2'
WIFI_NAME_CODE_TO_CHAR[0xF531]='3'
WIFI_NAME_CODE_TO_CHAR[0xF532]='4'
WIFI_NAME_CODE_TO_CHAR[0xF533]='5'
WIFI_NAME_CODE_TO_CHAR[0xF534]='6'
WIFI_NAME_CODE_TO_CHAR[0xF535]='7'
WIFI_NAME_CODE_TO_CHAR[0xF536]='8'
WIFI_NAME_CODE_TO_CHAR[0xF537]='9'
WIFI_NAME_CODE_TO_CHAR[0xF538]=':'
WIFI_NAME_CODE_TO_CHAR[0xF539]=';'
WIFI_NAME_CODE_TO_CHAR[0xF53A]='<'
WIFI_NAME_CODE_TO_CHAR[0xF53B]='='
WIFI_NAME_CODE_TO_CHAR[0xF53C]='>'
WIFI_NAME_CODE_TO_CHAR[0xF53D]='?'
WIFI_NAME_CODE_TO_CHAR[0xF53E]='@'
WIFI_NAME_CODE_TO_CHAR[0xF53F]='A'
WIFI_NAME_CODE_TO_CHAR[0xF540]='B'
WIFI_NAME_CODE_TO_CHAR[0xF541]='C'
WIFI_NAME_CODE_TO_CHAR[0xF542]='D'
WIFI_NAME_CODE_TO_CHAR[0xF543]='E'
WIFI_NAME_CODE_TO_CHAR[0xF544]='F'
WIFI_NAME_CODE_TO_CHAR[0xF545]='G'
WIFI_NAME_CODE_TO_CHAR[0xF546]='H'
WIFI_NAME_CODE_TO_CHAR[0xF547]='I'
WIFI_NAME_CODE_TO_CHAR[0xF548]='J'
WIFI_NAME_CODE_TO_CHAR[0xF549]='K'
WIFI_NAME_CODE_TO_CHAR[0xF54A]='L'
WIFI_NAME_CODE_TO_CHAR[0xF54B]='M'
WIFI_NAME_CODE_TO_CHAR[0xF54C]='N'
WIFI_NAME_CODE_TO_CHAR[0xF54D]='O'
WIFI_NAME_CODE_TO_CHAR[0xF54E]='P'
WIFI_NAME_CODE_TO_CHAR[0xF54F]='Q'
WIFI_NAME_CODE_TO_CHAR[0xF550]='R'
WIFI_NAME_CODE_TO_CHAR[0xF551]='S'
WIFI_NAME_CODE_TO_CHAR[0xF552]='T'
WIFI_NAME_CODE_TO_CHAR[0xF553]='U'
WIFI_NAME_CODE_TO_CHAR[0xF554]='V'
WIFI_NAME_CODE_TO_CHAR[0xF555]='W'
WIFI_NAME_CODE_TO_CHAR[0xF556]='X'
WIFI_NAME_CODE_TO_CHAR[0xF557]='Y'
WIFI_NAME_CODE_TO_CHAR[0xF558]='Z'
WIFI_NAME_CODE_TO_CHAR[0xF559]='['
WIFI_NAME_CODE_TO_CHAR[0xF55A]='〵'
WIFI_NAME_CODE_TO_CHAR[0xF55B]=']'
WIFI_NAME_CODE_TO_CHAR[0xF55C]='^'
WIFI_NAME_CODE_TO_CHAR[0xF55D]='_'
WIFI_NAME_CODE_TO_CHAR[0xF55E]="'"
WIFI_NAME_CODE_TO_CHAR[0xF55F]='a'
WIFI_NAME_CODE_TO_CHAR[0xF560]='b'
WIFI_NAME_CODE_TO_CHAR[0xF561]='c'
WIFI_NAME_CODE_TO_CHAR[0xF562]='d'
WIFI_NAME_CODE_TO_CHAR[0xF563]='e'
WIFI_NAME_CODE_TO_CHAR[0xF564]='f'
WIFI_NAME_CODE_TO_CHAR[0xF565]='g'
WIFI_NAME_CODE_TO_CHAR[0xF566]='h'
WIFI_NAME_CODE_TO_CHAR[0xF567]='i'
WIFI_NAME_CODE_TO_CHAR[0xF568]='j'
WIFI_NAME_CODE_TO_CHAR[0xF569]='k'
WIFI_NAME_CODE_TO_CHAR[0xF56A]='l'
WIFI_NAME_CODE_TO_CHAR[0xF56B]='m'
WIFI_NAME_CODE_TO_CHAR[0xF56C]='n'
WIFI_NAME_CODE_TO_CHAR[0xF56D]='o'
WIFI_NAME_CODE_TO_CHAR[0xF56E]='p'
WIFI_NAME_CODE_TO_CHAR[0xF56F]='q'
WIFI_NAME_CODE_TO_CHAR[0xF570]='r'
WIFI_NAME_CODE_TO_CHAR[0xF571]='s'
WIFI_NAME_CODE_TO_CHAR[0xF572]='t'
WIFI_NAME_CODE_TO_CHAR[0xF573]='u'
WIFI_NAME_CODE_TO_CHAR[0xF574]='v'
WIFI_NAME_CODE_TO_CHAR[0xF575]='w'
WIFI_NAME_CODE_TO_CHAR[0xF576]='x'
WIFI_NAME_CODE_TO_CHAR[0xF577]='y'
WIFI_NAME_CODE_TO_CHAR[0xF578]='z'
WIFI_NAME_CODE_TO_CHAR[0xF579]='｛'
WIFI_NAME_CODE_TO_CHAR[0xF57A]='l'
WIFI_NAME_CODE_TO_CHAR[0xF57B]='｝'
WIFI_NAME_CODE_TO_CHAR[0xF57C]='~'
WIFI_NAME_CODE_TO_CHAR[0xF57D]='€'
WIFI_NAME_CODE_TO_CHAR[0xF57E]='.'
WIFI_NAME_CODE_TO_CHAR[0xF57F]='̤'
WIFI_NAME_CODE_TO_CHAR[0xF580]='.̤'
WIFI_NAME_CODE_TO_CHAR[0xF581]='^'
WIFI_NAME_CODE_TO_CHAR[0xF582]='Œ'
WIFI_NAME_CODE_TO_CHAR[0xF583]='′'
WIFI_NAME_CODE_TO_CHAR[0xF584]='′'
WIFI_NAME_CODE_TO_CHAR[0xF585]='″'
WIFI_NAME_CODE_TO_CHAR[0xF586]='\u3000″'
WIFI_NAME_CODE_TO_CHAR[0xF587]='●'
WIFI_NAME_CODE_TO_CHAR[0xF588]='\u3000″'
WIFI_NAME_CODE_TO_CHAR[0xF589]='™'
WIFI_NAME_CODE_TO_CHAR[0xF58A]='≻'
WIFI_NAME_CODE_TO_CHAR[0xF58B]='œ'
WIFI_NAME_CODE_TO_CHAR[0xF58C]='¡'
WIFI_NAME_CODE_TO_CHAR[0xF58D]='¢'
WIFI_NAME_CODE_TO_CHAR[0xF58E]='£'
WIFI_NAME_CODE_TO_CHAR[0xF58F]='¨'
WIFI_NAME_CODE_TO_CHAR[0xF590]='©'
WIFI_NAME_CODE_TO_CHAR[0xF591]='®'
WIFI_NAME_CODE_TO_CHAR[0xF592]='°'
WIFI_NAME_CODE_TO_CHAR[0xF593]='±'
WIFI_NAME_CODE_TO_CHAR[0xF594]='´'
WIFI_NAME_CODE_TO_CHAR[0xF595]='+'
WIFI_NAME_CODE_TO_CHAR[0xF596]='¿'
WIFI_NAME_CODE_TO_CHAR[0xF597]='À'
WIFI_NAME_CODE_TO_CHAR[0xF598]='Á'
WIFI_NAME_CODE_TO_CHAR[0xF599]='Â'
WIFI_NAME_CODE_TO_CHAR[0xF59A]='Ã'
WIFI_NAME_CODE_TO_CHAR[0xF59B]='Ä'
WIFI_NAME_CODE_TO_CHAR[0xF59C]='Å'
WIFI_NAME_CODE_TO_CHAR[0xF59D]='Æ'
WIFI_NAME_CODE_TO_CHAR[0xF59E]='Ç'
WIFI_NAME_CODE_TO_CHAR[0xF59F]='È'
WIFI_NAME_CODE_TO_CHAR[0xF5A0]='É'
WIFI_NAME_CODE_TO_CHAR[0xF5A1]='Ê'
WIFI_NAME_CODE_TO_CHAR[0xF5A2]='Ë'
WIFI_NAME_CODE_TO_CHAR[0xF5A3]='Ì'
WIFI_NAME_CODE_TO_CHAR[0xF5A4]='Í'
WIFI_NAME_CODE_TO_CHAR[0xF5A5]='Î'
WIFI_NAME_CODE_TO_CHAR[0xF5A6]='Ï'
WIFI_NAME_CODE_TO_CHAR[0xF5A7]='Ð'
WIFI_NAME_CODE_TO_CHAR[0xF5A8]='Ñ'
WIFI_NAME_CODE_TO_CHAR[0xF5A9]='Ò'
WIFI_NAME_CODE_TO_CHAR[0xF5AA]='Ó'
WIFI_NAME_CODE_TO_CHAR[0xF5AB]='Ô'
WIFI_NAME_CODE_TO_CHAR[0xF5AC]='Õ'
WIFI_NAME_CODE_TO_CHAR[0xF5AD]='Ö'
WIFI_NAME_CODE_TO_CHAR[0xF5AE]='×'
WIFI_NAME_CODE_TO_CHAR[0xF5AF]='Ø'
WIFI_NAME_CODE_TO_CHAR[0xF5B0]='Ù'
WIFI_NAME_CODE_TO_CHAR[0xF5B1]='Ú'
WIFI_NAME_CODE_TO_CHAR[0xF5B2]='Û'
WIFI_NAME_CODE_TO_CHAR[0xF5B3]='Ü'
WIFI_NAME_CODE_TO_CHAR[0xF5B4]='Ý'
WIFI_NAME_CODE_TO_CHAR[0xF5B5]='ß'
WIFI_NAME_CODE_TO_CHAR[0xF5B6]='à'
WIFI_NAME_CODE_TO_CHAR[0xF5B7]='á'
WIFI_NAME_CODE_TO_CHAR[0xF5B8]='â'
WIFI_NAME_CODE_TO_CHAR[0xF5B9]='ã'
WIFI_NAME_CODE_TO_CHAR[0xF5BA]='ä'
WIFI_NAME_CODE_TO_CHAR[0xF5BB]='å'
WIFI_NAME_CODE_TO_CHAR[0xF5BC]='æ'
WIFI_NAME_CODE_TO_CHAR[0xF5BD]='ç'
WIFI_NAME_CODE_TO_CHAR[0xF5BE]='è'
WIFI_NAME_CODE_TO_CHAR[0xF5BF]='é'
WIFI_NAME_CODE_TO_CHAR[0xF5C0]='ê'
WIFI_NAME_CODE_TO_CHAR[0xF5C1]='ë'
WIFI_NAME_CODE_TO_CHAR[0xF5C2]='ì'
WIFI_NAME_CODE_TO_CHAR[0xF5C3]='í'
WIFI_NAME_CODE_TO_CHAR[0xF5C4]='î'
WIFI_NAME_CODE_TO_CHAR[0xF5C5]='ï'
WIFI_NAME_CODE_TO_CHAR[0xF5C6]='ð'
WIFI_NAME_CODE_TO_CHAR[0xF5C7]='ñ'
WIFI_NAME_CODE_TO_CHAR[0xF5C8]='ò'
WIFI_NAME_CODE_TO_CHAR[0xF5C9]='ó'
WIFI_NAME_CODE_TO_CHAR[0xF5CA]='ô'
WIFI_NAME_CODE_TO_CHAR[0xF5CB]='õ'
WIFI_NAME_CODE_TO_CHAR[0xF5CC]='ö'
WIFI_NAME_CODE_TO_CHAR[0xF5CD]='÷'
WIFI_NAME_CODE_TO_CHAR[0xF5CE]='ø'
WIFI_NAME_CODE_TO_CHAR[0xF5CF]='ù'
WIFI_NAME_CODE_TO_CHAR[0xF5D0]='ú'
WIFI_NAME_CODE_TO_CHAR[0xF5D1]='û'
WIFI_NAME_CODE_TO_CHAR[0xF5D2]='ü'
WIFI_NAME_CODE_TO_CHAR[0xF5D3]='ý'
WIFI_NAME_CODE_TO_CHAR[0xF5D5]='、'
WIFI_NAME_CODE_TO_CHAR[0xF5D6]='。'
WIFI_NAME_CODE_TO_CHAR[0xF5D7]='，'
WIFI_NAME_CODE_TO_CHAR[0xF5D8]='．'
WIFI_NAME_CODE_TO_CHAR[0xF5D9]='･'
WIFI_NAME_CODE_TO_CHAR[0xF5DA]='：'
WIFI_NAME_CODE_TO_CHAR[0xF5DB]='；'
WIFI_NAME_CODE_TO_CHAR[0xF5DC]='？'
WIFI_NAME_CODE_TO_CHAR[0xF5DD]='！'
WIFI_NAME_CODE_TO_CHAR[0xF5DE]='゛'
WIFI_NAME_CODE_TO_CHAR[0xF5DF]='゜'
WIFI_NAME_CODE_TO_CHAR[0xF5E0]='′'
WIFI_NAME_CODE_TO_CHAR[0xF5E1]='‵'
WIFI_NAME_CODE_TO_CHAR[0xF5E2]='̈'
WIFI_NAME_CODE_TO_CHAR[0xF5E3]='͡'
WIFI_NAME_CODE_TO_CHAR[0xF5E4]='￣'
WIFI_NAME_CODE_TO_CHAR[0xF5E5]='＿'
WIFI_NAME_CODE_TO_CHAR[0xF5E6]='ゝ'
WIFI_NAME_CODE_TO_CHAR[0xF5E7]='ヾ'
WIFI_NAME_CODE_TO_CHAR[0xF5E8]='々'
WIFI_NAME_CODE_TO_CHAR[0xF5E9]='‒'
WIFI_NAME_CODE_TO_CHAR[0xF5EA]='—'
WIFI_NAME_CODE_TO_CHAR[0xF5EB]='–'
WIFI_NAME_CODE_TO_CHAR[0xF5EC]='／'
WIFI_NAME_CODE_TO_CHAR[0xF5ED]='＼'
WIFI_NAME_CODE_TO_CHAR[0xF5EE]='～'
WIFI_NAME_CODE_TO_CHAR[0xF5EF]='❘'
WIFI_NAME_CODE_TO_CHAR[0xF5F0]='…'
WIFI_NAME_CODE_TO_CHAR[0xF5F1]='‘'
WIFI_NAME_CODE_TO_CHAR[0xF5F2]="'"
WIFI_NAME_CODE_TO_CHAR[0xF5F3]='“'
WIFI_NAME_CODE_TO_CHAR[0xF5F4]='”'
WIFI_NAME_CODE_TO_CHAR[0xF5F5]='（'
WIFI_NAME_CODE_TO_CHAR[0xF5F6]='）'
WIFI_NAME_CODE_TO_CHAR[0xF5F7]='〔'
WIFI_NAME_CODE_TO_CHAR[0xF5F8]='〕'
WIFI_NAME_CODE_TO_CHAR[0xF5F9]='［'
WIFI_NAME_CODE_TO_CHAR[0xF5FA]='］'
WIFI_NAME_CODE_TO_CHAR[0xF5FB]='｛'
WIFI_NAME_CODE_TO_CHAR[0xF5FC]='｝'
WIFI_NAME_CODE_TO_CHAR[0xF5FD]='＜'
WIFI_NAME_CODE_TO_CHAR[0xF5FE]='＞'
WIFI_NAME_CODE_TO_CHAR[0xF5FF]='「'
WIFI_NAME_CODE_TO_CHAR[0xF600]='」'
WIFI_NAME_CODE_TO_CHAR[0xF601]='+'
WIFI_NAME_CODE_TO_CHAR[0xF602]='-'
WIFI_NAME_CODE_TO_CHAR[0xF603]='±'
WIFI_NAME_CODE_TO_CHAR[0xF604]='×'
WIFI_NAME_CODE_TO_CHAR[0xF605]='÷'
WIFI_NAME_CODE_TO_CHAR[0xF606]='='
WIFI_NAME_CODE_TO_CHAR[0xF607]='∞'
WIFI_NAME_CODE_TO_CHAR[0xF608]='∴'
WIFI_NAME_CODE_TO_CHAR[0xF609]='°'
WIFI_NAME_CODE_TO_CHAR[0xF60A]='′'
WIFI_NAME_CODE_TO_CHAR[0xF60B]='″'
WIFI_NAME_CODE_TO_CHAR[0xF60C]='＆'
WIFI_NAME_CODE_TO_CHAR[0xF60D]='☆'
WIFI_NAME_CODE_TO_CHAR[0xF60E]='★'
WIFI_NAME_CODE_TO_CHAR[0xF60F]='○'
WIFI_NAME_CODE_TO_CHAR[0xF610]='●'
WIFI_NAME_CODE_TO_CHAR[0xF611]='◎'
WIFI_NAME_CODE_TO_CHAR[0xF612]='◇'
WIFI_NAME_CODE_TO_CHAR[0xF613]='◆'
WIFI_NAME_CODE_TO_CHAR[0xF614]='□'
WIFI_NAME_CODE_TO_CHAR[0xF615]='■'
WIFI_NAME_CODE_TO_CHAR[0xF616]='△'
WIFI_NAME_CODE_TO_CHAR[0xF617]='▲'
WIFI_NAME_CODE_TO_CHAR[0xF618]='▽'
WIFI_NAME_CODE_TO_CHAR[0xF619]='▼'
WIFI_NAME_CODE_TO_CHAR[0xF61A]='※'
WIFI_NAME_CODE_TO_CHAR[0xF61B]='〒'
WIFI_NAME_CODE_TO_CHAR[0xF61C]='→'
WIFI_NAME_CODE_TO_CHAR[0xF61D]='←'
WIFI_NAME_CODE_TO_CHAR[0xF61E]='↑'
WIFI_NAME_CODE_TO_CHAR[0xF61F]='↓'
WIFI_NAME_CODE_TO_CHAR[0xF620]='♯'
WIFI_NAME_CODE_TO_CHAR[0xF621]='♭'
WIFI_NAME_CODE_TO_CHAR[0xF622]='♪'
WIFI_NAME_CODE_TO_CHAR[0xF623]='ぁ'
WIFI_NAME_CODE_TO_CHAR[0xF624]='あ'
WIFI_NAME_CODE_TO_CHAR[0xF625]='ぃ'
WIFI_NAME_CODE_TO_CHAR[0xF626]='い'
WIFI_NAME_CODE_TO_CHAR[0xF627]='ぅ'
WIFI_NAME_CODE_TO_CHAR[0xF628]='う'
WIFI_NAME_CODE_TO_CHAR[0xF629]='ぇ'
WIFI_NAME_CODE_TO_CHAR[0xF62A]='え'
WIFI_NAME_CODE_TO_CHAR[0xF62B]='ぉ'
WIFI_NAME_CODE_TO_CHAR[0xF62C]='お'
WIFI_NAME_CODE_TO_CHAR[0xF62D]='か'
WIFI_NAME_CODE_TO_CHAR[0xF62E]='が'
WIFI_NAME_CODE_TO_CHAR[0xF62F]='き'
WIFI_NAME_CODE_TO_CHAR[0xF630]='ぎ'
WIFI_NAME_CODE_TO_CHAR[0xF631]='く'
WIFI_NAME_CODE_TO_CHAR[0xF632]='ぐ'
WIFI_NAME_CODE_TO_CHAR[0xF633]='け'
WIFI_NAME_CODE_TO_CHAR[0xF634]='げ'
WIFI_NAME_CODE_TO_CHAR[0xF635]='こ'
WIFI_NAME_CODE_TO_CHAR[0xF636]='ご'
WIFI_NAME_CODE_TO_CHAR[0xF637]='さ'
WIFI_NAME_CODE_TO_CHAR[0xF638]='ざ'
WIFI_NAME_CODE_TO_CHAR[0xF639]='し'
WIFI_NAME_CODE_TO_CHAR[0xF63A]='じ'
WIFI_NAME_CODE_TO_CHAR[0xF63B]='す'
WIFI_NAME_CODE_TO_CHAR[0xF63C]='ず'
WIFI_NAME_CODE_TO_CHAR[0xF63D]='せ'
WIFI_NAME_CODE_TO_CHAR[0xF63E]='ぜ'
WIFI_NAME_CODE_TO_CHAR[0xF63F]='そ'
WIFI_NAME_CODE_TO_CHAR[0xF640]='ぞ'
WIFI_NAME_CODE_TO_CHAR[0xF641]='た'
WIFI_NAME_CODE_TO_CHAR[0xF642]='だ'
WIFI_NAME_CODE_TO_CHAR[0xF643]='ち'
WIFI_NAME_CODE_TO_CHAR[0xF644]='ぢ'
WIFI_NAME_CODE_TO_CHAR[0xF645]='っ'
WIFI_NAME_CODE_TO_CHAR[0xF646]='つ'
WIFI_NAME_CODE_TO_CHAR[0xF647]='づ'
WIFI_NAME_CODE_TO_CHAR[0xF648]='て'
WIFI_NAME_CODE_TO_CHAR[0xF649]='で'
WIFI_NAME_CODE_TO_CHAR[0xF64A]='と'
WIFI_NAME_CODE_TO_CHAR[0xF64B]='ど'
WIFI_NAME_CODE_TO_CHAR[0xF64C]='な'
WIFI_NAME_CODE_TO_CHAR[0xF64D]='に'
WIFI_NAME_CODE_TO_CHAR[0xF64E]='ぬ'
WIFI_NAME_CODE_TO_CHAR[0xF64F]='ね'
WIFI_NAME_CODE_TO_CHAR[0xF650]='の'
WIFI_NAME_CODE_TO_CHAR[0xF651]='は'
WIFI_NAME_CODE_TO_CHAR[0xF652]='ば'
WIFI_NAME_CODE_TO_CHAR[0xF653]='ぱ'
WIFI_NAME_CODE_TO_CHAR[0xF654]='ひ'
WIFI_NAME_CODE_TO_CHAR[0xF655]='び'
WIFI_NAME_CODE_TO_CHAR[0xF656]='ぴ'
WIFI_NAME_CODE_TO_CHAR[0xF657]='ふ'
WIFI_NAME_CODE_TO_CHAR[0xF658]='ぶ'
WIFI_NAME_CODE_TO_CHAR[0xF659]='ぷ'
WIFI_NAME_CODE_TO_CHAR[0xF65A]='へ'
WIFI_NAME_CODE_TO_CHAR[0xF65B]='べ'
WIFI_NAME_CODE_TO_CHAR[0xF65C]='ぺ'
WIFI_NAME_CODE_TO_CHAR[0xF65D]='ほ'
WIFI_NAME_CODE_TO_CHAR[0xF65E]='ぼ'
WIFI_NAME_CODE_TO_CHAR[0xF65F]='ぽ'
WIFI_NAME_CODE_TO_CHAR[0xF660]='ま'
WIFI_NAME_CODE_TO_CHAR[0xF661]='み'
WIFI_NAME_CODE_TO_CHAR[0xF662]='む'
WIFI_NAME_CODE_TO_CHAR[0xF663]='め'
WIFI_NAME_CODE_TO_CHAR[0xF664]='も'
WIFI_NAME_CODE_TO_CHAR[0xF665]='ゃ'
WIFI_NAME_CODE_TO_CHAR[0xF666]='や'
WIFI_NAME_CODE_TO_CHAR[0xF667]='ゅ'
WIFI_NAME_CODE_TO_CHAR[0xF668]='ゆ'
WIFI_NAME_CODE_TO_CHAR[0xF669]='ょ'
WIFI_NAME_CODE_TO_CHAR[0xF66A]='よ'
WIFI_NAME_CODE_TO_CHAR[0xF66B]='ら'
WIFI_NAME_CODE_TO_CHAR[0xF66C]='り'
WIFI_NAME_CODE_TO_CHAR[0xF66D]='る'
WIFI_NAME_CODE_TO_CHAR[0xF66E]='れ'
WIFI_NAME_CODE_TO_CHAR[0xF66F]='ろ'
WIFI_NAME_CODE_TO_CHAR[0xF670]='ゎ'
WIFI_NAME_CODE_TO_CHAR[0xF671]='わ'
WIFI_NAME_CODE_TO_CHAR[0xF672]='ゐ'
WIFI_NAME_CODE_TO_CHAR[0xF673]='ゑ'
WIFI_NAME_CODE_TO_CHAR[0xF674]='を'
WIFI_NAME_CODE_TO_CHAR[0xF675]='ん'
WIFI_NAME_CODE_TO_CHAR[0xF676]='ァ'
WIFI_NAME_CODE_TO_CHAR[0xF677]='ア'
WIFI_NAME_CODE_TO_CHAR[0xF678]='ィ'
WIFI_NAME_CODE_TO_CHAR[0xF679]='イ'
WIFI_NAME_CODE_TO_CHAR[0xF67A]='ゥ'
WIFI_NAME_CODE_TO_CHAR[0xF67B]='ウ'
WIFI_NAME_CODE_TO_CHAR[0xF67C]='ェ'
WIFI_NAME_CODE_TO_CHAR[0xF67D]='エ'
WIFI_NAME_CODE_TO_CHAR[0xF67E]='ォ'
WIFI_NAME_CODE_TO_CHAR[0xF67F]='オ'
WIFI_NAME_CODE_TO_CHAR[0xF680]='カ'
WIFI_NAME_CODE_TO_CHAR[0xF681]='ガ'
WIFI_NAME_CODE_TO_CHAR[0xF682]='キ'
WIFI_NAME_CODE_TO_CHAR[0xF683]='ギ'
WIFI_NAME_CODE_TO_CHAR[0xF684]='ク'
WIFI_NAME_CODE_TO_CHAR[0xF685]='グ'
WIFI_NAME_CODE_TO_CHAR[0xF686]='ケ'
WIFI_NAME_CODE_TO_CHAR[0xF687]='ゲ'
WIFI_NAME_CODE_TO_CHAR[0xF688]='コ'
WIFI_NAME_CODE_TO_CHAR[0xF689]='ゴ'
WIFI_NAME_CODE_TO_CHAR[0xF68A]='サ'
WIFI_NAME_CODE_TO_CHAR[0xF68B]='ザ'
WIFI_NAME_CODE_TO_CHAR[0xF68C]='シ'
WIFI_NAME_CODE_TO_CHAR[0xF68D]='ジ'
WIFI_NAME_CODE_TO_CHAR[0xF68E]='ス'
WIFI_NAME_CODE_TO_CHAR[0xF68F]='ズ'
WIFI_NAME_CODE_TO_CHAR[0xF690]='セ'
WIFI_NAME_CODE_TO_CHAR[0xF691]='ゼ'
WIFI_NAME_CODE_TO_CHAR[0xF692]='ソ'
WIFI_NAME_CODE_TO_CHAR[0xF693]='ゾ'
WIFI_NAME_CODE_TO_CHAR[0xF694]='タ'
WIFI_NAME_CODE_TO_CHAR[0xF695]='ダ'
WIFI_NAME_CODE_TO_CHAR[0xF696]='チ'
WIFI_NAME_CODE_TO_CHAR[0xF697]='ヂ'
WIFI_NAME_CODE_TO_CHAR[0xF698]='ッ'
WIFI_NAME_CODE_TO_CHAR[0xF699]='ツ'
WIFI_NAME_CODE_TO_CHAR[0xF69A]='ヅ'
WIFI_NAME_CODE_TO_CHAR[0xF69B]='テ'
WIFI_NAME_CODE_TO_CHAR[0xF69C]='デ'
WIFI_NAME_CODE_TO_CHAR[0xF69D]='ト'
WIFI_NAME_CODE_TO_CHAR[0xF69E]='ド'
WIFI_NAME_CODE_TO_CHAR[0xF69F]='ナ'
WIFI_NAME_CODE_TO_CHAR[0xF6A0]='ニ'
WIFI_NAME_CODE_TO_CHAR[0xF6A1]='ヌ'
WIFI_NAME_CODE_TO_CHAR[0xF6A2]='ネ'
WIFI_NAME_CODE_TO_CHAR[0xF6A3]='ノ'
WIFI_NAME_CODE_TO_CHAR[0xF6A4]='ハ'
WIFI_NAME_CODE_TO_CHAR[0xF6A5]='バ'
WIFI_NAME_CODE_TO_CHAR[0xF6A6]='パ'
WIFI_NAME_CODE_TO_CHAR[0xF6A7]='ヒ'
WIFI_NAME_CODE_TO_CHAR[0xF6A8]='ビ'
WIFI_NAME_CODE_TO_CHAR[0xF6A9]='ピ'
WIFI_NAME_CODE_TO_CHAR[0xF6AA]='フ'
WIFI_NAME_CODE_TO_CHAR[0xF6AB]='ブ'
WIFI_NAME_CODE_TO_CHAR[0xF6AC]='プ'
WIFI_NAME_CODE_TO_CHAR[0xF6AD]='ヘ'
WIFI_NAME_CODE_TO_CHAR[0xF6AE]='ベ'
WIFI_NAME_CODE_TO_CHAR[0xF6AF]='ペ'
WIFI_NAME_CODE_TO_CHAR[0xF6B0]='ホ'
WIFI_NAME_CODE_TO_CHAR[0xF6B1]='ボ'
WIFI_NAME_CODE_TO_CHAR[0xF6B2]='ポ'
WIFI_NAME_CODE_TO_CHAR[0xF6B3]='マ'
WIFI_NAME_CODE_TO_CHAR[0xF6B4]='ミ'
WIFI_NAME_CODE_TO_CHAR[0xF6B5]='ム'
WIFI_NAME_CODE_TO_CHAR[0xF6B6]='メ'
WIFI_NAME_CODE_TO_CHAR[0xF6B7]='モ'
WIFI_NAME_CODE_TO_CHAR[0xF6B8]='ャ'
WIFI_NAME_CODE_TO_CHAR[0xF6B9]='ヤ'
WIFI_NAME_CODE_TO_CHAR[0xF6BA]='ュ'
WIFI_NAME_CODE_TO_CHAR[0xF6BB]='ユ'
WIFI_NAME_CODE_TO_CHAR[0xF6BC]='ョ'
WIFI_NAME_CODE_TO_CHAR[0xF6BD]='ヨ'
WIFI_NAME_CODE_TO_CHAR[0xF6BE]='ラ'
WIFI_NAME_CODE_TO_CHAR[0xF6BF]='リ'
WIFI_NAME_CODE_TO_CHAR[0xF6C0]='ル'
WIFI_NAME_CODE_TO_CHAR[0xF6C1]='レ'
WIFI_NAME_CODE_TO_CHAR[0xF6C2]='ロ'
WIFI_NAME_CODE_TO_CHAR[0xF6C3]='ヮ'
WIFI_NAME_CODE_TO_CHAR[0xF6C4]='ワ'
WIFI_NAME_CODE_TO_CHAR[0xF6C5]='ヰ'
WIFI_NAME_CODE_TO_CHAR[0xF6C6]='ヱ'
WIFI_NAME_CODE_TO_CHAR[0xF6C7]='ヲ'
WIFI_NAME_CODE_TO_CHAR[0xF6C8]='ン'
WIFI_NAME_CODE_TO_CHAR[0xF6C9]='ヴ'
WIFI_NAME_CODE_TO_CHAR[0xF6CA]='ヵ'
WIFI_NAME_CODE_TO_CHAR[0xF6CB]='ヶ'
NAME_CHAR_TO_CODE = {}
for _code,_ch in NAME_CODE_TO_CHAR.items():
    if len(_ch)==1 and _ch not in NAME_CHAR_TO_CODE: NAME_CHAR_TO_CODE[_ch]=_code
# Wiki page51: F22D=麻. Real QR『上条当麻』is a golden verification.
NAME_CODE_TO_CHAR[0xF22D]='麻'
NAME_CHAR_TO_CODE['麻']=0xF22D
# Poke12 F700-F7FF: selectable half-width player-name codes.
# A visible glyph can have both an ordinary code and an F7xx half-width code,
# so keep a separate reverse map instead of collapsing them in NAME_CHAR_TO_CODE.
HALF_NAME_CHAR_TO_CODE={ch:code for code,ch in NAME_CODE_TO_CHAR.items()
                        if 0xF700<=code<=0xF7FF and len(ch)==1}

# Direct mixed-name input uses real Unicode half-width kana (e.g. 王ｾﾘ).
# Convert each half-width kana token, including dakuten/handakuten pairs, to
# the visible glyph used by the Poke12 F7xx table.
_HALF_KANA_TO_NORMAL={}
for _cp in range(0xFF61,0xFFA0):
    _s=chr(_cp);_n=unicodedata.normalize("NFKC",_s)
    if len(_n)==1:_HALF_KANA_TO_NORMAL[_s]=_n
for _cp in range(0xFF61,0xFFA0):
    for _mark in ("ﾞ","ﾟ"):
        _s=chr(_cp)+_mark;_n=unicodedata.normalize("NFKC",_s)
        if len(_n)==1:_HALF_KANA_TO_NORMAL[_s]=_n
# Poke12's F7xx table does NOT use the glyph NFKC produces for two of these:
#   F777 stores '－' (U+FF0D FULLWIDTH HYPHEN-MINUS), while NFKC('ｰ') gives 'ー' (U+30FC)
#   F77A stores '･' (U+FF65 HALFWIDTH MIDDLE DOT),   while NFKC('･') gives '・' (U+30FB)
# Without these overrides, typing 'ｵｶﾈｽｷ－' produced f7 04 f7 05 f7 17 f7 0c f7 06 d6
# (a full-width 'ー' code d6 mixed into an all-half-width name), and '･' raised.
_HALF_KANA_TO_NORMAL['ｰ']='－'
_HALF_KANA_TO_NORMAL['･']='･'
_NORMAL_TO_HALF_KANA={}
for _s,_n in sorted(_HALF_KANA_TO_NORMAL.items(),key=lambda x:len(x[0])):
    _NORMAL_TO_HALF_KANA.setdefault(_n,_s)
# Let the ordinary glyphs reach the F7xx codes too, so a user who types the
# full-width 'ー' / '・' with the half-width box ticked still gets F777 / F77A.
HALF_NAME_CHAR_TO_CODE.setdefault('ー',0xF777)
HALF_NAME_CHAR_TO_CODE.setdefault('・',0xF77A)

def _name_code_bytes(code):
    return bytes([code]) if code <= 0xFF else bytes([(code>>8)&255,code&255])

def _normalize_player_name_char(ch):
    # Direct keyboard convenience: Pawapoke's ordinary player-name table uses
    # full-width Latin capitals/digits. Accept ASCII and convert automatically.
    if 'A' <= ch <= 'Z': return chr(ord('Ａ') + ord(ch) - ord('A'))
    if 'a' <= ch <= 'z': return chr(ord('Ａ') + ord(ch) - ord('a'))
    if '0' <= ch <= '9': return chr(ord('０') + ord(ch) - ord('0'))
    return ch

def _player_name_input_tokens(text):
    """Yield (normalized glyph, explicitly-half-width, source token)."""
    i=0
    while i<len(text):
        ch=text[i]
        if 0xFF61<=ord(ch)<=0xFF9F:
            token=ch
            if i+1<len(text) and text[i+1] in ("ﾞ","ﾟ"):
                pair=ch+text[i+1]
                if pair in _HALF_KANA_TO_NORMAL:token=pair;i+=1
            normal=_HALF_KANA_TO_NORMAL.get(token)
            if normal is None:raise ValueError(f'半角カナをF7文字へ変換できません: {token!r}')
            yield normal,True,token
        else:
            yield _normalize_player_name_char(ch),False,ch
        i+=1

def encode_name_text(text, maxbytes=12, force_half=False):
    out=bytearray()
    for ch,typed_half,source in _player_name_input_tokens(text):
        use_half=force_half or typed_half
        code=(HALF_NAME_CHAR_TO_CODE.get(ch) if use_half else NAME_CHAR_TO_CODE.get(ch))
        if code is None:
            mode="半角F7" if use_half else "通常"
            raise ValueError(f'{mode}文字コード表にない文字: {source!r}')
        bb=_name_code_bytes(code)
        if len(out)+len(bb)>maxbytes: raise ValueError(f'名前コードが{maxbytes} bytesを超えます ({len(out)+len(bb)}/{maxbytes})')
        out.extend(bb)
    out.extend(b'\x00'*(maxbytes-len(out)))
    return out

def decode_name_bytes(data):
    out=[];i=0;data=bytes(data[:12])
    while i<len(data) and data[i]:
        if 0xE8<=data[i]<=0xF7 and i+1<len(data): code=(data[i]<<8)|data[i+1];i+=2
        else: code=data[i];i+=1
        out.append(NAME_CODE_TO_CHAR.get(code,WIFI_NAME_CODE_TO_CHAR.get(code,f'<{code:04X}>' if code>255 else f'<{code:02X}>')))
    return ''.join(out)

def decode_name_entry_bytes(data):
    """Decode for the editor, showing F7 kana as actual half-width Unicode."""
    out=[];i=0;data=bytes(data[:12])
    while i<len(data) and data[i]:
        if 0xE8<=data[i]<=0xF7 and i+1<len(data):code=(data[i]<<8)|data[i+1];i+=2
        else:code=data[i];i+=1
        ch=NAME_CODE_TO_CHAR.get(code,WIFI_NAME_CODE_TO_CHAR.get(code,f'<{code:04X}>' if code>255 else f'<{code:02X}>'))
        if 0xF700<=code<=0xF7FF:
            ch=_NORMAL_TO_HALF_KANA.get(ch,ch)
            # F75B-F774 hold full-width 'Ａ'-'Ｚ' and F74C-F755 hold '０'-'９'.
            # Show them half-width, otherwise an all-F7 name like ＺＥＡＲＴＨ looks
            # identical to the ordinary full-width spelling that uses different bytes.
            if len(ch)==1 and ('Ａ'<=ch<='Ｚ' or '０'<=ch<='９'):
                ch=chr(ord(ch)-0xFEE0)
        out.append(ch)
    return ''.join(out)

def name_raw_display_units(data):
    full=half=0;i=0;data=bytes(data[:12])
    while i<len(data) and data[i]:
        if 0xE8<=data[i]<=0xF7 and i+1<len(data):code=(data[i]<<8)|data[i+1];i+=2
        else:code=data[i];i+=1
        glyph=NAME_CODE_TO_CHAR.get(code,WIFI_NAME_CODE_TO_CHAR.get(code,''))
        if 0xF700<=code<=0xF7FF:half+=1
        elif len(glyph)>1:half+=len(glyph)   # F3xx/F4xx composites render as N half cells
        else:full+=1
    return full,half

def name_raw_layout_warning(data):
    # Thresholds derived from the 127 genuine registered names in a real Poke12 SAV.
    # Observed (full, half) combinations include (4,0), (3,0), (2,6), (2,4), (2,3),
    # (1,4), (0,6) - so the old "full+half" envelope rejected real in-game names
    # such as 'G.銀森ﾞｰｲｼ' (full 2 / half 6). The only hard limit is the 12-byte
    # name field, which encode_name_text already enforces; observed maxima are
    # full<=4 and half<=6.
    full,half=name_raw_display_units(data)
    if full>4:return f'表示枠注意: 全角{full}文字は実機データで確認されていません（最大4）'
    if half>6:return f'表示枠注意: 半角{half}文字は12バイト枠に収まりません（最大6）'
    return ''

def name_display_units(text):
    full=half=0
    for ch in text:
        code=NAME_CHAR_TO_CODE.get(ch)
        if code is None: continue
        if 0xF700<=code<=0xF7FF: half+=1
        else: full+=1
    return full,half

def name_layout_warning(text):
    full,half=name_display_units(text)
    ok=((full==4 and half==0) or (full==3 and half<=1) or (full==2 and half<=3) or (full==1 and half<=4) or (full==0 and half<=6) or (full<4 and half==0))
    return '' if ok else f'表示枠注意: 全角{full} / 半角{half} はWiki推奨組合せ外'

# Original-pitch name codes. Wiki regular range: 00 + 51-CC + FF terminator.
_ORI_ROWS=[(0x51,"アイウエオカキクケコサシスセソ"),(0x60,"タチツテトナニヌネノハヒフヘホマ"),(0x70,"ミムメモヤユヨラリルレロワヲンヴ"),(0x80,"ァィゥェォッャュョガギグゲゴザジ"),(0x90,"ズゼゾダヂヅデドバビブベボパピプ"),(0xA0,"ペポ０１２３４５６７８９ＡＢＣＤ"),(0xB0,"ＥＦＧＨＩＪＫＬＭＮＯＰＱＲＳＴ"),(0xC0,"ＵＶＷＸＹＺー魔球改真超号")]
ORI_NAME_CODE_TO_CHAR={0x00:"　"}
for base,chars in _ORI_ROWS:
 for i,ch in enumerate(chars):ORI_NAME_CODE_TO_CHAR[base+i]=ch
ORI_NAME_CHAR_TO_CODE={ch:code for code,ch in ORI_NAME_CODE_TO_CHAR.items()}
for i,ch in enumerate("ABCDEFGHIJKLMNOPQRSTUVWXYZ"):ORI_NAME_CHAR_TO_CODE[ch]=0xAC+i
for i,ch in enumerate("abcdefghijklmnopqrstuvwxyz"):ORI_NAME_CHAR_TO_CODE[ch]=0xAC+i
for i,ch in enumerate("0123456789"):ORI_NAME_CHAR_TO_CODE[ch]=0xA2+i
ORI_NAME_CHAR_TO_CODE[" "]=0
_ORI_ASCII_TRANS=str.maketrans("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789","ＡＢＣＤＥＦＧＨＩＪＫＬＭＮＯＰＱＲＳＴＵＶＷＸＹＺＡＢＣＤＥＦＧＨＩＪＫＬＭＮＯＰＱＲＳＴＵＶＷＸＹＺ０１２３４５６７８９")
def normalize_ori_text(text):return text.translate(_ORI_ASCII_TRANS)
def encode_ori_name(text):
 text=normalize_ori_text(text.strip())
 if len(text)>9:raise ValueError("オリ変名は最大9文字")
 bad=[ch for ch in text if ch not in ORI_NAME_CHAR_TO_CODE]
 if bad:raise ValueError("オリ変名で正規使用不可: "+" ".join(sorted(set(bad)))+"（正規範囲 00 / 51–CC / FF終端）")
 out=bytearray(ORI_NAME_CHAR_TO_CODE[ch] for ch in text)
 if len(out)<9:out.append(0xFF);out.extend(bytes(9-len(out)))
 return out[:9]
def decode_ori_name(data):
 out=[]
 for x in data[:9]:
  if x==0xFF:break
  out.append(ORI_NAME_CODE_TO_CHAR.get(x,f"<{x:02X}>"))
 s="".join(out)
 return "" if not s.strip() else s

# ---- QR I/O ---------------------------------------------------------------
import qrcode.util as _qru
class _KanjiQRData(_qru.QRData):
    def __init__(self,text):
        self.mode=_qru.MODE_KANJI; self.text=text; self.data=text.encode("shift_jis")
        if len(self.data)!=2*len(text): raise ValueError("QR Kanji modeにできない文字が含まれています")
    def __len__(self): return len(self.text)
    def write(self,buf):
        for i in range(0,len(self.data),2):
            v=(self.data[i]<<8)|self.data[i+1]
            if 0x8140<=v<=0x9FFC: v-=0x8140
            elif 0xE040<=v<=0xEBBF: v-=0xC140
            else: raise ValueError(f"QR Kanji mode範囲外: {v:04X}")
            buf.put((v>>8)*0xC0+(v&0xFF),13)
def _write_png_matrix(matrix,path,scale=8,border=4):
    import struct,zlib
    n=len(matrix);w=(n+border*2)*scale;rows=[]
    for y in range(-border,n+border):
        rr=[]
        for x in range(-border,n+border):
            rr.extend([0 if (0<=x<n and 0<=y<n and matrix[y][x]) else 255]*scale)
        rr=bytes(rr)
        for _ in range(scale):rows.append(bytes([0])+rr)
    raw=b"".join(rows)
    def chunk(t,d):return struct.pack(">I",len(d))+t+d+struct.pack(">I",zlib.crc32(t+d)&0xffffffff)
    png=bytes([137,80,78,71,13,10,26,10])+chunk(b"IHDR",struct.pack(">IIBBBBB",w,w,8,0,0,0,0))+chunk(b"IDAT",zlib.compress(raw,9))+chunk(b"IEND",b"")
    open(path,"wb").write(png)
def _qr_matrix(text):
    compact="".join(ch for ch in text if not ch.isspace())
    qr=qrcode.QRCode(error_correction=qrcode.constants.ERROR_CORRECT_M,box_size=1,border=0)
    qr.add_data(_KanjiQRData(compact),optimize=0);qr.make(fit=True)
    return qr.get_matrix(),qr.version
def qr_write_file(text,path):
    matrix,_=_qr_matrix(text);_write_png_matrix(matrix,path,8,4);return path
def qr_read_file(path):
    try: import cv2
    except Exception: raise RuntimeError("QR画像読込にはOpenCV(cv2)が必要です。QR表示/保存にはpip不要です。")
    im=cv2.imread(str(path))
    if im is None: raise ValueError("画像を開けません")
    try:
        text,pts,_=cv2.QRCodeDetector().detectAndDecode(im)
        if not text: raise ValueError("QRコードを検出/復号できません")
        return text
    except UnicodeDecodeError as e:
        try:return e.object.decode("shift_jis")
        except UnicodeDecodeError:raise ValueError("QR payloadをShift-JISとして復号できません")

# ---- Validation --------------------------------------------------------------
def validate_password_text(text):
    result={"valid":False,"length":0,"stage":"input","message":"","raw":None}
    # preserve only whitespace as ignorable; unknown visible chars are errors
    compact="".join(ch for ch in text if not ch.isspace())
    result["length"]=len(compact)
    bad=[ch for ch in compact if ch not in ALPHABET]
    if bad:
        result["message"]="未知のパス文字: "+" ".join(sorted(set(bad)))
        return result
    over_limit = len(compact)>GAME_PASSWORD_LIMIT
    try:
        raw,ok,calc=decode(compact)
        result["raw"]=raw
        if not ok:
            result["stage"]="checksum";result["message"]=f"checksum不一致 stored={raw[12]:02X} {raw[13]:02X} calc={calc[0]:02X} {calc[1]:02X}"
            return result
        repw,_=encode(bytearray(raw))
        if repw!=compact:
            result["stage"]="roundtrip";result["message"]=f"checksum OKだが再encode不一致 ({len(repw)} vs {len(compact)} chars)"
            return result
        result.update(valid=True,stage="OK",message=f"VALID / checksum OK / round-trip {len(compact)}/{len(compact)}" + (" / GAME INPUT LIMIT EXCEEDED" if over_limit else ""))
        return result
    except Exception as e:
        result["stage"]="structure";result["message"]=f"復号構造エラー: {e}"
        return result

# User-confirmed real-hardware vectors. Expected semantic checks are deliberately
# separate from codec validity so a UI-field mapping bug cannot fake codec success.
GOLDEN = {
 # 実機QRから取得した検証ベクタ（melonDS画面のQRをデコードしたもの）
 "suiseiseki_qr_123":"べおざよへあぢたくすむせるよずちこれひねぬあけあでどどへはまぜだめでせうねれちでべこにづかうおわみるつよえばさべごぢふにうくあわもしゆぢめしぎぼげふへぜぢめかどびんこかよちまつはめるゆそほぶまえにのにふさきてひるぼこじぢどぬねえごあちふでほぬらで",
 "old_saikyo_no1_128":"ぞれまぐへゆさたむけてがるねせけこれでねふれひどもあきがわゆたざらひでくずぼこぼもそぼづれぢさへそぢらざめみどずまめづるごぢむめぞぢをうでんほまぬらごづごねざげにぎぼくやふひざろたでせぢほかせべるさぜたままほへおさぶろてじあじぼじさすづこひがざわねわじごわ",
 "terao": 'ろもをびはそゆなをくてきろめにずしまあづめごうぶさぎちがうらぢごいろぎぼばぼぬけむふひえこではふ',
 "kamijo": 'かつおまはそああをくてきぞでせじぜほほもすあやましうでよめのずぢほぬざづどでぐるぬでやだけのればいしついねご',
 "akagawa": 'ろつぶびはそあしがよまがすばれれせおぎたさおみせしすきぞてびちおつそぞぼはづにづびくむさ',

 "old_strongest_127": "ぞれまぐへゆさたむけてがるねせけこれできのほどかぢみむでかむあざらでむあごぞゆそずなさづやめでれぐめらぜくらどばひきらつてぢひべげれみざれくふにひばほせぢにぼすのびさかやふまめてたひるわもいけがこおえすめごまべでんどよろごらうちばよおらざちえそろろこじで",
 "a_44": "ぞぞぶびたみにぬふびませむねごのておまべざけぞなぢしゆがはつゆげびどにみなほあざげやはぶ",
}
def golden_selftest():
    report=[]
    for label,pw in GOLDEN.items():
        raw,ok,calc=decode(pw);repw,_=encode(bytearray(raw))
        report.append((label,len(pw),ok,repw==pw,decode_name_bytes(raw[14:26])))
        if not ok or repw!=pw: raise AssertionError(label+" golden vector failed")
    return report

# ---- Full editor v0.4 -------------------------------------------------------
POS=["0 (なし)","投","捕","一","二","三","遊","外"]+[str(i) for i in range(8,16)]
TEAMS=['0 (0) ドラゴンズ','1 (1) ジャイアンツ','2 (2) ベイスターズ','3 (3) スワローズ','4 (4) カープ','5 (5) タイガース','6 (6) ホークス','7 (7) ライオンズ','8 (8) バファローズ','9 (9) マリーンズ','A (10) ファイターズ','B (11) イーグルス','C (12) 極亜久高校','D (13) モグラーズ','E (14) オクトパス','F (15) 日の出高校']
SKINS=["0 普通","1 白","2 黒","3 茶色","4 黒表示(外れ値)","5 透明表示(外れ値)"]+[str(i) for i in range(6,16)]
ORIGINS=["-","ポケ1","ポケ2","戦争","ポケ3(元サイボーグ)","地雷","ポケ3(サイボーグ)","ポケ4","ファンタジー","ポケ5","忍者","ポケ5オレペナ","ポケ6","しあわせ","ポケ6オレペナ","ポケ1･2の1","ポケ1･2の2","ポケ1･2戦争","ポケ1･2オレペナ","ポケ7","大正奇譚","ポケ7オレペナ","ポケ8","昭和冒険","ポケ8オレペナ","ポケダッシュ","地獄","ポケ9","宇宙","少森寺","ポケ9オレペナ","ポケ10","ディッガー","ポケ10オレペナ","ポケ10おためし","パワポケ甲子園","DS甲子園","パワプロ14","パワポケ11","11･ハタ人間","11･グッピー","11･オレペナ","11･おためし","パワポケ12","12･秘密結社","12･グッピー","12･オレペナ","12･おためし"]
BATFORMS=[f"ノーマル{i}" for i in range(1,8)]+[f"オープン{i}" for i in range(1,11)]+[f"クローズド{i}" for i in range(1,8)]+["振り子","一本足","神主"]
PITCHFORMS=[f"オーバースロー{i}" for i in range(1,17)]+[f"スリークォーター{i}" for i in range(1,14)]+[f"サイドスロー{i}" for i in range(1,14)]+[f"アンダースロー{i}" for i in range(1,5)]
ABILITY_ROWS={
70:["広角打法","野手威圧感","途中交代","強振多用","代走要員","守備要員","代打要員","野手人気者"],
71:["内野安打○","サヨナラ男","流し打ち","逆境○","対左投手△","対左投手○","チャンス△","チャンス○"],
72:["体当たり","ヘッドスライディング","バント◎","バント○","パワーヒッター","アベレージヒッター","キャッチャー◎","キャッチャー○"],
73:["いぶし銀","走塁△","走塁○","守備職人","ブロック○","送球○","盗塁△","盗塁○"],
74:["ケガ△","ケガ○","三振","ムード△","ムード○","連打○","粘り打ち","固め打ち"],
75:["GBカラー","代打○","エラー","ムードメーカー","満塁男","安定感","初球○","野手ムラッ気"],
76:["積極打法","慎重盗塁","慎重打法","ミート多用","チャンスメーカー","持続","対左投手◎","チャンス◎"],
77:["積極守備","レーザービーム","ハイボールヒッター","ローボールヒッター","ゲッツー崩し","チームプレイ△","チームプレイ○","積極盗塁"],
78:["プルヒッター","ピボットマン","ベアハンドキャッチ",None,"盗塁◎","ケガ◎","センス△","センス○"],
79:["サブポジ○","帳尻合わせ","悪球打ち","天然芝○","送球△","対左投手×","チャンス×","内野安打◎"],
80:["豪力","神速","奪力","闘気","ヘッドスライディング2",None,None,"サブポジ△"],
81:[None,None,None,None,None,None,None,"緊縛"],
86:[None,None,"四球","投手威圧感","中継ぎエース","リリーフエース","完投タイプ","投手人気者"],
87:["勝ち運","一発","対左打者△","対左打者○","ランナー△","寸前△","ピンチ△","ピンチ○"],
88:["短気","打球反応○","けん制○","スロースターター","尻上がり","投手ムラッ気(効果無)","回復△","回復○"],
89:["逃げ球","打たれ弱い","打たれ強い","ノビ△","ノビ○","キレ△","キレ○","負け運"],
90:["速球中心","低め○","闘志","ポーカーフェイス","重い球","クイック△","クイック○","リリース○"],
91:["ノビ◎","球持ち○","対強打者○","フルカウント○","奪三振","軽い球","テンポ○","変化球中心"],
92:[None,None,None,None,"バント処理","乱調","ホーム○","ジャイロボール"],
93:["気迫","呪縛","絶倫","剛球","鉄腕",None,None,None],
}
THIRD_PITCH_SET_CHOICES=[f"{i} ({i:X})" for i in range(16)]

MINI_FACE_NAMES=['パワプロくん-1', 'メカパワプロくん', 'パワプロくん-2', 'パワプロくん-3', 'パワプロくん-4', 'メガネ(カメダなど)', 'プロペラカメダ', 'いぬ', 'がいどう', 'ひらやま', 'みずはら', 'むらかみ', 'たけだ', 'ボブ', 'みたか', 'さとう', 'たなか', 'すずき', 'ぎんじ', 'かねお', 'パルオ', 'トイくん', 'こまさか', 'こうもと', 'まつくら', 'ふゆの', 'いかりまもる', 'アフロいかり', 'いかりすすむ', 'まさかね', 'せいどう', 'はがね', '野球マスク', 'ふるさわ', 'はたやま', 'みずき', 'くらがり', 'ドミオ', 'メカドミオ', 'おづの', 'アルベルト', 'バッタ男', 'たかゆき', 'アンヌ', 'はっとり', 'ネロ', 'オクトパス選手', 'きず', 'ドルフィンズ選手', 'きおか', 'フラワーズ選手', 'プロペラ団選手', 'しまおか', 'やまもと', 'もりもと', 'こやま', 'つつみ', 'おおがみ', 'むらた', 'いしだ', 'うえだ', 'あきほ', 'くろの', 'まがつ', 'あかさか', 'ふぐり', 'しゃーろっく', 'こすぎ', 'イサム', 'もろぼし', 'うまい', 'あおの', 'みふね', 'むらやま', 'ちばやし', 'ゆうまクン', 'たかだ', 'もりた', 'カビンダ', 'ちばやし(兄)', 'いさりび', 'ほるひす', 'おくの', 'かちょう', 'もきち', 'ボンド', 'だいとうりょう', 'わたなべ', 'なかた', 'みたに', 'あばた', 'さが', 'あおい', 'だいごうげつ', '男-1', '男-2', '男-3', '男-4', '男-5', '男-6', 'レッド', 'だいば', 'しらいし', 'もりもり', 'ありた', 'のまる', 'あずま', 'かつの', 'あわお', 'うづき', 'つるた', 'めしあ', 'みずはら', 'あれく', 'えぐぜ', 'ぷると', 'くろだ', 'ほんだ', 'くらがりあきら', 'めだち', 'はやし', 'いしなか', 'きむら', 'かがやき-1', 'かがやき-2', 'おにざめ', 'おとこ', 'まじん', '選手パターン1-1', '選手パターン1-2', '選手パターン1-3', '選手パターン1-4', '選手パターン2-1', '選手パターン2-2', '選手パターン2-3', '選手パターン2-4', '選手パターン3-1', '選手パターン3-2', '選手パターン3-3', '選手パターン3-4', '選手パターン4-1', '選手パターン4-2', '選手パターン4-3', '選手パターン4-4', '親父ボール', 'おの', 'はるかわ', 'いちどう', 'はしば', 'あけち', 'にのみや', 'まうす', 'とくがわ', 'さくら', 'わんこ', 'さいば', 'そら', 'うらみ', 'もんじゅ', 'さくらぎ', 'かんた', 'きかわ', 'ごんだ', 'なみき', 'あおしま', 'おおむら', 'でんし', 'すいま', 'はく', 'しろた', 'じもん', 'ピエロ', 'カニ男', 'なつき', 'たけみ', 'さち', 'つばき', 'ソルジャー', 'ムシャ', 'ロボ', 'ばんちょう', 'えちご', 'いわた', 'たじま', 'かんどり', 'ひきた', 'いいじめ', 'きそう', 'きたの', 'まうす-2', 'チーム員-1', 'チーム員-2', 'てんどう-1', 'てんどう-2', 'さいばい高', 'へいめん高', 'タクシー高', 'グレイテスト高', 'さいばん高', 'オリエント高', 'てんかむそう高', 'あしぬま', 'かりむら', 'はぐるま', 'かきもと(兄)', 'かきもと(弟)', 'げんち', 'パワプロくん-5', 'パワプロくん(アバター)', 'ウズキ', 'サイデン', 'バル', 'スター', 'イーエル', 'アッシュ', 'ユウジロー', 'シズマ', 'ゼット', 'レン', 'パカ', 'ピンク', 'ミーナ', 'メガネ(アバター)', 'ナイトメアーズ選手', 'アドミラル', 'マイティブラザーズ選手', 'ツンドラーズ選手', 'ネットセイバーズ選手', 'しまだ']
def unpack_appearance(r):
 b=r[96:100]
 slots=[i for i in (0,1,2) if b[i]]+[3]
 vals=[b[x] for x in slots]
 origin=vals[0];i=1;ts=hi=lo=0
 if b[0]:ts=vals[i];i+=1
 if b[1]:hi=vals[i];i+=1
 if b[2]:lo=vals[i];i+=1
 return origin,ts&15,(ts>>4)&15,(hi<<8)|lo

def pack_appearance(r,origin,team,skin,face):
 ts=((skin&15)<<4)|(team&15);hi=(face>>8)&255;lo=face&255
 slots=[i for i,v in enumerate((ts,hi,lo)) if v]+[3]
 vals=[origin&255]+[v for v in (ts,hi,lo) if v]
 out=bytearray(4)
 for sl,v in zip(slots,vals):out[sl]=v
 r[96:100]=out

def poke12_structure_warnings(r):
 w=[]
 if any(r[i] for i in range(100,105)):w.append("INVALID: Wiki仕様ではbyte101–105は00必須（非0は入力不能）")
 # Wiki Poke12 minimal/native values: byte95=20 decimal (14h), byte96=48 decimal (30h).
 # byte95 bit0x10 is intentionally user-toggleable; with it OFF the corresponding valid base is 04h.
 exp95=0x14 if (r[94]&0x10) else 0x04
 if r[94]!=exp95:w.append(f"INVALID/要確認: byte95 選手判定がWiki標準 {exp95:02X} と異なる ({r[94]:02X})")
 if r[95]!=0x30:w.append(f"INVALID/要確認: byte96 選手判定がWiki標準30と異なる ({r[95]:02X})")
 if (r[105]&0xFC):w.append(f"INVALID/要確認: byte106上位6bitは未使用 ({r[105]:02X})")
 return w

def name_table_audit():
 checks={
  "E975=柏":NAME_CODE_TO_CHAR.get(0xE975)=="柏","F229=・":NAME_CODE_TO_CHAR.get(0xF229)=="・","F22D=麻":NAME_CODE_TO_CHAR.get(0xF22D)=="麻",
  "P12 F3A2=G.":NAME_CODE_TO_CHAR.get(0xF3A2)=="G.","P12 F3A5=攝":NAME_CODE_TO_CHAR.get(0xF3A5)=="攝","P12 F3AD=齊":NAME_CODE_TO_CHAR.get(0xF3AD)=="齊",
  "P12 F3B0=奎":NAME_CODE_TO_CHAR.get(0xF3B0)=="奎","P12 F3B1=洸":NAME_CODE_TO_CHAR.get(0xF3B1)=="洸","P12 F3B2=踐":NAME_CODE_TO_CHAR.get(0xF3B2)=="踐",
  "P12 F3B3 empty":0xF3B3 not in NAME_CODE_TO_CHAR,"P10-13 F4B2=朗":NAME_CODE_TO_CHAR.get(0xF4B2)=="朗","F4BF=條":NAME_CODE_TO_CHAR.get(0xF4BF)=="條",
  "F700=ア":NAME_CODE_TO_CHAR.get(0xF700)=="ア","F751=０":NAME_CODE_TO_CHAR.get(0xF751)=="０","F775=＿":NAME_CODE_TO_CHAR.get(0xF775)=="＿","F7C0=あ":NAME_CODE_TO_CHAR.get(0xF7C0)=="あ",
  "WiFi F500=AB":WIFI_NAME_CODE_TO_CHAR.get(0xF500)=="AB","WiFi F514=田":WIFI_NAME_CODE_TO_CHAR.get(0xF514)=="田","WiFi F6CB=ヶ":WIFI_NAME_CODE_TO_CHAR.get(0xF6CB)=="ヶ",
  "F5/F6 decode":decode_name_entry_bytes(bytes.fromhex("F514F690"))=="田セ",
 }
 return checks


HAT_PHOTOS={0x0000:'写真なし',0x0003:'工藤',0x0021:'山本昌',0x0026:'高木',0x0032:'立浪',0x0036:'緒方',0x003B:'山﨑武',0x0043:'木田',0x004F:'大道',0x0059:'堀',0x005E:'石井琢',0x005F:'谷繁',0x0091:'矢野',0x00A2:'木村拓',0x00A5:'下柳',0x00A8:'村松',0x00B1:'石井一',0x00B8:'金本',0x00C3:'中村紀',0x00C6:'萩原',0x00CA:'桧山',0x00CC:'三浦',0x00D7:'菊地原',0x00E0:'佐伯',0x00ED:'豊田',0x00F2:'牧野',0x0104:'大村',0x0106:'小野',0x0107:'金子誠',0x010A:'小久保',0x0117:'平尾',0x0118:'福浦',0x0119:'福地',0x012B:'稲葉',0x012D:'サブロー',0x0130:'金村曉',0x0131:'憲史',0x0133:'河原',0x0135:'北川',0x013C:'嶋',0x0144:'多村',0x0146:'西口',0x0148:'橋本将',0x014B:'福盛',0x014F:'宮本',0x0153:'横山',0x0156:'相川',0x0159:'荒木',0x0166:'清水',0x016C:'鶴岡',0x016F:'仁志',0x0170:'長谷川',0x0174:'日高',0x017D:'宮出',0x0185:'ローズ',0x0186:'井口',0x0188:'石井義',0x018F:'小笠原',0x019A:'小坂',0x019B:'小林宏',0x019C:'小山',0x01A0:'塩崎',0x01A1:'柴原',0x01A5:'関本',0x01A7:'高橋',0x01AA:'谷',0x01AF:'濱中',0x01B4:'松中',0x01B9:'森野',0x01BC:'和田',0x01C1:'飯山',0x01C2:'五十嵐',0x01C5:'井端',0x01CC:'倉',0x01D0:'清水',0x01D3:'鈴木',0x01D4:'高須',0x01D6:'高橋光',0x01D7:'高橋由',0x01D8:'ユウキ',0x01E4:'古城',0x01F6:'赤田',0x01F8:'新井',0x01FA:'岩瀬',0x01FD:'小笠原',0x0203:'川越',0x0206:'金城',0x0207:'英智',0x0208:'小池',0x020C:'里崎',0x0212:'建山',0x0215:'二岡',0x0216:'東出',0x0219:'福原',0x021B:'藤井',0x021C:'藤川',0x0220:'星野',0x0225:'水田',0x0227:'森笠',0x0228:'森本',0x023B:'青木勇',0x023C:'朝倉',0x023D:'岩隈',0x0243:'葛城',0x0247:'川﨑',0x0248:'木塚',0x024E:'清水直',0x0253:'高橋尚',0x0256:'田中賢',0x025F:'藤井',0x0298:'赤星',0x029A:'阿部',0x02A1:'内川',0x02A2:'大久保',0x02A3:'大沼',0x02A5:'岡本',0x02A7:'加藤康',0x02AC:'佐藤',0x02B5:'廣瀬',0x02B6:'藤田',0x02B7:'藤本',0x02B8:'帆足',0x02BD:'山本',0x02BE:'吉見',0x02BF:'渡辺俊',0x02C2:'カブレラ',0x02D3:'マクレーン',0x02D7:'ラミレス',0x02E2:'シコースキー',0x02E4:'真田',0x02E6:'鈴木',0x02ED:'大竹',0x02F0:'石原',0x02F2:'末永',0x02FA:'石川',0x02FC:'松元',0x02FD:'野口',0x02FE:'畠山',0x0307:'新沼',0x030C:'安藤',0x0315:'平野',0x0316:'セギノール',0x0322:'江尻',0x032D:'細川',0x0344:'杉内',0x0345:'寺原',0x0358:'栗原',0x035C:'田上',0x0367:'天谷',0x036F:'ワズディン',0x0378:'林',0x038F:'高橋',0x0393:'鉄平',0x03A8:'福川',0x03CF:'桜井',0x03D1:'喜田剛',0x03D3:'狩野',0x03DD:'後藤',0x040D:'中島',0x040E:'中村',0x040F:'栗山',0x0413:'有銘',0x0415:'近藤',0x0420:'塀内',0x0421:'辻',0x0422:'今江',0x042A:'神内',0x042F:'山崎',0x046C:'小林正',0x046F:'永川',0x0475:'館山',0x0482:'村田',0x0483:'吉村',0x0486:'武山',0x0489:'江草',0x048B:'久保田',0x048D:'林威助',0x0493:'ウィリアムス',0x0494:'加藤',0x049D:'オーティズ',0x04A3:'武田久',0x04A4:'小谷野',0x04A5:'紺田',0x04A7:'鶴岡',0x04A9:'小野寺',0x04AB:'上本',0x04AC:'後藤',0x04AD:'坂口',0x04B2:'大西',0x04B3:'下山',0x04BA:'西岡',0x04BB:'早坂',0x04BD:'和田',0x04C0:'森本',0x04ED:'リック',0x0506:'フェルナンデス',0x0510:'内海',0x051C:'川岸',0x0522:'川島亮',0x0524:'青木',0x052B:'鳥谷',0x052C:'筒井',0x0532:'一輝',0x0537:'糸井',0x0539:'押本',0x053A:'稲田',0x0542:'G.G.佐藤',0x0544:'香月',0x054A:'内',0x054C:'田中雅',0x054E:'成瀬',0x0550:'馬原',0x0551:'城所',0x0552:'明石',0x055E:'ベニー',0x0576:'李承燁',0x057B:'チェン',0x0583:'ゴンザレス',0x0589:'一場',0x0590:'松岡',0x0591:'川本',0x0592:'田中浩',0x0595:'野間口',0x0597:'木村正',0x0598:'東野',0x0599:'亀井',0x059C:'川井',0x059D:'中田',0x059F:'石井',0x05AA:'梅津',0x05AF:'藤田',0x05B3:'石川',0x05B6:'能見',0x05BD:'赤松',0x05C4:'ダルビッシュ',0x05C5:'M.中村',0x05C8:'菊地',0x05CB:'工藤',0x05CC:'涌井',0x05CD:'片岡',0x05D1:'金子',0x05D7:'久保康',0x05DA:'竹原',0x05DB:'大松',0x05E8:'クルーン',0x060B:'今井',0x060C:'齊藤',0x0617:'村中',0x0618:'川端',0x061C:'山口',0x061E:'銀仁朗',0x0621:'平田',0x062B:'大和',0x0630:'梵',0x0634:'青山',0x0637:'木谷',0x0639:'草野',0x063B:'福田',0x063D:'越智',0x063E:'脇谷',0x0642:'八木',0x0643:'川島慶',0x0644:'武田勝',0x0645:'小山',0x0648:'武内',0x064B:'飯原',0x064C:'平野佳',0x064D:'岸田',0x0658:'吉見',0x0659:'藤井',0x065E:'松田',0x065F:'藤岡',0x0661:'本多',0x0663:'岩田',0x0665:'渡辺',0x0667:'川﨑',0x0682:'グリン',0x068D:'田中',0x068F:'前田健',0x0695:'坂本',0x06AB:'岸',0x06AC:'高崎',0x06AE:'下園',0x06B1:'永井',0x06B2:'嶋',0x06B4:'渡辺直',0x06B7:'青木高',0x06B9:'小松',0x06BA:'大引',0x06C2:'萩野',0x06C4:'中郷',0x06CA:'大隣',0x06CB:'髙谷',0x06CD:'長谷川',0x06D5:'岩﨑',0x06D6:'大﨑',0x06D8:'浅尾',0x06DA:'岩﨑達',0x06DE:'糸数',0x06E4:'ボーグルソン',0x06EF:'山口',0x06F7:'松本',0x0703:'中村真',0x0704:'スウィーニー',0x0707:'李炳圭',0x0709:'グライシンガー',0x070A:'ガイエル',0x0712:'オビスポ',0x0721:'由規',0x0739:'唐川',0x073F:'中田',0x077E:'小窪',0x078B:'小瀬',0x078E:'長谷部',0x0790:'聖澤',0x0791:'大場',0x0792:'久米',0x0795:'伊藤',0x0797:'多田野',0x0798:'宮西',0x0799:'村田',0x07AE:'ボカチカ',0x07AF:'林昌勇',0x07B0:'スレッジ',0x07B1:'ブラゼル',0x07BA:'ルイス',0x07BC:'シュルツ',0x07BD:'アッチソン',0x07C0:'ホールトン',0x07C1:'デラロサ',0x07C2:'ネルソン',0x07D3:'グウィン',0x09B7:'山崎',0x09B8:'細山田',0x09C3:'小松',0x09C6:'野本',0x09E4:'攝津',0x09EC:'藤原',0x09EE:'井坂',0x09F3:'上野',0x09FF:'大野',0x0A05:'谷元',0x0A0C:'野上',0x0A12:'ロー',0x0A14:'李恵踐',0x0A16:'ファルケンボーグ',0x0A18:'ジャマーノ',0x0A19:'デントナ',0x0A1A:'ウォーランド',0x0A1C:'マストニー',0x0A21:'ブランコ',0x0A22:'パヤノ',0x0A24:'レスター',0x0A26:'ジョンソン',0x0ABF:'バーナムJr.',0x0AC0:'ランビン',0x0D90:'リンデン',0x0D91:'フィリップス',0x0D92:'ベイリス',0x0D93:'ランドルフ'}

# ---- v1.59: 研究用の生エンコード＋アドレス表データ -----------------------------
def encode_raw(raw):
 """RAW106をflags/checksumを再計算せずにそのまま文字化する（任意タブ編集のOFF用）。
 byte1–12の圧縮フラグが立っているbyteだけを送る＝実機ローダと同じ解釈。"""
 if len(raw)!=106:raise ValueError("RAW must be 106 bytes")
 r=bytearray(raw);a=bytearray(r[:14]);present={}
 for q,refs in enumerate(FM):
  for j,n in enumerate(refs):
   if n:present[n]=bool(r[q]&(1<<(7-j)))
 for n in range(15,107):
  if present.get(n,False):a.append(r[n-1])
 return "".join(ALPHABET[x] for x in b2v(mos(ncomp(a))))

def poke12_byte_map():
 """wiki『ポケ12の仕様』のバイト構造表を移植。{byte:(8セル[bit7..bit0], 最小設定値, 備考)}"""
 def full(n):return [f"{n} {1<<(7-j)}" for j in range(8)]
 def nib(a,b):return [f"{a} {8>>j}" for j in range(4)]+[f"{b} {8>>j}" for j in range(4)]
 U=["未使用"]*8;m={}
 for q,refs in enumerate(FM):m[q+1]=([f"{n}圧縮フラグ" if n else "未使用" for n in refs],"","自動計算（そのbyteが0以外なら1）")
 m[13]=(full("チェックサム1"),"","sum=byte1–12+15–106 / (sum+23) mod 256")
 m[14]=(full("チェックサム2"),"","255-(sum mod 256)")
 for i in range(12):m[15+i]=(full(f"名前コード{i+1}"),"1" if i==0 else "","選手名（漢字などは2byte）")
 m[27]=(["未使用","両打","左打","左投"]+[f"メインポジション {8>>j}" for j in range(4)],"1","")
 m[28]=(nib("サブポジション1","サブポジション2"),"","")
 m[29]=(full("パワー"),"","")
 m[30]=(nib("ミートカーソル","肩力"),"17","")
 m[31]=(nib("走力","守力"),"17","")
 m[32]=(full("打撃フォーム"),"","")
 m[33]=(full("背番号"),"","")
 m[34]=(nib("弾道","耐エラー"),"17","")
 for b in (35,36,37,68,69,82,83,84,85,94,101,102,103,104,105):m[b]=(U,"","未使用：値を入れてもパス入力・登録は通るが、SAVに置き場がなく再出力で消える［実機確認］" if b<101 else "未使用（1以上で入力不可）")
 m[38]=(full("球速"),"","");m[39]=(full("コントロール"),"","");m[40]=(full("スタミナ"),"","");m[41]=(full("投球フォーム"),"","")
 fams=["スライダー","カーブ","フォーク","シンカー","シュート","ストレート"]
 for i,fn in enumerate(fams):
  for base,pre in ((42,""),(48,"第二")):
   m[base+i]=([f"{pre}{fn} Lv{4>>j}" for j in range(3)]+[f"{pre}{fn} 特殊変化球 {16>>j}" for j in range(5)],"32" if (base==42 and fn=="ストレート") else "","Lv(3bit)<<5 | code(5bit)、code15=オリジナル")
 for i in range(9):m[54+i]=(full(f"オリ変名{i+1}文字目"),"255" if i==0 else "","オリ変名（終端FF）")
 m[63]=(full("スピード"),"","符号付き8bit");m[64]=(full("オリ変基本球種"),"","");m[65]=(full("横変化"),"","符号付き8bit");m[66]=(full("縦変化"),"","符号付き8bit")
 m[67]=(nib("ノビ","キレ"),"","")
 for b,names in ABILITY_ROWS.items():
  note=""
  if b==81:note="bit1–7: パス入出力では保持、サクセス→登録では消える（実機確認）"
  elif b==92:note="bit4–7＝パッチ用フラグ1–4（使用はROMパッチ）／サクセス→登録・パス入出力とも保持／投手能力なので野手は登録時に0（フラグも消える）"
  elif 86<=b<=93:note="投手能力（野手は登録時に0）"
  m[b]=([n or "未使用" for n in names],"",note)
 m[95]=(["ポケ8･あつパワ","ポケ甲子園","4バイト出身","パス選手","甲子園シリーズ","ポケシリーズ","選手判定","パス再入力"],"20","選手判定が誤りだと入力拒否")
 m[96]=(["選手判定","選手判定","ポケ11・12","ポケ10・12","選手判定","選手判定","ポケ9","通信コピー選手"],"48","")
 for b in (97,98,99,100):m[b]=(["可変"]*8,"43" if b==100 else "","出身/チーム・肌/顔上位/顔下位の可変配置（別タブ参照）")
 m[106]=(["未使用"]*6+["顔表示2","顔表示1"],"2","1=着帽写真 2=ミニ顔 3=撮影写真")
 return m

def poke12_appearance_layout_text():
 out=["byte97–100 可変配置（チーム・肌byte／顔上位byte／顔下位byteがそれぞれ0か1以上かで位置が変わる）",""]
 lab={0:"チーム・肌",1:"顔上位",2:"顔下位"}
 for ts in (0,1):
  for hi in (0,1):
   for lo in (0,1):
    slots=[i for i,v in enumerate((ts,hi,lo)) if v]+[3]
    names=["出身"]+[lab[i] for i,v in enumerate((ts,hi,lo)) if v];pos=["未使用"]*4
    for s,n in zip(slots,names):pos[s]=n
    out.append(f"チーム・肌{'≥1' if ts else '=0'}  顔上位{'≥1' if hi else '=0'}  顔下位{'≥1' if lo else '=0'}  →  "+"  ".join(f"{97+i}:{p}" for i,p in enumerate(pos)))
 out+=["","チーム・肌byte = 上位4bit 肌 / 下位4bit チーム","ツールは pack_appearance() でこの規則どおり自動配置します。"]
 return "\n".join(out)

def poke12_code_lists_text():
 out=["■ 守備位置（メイン・サブ共通）"]+[f"  {i}: {p}" for i,p in enumerate(POS[:8])]
 out+=["","■ チーム（4bit）"]+[f"  {t}" for t in TEAMS]
 out+=["","■ 肌（4bit）"]+[f"  {s}" for s in SKINS[:6]]
 out+=["","■ 特殊変化球 code（各系統、byte42–53の下位5bit）"]
 for fam,lst in P.items():out.append(f"  {fam}: "+" / ".join(f"{c}={n}" for n,c in lst if c is not None))
 out+=["","■ オリ変基本球種（byte64）","  0=なし 1=スライダー 2=カーブ 3=フォーク 4=シンカー 5=シュート 6=ストレート（6は非正規だが設定可）"]
 out+=["","■ 出身"]+[f"  {i}: {o}" for i,o in enumerate(ORIGINS)]
 out+=["","■ 顔表示設定（byte106）","  0=- 1=着帽写真 2=ミニ顔 3=撮影写真（撮影写真の顔下位byteは正規出力では00固定）"]
 out+=["","■ 打撃フォーム"]+[f"  {i}: {n}" for i,n in enumerate(BATFORMS)]
 out+=["","■ 投球フォーム"]+[f"  {i}: {n}" for i,n in enumerate(PITCHFORMS)]
 out+=["","※ ミニ顔・着帽写真コードは『選手プロフィール』タブの『顔/着帽写真コード表』を参照。","出典: パワポケで調べたデータ置き場『ポケ12の仕様』(w.atwiki.jp/pawapoke_dataokiba/pages/67.html)"]
 return "\n".join(out)


class App(tk.Tk):
 def __init__(self):
  super().__init__();self.title("PowerPoke 12 Password Maker / Analyzer v1.60c UNIFIED RESEARCH");sw=self.winfo_screenwidth();sh=self.winfo_screenheight()
  self.geometry(f"{min(1400,max(1050,sw-80))}x{min(900,max(700,sh-100))}")
  self.minsize(780,580)
  self.r=minimal();self.pw=[];self.av={};self.vars={};self.widgets={};self.pitch_exact={};self._speed_raw_preserve=None
  nb=ttk.Notebook(self);nb.pack(fill="both",expand=True,padx=6,pady=6);self.nb=nb
  self._tab_canvases={}
  tabs=[]
  for attr,label in [("tbasic","基礎能力"),("ta","特殊能力"),("tapp","選手プロフィール"),("tr","RAW 106"),("tc","パス生成/解析"),("tfree","任意タブ編集")]:
   outer=ttk.Frame(nb);nb.add(outer,text=label)
   inner,cv=self._make_scroll_tab(outer)
   setattr(self,attr,inner);self._tab_canvases[str(outer)]=cv;tabs.append(outer)
  self._free_outer=str(tabs[-1])
  self.tori=ttk.LabelFrame(self.tbasic,text="オリ変（投手のみ）")
  self.tp=self.tbasic
  self.bind_all("<MouseWheel>",self._global_mousewheel,add="+")
  self.bind_all("<Button-4>",self._global_mousewheel,add="+")
  self.bind_all("<Button-5>",self._global_mousewheel,add="+")
  self.basicui();self.pitchui();self.oriui();self.abilityui();self.appui();self.rawui();self.codecui();self.freeui();self.sync();self.vars["ptype"].set("投手");self.oriname.set("オリジナル");self.init_player_type();self.nb.bind("<<NotebookTabChanged>>",self.autotab)
  self.title(self.title()+" — codec self-test "+("OK" if selftest() else "FAILED"))
 def _make_scroll_tab(self,outer):
  cv=tk.Canvas(outer,highlightthickness=0,borderwidth=0)
  sy=ttk.Scrollbar(outer,orient="vertical",command=cv.yview)
  inner=ttk.Frame(cv);win=cv.create_window((0,0),window=inner,anchor="nw")
  inner.bind("<Configure>",lambda e,c=cv:c.configure(scrollregion=c.bbox("all")))
  cv.bind("<Configure>",lambda e,c=cv,w=win:c.itemconfigure(w,width=e.width))
  cv.configure(yscrollcommand=sy.set);cv.pack(side="left",fill="both",expand=True);sy.pack(side="right",fill="y")
  return inner,cv
 def _global_mousewheel(self,e):
  try:
   # Interactive widgets get first claim on the wheel.  In v1.37 the bind_all
   # handler also scrolled the whole tab while a Combobox/Spinbox/etc. was under
   # the pointer, which made dropdown operation feel broken.
   w=getattr(e,"widget",None)
   cls=(w.winfo_class() if w is not None else "")
   if cls in {"TCombobox","Combobox","TSpinbox","Spinbox","Listbox","Treeview","Text","Entry","TEntry","Canvas"}:
    return
   sel=self.nb.select();cv=self._tab_canvases.get(sel)
   if not cv:return
   if getattr(e,"num",None)==4:step=-3
   elif getattr(e,"num",None)==5:step=3
   else:
    d=getattr(e,"delta",0);step=-int(d/120) if abs(d)>=120 else (-1 if d>0 else 1 if d<0 else 0)
   if step:
    cv.yview_scroll(step,"units")
    return "break"
  except Exception:pass
 def spin(self,parent,row,col,key,label,lo,hi):
  ttk.Label(parent,text=label).grid(row=row,column=col*2,sticky="w",padx=5,pady=3)
  v=tk.IntVar();self.vars[key]=v
  box=ttk.Frame(parent);box.grid(row=row,column=col*2+1,sticky="w")
  w=ttk.Spinbox(box,textvariable=v,from_=lo,to=hi,width=8);w.pack(side="left")
  self.widgets[key]=w
  if not hasattr(self,"spin_boxes"):self.spin_boxes={}
  self.spin_boxes[key]=box
  # Range hints can be packed inside this value cell without overlapping the next field.
 def combo(self,parent,row,col,key,label,values):
  ttk.Label(parent,text=label).grid(row=row,column=col*2,sticky="w",padx=5,pady=3)
  v=tk.StringVar();self.vars[key]=v
  w=ttk.Combobox(parent,textvariable=v,values=values,state="readonly",width=20);w.grid(row=row,column=col*2+1,sticky="w")
  self.widgets[key]=w
  return w
 def basicui(self):
  f=self.tbasic
  pt=self.combo(f,0,4,"ptype","タイプ",["投手","野手"])
  pt.bind("<<ComboboxSelected>>",self.on_player_type_changed)
  ttk.Label(f,text="※ここを変えると入力した基礎能力・投手能力・球種はリセットされます",foreground="#8a3b00",wraplength=300,justify="left").grid(row=1,column=8,columnspan=2,padx=5,sticky="nw")
  self.spin(f,0,0,"power","パワー",0,255);self.spin(f,0,1,"meet","ミート",0,15);self.spin(f,0,2,"arm","肩力",0,15)
  self.spin(f,1,0,"run","走力",0,15);self.spin(f,1,1,"field","守備力",0,15);self.spin(f,1,2,"error","耐エラー",0,15);self.spin(f,1,3,"traj","弾道",0,15)
  self.spin(f,2,0,"speed","球速",0,165);self.spin(f,2,1,"control","コントロール",0,255);self.spin(f,2,2,"stamina","スタミナ",0,255);self.spin(f,2,3,"number","背番号",0,255)
  # Small right-side range hints. 0 is a valid stored value; regular in-game values can be narrower.
  hints={"power":"0–255","meet":"0–15","arm":"0–15","run":"0–15","field":"0–15","error":"0–15","traj":"0–15 (正規1–4)","speed":"0–165 ※166以上→165","control":"0–255","stamina":"0–255","number":"0–255 ※3桁目は表示されない"}
  for k,txt in hints.items():
   info=ttk.Label(self.spin_boxes[k],text=txt,foreground="#777777",font=("",8))
   info.pack(side="left",padx=(6,2))
  def clamp_speed(_e=None):
   try:
    x=int(self.vars["speed"].get())
    if x>165:self.vars["speed"].set(165)
    elif x<0:self.vars["speed"].set(0)
   except Exception:pass
  self.widgets["speed"].bind("<FocusOut>",clamp_speed,add="+")
  self.widgets["speed"].bind("<Return>",clamp_speed,add="+")
  self.combo(f,3,0,"main","メイン守備",POS);self.combo(f,3,1,"sub1","サブ1",POS);self.combo(f,3,2,"sub2","サブ2",POS)
  self.combo(f,4,0,"bat","打撃フォーム",BATFORMS);self.combo(f,4,1,"pitchform","投球フォーム",PITCHFORMS)
  for k in ("leftthrow","leftbat","switch"): self.vars[k]=tk.BooleanVar(value=False)
  self.combo(f,5,0,"handed","投打",["右投右打","右投左打","右投両打","左投右打","左投左打","左投両打"])
 def on_player_type_changed(self,event=None):
  self.init_player_type()

 def _apply_type_main_rules(self):
  typ=self.vars["ptype"].get()
  w=self.widgets.get("main")
  if not w:return
  pitcher=(typ=="投手")
  if pitcher:
   self.vars["main"].set("投")
   w.configure(values=["投"],state="disabled")
  else:
   vals=[x for x in POS if x!="投"]
   w.configure(values=vals,state="readonly")
   if self.vars["main"].get()=="投":self.vars["main"].set("一")
  for k in ("speed","control","stamina"):
   if k in self.widgets:self.widgets[k].configure(state="normal" if pitcher else "disabled")
  if "pitchform" in self.widgets:self.widgets["pitchform"].configure(state="readonly" if pitcher else "disabled")
  for pw in getattr(self,"pitchwidgets",[]):pw.configure(state="readonly" if pitcher and isinstance(pw,ttk.Combobox) else ("normal" if pitcher else "disabled"))
  self._update_pitch_level_states()
  if hasattr(self,"ori_enable_widget"):
   if not pitcher:self.ori_enabled.set("無")
   self.ori_enable_widget.configure(state="readonly" if pitcher else "disabled")
   self._update_ori_state()

 def init_player_type(self):
  typ=self.vars["ptype"].get() or "投手"
  # Common untouched/new-player batting defaults used by the current template.
  for k,v in {"power":50,"meet":6,"arm":6,"run":6,"field":6,"error":6,"traj":1,
              "control":50,"stamina":50,"number":1}.items(): self.vars[k].set(v)
  if typ=="投手":
   self.vars["speed"].set(80);self.vars["main"].set("投")
   for f,a,la,b,lb,lab in self.pw:
    a.set("球種なし");la.set(0);b.set("球種なし");lb.set(0)
    if f=="ストレート系":a.set("ストレート");la.set(1)
  else:
   self.vars["speed"].set(0);self.vars["control"].set(0);self.vars["stamina"].set(0)
   self.vars["main"].set("一")
   for f,a,la,b,lb,lab in self.pw:
    a.set("球種なし");la.set(0);b.set("球種なし");lb.set(0)
  if hasattr(self,"ori_enabled"):self.ori_enabled.set("無")
  self._apply_type_main_rules()
  self.commit_all(showerror=False)
 def pitchui(self):
  pf=ttk.LabelFrame(self.tbasic,text="変化球（12球種）")
  pf.grid(row=7,column=0,columnspan=10,sticky="nw",padx=5,pady=(16,6))
  self.pitchframe=pf;self.pitchwidgets=[];self.pitch_level_pairs=[]
  for j,x in enumerate(["方向","第1","Lv","第2","Lv","範囲"]):ttk.Label(pf,text=x,font=("",10,"bold")).grid(row=0,column=j,padx=5,pady=6)
  for i,f in enumerate(F):
   names=pitch_choices(f);a=tk.StringVar();la=tk.IntVar();b=tk.StringVar();lb=tk.IntVar();lab=ttk.Label(pf,text="Lv 0–7 / code 0–F",foreground="#777777",font=("",8))
   ttk.Label(pf,text=f).grid(row=i+1,column=0,sticky="w",padx=4);ca=ttk.Combobox(pf,textvariable=a,values=names,state="readonly",width=22);ca.grid(row=i+1,column=1,padx=2);sla=ttk.Spinbox(pf,textvariable=la,from_=0,to=7,width=4);sla.grid(row=i+1,column=2,padx=2)
   cb=ttk.Combobox(pf,textvariable=b,values=names,state="readonly",width=22);cb.grid(row=i+1,column=3,padx=2);slb=ttk.Spinbox(pf,textvariable=lb,from_=0,to=7,width=4);slb.grid(row=i+1,column=4,padx=2);lab.grid(row=i+1,column=5,padx=4);self.pw.append((f,a,la,b,lb,lab));self.pitchwidgets.extend((ca,sla,cb,slb))
   self.pitch_level_pairs.extend(((a,la,sla),(b,lb,slb)))
   ca.bind("<<ComboboxSelected>>",lambda e,v=a,l=la:self._on_pitch_selected(v,l))
   cb.bind("<<ComboboxSelected>>",lambda e,v=b,l=lb:self._on_pitch_selected(v,l))
   la.trace_add("write",lambda *_args,v=a,l=la:self._on_pitch_level_changed(v,l))
   lb.trace_add("write",lambda *_args,v=b,l=lb:self._on_pitch_level_changed(v,l))
 def _on_pitch_selected(self,pitch_var,level_var):
  if pitch_var.get()=="球種なし":
   level_var.set(0)
  elif int(level_var.get() or 0)==0:
   level_var.set(1)
  self._update_pitch_level_states()
 def _on_pitch_level_changed(self,pitch_var,level_var):
  if getattr(self,"_pitch_sync_busy",False):return
  try:lv=int(level_var.get())
  except (tk.TclError,ValueError):return
  if lv==0 and pitch_var.get()!="球種なし":
   self._pitch_sync_busy=True
   try:pitch_var.set("球種なし")
   finally:self._pitch_sync_busy=False
   self._update_pitch_level_states()
 def _update_pitch_level_states(self):
  pitcher=self.vars.get("ptype") is not None and self.vars["ptype"].get()=="投手"
  for pitch_var,level_var,widget in getattr(self,"pitch_level_pairs",[]):
   if not pitcher or pitch_var.get()=="球種なし":
    if pitch_var.get()=="球種なし":level_var.set(0)
    widget.configure(state="disabled")
   else:widget.configure(state="normal")
 def oriui(self):
  f=self.tori;f.grid(row=8,column=0,columnspan=10,sticky="ew",padx=5,pady=(8,6));self.oriv={};self.oriwidgets=[]
  ttk.Label(f,text="オリ変").grid(row=0,column=0,sticky="w",padx=5,pady=4)
  self.ori_enabled=tk.StringVar(value="無")
  self.ori_enable_widget=ttk.Combobox(f,textvariable=self.ori_enabled,values=["無","有"],state="readonly",width=5)
  self.ori_enable_widget.grid(row=0,column=1,sticky="w");self.ori_enable_widget.bind("<<ComboboxSelected>>",self._on_ori_enabled_changed)
  ttk.Label(f,text="名前（直接入力・最大9文字）").grid(row=0,column=2,sticky="w",padx=5,pady=4)
  self.oriname=tk.StringVar(value="");self.oristatus=tk.StringVar(value="オリ変「有」のとき入力可")
  oe=ttk.Entry(f,textvariable=self.oriname,width=35);oe.grid(row=0,column=3,sticky="w");self.oriwidgets.append(oe)
  ob1=ttk.Button(f,text="文字判定",command=self.checkoriname);ob1.grid(row=0,column=4,padx=5);self.oriwidgets.append(ob1)
  ob2=ttk.Button(f,text="オリ変文字表",command=self.showoritable);ob2.grid(row=0,column=5,padx=5);self.oriwidgets.append(ob2)
  ttk.Label(f,text="※名称を変更したら必ず文字判定を行うこと",foreground="#8a3b00",font=("",8)).grid(row=1,column=2,sticky="w",padx=5)
  ttk.Label(f,textvariable=self.oristatus).grid(row=1,column=3,columnspan=3,sticky="w")
  dirs=["なし","スライダー系","カーブ系","フォーク系","シンカー系","シュート系","ストレート系"]
  ttk.Label(f,text="基本方向").grid(row=2,column=0,sticky="w",padx=5,pady=4);v=tk.StringVar(value="なし");self.oriv["base"]=v
  cb=ttk.Combobox(f,textvariable=v,values=dirs,state="readonly",width=32);cb.grid(row=2,column=1,sticky="w");self.ori_direction_widget=cb;self.oriwidgets.append(cb)
  # Poke8-12 stores speed/H/V as signed 8-bit two's complement. UI exposes the full signed-byte range.
  rows=[("speed","スピード",-128,127,"正規値: -10 ～ +10　/　入力可能値: -128 ～ +127"),
        ("h","横変化",-128,127,"正規値: -30 ～ +30　/　入力可能値: -128 ～ +127"),
        ("v","縦変化",-128,127,"正規値: -30 ～ +30　/　入力可能値: -128 ～ +127")]
  for i,(k,l,lo,hi,note) in enumerate(rows,start=3):
   ttk.Label(f,text=l).grid(row=i,column=0,sticky="w",padx=5,pady=4);vv=tk.IntVar(value=0);self.oriv[k]=vv
   sp=ttk.Spinbox(f,textvariable=vv,from_=lo,to=hi,width=12);sp.grid(row=i,column=1,sticky="w");self.oriwidgets.append(sp)
   ttk.Label(f,text=note,foreground="#666666").grid(row=i,column=2,columnspan=2,sticky="w",padx=8)
  # byte67 is unsigned nibbles: high=nobi, low=kire. In Poke8-12 regular values are 0..+7 (up to +9 works); negative values do not exist.
  for i,(k,l) in enumerate((("nobi","ノビ"),("kire","キレ")),start=6):
   ttk.Label(f,text=l).grid(row=i,column=0,sticky="w",padx=5,pady=4);vv=tk.IntVar(value=0);self.oriv[k]=vv
   sp=ttk.Spinbox(f,textvariable=vv,from_=0,to=15,width=12);sp.grid(row=i,column=1,sticky="w");self.oriwidgets.append(sp)
   ttk.Label(f,text="正規値: +0 ～ +7（ポケ8～12は+9まで動作報告）　/　入力可能値: 0 ～ 15（4-bit）",foreground="#666666").grid(row=i,column=2,columnspan=2,sticky="w",padx=8)
  ttk.Label(f,text="※スピード/横/縦は10進数の符号付き8-bit入力（RAWではtwo's complement）。ノビ/キレは各4-bitの非負値です。",foreground="#555555").grid(row=8,column=0,columnspan=4,sticky="w",padx=5,pady=(8,2))
  ttk.Label(f,text="RAWへの反映ボタンは不要。タブ移動時/GENERATE時に全タブを自動反映します。").grid(row=9,column=0,columnspan=4,sticky="w",padx=5,pady=4)
  ttk.Label(f,text="オリ変名コード正規範囲: 00, 51–CC / FF終端。半角 a-z/A-Z/0-9 は全角英大文字/数字へ自動変換します。").grid(row=10,column=0,columnspan=4,sticky="w",padx=5,pady=4)
  self._update_ori_state()
 def _reset_ori_fields(self):
  self.oriname.set("")
  for k,v in {"speed":0,"base":"なし","h":0,"v":0,"nobi":0,"kire":0}.items():self.oriv[k].set(v)
 def _on_ori_enabled_changed(self,event=None):
  if self.vars["ptype"].get()=="投手" and self.ori_enabled.get()=="有" and not self.oriname.get().strip():
   self.oriname.set("オリジナル")
  self._update_ori_state()
  if self.ori_enabled.get()=="有":self.checkoriname()
 def _update_ori_state(self):
  pitcher=self.vars.get("ptype") is not None and self.vars["ptype"].get()=="投手"
  enabled=pitcher and self.ori_enabled.get()=="有"
  if not enabled:self._reset_ori_fields()
  for ow in self.oriwidgets:
   if enabled:ow.configure(state="readonly" if ow is self.ori_direction_widget else "normal")
   else:ow.configure(state="disabled")
 def showoritable(self):
  w=tk.Toplevel(self);w.title("オリ変文字コード表（正規 00 / 51–CC）");w.geometry("660x620")
  top=ttk.Frame(w);top.pack(fill="x",padx=6,pady=6)
  ttk.Label(top,text="検索").pack(side="left");q=tk.StringVar();ttk.Entry(top,textvariable=q,width=25).pack(side="left",padx=6)
  ttk.Button(top,text="検索解除",command=lambda:q.set("")).pack(side="left",padx=3)
  ttk.Label(w,text="半角英字は入力時に全角大文字へ、半角数字は全角数字へ自動変換。").pack(anchor="w",padx=6)
  tr=ttk.Treeview(w,columns=("code","char","kind"),show="headings")
  for k,t,wd in [("code","HEX",80),("char","文字",100),("kind","区分",390)]:tr.heading(k,text=t);tr.column(k,width=wd,anchor="center" if k!="kind" else "w")
  sy=ttk.Scrollbar(w,orient="vertical",command=tr.yview);tr.configure(yscrollcommand=sy.set);tr.pack(side="left",fill="both",expand=True,padx=(6,0),pady=6);sy.pack(side="right",fill="y",pady=6)
  def kind(code):
   if code==0:return "空白"
   if 0x51<=code<=0xA1:return "カタカナ"
   if 0xA2<=code<=0xAB:return "全角数字"
   if 0xAC<=code<=0xC5:return "全角英大文字"
   return "記号・特殊文字"
  def fill(*_):
   z=q.get().lower();tr.delete(*tr.get_children())
   for code,ch in sorted(ORI_NAME_CODE_TO_CHAR.items()):
    txt=f"{code:02X} {ch} {kind(code)}".lower()
    if not z or z in txt:tr.insert("","end",values=(f"{code:02X}",ch,kind(code)))
  def selected():
   sel=tr.selection()
   if not sel:raise ValueError("文字表から行を選択してください")
   v=tr.item(sel[0],"values");return int(str(v[0]),16),str(v[1])
  def cpchar():
   try:_,ch=selected();self.clipboard_clear();self.clipboard_append(ch);self.update()
   except Exception as e:messagebox.showerror("オリ変文字表",str(e))
  def cpcode():
   try:c,_=selected();self.clipboard_clear();self.clipboard_append(f"{c:02X}");self.update()
   except Exception as e:messagebox.showerror("オリ変文字表",str(e))
  def ins(event=None):
   try:
    _,ch=selected();cur=self.oriname.get();candidate=cur+ch
    encode_ori_name(candidate);self.oriname.set(candidate);self.checkoriname()
   except Exception as e:messagebox.showerror("オリ変文字表",str(e))
  ab=ttk.Frame(w);ab.pack(fill="x",padx=6,pady=(0,4))
  ttk.Button(ab,text="文字をコピー",command=cpchar).pack(side="left",padx=2)
  ttk.Button(ab,text="コードをコピー",command=cpcode).pack(side="left",padx=2)
  ttk.Button(ab,text="オリ変名へ挿入",command=ins).pack(side="left",padx=2)
  tr.bind("<Double-1>",ins)
  q.trace_add("write",fill);fill()

 def checkoriname(self):
  try:
   src=self.oriname.get();norm=normalize_ori_text(src);bb=encode_ori_name(src)
   if src!=norm:self.oriname.set(norm)
   self.oristatus.set("OK  表示: "+norm+"   bytes: "+" ".join(f"{x:02X}" for x in bb))
  except Exception as e:self.oristatus.set("不正: "+str(e))

 def abilityui(self):
  inn=self.ta
  ttk.Label(inn,text="投手ムラッ気(効果無): ポケ10以降は未使用。ムラッ気は野手ムラッ気側を共用。",foreground="#8a3b00").grid(row=0,column=0,columnspan=6,sticky="w",padx=4)
  ttk.Label(inn,text="◎と〇が両方存在する場合は選手登録の時点で◎に統合される。",foreground="#8a3b00").grid(row=1,column=0,columnspan=6,sticky="w",padx=4)
  ttk.Label(inn,text="ローボールヒッターとハイボールヒッターが両方存在する場合は前者が優先。",foreground="#8a3b00").grid(row=2,column=0,columnspan=6,sticky="w",padx=4)
  ttk.Label(inn,text="GBカラー: ポケ12ではフラグが立っていてもパス入力時に削除される。",foreground="#8a3b00").grid(row=3,column=0,columnspan=6,sticky="w",padx=4)
  PG="#dadada";st=ttk.Style(self)
  st.configure("Pit.TCheckbutton",background=PG);st.configure("Pit.TLabel",background=PG)
  row=4;pit_start=None
  for b in sorted(ABILITY_ROWS):
   pit=b>=86  # byte86以降＝投手能力ブロック（灰色背景）
   if pit and pit_start is None:pit_start=row;pitbg=tk.Frame(inn,bg=PG)
   ttk.Label(inn,text=f"byte {b}",font=("",9,"bold"),style="Pit.TLabel" if pit else "TLabel").grid(row=row,column=0,sticky="w",padx=4);col=1
   for j,n in enumerate(ABILITY_ROWS[b]):
    if not n:continue
    v=tk.BooleanVar();self.av[(b,j)]=v;ttk.Checkbutton(inn,text=n,variable=v,style="Pit.TCheckbutton" if pit else "TCheckbutton").grid(row=row,column=col,sticky="w",padx=4);col+=1
    if col>5:row+=1;col=1
   row+=1
  if pit_start is not None:
   # 第3球種セットは投手専用なので、投手能力の灰色ブロック最下段に配置。
   setrow=tk.Frame(inn,bg=PG);setrow.grid(row=row,column=0,columnspan=6,sticky="w",padx=4,pady=(5,6))
   tk.Label(setrow,text="第3球種セット（byte92 bit4–7を使用）:",bg=PG,fg="#8a3b00").pack(side="left")
   self.third_pitch_set=tk.StringVar(value="0 (0)")
   self.third_pitch_set_widget=ttk.Combobox(setrow,textvariable=self.third_pitch_set,values=THIRD_PITCH_SET_CHOICES,state="readonly",width=8)
   self.third_pitch_set_widget.pack(side="left",padx=(8,6))
   tk.Label(setrow,text="0 (0)=なし / ROMパッチ側のセット 1 (1)～15 (F) に対応、10進数(16進数)表記。未パッチのゲームでは効果なし。",bg=PG,fg="#8a3b00").pack(side="left")
   row+=1
   pitbg.grid(row=pit_start,column=0,rowspan=row-pit_start,columnspan=7,sticky="nsew");pitbg.lower()
   side=tk.Frame(inn,bg=PG);side.grid(row=pit_start,column=6,rowspan=row-pit_start,sticky="ns",padx=(10,4))
   brace=tk.Canvas(side,width=18,bg=PG,highlightthickness=0);brace.pack(side="left",fill="y")
   def _draw_brace(e,c=brace):
    c.delete("all");h=e.height;m=h/2
    c.create_line(2,4,8,4,8,m-6,15,m,8,m+6,8,h-4,2,h-4,width=2,fill="#555")
   brace.bind("<Configure>",_draw_brace)
   tk.Label(side,text="※投手限定\n（野手で登録すると\n　byte86–93は0になる）",bg=PG,fg="#8a3b00",justify="left").pack(side="left",padx=4)
 def appui(self):
  f=self.tapp
  ttk.Label(f,text="選手名",font=("",10,"bold")).grid(row=0,column=0,sticky="w",padx=5,pady=4)
  self.nametext=tk.StringVar(); self.namebytes=tk.StringVar(); self.namehalf=tk.BooleanVar(value=False); self.name_exact_raw=None; self._name_internal=False
  self.nametext.trace_add("write",self._name_text_changed); self.namehalf.trace_add("write",self._name_half_changed)
  ttk.Entry(f,textvariable=self.nametext,width=28).grid(row=0,column=1,sticky="w",padx=5)
  ttk.Button(f,text="文字コード検索…",command=self.showcharwindow).grid(row=0,column=2,sticky="w",padx=5)
  ttk.Checkbutton(f,text="入力全体を半角F7コード化（漢字との混在は実際の半角カナを直接入力）",variable=self.namehalf).grid(row=1,column=1,columnspan=3,sticky="w",padx=5)
  ttk.Label(f,textvariable=self.namebytes,font=("Consolas",10)).grid(row=2,column=0,columnspan=5,sticky="w",padx=5)
  self.combo(f,3,0,"origin","出身",ORIGINS);self.combo(f,4,0,"team","チーム",TEAMS)
  ttk.Label(f,text="※パス/QRの球団値は4bit=0～F。C=極亜久高校、D=モグラーズ、E=オクトパス、F=日の出高校。10h以上の内部球団IDは格納できません。",foreground="#444").grid(row=5,column=0,columnspan=5,sticky="w",padx=5)
  self.combo(f,6,0,"skin","肌",SKINS)
  self.spin(f,7,0,"face","顔コード（10進数）",0,65535)
  ttk.Label(f,text="10進数 0–65535",foreground="#777777",font=("",8)).place(in_=self.widgets["face"],relx=1.0,x=5,rely=0.5,anchor="w")
  ttk.Button(f,text="顔/着帽写真コード表",command=self.showfacetable).grid(row=7,column=2,sticky="w",padx=6)
  self.combo(f,8,0,"facemode","顔表示",["なし","着帽写真","ミニ顔","撮影写真"])
  ttk.Label(f,text="※撮影写真の正規パス出力では顔下位byte（写真ID）は00固定。外部パス/QRでは元DSiの撮影画像そのものは移送されません。",foreground="#444").grid(row=9,column=0,columnspan=5,sticky="w",padx=5)
  self.vars["passplayer"]=tk.BooleanVar(value=True)
  ttk.Checkbutton(f,text="パス選手フラグ（byte95 / 0x10）",variable=self.vars["passplayer"]).grid(row=10,column=0,columnspan=2,sticky="w",padx=5,pady=(8,2))
  ttk.Label(f,text="※通常はON。OFFは『パスワード選手ではない』扱い。byte95/96の選手判定はWiki標準値を検査します。",foreground="#8a3b00").grid(row=11,column=0,columnspan=5,sticky="w",padx=5)
  ttk.Label(f,text="※ポケ12固有の97–100 byte可変配置は自動packします。出身46 = 12･オレペナ。",foreground="#444").grid(row=12,column=0,columnspan=5,sticky="w",padx=5,pady=10)
 def showfacetable(self):
  w=tk.Toplevel(self);w.title("ポケ12 顔コード表");w.geometry("700x650")
  top=ttk.Frame(w);top.pack(fill="x",padx=6,pady=6)
  ttk.Label(top,text="ミニ顔 / 着帽写真（Wikiコード、検索可）").pack(side="left")
  q=tk.StringVar();ttk.Entry(top,textvariable=q,width=24).pack(side="left",padx=6)
  tree=ttk.Treeview(w,columns=("decimal","hex","name","kind"),show="headings");tree.heading("decimal",text="10進数");tree.heading("hex",text="16進数");tree.heading("name",text="名称");tree.heading("kind",text="種別");tree.column("decimal",width=80,anchor="center");tree.column("hex",width=80,anchor="center");tree.column("name",width=330);tree.column("kind",width=100)
  sy=ttk.Scrollbar(w,orient="vertical",command=tree.yview);tree.configure(yscrollcommand=sy.set);tree.pack(side="left",fill="both",expand=True);sy.pack(side="right",fill="y")
  def fill(*_):
   z=q.get().lower();tree.delete(*tree.get_children())
   for i,n in enumerate(MINI_FACE_NAMES):
    dec=str(i);hx=f"{i:04X}"
    if not z or z in n.lower() or z in dec or z in hx.lower():tree.insert("","end",values=(dec,hx,n,"ミニ顔"))
   for codev,n in sorted(HAT_PHOTOS.items()):
    dec=str(codev);hx=f"{codev:04X}"
    if not z or z in n.lower() or z in dec or z in hx.lower():tree.insert("","end",values=(dec,hx,n,"着帽写真"))
  q.trace_add("write",fill);fill()
  def choose(_=None):
   sel=tree.selection()
   if sel:
    vals=tree.item(sel[0],"values");self.vars["face"].set(int(vals[0],10));self.vars["facemode"].set(str(vals[3]));w.destroy()
  tree.bind("<Double-1>",choose)
 def rawui(self):
  b=ttk.Frame(self.tr);b.pack(fill="x");ttk.Button(b,text="Apply edited RAW",command=self.applyraw).pack(side="left",padx=4);ttk.Button(b,text="Minimal template",command=self.reset).pack(side="left")
  self.rt=tk.Text(self.tr,font=("Consolas",10),wrap="none");self.rt.pack(fill="both",expand=True)
 def _name_half_changed(self,*_):
  if not self._name_internal:self.name_exact_raw=None
  self.previewname()
 def _name_text_changed(self,*_):
  if not getattr(self,"_name_internal",False): self.name_exact_raw=None
  self.previewname()
 def _set_exact_name_raw(self,bb):
  bb=bytes(bb)
  if len(bb)>12: raise ValueError("名前コードが12 bytesを超えます")
  bb=bb+b"\x00"*(12-len(bb)); self.name_exact_raw=bb
  self._name_internal=True
  try:
   self.nametext.set(decode_name_entry_bytes(bb))
   codes=[];i=0
   while i<12 and bb[i]:
    if 0xE8<=bb[i]<=0xF7 and i+1<12: codes.append((bb[i]<<8)|bb[i+1]);i+=2
    else: codes.append(bb[i]);i+=1
   self.namehalf.set(bool(codes) and all(0xF700<=c<=0xF7FF for c in codes))
  finally:self._name_internal=False
  self.previewname()
 def _current_name_raw(self):
  if self.name_exact_raw is not None:return bytearray(self.name_exact_raw)
  return encode_name_text(self.nametext.get(),12,self.namehalf.get())
 def _selected_name_code(self):
  sel=self.chartree.selection()
  if not sel: raise ValueError("文字表から行を選択してください")
  vals=self.chartree.item(sel[0],"values"); hx=str(vals[1])
  return int(hx,16),str(vals[0])
 def copy_name_char(self):
  try:_,ch=self._selected_name_code();self.clipboard_clear();self.clipboard_append(ch);self.update()
  except Exception as e:messagebox.showerror("文字パレット",str(e))
 def copy_name_code(self):
  try:code,_=self._selected_name_code();txt=f"{code:02X}" if code<=255 else f"{code:04X}";self.clipboard_clear();self.clipboard_append(txt);self.update()
  except Exception as e:messagebox.showerror("文字パレット",str(e))
 def insert_name_code(self,event=None):
  try:
   code,_=self._selected_name_code();cur=bytearray(self._current_name_raw());used=0
   while used<12 and cur[used]:
    used += 2 if 0xE8<=cur[used]<=0xF7 and used+1<12 else 1
   add=_name_code_bytes(code)
   if used+len(add)>12:raise ValueError(f"名前コードが12 bytesを超えます ({used+len(add)}/12)")
   self._set_exact_name_raw(cur[:used]+add)
  except Exception as e:messagebox.showerror("文字パレット",str(e))
 def previewname(self):
  try:
   _nb=self._current_name_raw();_used=len(_nb.rstrip(b"\x00"));_fw,_hw=name_raw_display_units(_nb);_w=name_raw_layout_warning(_nb)
   self.namebytes.set(f"bytes {_used}/12 | 全角{_fw} 半角{_hw}: "+" ".join(f"{x:02X}" for x in _nb)+((" | "+_w) if _w else ""))
  except Exception as e:self.namebytes.set("ERROR: "+str(e))
 def showcharwindow(self):
  w=tk.Toplevel(self);w.title("選手名 文字コード検索");w.geometry("900x650")
  top=ttk.Frame(w);top.pack(fill="x",padx=6,pady=6)
  ttk.Label(top,text="選手名用 文字/コード検索").pack(side="left")
  self.charq=tk.StringVar();ttk.Entry(top,textvariable=self.charq,width=24).pack(side="left",padx=5)
  ttk.Button(top,text="検索",command=self.charsearch).pack(side="left");ttk.Button(top,text="検索解除",command=lambda:(self.charq.set(""),self.charsearch())).pack(side="left",padx=3)
  ttk.Label(top,text="  ※半角F7＝選手名用。F5/F6＝表由来の拡張文字（実機未確認・挿入可）。").pack(side="left")
  self.chartree=ttk.Treeview(w,columns=("char","hex","bytes","kind"),show="headings")
  for c,t,width in [("char","文字",120),("hex","コード(hex)",130),("bytes","bytes",100),("kind","種別",140)]:
   self.chartree.heading(c,text=t);self.chartree.column(c,width=width,anchor="center")
  sy=ttk.Scrollbar(w,orient="vertical",command=self.chartree.yview);self.chartree.configure(yscrollcommand=sy.set)
  self.chartree.pack(side="left",fill="both",expand=True,padx=(6,0),pady=6);sy.pack(side="right",fill="y",pady=6)
  acts=ttk.Frame(top);acts.pack(side="right",padx=4)
  ttk.Button(acts,text="文字をコピー",command=self.copy_name_char).pack(side="left",padx=2)
  ttk.Button(acts,text="コードをコピー",command=self.copy_name_code).pack(side="left",padx=2)
  ttk.Button(acts,text="名前へ挿入",command=self.insert_name_code).pack(side="left",padx=2)
  self.chartree.bind("<Double-1>",self.insert_name_code)
  self.charsearch()
 def charsearch(self):
  q=self.charq.get().strip() if hasattr(self,"charq") else ""
  for x in self.chartree.get_children():self.chartree.delete(x)
  rows=[]
  for code,ch in NAME_CODE_TO_CHAR.items():
   bb=_name_code_bytes(code);hx=bb.hex().upper()
   half=(0xF700<=code<=0xF7FF);display=_NORMAL_TO_HALF_KANA.get(ch,ch) if half else ch
   kind=("半角F7（選手名可）" if half else ("全角2-byte" if code>0xFF else "全角1-byte"))
   if not q or q in ch or q in display or q.upper() in hx: rows.append((0 if half else 1,code,display,hx,len(bb),kind))
  for code,ch in WIFI_NAME_CODE_TO_CHAR.items():
   hx=f"{code:04X}"
   if not q or q in ch or q.upper() in hx: rows.append((2,code,ch,hx,2,"F5/F6拡張（実機未確認）"))
  rows.sort()
  for _,_,ch,hx,n,kind in rows[:8000]:self.chartree.insert("", "end", values=(ch,hx,n,kind))
 def codecui(self):
  body=self.tc;self.codecbody=body
  ttk.Label(body,text="Password").pack(anchor="w");self.pt=tk.Text(body,height=7,font=("",13),wrap="word");self.pt.pack(fill="x")
  b=ttk.Frame(body);b.pack(fill="x",pady=4);ttk.Button(b,text="GENERATE",command=self.gen).pack(side="left");ttk.Button(b,text="DECODE（解析読込）",command=self.dec).pack(side="left",padx=5);ttk.Button(b,text="入力パス能力反映",command=self.validateui).pack(side="left",padx=5);ttk.Button(b,text="QR読み込み",command=self.qrload).pack(side="left",padx=5);ttk.Button(b,text="QR表示",command=self.qrshow).pack(side="left",padx=5)
  ttk.Button(b,text="QR保存",command=self.qrsave).pack(side="left",padx=5);ttk.Button(b,text="COPY",command=self.copy).pack(side="left")
  ttk.Label(body,text="※入力欄へパスを貼り付け、『入力パス能力反映』を押すとvalidate後に左3タブ各種へ能力を反映します。\n※QR読み込み→validate→左3タブ各種に能力を反映します。\n※DECODE＝checksum不一致でもRAWへ展開して編集タブへ読み込む解析用",foreground="#555",wraplength=1200,justify="left").pack(anchor="w",pady=(0,3))
  self.vstatus=tk.StringVar(value="UNVALIDATED");ttk.Label(body,textvariable=self.vstatus,font=("",16,"bold")).pack(anchor="w",pady=4)
  self.lenstatus=tk.StringVar(value="0 / 128  OK");ttk.Label(body,textvariable=self.lenstatus,font=("",14,"bold")).pack(anchor="w",pady=2)
  self.pt.bind("<KeyRelease>",self._password_text_edited)
  qf=ttk.LabelFrame(body,text="QRプレビュー");qf.pack(fill="both",expand=False,pady=6)
  self.qrlabel=ttk.Label(qf,text="有効なパスを生成/入力して「QR表示」")
  self.qrlabel.pack(padx=8,pady=8)
  self._qrphoto=None
  self._qrpng=None
  self.info=tk.Text(body,font=("Consolas",9),height=14);self.info.pack(fill="both",expand=True)
 def sync(self):
  r=self.r
  self._speed_raw_preserve=r[37] if r[37]>165 else None
  vals={"power":r[28],"meet":r[29]>>4,"arm":r[29]&15,"run":r[30]>>4,"field":r[30]&15,"error":r[33]&15,"traj":r[33]>>4,"speed":r[37],"control":r[38],"stamina":r[39],"number":r[32],
        "main":POS[r[26]&15],"sub1":POS[r[27]>>4],"sub2":POS[r[27]&15],"bat":BATFORMS[r[31]] if r[31]<len(BATFORMS) else BATFORMS[0],"pitchform":PITCHFORMS[r[40]] if r[40]<len(PITCHFORMS) else PITCHFORMS[0]}
  for k,v in vals.items():self.vars[k].set(v)
  self.vars["ptype"].set("投手" if (r[26]&15)==1 else "野手")
  self._apply_type_main_rules()
  if self.vars["ptype"].get()=="野手":self.vars["speed"].set(0);self.vars["control"].set(0);self.vars["stamina"].set(0)
  self.vars["leftthrow"].set(bool(r[26]&16));self.vars["leftbat"].set(bool(r[26]&32));self.vars["switch"].set(bool(r[26]&64))
  self.vars["handed"].set(("左投" if self.vars["leftthrow"].get() else "右投")+("両打" if self.vars["switch"].get() else ("左打" if self.vars["leftbat"].get() else "右打")))
  _nd=bytes(r[14:26]);_codes=[];_i=0
  while _i<len(_nd) and _nd[_i]:
   if 0xE8<=_nd[_i]<=0xF7 and _i+1<len(_nd):_codes.append((_nd[_i]<<8)|_nd[_i+1]);_i+=2
   else:_codes.append(_nd[_i]);_i+=1
  self._set_exact_name_raw(bytes(r[14:26]))
  for i,(f,a,la,b,lb,lab) in enumerate(self.pw):
   if self.vars["ptype"].get()=="野手":
    a.set("球種なし");la.set(0);b.set("球種なし");lb.set(0);lab.config(text="Lv 0–7");continue
   for var,lv,bb in ((a,la,r[41+i]),(b,lb,r[47+i])):
    if bb==0: var.set("球種なし");lv.set(0);self.pitch_exact.pop((i,id(var)),None)
    else:
     code=bb&31;known=next((n for n,v in P[f] if v is not None and v==code),None)
     if known is None:
      label=(f"未登録 code {code:X}" if code<=15 else f"範囲外 code {code:02X}");var.set(label)
      w=self.pitchwidgets[i*4+(0 if var is a else 2)];vals=list(w.cget("values"))
      if label not in vals:w.configure(values=vals+[label])
     else:var.set(known)
     lv.set(bb>>5)
   lab.config(text="Lv 0–7")
  _ori_raw=bytes(r[53:67]);_ori_present=(_ori_raw!=b"\x00"*14 and _ori_raw!=b"\xff"+b"\x00"*13)
  self.ori_enabled.set("有" if self.vars["ptype"].get()=="投手" and _ori_present else "無")
  if self.ori_enabled.get()=="有":
   self.oriname.set(decode_ori_name(r[53:62]));self.checkoriname();self.oriv["speed"].set(r[62] if r[62]<128 else r[62]-256);self.oriv["base"].set(["なし","スライダー系","カーブ系","フォーク系","シンカー系","シュート系","ストレート系"][r[63]] if r[63]<=6 else "なし");self.oriv["h"].set(r[64] if r[64]<128 else r[64]-256);self.oriv["v"].set(r[65] if r[65]<128 else r[65]-256);self.oriv["nobi"].set((r[66]>>4)&15);self.oriv["kire"].set(r[66]&15)
  else:self._reset_ori_fields()
  self._apply_type_main_rules()
  for (bn,j),v in self.av.items():v.set(bool(r[bn-1]&(1<<(7-j))))
  self.third_pitch_set.set(f"{(r[91]>>4)&15} ({((r[91]>>4)&15):X})")
  self.vars["passplayer"].set(bool(r[94]&0x10))
  o,t,s,fc=unpack_appearance(r);self.vars["origin"].set(ORIGINS[o] if o<len(ORIGINS) else ORIGINS[0]);self.vars["team"].set(TEAMS[t]);self.vars["skin"].set(SKINS[s]);self.vars["face"].set(fc);self.vars["facemode"].set(["なし","着帽写真","ミニ顔","撮影写真"][r[105]&3])
  self.rt.delete("1.0","end");self.rt.insert("1.0",dump(r))
 def commit_all(self, showerror=True):
  """Assemble every editor tab into RAW106 without requiring per-tab buttons."""
  try:
   r=self.r
   r[28]=self.vars["power"].get();r[29]=(self.vars["meet"].get()<<4)|self.vars["arm"].get();r[30]=(self.vars["run"].get()<<4)|self.vars["field"].get();r[33]=(self.vars["traj"].get()<<4)|self.vars["error"].get()
   if self.vars["ptype"].get()=="野手":
    self.vars["speed"].set(0);self.vars["control"].set(0);self.vars["stamina"].set(0);r[37]=r[38]=r[39]=0
   else:
    _entered=int(self.vars["speed"].get());_spd=(self._speed_raw_preserve if self._speed_raw_preserve is not None and _entered==self._speed_raw_preserve else max(0,min(165,_entered)));r[37]=_spd;r[38]=self.vars["control"].get();r[39]=self.vars["stamina"].get()
   r[32]=self.vars["number"].get()
   r[27]=(POS.index(self.vars["sub1"].get())<<4)|POS.index(self.vars["sub2"].get())
   if self.vars["ptype"].get()=="投手":
    self.vars["main"].set("投")
   elif self.vars["main"].get()=="投":
    raise ValueError("タイプ「野手」ではメイン守備に「投」は選べません")
   h=self.vars["handed"].get();self.vars["leftthrow"].set(h.startswith("左投"));self.vars["switch"].set("両打" in h);self.vars["leftbat"].set(("左打" in h) and ("両打" not in h))
   r[26]=POS.index(self.vars["main"].get())|(16 if self.vars["leftthrow"].get() else 0)|(32 if self.vars["leftbat"].get() else 0)|(64 if self.vars["switch"].get() else 0)
   r[31]=BATFORMS.index(self.vars["bat"].get());r[40]=PITCHFORMS.index(self.vars["pitchform"].get())
   r[14:26]=self._current_name_raw()
   for i,(f,a,la,b,lb,lab) in enumerate(self.pw):
    if self.vars["ptype"].get()=="野手":
     a.set("球種なし");la.set(0);b.set("球種なし");lb.set(0);r[41+i]=r[47+i]=0;continue
    def encpitch(name,lv):
     if name=="球種なし":return 0
     if lv<1:raise ValueError(f"{f}: {name} は変化量1～7を指定してください")
     return (lv<<5)|(pitch_code(f,name)&31)
    r[41+i]=encpitch(a.get(),la.get());r[47+i]=encpitch(b.get(),lb.get())
   if self.vars["ptype"].get()=="野手":
    r[53:67]=b"\x00"*14;r[40]=0
    for _b in range(85,93):r[_b]=0
    for (bn,j),v in self.av.items():
     if 86<=bn<=93:v.set(False)
   elif self.ori_enabled.get()=="無":
    # 本物データでは「オリ変なしの投手」は byte54=FF（終端のみ）。a_44 がそれ。
    # 読み込んだRAWが FF 00*13 のときはFFを保持する（触っていないバイトを壊さない）。
    _keepff=(r[53]==0xFF and not any(r[54:67]))
    r[53:67]=b"\x00"*14
    if _keepff:r[53]=0xFF
   else:
    _os=int(self.oriv["speed"].get());_oh=int(self.oriv["h"].get());_ov=int(self.oriv["v"].get());_on=int(self.oriv["nobi"].get());_ok=int(self.oriv["kire"].get())
    if not(-128<=_os<=127 and -128<=_oh<=127 and -128<=_ov<=127):raise ValueError("オリ変: スピード/横変化/縦変化は符号付き8-bit範囲 -128～+127 で入力してください")
    if not(0<=_on<=15 and 0<=_ok<=15):raise ValueError("オリ変: ノビ/キレは4-bit値 0～15 で入力してください")
    r[53:62]=encode_ori_name(self.oriname.get());r[62]=int(self.oriv["speed"].get())&255;r[63]=["なし","スライダー系","カーブ系","フォーク系","シンカー系","シュート系","ストレート系"].index(self.oriv["base"].get());r[64]=int(self.oriv["h"].get())&255;r[65]=int(self.oriv["v"].get())&255;r[66]=((int(self.oriv["nobi"].get())&15)<<4)|(int(self.oriv["kire"].get())&15)
   for (bn,j),v in self.av.items():
    m=1<<(7-j)
    if v.get():r[bn-1]|=m
    else:r[bn-1]&=(~m)&255
   _third_set=0 if self.vars["ptype"].get()=="野手" else int(self.third_pitch_set.get().split()[0])
   r[91]=(r[91]&0x0F)|((_third_set&0x0F)<<4)
   if self.vars["passplayer"].get():r[94]|=0x10
   else:r[94]&=0xEF
   o=ORIGINS.index(self.vars["origin"].get());t=TEAMS.index(self.vars["team"].get());sk=SKINS.index(self.vars["skin"].get());fc=self.vars["face"].get()
   mode=["なし","着帽写真","ミニ顔","撮影写真"].index(self.vars["facemode"].get())
   if mode==3 and (fc&0xFF)!=0: raise ValueError("Wiki仕様: 撮影写真は正規パス出力では顔下位byte=00固定です")
   pack_appearance(r,o,t,sk,fc);r[105]=mode
   self.refresh_raw_only()
   return True
  except Exception as e:
   if showerror:messagebox.showerror("入力エラー",str(e))
   return False
 def refresh_raw_only(self):
  self.rt.delete("1.0","end");self.rt.insert("1.0",dump(self.r))
 def autotab(self,event=None):
  # Leaving/changing a tab commits current editor state to RAW.
  self.commit_all(showerror=False)
  # 任意タブ編集: 開いたら基準RAWを読み直し、離れたらタブ内の編集を破棄。
  if hasattr(self,"_free_outer"):
   if self.nb.select()==self._free_outer:self._free_load_base()
   else:self._free_reset()
 def applybasic(self):
  r=self.r;r[28]=self.vars["power"].get();r[29]=(self.vars["meet"].get()<<4)|self.vars["arm"].get();r[30]=(self.vars["run"].get()<<4)|self.vars["field"].get();r[33]=(self.vars["traj"].get()<<4)|self.vars["error"].get()
  r[37]=self.vars["speed"].get();r[38]=self.vars["control"].get();r[39]=self.vars["stamina"].get();r[32]=self.vars["number"].get();r[27]=(POS.index(self.vars["sub1"].get())<<4)|POS.index(self.vars["sub2"].get())
  h=self.vars["handed"].get();self.vars["leftthrow"].set(h.startswith("左投"));self.vars["switch"].set("両打" in h);self.vars["leftbat"].set(("左打" in h) and ("両打" not in h))
  r[26]=POS.index(self.vars["main"].get())|(16 if self.vars["leftthrow"].get() else 0)|(32 if self.vars["leftbat"].get() else 0)|(64 if self.vars["switch"].get() else 0);r[31]=BATFORMS.index(self.vars["bat"].get());r[40]=PITCHFORMS.index(self.vars["pitchform"].get())
  try:r[14:26]=self._current_name_raw()
  except Exception as e:messagebox.showerror("Name",str(e));return
  self.sync()
 def applyp(self):
  for i,(f,a,la,b,lb,lab) in enumerate(self.pw):
   def encpitch(name,lv):
    if name=="球種なし":return 0
    if lv<1:raise ValueError(f"{f}: {name} は変化量1～7を指定してください")
    return (lv<<5)|(pitch_code(f,name)&31)
   self.r[41+i]=encpitch(a.get(),la.get());self.r[47+i]=encpitch(b.get(),lb.get())
  self.sync()
 def applyori(self, dosync=True):
  try:
   if self.vars["ptype"].get()=="野手" or self.ori_enabled.get()=="無":
    _keepff=(self.vars["ptype"].get()=="投手" and self.r[53]==0xFF and not any(self.r[54:67]))
    self.r[53:67]=b"\x00"*14
    if _keepff:self.r[53]=0xFF
    if dosync:self.sync()
    return True
   _os=int(self.oriv["speed"].get());_oh=int(self.oriv["h"].get());_ov=int(self.oriv["v"].get());_on=int(self.oriv["nobi"].get());_ok=int(self.oriv["kire"].get())
   if not(-128<=_os<=127 and -128<=_oh<=127 and -128<=_ov<=127):raise ValueError("オリ変: スピード/横変化/縦変化は符号付き8-bit範囲 -128～+127 で入力してください")
   if not(0<=_on<=15 and 0<=_ok<=15):raise ValueError("オリ変: ノビ/キレは4-bit値 0～15 で入力してください")
   self.r[53:62]=encode_ori_name(self.oriname.get())
   self.r[62]=int(self.oriv["speed"].get())&255
   self.r[63]=["なし","スライダー系","カーブ系","フォーク系","シンカー系","シュート系","ストレート系"].index(self.oriv["base"].get())
   self.r[64]=int(self.oriv["h"].get())&255
   self.r[65]=int(self.oriv["v"].get())&255
   self.r[66]=((int(self.oriv["nobi"].get())&15)<<4)|(int(self.oriv["kire"].get())&15)
   if dosync:self.sync()
   return True
  except Exception as e:
   if dosync:messagebox.showerror("Original pitch",str(e))
   return False
 def applyabilities(self):
  for (bn,j),v in self.av.items():
   m=1<<(7-j)
   if v.get():self.r[bn-1]|=m
   else:self.r[bn-1]&=(~m)&255
  _third_set=0 if self.vars["ptype"].get()=="野手" else int(self.third_pitch_set.get().split()[0])
  self.r[91]=(self.r[91]&0x0F)|((_third_set&0x0F)<<4)
  self.sync()
 def applyapp(self):
  o=ORIGINS.index(self.vars["origin"].get());t=TEAMS.index(self.vars["team"].get());s=SKINS.index(self.vars["skin"].get());fc=self.vars["face"].get();pack_appearance(self.r,o,t,s,fc);self.r[105]=["なし","着帽写真","ミニ顔","撮影写真"].index(self.vars["facemode"].get());self.sync()
 def applyraw(self):
  try:self.r=parse(self.rt.get("1.0","end"));self.sync()
  except Exception as e:messagebox.showerror("RAW",str(e))
 def reset(self):self.r=minimal();self.sync()
 def gen(self):
  try:
   if not self.commit_all(showerror=True):return
   pw,self.r=encode(self.r);self.sync();self.pt.delete("1.0","end");self.pt.insert("1.0",format_password_groups(pw))
   warn="";L=len(pw)
   if L>128:warn="\nWARNING: Poke12 only reads through character 128; Wiki says longer passwords cannot be entered."
   for x in poke12_structure_warnings(self.r):warn+="\n"+x
   self.updatelen();self.info.delete("1.0","end");self.info.insert("1.0",f"Length: {L} chars\nChecksum: {self.r[12]:02X} {self.r[13]:02X}\nbyte95: {self.r[94]:02X}  Pass-player: {'ON' if self.r[94]&0x10 else 'OFF'}{warn}\n\n{dump(self.r)}")
   self.vstatus.set(f"VALID  VALID / checksum OK / round-trip {L}/{L}")
   self.qrshow()
  except Exception as e:messagebox.showerror("Encode",str(e))
 def dec(self):
  try:
   _text=self.pt.get("1.0","end");self.r,ok,c=decode(_text);self.pt.delete("1.0","end");self.pt.insert("1.0",format_password_groups(_text));self.sync();self.info.delete("1.0","end");self.info.insert("1.0",f"Checksum valid: {ok}\nStored {self.r[12]:02X} {self.r[13]:02X} / Calc {c[0]:02X} {c[1]:02X}\nbyte95: {self.r[94]:02X}  Pass-player: {'ON' if self.r[94]&0x10 else 'OFF'}\n\n{dump(self.r)}")
  except Exception as e:messagebox.showerror("Decode",str(e))
 def updatelen(self):
  n=len("".join(ch for ch in self.pt.get("1.0","end") if not ch.isspace()))
  # ROM(overlay17)のパスワード作業バッファは 0x60 = 96 バイト固定。b2v は 3 バイト -> 4 文字
  # なので 96 バイト = ちょうど 128 文字。129 文字は構造上存在しない（127,128,130,131...と飛ぶ）。
  q,rem=divmod(n,4)
  b=3*q+{0:0,2:1,3:2}.get(rem)  if rem!=1 else None
  bs=f"圧縮{b}バイト" if b is not None else "長さ不正"
  self.lenstatus.set(f"{n}文字 / {bs} （バッファ96byte=128文字、130文字以上は実機入力不可）  "
                     + ("OK: ポケ12へ入力可能" if n<=GAME_PASSWORD_LIMIT else "OVER: ゲーム実機へ入力不可"))

 def _password_text_edited(self,event=None):
  self.updatelen()
  self.vstatus.set("UNVALIDATED  パス文字が変更されました")
  self._qrphoto=None;self._qrpng=None
  self.qrlabel.configure(image="",text="パス文字が変更されました。「QR表示」で更新してください")

 # ---- 任意タブ編集（v1.59：未知メモリ検証タブの置き換え） -------------------------
 def freeui(self):
  f=self.tfree
  self.fr_base=None;self.fr_last_raw=None;self.fr_last_pw="";self._fr_qrphoto=None
  ttk.Label(f,text="任意タブ編集",font=("",13,"bold")).grid(row=0,column=0,columnspan=6,sticky="w",padx=8,pady=(10,4))
  helpf=ttk.LabelFrame(f,text="使い方")
  helpf.grid(row=1,column=0,columnspan=6,sticky="ew",padx=8,pady=6)
  ttk.Label(helpf,text=(
   "① このタブを開いた時点の選手（他タブの編集内容）を基準RAWとして読み込みます。\n"
   "② 『上書き指定』に RAW番号=値 を書いて『生成』を押すと、その値で上書きしたパス／QRを出力します。\n"
   "   書式: 81=65, 92=FB ／ 範囲 35-37=00 ／ 区切りはカンマ・空白・改行 ／ # 以降はコメント\n"
   "   byte番号は10進（RAW番号は1始まり）、値は16進（0x省略可）。"),
   justify="left",wraplength=1050).grid(row=0,column=0,sticky="w",padx=6,pady=5)
  ttk.Label(helpf,text=("※ このタブでの編集内容はこのタブ内だけで有効です。他のタブへ移動すると上書き指定と出力は破棄され、"
   "基礎能力・特殊能力などの通常の編集内容には一切反映されません。戻ってきたときは、その時点の編集内容から基準RAWを読み直します。"),
   foreground="#a00000",justify="left",wraplength=1050).grid(row=1,column=0,sticky="w",padx=6,pady=(0,5))
  basef=ttk.LabelFrame(f,text="基準RAW（RAW106）")
  basef.grid(row=2,column=0,columnspan=6,sticky="ew",padx=8,pady=6)
  ttk.Button(basef,text="基準RAWを読み直す",command=self._free_load_base).grid(row=0,column=0,sticky="w",padx=6,pady=5)
  self.fr_base_status=tk.StringVar(value="未読込")
  ttk.Label(basef,textvariable=self.fr_base_status,wraplength=800,justify="left").grid(row=0,column=1,sticky="w",padx=6,pady=5)
  ttk.Button(basef,text="アドレス表を開く",command=self.show_address_table).grid(row=0,column=2,sticky="e",padx=6,pady=5)
  specf=ttk.LabelFrame(f,text="上書き指定")
  specf.grid(row=3,column=0,columnspan=6,sticky="ew",padx=8,pady=6)
  self.fr_spec=tk.Text(specf,height=4,width=90,font=("Consolas",11));self.fr_spec.grid(row=0,column=0,columnspan=4,sticky="w",padx=6,pady=5)
  self.fr_recalc=tk.BooleanVar(value=True)
  ttk.Checkbutton(specf,text="可能なら圧縮・チェックサムに反映",variable=self.fr_recalc).grid(row=1,column=0,sticky="w",padx=6)
  ttk.Label(specf,text=("ON: 上書き後のRAWから byte1–12（圧縮フラグ）と byte13–14（checksum）を再計算します。byte1–14への指定は再計算で上書きされます。\n"
   "OFF: 指定したRAWをそのまま文字化します。圧縮フラグが0のbyteは値があっても送られず、checksumも再計算しないため、実機で弾かれるパスになることがあります。"),
   foreground="#444",justify="left",wraplength=1000).grid(row=2,column=0,columnspan=4,sticky="w",padx=6,pady=(0,5))
  af=ttk.Frame(f);af.grid(row=4,column=0,columnspan=6,sticky="w",padx=8,pady=6)
  ttk.Button(af,text="生成",command=self._free_generate).pack(side="left")
  ttk.Button(af,text="COPY",command=self._free_copy).pack(side="left",padx=5)
  ttk.Button(af,text="QR保存",command=self._free_qrsave).pack(side="left",padx=5)
  self.fr_status=tk.StringVar(value="待機中")
  ttk.Label(f,textvariable=self.fr_status,font=("",13,"bold")).grid(row=5,column=0,columnspan=6,sticky="w",padx=8,pady=4)
  self.fr_pw=tk.Text(f,height=5,width=90,font=("",13),wrap="word");self.fr_pw.grid(row=6,column=0,columnspan=6,sticky="w",padx=8)
  self.fr_qrlabel=ttk.Label(f,text="");self.fr_qrlabel.grid(row=7,column=0,columnspan=6,sticky="w",padx=8,pady=6)
  self.fr_info=tk.Text(f,height=16,width=110,font=("Consolas",9));self.fr_info.grid(row=8,column=0,columnspan=6,sticky="w",padx=8,pady=(0,10))

 def _free_reset(self):
  if not hasattr(self,"fr_spec"):return
  self.fr_base=None;self.fr_last_raw=None;self.fr_last_pw="";self._fr_qrphoto=None
  self.fr_spec.delete("1.0","end");self.fr_pw.delete("1.0","end");self.fr_info.delete("1.0","end")
  self.fr_qrlabel.configure(image="",text="")
  self.fr_base_status.set("未読込（このタブを開くと読み込みます）");self.fr_status.set("待機中")

 def _free_load_base(self):
  try:
   pw,norm=encode(bytearray(self.r))
   self.fr_base=bytearray(norm)
   name=decode_name_bytes(norm[14:26]) or "（無名）";ptype="投手" if (norm[26]&15)==1 else "野手"
   self.fr_base_status.set(f"読込済み: {name} / {ptype} / 基準パス {len(pw)}文字")
  except Exception as e:
   self.fr_base=None;self.fr_base_status.set("読込失敗: "+str(e))

 def _free_parse(self,text):
  edits={}
  for line in text.splitlines():
   line=line.split("#",1)[0]
   for tok in line.replace(",", " ").replace("、"," ").split():
    if "=" not in tok:raise ValueError(f"書式エラー: {tok}（例: 81=65）")
    a,v=tok.split("=",1)
    val=int(v,16)
    if not 0<=val<=255:raise ValueError(f"値は00–FF: {tok}")
    if "-" in a:
     x,y=(int(s,10) for s in a.split("-",1));rng=range(min(x,y),max(x,y)+1)
    else:rng=[int(a,10)]
    for b in rng:
     if not 1<=b<=106:raise ValueError(f"byte番号は1–106: {tok}")
     edits[b]=val
  return edits

 def _free_generate(self):
  try:
   if self.fr_base is None:self._free_load_base()
   if self.fr_base is None:raise ValueError("基準RAWを読み込めません")
   edits=self._free_parse(self.fr_spec.get("1.0","end"))
   base=bytearray(self.fr_base);r=bytearray(base)
   for b,v in edits.items():r[b-1]=v
   notes=[]
   if self.fr_recalc.get():
    pw,out=encode(r)
    lost=[b for b in sorted(edits) if b<=14 and out[b-1]!=edits[b]]
    if lost:notes.append("byte1–14の指定は再計算で上書き: "+", ".join(f"byte{b} {edits[b]:02X}→{out[b-1]:02X}" for b in lost))
   else:
    out=bytearray(r);pw=encode_raw(out)
   try:
    dec,ok,calc=decode(pw)
    back=[i+1 for i in range(106) if dec[i]!=out[i]]
    ck=("OK" if ok else f"不一致 stored={dec[12]:02X} {dec[13]:02X} calc={calc[0]:02X} {calc[1]:02X}")
   except Exception as e:
    dec=None;ok=False;back=None;ck="復号不能: "+str(e)
   L=len(pw)
   lim="入力可（≤128）" if L<=GAME_PASSWORD_LIMIT else "実機入力不可（128文字超）"
   self.fr_status.set(f"{L}文字 / {lim} / checksum {('OK' if ok else 'NG')}")
   self.fr_pw.delete("1.0","end");self.fr_pw.insert("1.0",format_password_groups(pw))
   self.fr_last_pw=pw;self.fr_last_raw=bytearray(out)
   lines=[f"上書き指定: {len(edits)}byte"]
   for b in sorted(edits):lines.append(f"  byte{b:3d}: {base[b-1]:02X} → {edits[b]:02X}")
   lines+=notes
   lines.append(f"checksum: {ck}")
   if back is None:pass
   elif back:lines.append("復号結果が出力RAWと一致しないbyte（圧縮フラグ0で送られなかった値など）: "+", ".join(str(b) for b in back))
   else:lines.append("復号結果: 出力RAWと完全一致")
   lines.append("");lines.append("出力RAW106:");lines.append(dump(out))
   self.fr_info.delete("1.0","end");self.fr_info.insert("1.0","\n".join(lines))
   import tempfile
   p=os.path.join(tempfile.gettempdir(),"pawapoke12_free_qr.png");qr_write_file(pw,p)
   self._fr_qrphoto=tk.PhotoImage(file=p);self.fr_qrlabel.configure(image=self._fr_qrphoto,text="")
  except Exception as e:messagebox.showerror("任意タブ編集",str(e))

 def _free_copy(self):
  if not self.fr_last_pw:return
  self.clipboard_clear();self.clipboard_append(self.fr_last_pw)

 def _free_qrsave(self):
  from tkinter import filedialog
  if not self.fr_last_pw:messagebox.showerror("QR保存","先に『生成』を押してください");return
  p=filedialog.asksaveasfilename(defaultextension=".png",filetypes=[("PNG","*.png")])
  if not p:return
  try:qr_write_file(self.fr_last_pw,p);messagebox.showinfo("QR保存","保存しました")
  except Exception as e:messagebox.showerror("QR保存",str(e))

 def show_address_table(self):
  cur=self.fr_last_raw or self.fr_base or self.r
  w=tk.Toplevel(self);w.title("ポケ12 パスワードRAW アドレス表");w.geometry("1150x700")
  nb=ttk.Notebook(w);nb.pack(fill="both",expand=True,padx=6,pady=6)
  t1=ttk.Frame(nb);nb.add(t1,text="バイト構造")
  top=ttk.Frame(t1);top.pack(fill="x",pady=4)
  ttk.Label(top,text="検索").pack(side="left",padx=4);q=tk.StringVar();ttk.Entry(top,textvariable=q,width=24).pack(side="left")
  ttk.Label(top,text="  現在値＝このタブの最新出力（未生成なら基準RAW）。RAW番号は1始まり。").pack(side="left")
  cols=("byte","now","min")+tuple(f"b{7-j}" for j in range(8))+("note",)
  fr=ttk.Frame(t1);fr.pack(fill="both",expand=True)
  tr=ttk.Treeview(fr,columns=cols,show="headings")
  heads={"byte":("byte",45),"now":("現在値",55),"min":("最小",45),"note":("備考",680)}
  for j in range(8):heads[f"b{7-j}"]=(str(1<<(7-j)),105)
  for c in cols:tr.heading(c,text=heads[c][0]);tr.column(c,width=heads[c][1],minwidth=heads[c][1],anchor="w",stretch=False)
  sy=ttk.Scrollbar(fr,orient="vertical",command=tr.yview);sx=ttk.Scrollbar(fr,orient="horizontal",command=tr.xview)
  tr.configure(yscrollcommand=sy.set,xscrollcommand=sx.set)
  tr.grid(row=0,column=0,sticky="nsew");sy.grid(row=0,column=1,sticky="ns");sx.grid(row=1,column=0,sticky="ew")
  fr.rowconfigure(0,weight=1);fr.columnconfigure(0,weight=1)
  rows=poke12_byte_map()
  def fill(*_):
   z=q.get().strip();tr.delete(*tr.get_children())
   for b in range(1,107):
    cells,mn,note=rows[b]
    if z and not(z==str(b) or any(z in c for c in cells) or z in note):continue
    tr.insert("","end",values=(b,f"{cur[b-1]:02X}",mn)+tuple(cells)+(note,))
  q.trace_add("write",fill);fill()
  for title,text in (("97–100 可変配置",poke12_appearance_layout_text()),("設定コード",poke12_code_lists_text())):
   t=ttk.Frame(nb);nb.add(t,text=title)
   tx=tk.Text(t,font=("Consolas",10),wrap="none");s2=ttk.Scrollbar(t,orient="vertical",command=tx.yview);tx.configure(yscrollcommand=s2.set)
   tx.pack(side="left",fill="both",expand=True);s2.pack(side="right",fill="y")
   tx.insert("1.0",text);tx.configure(state="disabled")
 def qrload(self):
  from tkinter import filedialog,messagebox
  p=filedialog.askopenfilename(filetypes=[("Image","*.png *.jpg *.jpeg *.bmp"),("All","*.*")])
  if not p:return
  try:
   t=qr_read_file(p);self.pt.delete("1.0","end");self.pt.insert("1.0",format_password_groups(t));self.updatelen();self.validateui()
  except Exception as e:messagebox.showerror("QR読込",str(e))
 def _make_qr_png(self,text,path):
  return qr_write_file(text,path)

 def qrshow(self):
  import tempfile
  from tkinter import messagebox
  t="".join(ch for ch in self.pt.get("1.0","end") if not ch.isspace())
  v=validate_password_text(t)
  if not v["valid"]:
   messagebox.showerror("QR表示","有効なパスワードではありません:\\n"+v["message"]);return
  try:
   p=os.path.join(tempfile.gettempdir(),"pawapoke12_qr_preview.png")
   self._make_qr_png(t,p)
   self._qrphoto=tk.PhotoImage(file=p)
   self.qrlabel.configure(image=self._qrphoto,text="")
   self._qrpng=p
  except Exception as e:messagebox.showerror("QR表示",str(e))
 def qrsave(self):
  from tkinter import filedialog,messagebox
  t="".join(ch for ch in self.pt.get("1.0","end") if not ch.isspace())
  v=validate_password_text(t)
  if not v["valid"]:
   messagebox.showerror("QR保存","有効なパスワードではありません:\n"+v["message"]);return
  p=filedialog.asksaveasfilename(defaultextension=".png",filetypes=[("PNG","*.png")])
  if not p:return
  try:
   self._make_qr_png(t,p)
   messagebox.showinfo("QR保存","保存しました")
  except Exception as e:messagebox.showerror("QR保存",str(e))

 def validateui(self):
  v=validate_password_text(self.pt.get("1.0","end"))
  self.vstatus.set(("VALID  " if v["valid"] else "INVALID  ")+v["message"])
  self.info.delete("1.0","end")
  self.info.insert("1.0",f'Stage: {v["stage"]}\nLength: {v["length"]}\n{v["message"]}\n')
  if v.get("raw") is not None:
   _text=self.pt.get("1.0","end");self.pt.delete("1.0","end");self.pt.insert("1.0",format_password_groups(_text))
   self.info.insert("end","\n"+dump(v["raw"]))
   if v["valid"]:
    self.r=bytearray(v["raw"]);self.sync()
 def copy(self):
  s=clean(self.pt.get("1.0","end"));self.clipboard_clear();self.clipboard_append(s)

if __name__=="__main__":
 if not selftest():raise RuntimeError("codec self-test failed")
 App().mainloop()
