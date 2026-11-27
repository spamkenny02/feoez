"""Compatibility policy matching the V75 IPS validated by the user on SD2SNES."""

# Only the three-byte JSL operands are omitted; the opcode remains unchanged.
DISABLED_HOOK_SPANS = ((0x006F59, 0x006F5C), (0x037029, 0x03702C))


def preserve_native_calls(source, target):
    """Keep source call targets, preserving all other bytes of the validated patch.

    Deliberately do not recalculate the checksum: the supplied hardware-tested
    IPS retains V75's checksum bytes. This reproduces that exact artifact.
    """
    out = bytearray(target)
    for start, end in DISABLED_HOOK_SPANS:
        if min(len(source), len(target)) < end:
            raise ValueError('ROM too short for SD2SNES compatibility calls')
        out[start:end] = source[start:end]
    return bytes(out)
