# -*- coding: utf-8 -*-
"""gen-translations.py - builds the eleven PotionOfClarity_<language>.txt files.

The English key list is extracted from the PATCHED source/UI.cpp by regex on
strings::TR("KEY", "text") so it can never drift from the code. The other ten languages are
this project's own translations of that list, held below as parallel dictionaries.

Writes REPO/dist/Interface/Translations/PotionOfClarity_<language>.txt for english + the
owner's ten languages (UTF-16LE with a BOM, one "$key<TAB>text" per line, literal "\\n" for an
embedded line break, CRLF records - the SKSE/SkyUI shape AMF's own Strings.cpp reads).

Run: `python tools/gen-translations.py` from the repo root or anywhere (paths are relative to
this script's grandparent directory).
"""
import io
import os
import re

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LANGS = ["english", "japanese", "korean", "chinese", "russian", "german", "french", "spanish", "italian", "polish", "czech"]

TR_RE = re.compile(r'strings::TR\(\s*"((?:[^"\\]|\\.)+)"\s*,\s*"((?:[^"\\]|\\.)*)"\s*\)')


def unescape(s):
    return s.encode("latin-1", "backslashreplace").decode("unicode_escape") if "\\" in s else s


KEY_ARRAY_RE = re.compile(r'constexpr const char\* kLogLevelKeys\[\]\s*=\s*\{([^}]*)\};', re.S)
NAME_ARRAY_RE = re.compile(r'constexpr const char\* kLogLevelNames\[\]\s*=\s*\{([^}]*)\};', re.S)
STR_LIT_RE = re.compile(r'"((?:[^"\\]|\\.)*)"')


def read_keys():
    path = os.path.join(REPO, "source", "UI.cpp")
    src = io.open(path, "r", encoding="utf-8").read()
    keys = {}
    order = []
    for m in TR_RE.finditer(src):
        key, text = unescape(m.group(1)), unescape(m.group(2))
        if key in keys and keys[key] != text:
            raise RuntimeError(f"duplicate key {key!r} with two different English texts: {keys[key]!r} vs {text!r}")
        if key not in keys:
            order.append(key)
        keys[key] = text

    # The log-level Combo's option labels are looked up by a parallel key array
    # (kLogLevelKeys[i] -> kLogLevelNames[i]) rather than a literal strings::TR(...) call, since
    # the option text is rebuilt into a std::vector per frame. Pair the two arrays positionally.
    km = KEY_ARRAY_RE.search(src)
    nm = NAME_ARRAY_RE.search(src)
    if not km or not nm:
        raise RuntimeError("could not find kLogLevelKeys/kLogLevelNames arrays in source/UI.cpp")
    array_keys = [unescape(s) for s in STR_LIT_RE.findall(km.group(1))]
    array_names = [unescape(s) for s in STR_LIT_RE.findall(nm.group(1))]
    if len(array_keys) != len(array_names):
        raise RuntimeError(f"kLogLevelKeys ({len(array_keys)}) and kLogLevelNames ({len(array_names)}) length mismatch")
    for key, text in zip(array_keys, array_names):
        if key in keys and keys[key] != text:
            raise RuntimeError(f"duplicate key {key!r} with two different English texts: {keys[key]!r} vs {text!r}")
        if key not in keys:
            order.append(key)
        keys[key] = text

    return keys, order


# ------------------------------------------------------------------------------------------------
# Translations for every key found in source/UI.cpp. Plain, literal renderings of the UI text;
# every printf specifier is kept exactly; product names (Skyrim, Apocrypha Menu Framework,
# Potion of Clarity, Static Skill Leveling Rewritten, Character Progression Control) stay
# untranslated; file names (PotionOfClarity.log, PotionOfClarity.esl, the INI) stay untranslated
# inside the translated sentence.
# ------------------------------------------------------------------------------------------------
TRANSLATIONS = {
    "POC_HelpMark": {
        "japanese": "(?)", "korean": "(?)", "chinese": "(?)", "russian": "(?)", "german": "(?)",
        "french": "(?)", "spanish": "(?)", "italian": "(?)", "polish": "(?)", "czech": "(?)",
    },
    "POC_Title": {
        "japanese": "クラリティのポーション", "korean": "명료함의 마법약", "chinese": "清明药水",
        "russian": "Зелье прозрения", "german": "Trank der Klarheit", "french": "Potion de clarté",
        "spanish": "Poción de claridad", "italian": "Pozione di chiarezza", "polish": "Eliksir jasności",
        "czech": "Lektvar jasnosti",
    },
    "POC_Price": {
        "japanese": "価格", "korean": "가격", "chinese": "价格", "russian": "Цена", "german": "Preis",
        "french": "Prix", "spanish": "Precio", "italian": "Prezzo", "polish": "Cena", "czech": "Cena",
    },
    "POC_PriceFormat": {
        "japanese": "%.0f ゴールド", "korean": "%.0f 골드", "chinese": "%.0f 金币", "russian": "%.0f золота",
        "german": "%.0f Gold", "french": "%.0f or", "spanish": "%.0f de oro", "italian": "%.0f oro",
        "polish": "%.0f złota", "czech": "%.0f zlata",
    },
    "POC_HelpPrice": {
        "japanese": "クラリティのポーションの価格 - その金価値で、商人がそれに支払う額でもあります(0から1000)。",
        "korean": "명료함의 마법약의 가격입니다 - 상인이 지불하는 금 가치입니다 (0에서 1000까지).",
        "chinese": "清明药水的价格 - 它的金币价值,也是商人为其支付的金额(0 到 1000)。",
        "russian": "Сколько стоит Зелье прозрения - его золотая ценность, то есть сумма, которую платят торговцы (от 0 до 1000).",
        "german": "Wie viel ein Trank der Klarheit kostet - sein Goldwert, den auch Händler dafür zahlen (0 bis 1000).",
        "french": "Combien coûte une Potion de clarté - sa valeur en or, celle que paient les marchands (0 à 1000).",
        "spanish": "Cuánto cuesta una Poción de claridad - su valor en oro, que es lo que pagan los mercaderes por ella (0 a 1000).",
        "italian": "Quanto costa una Pozione di chiarezza - il suo valore in oro, ossia quanto pagano i mercanti per essa (da 0 a 1000).",
        "polish": "Ile kosztuje Eliksir jasności - jego wartość w złocie, którą płacą też kupcy (od 0 do 1000).",
        "czech": "Kolik stojí Lektvar jasnosti - jeho hodnota ve zlatě, kterou za něj platí i obchodníci (0 až 1000).",
    },
    "POC_SslrToggle": {
        "japanese": "Static Skill Leveling Rewritten 互換性", "korean": "Static Skill Leveling Rewritten 호환성",
        "chinese": "Static Skill Leveling Rewritten 兼容", "russian": "Совместимость со Static Skill Leveling Rewritten",
        "german": "Static Skill Leveling Rewritten-Kompatibilität", "french": "Compatibilité Static Skill Leveling Rewritten",
        "spanish": "Compatibilidad con Static Skill Leveling Rewritten", "italian": "Compatibilità con Static Skill Leveling Rewritten",
        "polish": "Zgodność ze Static Skill Leveling Rewritten", "czech": "Kompatibilita se Static Skill Leveling Rewritten",
    },
    "POC_HelpSslrToggle": {
        "japanese": "Static Skill Leveling Rewrittenがインストールされていると、ポーションを飲むことで訓練したすべてのスキルが初期値(15+種族ボーナス)に戻り、それより上のレベルでSSLRが要求したスキルポイントがプールに返還され、次のレベルアップ時に再度使えます。オフ:パークのみ。",
        "korean": "Static Skill Leveling Rewritten이 설치되어 있으면, 마법약을 마실 때 훈련된 모든 스킬이 시작 값(15 + 종족 보너스)으로 재설정되고 그 이상의 레벨에 대해 SSLR이 청구한 스킬 포인트가 풀로 반환되어 다음 레벨업에서 다시 사용할 수 있습니다. 꺼짐: 펄크만.",
        "chinese": "安装了 Static Skill Leveling Rewritten 后,饮用药水还会将每项已训练的技能重置为初始值(15 加上你的种族加值),并将 SSLR 为高于该值的等级所收取的技能点返还到其点数池中,供你下次升级时再次使用。关闭:仅重置技能点。",
        "russian": "Если установлен Static Skill Leveling Rewritten, выпитое зелье также сбрасывает каждый тренированный навык до начального значения (15 плюс расовый бонус) и возвращает очки навыков, потраченные SSLR за уровни выше него, в его пул для повторной трата при следующем повышении уровня. Выкл: только перки.",
        "german": "Ist Static Skill Leveling Rewritten installiert, setzt das Trinken des Tranks zusätzlich jede trainierte Fertigkeit auf ihren Startwert zurück (15 plus dein Rassenbonus) und gibt die von SSLR für die Stufen darüber verlangten Fertigkeitspunkte in dessen Pool zurück, um sie beim nächsten Stufenaufstieg erneut auszugeben. Aus: nur Perks.",
        "french": "Avec Static Skill Leveling Rewritten installé, boire la potion réinitialise aussi chaque compétence entraînée à sa valeur de départ (15 plus votre bonus racial) et renvoie dans sa réserve les points de compétence que SSLR a facturés pour les niveaux au-dessus, à dépenser à nouveau à votre prochaine montée de niveau. Désactivé : uniquement les capacités.",
        "spanish": "Con Static Skill Leveling Rewritten instalado, beber la poción también reinicia cada habilidad entrenada a su valor inicial (15 más tu bonificación racial) y devuelve a su reserva los puntos de habilidad que SSLR cobró por los niveles por encima, para gastarlos de nuevo en tu próxima subida de nivel. Desactivado: solo dotes.",
        "italian": "Con Static Skill Leveling Rewritten installato, bere la pozione azzera anche ogni abilità addestrata al suo valore iniziale (15 più il tuo bonus razziale) e restituisce al suo pool i punti abilità che SSLR ha addebitato per i livelli superiori, da spendere di nuovo al prossimo passaggio di livello. Disattivato: solo abilità speciali.",
        "polish": "Gdy zainstalowano Static Skill Leveling Rewritten, wypicie eliksiru resetuje też każdą wytrenowaną umiejętność do wartości początkowej (15 plus twój bonus rasowy) i zwraca do jego zasobu punkty umiejętności naliczone przez SSLR za poziomy powyżej, do ponownego wydania przy następnym awansie. Wyłączone: tylko atuty.",
        "czech": "Je-li nainstalován Static Skill Leveling Rewritten, vypití lektvaru také vrátí každou vycvičenou dovednost na počáteční hodnotu (15 plus váš rasový bonus) a vrátí body dovedností, které SSLR naúčtoval za úrovně nad ní, do jeho zásoby k opětovnému využití při dalším postupu na úroveň. Vypnuto: pouze schopnosti.",
    },
    "POC_SslrDetected": {
        "japanese": "SSLR検出 - ポイントプール: %d", "korean": "SSLR 감지됨 - 포인트 풀: %d",
        "chinese": "已检测到 SSLR - 点数池: %d", "russian": "SSLR обнаружен - пул очков: %d",
        "german": "SSLR erkannt - Punktepool: %d", "french": "SSLR détecté - réserve de points : %d",
        "spanish": "SSLR detectado - reserva de puntos: %d", "italian": "SSLR rilevato - pool di punti: %d",
        "polish": "Wykryto SSLR - pula punktów: %d", "czech": "SSLR detekován - zásoba bodů: %d",
    },
    "POC_SslrNotDetected": {
        "japanese": "SSLRが検出されません - インストールされるまでこのトグルは何もしません。",
        "korean": "SSLR가 감지되지 않았습니다 - 설치되기 전까지 이 토글은 아무 동작도 하지 않습니다.",
        "chinese": "未检测到 SSLR - 该开关在其安装前不会产生任何效果。",
        "russian": "SSLR не обнаружен - переключатель ничего не делает, пока он не установлен.",
        "german": "SSLR nicht erkannt - der Schalter bewirkt nichts, bis es installiert ist.",
        "french": "SSLR non détecté - ce bouton ne fait rien jusqu'à son installation.",
        "spanish": "SSLR no detectado - el interruptor no hace nada hasta que se instale.",
        "italian": "SSLR non rilevato - l'interruttore non fa nulla finché non viene installato.",
        "polish": "Nie wykryto SSLR - ten przełącznik nic nie robi, dopóki nie zostanie zainstalowany.",
        "czech": "SSLR nebyl detekován - tento přepínač nedělá nic, dokud nebude nainstalován.",
    },
    "POC_CpcToggle": {
        "japanese": "Character Progression Control 互換性", "korean": "Character Progression Control 호환성",
        "chinese": "Character Progression Control 兼容", "russian": "Совместимость с Character Progression Control",
        "german": "Character Progression Control-Kompatibilität", "french": "Compatibilité Character Progression Control",
        "spanish": "Compatibilidad con Character Progression Control", "italian": "Compatibilità con Character Progression Control",
        "polish": "Zgodność z Character Progression Control", "czech": "Kompatibilita s Character Progression Control",
    },
    "POC_HelpCpcToggle": {
        "japanese": "Character Progression Controlがインストールされ、スキルポイントを使用している場合、ポーションを飲むことで訓練したすべてのスキルを初期値に戻すよう要求し、それが要求したポイントを銀行に返還します。それ以外の場合は何もしません。既定でオン。",
        "korean": "Character Progression Control이 설치되어 스킬 포인트를 사용 중이면, 마법약을 마실 때 훈련된 모든 스킬을 시작 값으로 재설정하고 청구된 포인트를 그 뱅크로 반환하도록 요청합니다. 그 외에는 아무 동작도 하지 않습니다. 기본값은 켜짐.",
        "chinese": "如果安装了 Character Progression Control 并使用技能点,饮用药水还会请求它将每项已训练的技能重置为初始值,并将其收取的点数返还到其点数库。否则不会有任何效果。默认开启。",
        "russian": "Если установлен Character Progression Control и используются очки навыков, выпитое зелье также просит его сбросить каждый тренированный навык до начального значения и вернуть потраченные очки в его банк. В остальных случаях ничего не делает. По умолчанию включено.",
        "german": "Ist Character Progression Control installiert und werden Fertigkeitspunkte verwendet, bittet das Trinken des Tranks es außerdem, jede trainierte Fertigkeit auf ihren Startwert zurückzusetzen und die verlangten Punkte in dessen Bank zurückzugeben. Andernfalls bewirkt es nichts. Standardmäßig aktiviert.",
        "french": "Avec Character Progression Control installé et utilisant les points de compétence, boire la potion lui demande aussi de réinitialiser chaque compétence entraînée à sa valeur de départ et de renvoyer les points facturés dans sa banque. Sinon, cela ne fait rien. Activé par défaut.",
        "spanish": "Con Character Progression Control instalado y usando puntos de habilidad, beber la poción también le pide que reinicie cada habilidad entrenada a su valor inicial y devuelva los puntos cobrados a su banco. En cualquier otro caso, no hace nada. Activado por defecto.",
        "italian": "Con Character Progression Control installato e in uso i punti abilità, bere la pozione gli chiede anche di azzerare ogni abilità addestrata al valore iniziale e restituire i punti addebitati alla sua banca. Altrimenti non fa nulla. Attivo per impostazione predefinita.",
        "polish": "Gdy zainstalowano Character Progression Control i używane są punkty umiejętności, wypicie eliksiru prosi go też o zresetowanie każdej wytrenowanej umiejętności do wartości początkowej i zwrócenie naliczonych punktów do jego banku. W innym przypadku nic nie robi. Domyślnie włączone.",
        "czech": "Je-li nainstalován Character Progression Control a používány body dovedností, vypití lektvaru jej také požádá, aby vrátil každou vycvičenou dovednost na počáteční hodnotu a vrátil naúčtované body do jeho banky. Jinak nedělá nic. Výchozí stav: zapnuto.",
    },
    "POC_CpcDetected": {
        "japanese": "Character Progression Control が検出されました。", "korean": "Character Progression Control이 감지되었습니다.",
        "chinese": "已检测到 Character Progression Control。", "russian": "Character Progression Control обнаружен.",
        "german": "Character Progression Control erkannt.", "french": "Character Progression Control détecté.",
        "spanish": "Character Progression Control detectado.", "italian": "Character Progression Control rilevato.",
        "polish": "Wykryto Character Progression Control.", "czech": "Character Progression Control detekován.",
    },
    "POC_CpcNotDetected": {
        "japanese": "Character Progression Control が検出されません - インストールされるまでこのトグルは何もしません。",
        "korean": "Character Progression Control이 감지되지 않았습니다 - 설치되기 전까지 이 토글은 아무 동작도 하지 않습니다.",
        "chinese": "未检测到 Character Progression Control - 该开关在其安装前不会产生任何效果。",
        "russian": "Character Progression Control не обнаружен - переключатель ничего не делает, пока он не установлен.",
        "german": "Character Progression Control nicht erkannt - der Schalter bewirkt nichts, bis es installiert ist.",
        "french": "Character Progression Control non détecté - ce bouton ne fait rien jusqu'à son installation.",
        "spanish": "Character Progression Control no detectado - el interruptor no hace nada hasta que se instale.",
        "italian": "Character Progression Control non rilevato - l'interruttore non fa nulla finché non viene installato.",
        "polish": "Nie wykryto Character Progression Control - ten przełącznik nic nie robi, dopóki nie zostanie zainstalowany.",
        "czech": "Character Progression Control nebyl detekován - tento přepínač nedělá nic, dokud nebude nainstalován.",
    },
    "POC_EslNotLoaded": {
        "japanese": "PotionOfClarity.esl が読み込まれていません - Modマネージャーで有効にしてください。そうしないとポーションは存在できません。",
        "korean": "PotionOfClarity.esl 이(가) 로드되지 않았습니다 - 모드 매니저에서 활성화하세요. 그렇지 않으면 마법약이 존재할 수 없습니다.",
        "chinese": "PotionOfClarity.esl 未加载 - 请在你的模组管理器中启用它,否则该药水无法存在。",
        "russian": "PotionOfClarity.esl не загружен - включите его в вашем менеджере модов, иначе зелье не может существовать.",
        "german": "PotionOfClarity.esl ist nicht geladen - aktiviere es in deinem Mod-Manager, sonst kann der Trank nicht existieren.",
        "french": "PotionOfClarity.esl n'est pas chargé - activez-le dans votre gestionnaire de mods, sinon la potion ne peut pas exister.",
        "spanish": "PotionOfClarity.esl no está cargado - actívalo en tu gestor de mods, o la poción no puede existir.",
        "italian": "PotionOfClarity.esl non è caricato - attivalo nel tuo gestore di mod, altrimenti la pozione non può esistere.",
        "polish": "PotionOfClarity.esl nie jest wczytany - włącz go w swoim menedżerze modów, inaczej eliksir nie może istnieć.",
        "czech": "PotionOfClarity.esl není načten - povolte jej ve svém správci modů, jinak lektvar nemůže existovat.",
    },
    "POC_Debug": {
        "japanese": "デバッグ", "korean": "디버그", "chinese": "调试", "russian": "Отладка", "german": "Debug",
        "french": "Débogage", "spanish": "Depuración", "italian": "Debug", "polish": "Debugowanie", "czech": "Ladění",
    },
    "POC_LogLevel": {
        "japanese": "ログレベル", "korean": "로그 레벨", "chinese": "日志级别", "russian": "Уровень журнала",
        "german": "Protokollstufe", "french": "Niveau de journal", "spanish": "Nivel de registro",
        "italian": "Livello di log", "polish": "Poziom logowania", "czech": "Úroveň logování",
    },
    "POC_LogLevel_Trace": {
        "japanese": "トレース", "korean": "추적", "chinese": "跟踪", "russian": "Трассировка", "german": "Trace",
        "french": "Trace", "spanish": "Trace", "italian": "Trace", "polish": "Trace", "czech": "Trace",
    },
    "POC_LogLevel_Debug": {
        "japanese": "デバッグ", "korean": "디버그", "chinese": "调试", "russian": "Отладка", "german": "Debug",
        "french": "Débogage", "spanish": "Depuración", "italian": "Debug", "polish": "Debugowanie", "czech": "Ladění",
    },
    "POC_LogLevel_Info": {
        "japanese": "情報", "korean": "정보", "chinese": "信息", "russian": "Информация", "german": "Info",
        "french": "Infos", "spanish": "Información", "italian": "Informazioni", "polish": "Informacje", "czech": "Informace",
    },
    "POC_LogLevel_Warning": {
        "japanese": "警告", "korean": "경고", "chinese": "警告", "russian": "Предупреждение", "german": "Warnung",
        "french": "Avertissement", "spanish": "Advertencia", "italian": "Avviso", "polish": "Ostrzeżenie", "czech": "Varování",
    },
    "POC_LogLevel_Error": {
        "japanese": "エラー", "korean": "오류", "chinese": "错误", "russian": "Ошибка", "german": "Fehler",
        "french": "Erreur", "spanish": "Error", "italian": "Errore", "polish": "Błąd", "czech": "Chyba",
    },
    "POC_LogLevel_Critical": {
        "japanese": "重大", "korean": "치명적", "chinese": "严重", "russian": "Критическая",
        "german": "Kritisch", "french": "Critique", "spanish": "Crítico", "italian": "Critico",
        "polish": "Krytyczny", "czech": "Kritická",
    },
    "POC_LogLevel_Off": {
        "japanese": "オフ", "korean": "끄기", "chinese": "关闭", "russian": "Отключено", "german": "Aus",
        "french": "Désactivé", "spanish": "Desactivado", "italian": "Disattivato", "polish": "Wyłączone", "czech": "Vypnuto",
    },
    "POC_HelpLogLevel": {
        "japanese": "即座に適用されます。ログは Documents\\My Games\\Skyrim Special Edition\\SKSE\\PotionOfClarity.log にあります。",
        "korean": "즉시 적용됩니다. 로그는 Documents\\My Games\\Skyrim Special Edition\\SKSE\\PotionOfClarity.log 에 있습니다.",
        "chinese": "立即生效。日志位于 Documents\\My Games\\Skyrim Special Edition\\SKSE\\PotionOfClarity.log。",
        "russian": "Применяется немедленно. Журнал находится здесь: Documents\\My Games\\Skyrim Special Edition\\SKSE\\PotionOfClarity.log.",
        "german": "Wird sofort angewendet. Das Log liegt unter Documents\\My Games\\Skyrim Special Edition\\SKSE\\PotionOfClarity.log.",
        "french": "S'applique immédiatement. Le journal se trouve dans Documents\\My Games\\Skyrim Special Edition\\SKSE\\PotionOfClarity.log.",
        "spanish": "Se aplica de inmediato. El registro está en Documents\\My Games\\Skyrim Special Edition\\SKSE\\PotionOfClarity.log.",
        "italian": "Si applica immediatamente. Il log si trova in Documents\\My Games\\Skyrim Special Edition\\SKSE\\PotionOfClarity.log.",
        "polish": "Stosowane natychmiast. Log znajduje się w Documents\\My Games\\Skyrim Special Edition\\SKSE\\PotionOfClarity.log.",
        "czech": "Použije se okamžitě. Log je v Documents\\My Games\\Skyrim Special Edition\\SKSE\\PotionOfClarity.log.",
    },
    "POC_SaveBtn": {
        "japanese": "保存", "korean": "저장", "chinese": "保存", "russian": "Сохранить", "german": "Speichern",
        "french": "Enregistrer", "spanish": "Guardar", "italian": "Salva", "polish": "Zapisz", "czech": "Uložit",
    },
    "POC_StatusSaving": {
        "japanese": "保存中...", "korean": "저장 중...", "chinese": "正在保存...", "russian": "Сохранение...",
        "german": "Wird gespeichert...", "french": "Enregistrement...", "spanish": "Guardando...",
        "italian": "Salvataggio...", "polish": "Zapisywanie...", "czech": "Ukládání...",
    },
    "POC_StatusSaved": {
        "japanese": "設定を保存しました。", "korean": "설정을 저장했습니다.", "chinese": "设置已保存。",
        "russian": "Настройки сохранены.", "german": "Einstellungen gespeichert.", "french": "Paramètres enregistrés.",
        "spanish": "Ajustes guardados.", "italian": "Impostazioni salvate.", "polish": "Ustawienia zapisane.",
        "czech": "Nastavení uložena.",
    },
    "POC_StatusSaveFail": {
        "japanese": "INIの書き込みに失敗しました。理由はログを確認してください。",
        "korean": "INI를 쓸 수 없습니다. 이유는 로그를 확인하세요.",
        "chinese": "无法写入 INI。请查看日志了解原因。",
        "russian": "Не удалось записать INI. Причина — в журнале.",
        "german": "Die INI konnte nicht geschrieben werden. Der Grund steht im Log.",
        "french": "Impossible d'écrire l'INI. Voyez le journal pour la raison.",
        "spanish": "No se pudo escribir el INI. Consulta el registro para saber por qué.",
        "italian": "Impossibile scrivere l'INI. Consulta il log per il motivo.",
        "polish": "Nie można zapisać INI. Sprawdź log, aby dowiedzieć się dlaczego.",
        "czech": "Nelze zapsat INI. Důvod najdete v logu.",
    },
    "POC_HelpSave": {
        "japanese": "このページのすべての設定をプラグインのINIに書き込み、再起動後も残します。",
        "korean": "이 페이지의 모든 설정을 플러그인의 INI에 기록하여 재시작 후에도 유지되게 합니다.",
        "chinese": "将此页面的所有设置写入插件的 INI,使其在重启后仍然保留。",
        "russian": "Записывает каждую настройку этой страницы в INI плагина, чтобы она сохранилась после перезапуска.",
        "german": "Schreibt jede Einstellung dieser Seite in die INI des Plugins, damit sie einen Neustart überlebt.",
        "french": "Écrit chaque paramètre de cette page dans le fichier INI du plugin afin qu'il survive à un redémarrage.",
        "spanish": "Escribe cada ajuste de esta página en el INI del plugin para que sobreviva a un reinicio.",
        "italian": "Scrive ogni impostazione di questa pagina nell'INI del plugin, così sopravvive a un riavvio.",
        "polish": "Zapisuje każde ustawienie tej strony do pliku INI wtyczki, dzięki czemu przetrwa restart.",
        "czech": "Zapíše každé nastavení této stránky do INI pluginu, aby přežilo restart.",
    },
    "POC_ReloadBtn": {
        "japanese": "INIから再読み込み", "korean": "INI에서 다시 불러오기", "chinese": "从 INI 重新加载",
        "russian": "Перезагрузить из INI", "german": "Aus INI neu laden", "french": "Recharger depuis l'INI",
        "spanish": "Recargar desde el INI", "italian": "Ricarica dall'INI", "polish": "Wczytaj ponownie z INI",
        "czech": "Znovu načíst z INI",
    },
    "POC_StatusReloading": {
        "japanese": "再読み込み中...", "korean": "다시 불러오는 중...", "chinese": "正在重新加载...",
        "russian": "Перезагрузка...", "german": "Wird neu geladen...", "french": "Rechargement...",
        "spanish": "Recargando...", "italian": "Ricaricamento...", "polish": "Wczytywanie ponowne...",
        "czech": "Znovu se načítá...",
    },
    "POC_StatusReloaded": {
        "japanese": "INIから設定を再読み込みしました。", "korean": "INI에서 설정을 다시 불러왔습니다.",
        "chinese": "已从 INI 重新加载设置。", "russian": "Настройки перезагружены из INI.",
        "german": "Einstellungen aus der INI neu geladen.", "french": "Paramètres rechargés depuis l'INI.",
        "spanish": "Ajustes recargados desde el INI.", "italian": "Impostazioni ricaricate dall'INI.",
        "polish": "Ustawienia wczytane ponownie z INI.", "czech": "Nastavení znovu načtena z INI.",
    },
    "POC_StatusReloadFail": {
        "japanese": "INIの読み込みに失敗しました。理由はログを確認してください。",
        "korean": "INI를 읽을 수 없습니다. 이유는 로그를 확인하세요.",
        "chinese": "无法读取 INI。请查看日志了解原因。",
        "russian": "Не удалось прочитать INI. Причина — в журнале.",
        "german": "Die INI konnte nicht gelesen werden. Der Grund steht im Log.",
        "french": "Impossible de lire l'INI. Voyez le journal pour la raison.",
        "spanish": "No se pudo leer el INI. Consulta el registro para saber por qué.",
        "italian": "Impossibile leggere l'INI. Consulta il log per il motivo.",
        "polish": "Nie można odczytać INI. Sprawdź log, aby dowiedzieć się dlaczego.",
        "czech": "Nelze přečíst INI. Důvod najdete v logu.",
    },
    "POC_HelpReload": {
        "japanese": "最後の保存以降にここで行った変更をすべて捨て、INIをディスクから再読み込みします。",
        "korean": "마지막 저장 이후 여기서 만든 변경 사항을 모두 버리고 INI를 디스크에서 다시 읽습니다.",
        "chinese": "放弃自上次保存以来在此处所做的任何更改,并从磁盘重新读取 INI。",
        "russian": "Отбрасывает все изменения, сделанные здесь с последнего сохранения, и заново считывает INI с диска.",
        "german": "Verwirft jede hier seit dem letzten Speichern vorgenommene Änderung und liest die INI erneut von der Festplatte.",
        "french": "Annule tout changement effectué ici depuis le dernier enregistrement et relit l'INI depuis le disque.",
        "spanish": "Descarta cualquier cambio hecho aquí desde el último guardado y vuelve a leer el INI desde el disco.",
        "italian": "Scarta ogni modifica fatta qui dall'ultimo salvataggio e rilegge l'INI dal disco.",
        "polish": "Odrzuca wszelkie zmiany wprowadzone tutaj od ostatniego zapisu i ponownie odczytuje INI z dysku.",
        "czech": "Zahodí všechny změny provedené zde od posledního uložení a znovu načte INI z disku.",
    },
    "POC_RestoreBtn": {
        "japanese": "既定値に戻す", "korean": "기본값으로 복원", "chinese": "恢复默认值", "russian": "Восстановить умолч.",
        "german": "Standard wiederherstellen", "french": "Restaurer les valeurs par défaut",
        "spanish": "Restaurar valores predeterminados", "italian": "Ripristina i valori predefiniti",
        "polish": "Przywróć wartości domyślne", "czech": "Obnovit výchozí",
    },
    "POC_StatusRestored": {
        "japanese": "既定値に戻しました。保存を押して確定してください。",
        "korean": "기본값으로 복원했습니다. 유지하려면 저장을 누르세요.",
        "chinese": "已恢复默认值。按保存以保留它们。",
        "russian": "Значения по умолчанию восстановлены. Нажмите «Сохранить», чтобы закрепить их.",
        "german": "Standardwerte wiederherstellt. Drücke Speichern, um sie zu behalten.",
        "french": "Valeurs par défaut restaurées. Appuyez sur Enregistrer pour les conserver.",
        "spanish": "Valores predeterminados restaurados. Pulsa Guardar para conservarlos.",
        "italian": "Valori predefiniti ripristinati. Premi Salva per conservarli.",
        "polish": "Przywrócono wartości domyślne. Naciśnij Zapisz, aby je zachować.",
        "czech": "Výchozí hodnoty obnoveny. Stiskněte Uložit, abyste je zachovali.",
    },
    "POC_HelpRestore": {
        "japanese": "新規インストール時の値にすべての設定を戻します。保存ボタンを押すまで何も書き込まれません。",
        "korean": "새로 설치했을 때의 값으로 모든 설정을 되돌립니다. 저장을 누르기 전까지는 아무것도 기록되지 않습니다.",
        "chinese": "将每个设置恢复为全新安装时的值。在你按下保存之前,不会写入任何内容。",
        "russian": "Возвращает каждую настройку к значению, которое было бы при свежей установке. Ничего не записывается, пока вы не нажмёте «Сохранить».",
        "german": "Setzt jede Einstellung auf den Wert zurück, den sie bei einer frischen Installation hätte. Nichts wird geschrieben, bis du auf Speichern drückst.",
        "french": "Remet chaque paramètre à sa valeur d'une installation neuve. Rien n'est écrit avant que vous n'appuyiez sur Enregistrer.",
        "spanish": "Devuelve cada ajuste al valor que tendría en una instalación nueva. No se escribe nada hasta que pulses Guardar.",
        "italian": "Riporta ogni impostazione al valore che avrebbe in un'installazione nuova. Non viene scritto nulla finché non premi Salva.",
        "polish": "Przywraca każde ustawienie do wartości z nowej instalacji. Nic nie zostaje zapisane, dopóki nie naciśniesz Zapisz.",
        "czech": "Vrátí každé nastavení na hodnotu, jakou by mělo při čerstvé instalaci. Nic se nezapíše, dokud nestisknete Uložit.",
    },
    "POC_Intro": {
        "japanese": "変更はすぐに適用されます。次回プレイ時にも残すには保存を押してください。",
        "korean": "변경 사항은 즉시 적용됩니다. 다음에 플레이할 때도 유지하려면 저장을 누르세요.",
        "chinese": "更改会立即生效。按保存可在下次游玩时保留它们。",
        "russian": "Изменения применяются сразу же. Нажмите «Сохранить», чтобы они остались и в следующий раз.",
        "german": "Änderungen wirken sofort. Drücke Speichern, um sie für das nächste Mal zu behalten.",
        "french": "Les changements s'appliquent dès que vous les faites. Appuyez sur Enregistrer pour les garder la prochaine fois.",
        "spanish": "Los cambios se aplican en cuanto los haces. Pulsa Guardar para conservarlos la próxima vez que juegues.",
        "italian": "Le modifiche si applicano non appena le fai. Premi Salva per conservarle per la prossima partita.",
        "polish": "Zmiany obowiązują natychmiast po ich wprowadzeniu. Naciśnij Zapisz, aby zachować je na następną rozgrywkę.",
        "czech": "Změny se použijí okamžitě, jak je provedete. Stiskněte Uložit, abyste je zachovali pro příští hraní.",
    },
}


def write_translation_file(path, entries):
    lines = []
    for key, text in entries.items():
        escaped = text.replace("\r\n", "\n").replace("\n", "\\n")
        lines.append(f"${key}\t{escaped}")
    body = "\r\n".join(lines) + "\r\n"
    data = b"\xff\xfe" + body.encode("utf-16-le")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "wb") as f:
        f.write(data)


def main():
    keys, order = read_keys()
    missing_translation_keys = [k for k in order if k not in TRANSLATIONS]
    if missing_translation_keys:
        raise RuntimeError(f"no translations held for keys found in source: {missing_translation_keys}")
    extra_translation_keys = [k for k in TRANSLATIONS if k not in keys]
    if extra_translation_keys:
        raise RuntimeError(f"translations held for keys no longer in source: {extra_translation_keys}")

    out_dir = os.path.join(REPO, "dist", "Interface", "Translations")
    english = {k: keys[k] for k in order}
    write_translation_file(os.path.join(out_dir, "PotionOfClarity_english.txt"), english)
    print(f"english: {len(english)} keys")

    for lang in LANGS[1:]:
        translated = {k: TRANSLATIONS[k][lang] for k in order}
        write_translation_file(os.path.join(out_dir, f"PotionOfClarity_{lang}.txt"), translated)
        print(f"{lang}: {len(translated)} keys written")


if __name__ == "__main__":
    main()
