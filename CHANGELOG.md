# PotionOfClarity - changelog

Rule 61: this mod's own history, kept beside the code it describes.

<!-- VERSIONING-RULES -->
> **Versioning rules (CLAUDE.md rules 6 and 48):** `X.Y.Z`; a change increments the THIRD
> number; at `.9` the MINOR rolls. The next number is LAST WORKING + 1; failed/scratch/
> untested numbers are reused. Numbers come from version-ledger.ps1 + set-version.ps1.

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
