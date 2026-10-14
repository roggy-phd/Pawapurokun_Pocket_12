#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""パワポケ12の通常セーブ(.sav)またはmelonDS 1.1ステート(.ml*)から投手シーズン成績をCSV出力。
Python 3.8+ 標準ライブラリのみ。--cli でGUIを使わずに実行できます。
"""
import csv
from pathlib import Path
import struct
import json

RAM_START=0x02000000
RAM_BYTES=0x400000
STAT_SIZE=0x16
TEAM_STRIDE=0x308
PITCHERS=12
TEAMS=12
STATE_RAM_OFFSET=0x24
SAVE_BYTES=0x80000          # 通常セーブ (.sav) は512KB。ペナント①の成績配列が平文で入っている
FIELDS=['球団番号','球団名','投手枠','投手名','レコード位置','登板','完投','完封','勝利','敗戦','セーブ','未解読_0x09(本データではセーブと一致)','HP','投球回','投球アウト数','奪三振','与四球','与死球','与四死球','被安打','自責点','防御率','K/9','BB/9','K/BB','WHIP','K-BB/9','残り有効スタミナ','未解読_0x14','警告']

def r16(buf,pos):
    return struct.unpack_from('<H',buf,pos)[0]

def parse_rec(mem, off, name='', team=0, slot=0, loc='', club=''):
    outs=r16(mem,off);k=r16(mem,off+2)
    cg,sh,w,l,sv,hold=mem[off+4:off+10]
    bb,hbp,g,hp=mem[off+10:off+14]
    er=r16(mem,off+14)&0x3ff
    stamina=r16(mem,off+16)&0xfff
    hits=r16(mem,off+18)&0x3ff
    unknown=r16(mem,off+20)
    ip=outs/3
    notes=[]
    if outs==0 and (k or er or hits): notes.append('投球回ゼロで記録あり')
    if outs and (k>outs+100 or hits>outs+200):notes.append('成績値要確認')
    if cg>g or sh>cg or w+l>g+2:notes.append('成績値不整合')
    if any((bb==255,hbp==255,g==255,hp==255)):notes.append('8bitの上限付近: オーバーフロー注意')
    def fmt(v):return f'{v:.4f}' if v is not None else ''
    ip_display=f'{outs//3}' if outs%3==0 else f'{outs//3} {outs%3}/3'
    return dict(zip(FIELDS,[team,club,slot,name,loc,g,cg,sh,w,l,sv,hold,hp,ip_display,outs,k,bb,hbp,bb+hbp,hits,er,fmt(9*er/ip) if ip else '',fmt(9*k/ip) if ip else '',fmt(9*bb/ip) if ip else '',fmt(k/bb) if bb else '',fmt((hits+bb)/ip) if ip else '',fmt(9*(k-bb)/ip) if ip else '',stamina,unknown,'; '.join(notes)]))

def plausible(mem,off):
    if off < 0 or off+STAT_SIZE>len(mem):return False
    g=mem[off+12]; cg=mem[off+4]; sh=mem[off+5]; w=mem[off+6];l=mem[off+7]
    if g>145 or cg>g or sh>cg or w+l>g+2:return False
    outs=r16(mem,off);k=r16(mem,off+2);er=r16(mem,off+14)&1023;hits=r16(mem,off+18)&1023
    if outs>4000 or k>2400 or k>outs+160 or er>outs+40 or hits>outs+180:return False
    return True

def team_score(mem, off):
    if off<0 or off+TEAM_STRIDE>len(mem):return -1
    active=0
    for j in range(PITCHERS):
        p=off+j*STAT_SIZE
        if not plausible(mem,p):return -1
        if mem[p+12]>=8 and r16(mem,p)>=30:active+=1
    return active if active>=4 else -1

def open_source(data):
    """melonDSステートと通常セーブの両方を受け付け、(探索バッファ, 走査範囲, 位置表記, 種別名) を返す。

    melonDS 1.1 の .ml1 は先頭が ASCII 'MELN' で、ARM9主RAM 4MB がファイル先頭 0x24 から入る。
    通常セーブ (.sav, 512KB) にはペナント①の投手成績配列がそのまま平文で入っているので、
    ファイル全体を走査対象にする。どちらも読み取り専用で開き、入力は一切書き換えない。
    """
    if data[:4]==b'MELN':
        if len(data) < STATE_RAM_OFFSET+RAM_BYTES:
            raise ValueError('ステートに必要な4MBメモリ領域がありません。壊れているか別バージョンの形式です。')
        mem=memoryview(data)[STATE_RAM_OFFSET:STATE_RAM_OFFSET+RAM_BYTES]
        return mem,0x200000,0x3f0000,(lambda o:f'RAM 0x{RAM_START+o:08X}'),'melonDSステート'
    if len(data)==SAVE_BYTES:
        return memoryview(data),0,len(data),(lambda o:f'セーブ +0x{o:05X}'),'通常セーブ'
    raise ValueError('melonDSステート (先頭MELN) でも512KBの通常セーブでもありません: %d バイト'%len(data))

def find_tables(data):
    mem,begin,end,locfmt,kind=open_source(data)
    candidates=[]
    for off in range(begin,end-TEAMS*TEAM_STRIDE,2):
        if not (40<=mem[off+12]<=145 and mem[off+4]<=mem[off+12]):continue
        if not (120<=r16(mem,off)<=2500 and 25<=r16(mem,off+2)<=1600):continue
        if team_score(mem,off)<4:continue
        # この位置を球団先頭とする連続12球団配列を検証
        total=0;valid=0
        for i in range(TEAMS):
            s=team_score(mem,off+i*TEAM_STRIDE)
            if s<0:break
            valid+=1;total+=s
        if valid>=10:candidates.append((valid,total,off))
    # 球団2番目からも候補が出る場合があるので、最も長い鎖・最多活動投手を選ぶ
    candidates.sort(reverse=True)
    output=[]
    for valid,total,off in candidates:
        if any(abs(off-p)<TEAM_STRIDE for p in output):continue
        output.append(off)
        if len(output)>=5:break
    return mem,output,locfmt,kind


# ペナント成績配列はチーム順と実際の球団IDを別管理する。
# P + team_index * 0x308 + 0xF07 : 球団ID
# 0x00-0x0B : 既存球団。名前はROM由来の通常球団表。
# 0xF0-   : 編成球団。P+0x33F0+(ID-0xF0)*0xA34 の選手名を参照。
TEAM_ID_OFFSET = 0xF07
CUSTOM_ROSTER_OFFSET = 0x33F0
CUSTOM_TEAM_STRIDE = 0xA34
ROSTER_PLAYER_STRIDE = 0x44
OFFICIAL_CLUBS = {0:'中日ドラゴンズ',1:'読売ジャイアンツ',2:'横浜ベイスターズ',3:'東京ヤクルトスワローズ',4:'広島東洋カープ',5:'阪神タイガース',6:'福岡ソフトバンクホークス',7:'埼玉西武ライオンズ',8:'オリックス・バファローズ',9:'千葉ロッテマリーンズ',10:'北海道日本ハムファイターズ',11:'東北楽天ゴールデンイーグルス'}

def load_name_codes():
    file = Path(__file__).resolve().with_name('name_codes.json')
    if not file.is_file():
        raise FileNotFoundError(f'文字コード表がありません: {file}')
    return {int(k,16):v for k,v in json.loads(file.read_text(encoding='utf-8')).items()}

def decode_roster_name(raw, codes):
    raw=bytes(raw[:12]); result=[]; pos=0
    while pos<len(raw):
        c=raw[pos]
        if c in (0,255):break
        if 0xE8<=c<=0xF7:
            if pos+1>=len(raw):return ''
            code=(c<<8)|raw[pos+1];pos+=2
        else:code=c;pos+=1
        value=codes.get(code)
        if value is None:return ''
        result.append(value)
    return ''.join(result).strip()

def load_standard_names():
    file=Path(__file__).resolve().with_name('standard_pitchers_2009.json')
    if not file.is_file():raise FileNotFoundError(f'標準選手名データがありません: {file}')
    return json.loads(file.read_text(encoding='utf-8'))

def resolve_rosters(mem, stats_start, codes):
    P=stats_start-0x1106
    db=load_standard_names()
    result={}
    for i in range(TEAMS):
        tid=mem[P+i*TEAM_STRIDE+TEAM_ID_OFFSET]
        if tid<12:
            # Standard roster is an in-game ROM-derived fixed list for the known 2009 ROM.
            raw=db['decoded'][str(tid)]
            display=db['normalized'][str(tid)]
            club=OFFICIAL_CLUBS[tid]
        elif 0xF0<=tid<=0xFB:
            base=P+CUSTOM_ROSTER_OFFSET+(tid-0xF0)*CUSTOM_TEAM_STRIDE
            if base+12*ROSTER_PLAYER_STRIDE>len(mem):
                raise ValueError('編成チームの選手データが範囲外です')
            raw=[decode_roster_name(mem[base+j*ROSTER_PLAYER_STRIDE:base+j*ROSTER_PLAYER_STRIDE+12],codes) for j in range(12)]
            display=list(raw)
            # Deduce source team from roster similarity, not from arbitrary block order.
            best=[]
            for k, standard in db['decoded'].items():
                match=sum(a==b for a,b in zip(raw[1:],standard[1:]))
                if match>=8:best.append((match,int(k)))
            best.sort(reverse=True)
            club=(OFFICIAL_CLUBS[best[0][1]]+'（編成）') if best and (len(best)==1 or best[0][0]>best[1][0]) else f'編成球団ID 0x{tid:02X}'
        else:
            raw=['']*12; display=['']*12;club=f'未対応球団ID 0x{tid:02X}'
        result[i+1]=(club,display,raw,tid)
    return result


def export(path,output,table_index=0,team_index=0):
    data=path.read_bytes()
    mem,tables,locfmt,kind=find_tables(data)
    if not tables:raise ValueError('12球団の連続した成績配列を検出できません。'
        'ステートならペナントのシーズン成績が読み込まれている場面で、通常セーブならシーズン記録が'
        '書き込まれた後のものを使ってください。')
    if table_index>=len(tables):raise ValueError('候補テーブル番号が範囲外です。')
    start=tables[table_index]
    codes=load_name_codes()
    # SAV uses the original bytes, state uses its full container for roster search.
    teams=resolve_rosters(mem,start,codes)
    rows=[]
    for i in range(TEAMS):
        if team_index and i+1!=team_index:continue
        base=start+i*TEAM_STRIDE
        for j in range(PITCHERS):
            off=base+j*STAT_SIZE
            club,display,raw,tid=teams[i+1]
            name=display[j]
            row=parse_rec(mem,off,team=i+1,slot=j+1,loc=locfmt(off),name=name,club=club)
            rows.append(row)
    with output.open('w',newline='',encoding='utf-8-sig') as f:
        writer=csv.DictWriter(f,fieldnames=FIELDS);writer.writeheader();writer.writerows(rows)
    return rows,tables,start,locfmt,kind


def gui_main(*_a,**_k):
    raise RuntimeError('pp12_core は内部モジュールです。pp12_pennant_stats.py を起動してください。')

if __name__=='__main__':
    print('pp12_core.py は内部モジュールです。pp12_pennant_stats.py を実行してください。')
    raise SystemExit(1)
