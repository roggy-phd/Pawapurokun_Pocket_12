"""PowerPoke 12 season batting stats (0x12 bytes per player, 26 per club)."""
import json
from pathlib import Path
import pp12_core as core

BATTERS=26
BAT_STRIDE=0x12
BAT_OFFSET_BEFORE_PITCHERS=26*BAT_STRIDE
FIELDS=['ペナントスロット','球団番号','球団名','球団ID','選手枠','選手名','レコード位置','打席','打数','安打','二塁打','三塁打','本塁打','打点','四球','死球','三振','盗塁','犠打','未解読_0x09','打率','出塁率(犠飛0前提)','長打率','OPS(犠飛0前提)','未解読_0x11(盗塁死の可能性)','警告']


def standard_rosters():
    path=Path(__file__).resolve().with_name('standard_batters_2009.json')
    if not path.is_file(): raise FileNotFoundError(f'標準野手名データがありません: {path}')
    return json.loads(path.read_text(encoding='utf-8'))


def rosters26(mem,pitch_start,codes):
    P=pitch_start-0x1106
    std=standard_rosters()
    pitcher_rosters=core.resolve_rosters(mem,pitch_start,codes)
    roster={}
    for i in range(12):
        club,pitch_names,_,tid=pitcher_rosters[i+1]
        if 0 <= tid < 12:
            names=list(std[str(tid)])
            # Existing pitcher reference data already has corrections to original encoding
            names[:12]=pitch_names[:12]
        elif 0xf0<=tid<=0xfb:
            a=P+core.CUSTOM_ROSTER_OFFSET+(tid-0xf0)*core.CUSTOM_TEAM_STRIDE
            names=[core.decode_roster_name(mem[a+j*0x44:a+j*0x44+12],codes) for j in range(26)]
        else:
            names=['']*26
        roster[i+1]=(club,tid,names)
    return roster


def rec(mem,off,slot,team,club,tid,index,name,loc):
    pa=core.r16(mem,off)
    hits=core.r16(mem,off+2)&0xfff
    doubles=core.r16(mem,off+4)&0xfff
    triples=mem[off+6];hr=mem[off+7]
    sacrifice=mem[off+8];unknown09=mem[off+9]
    rbi=core.r16(mem,off+0xa)&0xfff
    strikeouts=core.r16(mem,off+0xc)&0xfff
    bb,hbp,sb,unknown=[mem[off+j] for j in (0xe,0xf,0x10,0x11)]
    ab=pa-bb-hbp-sacrifice-unknown09
    warn=[]
    if ab<0 or hits>ab or doubles+triples+hr>hits:warn.append('打撃記録要確認')
    # +0x08 behaves as 犠打 (SH): pitchers reach 0.057/PA vs 0.031/PA for position players.
    # +0x09 is 0 in every record of both verified saves (1248 records), so 犠飛 (SF) appears not to
    # be stored, the same way 被本塁打 is not.  OBP/OPS are therefore computed assuming SF = 0 and
    # the column names say so; they are exact only if SF really is absent from the save.
    avg=hits/ab if ab>0 else None
    tb=hits+doubles+2*triples+3*hr
    slg=tb/ab if ab>0 else None
    reached=ab+bb+hbp
    obp=(hits+bb+hbp)/reached if reached>0 else None
    ops=(obp+slg) if (obp is not None and slg is not None) else None
    def v(x):return f'{x:.4f}' if x is not None else ''
    return dict(zip(FIELDS,[slot,team,club,f'0x{tid:02X}',index+1,name,loc,pa,ab,hits,doubles,triples,hr,rbi,bb,hbp,strikeouts,sb,sacrifice,unknown09,v(avg),v(obp),v(slg),v(ops),unknown,'; '.join(warn)]))
