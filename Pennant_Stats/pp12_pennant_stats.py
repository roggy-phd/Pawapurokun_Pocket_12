#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""PowerPoke 12 pennant season pitcher-stat extractor, slots 1 & 2.
Works with 512KiB .sav and melonDS 1.1 .ml1 etc. Standard library only.
"""
from pathlib import Path
import argparse
import csv
import sys
import traceback
import pp12_core as core
import pp12_batters as batting

SAV_STARTS={1:0x182C2, 2:0x1F3C2}
HEADERS=['ペナントスロット']+core.FIELDS

def _valid_full_table(mem,off):
    return 0 <= off <= len(mem)-core.TEAMS*core.TEAM_STRIDE and all(
        core.team_score(mem,off+i*core.TEAM_STRIDE)>=0 for i in range(core.TEAMS))

def find_sources(path, slots='both'):
    data=Path(path).read_bytes()
    mem, candidates, location, kind = core.find_tables(data)
    selected=([1,2] if slots=='both' else [int(slots)]) if kind=='通常セーブ' else []
    result=[];notes=[]
    if kind=='通常セーブ':
        # The fixed offsets hold for every save verified so far, but fall back to the scan result
        # rather than giving up: find_tables has already located the candidates, and a candidate is
        # only accepted when it is itself a full 12-club table and is not the other slot's table.
        spare=[c for c in candidates if _valid_full_table(mem,c) and c not in SAV_STARTS.values()]
        for slot in selected:
            start=SAV_STARTS[slot]
            if not _valid_full_table(mem,start):
                if spare:
                    start=spare.pop(0)
                    notes.append(f'セーブスロット{slot}は既定位置 +0x{SAV_STARTS[slot]:X} で確認できず、'
                                 f'走査で見つかった +0x{start:X} を使用しました。スロット番号の対応は未確認です。')
                elif slots=='both':
                    # Never silently substitute data from the other slot.
                    continue
                else:
                    raise ValueError(f'セーブスロット{slot}の成績配列を確認できません（+0x{start:X}）。'
                                     '未使用・保存前・非対応形式の可能性があります。')
            result.append((slot,start))
        if not result:
            raise ValueError('セーブスロット１・２ともに有効な成績配列が見つかりません。未使用・保存前・非対応形式の可能性があります。')
    else:
        # A state contains the currently loaded pennant only. Never silently label it slot 1 or 2.
        valid=[p for p in candidates if _valid_full_table(mem,p)]
        if not valid: raise ValueError('melonDSステートにペナントの投手成績配列が見つかりません。')
        start=valid[0]
        if slots in ('both','active'):
            slot_label='ステート内（要指定）'
        else:slot_label=str(slots)+'（使用者指定）'
        result.append((slot_label,start))
    return mem,location,kind,result,notes

def extract(path,output,slots='both',team=0,kind='both'):
    mem,location,source_type,sources,notes=find_sources(path,slots)
    codes=core.load_name_codes()
    pitcher_rows=[];batter_rows=[]
    for slot,start in sources:
        pitcher_rosters=core.resolve_rosters(mem,start,codes)
        batter_rosters=batting.rosters26(mem,start,codes) if kind in ('batters','both') else {}
        for i in range(12):
            if team and i+1!=team:continue
            club,names,_,tid=pitcher_rosters[i+1]
            if kind in ('pitchers','both'):
                for j in range(12):
                    pos=start+i*core.TEAM_STRIDE+j*core.STAT_SIZE
                    row=core.parse_rec(mem,pos,team=i+1,slot=j+1,loc=location(pos),name=names[j],club=club)
                    pitcher_rows.append({'ペナントスロット':slot,**row})
            if kind in ('batters','both'):
                bc,bt,bnames=batter_rosters[i+1]
                for j in range(26):
                    pos=start+i*core.TEAM_STRIDE-batting.BAT_OFFSET_BEFORE_PITCHERS+j*batting.BAT_STRIDE
                    batter_rows.append(batting.rec(mem,pos,slot,i+1,bc,bt,j,bnames[j],location(pos)))
    def write(path,fields,rows):
        with open(path,'w',newline='',encoding='utf-8-sig') as file:
            writer=csv.DictWriter(file,fieldnames=fields)
            writer.writeheader();writer.writerows(rows)
    paths=[]
    if kind in ('pitchers','both'):
        dest=Path(output) if kind=='pitchers' else Path(output).with_name(Path(output).stem+'_pitchers.csv')
        write(dest,HEADERS,pitcher_rows); paths.append(str(dest))
    if kind in ('batters','both'):
        dest=Path(output) if kind=='batters' else Path(output).with_name(Path(output).stem+'_batters.csv')
        write(dest,batting.FIELDS,batter_rows); paths.append(str(dest))
    return pitcher_rows,batter_rows,source_type,sources,paths,notes

def gui():
    import tkinter as tk
    from tkinter import ttk,filedialog,messagebox
    root=tk.Tk();root.title('パワポケ12 ペナント成績CSV v3.0')
    root.geometry('750x480');root.minsize(650,430)
    main=ttk.Frame(root,padding=18);main.pack(fill='both',expand=True)
    ttk.Label(main,text='ペナント投手・打撃成績 CSV抽出',font=('',16,'bold')).pack(anchor='w',pady=(0,10))
    ttk.Label(main,text='通常セーブはペナント①・②に対応。melonDSステートは開いている1スロットのみ抽出します。',wraplength=660).pack(anchor='w',pady=(0,12))
    source=tk.StringVar(value=''); mode=tk.StringVar(value='sav');slot=tk.StringVar(value='セーブスロット１・２両方'); team=tk.StringVar(value='全チーム')
    status=tk.StringVar(value='ファイルを選択してください。'); export_kind=tk.StringVar(value='全て')
    pickrow=ttk.Frame(main);pickrow.pack(fill='x',pady=(0,9))
    def choose(kind):
        pats=('通常セーブ (*.sav)','*.sav') if kind=='sav' else ('melonDSステート (*.ml1～*.ml9)','*.ml1 *.ml2 *.ml3 *.ml4 *.ml5 *.ml6 *.ml7 *.ml8 *.ml9')
        path=filedialog.askopenfilename(parent=root,title='読み込むファイルを選択',filetypes=[pats,('すべてのファイル','*.*')])
        if path:
            mode.set(kind); source.set(path);status.set('読み込み準備OK')
            # State contains one active slot; 'both' is not meaningful.
            if kind=='ml':
                slot.set('現在開いているスロット')
            elif slot.get()=='現在開いているスロット':
                slot.set('セーブスロット１・２両方')
            slot_box.configure(values=options())
    ttk.Button(pickrow,text='.sav を選択',command=lambda:choose('sav')).pack(side='left',padx=(0,8))
    ttk.Button(pickrow,text='.ml* を選択',command=lambda:choose('ml')).pack(side='left',padx=(0,8))
    ttk.Button(pickrow,text='終了',command=root.destroy).pack(side='right')
    ttk.Label(main,textvariable=source,wraplength=655,foreground='#245484').pack(anchor='w',pady=(0,12))
    SLOT_LABELS = {
        'セーブスロット１・２両方': 'both',
        'セーブスロット１のみ': '1',
        'セーブスロット２のみ': '2',
        '現在開いているスロット': 'active',
    }
    DATA_LABELS = {'全て': 'both', '投手成績のみ': 'pitchers', '野手成績のみ': 'batters'}
    def options():
        return ['セーブスロット１・２両方', 'セーブスロット１のみ', 'セーブスロット２のみ'] if mode.get()=='sav' else ['現在開いているスロット', 'セーブスロット１のみ', 'セーブスロット２のみ']
    setting=ttk.Frame(main);setting.pack(fill='x',pady=(0,8))
    ttk.Label(setting,text='ペナント：').pack(side='left')
    slot_box=ttk.Combobox(setting,textvariable=slot,values=options(),state='readonly',width=26)
    slot_box.pack(side='left',padx=(4,20))
    ttk.Label(setting,text='球団：').pack(side='left')
    team_labels = ['全チーム'] + [f'同リーグ{i}番' for i in range(1,7)] + [f'別リーグ{i}番' for i in range(1,7)]
    team_ids = {label: idx for idx, label in enumerate(team_labels)}
    ttk.Combobox(setting,textvariable=team,values=team_labels,state='readonly',width=17).pack(side='left',padx=4)
    ttk.Label(main,text='抽出データ：').pack(anchor='w',pady=(8,2))
    ttk.Combobox(main,textvariable=export_kind,values=['全て','投手成績のみ','野手成績のみ'],state='readonly',width=18).pack(anchor='w',pady=(0,8))
    ttk.Label(main,text='「全て」では投手成績と野手成績を別々のCSVに出力します。',foreground='#555555').pack(anchor='w',pady=(0,14))
    def run():
        path=source.get()
        if not path:messagebox.showwarning('未選択','入力ファイルを選択してください。',parent=root);return
        output=filedialog.asksaveasfilename(parent=root,title='CSVの保存先',initialfile=Path(path).stem+'_pitchers.csv',defaultextension='.csv',filetypes=[('CSV','*.csv')])
        if not output:return
        button.configure(state='disabled');status.set('解析中…');root.update_idletasks()
        try:
            selected_slot = SLOT_LABELS[slot.get()]
            selected_team = team_ids[team.get()]
            p_rows,b_rows,kind,tables,paths,notes=extract(path,output,selected_slot,selected_team,DATA_LABELS[export_kind.get()])
            missing = [n for n in (1, 2) if n not in [x[0] for x in tables]] if kind == '通常セーブ' and selected_slot == 'both' else []
            warning = ('\n\n注意：スロット'+','.join(map(str,missing))+'の成績は確認できず、出力していません。未使用・保存前・非対応形式の可能性があります。') if missing else ''
            if notes: warning += '\n\n'+'\n'.join(notes)
            status.set(f'出力完了：投手{len(p_rows)}件、野手・打撃{len(b_rows)}件'+('（一部スロット未取得）' if missing else ''))
            messagebox.showwarning('一部スロット未取得',f'投手{len(p_rows)}件、野手・打撃{len(b_rows)}件を出力しました。\n'+'\n'.join(paths)+warning,parent=root) if missing else messagebox.showinfo('完了',f'投手{len(p_rows)}件、野手・打撃{len(b_rows)}件を出力しました。\n'+'\n'.join(paths),parent=root)
        except Exception as exc:
            status.set('エラー：'+str(exc));messagebox.showerror('抽出できませんでした',str(exc),parent=root)
        finally:button.configure(state='normal')
    button=ttk.Button(main,text='CSVを出力',command=run);button.pack(anchor='w',pady=(0,14))
    ttk.Label(main,textvariable=status,wraplength=660).pack(anchor='w')
    ttk.Label(main,text='基本能力・特殊能力は未実装。出塁率とOPSは犠飛が保存されていない前提での算出です。',foreground='#666').pack(side='bottom',anchor='w')
    root.mainloop()

def main():
    p=argparse.ArgumentParser(description='パワポケ12 ペナント①②の投手成績をCSVに出力')
    p.add_argument('input',nargs='?')
    p.add_argument('-o','--output')
    p.add_argument('--slot',choices=['1','2','both','active'],default='both')
    p.add_argument('--team',type=int,default=0)
    p.add_argument('--kind',choices=['pitchers','batters','both'],default='both')
    p.add_argument('--cli',action='store_true')
    args=p.parse_args()
    if args.input or args.cli:
        if not args.input:p.error('入力 .sav / .ml ファイルを指定してください')
        if args.team<0 or args.team>12:p.error('--team は0～12')
        out=args.output or str(Path(args.input).with_name(Path(args.input).stem+'_pitchers.csv'))
        p_rows,b_rows,kind,tables,paths,notes=extract(args.input,out,args.slot,args.team,args.kind)
        for n in notes: print('注意:',n)
        print(f'{kind}: 投手{len(p_rows)}件 打撃{len(b_rows)}件 → '+', '.join(paths))
        if kind == '通常セーブ' and args.slot == 'both':
            missing=[n for n in (1, 2) if n not in [x[0] for x in tables]]
            if missing: print('警告: 成績未確認のスロット '+','.join(map(str,missing))+' は出力していません（未使用・保存前・非対応形式の可能性）。',file=sys.stderr)
        for slot,start in tables:print(f'  slot={slot} table={start:#x}')
    else:gui()

if __name__=='__main__':
    try:main()
    except Exception:
        traceback.print_exc()
        if sys.stdin.isatty():input('Enterキーで終了...')
        sys.exit(1)
