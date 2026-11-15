"""Compresseur SPC7110 (mode 2 = 4 bits, mode 1 = 2 bits), miroir exact du décompresseur de byuu/neviksti.

Entrée : données de tuiles planaires SNES (32 octets par tuile en 4 bits, 16 en 2 bits). Sortie : flux d'octets.
Le décodeur lit des bits « à la volée » : l'encodeur maintient un intervalle [low, low+span] en entiers Python
(précision arbitraire, donc pas de gestion de retenue) puis choisit dans l'intervalle final la valeur qui a le
plus de zéros de fin et ne garde que les octets nécessaires. Les bits suivants du flux n'influencent jamais le
décodage des symboles encodés.
"""
EVO=[(0x5a,1,1,1),(0x25,6,2,0),(0x11,8,3,0),(0x08,10,4,0),(0x03,12,5,0),(0x01,15,5,0),
(0x5a,7,7,1),(0x3f,19,8,0),(0x2c,21,9,0),(0x20,22,10,0),(0x17,23,11,0),(0x11,25,12,0),(0x0c,26,13,0),(0x09,28,14,0),(0x07,29,15,0),(0x05,31,16,0),(0x04,32,17,0),(0x03,34,18,0),(0x02,35,5,0),
(0x5a,20,20,1),(0x48,39,21,0),(0x3a,40,22,0),(0x2e,42,23,0),(0x26,44,24,0),(0x1f,45,25,0),(0x19,46,26,0),(0x15,25,27,0),(0x11,26,28,0),(0x0e,26,29,0),(0x0b,27,30,0),(0x09,28,31,0),(0x08,29,32,0),(0x07,30,33,0),(0x05,31,34,0),(0x04,33,35,0),(0x04,33,36,0),(0x03,34,37,0),(0x02,35,38,0),(0x02,36,5,0),
(0x58,39,40,1),(0x4d,47,41,0),(0x43,48,42,0),(0x3b,49,43,0),(0x34,50,44,0),(0x2e,51,45,0),(0x29,44,46,0),(0x25,45,24,0),
(0x56,47,48,1),(0x4f,47,49,0),(0x47,48,50,0),(0x41,49,51,0),(0x3c,50,52,0),(0x37,51,43,0)]
M2CTX=[(1,2),(3,8),(13,14),(15,16),(17,18),(19,20),(21,22),(23,24),(25,26),(25,26),(25,26),(25,26),(25,26),(27,28),(29,30)]+[(31,31)]*17

class _Coder:
    def __init__(self):
        self.low=0;self.span=0xff;self.shifts=0
        self.idx=[0]*32;self.inv=[0]*32
    def code(self,con,t):
        """Encode un bit t dans le contexte con. Renvoie le bit décodé (= t)."""
        ib=self.inv[con];flag=t^ib;prob=EVO[self.idx[con]][0]
        if flag==0: self.span-=prob
        else:
            self.low+=self.span-(prob-1);self.span=prob-1
        shift=0
        while self.span<0x7f:
            shift+=1;self.span=(self.span<<1)+1;self.low<<=1
        self.shifts+=shift
        e=EVO[self.idx[con]]
        if flag&e[3]: self.inv[con]^=1
        if flag: self.idx[con]=e[1]
        elif shift: self.idx[con]=e[2]
        return ib
    def finish(self):
        L=8+self.shifts
        lo,hi=self.low,self.low+self.span
        # valeur de l'intervalle avec le plus de zéros de fin
        best=lo;k=0
        for k in range(L,-1,-1):
            v=((lo+(1<<k)-1)>>k)<<k
            if v<=hi: best=v;break
        nbytes=(L+7)//8
        v=best<<(nbytes*8-L)   # alignement sur un nombre entier d'octets
        data=v.to_bytes(nbytes,'big')
        return data.rstrip(b'\x00') if False else data

def _mtf(order,v):
    i=order.index(v);del order[i];order.insert(0,v)

def encode_mode2(tiles):
    """tiles : octets planaires 4 bits (multiple de 32)."""
    assert len(tiles)%32==0
    c=_Coder();po=list(range(16));out0=0;out1=0
    for t in range(len(tiles)//32):
        raw=tiles[t*32:t*32+32]
        for y in range(8):
            p=[raw[y*2],raw[y*2+1],raw[16+y*2],raw[16+y*2+1]]
            for x in range(8):
                b7=7-x
                pix=(((p[0]>>b7)&1)<<3)|(((p[1]>>b7)&1)<<2)|(((p[2]>>b7)&1)<<1)|((p[3]>>b7)&1)
                a=out0&15;b=(out0>>28)&15;cc=out1&15
                refcon=(b!=cc) if a==b else (2 if b==cc else 4-(a==cc))
                _mtf(po,a);ro=list(po)
                for v in (cc,b,a): _mtf(ro,v)
                r=ro.index(pix);con=0
                for k in range(4):
                    bit=(r>>(3-k))&1
                    ib=c.code(con,bit)
                    con=M2CTX[con][bit]+(refcon if con==1 else 0)
                out1=((out1<<4)+((out0>>28)&15))&0xffffffff
                out0=((out0<<4)+pix)&0xffffffff
    return c.finish()


# ---------------------------------------------------------------------------------------------------------
# Décompresseur (même logique que le décompresseur de byuu / neviksti publié dans Snes9x), pour vérifier
# chaque flux produit par l'encodeur sans émulateur.
def decode_mode2(rom, stream_off, nbytes):
    """Décompresse nbytes octets (multiple de 32) d'un flux de mode 2 situé à l'offset de fichier stream_off.
    Les lectures se font dans la ROM de données (offset 0x100000 + n), avec bouclage comme l'émulateur."""
    size = len(rom) - 0x200000 if len(rom) > 0x500000 else len(rom) - 0x100000
    pos = [stream_off - 0x100000]

    def rd():
        o = pos[0]
        while o >= size:
            o -= size
        pos[0] += 1
        return rom[0x100000 + o]

    idx = [0] * 32; inv = [0] * 32
    val = rd(); inb = rd(); span = 0xff; in_count = 8
    po = list(range(16)); out0 = out1 = 0; inverts = lps = 0
    out = bytearray(); bpb = []
    while len(out) < nbytes:
        for _ in range(8):
            a = out0 & 15; b = (out0 >> 28) & 15; c = out1 & 15
            refcon = (b != c) if a == b else (2 if b == c else 4 - (a == c))
            _mtf(po, a); ro = list(po)
            for v in (c, b, a):
                _mtf(ro, v)
            con = 0
            for _ in range(4):
                prob = EVO[idx[con]][0]
                if val <= span - prob:
                    span -= prob; flag = 0
                else:
                    val -= span - (prob - 1); span = prob - 1; flag = 1
                shift = 0
                while span < 0x7f:
                    shift += 1; span = (span << 1) + 1
                    val = ((val << 1) + (inb >> 7)) & 0xff
                    inb = (inb << 1) & 0xff
                    in_count -= 1
                    if in_count == 0:
                        inb = rd(); in_count = 8
                lps = ((lps << 1) + flag) & 0xffffffff
                ib = inv[con]; inverts = ((inverts << 1) + ib) & 0xffffffff
                e = EVO[idx[con]]
                if flag & e[3]:
                    inv[con] ^= 1
                if flag:
                    idx[con] = e[1]
                elif shift:
                    idx[con] = e[2]
                con = M2CTX[con][flag ^ ib] + (refcon if con == 1 else 0)
            pix = ro[(lps ^ inverts) & 15]
            out1 = ((out1 << 4) + ((out0 >> 28) & 15)) & 0xffffffff
            out0 = ((out0 << 4) + pix) & 0xffffffff
        # conversion en plans de bits : plan 0 = bit 3 du pixel, ..., plan 3 = bit 0 (voir le décodeur d'origine)
        p = [0, 0, 0, 0]
        for x in range(8):
            pix = (out0 >> (4 * (7 - x))) & 15
            for k in range(4):
                p[k] |= ((pix >> (3 - k)) & 1) << (7 - x)
        out.append(p[0]); out.append(p[1]); bpb.extend((p[2], p[3]))
        if len(bpb) == 16:
            out.extend(bpb); bpb = []
    return bytes(out[:nbytes])
