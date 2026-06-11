local function compileIfNeeded(source)
    if os.stat(source) then
        system.compile(source)
    end
end

local function loadChunk(path)
    local loader, err = loadfile(path)
    if loader then return loader end
    local compiledPath = path:gsub("%.lua$", ".luac")
    if compiledPath ~= path then
        local compiledLoader = loadfile(compiledPath)
        if compiledLoader then return compiledLoader end
    end
    error("failed to load '" .. path .. "': " .. tostring(err))
end

compileIfNeeded("widget_impl.lua")
compileIfNeeded("lazy.lua")

local lazy = loadChunk("lazy.lua")()

local function create()
    return {
        yearIdx    = 1,
        classIdx   = 1,
        mnvrIdx    = 0,
        trigSwitch = system.getSource({category=CATEGORY_SWITCH_POSITION, member=23}),
        rstSwitch  = system.getSource({category=CATEGORY_SWITCH_POSITION, member=29}),
        repSwitch  = system.getSource({category=CATEGORY_SWITCH_POSITION, member=26}),
        trigActive = false,
        rstActive  = false,
        repActive  = false,
        lang       = "auto",
    }
end

local widget = lazy.wrapModule(
    {
        key    = "imaccal",
        name   = "IMAC Caller",
        create = create,
    },
    "widget_impl.lua",
    {"paint", "wakeup", "configure", "read", "write"}
)

local function init()
    system.registerWidget(widget)
end

return {init = init}
