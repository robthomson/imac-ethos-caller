-- Reusable lazy-loading helper.

local lazy = {}
local cache = {}

local function loadModule(path)
    if cache[path] then return cache[path] end
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
        error("lazy: failed to load '" .. path .. "': " .. tostring(err))
    end
    cache[path] = loader()
    return cache[path]
end

function lazy.wrapFunction(path, method)
    local module
    return function(...)
        if not module then
            module = loadModule(path)
        end
        local func = module[method]
        return func(...)
    end
end

function lazy.wrapModule(base, path, methods)
    for i = 1, #methods do
        local method = methods[i]
        base[method] = lazy.wrapFunction(path, method)
    end
    return base
end

return lazy
