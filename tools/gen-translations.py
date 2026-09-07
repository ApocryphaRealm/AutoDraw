# -*- coding: utf-8 -*-
"""gen-translations.py - builds the eleven AutoDraw_<language>.txt files.

The English key list is extracted from the PATCHED source/UI.cpp by regex on
strings::TR("KEY", "text") so it can never drift from the code. The other ten languages are
this project's own translations of that list, held below as parallel dictionaries.

Writes REPO/dist/Interface/Translations/AutoDraw_<language>.txt for english + the owner's ten
languages (UTF-16LE with a BOM, one "$key<TAB>text" per line, literal "\\n" for an embedded line
break, CRLF records - the SKSE/SkyUI shape AMF's own Strings.cpp reads).

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
# Auto Draw) stay untranslated; file names (AutoDraw.log, the INI) stay untranslated inside the
# translated sentence, matching the SkyHudMenu reference (skyhud.txt kept literal there too).
# ------------------------------------------------------------------------------------------------
TRANSLATIONS = {
    "AD_HelpMark": {
        "japanese": "(?)", "korean": "(?)", "chinese": "(?)", "russian": "(?)", "german": "(?)",
        "french": "(?)", "spanish": "(?)", "italian": "(?)", "polish": "(?)", "czech": "(?)",
    },
    "AD_NudgeArrows": {
        "japanese": "<-->", "korean": "<-->", "chinese": "<-->", "russian": "<-->", "german": "<-->",
        "french": "<-->", "spanish": "<-->", "italian": "<-->", "polish": "<-->", "czech": "<-->",
    },
    "AD_Automation": {
        "japanese": "オートメーション", "korean": "자동화", "chinese": "自动化", "russian": "Автоматизация",
        "german": "Automatisierung", "french": "Automatisation", "spanish": "Automatización",
        "italian": "Automazione", "polish": "Automatyzacja", "czech": "Automatizace",
    },
    "AD_AutoDraw": {
        "japanese": "自動抜刀", "korean": "자동 무기 뽑기", "chinese": "自动拔出武器", "russian": "Автоматически достать",
        "german": "Automatisch ziehen", "french": "Dégainage automatique", "spanish": "Desenvainado automático",
        "italian": "Sfoderamento automatico", "polish": "Automatyczne wyjmowanie", "czech": "Automatické tažení",
    },
    "AD_HelpAutoDraw": {
        "japanese": "戦闘で何かがあなたを対象にした瞬間、武器や魔法を構えます。",
        "korean": "전투에서 무언가가 당신을 대상으로 하는 즉시 무기나 마법을 뽑습니다.",
        "chinese": "当有目标在战斗中锁定你时,立即拔出你的武器或魔法。",
        "russian": "Достаёт ваше оружие или магию в тот момент, когда что-то нацеливается на вас в бою.",
        "german": "Zieht deine Waffe oder Magie in dem Moment, in dem dich im Kampf etwas ins Visier nimmt.",
        "french": "Dégaine votre arme ou votre magie dès qu'une cible vous vise en combat.",
        "spanish": "Desenvaina tu arma o magia en el instante en que algo te apunta en combate.",
        "italian": "Sfodera l'arma o la magia nell'istante in cui qualcosa ti punta durante il combattimento.",
        "polish": "Wyjmuje twoją broń lub magię w chwili, gdy coś celuje w tobie w walce.",
        "czech": "Vytáhne vaši zbraň nebo magii ve chvíli, kdy vás v boji něco zacílí.",
    },
    "AD_AutoSheathe": {
        "japanese": "自動納刀", "korean": "자동 무기 집어넣기", "chinese": "自动收起武器", "russian": "Автоматически убрать",
        "german": "Automatisch einstecken", "french": "Rangement automatique", "spanish": "Enfundado automático",
        "italian": "Rinfodero automatico", "polish": "Automatyczne chowanie", "czech": "Automatické schování",
    },
    "AD_HelpAutoSheathe": {
        "japanese": "戦闘を離れてから、または手動で構えてから一定の遅延の後に、武器や魔法を収めます。",
        "korean": "전투를 벗어난 후, 또는 직접 무기를 뽑은 후 일정 시간이 지나면 무기나 마법을 집어넣습니다.",
        "chinese": "在你脱离战斗后,或手动拔出后,经过设定的延迟时间收起你的武器或魔法。",
        "russian": "Убирает ваше оружие или магию через заданную задержку после выхода из боя или после того, как вы достали их вручную.",
        "german": "Steckt deine Waffe oder Magie nach einer festgelegten Verzögerung ein, nachdem du den Kampf verlassen oder sie manuell gezogen hast.",
        "french": "Range votre arme ou votre magie après un délai défini, une fois le combat terminé ou après un dégainage manuel.",
        "spanish": "Enfunda tu arma o magia tras un retraso fijo después de salir del combate o de desenvainarla manualmente.",
        "italian": "Rinfodera l'arma o la magia dopo un ritardo prefissato quando lasci il combattimento o la sfoderi manualmente.",
        "polish": "Chowa twoją broń lub magię po ustalonym czasie od wyjścia z walki lub od ręcznego wyjęcia.",
        "czech": "Schová vaši zbraň nebo magii po nastavené prodlevě po opuštění boje nebo po ručním vytažení.",
    },
    "AD_SheatheDelay": {
        "japanese": "納刀までの遅延", "korean": "무기 집어넣기 지연", "chinese": "收起延迟", "russian": "Задержка перед убиранием",
        "german": "Einsteck-Verzögerung", "french": "Délai de rangement", "spanish": "Retraso de enfundado",
        "italian": "Ritardo di rinfodero", "polish": "Zwłoka chowania", "czech": "Prodleva schování",
    },
    "AD_HelpSheatheDelay": {
        "japanese": "戦闘を離れてから、または手動で構えてから、強制的に納刀するまでの待機時間。攻撃、防御、空中にいること、再度戦闘に入ることで待機時間はリセットされます。",
        "korean": "전투를 벗어난 후, 또는 직접 무기를 뽑은 후 강제로 무기를 집어넣기까지 대기하는 시간입니다. 공격, 방어, 공중에 있는 것, 다시 전투에 들어가는 것은 대기 시간을 다시 시작시킵니다.",
        "chinese": "脱离战斗后,或手动拔出武器后,强制收起前的等待时间。攻击、格挡、处于空中或重新进入战斗都会重新开始等待。",
        "russian": "Сколько ждать после выхода из боя или после того, как вы достали оружие вручную, перед принудительным убиранием. Атака, блокирование, полёт в воздухе или повторный вход в бой перезапускают отсчёт.",
        "german": "Wie lange gewartet wird, nachdem du den Kampf verlassen oder manuell gezogen hast, bevor das erzwungene Einstecken erfolgt. Angreifen, Blocken, in der Luft sein oder erneut in den Kampf eintreten setzen die Wartezeit zurück.",
        "french": "Délai d'attente après avoir quitté le combat, ou après un dégainage manuel, avant le rangement forcé. Attaquer, bloquer, être en l'air ou revenir en combat relance l'attente.",
        "spanish": "Cuánto esperar tras salir del combate, o tras desenvainar manualmente, antes del enfundado forzado. Atacar, bloquear, estar en el aire o volver a entrar en combate reinicia la espera.",
        "italian": "Quanto attendere dopo aver lasciato il combattimento, o dopo aver sfoderato manualmente, prima del rinfodero forzato. Attaccare, parare, essere in aria o rientrare in combattimento riavvia l'attesa.",
        "polish": "Jak długo czekać po wyjściu z walki lub po ręcznym wyjęciu broni, przed wymuszonym chowaniem. Atakowanie, blokowanie, bycie w powietrzu lub ponowne wejście do walki zaczyna odliczanie od nowa.",
        "czech": "Jak dlouho čekat po opuštění boje nebo po ručním vytažení, než dojde k vynucenému schování. Útok, blokování, vznášení se ve vzduchu nebo opětovný vstup do boje čekání znovu spustí.",
    },
    "AD_ExemptBound": {
        "japanese": "束縛武器は抜いたままにする", "korean": "속박된 무기는 뽑은 상태로 유지",
        "chinese": "让束缚武器保持拔出状态", "russian": "Не убирать связанное оружие",
        "german": "Gebundene Waffen gezogen lassen", "french": "Laisser les armes liées dégainées",
        "spanish": "Dejar desenvainadas las armas ligadas", "italian": "Lascia sfoderate le armi legate",
        "polish": "Nie chowaj związanej broni", "czech": "Nechat spřízněné zbraně vytažené",
    },
    "AD_HelpExemptBound": {
        "japanese": "束縛(召喚)武器を構えている間は強制納刀をスキップします。早期に解除されることはありません - 束縛武器自身の持続時間が切れるか、自分で納刀したときに終わります。",
        "korean": "속박(소환) 무기를 들고 있는 동안 강제 무기 집어넣기를 건너뜁니다 - 이 무기는 조기에 사라지지 않으며, 자체 지속시간이 끝나거나 직접 집어넣을 때 끝납니다.",
        "chinese": "在持有束缚(召唤)武器时跳过强制收起 - 它不会提前解除,只会在其自身持续时间结束或你自己收起它时结束。",
        "russian": "Пропускает принудительное убирание, когда в руках связанное (призванное) оружие, чтобы оно не исчезало раньше времени - оно всё равно закончится по истечении своей длительности или когда вы убёрете его сами.",
        "german": "Überspringt das erzwungene Einstecken, während eine gebundene (heraufbeschworene) Waffe gezogen ist, damit sie nicht vorzeitig verschwindet - sie endet weiterhin durch ihre eigene Dauer oder wenn du sie selbst einsteckst.",
        "french": "Ignore le rangement forcé tant qu'une arme liée (invoquée) est dégainée, afin qu'elle ne disparaisse pas trop tôt - elle prend fin par sa propre durée ou lorsque vous la rangez vous-même.",
        "spanish": "Omite el enfundado forzado mientras un arma ligada (conjurada) está desenvainada, para que no se disipe antes de tiempo - termina por su propia duración o cuando la enfundas tú mismo.",
        "italian": "Salta il rinfodero forzato mentre un'arma legata (evocata) è sfoderata, così non viene dissolta in anticipo - termina comunque per la sua durata o quando la rinfoderi tu stesso.",
        "polish": "Pomija wymuszone chowanie, gdy trzymana jest związana (przywołana) broń, dzięki czemu nie zniknie przedwcześnie - i tak zakończy się z upływem własnego czasu trwania lub gdy schowasz ją sam.",
        "czech": "Přeskočí vynucené schování, dokud je vytažena spřízněná (vyvolaná) zbraň, takže nezmizí předčasně - stejně skončí uplynutím vlastní doby trvání nebo když ji schováte sami.",
    },
    "AD_Debug": {
        "japanese": "デバッグ", "korean": "디버그", "chinese": "调试", "russian": "Отладка", "german": "Debug",
        "french": "Débogage", "spanish": "Depuración", "italian": "Debug", "polish": "Debugowanie", "czech": "Ladění",
    },
    "AD_LogLevel": {
        "japanese": "ログレベル", "korean": "로그 레벨", "chinese": "日志级别", "russian": "Уровень журнала",
        "german": "Protokollstufe", "french": "Niveau de journal", "spanish": "Nivel de registro",
        "italian": "Livello di log", "polish": "Poziom logowania", "czech": "Úroveň logování",
    },
    "AD_HelpLogLevel": {
        "japanese": "即座に適用されます。ログは Documents\\My Games\\Skyrim Special Edition\\SKSE\\AutoDraw.log にあります。バグを報告する前に、これを Trace か Debug に設定してください。",
        "korean": "즉시 적용됩니다. 로그는 Documents\\My Games\\Skyrim Special Edition\\SKSE\\AutoDraw.log 에 있습니다. 버그를 보고하기 전에 이 값을 Trace나 Debug로 설정하세요.",
        "chinese": "立即生效。日志位于 Documents\\My Games\\Skyrim Special Edition\\SKSE\\AutoDraw.log。在重现要报告的问题之前,请将其设置为 Trace 或 Debug。",
        "russian": "Применяется немедленно. Журнал находится здесь: Documents\\My Games\\Skyrim Special Edition\\SKSE\\AutoDraw.log. Установите Trace или Debug перед тем, как воспроизводить ошибку, о которой вы сообщаете.",
        "german": "Wird sofort angewendet. Das Log liegt unter Documents\\My Games\\Skyrim Special Edition\\SKSE\\AutoDraw.log. Stelle dies auf Trace oder Debug, bevor du einen Fehler reproduzierst, den du melden willst.",
        "french": "S'applique immédiatement. Le journal se trouve dans Documents\\My Games\\Skyrim Special Edition\\SKSE\\AutoDraw.log. Réglez ceci sur Trace ou Debug avant de reproduire un bug que vous comptez signaler.",
        "spanish": "Se aplica de inmediato. El registro está en Documents\\My Games\\Skyrim Special Edition\\SKSE\\AutoDraw.log. Ponlo en Trace o Debug antes de reproducir un error que vayas a reportar.",
        "italian": "Si applica immediatamente. Il log si trova in Documents\\My Games\\Skyrim Special Edition\\SKSE\\AutoDraw.log. Impostalo su Trace o Debug prima di riprodurre un bug che intendi segnalare.",
        "polish": "Stosowane natychmiast. Log znajduje się w Documents\\My Games\\Skyrim Special Edition\\SKSE\\AutoDraw.log. Ustaw to na Trace lub Debug przed odtworzeniem błędu, który zamierzasz zgłosić.",
        "czech": "Použije se okamžitě. Log je v Documents\\My Games\\Skyrim Special Edition\\SKSE\\AutoDraw.log. Před reprodukcí chyby, kterou chcete nahlásit, nastavte toto na Trace nebo Debug.",
    },
    "AD_LogLevel_Trace": {
        "japanese": "トレース", "korean": "추적", "chinese": "跟踪", "russian": "Трассировка", "german": "Trace",
        "french": "Trace", "spanish": "Trace", "italian": "Trace", "polish": "Trace", "czech": "Trace",
    },
    "AD_LogLevel_Debug": {
        "japanese": "デバッグ", "korean": "디버그", "chinese": "调试", "russian": "Отладка", "german": "Debug",
        "french": "Débogage", "spanish": "Depuración", "italian": "Debug", "polish": "Debugowanie", "czech": "Ladění",
    },
    "AD_LogLevel_Info": {
        "japanese": "情報", "korean": "정보", "chinese": "信息", "russian": "Информация", "german": "Info",
        "french": "Infos", "spanish": "Información", "italian": "Informazioni", "polish": "Informacje", "czech": "Informace",
    },
    "AD_LogLevel_Warning": {
        "japanese": "警告", "korean": "경고", "chinese": "警告", "russian": "Предупреждение", "german": "Warnung",
        "french": "Avertissement", "spanish": "Advertencia", "italian": "Avviso", "polish": "Ostrzeżenie", "czech": "Varování",
    },
    "AD_LogLevel_Error": {
        "japanese": "エラー", "korean": "오류", "chinese": "错误", "russian": "Ошибка", "german": "Fehler",
        "french": "Erreur", "spanish": "Error", "italian": "Errore", "polish": "Błąd", "czech": "Chyba",
    },
    "AD_LogLevel_Critical": {
        "japanese": "重大", "korean": "치명적", "chinese": "严重", "russian": "Критическая",
        "german": "Kritisch", "french": "Critique", "spanish": "Crítico", "italian": "Critico",
        "polish": "Krytyczny", "czech": "Kritická",
    },
    "AD_LogLevel_Off": {
        "japanese": "オフ", "korean": "끄기", "chinese": "关闭", "russian": "Отключено", "german": "Aus",
        "french": "Désactivé", "spanish": "Desactivado", "italian": "Disattivato", "polish": "Wyłączone", "czech": "Vypnuto",
    },
    "AD_SaveBtn": {
        "japanese": "保存", "korean": "저장", "chinese": "保存", "russian": "Сохранить", "german": "Speichern",
        "french": "Enregistrer", "spanish": "Guardar", "italian": "Salva", "polish": "Zapisz", "czech": "Uložit",
    },
    "AD_HelpSave": {
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
    "AD_ReloadBtn": {
        "japanese": "INIから再読み込み", "korean": "INI에서 다시 불러오기", "chinese": "从 INI 重新加载",
        "russian": "Перезагрузить из INI", "german": "Aus INI neu laden", "french": "Recharger depuis l'INI",
        "spanish": "Recargar desde el INI", "italian": "Ricarica dall'INI", "polish": "Wczytaj ponownie z INI",
        "czech": "Znovu načíst z INI",
    },
    "AD_HelpReload": {
        "japanese": "最後の保存以降にここで行った変更をすべて捨て、INIをディスクから再読み込みします。手動で編集したファイルの変更も反映されます。",
        "korean": "마지막 저장 이후 여기서 만든 변경 사항을 모두 버리고 INI를 디스크에서 다시 읽습니다. 파일을 직접 편집한 내용도 반영됩니다.",
        "chinese": "放弃自上次保存以来在此处所做的任何更改,并从磁盘重新读取 INI。也会读取手动对文件所做的编辑。",
        "russian": "Отбрасывает все изменения, сделанные здесь с последнего сохранения, и заново считывает INI с диска. Также подхватывает правки, сделанные в файле вручную.",
        "german": "Verwirft jede hier seit dem letzten Speichern vorgenommene Änderung und liest die INI erneut von der Festplatte. Übernimmt auch Änderungen, die von Hand an der Datei vorgenommen wurden.",
        "french": "Annule tout changement effectué ici depuis le dernier enregistrement et relit l'INI depuis le disque. Reprend aussi les modifications faites à la main dans le fichier.",
        "spanish": "Descarta cualquier cambio hecho aquí desde el último guardado y vuelve a leer el INI desde el disco. También recoge ediciones hechas a mano en el archivo.",
        "italian": "Scarta ogni modifica fatta qui dall'ultimo salvataggio e rilegge l'INI dal disco. Riprende anche le modifiche fatte a mano al file.",
        "polish": "Odrzuca wszelkie zmiany wprowadzone tutaj od ostatniego zapisu i ponownie odczytuje INI z dysku. Uwzględnia też zmiany wprowadzone w pliku ręcznie.",
        "czech": "Zahodí všechny změny provedené zde od posledního uložení a znovu načte INI z disku. Zohlední i úpravy provedené v souboru ručně.",
    },
    "AD_RestoreBtn": {
        "japanese": "既定値に戻す", "korean": "기본값으로 복원", "chinese": "恢复默认值", "russian": "Восстановить умолч.",
        "german": "Standard wiederherstellen", "french": "Restaurer les valeurs par défaut",
        "spanish": "Restaurar valores predeterminados", "italian": "Ripristina i valori predefiniti",
        "polish": "Przywróć wartości domyślne", "czech": "Obnovit výchozí",
    },
    "AD_HelpRestore": {
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
    "AD_StatusSaving": {
        "japanese": "保存中...", "korean": "저장 중...", "chinese": "正在保存...", "russian": "Сохранение...",
        "german": "Wird gespeichert...", "french": "Enregistrement...", "spanish": "Guardando...",
        "italian": "Salvataggio...", "polish": "Zapisywanie...", "czech": "Ukládání...",
    },
    "AD_StatusSaved": {
        "japanese": "設定を保存しました。", "korean": "설정을 저장했습니다.", "chinese": "设置已保存。",
        "russian": "Настройки сохранены.", "german": "Einstellungen gespeichert.", "french": "Paramètres enregistrés.",
        "spanish": "Ajustes guardados.", "italian": "Impostazioni salvate.", "polish": "Ustawienia zapisane.",
        "czech": "Nastavení uložena.",
    },
    "AD_StatusSaveFail": {
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
    "AD_StatusReloading": {
        "japanese": "再読み込み中...", "korean": "다시 불러오는 중...", "chinese": "正在重新加载...",
        "russian": "Перезагрузка...", "german": "Wird neu geladen...", "french": "Rechargement...",
        "spanish": "Recargando...", "italian": "Ricaricamento...", "polish": "Wczytywanie ponowne...",
        "czech": "Znovu se načítá...",
    },
    "AD_StatusReloaded": {
        "japanese": "INIから設定を再読み込みしました。", "korean": "INI에서 설정을 다시 불러왔습니다.",
        "chinese": "已从 INI 重新加载设置。", "russian": "Настройки перезагружены из INI.",
        "german": "Einstellungen aus der INI neu geladen.", "french": "Paramètres rechargés depuis l'INI.",
        "spanish": "Ajustes recargados desde el INI.", "italian": "Impostazioni ricaricate dall'INI.",
        "polish": "Ustawienia wczytane ponownie z INI.", "czech": "Nastavení znovu načtena z INI.",
    },
    "AD_StatusReloadFail": {
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
    "AD_StatusRestored": {
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
    "AD_Intro": {
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
    write_translation_file(os.path.join(out_dir, "AutoDraw_english.txt"), english)
    print(f"english: {len(english)} keys")

    for lang in LANGS[1:]:
        translated = {k: TRANSLATIONS[k][lang] for k in order}
        write_translation_file(os.path.join(out_dir, f"AutoDraw_{lang}.txt"), translated)
        print(f"{lang}: {len(translated)} keys written")


if __name__ == "__main__":
    main()
