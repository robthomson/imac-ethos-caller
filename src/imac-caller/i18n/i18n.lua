-- Runtime i18n loader.
--
-- Loads all bundled locale tables and provides lookup/fallback helpers.
-- Modeled on the StabilizerConfig i18n pattern (system.getLocale() + per-locale table).

local BASE = "SCRIPTS:/imac-caller/i18n/"

local SUPPORTED = {"en", "fr", "de", "nl", "cs", "es", "he", "it", "no", "pl", "pt-br", "zh-cn"}

local locales = {}
for _, lang in ipairs(SUPPORTED) do
    local chunk = loadfile(BASE .. lang .. ".lua")
    locales[lang] = chunk and chunk() or {}
end

local function resolveLocale(lang)
    if type(lang) == "string" then
        lang = lang:lower()
        if locales[lang] then return lang end
        local short = lang:sub(1, 2)
        if locales[short] then return short end
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
