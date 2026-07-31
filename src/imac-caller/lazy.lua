-- Reusable lazy-loading helper.
--
-- Each method wrapModule() wraps starts as a proxy that loads the target
-- module on first call, but that first call also replaces every wrapped
-- method on `base` with its real, direct implementation -- so every call
-- after that goes straight to the real function, with none of this
-- file's own indirection. Without this, wakeup()/paint() would pay an
-- extra table lookup and function call on every single tick for the
-- widget's entire remaining lifetime, not just until the module first
-- loads.

local lazy = {}
local cache = {}
local failed = {}

local function loadModule(path)
    if cache[path] then return cache[path] end
    if failed[path] then return nil end

    local loader, err = loadfile(path)
    if not loader then
        local compiledPath = path:gsub("%.lua$", ".luac")
        if compiledPath ~= path then
            local compiledLoader, compiledErr = loadfile(compiledPath)
            if compiledLoader then
                loader = compiledLoader
            else
                err = tostring(err) .. "; " .. tostring(compiledErr)
            end
        end
    end

    if not loader then
        failed[path] = true
        print("lazy: failed to load '" .. path .. "': " .. tostring(err))
        return nil
    end

    local ok, result = pcall(loader)
    if not ok then
        failed[path] = true
        print("lazy: '" .. path .. "' errored: " .. tostring(result))
        return nil
    end

    cache[path] = result
    return result
end

function lazy.wrapFunction(path, method)
    local module
    return function(...)
        if not module then
            module = loadModule(path)
        end
        local func = module and module[method]
        if type(func) == "function" then
            return func(...)
        end
    end
end

-- Overwrites every method wrapModule() wrapped from `path` with its
-- final, direct implementation (or leaves the proxy in place, harmlessly
-- returning nil, if the module didn't provide that method).
local function resolveMethods(base, methods, mod)
    for i = 1, #methods do
        local method = methods[i]
        local fn = mod and mod[method]
        if type(fn) == "function" then
            base[method] = fn
        end
    end
end

function lazy.wrapModule(base, path, methods)
    local resolved = false
    local mod

    for i = 1, #methods do
        local method = methods[i]
        base[method] = function(...)
            if not resolved then
                resolved = true
                mod = loadModule(path)
                resolveMethods(base, methods, mod)
            end
            local fn = mod and mod[method]
            if type(fn) == "function" then
                return fn(...)
            end
        end
    end

    return base
end

return lazy
