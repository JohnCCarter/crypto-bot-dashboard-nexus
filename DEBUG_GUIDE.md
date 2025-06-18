# 🐛 Debug & Felhantering Guide - Crypto Trading Bot

**🎯 ÄNTLIGEN! Nu har du kraftfull debugging för att förstå vad som händer med boten.**

---

## 📊 Debug Log Viewer

### Vad du nu kan se

**✅ FRONTEND LOGGING:**

- 🤖 `[BotControl]` - Bot start/stop operationer
- 📈 `[ManualTrade]` - Manuella order placements  
- ⚙️ `[Settings]` - Konfigurationsändringar
- 🏠 `[Index]` - Dashboard aktivitet

**✅ BACKEND LOGGING:**

- 🤖 `[Backend]` - Server-side bot operations
- 📋 `[Backend]` - Order API responses
- ⚙️ `[Backend]` - Configuration handling

---

## 🔍 Så här använder du Debug Viewer

### 1. **Öppna Log Viewer**

- Finns längst ner till höger på dashboard
- Uppdateras automatiskt när du använder boten

### 2. **Filtrera logs**

```
🔘 All Logs        - Allt (frontend + backend)
🔘 Errors Only     - Bara fel och problem  
🔘 Warnings        - Varningar och notices
🔘 Bot Control     - Bot start/stop logs
🔘 Trading         - Order & trading logs
🔘 Settings        - Configuration logs
```

### 3. **Exportera för felsökning**

- Klicka **Export** för att ladda ner JSON-fil
- Skicka till support om du behöver hjälp

---

## 🚨 Fel-diagnosing Step-by-Step

### **Problem: Bot startar inte**

**STEG 1:** Filtrera på "Bot Control"

```
🤖 [BotControl] User clicked START button ✓
🤖 [Backend] START bot request received ✓
❌ [Backend] Start bot failed: Connection error
```

**STEG 2:** Kolla detaljer

- Se exakt felmeddelande
- Kontrollera stack trace
- Verifiera API-anslutning

---

### **Problem: Orders fungerar inte**

**STEG 1:** Filtrera på "Trading"

```
📈 [ManualTrade] User initiated BUY order ✓
📈 [ManualTrade] Order validation passed ✓
❌ [ManualTrade] Order submission failed: Invalid amount
```

**STEG 2:** Troubleshoot

- Kontrollera amount/price values
- Verifiera exchange connectivity  
- Kolla balans tillräcklighet

---

### **Problem: Configuration sparas inte**

**STEG 1:** Filtrera på "Settings"

```
⚙️ [Settings] User clicked save configuration ✓
⚙️ [Settings] Calling api.updateConfig()... ✓
❌ [Settings] Configuration save failed: Validation error
```

**STEG 2:** Fixa

- Se vilka fält som är felaktiga
- Kontrollera nummer-format
- Verifiera obligatoriska fält

---

## 🛠️ Teknisk Felsökning

### **Console.log intercept**

Alla `console.log()`, `console.error()`, `console.warn()` fångas nu automatiskt och visas i Log Viewer.

### **Real-time debugging**

```javascript
// Dessa visas automatiskt i Log Viewer:
console.log("Debug info här");
console.error("Fel uppstod:", error);
console.warn("Varning:", details);
```

### **Backend error tracking**

- Detaljerade stack traces
- Exception types
- Request/response data
- Timestamp för varje operation

---

## 📋 Log Format

```
✅ [Component] Operation successful: details
❌ [Component] Operation failed: error message  
⚠️ [Component] Warning message
🤖 [Component] Bot operation
📈 [Component] Trading operation
⚙️ [Component] Settings operation
🏠 [Component] Dashboard operation
```

---

## 🎯 Praktiska tips

### **1. Förebyggande debugging:**

- Kör alltid "All Logs" filter först
- Kolla efter error patterns
- Exportera logs innan större ändringar

### **2. Effektiv felsökning:**

1. Reproducera problemet
2. Filtrera relevant kategori  
3. Leta efter error messages
4. Kontrollera stack traces
5. Fixa grundorsaken

### **3. Performance monitoring:**

- Håll koll på API response times
- Övervaka memory usage i logs
- Upptäck patterns i fel

---

## 🆘 Support & Hjälp

**Vid tekniska problem:**

1. **Exportera logs** från tiden då felet uppstod
2. **Filtrera på "Errors Only"** för att se exakta fel
3. **Kopiera felmeddelanden** med full stack trace
4. **Skicka till support** med beskrivning av vad du försökte göra

**Vanliga lösningar:**

- Starta om servern: `Ctrl+C` → `npm run dev`
- Rensa cache: `Ctrl+Shift+R`
- Kontrollera network tab i browser
- Verifiera backend är igång på port 5000

---

## ✨ Nu är du redo

**Med denna debugging kan du:**

- ✅ Se exakt vad som händer under huven
- ✅ Diagnostisera problem snabbt och effektivt  
- ✅ Förstå varför bot/trading operationer misslyckas
- ✅ Få professionell felhantering som hjälper dig felsöka

**🎉 Ingen mer gissning - nu ser du allt i realtid!**
