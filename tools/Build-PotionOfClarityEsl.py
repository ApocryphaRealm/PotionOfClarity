#!/usr/bin/env python3
r"""
Build-PotionOfClarityEsl.py - authors PotionOfClarity.esl, the item carrier for Potion of
Clarity. Two NEW records, one master (Skyrim.esm), light-flagged, no vanilla overrides:

    0x800  MGEF  POC_ClarityEffect     inert placeholder effect (archetype Script, NO script)
    0x801  ALCH  POC_PotionOfClarity   the potion  (DLL contract: LookupForm(0x801, "PotionOfClarity.esl"))

Design decision 2026-09-01: the potion is NOT craftable - no recipe record. It carries the
VendorItemPotion keyword and a real gold value (default 500, set live from the DLL), so it
exists for merchants and the console; how it enters the world is the DLL's business.
Everything the potion DOES lives in PotionOfClarity.dll (it watches TESEquipEvent for this
ALCH); the plugin only has to make the potion exist. No VMAD anywhere.
Byte-level writer on the primitives proven by this project's earlier plugin builders; every
vanilla FormID below was read out of the live Skyrim.esm by EDID, not guessed.

Usage:  python Build-PotionOfClarityEsl.py [out.esl]
"""
import struct, sys, os

FORM_VER = 44
NEW_MGEF = 0x01000800
NEW_ALCH = 0x01000801

# --- vanilla references (Skyrim.esm, scanned by EDID 2026-09-01) ---
KYWD_VendorItemPotion = 0x0008CDEC
SNDR_ITMPotionUpSD    = 0x0003EDBD
SNDR_ITMPotionDownSD  = 0x0003EDC0
SNDR_ITMPotionUse     = 0x000B6435

BS = chr(92)
ALCH_MODL = ('Clutter' + BS + 'Potions' + BS + 'PotionFortifyMagickaExtreme.nif\x00').encode('ascii')  # real vanilla mesh
MODT_V2 = bytes.fromhex('020000000000000000000000')

# 152-byte MGEF DATA: archetype 1 (Script), cast type 1 (Fire and Forget), delivery 0 (Self),
# no actor values, no art, no projectile. With no VMAD a Script-archetype effect runs nothing.
MGEF_DATA = bytes.fromhex(
    '00000000' '00000000' '00000000' 'ffffffff' 'ffffffff' '00000000' '00000000' '00000000'
    '00000000' '00000000' '00000000' '00000000' '00000000' '00000000' '00000000' '00000000'
    '01000000' 'ffffffff' '00000000' '00000000' '01000000' '00000000' 'ffffffff' '00000000'
    '00000000' '00000000' '00000000' '00000000' '0000803f' '00000000' '00000000' '00000000'
    '00000000' '00000000' '00000000' '01000000' '00000000' '00000000')
assert len(MGEF_DATA) == 152


def sub(sig, data):
    assert len(data) < 0x10000, sig
    return sig.encode() + struct.pack('<H', len(data)) + data


def rec(sig, formid, body, flags=0):
    return (sig.encode() + struct.pack('<I', len(body)) + struct.pack('<I', flags)
            + struct.pack('<I', formid) + struct.pack('<HHHH', 0, 0, FORM_VER, 0) + body)


def grup(label, gtype, payload):
    return (b'GRUP' + struct.pack('<I', len(payload) + 24) + label
            + struct.pack('<i', gtype) + b'\x00' * 8 + payload)


def build():
    mgef = (sub('EDID', b'POC_ClarityEffect\x00')
            + sub('FULL', b'Clarity\x00')
            + sub('DATA', MGEF_DATA)
            + sub('SNDD', b'')
            + sub('DNAM', b'Clears the mind of every learned perk, returning the points to be spent anew.\x00'))

    alch = (sub('EDID', b'POC_PotionOfClarity\x00')
            + sub('OBND', b'\x00' * 12)
            + sub('FULL', b'Potion of Clarity\x00')
            + sub('KSIZ', struct.pack('<I', 1))
            + sub('KWDA', struct.pack('<I', KYWD_VendorItemPotion))
            + sub('MODL', ALCH_MODL)
            + sub('MODT', MODT_V2)
            + sub('YNAM', struct.pack('<I', SNDR_ITMPotionUpSD))
            + sub('ZNAM', struct.pack('<I', SNDR_ITMPotionDownSD))
            + sub('DATA', struct.pack('<f', 0.5))                                   # weight
            + sub('ENIT', struct.pack('<IIIII', 500, 0x00000001, 0, 0, SNDR_ITMPotionUse))  # value 500 (default price), No Auto-Calc
            + sub('EFID', struct.pack('<I', NEW_MGEF))
            + sub('EFIT', struct.pack('<fII', 0.0, 0, 0)))                          # magnitude, area, duration

    assert b'VMAD' not in mgef + alch

    # top-level groups in the engine's canonical order: MGEF < ALCH
    body = (grup(b'MGEF', 0, rec('MGEF', NEW_MGEF, mgef))
            + grup(b'ALCH', 0, rec('ALCH', NEW_ALCH, alch)))

    num_records = 4  # 2 records + 2 groups, TES4 excluded
    hedr = struct.pack('<fiI', 1.7, num_records, 0x802)
    tes4_body = (sub('HEDR', hedr)
                 + sub('CNAM', b'ApocryphaRealm\x00')
                 + sub('SNAM', b'Potion of Clarity - item carrier. All behaviour is in PotionOfClarity.dll.\x00')
                 + sub('MAST', b'Skyrim.esm\x00') + sub('DATA', b'\x00' * 8))
    tes4 = rec('TES4', 0, tes4_body, flags=0x00000200)  # Light
    return tes4 + body


if __name__ == '__main__':
    out = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'dist', 'PotionOfClarity.esl')
    blob = build()
    os.makedirs(os.path.dirname(os.path.abspath(out)), exist_ok=True)
    open(out, 'wb').write(blob)
    print('wrote %s (%d bytes)' % (os.path.abspath(out), len(blob)))
