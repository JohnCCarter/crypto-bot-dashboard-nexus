-- ============================================
-- 🐛 DEBUG STEG 2: TESTA CONSTRAINTS EN I TAGET
-- ============================================

-- TEST 1: Lägg till constraint på trades.side
ALTER TABLE trades ADD CONSTRAINT trades_side_check 
    CHECK (side IN ('buy', 'sell'));

-- Kör SELECT för att verifiera
SELECT 'trades_side_check tillagd!' as status;