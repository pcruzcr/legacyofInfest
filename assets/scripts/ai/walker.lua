-- Walker AI
-- Simple patrol with chase behavior

function patrol(ctx)
    local speed = ctx.enemy.speed or 60
    -- Walk left/right, reverse at edges
    local dx = speed * ctx.dt * ctx.enemy.facing
    return dx, 0
end

function alert(ctx)
    local dist = ctx.distance
    if dist < 120 then
        return "retreat"
    elseif dist < 400 then
        return "approach"
    end
    return "wait"
end

function on_hit(ctx)
    -- Flinch animation handled by engine
end
