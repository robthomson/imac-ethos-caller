local BASE   = "SCRIPTS:/imac-ethos-caller/"
local SOUNDS = BASE .. "seasons/"

local i18n = loadfile(BASE .. "i18n/i18n.lua")()

local function effectiveLang(widget)
    local lang = widget.lang or "auto"
    if lang ~= "auto" then return lang end
    return i18n.resolveLocale(system.getLocale())
end

local function loadYear(name)
    local chunk = loadfile(SOUNDS .. name .. "/sequences.lua")
    return chunk and chunk() or nil
end

local YEARS = {}
local entries = system.listFiles(SOUNDS)
if entries then
    table.sort(entries)
    for _, entry in ipairs(entries) do
        if entry:match("^%d%d%d%d$") then
            local yr = loadYear(entry)
            if yr then YEARS[#YEARS + 1] = yr end
        end
    end
end

local function currentSeq(widget)
    local yr  = YEARS[widget.yearIdx] or YEARS[1]
    local cls = yr.classes[widget.classIdx] or yr.classes[1]
    return {year = yr.year, cls = cls}
end

-- Voice variant folders per locale, matching the official Ethos audio pack
-- names used by rfsuite (e.g. "en/gb", "en/us", "fr/femme", "fr/homme").
-- Locales not listed here only ship a single "default" voice.
local LOCALE_VARIANTS = {
    en = {default = "gb", gb = true, us = true},
    fr = {default = "femme", femme = true, homme = true},
}

local function audioVoiceFolder()
    if type(system.getAudioVoice) ~= "function" then return "" end
    local av = system.getAudioVoice() or ""
    av = av:gsub("SD:", ""):gsub("RADIO:", ""):gsub("AUDIO:", ""):gsub("VOICE[1-4]:", ""):gsub("audio/", "")
    if av:sub(1, 1) == "/" then av = av:sub(2) end
    return av
end

-- Resolve which voice-pack variant folder to use for a locale, based on the
-- radio's currently selected audio voice, falling back to that locale's
-- default variant.
local function resolveVariant(lang)
    local variants = LOCALE_VARIANTS[lang]
    if not variants then return "default" end
    local avLang, avVariant = audioVoiceFolder():match("^([^/]+)/([^/]+)$")
    -- "default" is a fallback alias (e.g. variants.default == "gb"), not a
    -- folder of its own, so it must not be returned verbatim here.
    if avLang == lang and avVariant ~= "default" and variants[avVariant] then return avVariant end
    return variants.default
end

local function audioPath(widget, year, clsKey, file)
    local lang = effectiveLang(widget)
    if lang ~= "en" then
        local localized = SOUNDS .. year .. "/" .. clsKey .. "/" .. lang .. "/" .. resolveVariant(lang) .. "/" .. file .. ".wav"
        if os.stat(localized) then return localized end
    end
    return SOUNDS .. year .. "/" .. clsKey .. "/en/" .. resolveVariant("en") .. "/" .. file .. ".wav"
end

local function playMnvr(widget, idx)
    local s = currentSeq(widget)
    if idx >= 1 and idx <= #s.cls.seq then
        system.playFile(audioPath(widget, s.year, s.cls.key, s.cls.seq[idx].file))
    end
end

local function resetSeq(widget)
    local s = currentSeq(widget)
    widget.mnvrIdx = 0
    system.playFile(audioPath(widget, s.year, s.cls.key, "rst"))
    lcd.invalidate()
end

local function paint(widget)
    local s    = currentSeq(widget)
    local seq  = s.cls.seq
    local w, h = lcd.getWindowSize()

    if     h < 50  then lcd.font(FONT_XS)
    elseif h < 80  then lcd.font(FONT_S)
    elseif h > 170 then lcd.font(FONT_XL)
    else               lcd.font(FONT_STD) end

    local tw, th = lcd.getTextSize("")
    local bx, by = 4, th
    local bw, bh = w - 8, h - th - 4
    local total  = #seq
    local pct    = widget.mnvrIdx > 0
                   and math.floor(widget.mnvrIdx / total * 100) or 0
    local bar    = math.max(2, math.floor((bw - 2) * pct / 100) + 2)

    lcd.color(lcd.RGB(40, 40, 40))
    lcd.drawFilledRectangle(bx, by, bw, bh)
    lcd.color(lcd.RGB(0, 120, 200))
    lcd.drawFilledRectangle(bx, by, bar, bh)
    lcd.color(GREEN)
    lcd.drawRectangle(bx, by, bw, bh)
    lcd.color(WHITE)
    lcd.drawText(bx + bw / 2, by + bh * 0.10,
        s.year .. "  " .. s.cls.name, CENTERED)

    if widget.mnvrIdx > 0 then
        local m = seq[widget.mnvrIdx]
        lcd.drawText(bx + bw / 2, by + bh * 0.42,
            widget.mnvrIdx .. " / " .. total, CENTERED)
        lcd.drawText(bx + bw / 2, by + bh * 0.70, m.label, CENTERED)
    else
        lcd.drawText(bx + bw / 2, by + bh * 0.45, i18n.translate(effectiveLang(widget), "ready"), CENTERED)
    end
end

local function wakeup(widget)
    local trigNow = widget.trigSwitch and widget.trigSwitch:state() or false
    if trigNow and not widget.trigActive then
        local seq = currentSeq(widget).cls.seq
        widget.mnvrIdx = widget.mnvrIdx + 1
        if widget.mnvrIdx > #seq then
            resetSeq(widget)
        else
            playMnvr(widget, widget.mnvrIdx)
            lcd.invalidate()
        end
    end
    widget.trigActive = trigNow

    local rstNow = widget.rstSwitch and widget.rstSwitch:state() or false
    if rstNow and not widget.rstActive then
        resetSeq(widget)
    end
    widget.rstActive = rstNow

    local repNow = widget.repSwitch and widget.repSwitch:state() or false
    if repNow and not widget.repActive and widget.mnvrIdx > 0 then
        playMnvr(widget, widget.mnvrIdx)
    end
    widget.repActive = repNow
end

local function configure(widget)
    local lang = effectiveLang(widget)
    local t = function(key) return i18n.translate(lang, key) end

    local yearChoices = {}
    for i, yr in ipairs(YEARS) do
        yearChoices[i] = {yr.year, i}
    end

    local classField
    local line = form.addLine(t("year"))
    form.addChoiceField(line, nil, yearChoices,
        function() return widget.yearIdx end,
        function(v)
            widget.yearIdx  = v
            widget.classIdx = 1
            widget.mnvrIdx  = 0
            if classField then
                local choices = {}
                for i, cls in ipairs(YEARS[v].classes) do
                    choices[i] = {cls.name, i}
                end
                classField:values(choices)
            end
        end)

    local yr = YEARS[widget.yearIdx] or YEARS[1]
    local classChoices = {}
    for i, cls in ipairs(yr.classes) do
        classChoices[i] = {cls.name, i}
    end
    line = form.addLine(t("routine"))
    classField = form.addChoiceField(line, nil, classChoices,
        function() return widget.classIdx end,
        function(v) widget.classIdx = v; widget.mnvrIdx = 0 end)

    line = form.addLine(t("trigger_switch"))
    form.addSwitchField(line, form.getFieldSlots(line)[0],
        function() return widget.trigSwitch end,
        function(v) widget.trigSwitch = v end)

    line = form.addLine(t("repeat_switch"))
    form.addSwitchField(line, form.getFieldSlots(line)[0],
        function() return widget.repSwitch end,
        function(v) widget.repSwitch = v end)

    line = form.addLine(t("reset_switch"))
    form.addSwitchField(line, form.getFieldSlots(line)[0],
        function() return widget.rstSwitch end,
        function(v) widget.rstSwitch = v end)

    local langCodes   = {"auto"}
    local langChoices = {{t("lang_auto"), 1}}
    for i, code in ipairs(i18n.SUPPORTED) do
        langCodes[i + 1]   = code
        langChoices[i + 1] = {t("lang_" .. code), i + 1}
    end

    line = form.addLine(t("language"))
    form.addChoiceField(line, nil, langChoices,
        function()
            for i, code in ipairs(langCodes) do
                if code == (widget.lang or "auto") then return i end
            end
            return 1
        end,
        function(v) widget.lang = langCodes[v] end)
end

local function read(widget)
    widget.yearIdx    = storage.read("yearIdx")    or widget.yearIdx
    widget.classIdx   = storage.read("classIdx")   or widget.classIdx
    widget.trigSwitch = storage.read("trigSwitch") or widget.trigSwitch
    widget.rstSwitch  = storage.read("rstSwitch")  or widget.rstSwitch
    widget.repSwitch  = storage.read("repSwitch")  or widget.repSwitch
    widget.lang       = storage.read("lang")       or widget.lang
end

local function write(widget)
    storage.write("yearIdx",    widget.yearIdx)
    storage.write("classIdx",   widget.classIdx)
    storage.write("trigSwitch", widget.trigSwitch)
    storage.write("rstSwitch",  widget.rstSwitch)
    storage.write("repSwitch",  widget.repSwitch)
    storage.write("lang",       widget.lang)
end

return {
    paint     = paint,
    wakeup    = wakeup,
    configure = configure,
    read      = read,
    write     = write,
}
