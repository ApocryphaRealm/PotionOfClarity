# PotionOfClarity - changelog

Rule 61: this mod's own history, kept beside the code it describes.

<!-- VERSIONING-RULES -->
> **Versioning rules (CLAUDE.md rules 6 and 48):** `X.Y.Z`; a change increments the THIRD
> number; at `.9` the MINOR rolls. The next number is LAST WORKING + 1; failed/scratch/
> untested numbers are reused. Numbers come from version-ledger.ps1 + set-version.ps1.

## 1.0.4 - 2026-09-01 - working

### Added
- Static Skill Leveling Rewritten compatibility (bSSLRCompat, off by default; settings-page
  toggle). With SSLR installed, drinking the potion also resets every trained skill to its
  starting value (15 plus the racial bonus), zeroes its XP and returns the skill points SSLR
  charged for the levels above it (per-level cost tiers from SSLR's own globals) to SSLR's
  points pool - the global SSL_PointsLeftAfterLvlUp, plus the quest script's Int property on
  variants that keep it there. Own code from the documented behaviour of SSLR and its Skill
  Reset addon; nothing of theirs is used. Untrained skills are left alone.

## 1.0.3 - 2026-09-01 - working

### Added
- Elgrim's Elixirs in Riften always stocks the potion (the original mod's guarantee, kept -
  design decision 2026-09-01). Applied at runtime to the vanilla merchant chest's base form
  (99 in stock, like the original) rather than as a plugin override, so no record conflict
  is possible; an existing save sees it after the merchant's next restock.

## 1.0.2 - 2026-09-01 - working

### Changed
- The potion is no longer craftable (design decision 2026-09-01): the cookpot recipe record
  is gone from PotionOfClarity.esl, which now holds just the inert effect and the potion.
- Price: default 500 gold, slider range 0 to 1000 (was 250 / 0 to 5000).

## 1.0.1 - 2026-09-01 - working

### Changed
- The settings page now does one thing (design decision 2026-09-01): it sets how much the
  potion costs. uPrice (default 250) is written onto the potion's gold value at load and on
  change, so merchants charge and pay that amount. The Enabled toggle and the readouts are
  gone - the potion is the feature.

## 1.0.0 - 2026-09-01 - working

### Added
- First release. Drink a Potion of Clarity and every perk bought from the 18 skill trees is
  removed and handed back as perk points (skill levels untouched; racial, quest and other
  abilities outside the trees are never touched).
- The potion lives in a three-record light plugin (PotionOfClarity.esl: inert effect, the
  potion, a cookpot recipe - Salt Pile + Frost Mirriam). It carries the VendorItemPotion
  keyword so alchemists can trade it. No vanilla record is overridden.
- SKSE side: a TESEquipEvent sink keyed on the potion's FormID; the refund is a main-thread
  edit of the player's perk list and the game's own perk-point counter, so nothing is
  serialized and uninstalling leaves exactly the state the last drink produced. Perk points
  clamp at the engine's 127 cap (logged when it bites).
- In-game settings page (Apocrypha Menu Framework, stock SKSE Menu Framework fallback):
  Enabled toggle, live spent-perks / perk-points readout, last refund message,
  Save/Reload/Restore.
- Plain-file INI (redirector-proof), DevBench driving tool `poc.control` (give / drink
  through the equip manager / direct refund / reload), .pdb debug symbols in the main download.
