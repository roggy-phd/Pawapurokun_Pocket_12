#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""
PowerPoke 12 (VPTJ) — Third Pitch Patcher v31 (final): batter-read bug fixes + 4th and later pitches (extra lists).

Extra pitches (4th+):
  Each set (byte92 upper nibble 1-15) holds up to 50 patch entries (the six row-1 cells included), freely distributed
  over the categories: 15 sets x 56 bytes = 6 per-category counts + 50 entries in category order (Lv<<5|type); the
  1st entry of a category is its row-1 cell (old third pitch) when that cell is set.  The same pitch type
  may appear more than once with different Lv; the same type AND Lv twice in a category is rejected.
  The original pitch (type 15) cannot be an extra.
  Rule B (v28-v29 compatibility): the 1st pitch of each category in a set (row 1 of the window = the old third pitch)
  is always usable, even if the pitcher already has it.  The 2nd and later pitches are skipped only when they are an
  exact duplicate (same type AND Lv) of the pitcher's 1st or 2nd slot.  Both slots of the category must be filled.
  Human:  each press of the same direction: 1st -> 2nd -> extra 1 -> extra 2 -> ... -> 1st.
  CPU:    after the category is chosen, 1st/2nd/extras are drawn by Lv weight (extra i with Li/(L1+L2+sum Lx)).
          Action Baseball: drawn once per pitch (before the fix it was drawn at the strategy pick 0x021723F4 and again
          at the decision end 0x02172B64; the second draw is now skipped).
  個人データ: pitch pages 1-6, 7-12 (if >6), then the extras, 6 per page; page digits 1-7 (row 0x17 is the last
  visible row), later pages stay reachable with L/R.
  Mini card (Y): per category the highest Lv among the usable extras, in fixed columns (slider, curve, fork, sinker,
  shoot, straight; blank = no usable extra).
  Auto-pennant read (default ON with the read fix; --no-read-sep): an extra is a separate pitch for the batter.
    Identity (--read-lv / --read-type; GUI checkbox; default: max edition = Lv, normal edition = type):
      type: an extra of the same TYPE as a slot pitch is read as that slot (code c / c+7); other extras use 0x20|ID
      Lv  : only the same type AND Lv is the same pitch; other extras use (Lv<<5)|ID (always >= 0x20)
    Straight-family extras are separate from the straight wait by default (--straight-together: read as the
    straight).  Replaces the v29 read split.  Action Baseball keeps slot codes.
  Editions: same program; EDITION="normal" (sets as v28-v29) or "max" (set F: every slider/curve/fork/shoot/straight
  type at Lv7, plain straight included; no sinker).
  Config JSON: {"F": {"スライダー系": [["スライダー",7],["Hスライダー",6]], ...}}; the v30 form ["スライダー",7] still loads.
Python 3.8+, standard library only (tkinter for the window; CLI works without it).

Rule (human pitching only):
  set = (pitcher record +0x1A) >> 4        # = password byte92 upper nibble (patch flags 1-4), 0 = none
  For category c (0 slider,1 curve,2 fork,3 sinker,4 shoot,5 straight):
    1st press -> 1st slot, 2nd press -> 2nd slot, 3rd press -> TABLE[set][c] (if defined), 4th -> 1st slot ...
  The 1st slot is temporarily overwritten and restored on the next change / next pitch.
  Requires both slots of that category to be filled.

Patched: overlay 3 only (build from the CLEAN ROM).
  0x020EBF38  push {r4-r8,lr} -> b  0x02147EC0   (per-frame restore check)
  0x020EC1E0  strb r7,[r1,#1] -> bl 0x02147EC4   (selection interceptor)
  v31: 0x02147EC0  +0 b stub1, +4 b stub2, code, state (8: active, orig byte, cat, extra index, slot addr) |
       extra table (15 x 27) | "PKP4"

CPU third pitches (option, default ON; --no-cpu): CPU pitchers also use third pitches,
  in played games and in the auto-pennant (オーペナ) simulated games.
  Also patches overlay 10:
  0x02172B64  ldr r1,[r5]    -> bl 0x02192200   (end of each CPU pitch decision, CPU AI 0x02172910)
  0x021723F4  strb r0,[r1]   -> bl 0x02192370   (end of the CPU strategy pick 0x02172308; the auto-pennant
              simulation calls this directly from ov15 0x021A6AA4 and never goes through 0x02172910)
  0x02192200  CPU stub (0x1E8 incl. diag, entry, own state and own 90-byte set table) written over dead
              profiler name strings; no longer depends on overlay 3 (not loaded during the pennant)
Removed in v25: the v22 "batter read" / history-match exclusion (it penalised third pitches).
              (0x021921C4-0x02192E12, referenced only by no-op 0x0201CA48/0x0201CA4C calls)
  Per decision: restore any previous swap; if the chosen code is category c (1st or 2nd) and the
  pitcher's set defines a third pitch for c and both slots are filled, pick the third with
  probability L3/(L1+L2+L3) using the game's rand (0x020591B8); else keep the CPU's choice.
  Diag @0x02192368: u16 eligible decisions, u16 third picks, u8 last third byte, u8 last category (v28-v30).
  v31: the D1 body jumps to OV10X; its diag is at OV10X_DIAG: u16 eligible, u16 extra picks, u8 last extra byte,
  u8 last category, u8 ID of the extra now in the slot (used by the separate read).

個人データ pitch pages (option, default ON; --no-pages): on the pitcher page L/R now cycles
  pitches 1-6 -> pitches 7-12 (if >6) -> this pitcher's usable third pitches (if any) -> batter page.
  Hooks 0x02055C98/9C (L/R state change), 0x02056990 / 0x020569FC (skip rows), 0x02056A58 (draw thirds).
  Page indicator: existing pages drawn as digits 1-3 in column 0x1E (cream strip right of the pitch box) from row 0x0B; current page uses
  the white-on-black digit set (stamp 0x7F+n), others the brown set (0x8A+n). Nothing is drawn for 1-page pitchers.
Ability-list scroll (option, default ON; --no-scroll): the 個人データ special-ability grid
  (8x5 icons, shared ARM9 card module) scrolls one row when pressing Down on the last row / Up on
  the first row. ARM9 is decompressed, patched and recompressed; the code lives in free ITCM
  (0x01FFAC00-), loaded by extending the ITCM autoload block (0x2C00 -> 0x2FC0).
  0x020574E8 builder -> b ITCM (full list up to 160 abilities, window copied to 0x020D0D70)
  0x020573E4/E8 (Up) and 0x02057404/08 (Down) -> bl ITCM hooks
  Module params list_start/list_end/compressed_end, header ARM9 size, secure-area CRC (0x6C,
  updated affinely: only plaintext bytes 0x4FB0-0x4FC7 change) and header CRC are updated.
  Requires melonDS direct boot (default) or a loader that accepts a decrypted secure area.
DSi / TWiLight Menu++ / nds-bootstrap (v26e): nds-bootstrap applies the anti-piracy fix apFix/VPTJ-757E.ips
  (2 bytes in overlay 30) only when TID+header CRC match. v26d changed the header CRC whenever the ARM9 was
  rebuilt, so the AP fix was skipped and saves were silently discarded. v26e keeps the header CRC at the
  clean value 0x757E via two reserved header bytes (0x016-0x017). Overlay 30 is never modified.
Pennant team-swap bug fix (default ON since v27; --no-pennant-fix; overlays 5 and 10):
  Saving a pennant runs ov5 0x020EDAA0 for the six league teams. For an arrange team (code 0xFn)
  it loads arrange file n into pennant slot i and then REWRITES the code to 0xF0+i (0x020EDB10).
  On the next save the builder runs again, now reading "file i" for slot i, so every arrange team
  whose file number differs from its slot is replaced (the user's team, slot 0, becomes arrange
  file 1: the well-known swap). Fix: 0x020EDAD4 "tst r3,#0xf0" -> bl helper (ov10 0x021923F0) that
  also skips teams whose code is already 0xF0+i, i.e. already converted by an earlier save.
Password-registration ability merge (v26 option; default all = every merge store disabled; --merge off|upgrade|all; overlay 17):
  When a password/QR player is registered, ov17 0x021A09A4 converts the decoded data and calls
  0x021A11C4 (pitcher abilities) and 0x021A0D00 (batter abilities, from 0x021A0558). Each function
  keeps only one ability of every tier/contradiction group (e.g. ノビ◎ clears ノビ○/△, ローボール clears
  ハイボール). The option replaces the write-back stores with NOPs (mov r0,r0):
    upgrade : only the stores executed because a ◎ is present (◎ and ○ can coexist)   10 stores
    all     : every group store (also ○/△, ハイ/ロー, 勝ち運/負け運, 重い/軽い, ...)       35 stores
  The version-dependent clears at the end of both functions (and the removal of pitcher abilities from
  fielders, incl. the byte92 third-pitch nibble) are NOT touched.
Mini card Y toggle (option, default ON; --no-card; team arrange / order setting / in-game quick view, overlay 10):
  0x02158478 / 0x02158680 (card fill) -> b ITCM : remember byte92 set per card
              (v23: the pitcher-record pointer is range-checked; 総合守備 fills cards with a NULL record,
               which made v22 read address 0x1A and stop with a data abort)
  0x02159010 (pitching-form label stamp) -> bl ITCM : draw usable third-pitch levels there instead
  0x02159BA8 (end of per-frame card updater) -> bl ITCM : Y toggles 'third-pitch mode' (third Lv instead of form; face/name are NOT hidden since v18)
Plain straight shown in the pitch lists (v28; part of pages / card):
  ARM9 0x020569F8 beq (skip straight) -> NOP (pages); ov10 0x021590E4/0x0215920C/0x02159480 cmp r7,#5 -> #6 (card).
Upward original-pitch break (v28; default ON; --no-pop-unlock; overlay 10):
  ov10 0x02169E40 movlt r0,#0 -> NOP in the vertical-break function 0x02169D8C (Action Baseball pitch flight and the
  CPU batter's break prediction; the auto-pennant judge never calls it).
Auto-pennant batter read (v29; overlays 10 and 15; see the comments above patch_read_split / patch_read_code_fix):
  read split (default ON together with CPU third pitches; --no-read-split) makes a CPU third pitch count as read only
  with probability L1/(L1+L3); the read fix (v30, default ON; --no-read-fix) fixes two retail bugs: the read history
  stores the pitch-type ID instead of the slot code (auto-pennant and Action Baseball), and the auto-pennant writes the
  current pitch into the history before the batter guesses (sign stealing).  Action Baseball needs no change: its CPU batter fixes the guess and the predicted break
  at the start of each pitch (UcAtkInit), before a third pitch is selected.

The ITCM code block (ARM9 autoload extension) is added whenever scroll, pages or card is ON;
only the hooks of the enabled options are installed.
Usage:
  python PowerPoke12_ThirdPitch_v31.py                      -> window (Sub-position ○ fix OFF by default)
  python PowerPoke12_ThirdPitch_v31.py IN.nds OUT.nds [--config sets.json | --edition normal|max] [--no-read-sep] [--straight-together] [--no-cpu] [--no-scroll] [--no-pages] [--no-card] [--merge off|upgrade|all] [--subpos-fix] [--no-pop-unlock] [--no-pennant-fix] [--no-read-split] [--no-read-fix]
  (--cpu / --scroll from older versions are still accepted and ignored: those options are ON by default.)
"""
import argparse, hashlib, json, struct, sys
from pathlib import Path
BASE_SHA1="4327f56f23729a59d44bd170e0ed53a2bb4667dd"
OV_ID=3; OV_RAM=0x020D87E0; OV_SIZE=0x6F200; OV_BSS=0x4E0
EXT=0x02147EC0; EXT_LIMIT=0x02149D00
HOOK1=0x020EBF38; HOOK1_ORIG=bytes.fromhex("f0412de9")
HOOK2=0x020EC1E0; HOOK2_ORIG=bytes.fromhex("0170c1e5")
STUB1=0x02147EC0; STUB2=0x02147EC4   # v31: jump table at the start of OV3X_CODE
# --- Stage D1 (CPU pitching) ---
OV10_ID=10; OV10_RAM=0x02149D00; OV10_SIZE=0x49800
D1_HOOK=0x02172B64; D1_HOOK_ORIG=bytes.fromhex("001095e5")
D1_STUB=0x02192200; D1_DEAD=(0x021921C4,0x02192E12); D1_DIAG=0x02192368; OV10X_DIAG=0x02192948
D1_HOOK2=0x021723F4; D1_HOOK2_ORIG=bytes.fromhex("0000c1e5")   # end of CPU strategy pick 0x02172308 (also used by auto-pennant sim)
D1_ENTRY2=0x02192370; D1_T3_OFF=0x18C
# own copy of the third-pitch table inside the ov10 blob
D1_DEAD_SHA1="7a17e6c347e07f7269c44960d888b8b8660fa1d7"
# --- ability-list scroll (ARM9 + ITCM) ---
A9_RAM=0x02004000; A9_STATIC_END=0x020B5180; A9_ITCM_SZ=0x2C00; A9_DTCM_SZ=0x120; A9_LIST=0x020B7EA0
SC_ITCM=0x01FFAC00
SC_BLOB=bytes.fromhex("090000ea6d0000ea7b0000ead50000eaee0000eafa0000ea050100ea560100ea5d0100ea780100eab30100eaf04f2de90040a0e10150a0e10060e0e30070e0e30080e0e30090e0e300a0e0e3000052e30300001af4779fe5f4879fe5f4979fe5f4a79fe508b59fe50030a0e3280094e5060000e08010a0e3180000eb2c0094e5070000e0a010a0e3140000eb300094e5080000e0c010a0e3100000eb1700d4e5010050e30700001a140095e5090000e0e010a0e3090000eb180095e50a0000e0011ca0e3050000eba0378fe50000a0e39c078fe59c078fe50c0000ebf08fbde8000050e31eff2f01010010e30400000aa00053e30200002a8320a0e1b2108be1013083e2a000a0e1011081e2f3ffffea70402de944479fe554079fe58001a0e148179fe548249fe50030a0e3035080e0010055e10060a0238560a031b6609231036184e7013083e2280053e3f6ffffba7080bde8f04f2de9ecffffeb00479fe500a79fe5f4969fe5fc869fe50070a0e3075199e7076198e70500a0e10210d4e50020a0e3c62c01eb2410a0e396a121e00c30d1e50230c3e3000055e30100000a010070e3023083130c30c1e5be00c1e1017087e2280057e3ecffffbaf08fbde80f502de9340094e5000050e30600001a9c169fe5000051e30300000a011041e28c168fe5daffffeb020000ea010050e20500a043340084e50f90bde80f502de9340094e5040050e30900001a60169fe5052081e28221a0e150369fe5030052e10300002a011081e244168fe5c8ffffeb0b0000ea010080e2050050e30000a0c3340084e5000050e30500001a20169fe5000051e30200000a0010a0e310168fe5bbffffeb0f90bde8f0412de9f0859fe5048098e50040a0e30050a0e30060a0e3040088e2850080e00600d0e7a002b0e10600000a0800a0e10510a0e10620a0e10d7201eb98159fe5010050e101408412016086e2020056e3f0ffffba015085e2060055e3ecffffba0400a0e1f081bde830402de988459fe5044094e5000054e31100000a1a50d4e52552b0e10e00000a041084e2801081e00020d1e5a222b0e10900000a0120d1e5a222b0e10600000a015045e20620a0e3950203e0003083e050229fe50300d2e73080bde80000a0e33080bde810402de90040a0e30400a0e1e2ffffeb000050e30400001a014084e2060054e3f8ffffba0000a0e31080bde80100a0e31080bde80f502de904059fe5000050e30300001abaffffeb060050e30100a0c30b0000cae8049fe5020050e3030000aae6ffffeb000050e30200a0130400001a0000a0e3c8048fe50200a0e3140084e50f90bde8b8048fe50100a0e3b8048fe50000a0e3140084e50f90bde801402de9a4049fe5000050e394048f050000a0e394048fe588049fe5010050e30600a0036300a0c37c048fe50040a0e30180bde804002de56c049fe5000050e30400000a010040e25c048fe504009de420e49fe51eff2fe104009de4050054e31eff2fe1f84f2de908d04de234049fe5020050e31e00001a50b09de50090a0e3050054e31a0000ca0900a0e19bffffeb0060b0e11300000a1f0006e2d8139fe5091191e78000a0e1b02091e10b2082e000a08de50700a0e10210a0e31330a0e362feffeba622a0e19c2082e200a08de50700a0e10210a0e31c30a0e35bfeffeb02a08ae2014084e2019089e2060059e3e2ffffba98039fe5040090e5000050e31300000a63ffffeb060050e30150a0c30050a0d392ffffeb0060a0e1060095e10b00000a0b80a0e30190a0e30000a0e30b0000eb000055e30100000a0100a0e3070000eb000056e30100000a0200a0e3030000eb08d08de2f84fbde844d08de21eff2fe110402de908d04de234139fe5010050e17f20a0038a20a013092082e000808de50700a0e10210a0e31e30a0e32efeffeb028088e2019089e208d08de21080bde8ecb4ff018cb4ff01a0b084e50f502de90400a0e10610a0e10a0000eb0f50bde898c29fe51cff2fe1a0e081e50f502de90100a0e10310a0e1020000eb0f50bde87cc29fe51cff2fe178229fe5002092e5042082e2023040e0000053e30030a0030200000aa40053e31eff2f110130a0e30020a0e3020451e30300003a090551e30100002a1a20d1e52222a0e138029fe50320c0e71eff2fe1f84f2de914829fe5000058e32900000a010057e32700008a14829fe50780d8e7000058e32300000a0170a0e1018048e20690a0e398090ae0d4901fe50aa089e00090a0e300b0a0e31c0000eb000056e301b08b12019089e2060059e3f9ffffba00005be31300000a08d04de20090a0e300b0a0e3110000eb000056e30800000aa662a0e1b42086e20200a0e300008de50500a0e10710a0e101308be2dcfdffeb01b08be2019089e2060059e3f0ffffba08d08de2f88fbde8f84fbde8d4fdffea946084e2896086e00080d6e5a882b0e10400000a0180d6e5a882b0e10100000a0960dae71eff2fe10060a0e31eff2fe1ff402de918019fe5b000d0e11c119fe50070a0e318219fe5020b10e30020a0030500000a000052e30300001a0120a0e3011021e2f4108fe50170a0e3f0208fe5000057e31000000a0060a0e3ec309fe5003093e5043083e2a440a0e3963423e0084093e5010054e30400001a004093e5000054e30100000a0600a0e1cf7505eb016086e2020056e3efffffba9c109fe5000051e30100001a000057e31d00000a0020a0e394309fe5003093e5043083e2a440a0e3923423e0084093e5010054e31100001a004093e5000054e30e00000a68409fe5004094e5004094e548509fe540609fe5946526e0054082e22450a0e3946526e00c40d6e5000051e30240c403024084030240c4130c40c6e5012082e2020052e3e2ffffbaff40bde81cd08de21eff2fe16cbf0b0218380c02e010000000000000000000007c841502848615020035190284b4ff013c010000406a050220d40a02ff7fffffeffff9013fffffffffff0ff8700d0d02740c0d02f8480c02d00c0d020000000000000000000000000000000000000000000000005053434c00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000")
# v18 mini-card fix:
# v16 wrote to a sprite/OAM attribute at ITCM blob +0x7F0 (v23: +SC_FACE_NOP) while Y mode was active.
# Real melonDS testing showed that this hid the PLAYER NAME, not the face.
# Disable only that write.  Third-pitch level drawing / Y toggle logic remains unchanged.
# ARM NOP used here: MOV r4,r4 (04 40 A0 E1).
SC_FACE_NOP=0x804   # v23: offset moved (+0x14) because fill_common got a pointer check
assert SC_BLOB[SC_FACE_NOP:SC_FACE_NOP+4] == bytes.fromhex("0c40c6e5")
SC_BLOB = SC_BLOB[:SC_FACE_NOP] + bytes.fromhex("0440a0e1") + SC_BLOB[SC_FACE_NOP+4:]

SC_T3_OFF=0x88C   # third-pitch table copy inside the ITCM blob (for the 個人データ pitch pages)
SC_HOOKS=[(0x020574E8,"f84f2de9"),(0x020573E4,"340094e5"),(0x020573E8,"010050e2"),(0x02057404,"34009415"),(0x02057408,"01008012"),
          (0x02055C98,"140094e5"),(0x02055C9C,"010080e2"),(0x02056990,"0040a0e3"),(0x020569FC,"050054e3"),(0x02056A58,"44d08de2")]
D1_CODE=bytes.fromhex("f8432de90090a0e344519fe50030d5e5000053e30500000a043095e50120d5e50020c3e50030a0e30030c5e50190a0e320719fe5007097e5000057e33800000a0100d7e50c0050e33500008a060050e33300000a0040a0e1070054e307404422f4209fe5002092e5000052e32c00000a082092e5000052e32900000a1a30d2e52332b0e12600000a013043e20600a0e3930001e0041081e0c0009fe50180d0e7000058e31e00000a046082e2846086e00100d6e5a002b0e11900000a0010d6e5a10280e0a80280e098108fe2b020d1e1012082e2b020c1e1010040e2b51bfbeba80250e10e00002a0000d6e50100c5e5046085e50080c6e50240c5e50100a0e30000c5e50140c7e558108fe2b220d1e1012082e2b220c1e10480c1e50540c1e50190a0e3000059e30600000a24709fe5007097e5000057e30200000a0100d7e5d85dffeb0000c7e5f843bde8001095e51eff2fe184231902440e0d020c0f0d028c2319024c0e0d0200000000000000000000c1e520402de91c501fe59fffffeb2080bde800000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000")
CODE=bytes.fromhex("0f502de918219fe50030d2e5000053e30a00000a00019fe5000090e50100d0e50210d2e5010050e10400000a040092e50110d2e50010c0e50030a0e30030c2e50f50bde8f0412de90b90feea7e502de90120d1e5c8609fe50030d6e5000053e30900000a043096e50150d6e50050c3e50030a0e30030c6e50240d6e5075084e2050057e10470a0011f0000ea050057e31d00008a075087e2050052e11a00001a78309fe5003093e5000053e31600000a083093e5000053e31300000a1a40d3e52442b0e11000000a014044e20650a0e394050ce007c08ce048509fe50c50d5e7000055e30800000a043083e2873083e00040d3e50140c6e5043086e50050c3e50270c6e50140a0e30040c6e50170c1e50700a0e17e50bde81eff2fe1440e0d020c0f0d02ec7f1402f47f1402")
# --- v31: 4th and later pitches (machine code assembled from pp12-autosim tools/asm_v31.py) ---
XT_HDR=6; XT_ENT=50; XT_ROW=XT_HDR+XT_ENT; XT_LEN=15*XT_ROW   # per set: counts[6] + 50 entries (free allocation)
OV3X_CODE=bytes.fromhex("000000ea120000ea0f502de930219fe50030d2e5000053e30a00000a18019fe5000090e50100d0e50210d2e5010050e10400000a040092e50110d2e50010c0e50030a0e30030c2e50f50bde8f0412de90990feea7e502de90120d1e5e0609fe50030d6e5000053e30c00000a043096e50150d6e50050c3e50030a0e30030c6e50240d6e5075084e2050057e12600001a0470a0e10320d6e5012082e2060000ea050057e32000008a075087e2050052e11d00001a0740a0e10020a0e37c309fe5003093e5000053e31700000a085093e5000055e31400000a04102de5040085e20410a0e11a30d5e52332a0e1170000eb0120a0e104109de4000050e30a00000a043085e2843083e00050d3e50150c6e5043086e50000c3e50240c6e50320c6e50150a0e30050c6e50470a0e10170c1e50700a0e17e50bde81eff2fe1440e0d020c0f0d02088014020000000000000000000053e32800000a0f0053e32600008a013043e238c0a0e39c0303e090c09fe503308ce0f0402de9814080e00050d4e50160d4e5a5c2b0e11900000aa6c2b0e11700000a0640a0e30070a0e3010057e10300002a07c0d3e70c4084e0017087e2f9ffffea0170d3e7044083e0070052e10b00002a0200d4e7000050e30600000a000052e30200000a050050e1060050110100000a0210a0e1f080bde8012082e2f1ffffea0000a0e3f080bde80000a0e31eff2fe1c8801402")   # ov3 0x02147EC0; the extra table follows the code
OV10X=0x02192600                               # ov10 dead profiler-string area, after HS_STATE; 0x02192200 jumps to +0
OV10X_FLAGS=16                                 # +16 u8 straight-together, +17 u8 read identity (0 type, 1 type+Lv), +18 runtime
OV10X_ENTRY2=20                                # ENTRY2 (0x021723F4 path) enters here; 0x02192200 (0x02172B64 path) enters at +0
D1_ENTRY2_BL=0x0219237C                        # bl 0x02192200 inside ENTRY2 -> bl OV10X+OV10X_ENTRY2
OV10X_CODE=bytes.fromhex("0a0000eab90000eabd0000eac00000ea00000000ffffffea03002de914004fe20110a0e30210c0e50300bde80a0000ea03002de92c004fe20210d0e5000051e30400000a0010a0e30210c0e50300bde8001095e51eff2fe10300bde8f8432de908d04de20090a0e3c8529fe50030d5e5000053e30500000a043095e50120d5e50020c3e50030a0e30030c5e50190a0e3a4729fe5007097e5000057e35400000a0100d7e50c0050e35100008a060050e34f00000a0040a0e1070054e30740442278629fe5006096e5000056e34800000a086096e5000056e34500000a0080a0e300808de5040086e20410a0e10820a0e11a30d6e52332a0e1940000eb000050e30400000a00209de5a02282e000208de5018081e2f2ffffea00209de5000052e33300000a871f8fe2b030d1e1013083e2b030c1e1041086e2841081e00000d1e50130d1e5a002a0e1a30280e0020080e0010040e2971afbeb00209de5020050e12300002a04008de50080a0e3040086e20410a0e10820a0e11a30d6e52332a0e1720000eb000050e31900000a04209de5a032a0e1030052e10300003a032042e004208de5018081e2efffffea043086e2843083e00020d3e50120c5e5043085e50000c3e50240c5e50310c5e50120a0e30020c5e50140c7e55a1f8fe2b220d1e1012082e2b220c1e10400c1e50540c1e50190a0e3000059e30a00000a38719fe5007097e5000057e30600000a0100d7e5a45cffeb0000c7e50010d5e5000051e3121e8f120600c11508d08de2f843bde8001095e51eff2fe11f402de9f8209fe5002092e50100d2e5e8109fe50030d1e5000053e32300000a0230d1e5000053e12000001adc108fe20610d1e500c0d2e501005ce11b00001a274e4fe20140d4e5000054e31f40a003ff40a013a4109fe504e091e500e0dee50110d1e50e1021e0040011e10f00000a88109fe5041091e50110d1e50e1021e0040011e1070080020800000a050053e30200001ac4125fe5000051e30300001a1f0054e320008c03e0000e120c00801100c0a0e11f80bde804e02de5cfffffeb04e09de400005ce11eff2fe104e02de5caffffeb0c10a0e104f09de410402de9dd56ffebc5ffffeb1c009fe5000090e5040090e5bd0f80e202c0c0e51080bde884231902440e0d020c0f0d02500e0d020000000000000000000053e32800000a0f0053e32600008a013043e238c0a0e39c0303e090c09fe503308ce0f0402de9814080e00050d4e50160d4e5a5c2b0e11900000aa6c2b0e11700000a0640a0e30070a0e3010057e10300002a07c0d3e70c4084e0017087e2f9ffffea0170d3e7044083e0070052e10b00002a0200d4e7000050e30600000a000052e30200000a050050e1060050110100000a0210a0e1f080bde8012082e2f1ffffea0000a0e3f080bde80000a0e31eff2fe1082a1902")  # +0 d1x, +4 rs_sep, +8 rn_r1, +12 hc_sep; extra table after the code
SCX=0x01FFAC00+0xA40                           # ITCM, right after SC_BLOB
SCX_CODE=bytes.fromhex("010000ea3c0000eaa00000ea6f502de9bc629fe5005096e5015085e2010055e30300001afffdffeb060050e3040000ca0250a0e3260000eb021045e2000051e10600002a005086e50100a0e384129fe5000081e50000a0e3140084e56f90bde80000a0e3000086e50200a0e3140084e56f90bde8f0412de95c629fe5006096e50070a0e3000056e30f00000a0040a0e30080a0e3040086e20410a0e10820a0e11a30d6e52332a0e1900000eb000050e30200000a017087e2018081e2f4ffffea014084e2060054e3f0ffffba0700a0e1f081bde802402de9e5ffffeb0010a0e3000050e3020000da060040e2011081e2faffffea0100a0e10280bde8f84f2de910d04de2c8019fe5000090e5020050e33c0000ba58b09de5020040e2800080e08000a0e108008de50000a0e30c008de5a4619fe5006096e5000056e33100000a0090a0e30080a0e3040086e20910a0e10820a0e11a30d6e52332a0e1630000eb000050e32400000a018081e20050a0e10c109de5012081e20c208de508209de5020051e1efffff3a062082e2020051e1ecffff2a050054e3eaffffca1f0005e20f0050e338019f050900d0072c119fe5091191e78000a0e1b02091e10b2082e000a08de50700a0e10210a0e31330a0e382fcffeba522a0e19c2082e200a08de50700a0e10210a0e31c30a0e37bfcffeb02a08ae2014084e2d2ffffea019089e2060059e3ceffffbacc009fe5000090e5000050e31900000a82fdffeb060050e30150a0c30050a0d3a9ffffeb0060a0e1060095e11100000a0b80a0e30190a0e30000a0e32afeffeb000055e30100000a0100a0e326feffeb0250a0e3000056e30600000a070059e30400008a0500a0e11ffeffeb015085e2016046e2f6ffffea10d08de2f84fbde844d08de21eff2fe1af412de90060a0e30080a0e3940084e20910a0e10820a0e10a30a0e1180000eb000050e30500000ae02000e2e03006e2030052e10060a081018081e2f2ffffeaaf81bde878b4ff0180b4ff01780c0d0220d40a0228b9ff010306090203040000000053e32800000a0f0053e32600008a013043e238c0a0e39c0303e090c09fe503308ce0f0402de9814080e00050d4e50160d4e5a5c2b0e11900000aa6c2b0e11700000a0640a0e30070a0e3010057e10300002a07c0d3e70c4084e0017087e2f9ffffea0170d3e7044083e0070052e10b00002a0200d4e7000050e30600000a000052e30200000a050050e1060050110100000a0210a0e1f080bde8012082e2f1ffffea0000a0e3f080bde80000a0e31eff2fe1e8b9ff01")    # +0 page L/R, +4 page draw, +8 mini-card helper; extra table after the code
SCX_EDITS=[   # (SC_BLOB offset, original, new) -- the new code is reached through these
    (0x00C,None,"page L/R  -> SCX+0"),
    (0x018,None,"page draw -> SCX+4"),
    (0x578,bytes.fromhex("8cb4ff01"),"mini card: table literal -> extra table"),
    (0x63C,bytes.fromhex("0690a0e3"),"mini card: row size 6 -> 56"),
    (0x6CC,bytes.fromhex("946084e2"),"mini card: per-category helper -> SCX+8"),
    (0x6A4,bytes.fromhex("01308be2"),"mini card: digit position = category+1 (fixed columns; was packed)"),
]

CATS=["スライダー系","カーブ系","フォーク系","シンカー系","シュート系","ストレート系"]
PITCHES=[
 ["スライダー","Hスライダー","カットボール"],
 ["カーブ","スローカーブ","スラーブ","Dカーブ","ドロップ","ナックルカーブ"],
 ["フォーク","パーム","ナックル","Vスライダー","SFF","チェンジアップ","あばたボール","サークルチェンジ","フォッシュ"],
 ["シンカー","Hシンカー"],
 ["シュート","Hシュート","シンキングファスト"],
 ["ストレート","ムービングファスト","ツーシーム","超スローボール"],
]
PITCH_CODE_MAP=[{p:(15 if p=="オリジナル" else i) for i,p in enumerate(lst)} for lst in PITCHES]
SETS="123456789ABCDEF"
# v28a defaults:
#   Sets 1-7: basic pitches in the five breaking-ball categories at Lv1-Lv7.
#             Straight is intentionally left empty.
#   Set E:    Straight Lv7 only.
#   Set F:    Cut Ball / D Curve / Changeup / H Sinker / H Shoot, all Lv4 / Straight Lv7.
DEFAULT={
    **{
        str(lv): {cat:[PITCHES[i][0],lv] for i,cat in enumerate(CATS[:5])}
        for lv in range(1,8)
    },
    "E": {
        CATS[5]: ["ストレート",7],
    },
    "F": {
        CATS[0]: ["カットボール",4],
        CATS[1]: ["Dカーブ",4],
        CATS[2]: ["チェンジアップ",4],
        CATS[3]: ["Hシンカー",4],
        CATS[4]: ["Hシュート",4],
        CATS[5]: ["ストレート",7],
    },
}
EDITION="normal"   # "max" for the max edition (only the initial sets differ)
DEFAULT_MAX={**DEFAULT,"F":{CATS[c]:[[p,7] for p in PITCHES[c] if p!="オリジナル"] for c in (0,1,2,4,5)}}
def default_cfg(edition=None):
    return DEFAULT_MAX if (edition or EDITION)=="max" else DEFAULT
def cfg_lists(cfg):
    """{set:{cat:[(type,lv),...]}}; accepts the v30 form [name,lv] and the v31 form [[name,lv],...]."""
    out={}
    for si,s in enumerate(SETS):
        for c,cat in enumerate(CATS):
            v=cfg.get(s,{}).get(cat)
            if not v: continue
            if isinstance(v[0],str): v=[v]
            lst=[]
            for name,lv in v:
                lv=int(lv)
                if name not in PITCHES[c]: raise ValueError(f"set {s} {cat}: unknown pitch {name}")
                if not 1<=lv<=7: raise ValueError(f"set {s} {cat}: level must be 1-7")
                t=PITCH_CODE_MAP[c][name]
                if any(t==x and lv==y for x,y in lst): raise ValueError(f"set {s} {cat}: {name} Lv{lv} appears twice")
                lst.append((t,lv))
            if lst: out.setdefault(s,{})[c]=lst
    for s,cats in out.items():
        n=sum(len(v) for v in cats.values())
        if n>XT_ENT: raise ValueError(f"set {s}: at most {XT_ENT} patch entries total")
    return out
def make_xt(cfg):
    """v31 extra table: 15 sets x 56 bytes = 6 per-category counts + 50 entries in category order."""
    t=bytearray(XT_LEN)
    for s,cats in cfg_lists(cfg).items():
        base=SETS.index(s)*XT_ROW; pos=base+XT_HDR
        for c in range(6):
            lst=cats.get(c,[])
            t[base+c]=len(lst)
            for ty,lv in lst: t[pos]=(lv<<5)|ty; pos+=1
    return bytes(t)
def u32(b,o): return struct.unpack_from("<I",b,o)[0]
def arm_b(src,dst,link=False):
    d=dst-src-8
    return struct.pack("<I",(0xEB000000 if link else 0xEA000000)|((d>>2)&0xFFFFFF))
def make_table(cfg):
    """v30 third-pitch table (15 x 6) = first extra of each category (kept in the old places; v31 code uses make_xt)."""
    t=bytearray(90)
    for s,cats in cfg_lists(cfg).items():
        for c,lst in cats.items(): t[SETS.index(s)*6+c]=(lst[0][1]<<5)|lst[0][0]
    return bytes(t)
def blz_decompress(data):
    data = bytes(data)
    hdr = data[-5]; enc = u32(data, len(data) - 8) & 0xFFFFFF; extra = u32(data, len(data) - 4)
    buf = bytearray(data) + bytearray(extra)             # single buffer = real in-place behaviour
    inp = len(data) - hdr; out = len(buf); end = len(data) - enc
    while inp > end:
        inp -= 1; flags = buf[inp]
        for _ in range(8):
            if flags & 0x80:
                inp -= 2; v = buf[inp] | (buf[inp + 1] << 8)
                disp = (v & 0xFFF) + 3; ln = (v >> 12) + 3
                for _ in range(ln):
                    out -= 1; buf[out] = buf[out + disp]
            else:
                inp -= 1; out -= 1; buf[out] = buf[inp]
            if out < inp: raise ValueError("BLZ in-place overlap violated")
            flags = (flags << 1) & 0xFF
            if inp <= end: break
    return bytes(buf)

def blz_compress(raw, tries=4096, lazy=True):
    r = raw[::-1]; n = len(r)
    head = {}; prev = [-1]*n
    def insert(p):
        if p+3 <= n:
            k = r[p:p+3]; prev[p] = head.get(k,-1); head[k] = p
    def best(i):
        bl=0; bd=0
        if i+3<=n:
            c=head.get(r[i:i+3],-1); t=0
            while c>=0 and t<tries:
                d=i-c
                if d>0x1002: break
                if d>=3:
                    l=3; mx=min(18,n-i)
                    while l<mx and r[c+l]==r[i+l]: l+=1
                    if l>bl: bl,bd=l,d
                    if l==18: break
                c=prev[c]; t+=1
        return bl,bd
    toks=[]; i=0
    while i<n:
        bl,bd=best(i)
        if bl>=3 and lazy and i+1<n:
            insert(i)
            bl2,bd2=best(i+1)
            if bl2>bl+1:
                toks.append((1,bytes([r[i]]))); i+=1; continue
            # already inserted i
            v=((bl-3)<<12)|(bd-3); toks.append((bl,bytes([v>>8,v&0xff])))
            for q in range(i+1,i+bl): insert(q)
            i+=bl; continue
        if bl>=3:
            v=((bl-3)<<12)|(bd-3); toks.append((bl,bytes([v>>8,v&0xff])))
            for q in range(i,i+bl): insert(q)
            i+=bl
        else:
            toks.append((1,bytes([r[i]]))); insert(i); i+=1
    out=bytearray(); produced=0; best_gain=0; bp=None; t=0
    while t<len(toks):
        fpos=len(out); out.append(0); flags=0
        for b in range(8):
            if t>=len(toks): break
            ln,bts=toks[t]
            if ln>1: flags|=0x80>>b
            out+=bts; produced+=ln; t+=1
            g=produced-len(out)
            if g>=best_gain: best_gain=g; bp=(len(out),produced,fpos,b,flags)
        out[fpos]=flags
    olen,produced,fpos,bit,flags=bp
    comp=bytearray(out[:olen]); mask=0
    for b in range(bit+1): mask|=0x80>>b
    comp[fpos]=flags&mask
    body=bytes(comp[::-1]); prefix=raw[:len(raw)-produced]
    pad=(-(len(prefix)+len(body)))%4; hdr=8+pad; enc=len(body)+hdr
    extra=len(raw)-(len(prefix)+enc)
    return prefix+body+b'\xff'*pad+struct.pack('<II',enc|(hdr<<24),extra)

def patch_ov10_cpu(rom,table,log=print,hooks=True,xt=None,together=False,read_lv=False):
    """Stage D1: hook the end of each CPU pitch decision (overlay 10)."""
    ovt,ovsz=u32(rom,0x50),u32(rom,0x54)
    ent=next(p for p in range(ovt,ovt+ovsz,32) if u32(rom,p)==OV10_ID)
    _,ram,ramsz,bss,s0,s1,fid,info=struct.unpack_from("<8I",rom,ent)
    if (ram,ramsz)!=(OV10_RAM,OV10_SIZE): raise ValueError("overlay 10 entry not as expected")
    fat=u32(rom,0x48); n=u32(rom,0x4C)//8
    fs,fe=struct.unpack_from("<II",rom,fat+fid*8)
    nxt=min([u32(rom,fat+i*8) for i in range(n) if u32(rom,fat+i*8)>=fe]+[len(rom)])
    dec=bytearray(blz_decompress(rom[fs:fe]))
    o=lambda a:a-OV10_RAM
    if dec[o(D1_HOOK):o(D1_HOOK)+4]!=D1_HOOK_ORIG: raise ValueError("ov10 CPU hook site not pristine")
    if dec[o(D1_HOOK2):o(D1_HOOK2)+4]!=D1_HOOK2_ORIG: raise ValueError("ov10 CPU strategy hook site not pristine")
    if hashlib.sha1(dec[o(D1_DEAD[0]):o(D1_DEAD[1])]).hexdigest()!=D1_DEAD_SHA1: raise ValueError("ov10 dead-string area not as expected")
    if hooks:
        dec[o(D1_HOOK):o(D1_HOOK)+4]=arm_b(D1_HOOK,D1_STUB,True)
        dec[o(D1_HOOK2):o(D1_HOOK2)+4]=arm_b(D1_HOOK2,D1_ENTRY2,True)
    code=bytearray(D1_CODE); code[D1_T3_OFF:D1_T3_OFF+len(table)]=table
    dec[o(D1_STUB):o(D1_STUB)+len(code)]=code
    if xt is not None:   # v31: the D1 body jumps to the extra-list version
        x=bytearray(OV10X_CODE); x[OV10X_FLAGS]=1 if together else 0; x[OV10X_FLAGS+1]=1 if read_lv else 0; x+=xt
        if OV10X<HS_STATE+8 or OV10X+len(x)>D1_DEAD[1]: raise ValueError("ov10 extra code does not fit")
        dec[o(D1_STUB):o(D1_STUB)+4]=arm_b(D1_STUB,OV10X)
        dec[o(D1_ENTRY2_BL):o(D1_ENTRY2_BL)+4]=arm_b(D1_ENTRY2_BL,OV10X+OV10X_ENTRY2,True)   # one draw per decision (Action CPU)
        dec[o(OV10X):o(OV10X)+len(x)]=x
    new=bytes(dec)
    log("compressing overlay 10 ...")
    comp=blz_compress(new)
    if blz_decompress(comp)!=new: raise ValueError("ov10 recompression mismatch")
    if fs+len(comp)>nxt: raise ValueError("compressed overlay 10 exceeds allocation")
    rom[fs:nxt]=comp+b"\xFF"*(nxt-fs-len(comp))
    struct.pack_into("<I",rom,fat+fid*8+4,fs+len(comp))
    struct.pack_into("<I",rom,ent+28,(info&0xFF000000)|len(comp))
    return fid,new

# --- mini card (overlay 10; team arrange / order / in-game quick view) ---
# --- show normal straight pitches in pitch lists ---
# Retail PP12 intentionally hides the normal straight (pitch index 0)
# from the pitch displays even when it occupies a stored pitch slot.
#
# 個人データ:
#   0x020569F8  BEQ skip -> NOP
#
# Mini card:
#   Three separate category==5 checks special-case the straight category:
#     0x021590E4  existence/filter
#     0x0215920C  pitch drawing
#     0x02159480  level drawing
#   Change CMP r7,#5 -> CMP r7,#6.  Valid categories are only 0..5,
#   so category 5 follows the normal-pitch display path.

STRAIGHT_DETAIL_ADDR = 0x020569F8
STRAIGHT_DETAIL_ORIG = bytes.fromhex("1000000a")  # beq ...
STRAIGHT_DETAIL_NEW  = bytes.fromhex("0000a0e1")  # mov r0,r0 (ARM NOP)

STRAIGHT_CARD_EDITS = [
    (0x021590E4, bytes.fromhex("050057e3"), bytes.fromhex("060057e3")),  # cmp r7,#5 -> #6
    (0x0215920C, bytes.fromhex("050057e3"), bytes.fromhex("060057e3")),  # cmp r7,#5 -> #6
    (0x02159480, bytes.fromhex("050057e3"), bytes.fromhex("060057e3")),  # cmp r7,#5 -> #6
]
CARD_HOOKS=[(0x02158478,"a0b084e5"),(0x02158680,"a0e081e5"),(0x02159010,"8286faeb"),(0x02159BA8,"1cd08de2")]
def patch_ov10_card(rom,log=print):
    """Mini card: pitchers with usable third pitches show their levels instead of the pitching-form
    label (ITCM code, needs the ARM9/ITCM option)."""
    ovt,ovsz=u32(rom,0x50),u32(rom,0x54)
    ent=next(p for p in range(ovt,ovt+ovsz,32) if u32(rom,p)==OV10_ID)
    _,ram,ramsz,bss,s0,s1,fid,info=struct.unpack_from("<8I",rom,ent)
    fat=u32(rom,0x48); n=u32(rom,0x4C)//8
    fs,fe=struct.unpack_from("<II",rom,fat+fid*8)
    nxt=min([u32(rom,fat+i*8) for i in range(n) if u32(rom,fat+i*8)>=fe]+[len(rom)])
    dec=bytearray(blz_decompress(rom[fs:fe]))
    o=lambda a:a-OV10_RAM
    for a,h in CARD_HOOKS:
        if dec[o(a):o(a)+4].hex()!=h: raise ValueError(f"ov10 card hook 0x{a:08X} not pristine")
    dec[o(0x02158478):o(0x02158478)+4]=arm_b(0x02158478,SC_ITCM+28)
    dec[o(0x02158680):o(0x02158680)+4]=arm_b(0x02158680,SC_ITCM+32)
    dec[o(0x02159010):o(0x02159010)+4]=arm_b(0x02159010,SC_ITCM+36,True)
    # (face OBJ priority change removed: the face stayed on top and the name vanished)
    dec[o(0x02159BA8):o(0x02159BA8)+4]=arm_b(0x02159BA8,SC_ITCM+40,True)   # per-frame card update: Y toggles faces
    
    # Show a stored normal straight pitch on the mini card.
    # Retail code special-cases category 5 (straight) at three stages.
    # Treat it like the other categories by changing cmp r7,#5 -> cmp r7,#6.
    for a,orig,repl in STRAIGHT_CARD_EDITS:
        oo=o(a)
        if dec[oo:oo+4] != orig:
            raise ValueError(f"ov10 straight-display site 0x{a:08X} not pristine")
        dec[oo:oo+4] = repl

    new=bytes(dec)
    log("compressing overlay 10 (card) ...")
    comp=blz_compress(new)
    if blz_decompress(comp)!=new: raise ValueError("ov10 recompression mismatch")
    if fs+len(comp)>nxt: raise ValueError("compressed overlay 10 exceeds allocation")
    rom[fs:nxt]=comp+b"\xFF"*(nxt-fs-len(comp))
    struct.pack_into("<I",rom,fat+fid*8+4,fs+len(comp))
    struct.pack_into("<I",rom,ent+28,(info&0xFF000000)|len(comp))
    return fid,new

# --- v26c: optional Action Baseball Sub-position ○ bug fix (overlay 3; default OFF) ---
# 0x021155AC computes the 0..6 fielding-position mismatch level.  At 0x02115764 it applies
# Sub-position ○ (player +0x30 bit15) as -1 and Sub-position △ (bit16) as +1.
# Original code subtracts 1 even when the base level is 0 (main position), then masks to u8:
# 0 -> 255 -> final clamp (>=6) -> 6, i.e. the worst mismatch level.
# Rewrite the 7-instruction ○/△ block so ○ saturates at 0 instead of underflowing.
SUBPOS_FIX_ADDR=0x02115770
SUBPOS_FIX_ORIG=bytes.fromhex(
    "01004012 ff000012 0300001a 8117a0e1 a11fb0e1 01008012 ff000012"
)
SUBPOS_FIX_NEW=bytes.fromhex(
    "0300001a 8117a0e1 a11fb0e1 01008012 010000ea 000050e3 01004012"
)

# --- v26: password-registration ability merge (overlay 17) ---
OV17_ID=17; OV17_RAM=0x02193540; OV17_SIZE=0x33980
MERGE_NOP=bytes.fromhex("0000a0e1")   # mov r0,r0
MERGE_UPGRADE=[   # stores executed only because a ◎ ability is present
    (0x021A1348,"14008115"),   # pitcher: ノビ○/ノビ△
    (0x021A0D68,"28308115"),   # batter: チャンス○/チャンス△
    (0x021A0D6C,"30008115"),   # batter: チャンス×
    (0x021A0E08,"28308115"),   # batter: 対左投手○/対左投手△
    (0x021A0E0C,"30008115"),   # batter: 対左投手×
    (0x021A0E7C,"28008115"),   # batter: 内野安打○
    (0x021A0F44,"2c008115"),   # batter: ケガ○/ケガ△
    (0x021A0F94,"28008115"),   # batter: キャッチャー○
    (0x021A0FD0,"28008115"),   # batter: バント○
    (0x021A1020,"28008115"),   # batter: 盗塁○/盗塁△
]
MERGE_ALL=[       # every tier/contradiction group store in 0x021A11C4 and 0x021A0D00
    (0x021A11FC,"140081c5"),   # pitcher: ピンチ△
    (0x021A1230,"140081c5"),   # pitcher: 対左打者△
    (0x021A1264,"140081c5"),   # pitcher: 負け運
    (0x021A1298,"140081c5"),   # pitcher: 回復△
    (0x021A12C8,"140081c5"),   # pitcher: 一発
    (0x021A12FC,"140081c5"),   # pitcher: キレ△
    (0x021A1348,"14008115"),   # pitcher: ノビ○/ノビ△
    (0x021A135C,"14008115"),   # pitcher: ノビ△
    (0x021A1394,"140081c5"),   # pitcher: 打たれ弱い
    (0x021A13C8,"180081c5"),   # pitcher: クイック△
    (0x021A13F8,"180081c5"),   # pitcher: 軽い球
    (0x021A0D68,"28308115"),   # batter: チャンス○/チャンス△
    (0x021A0D6C,"30008115"),   # batter: チャンス×
    (0x021A0D88,"28308115"),   # batter: チャンス△
    (0x021A0D8C,"30008115"),   # batter: チャンス×
    (0x021A0DA0,"30008115"),   # batter: チャンス×
    (0x021A0E08,"28308115"),   # batter: 対左投手○/対左投手△
    (0x021A0E0C,"30008115"),   # batter: 対左投手×
    (0x021A0E28,"28308115"),   # batter: 対左投手△
    (0x021A0E2C,"30008115"),   # batter: チャンス×
    (0x021A0E40,"30008115"),   # batter: 対左投手×
    (0x021A0E7C,"28008115"),   # batter: 内野安打○
    (0x021A0EB8,"2c008115"),   # batter: チームプレイ△
    (0x021A0EF4,"2c008115"),   # batter: ハイボールヒッター
    (0x021A0F44,"2c008115"),   # batter: ケガ○/ケガ△
    (0x021A0F58,"2c008115"),   # batter: ケガ△
    (0x021A0F94,"28008115"),   # batter: キャッチャー○
    (0x021A0FD0,"28008115"),   # batter: バント○
    (0x021A1020,"28008115"),   # batter: 盗塁○/盗塁△
    (0x021A1034,"28008115"),   # batter: 盗塁△
    (0x021A1070,"28008115"),   # batter: 走塁△
    (0x021A10AC,"2c008115"),   # batter: ムード△
    (0x021A10E8,"2c008115"),   # batter: 野手ムラッ気
    (0x021A1124,"30008115"),   # batter: 送球△
    (0x021A1160,"30008115"),   # batter: サブポジ△
]
def patch_ov17_merge(rom,mode,log=print):
    """v26: NOP the ability-merge write-backs of password registration (mode 'upgrade' or 'all')."""
    sites=MERGE_UPGRADE if mode=="upgrade" else MERGE_ALL
    ovt,ovsz=u32(rom,0x50),u32(rom,0x54)
    ent=next(p for p in range(ovt,ovt+ovsz,32) if u32(rom,p)==OV17_ID)
    _,ram,ramsz,bss,s0,s1,fid,info=struct.unpack_from("<8I",rom,ent)
    if (ram,ramsz)!=(OV17_RAM,OV17_SIZE): raise ValueError("overlay 17 entry not as expected")
    fat=u32(rom,0x48); n=u32(rom,0x4C)//8
    fs,fe=struct.unpack_from("<II",rom,fat+fid*8)
    nxt=min([u32(rom,fat+i*8) for i in range(n) if u32(rom,fat+i*8)>=fe]+[len(rom)])
    dec=bytearray(blz_decompress(rom[fs:fe]))
    o=lambda a:a-OV17_RAM
    for a,h in sites:
        if dec[o(a):o(a)+4].hex()!=h: raise ValueError(f"ov17 merge site 0x{a:08X} not pristine")
        dec[o(a):o(a)+4]=MERGE_NOP
    new=bytes(dec)
    log("compressing overlay 17 ...")
    comp=blz_compress(new)
    if blz_decompress(comp)!=new: raise ValueError("ov17 recompression mismatch")
    if fs+len(comp)>nxt: raise ValueError("compressed overlay 17 exceeds allocation")
    rom[fs:nxt]=comp+b"\xFF"*(nxt-fs-len(comp))
    struct.pack_into("<I",rom,fat+fid*8+4,fs+len(comp))
    struct.pack_into("<I",rom,ent+28,(info&0xFF000000)|len(comp))
    return fid,new

# --- v26d: pennant team-swap bug fix ---
OV5_ID=5; OV5_RAM=0x020D87E0; OV5_SIZE=0x70F20
PEN_HOOK=0x020EDAD4; PEN_HOOK_ORIG=bytes.fromhex("f00013e3")      # tst r3,#0xf0 (arrange-team test in the save builder)
PEN_HELPER=0x021923F0                                              # ov10 dead-string area (after the D1 blob)
PEN_HELPER_CODE=bytes.fromhex("f00013e31eff2f01f0c080e20c0053e11eff2fe1")   # tst r3,#0xf0; bxeq lr; add ip,r0,#0xf0; cmp r3,ip; bx lr
def _ov_patch(rom,ov_id,ov_ram,ov_size,edits,log,label):
    """decompress overlay ov_id, apply [(addr,orig_bytes_or_None,new_bytes)], recompress, update FAT/table."""
    ovt,ovsz=u32(rom,0x50),u32(rom,0x54)
    ent=next(p for p in range(ovt,ovt+ovsz,32) if u32(rom,p)==ov_id)
    _,ram,ramsz,bss,s0,s1,fid,info=struct.unpack_from("<8I",rom,ent)
    if (ram,ramsz)!=(ov_ram,ov_size): raise ValueError(f"overlay {ov_id} entry not as expected")
    fat=u32(rom,0x48); n=u32(rom,0x4C)//8
    fs,fe=struct.unpack_from("<II",rom,fat+fid*8)
    nxt=min([u32(rom,fat+i*8) for i in range(n) if u32(rom,fat+i*8)>=fe]+[len(rom)])
    dec=bytearray(blz_decompress(rom[fs:fe]))
    for a,orig,new in edits:
        o=a-ov_ram
        if orig is not None and dec[o:o+len(orig)]!=orig: raise ValueError(f"{label}: 0x{a:08X} not pristine")
        dec[o:o+len(new)]=new
    new=bytes(dec)
    log(f"compressing overlay {ov_id} ({label}) ...")
    comp=blz_compress(new)
    if blz_decompress(comp)!=new: raise ValueError(f"ov{ov_id} recompression mismatch")
    if fs+len(comp)>nxt: raise ValueError(f"compressed overlay {ov_id} exceeds allocation")
    rom[fs:nxt]=comp+b"\xFF"*(nxt-fs-len(comp))
    struct.pack_into("<I",rom,fat+fid*8+4,fs+len(comp))
    struct.pack_into("<I",rom,ent+28,(info&0xFF000000)|len(comp))
    return fid,new
def patch_pennant_fix(rom,log=print):
    """v26d: pennant team-swap fix (ov10 helper + ov5 hook). Returns (ov10 result, ov5 result)."""
    r10=_ov_patch(rom,OV10_ID,OV10_RAM,OV10_SIZE,[(PEN_HELPER,None,PEN_HELPER_CODE)],log,"pennant helper")
    r5=_ov_patch(rom,OV5_ID,OV5_RAM,OV5_SIZE,[(PEN_HOOK,PEN_HOOK_ORIG,arm_b(PEN_HOOK,PEN_HELPER,True))],log,"pennant fix")
    return r10,r5

# --- v28: optional upward original-pitch break unlock (overlay 10; default ON since v28 final; --no-pop-unlock) ---
# Action Baseball trajectory calculation clamps a negative vertical coefficient to zero:
#   0x02169E3C cmp r0,#0
#   0x02169E40 movlt r0,#0
# Replacing only the MOVLT with a NOP lets sufficiently negative original-pitch vertical
# modifiers pass through and produce genuine upward break.  The original instruction is
# verified before writing so an unexpected ROM/layout fails closed.
POP_UNLOCK_ADDR=0x02169E40
POP_UNLOCK_ORIG=bytes.fromhex("0000a0b3")   # movlt r0,#0
POP_UNLOCK_NEW =bytes.fromhex("0000a0e1")   # mov r0,r0 (ARM NOP)

def patch_pop_unlock(rom,log=print):
    return _ov_patch(rom,OV10_ID,OV10_RAM,OV10_SIZE,
                     [(POP_UNLOCK_ADDR,POP_UNLOCK_ORIG,POP_UNLOCK_NEW)],
                     log,"upward original-pitch break unlock")

# --- v29: batter-read split for third pitches (auto-pennant only; default ON with CPU third pitches; --no-read-split) ---
# The auto-pennant pitch judge UaHitChk (ov15) asks the batter to guess the pitch with UcRnd and
# compares the guess with the thrown pitch code (0x021A7764 / 0x021A7790: cmp r1,r0).  A CPU third pitch
# keeps the code of the category's 1st pitch, so a guess of that code always counted as a read.
# The two CMPs become BL RS_STUB: if the codes match and the D1 state (0x02192384) says the current pitch is
# a third pitch of that category, the read only counts with probability L1/(L1+L3) (Lv of the original 1st
# pitch vs the third pitch).  If the third pitch is the same pitch type as the original 1st pitch it always
# counts (no split).  Flags are returned as the CMP would set them (Z=1 read, Z=0 no read).
# Note: the game's rand(n) (0x020591B8) returns 0..n inclusive, hence rand(L1+L3-1).
OV15_ID=15; OV15_RAM=0x02193540; OV15_SIZE=0x228E0
RS_STUB=0x02192410                       # ov10 dead profiler-string area, after the pennant helper
RS_CODE=bytes.fromhex("000051e11eff2f111f402de964209fe50030d2e5000053e31000000a0230d2e5010053e10d00001a0140d2e5043092e50030d3e5030024e01f0010e30700000aa442a0e1a30284e0000050e30300000a010040e2531bfbeb040050e10200002a1f40bde800c0b0e31eff2fe11f40bde801c0b0e31eff2fe184231902")
RS_HOOKS=[(0x021A7764,bytes.fromhex("000051e1")),(0x021A7790,bytes.fromhex("000051e1"))]   # cmp r1,r0

def patch_read_split(rom,log=print):
    """v29: returns (ov10 result, ov15 result)."""
    r10=_ov_patch(rom,OV10_ID,OV10_RAM,OV10_SIZE,[(RS_STUB,None,RS_CODE)],log,"read-split helper")
    r15=_ov_patch(rom,OV15_ID,OV15_RAM,OV15_SIZE,[(a,o,arm_b(a,RS_STUB,True)) for a,o in RS_HOOKS],log,"read split")
    return r10,r15

# --- v29: auto-pennant read-code fix (retail bug fix; v30: part of the read fix, default ON) ---
# The auto-pennant keeps the last five pitches in the batter-side history (+0x2F6..+0x2FA, reset to 5 at each
# UaInit0) and UcRnd draws 11 of its 20 outcomes from it.  The history is written by 0x02168494 with the pitch
# TYPE ID (pitch-select +0), but UaHitChk compares the guess with the slot CODE (pitch-select +1).  Only the
# basic pitch of each category in the 1st slot has ID == code, so upper pitch types and 2nd-slot pitches are
# almost never read from the history, and a few unrelated ID/code coincidences (7-12) count as reads.
# Fix: the three auto-pennant calls of 0x02168494 (ov15 UaDHenkan and two result handlers) go through HC_STUB,
# which calls the original and then overwrites the newest history entry with the slot code.  The history
# position (the current pitch is already at the head when UaHitChk runs) is left as in the retail game.
# Action Baseball (UcAtkSub2) and the displayed pitch names are not affected.
HC_STUB=0x02192490                       # ov10 dead profiler-string area, after RS_STUB
HC_CODE=bytes.fromhex("10402de9fe57ffeb1c009fe5000090e50110d0e514009fe5000090e5040090e5bd0f80e20210c0e51080bde8440e0d02500e0d02")
HC_HOOKS=[(0x021A3904,bytes.fromhex("e212ffeb")),(0x021A4704,bytes.fromhex("620fffeb")),(0x021A705C,bytes.fromhex("0c05ffeb"))]   # bl 0x02168494

# --- v30: no sign stealing in the auto-pennant (part of the read fix) ---
# UaDefMain calls UaDHenkan (which appends the pitch to the history via 0x02168494) BEFORE UaHitChk asks the batter
# to guess, so the newest history entry (4 of the 20 guess outcomes) is the pitch being thrown.  In Action Baseball the
# guess (UcAtkInit) comes first and the history is appended after the pitch arrives (ov3 0x020E4F48).
# HS_PRE (at UaDHenkan's call) runs 0x02168494 for its other effects, puts the five history bytes back and remembers the
# pitch code; HS_POST (at the no-op profiler call right after UaHitChk, 0x021A6AB4) appends it.
HS_PRE=0x21924d0; HS_POST=0x2192558; HS_STATE=0x021925C0
HS_PRE_CODE=bytes.fromhex("70402de970409fe5004094e5044094e5bd4f84e20250d4e50300d4e5005485e10400d4e5005885e10500d4e5005c85e10660d4e5e257ffeb0250c4e52504a0e10300c4e52508a0e10400c4e5250ca0e10500c4e50660c4e520009fe5000090e50110d0e518209fe50100a0e30000c2e50110c2e5044082e57080bde8500e0d02440e0d02c0251902")
HS_POST_CODE=bytes.fromhex("1f402de940209fe50000d2e5000050e30c00000a0000a0e30000c2e5043092e50500d3e50600c3e50400d3e50500c3e50300d3e50400c3e50200d3e50300c3e50100d2e50200c3e51f80bde8c0251902")
HS_PRE_HOOK=(0x021A705C,bytes.fromhex("0c05ffeb"))     # UaDHenkan: bl 0x02168494
HS_POST_HOOK=(0x021A6AB4,bytes.fromhex("e4d7f9eb"))    # UaDefMain: bl 0x0201CA4C (no-op), right after UaHitChk
ACT_HC_HOOK=(0x020E4F48,bytes.fromhex("510d02eb"))     # ov3 (Action Baseball): bl 0x02168494 after the pitch arrives

def patch_read_code_fix(rom,log=print):
    """v29/v30: returns (ov10 result, ov15 result).  The ov3 (Action Baseball) site is patched in build()."""
    r10=_ov_patch(rom,OV10_ID,OV10_RAM,OV10_SIZE,[(HC_STUB,None,HC_CODE),(HS_PRE,None,HS_PRE_CODE),(HS_POST,None,HS_POST_CODE)],log,"read-fix helpers")
    hooks=[(a,o,arm_b(a,HC_STUB,True)) for a,o in HC_HOOKS if a!=HS_PRE_HOOK[0]]
    hooks+=[(HS_PRE_HOOK[0],HS_PRE_HOOK[1],arm_b(HS_PRE_HOOK[0],HS_PRE,True)),(HS_POST_HOOK[0],HS_POST_HOOK[1],arm_b(HS_POST_HOOK[0],HS_POST,True))]
    r15=_ov_patch(rom,OV15_ID,OV15_RAM,OV15_SIZE,hooks,log,"read fix")
    return r10,r15

# --- v31: auto-pennant batter read treats extras as separate pitches (default ON; --no-read-sep) ---
# rec_num (OV10X) returns 0x20|pitch-type ID while the D1 state says the current pitch is an extra (straight family:
# the slot code instead when the straight-together flag is set), else the slot code.  Used by:
#   ov15 0x021A7764 / 0x021A7790 (UaHitChk: cmp r1,r0)  -> bl rs_sep   (replaces the v29 read split)
#   ov15 0x021A3904 / 0x021A4704 (result handlers)       -> bl hc_sep   (HC_STUB stays for Action Baseball)
#   ov10 0x02192530 (HS_PRE: ldrb r1,[r0,#1])           -> bl rn_r1    (the pitch appended after UaHitChk)
SEP_HS_SITE=(0x02192530,bytes.fromhex("0110d0e5"))
def patch_read_sep(rom,log=print):
    """v31: needs the read fix and the CPU extras.  Returns (ov10 result, ov15 result)."""
    r10=_ov_patch(rom,OV10_ID,OV10_RAM,OV10_SIZE,[(SEP_HS_SITE[0],SEP_HS_SITE[1],arm_b(SEP_HS_SITE[0],OV10X+8,True))],log,"read separate")
    hooks=[(a,o,arm_b(a,OV10X+4,True)) for a,o in RS_HOOKS]
    hooks+=[(a,arm_b(a,HC_STUB,True),arm_b(a,OV10X+12,True)) for a,_ in HC_HOOKS if a!=HS_PRE_HOOK[0]]
    r15=_ov_patch(rom,OV15_ID,OV15_RAM,OV15_SIZE,hooks,log,"read separate")
    return r10,r15

def keep_header_crc(rom,target,log=print):
    """v26e: nds-bootstrap looks up per-game fixes by TID + header CRC (apFix/VPTJ-757E.ips = anti-piracy
    fix for PowerPoke 12). When the header changes (ARM9 size / secure-area CRC), the CRC changes, the AP fix
    is not applied and in-game saves are silently lost on DSi/TWiLight. Restore the original header CRC by
    setting two reserved header bytes (0x016-0x017, zero in the clean ROM) so that CRC16(0x000-0x15D) == target."""
    if crc16(bytes(rom[:0x15E]))==target and struct.unpack_from("<H",rom,0x15E)[0]==target: return False
    if rom[0x16] or rom[0x17]: raise ValueError("header bytes 0x16/0x17 are not free")
    base=bytearray(rom[:0x15E]); c0=crc16(bytes(base))
    zero=crc16(bytes(0x15E))
    cols=[]
    for bit in range(16):
        d=bytearray(0x15E); d[0x16+bit//8]=1<<(bit%8); cols.append(crc16(bytes(d))^zero)
    want=c0^target
    for v in range(0x10000):          # 16 unknown bits: small exhaustive solve of the linear system
        acc=0; x=v; b=0
        while x:
            if x&1: acc^=cols[b]
            x>>=1; b+=1
        if acc==want:
            rom[0x16]=v&0xFF; rom[0x17]=v>>8; break
    else: raise ValueError("could not restore header CRC")
    struct.pack_into("<H",rom,0x15E,crc16(bytes(rom[:0x15E])))
    if struct.unpack_from("<H",rom,0x15E)[0]!=target: raise ValueError("header CRC restore failed")
    log(f"Header CRC kept at 0x{target:04X} (reserved bytes 0x16/0x17 = {rom[0x16]:02X} {rom[0x17]:02X})")
    return True

def crc16(data,crc=0xFFFF):
    for b in data:
        crc^=b
        for _ in range(8): crc=(crc>>1)^0xA001 if crc&1 else crc>>1
    return crc

def patch_arm9(rom,table,scroll=True,pages=True,log=print,xt=None):
    """Add the ITCM code via the autoload block; install the ARM9 hooks of the enabled options
    (scroll = ability-list scroll, pages = 個人データ pitch pages)."""
    off,size=u32(rom,0x20),u32(rom,0x2C); limit=u32(rom,0x50)
    if off!=0x4000 or u32(rom,0x28)!=A9_RAM: raise ValueError("unexpected ARM9 header")
    dec=bytearray(blz_decompress(rom[off:off+size]))
    P=0xFB0
    ls,le,ast,bs,be,ce=struct.unpack_from("<6I",dec,P)
    if (ls,le,ast,ce)!=(A9_LIST,A9_LIST+0x20,A9_STATIC_END,A9_RAM+size) or len(dec)!=A9_LIST+0x20-A9_RAM:
        raise ValueError("ARM9 module params not as expected")
    lst=list(struct.unpack_from("<8I",dec,A9_LIST-A9_RAM))
    if lst[:2]!=[0x01FF8000,A9_ITCM_SZ] or lst[4:6]!=[0x02FE0000,A9_DTCM_SZ]: raise ValueError("autoload list not as expected")
    for a,h in SC_HOOKS:
        if dec[a-A9_RAM:a-A9_RAM+4].hex()!=h: raise ValueError(f"ARM9 hook 0x{a:08X} not pristine")
    so=A9_STATIC_END-A9_RAM
    static=bytearray(dec[:so]); itcm=dec[so:so+A9_ITCM_SZ]; dtcm=dec[so+A9_ITCM_SZ:so+A9_ITCM_SZ+A9_DTCM_SZ]
    if any(itcm[0x2BEC:]): raise ValueError("ITCM block tail not empty")
    def put(a,b): static[a-A9_RAM:a-A9_RAM+4]=b
    def bc(src,dst,link=False,cond=0xE):
        d=dst-src-8; return struct.pack("<I",(cond<<28)|(0x0B000000 if link else 0x0A000000)|((d>>2)&0xFFFFFF))
    if scroll:
        put(0x020574E8,bc(0x020574E8,SC_ITCM))
        put(0x020573E4,bc(0x020573E4,SC_ITCM+4,True)); put(0x020573E8,bc(0x020573E8,0x02057418))
        put(0x02057404,bc(0x02057404,SC_ITCM+8,True,0x1)); put(0x02057408,bc(0x02057408,0x02057418))
    if pages:
        # 個人データ pitch pages: L/R on the pitcher page cycles pitches 1-6 -> 7-12 -> third-pitch set -> batter page
        put(0x02055C98,bc(0x02055C98,SC_ITCM+12,True)); put(0x02055C9C,bytes.fromhex("7080bde8"))
        put(0x02056990,bc(0x02056990,SC_ITCM+16,True)); put(0x020569FC,bc(0x020569FC,SC_ITCM+20,True))
        put(0x02056A58,bc(0x02056A58,SC_ITCM+24,True))

        # Retail PP12 hides the normal straight from the 個人データ pitch list.
        # This branch was experimentally confirmed: NOPing it displays
        # the stored straight pitch and its correct level.
        so = STRAIGHT_DETAIL_ADDR - A9_RAM
        if static[so:so+4] != STRAIGHT_DETAIL_ORIG:
            raise ValueError("ARM9 straight-display site 0x020569F8 not pristine")
        static[so:so+4] = STRAIGHT_DETAIL_NEW
    blob=bytearray(SC_BLOB); blob[SC_T3_OFF:SC_T3_OFF+len(table)]=table
    if xt is not None:   # v31: pages and mini card read the extra lists
        if len(blob)!=SCX-SC_ITCM: raise ValueError("SC_BLOB length changed")
        new_t={0x00C:arm_b(SC_ITCM+0x00C,SCX),0x018:arm_b(SC_ITCM+0x018,SCX+4),0x578:struct.pack("<I",SCX+len(SCX_CODE)),
               0x63C:bytes.fromhex("3890a0e3"),0x6CC:arm_b(SC_ITCM+0x6CC,SCX+8),
               0x6A4:bytes.fromhex("013089e2")}   # add r3,fp,#1 -> add r3,sb,#1
        for bo,orig,_ in SCX_EDITS:
            if orig is not None and blob[bo:bo+4]!=orig: raise ValueError(f"SC_BLOB +0x{bo:X} not as expected")
            blob[bo:bo+4]=new_t[bo]
        blob+=SCX_CODE+xt; blob+=bytes((-len(blob))%32)
    N=len(blob); lst[1]=A9_ITCM_SZ+N
    new=static+itcm+bytes(blob)+dtcm+struct.pack("<8I",*lst)
    struct.pack_into("<2I",new,P,A9_LIST+N,A9_LIST+N+0x20)
    log("compressing ARM9 ...")
    comp=bytearray(new[:0x4000])+blz_compress(bytes(new[0x4000:]))
    struct.pack_into("<I",comp,P+0x14,A9_RAM+len(comp)); struct.pack_into("<I",new,P+0x14,A9_RAM+len(comp))
    if blz_decompress(bytes(comp))!=bytes(new): raise ValueError("ARM9 recompression mismatch")
    if off+len(comp)>limit: raise ValueError("compressed ARM9 too large")
    old_sa=bytes(rom[0x4000:0x8000]); new_sa=bytes(comp[:0x4000])
    if old_sa[:0x800]!=new_sa[:0x800]: raise ValueError("secure area (encrypted part) would change")
    sacrc=u32(rom,0x6C)&0xFFFF
    sacrc^=crc16(bytes(a^b for a,b in zip(old_sa,new_sa)))^crc16(bytes(0x4000))
    rom[off:limit]=bytes(comp)+b"\xFF"*(limit-off-len(comp))
    struct.pack_into("<I",rom,0x2C,len(comp)); struct.pack_into("<H",rom,0x6C,sacrc)
    struct.pack_into("<H",rom,0x15E,crc16(bytes(rom[:0x15E])))
    return bytes(new)

def build(src,dst,cfg,force=False,log=print,cpu=True,scroll=True,pages=True,card=True,merge="all",subpos_fix=False,pennant_fix=True,pop_unlock=True,read_split=True,read_code_fix=True,read_sep=True,straight_together=False,read_lv=None):
    if Path(src).resolve()==Path(dst).resolve(): raise ValueError("input and output must differ")
    rom=bytearray(Path(src).read_bytes()); sha=hashlib.sha1(rom).hexdigest()
    orig_hdr_crc=struct.unpack_from("<H",rom,0x15E)[0]   # v26e: 0x757E for the clean ROM
    if rom[0:10]!=b"PAWAPOKE12" or rom[0x0C:0x10]!=b"VPTJ": raise ValueError("not PAWAPOKE12 / VPTJ")
    if sha!=BASE_SHA1 and not force: raise ValueError(f"SHA1 {sha} is not the clean ROM")
    table=make_table(cfg); xt=make_xt(cfg)
    ovt,ovsz=u32(rom,0x50),u32(rom,0x54)
    ent=next(p for p in range(ovt,ovt+ovsz,32) if u32(rom,p)==OV_ID)
    _,ram,ramsz,bss,s0,s1,fid,info=struct.unpack_from("<8I",rom,ent)
    if (ram,ramsz,bss)!=(OV_RAM,OV_SIZE,OV_BSS): raise ValueError("overlay 3 entry not as expected")
    fat=u32(rom,0x48); n=u32(rom,0x4C)//8
    fs,fe=struct.unpack_from("<II",rom,fat+fid*8)
    nxt=min([u32(rom,fat+i*8) for i in range(n) if u32(rom,fat+i*8)>=fe]+[len(rom)])
    dec=bytearray(blz_decompress(rom[fs:fe]))
    o=lambda a:a-OV_RAM
    if dec[o(HOOK1):o(HOOK1)+4]!=HOOK1_ORIG or dec[o(HOOK2):o(HOOK2)+4]!=HOOK2_ORIG: raise ValueError("hook sites not pristine")
    if subpos_fix:
        so=o(SUBPOS_FIX_ADDR)
        if dec[so:so+len(SUBPOS_FIX_ORIG)]!=SUBPOS_FIX_ORIG: raise ValueError("sub-position fix site not pristine")
        dec[so:so+len(SUBPOS_FIX_NEW)]=SUBPOS_FIX_NEW
    dec[o(HOOK1):o(HOOK1)+4]=arm_b(HOOK1,STUB1)
    dec[o(HOOK2):o(HOOK2)+4]=arm_b(HOOK2,STUB2,True)
    if read_code_fix:   # v30: Action Baseball history stores the slot code too (helper lives in ov10)
        ao=o(ACT_HC_HOOK[0])
        if dec[ao:ao+4]!=ACT_HC_HOOK[1]: raise ValueError("Action Baseball history site not pristine")
        dec[ao:ao+4]=arm_b(ACT_HC_HOOK[0],HC_STUB,True)
    blob=OV3X_CODE+xt+b"PKP4"   # v31 (v30: CODE+bytes(8)+table+b"PKP3")
    new=bytes(dec)+bytes(OV_BSS)+blob; new+=bytes((-len(new))%32)
    if OV_RAM+len(new)>EXT_LIMIT: raise ValueError("extension too large")
    log("compressing overlay 3 ...")
    comp=blz_compress(new)
    if blz_decompress(comp)!=new: raise ValueError("recompression mismatch")
    if fs+len(comp)>nxt: raise ValueError("compressed overlay exceeds allocation")
    rom[fs:nxt]=comp+b"\xFF"*(nxt-fs-len(comp))
    struct.pack_into("<I",rom,fat+fid*8+4,fs+len(comp))
    struct.pack_into("<I",rom,ent+8,len(new)); struct.pack_into("<I",rom,ent+12,0)
    struct.pack_into("<I",rom,ent+28,(info&0xFF000000)|len(comp))
    if read_lv is None: read_lv=(EDITION=="max")
    d1=patch_ov10_cpu(rom,table,log,xt=xt,together=straight_together,read_lv=read_lv) if cpu else None
    a9=patch_arm9(rom,table,scroll,pages,log,xt=xt) if (scroll or pages or card) else None
    cardp=patch_ov10_card(rom,log) if card else None
    if merge not in ("off","upgrade","all"): raise ValueError("merge must be off/upgrade/all")
    m17=patch_ov17_merge(rom,merge,log) if merge!="off" else None
    pen=patch_pennant_fix(rom,log) if pennant_fix else None
    pop=patch_pop_unlock(rom,log) if pop_unlock else None
    if read_split and not cpu:
        log("Auto-pennant read split: skipped (it only applies to CPU third pitches, which are OFF)"); read_split=False
    if read_sep and not (cpu and read_code_fix):
        log("Auto-pennant read (extras separate): skipped (needs CPU extra pitches and the read fix)"); read_sep=False
    if read_sep and read_split: read_split=False   # v31: the separate read replaces the v29 read split
    rs=patch_read_split(rom,log) if read_split else None
    hc=patch_read_code_fix(rom,log) if read_code_fix else None
    sep=patch_read_sep(rom,log) if read_sep else None
    ov10final=(sep[0] if sep else None) or (hc[0] if hc else None) or (rs[0] if rs else None) or pop or (pen[0] if pen else None) or cardp or d1
    ov15final=(sep[1] if sep else None) or (hc[1] if hc else None) or (rs[1] if rs else None)
    keep_header_crc(rom,orig_hdr_crc,log)   # v26e
    Path(dst).write_bytes(rom)
    chk=Path(dst).read_bytes(); a,b=struct.unpack_from("<II",chk,fat+fid*8)
    if blz_decompress(chk[a:b])!=new: Path(dst).unlink(); raise ValueError("verification failed")
    if ov10final:
        a,b=struct.unpack_from("<II",chk,fat+ov10final[0]*8)
        if blz_decompress(chk[a:b])!=ov10final[1]: Path(dst).unlink(); raise ValueError("ov10 verification failed")
    if subpos_fix: log("Action Baseball Sub-position ○ bug fix: ON (0x02115770-0x02115788)")
    if pop: log("Action Baseball upward original-pitch break unlock: ON (ov10 0x02169E40 MOVLT -> NOP)")
    if ov15final:
        a,b=struct.unpack_from("<II",chk,fat+ov15final[0]*8)
        if blz_decompress(chk[a:b])!=ov15final[1]: Path(dst).unlink(); raise ValueError("ov15 verification failed")
    if sep: log(f"Auto-pennant read: extras are separate pitches by {'pitch type + Lv' if read_lv else 'pitch type'}; straight-family extras {'read as the straight' if straight_together else 'separate too'}")
    if rs: log(f"Auto-pennant read split for third pitches: ON (ov15 0x021A7764/0x021A7790 -> ov10 0x{RS_STUB:08X})")
    if hc: log(f"Batter-read fix: ON (history code: ov15 0x021A3904/0x021A4704 + ov3 0x020E4F48 -> 0x{HC_STUB:08X}; no sign stealing: 0x021A705C/0x021A6AB4)")
    if pen:
        a,b=struct.unpack_from("<II",chk,fat+pen[1][0]*8)
        if blz_decompress(chk[a:b])!=pen[1][1]: Path(dst).unlink(); raise ValueError("ov5 verification failed")
        log("Pennant team-swap bug fix: ON (ov5 0x020EDAD4 -> ov10 0x021923F0)")
    if d1 and cpu: log(f"CPU extra pitches: ON (diag @0x{OV10X_DIAG:08X})")
    if cardp: log("Mini card: Y toggles third-pitch Lv display (in place of the pitching form)")
    if m17:
        a,b=struct.unpack_from("<II",chk,fat+m17[0]*8)
        if blz_decompress(chk[a:b])!=m17[1]: Path(dst).unlink(); raise ValueError("ov17 verification failed")
        log(f"Password-registration ability merge disabled: {merge} ({len(MERGE_UPGRADE if merge=='upgrade' else MERGE_ALL)} stores)")
    if a9:
        if blz_decompress(chk[0x4000:0x4000+u32(chk,0x2C)])!=a9: Path(dst).unlink(); raise ValueError("ARM9 verification failed")
        log(f"ITCM code added (ARM9 0x{u32(chk,0x2C):X} bytes, @0x{SC_ITCM:08X}); ability scroll: {'ON' if scroll else 'OFF'}, pitch pages: {'ON' if pages else 'OFF'}")
    log(f"Created {dst}\nSHA1 {hashlib.sha1(chk).hexdigest()}")
    for s,cats in cfg_lists(cfg).items():
        row=[f"{CATS[c]}="+"/".join(f"{next(p for p,code in PITCH_CODE_MAP[c].items() if code==t)}Lv{lv}" for t,lv in lst) for c,lst in sorted(cats.items())]
        log(f"  set {int(s,16)}({s}): "+", ".join(row))

def gui():
    import tkinter as tk
    from tkinter import ttk, filedialog, messagebox
    root=tk.Tk(); root.title("パワポケ12 第三球種パッチ v31"+("max" if EDITION=="max" else ""))
    # v30: the whole window scrolls vertically
    _cv=tk.Canvas(root,highlightthickness=0); _sb=ttk.Scrollbar(root,orient="vertical",command=_cv.yview)
    _cv.configure(yscrollcommand=_sb.set); _sb.pack(side="right",fill="y"); _cv.pack(side="left",fill="both",expand=True)
    body=ttk.Frame(_cv); _cv.create_window((0,0),window=body,anchor="nw")
    body.bind("<Configure>",lambda e:_cv.configure(scrollregion=_cv.bbox("all"),width=body.winfo_reqwidth(),height=min(body.winfo_reqheight(),root.winfo_screenheight()-120)))
    root.bind_all("<MouseWheel>",lambda e:_cv.yview_scroll(int(-e.delta/120),"units"))
    # v31: the wheel must only scroll the window.  ttk Combobox/Spinbox change their value on the wheel, so scrolling
    # over the set table silently changed pitches and levels (since v30).  Remove those class bindings.
    for _cls in ("TCombobox","TSpinbox"):
        for _ev in ("<MouseWheel>","<Button-4>","<Button-5>"): root.unbind_class(_cls,_ev)
    NONE="なし"
    # v31: row 1 of each set = one pitch per category (as before); "＋" adds rows (any pitch type + Lv), "−" removes one
    ALL=[(c,p) for c in range(6) for p in PITCHES[c]]
    LABEL={(c,p):f"{p}（{CATS[c]}）" for c,p in ALL}; UNLABEL={v:k for k,v in LABEL.items()}
    first={}; extras={s:[] for s in SETS}; plus={}
    fr=ttk.Frame(body,padding=6); fr.grid(sticky="nsew")
    hdr=ttk.Frame(fr); hdr.grid(row=0,column=0,sticky="w")
    ttk.Label(hdr,text="セット\n10進数(16進数)\n(byte92上位)",width=14).grid(row=0,column=0)
    for c,cat in enumerate(CATS): ttk.Label(hdr,text=cat,width=18,anchor="center").grid(row=0,column=1+c)
    def used_count(s,c):
        n=1 if first[(s,c)][0].get()!=NONE else 0
        for ev,_,_ in extras[s]:
            if ev.get() in UNLABEL and UNLABEL[ev.get()][0]==c: n+=1
        return n
    def full(s):
        return sum(used_count(s,c) for c in range(6))>=XT_ENT
    def refresh(s):
        plus[s].state(["disabled"] if full(s) else ["!disabled"])
    def lv_sync(pitch,level,control,none_value):
        def f(*_):
            if pitch.get() in (NONE,""):
                level.set("0"); control.configure(state="disabled")
            else:
                if level.get()=="0": level.set("7")
                control.configure(state="normal",from_=1,to=7)
        pitch.trace_add("write",f); f()
    def add_extra(s,label=None,lv=7):
        sf=setframes[s][1]
        row=ttk.Frame(sf); row.pack(anchor="w",pady=1)
        ev=tk.StringVar(value=label or ""); lvv=tk.StringVar(value=str(lv) if label else "0")
        cb=ttk.Combobox(row,textvariable=ev,width=30,state="readonly")
        def post(cb=cb,ev=ev,s=s):   # only pitch types not yet used in this set/category
            cb.configure(values=[LABEL[(c,p)] for c,p in ALL])
        cb.configure(postcommand=post); post()
        ttk.Label(row,text="追加",width=6).pack(side="left",padx=(116,0)); cb.pack(side="left")
        sp=ttk.Spinbox(row,textvariable=lvv,from_=0,to=7,width=2); sp.pack(side="left")
        item=(ev,lvv,row)
        def rm(item=item,s=s):
            extras[s].remove(item); item[2].destroy(); refresh(s)
        ttk.Button(row,text="−",width=2,command=rm).pack(side="left",padx=2)
        lv_sync(ev,lvv,sp,"")
        ev.trace_add("write",lambda *_,s=s: refresh(s))
        extras[s].append(item); refresh(s)
    setframes={}
    for si,s in enumerate(SETS):
        box=ttk.Frame(fr); box.grid(row=1+si,column=0,sticky="w")
        r1=ttk.Frame(box); r1.pack(anchor="w"); sf=ttk.Frame(box); sf.pack(anchor="w")
        setframes[s]=(r1,sf)
        ttk.Label(r1,text=f"{int(s,16)}({s})",width=14,anchor="center").grid(row=0,column=0)
        for c in range(6):
            pv=tk.StringVar(value=NONE); lv=tk.StringVar(value="0")
            cell=ttk.Frame(r1); cell.grid(row=0,column=1+c,padx=1,pady=1)
            cb=ttk.Combobox(cell,textvariable=pv,width=12,state="readonly"); cb.pack(side="left")
            def post(cb=cb,pv=pv,s=s,c=c):
                cb.configure(values=[NONE]+PITCHES[c])
            cb.configure(postcommand=post)
            spin=ttk.Spinbox(cell,textvariable=lv,from_=0,to=7,width=2); spin.pack(side="left")
            lv_sync(pv,lv,spin,NONE)
            pv.trace_add("write",lambda *_,s=s: refresh(s) if s in plus else None)
            first[(s,c)]=(pv,lv)
        plus[s]=ttk.Button(r1,text="＋",width=2,command=lambda s=s:add_extra(s)); plus[s].grid(row=0,column=7,padx=4)
    def set_cfg(cfg):
        for s in SETS:
            for item in list(extras[s]): item[2].destroy()
            extras[s].clear()
            for c,cat in enumerate(CATS):
                v=cfg.get(s,{}).get(cat) or []
                if v and isinstance(v[0],str): v=[v]   # v30 form
                pv,lv=first[(s,c)]
                if v: pv.set(v[0][0]); lv.set(str(v[0][1]))
                else: pv.set(NONE); lv.set("0")
            for c,cat in enumerate(CATS):
                v=cfg.get(s,{}).get(cat) or []
                if v and isinstance(v[0],str): v=[v]
                for name,l in v[1:]: add_extra(s,LABEL[(c,name)],int(l))
            refresh(s)
    def get_cfg():
        cfg={}
        for s in SETS:
            for c in range(6):
                pv,lv=first[(s,c)]
                if pv.get()!=NONE: cfg.setdefault(s,{}).setdefault(CATS[c],[]).append([pv.get(),int(lv.get())])
            for ev,lvv,_ in extras[s]:
                if ev.get() not in UNLABEL: continue
                c,p=UNLABEL[ev.get()]
                cfg.setdefault(s,{}).setdefault(CATS[c],[]).append([p,int(lvv.get())])
        return cfg
    ttk.Label(fr,text="※ 1行目の球（従来の第三球種）は、選手がすでに同じ種類の球を持っていても使われます（v29までと同じ）。\n"
                      "※ ＋で足した球は、同じ球種でもLvが違えば別エントリとして使えます。同一球種・同一Lvの重複は不可です。\n"
                      "※ 1セット合計50エントリまで（1行目の第三球種6枠を含む）。系統ごとの配分は自由です。\n"
                      "※ どちらも、その系統の1番目・2番目の枠が両方埋まっているときだけ使われます。",
              justify="left").grid(row=1+len(SETS),column=0,sticky="w",pady=(6,0))
    set_cfg(default_cfg())
    bot=ttk.Frame(body,padding=6); bot.grid(sticky="ew")
    src=tk.StringVar(); dst=tk.StringVar()
    ttk.Label(bot,text="元ROM").grid(row=0,column=0); ttk.Entry(bot,textvariable=src,width=60).grid(row=0,column=1)
    ttk.Button(bot,text="参照",command=lambda:src.set(filedialog.askopenfilename(filetypes=[("NDS","*.nds")]) or src.get())).grid(row=0,column=2)
    ttk.Label(bot,text="出力").grid(row=1,column=0); ttk.Entry(bot,textvariable=dst,width=60).grid(row=1,column=1)
    ttk.Button(bot,text="参照",command=lambda:dst.set(filedialog.asksaveasfilename(defaultextension=".nds",filetypes=[("NDS","*.nds")]) or dst.get())).grid(row=1,column=2)
    logw=tk.Text(body,height=8,width=100); logw.grid(padx=6,pady=4)
    def log(m): logw.insert("end",m+"\n"); logw.see("end"); root.update()
    def save():
        p=filedialog.asksaveasfilename(defaultextension=".json",filetypes=[("JSON","*.json")])
        if p: Path(p).write_text(json.dumps(get_cfg(),ensure_ascii=False,indent=1),encoding="utf-8"); log("saved "+p)
    def load():
        p=filedialog.askopenfilename(filetypes=[("JSON","*.json")])
        if p: set_cfg(json.loads(Path(p).read_text(encoding="utf-8"))); log("loaded "+p)
    def run():
        try: build(src.get(),dst.get(),get_cfg(),log=log,cpu=cpu_var.get(),scroll=scroll_var.get(),pages=pages_var.get(),card=card_var.get(),merge={"しない":"off","◎と○の統合だけ止める":"upgrade","すべての統合を止める":"all"}[merge_var.get()],subpos_fix=subpos_var.get(),pennant_fix=pen_var.get(),pop_unlock=pop_var.get(),read_split=rs_var.get(),read_code_fix=hc_var.get(),read_sep=sep_var.get(),straight_together=not sepst_var.get(),read_lv=lv_var.get()); messagebox.showinfo("完了","パッチ済みROMを作成しました")
        except Exception as e: log("ERROR: "+str(e)); messagebox.showerror("エラー",str(e))
    cpu_var=tk.BooleanVar(value=True); rs_var=tk.BooleanVar(value=False)
    sep_var=tk.BooleanVar(value=True); sepst_var=tk.BooleanVar(value=True); hc_var=tk.BooleanVar(value=True)
    lv_var=tk.BooleanVar(value=(EDITION=="max"))
    cpu_fr=ttk.Frame(bot); cpu_fr.grid(row=3,column=0,columnspan=3,sticky="w")
    sep_cb=ttk.Checkbutton(cpu_fr,text="└ オーペナ: CPU投手の追加球種（第三球種以降）を、打者の読みでは別の球として扱う",variable=sep_var)
    sepst_cb=ttk.Checkbutton(cpu_fr,text="　└ ストレート系の追加球種も、ストレート待ちでは読まれない別の球にする",variable=sepst_var)
    lv_cb=ttk.Checkbutton(cpu_fr,text="　└ 同じ球種でもLvが違えば別の球として読む（ロマン。オフなら同じ球種は同じ球）",variable=lv_var)
    rs_cb=ttk.Checkbutton(cpu_fr,text="└ （別の球として扱わない場合）v29の読み分け：1種類目と読まれても Lv比 でしか当たらない",variable=rs_var)
    def _dep(*_):
        on=cpu_var.get()
        sep_cb.state(["!disabled"] if on and hc_var.get() else ["disabled"])
        sepst_cb.state(["!disabled"] if on and hc_var.get() and sep_var.get() else ["disabled"])
        lv_cb.state(["!disabled"] if on and hc_var.get() and sep_var.get() else ["disabled"])
        rs_cb.state(["!disabled"] if on and not (sep_var.get() and hc_var.get()) else ["disabled"])
    ttk.Checkbutton(cpu_fr,text="CPU投手も追加球種を使う(自動試合進行も含む)",variable=cpu_var,command=_dep).grid(row=0,column=0,sticky="w")
    sep_cb.configure(command=_dep)
    sep_cb.grid(row=1,column=0,sticky="w",padx=(20,0)); sepst_cb.grid(row=2,column=0,sticky="w",padx=(20,0)); lv_cb.grid(row=3,column=0,sticky="w",padx=(20,0)); rs_cb.grid(row=4,column=0,sticky="w",padx=(20,0))
    scroll_var=tk.BooleanVar(value=True)
    ttk.Checkbutton(bot,text="選手能力詳細画面(下): 特殊能力一覧のスクロール",variable=scroll_var).grid(row=4,column=0,columnspan=3,sticky="w")
    pages_var=tk.BooleanVar(value=True)
    ttk.Checkbutton(bot,text="選手能力詳細画面(上): LRで変化球ページ切替（続き・追加球種）",variable=pages_var).grid(row=5,column=0,columnspan=3,sticky="w")
    merge_var=tk.StringVar(value="すべての統合を止める")
    ttk.Label(bot,text="パス/QR登録時の特殊能力統合の無効化:").grid(row=7,column=0,columnspan=2,sticky="w")
    ttk.Combobox(bot,textvariable=merge_var,values=["しない","◎と○の統合だけ止める","すべての統合を止める"],state="readonly",width=24).grid(row=7,column=2,sticky="w")
    subpos_var=tk.BooleanVar(value=False)
    ttk.Checkbutton(bot,text="アクション野球: サブポジ○のメイン守備バグを修正",variable=subpos_var).grid(row=8,column=0,columnspan=3,sticky="w")
    pop_var=tk.BooleanVar(value=True)
    ttk.Checkbutton(bot,text="アクション野球: オリ変の上方向変化を解禁",variable=pop_var).grid(row=9,column=0,columnspan=3,sticky="w")
    pen_var=tk.BooleanVar(value=True)
    ttk.Checkbutton(bot,text="ペナント: セーブ後にアレンジチームの選手が入れ替わるバグを修正",variable=pen_var).grid(row=10,column=0,columnspan=3,sticky="w")
    ttk.Checkbutton(bot,text="打者の読みの修正（原作バグ修正: 投球履歴の番号の取り違え＋オーペナのサインバレ）",variable=hc_var,command=_dep).grid(row=11,column=0,columnspan=3,sticky="w")
    card_var=tk.BooleanVar(value=True)
    ttk.Checkbutton(bot,text="選手能力簡易カード: Yで投法欄⇔追加球種の最高Lv表示を切替",variable=card_var).grid(row=6,column=0,columnspan=3,sticky="w")
    _dep()
    b2=ttk.Frame(bot); b2.grid(row=2,column=0,columnspan=3,pady=4)
    ed_var=tk.StringVar(value="max版" if EDITION=="max" else "通常版")
    for t,f in (("設定を保存",save),("設定を読込",load),("パッチ作成",run)): ttk.Button(b2,text=t,command=f).pack(side="left",padx=4)
    ttk.Combobox(b2,textvariable=ed_var,values=["通常版","max版"],state="readonly",width=7).pack(side="left",padx=(16,2))
    ttk.Button(b2,text="の初期セットに戻す",command=lambda:set_cfg(default_cfg("max" if ed_var.get()=="max版" else "normal"))).pack(side="left")
    root.mainloop()

if __name__=="__main__":
    if len(sys.argv)==1: gui(); sys.exit()
    ap=argparse.ArgumentParser(); ap.add_argument("input_rom"); ap.add_argument("output_rom")
    ap.add_argument("--config"); ap.add_argument("--force",action="store_true")
    ap.add_argument("--no-cpu",action="store_true",help="CPU pitchers do not use third pitches")
    ap.add_argument("--no-scroll",action="store_true",help="no special-ability list scroll")
    ap.add_argument("--no-pages",action="store_true",help="no 個人データ pitch pages")
    ap.add_argument("--no-card",action="store_true",help="no mini-card Y toggle")
    ap.add_argument("--merge",choices=["off","upgrade","all"],default="all",help="v26: disable password-registration ability merge")
    ap.add_argument("--subpos-fix",action="store_true",help="fix the Action Baseball Sub-position ○ main-position bug (default OFF)")
    ap.add_argument("--no-pop-unlock",action="store_true",help="keep the retail clamp on upward original-pitch vertical break (unlock is ON by default)")
    ap.add_argument("--pop-unlock",action="store_true",help=argparse.SUPPRESS)   # v28 initial flag: accepted, now the default
    ap.add_argument("--no-read-split",action="store_true",help="auto-pennant: keep reading a CPU third pitch as the category's 1st pitch (by default it only counts as read with probability L1/(L1+L3))")
    ap.add_argument("--read-split",action="store_true",help=argparse.SUPPRESS)   # v29 test builds: accepted, now the default
    ap.add_argument("--no-read-sep",action="store_true",help="auto-pennant: do not treat extra pitches as separate pitches for the batter read (v29 read split is used instead)")
    ap.add_argument("--read-lv",dest="read_lv",action="store_const",const=True,default=None,help="auto-pennant: same pitch type at a different Lv is a different pitch (max edition default)")
    ap.add_argument("--read-type",dest="read_lv",action="store_const",const=False,help="auto-pennant: same pitch type is the same pitch regardless of Lv")
    ap.add_argument("--straight-together",action="store_true",help="auto-pennant: straight-family extras are read by the straight wait (default: separate)")
    ap.add_argument("--edition",choices=["normal","max"],help="initial sets when no --config is given (default: this file's EDITION)")
    ap.add_argument("--no-read-fix",action="store_true",help="keep the retail batter-read bugs (ID/code history mix-up, auto-pennant sign stealing); the fix is ON by default")
    ap.add_argument("--read-code-fix",action="store_true",help=argparse.SUPPRESS)   # v29 flag: accepted, now the default
    ap.add_argument("--no-pennant-fix",action="store_true",help="do not fix the pennant arrange-team swap (fix is ON by default)")
    ap.add_argument("--pennant-fix",action="store_true",help=argparse.SUPPRESS)   # v26d/v26e flag: accepted, now the default
    ap.add_argument("--no-read",action="store_true",help=argparse.SUPPRESS)   # v22-v24 flag: accepted, ignored (feature removed in v25)
    ap.add_argument("--cpu",action="store_true",help=argparse.SUPPRESS)      # old flags: accepted, ignored (default ON)
    ap.add_argument("--scroll",action="store_true",help=argparse.SUPPRESS)
    a=ap.parse_args()
    cfg=json.loads(Path(a.config).read_text(encoding="utf-8")) if a.config else default_cfg(a.edition)
    try: build(a.input_rom,a.output_rom,cfg,a.force,cpu=not a.no_cpu,scroll=not a.no_scroll,pages=not a.no_pages,card=not a.no_card,merge=a.merge,subpos_fix=a.subpos_fix,pennant_fix=not a.no_pennant_fix,pop_unlock=not a.no_pop_unlock,read_split=not a.no_read_split,read_code_fix=not a.no_read_fix,read_sep=not a.no_read_sep,straight_together=a.straight_together,read_lv=a.read_lv)
    except ValueError as e: raise SystemExit(str(e))
