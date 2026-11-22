#!/usr/bin/env python3
"""Store rebuilt blocks in their audited source span or the pinned free pool.
All planning/validation completes before writing. Directory aliases move together.
Source ROM bytes are never written to disk by this module.
"""
from pointers import FREE_START, FREE_END, file_to_cpu

PROTECTED=(0x6C9400,0x6C9510)   # données non textuelles (abréviations + hook) à ne jamais écraser

def store_blocks(original, items):
    if len(original)<FREE_END or any(original[FREE_START:FREE_END]):
        raise ValueError('Pinned free pool is unavailable')
    cursor=FREE_START; plans=[]; source_spans=[]; destinations=[]; slots=set()
    for item in items:
        block=item['block'];source=item['source'];old=item['old'];payload=item['payload'];relative=item['relative']
        if not old or original[source:source+len(old)]!=old:
            raise ValueError('Source block differs from audit')
        if int(block['offset'],16)!=source or int(block['end_exclusive'],16)!=source+len(old) or block['length']!=len(old):
            raise ValueError('Source span differs from directory audit')
        if source<0x600000 or source+len(old)>FREE_START:
            raise ValueError('Source outside audited main pool')
        if any(source<end and source+len(old)>start for start,end in source_spans):
            raise ValueError('Duplicate or overlapping source blocks')
        source_spans.append((source,source+len(old)))
        if not 2<=len(payload)<=65535 or not relative or relative[0]!=2*len(relative):
            raise ValueError('Invalid rebuilt group table')
        if relative!=sorted(relative) or any(not 2*len(relative)<=v<len(payload) for v in relative):
            raise ValueError('Group target outside rebuilt payload')
        if any(int.from_bytes(payload[2*i:2*i+2],'little')!=v for i,v in enumerate(relative)):
            raise ValueError('Group table differs from relocation metadata')
        if len(payload)<=len(old):
            destination=source;storage_length=len(old);kind='in_place'
        else:
            if cursor<PROTECTED[1] and cursor+len(payload)>PROTECTED[0]:
                cursor=(PROTECTED[1]+15)&~15
            if cursor+len(payload)>FREE_END:
                raise ValueError('Rebuilt text exhausts approved free pool')
            destination=cursor;storage_length=len(payload);kind='relocated'
            cursor=(cursor+storage_length+15)&~15
            if cursor>FREE_END:
                raise ValueError('Rebuilt text exhausts approved free pool')
        if any(destination<end and destination+storage_length>start for start,end in destinations):
            raise ValueError('Overlapping destination blocks')
        destinations.append((destination,destination+storage_length))
        directory=[]
        for entry in block['directory_slots']:
            slot=int(entry,16)
            if slot in slots or not 0x0C9800<=slot<0x0C9800+253*3 or (slot-0x0C9800)%3:
                raise ValueError('Invalid or duplicate directory slot')
            if original[slot:slot+3]!=file_to_cpu(source).to_bytes(3,'little'):
                raise ValueError('Directory no longer points to audited source')
            slots.add(slot);directory.append(slot)
        expected_slots={0x0C9800+3*i for i in range(253)
                        if original[0x0C9800+3*i:0x0C9800+3*i+3]==file_to_cpu(source).to_bytes(3,'little')}
        if not directory or set(directory)!=expected_slots:
            raise ValueError('Directory alias list is incomplete')
        plans.append((item,destination,storage_length,kind,directory))
    out=bytearray(original)
    for item,destination,length,kind,directory in plans:
        payload=item['payload']
        out[destination:destination+length]=payload+bytes(length-len(payload))
        for slot in directory:
            out[slot:slot+3]=file_to_cpu(destination).to_bytes(3,'little')
        item.update(destination=destination,storage_length=length,allocation_kind=kind)
    assert len(out)==len(original)
    return bytes(out),{'allocation_end':hex(cursor),'free_bytes':FREE_END-cursor,
                       'in_place_blocks':sum(p[3]=='in_place' for p in plans),
                       'relocated_blocks':sum(p[3]=='relocated' for p in plans),
                       'alignment_bytes':16}
