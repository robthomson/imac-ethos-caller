-- Runtime i18n loader.
--
-- Loads all bundled locale tables and provides lookup/fallback helpers.
-- Modeled on the StabilizerConfig i18n pattern (system.getLocale() + per-locale table).

local BASE = "SCRIPTS:/imac-caller/i18n/"

local SUPPORTED = {"en", "fr", "de", "nl", "cz"}
local ALIASES = {cs = "cz"}

local locales = {}
for _, lang in ipairs(SUPPORTED) do
    local chunk = loadfile(BASE .. lang .. ".lua")
    locales[lang] = chunk and chunk() or {}
end

local function resolveLocale(lang)
    if type(lang) == "string" then
        lang = lang:sub(1, 2):lower()
        lang = ALIASES[lang] or lang
        if locales[lang] then return lang end
    end
    return "en"
end

local function translate(lang, key)
    local table_ = locales[lang] or locales.en
    return table_[key] or locales.en[key] or key
end

return {
    SUPPORTED     = SUPPORTED,
    resolveLocale = resolveLocale,
    translate     = translate,
}
