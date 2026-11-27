#!/usr/bin/env python3
"""Restricted execution of the pinned numeric substitution producer and converter.
No PPU, event binding or timing validation. The SNES 8x8 multiplication result
is modeled mathematically; the ROM's four delay NOPs execute, but IO timing is
not emulated. Unsupported instructions and PC ranges fail closed.
"""
from cpu65816_probe import ProbeError
class NumericCPU:
    allowed_ranges=((0xc32ad3,0xc32b0e),(0xc10450,0xc10586),(0xc029a1,0xc029bb))
    def __init__(self,rom):
        self.rom=rom;self.ram=bytearray(65536);self.A=self.X=self.Y=0;self.P=0x30;self.S=0x1ff;self.PC=0;self.depth=0;self.DBR=0;self.reads=[];self.trace=[]
    def mapped(self,address):
        address&=0xffffff;bank=address>>16;offset=address&0xffff
        if 0x40<=bank<=0x4f:return address+0x200000
        if 0xc0<=bank<=0xcf:return address-0xc00000
        raise ProbeError(f'Unmapped ROM address {address:06X}')
    def rb(self,a):
        a&=0xffffff
        if 0x7e0000<=a<0x7e8000:return self.ram[a&65535]
        if a<0x8000:return self.ram[a]
        p=self.mapped(a)
        if p>=len(self.rom):raise ProbeError('ROM read out of bounds')
        self.reads.append(p);return self.rom[p]
    def read(self,a,n):return sum(self.rb(a+i)<<(8*i) for i in range(n))
    def write(self,a,v,n):
        if 0x7e0000<=a<0x7e8000:a&=65535
        if not 0<=a<=0x8000-n:raise ProbeError('Non-RAM write')
        for i in range(n):self.ram[a+i]=(v>>(8*i))&255
        if a==0x4203 and n==1:
            product=self.ram[0x4202]*self.ram[0x4203]
            self.ram[0x4216:0x4218]=product.to_bytes(2,'little')
    def fetch(self,n=1):
        v=self.read(self.PC,n);self.PC=(self.PC&0xff0000)|((self.PC+n)&0xffff);return v
    @property
    def mw(self):return 1 if self.P&0x20 else 2
    @property
    def xw(self):return 1 if self.P&0x10 else 2
    def nz(self,v,n):
        self.P&=~0x82
        if not v:self.P|=2
        if v&(1<<(n*8-1)):self.P|=0x80
    def set_a(self,v):
        n=self.mw;v&=(1<<(n*8))-1;self.A=(self.A&0xff00)|v if n==1 else v;self.nz(v,n)
    def push(self,v,n):
        for i in reversed(range(n)):self.write(self.S,(v>>(8*i))&255,1);self.S=(self.S-1)&65535
    def pop(self,n):
        v=0
        for i in range(n):self.S=(self.S+1)&65535;v|=self.read(self.S,1)<<(8*i)
        return v
    def adc(self,v):
        if self.P&8:raise ProbeError('Decimal arithmetic unsupported')
        mask=(1<<(self.mw*8))-1;a=self.A&mask;r=a+v+(self.P&1);self.P=(self.P&~0x41)|(1 if r>mask else 0)
        if (~(a^v)&(a^r))&(1<<(self.mw*8-1)):self.P|=0x40
        self.set_a(r)
    def run(self,address,a=None,limit=100000):
        if a is not None:self.A=(self.A&0xff00)|(a&255) if self.mw==1 else a&65535
        self.PC=address;self.depth=0;start_stack=self.S
        for _ in range(limit):
            pc=self.PC
            if not any(start<=pc<end for start,end in self.allowed_ranges):raise ProbeError(f'Execution left allowed routines: {pc:06X}')
            self.trace.append(pc);op=self.fetch();mw=self.mw;xw=self.xw
            if op==0x08:self.push(self.P,1)
            elif op==0x28:
                self.P=self.pop(1)
                if self.P&0x10:self.X&=255;self.Y&=255
            elif op==0x8b:self.push(self.DBR,1)
            elif op==0xab:self.DBR=self.pop(1);self.nz(self.DBR,1)
            elif op==0xc2:self.P&=~self.fetch()
            elif op==0xe2:
                self.P|=self.fetch()
                if self.P&0x10:self.X&=255;self.Y&=255
            elif op==0xda:self.push(self.X,xw)
            elif op==0x5a:self.push(self.Y,xw)
            elif op==0x48:self.push(self.A,mw)
            elif op==0xfa:self.X=self.pop(xw);self.nz(self.X,xw)
            elif op==0x7a:self.Y=self.pop(xw);self.nz(self.Y,xw)
            elif op==0x68:self.set_a(self.pop(mw))
            elif op==0x29:self.set_a(self.A&self.fetch(mw))
            elif op in (0xc9,0xc5,0xe0,0xc0):
                n=xw if op in (0xe0,0xc0) else mw
                v=self.read(self.fetch(),n) if op==0xc5 else self.fetch(n)
                reg=self.X if op==0xe0 else self.Y if op==0xc0 else self.A
                r=(reg&((1<<(8*n))-1))-v;self.P=(self.P&~1)|(1 if r>=0 else 0);self.nz(r&((1<<(8*n))-1),n)
            elif op in (0xd0,0xf0,0x90,0xb0,0x80,0x30,0x10):
                d=self.fetch();d=d if d<128 else d-256
                take=(op==0x80 or op==0xd0 and not self.P&2 or op==0xf0 and self.P&2 or op==0x90 and not self.P&1 or op==0xb0 and self.P&1 or op==0x30 and self.P&0x80 or op==0x10 and not self.P&0x80)
                if take:self.PC=(self.PC&0xff0000)|((self.PC+d)&65535)
            elif op==0x18:self.P&=~1
            elif op==0x38:self.P|=1
            elif op==0xea:pass
            elif op==0x5c:self.PC=self.fetch(3)
            elif op==0x88:self.Y=(self.Y-1)&((1<<(8*xw))-1);self.nz(self.Y,xw)
            elif op==0x98:self.set_a(self.Y)
            elif op==0xbb:self.X=self.Y&((1<<(8*xw))-1);self.nz(self.X,xw)
            elif op==0xa4:self.Y=self.read(self.fetch(),xw);self.nz(self.Y,xw)
            elif op==0xcc:
                r=self.Y-self.read(self.fetch(2),xw);self.P=(self.P&~1)|(1 if r>=0 else 0);self.nz(r&((1<<(8*xw))-1),xw)
            elif op==0x0d:self.set_a(self.A|self.read(self.fetch(2),mw))
            elif op==0x8e:self.write(self.fetch(2),self.X,xw)
            elif op==0x8c:self.write(self.fetch(2),self.Y,xw)
            elif op==0x9e:self.write(self.fetch(2)+self.X,0,mw)
            elif op==0xeb:
                self.A=((self.A&255)<<8)|(self.A>>8);self.nz(self.A&255,1)
            elif op==0xc8:self.Y=(self.Y+1)&((1<<(8*xw))-1);self.nz(self.Y,xw)
            elif op==0xa2:self.X=self.fetch(xw);self.nz(self.X,xw)
            elif op==0xa0:self.Y=self.fetch(xw);self.nz(self.Y,xw)
            elif op==0xa6:self.X=self.read(self.fetch(),xw);self.nz(self.X,xw)
            elif op==0xae:self.X=self.read(self.fetch(2),xw);self.nz(self.X,xw)
            elif op==0xbc:self.Y=self.read(self.fetch(2)+self.X,xw);self.nz(self.Y,xw)
            elif op==0x64:self.write(self.fetch(),0,mw)
            elif op==0xe5:self.adc(self.read(self.fetch(),mw)^((1<<(8*mw))-1))
            elif op==0xe9:self.adc(self.fetch(mw)^((1<<(8*mw))-1))
            elif op==0x79:self.adc(self.read(self.fetch(2)+self.Y,mw))
            elif op==0x7d:self.adc(self.read(self.fetch(2)+self.X,mw))
            elif op in (0xbd,0xb9):self.set_a(self.read(self.fetch(2)+(self.X if op==0xbd else self.Y),mw))
            elif op in (0x9d,0x99):self.write(self.fetch(2)+(self.X if op==0x9d else self.Y),self.A,mw)
            elif op==0x9f:self.write(self.fetch(3)+self.X,self.A,mw)
            elif op==0x20:
                target=self.fetch(2);self.push((self.PC-1)&65535,2);self.PC=(self.PC&0xff0000)|target;self.depth+=1
            elif op==0x60:
                if not self.depth:
                    if self.S!=start_stack:raise ProbeError('Stack imbalance')
                    return self.A&((1<<(8*self.mw))-1)
                self.PC=(self.PC&0xff0000)|((self.pop(2)+1)&65535);self.depth-=1
            elif op in (0x1a,0x3a):self.set_a(self.A+(1 if op==0x1a else -1))
            elif op in (0xe8,0xca):self.X=(self.X+(1 if op==0xe8 else -1))&((1<<(8*xw))-1);self.nz(self.X,xw)
            elif op in (0x0a,0x4a):
                v=self.A&((1<<(8*mw))-1);c=(v>>(mw*8-1)) if op==0x0a else v&1;self.P=(self.P&~1)|c;self.set_a(v<<1 if op==0x0a else v>>1)
            elif op==0xaa:self.X=self.A&((1<<(8*xw))-1);self.nz(self.X,xw)
            elif op==0xa8:self.Y=self.A&((1<<(8*xw))-1);self.nz(self.Y,xw)
            elif op==0x8a:self.set_a(self.X)
            elif op==0x65:self.adc(self.read(self.fetch(),mw))
            elif op==0x69:self.adc(self.fetch(mw))
            elif op==0x6d:self.adc(self.read(self.fetch(2),mw))
            elif op==0xed:self.adc(self.read(self.fetch(2),mw)^((1<<(8*mw))-1))
            elif op==0xee:
                addr=self.fetch(2);v=(self.read(addr,mw)+1)&((1<<(8*mw))-1);self.write(addr,v,mw);self.nz(v,mw)
            elif op==0x77:self.adc(self.read((self.read(self.fetch(),3)+self.Y)&0xffffff,mw))
            elif op==0xa9:self.set_a(self.fetch(mw))
            elif op==0xa5:self.set_a(self.read(self.fetch(),mw))
            elif op==0xad:self.set_a(self.read(self.fetch(2),mw))
            elif op==0xbf:self.set_a(self.read((self.fetch(3)+self.X)&0xffffff,mw))
            elif op==0xa7:self.set_a(self.read(self.read(self.fetch(),3),mw))
            elif op==0xb7:self.set_a(self.read((self.read(self.fetch(),3)+self.Y)&0xffffff,mw))
            elif op==0x85:self.write(self.fetch(),self.A,mw)
            elif op==0x8d:self.write(self.fetch(2),self.A,mw)
            elif op==0x9c:self.write(self.fetch(2),0,mw)
            elif op in (0xe6,0xc6):
                addr=self.fetch();v=(self.read(addr,mw)+(1 if op==0xe6 else -1))&((1<<(8*mw))-1);self.write(addr,v,mw);self.nz(v,mw)
            elif op==0x22:
                target=self.fetch(3);self.push(self.PC>>16,1);self.push((self.PC-1)&65535,2);self.PC=target;self.depth+=1
            elif op==0x6b:
                if not self.depth:
                    if self.S!=start_stack:raise ProbeError('Stack imbalance')
                    return self.A&((1<<(8*self.mw))-1)
                addr=self.pop(2);bank=self.pop(1);self.PC=(bank<<16)|((addr+1)&65535);self.depth-=1
            else:raise ProbeError(f'Unsupported opcode {op:02X} at {pc:06X}')
        raise ProbeError('Instruction budget exceeded')
