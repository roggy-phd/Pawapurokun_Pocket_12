"""ARM execution checks. Requires unicorn; run beside the patcher."""
import importlib.util
from pathlib import Path
from unicorn import Uc, UC_ARCH_ARM, UC_MODE_ARM
from unicorn.arm_const import *
pth=Path(__file__).with_name('PowerPoke12_ThirdPitch_v31unlimited.py')
spec=importlib.util.spec_from_file_location('patch',pth)
p=importlib.util.module_from_spec(spec);spec.loader.exec_module(p)
xt=p.make_xt(p.default_cfg())
assert len(xt)==979
assert list(xt[784:790])==[21,42,63,14,21,28]
checks=0
for base,code,entry in [(p.EXT,p.OV3X_CODE,0x150),(p.OV10X,p.OV10X_CODE,0x350),(p.SCX,p.SCX_CODE,0x2f0)]:
 u=Uc(UC_ARCH_ARM,UC_MODE_ARM)
 u.mem_map(base&~0xfff,0x4000)
 u.mem_map(0x03000000,0x10000)
 u.mem_write(base,code+xt)
 rec=0x03001000; stop=0x03008000
 # Base pitches with legal Lv7, deliberately absent IDs 14 and 15.
 u.mem_write(rec,bytes([238,239])*6)
 for category in range(6):
  n=xt[784+category];start=790+sum(xt[784:784+category])
  for index in range(n+1):
   for reg,val in [(UC_ARM_REG_R0,rec),(UC_ARM_REG_R1,category),(UC_ARM_REG_R2,index),(UC_ARM_REG_R3,15),(UC_ARM_REG_SP,0x03007000),(UC_ARM_REG_LR,stop)]:u.reg_write(reg,val)
   u.emu_start(base+entry,stop,count=1000)
   assert u.reg_read(UC_ARM_REG_PC)==stop
   assert u.reg_read(UC_ARM_REG_R0)==(xt[start+index] if index<n else 0),(hex(base),category,index)
   checks+=1
 # Boundary: set E is unchanged and must not read F.
 for reg,val in [(UC_ARM_REG_R0,rec),(UC_ARM_REG_R1,5),(UC_ARM_REG_R2,1),(UC_ARM_REG_R3,14),(UC_ARM_REG_SP,0x03007000),(UC_ARM_REG_LR,stop)]:u.reg_write(reg,val)
 u.emu_start(base+entry,stop,count=1000);assert u.reg_read(UC_ARM_REG_R0)==0
 checks+=1
 # Later base duplicates are skipped; entry zero retains the original v31 rule.
 u.mem_write(rec,bytes([225,226])*6)
 for reg,val in [(UC_ARM_REG_R0,rec),(UC_ARM_REG_R1,0),(UC_ARM_REG_R2,7),(UC_ARM_REG_R3,15),(UC_ARM_REG_SP,0x03007000),(UC_ARM_REG_LR,stop)]:u.reg_write(reg,val)
 u.emu_start(base+entry,stop,count=1000)
 assert u.reg_read(UC_ARM_REG_R0)==193
 checks+=1
print(f'PASS: {checks} ARM extra-list boundary/retrieval checks across action, CPU and display helpers')
print(f'Overlay10 table ends at {p.OV10X+len(p.OV10X_CODE)+len(xt):#010x}; {p.D1_DEAD[1]-(p.OV10X+len(p.OV10X_CODE)+len(xt))} bytes remain')
