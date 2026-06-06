local SOUNDS = "/scripts/imac-ethos-caller/sounds/"

local function loadYear(name)
    local chunk = loadfile("SCRIPTS:/imac-ethos-caller/sequences/" .. name .. ".lua")
    return chunk and chunk() or nil
end

-- To add a new season: create sequences/<year>.lua and add a loadYear line below.
local YEARS = {
    loadYear("2026"),
}

-- Flat list of all year+class combinations, built once at load time.
-- Stored as seqIdx in widget state so the configure choice field is simple and reactive.
local SEQUENCES = {}
local SEQ_CHOICES = {}
for _, yr in ipairs(YEARS) do
    for _, cls in ipairs(yr.classes) do
        SEQUENCES[#SEQUENCES + 1] = {year = yr.year, cls = cls}
        SEQ_CHOICES[#SEQ_CHOICES + 1] = {yr.year .. "  " .. cls.name, #SEQUENCES}
    end
end

local function currentSeq(widget)
    return SEQUENCES[widget.seqIdx] or SEQUENCES[1]
end

local function name(widget)
    return "IMAC Caller"
end

local function create()
    return {
        seqIdx     = 1,
        mnvrIdx    = 0,
        trigSwitch = system.getSource({category=CATEGORY_SWITCH_POSITION, member=23}),
        rstSwitch  = system.getSource({category=CATEGORY_SWITCH_POSITION, member=29}),
        repSwitch  = system.getSource({category=CATEGORY_SWITCH_POSITION, member=26}),
        trigActive = false,
        rstActive  = false,
        repActive  = false,
    }
end

local function playMnvr(widget, idx)
    local s = currentSeq(widget)
    if idx >= 1 and idx <= #s.cls.seq then
        system.playFile(SOUNDS .. s.year .. "/" .. s.cls.key .. "/" .. s.cls.seq[idx].file .. ".wav")
    end
end

local function resetSeq(widget)
    local s = currentSeq(widget)
    widget.mnvrIdx = 0
    system.playFile(SOUNDS .. s.year .. "/" .. s.cls.key .. "/rst.wav")
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
        lcd.drawText(bx + bw / 2, by + bh * 0.45, "Ready", CENTERED)
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
    local line = form.addLine("Routine")
    form.addChoiceField(line, nil, SEQ_CHOICES,
        function() return widget.seqIdx end,
        function(v) widget.seqIdx = v; widget.mnvrIdx = 0 end)

    line = form.addLine("Trigger Switch")
    form.addSwitchField(line, form.getFieldSlots(line)[0],
        function() return widget.trigSwitch end,
        function(v) widget.trigSwitch = v end)

    line = form.addLine("Repeat Switch")
    form.addSwitchField(line, form.getFieldSlots(line)[0],
        function() return widget.repSwitch end,
        function(v) widget.repSwitch = v end)

    line = form.addLine("Reset Switch")
    form.addSwitchField(line, form.getFieldSlots(line)[0],
        function() return widget.rstSwitch end,
        function(v) widget.rstSwitch = v end)
end

local function read(widget)
    widget.seqIdx    = storage.read("seqIdx")    or widget.seqIdx
    widget.trigSwitch = storage.read("trigSwitch") or widget.trigSwitch
    widget.rstSwitch  = storage.read("rstSwitch")  or widget.rstSwitch
    widget.repSwitch  = storage.read("repSwitch")  or widget.repSwitch
end

local function write(widget)
    storage.write("seqIdx",    widget.seqIdx)
    storage.write("trigSwitch", widget.trigSwitch)
    storage.write("rstSwitch",  widget.rstSwitch)
    storage.write("repSwitch",  widget.repSwitch)
end

local function init()
    system.registerWidget({
        key       = "imaccal",
        name      = name,
        create    = create,
        paint     = paint,
        wakeup    = wakeup,
        configure = configure,
        read      = read,
        write     = write,
    })
end

return {init = init}
