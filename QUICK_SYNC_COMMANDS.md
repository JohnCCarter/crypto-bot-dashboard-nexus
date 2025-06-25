# ⚡ Snabb Synkronisering - Kommandoreferens

## 🚨 KRITISKA KOMMANDON (Använd Dessa!)

### **📥 Börja Arbeta (Första saken du gör)**
```bash
./sync-start.sh
```
*Eller manuellt:*
```bash
git pull
```

### **📤 Sluta Arbeta (Sista saken du gör)**
```bash
./sync-end.sh
```
*Eller manuellt:*
```bash
git add . && git commit -m "Arbetssession slutförd" && git push
```

---

## 🔍 Status Kommandon

| Kommando | Vad det visar |
|----------|---------------|
| `git status` | Vilka filer som är ändrade |
| `git log --oneline -5` | Senaste 5 commits |
| `git remote -v` | Vilken GitHub repo du är kopplad till |
| `git branch` | Vilken branch du jobbar på |

---

## 🚨 Nödsituationer

### **Problem: Får inte pusha**
```bash
git pull          # Hämta senaste ändringar först
git push          # Försök igen
```

### **Problem: Konflikter vid pull**
```bash
git stash         # Spara dina ändringar temporärt
git pull          # Hämta remote ändringar
git stash pop     # Ta tillbaka dina ändringar
# Lös konflikter manuellt i editor
git add .
git commit -m "Löst konflikt"
git push
```

### **Problem: Glömde pusha igår**
```bash
# På datorn där du jobbade igår:
git status        # Kolla vad som finns ospart
git add .
git commit -m "Glömda ändringar från igår"
git push

# På andra datorn:
git pull          # Hämta det du glömde
```

---

## ✅ Daglig Rutin (VIKTIGT!)

### **🌅 När du börjar (VARJE DAG)**
1. Öppna terminal i projektmappen
2. Kör: `./sync-start.sh`
3. Börja jobba

### **🌙 När du slutar (VARJE DAG)**
1. Spara alla filer i editorn
2. Kör: `./sync-end.sh`
3. Vänta tills det säger "✅ Framgångsrikt"
4. Stäng datorn

---

## 💡 Protips

- **Commita ofta!** - Spara inte bara vid dagens slut
- **Beskrivande meddelanden** - "Fixade login bug" inte bara "fix"
- **Dubbelkolla status** - Kör `git status` innan du slutar
- **Internet krävs** - Du måste vara online för push/pull

---

## 🎯 Resultat

**Med dessa kommandon kommer du ALDRIG förlora arbete mellan datorer!** 🚀