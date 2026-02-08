# 📦 Istruzioni per Pubblicare la Release v2.0.0

## ✅ Completato

- [x] Tag `v2.0.0` creato e pushato su GitHub
- [x] Build macOS pronto: `dist/AMI-macOS.zip` (126MB)
- [x] Note di rilascio preparate: `GITHUB_RELEASE_NOTES.md`
- [x] SHA256 checksum generato

## 📋 Informazioni Build macOS

- **File**: `AMI-macOS.zip`
- **Dimensione**: 126 MB
- **SHA256**: `917cc4893f814d301162716bb06c2a30bd40e996a7f5a601ff62afd12ea1470b`
- **Architettura**: Universal (Apple Silicon + Intel)
- **Compatibilità**: macOS 10.14+ (Mojave or later)

---

## 🚀 Passo 1: Vai su GitHub Releases

Apri nel browser:
```
https://github.com/dgiovannetti/AMI/releases/new?tag=v2.0.0
```

Il tag `v2.0.0` è già stato creato e pushato, quindi dovrebbe essere selezionato automaticamente.

---

## 📝 Passo 2: Compila i Campi

### Release Title
```
AMI v2.0.0 - Public Release 🎉
```

### Description
Copia e incolla il contenuto di `GITHUB_RELEASE_NOTES.md` (già preparato).

Oppure usa questo link per copiare:
```bash
cat GITHUB_RELEASE_NOTES.md | pbcopy
```

---

## 📦 Passo 3: Upload File macOS

1. Nella sezione **"Attach binaries"**, clicca **"Attach files by dropping them here or selecting them"**

2. Seleziona il file:
   ```
   dist/AMI-macOS.zip
   ```

3. Aspetta che l'upload completi (126MB, ~1-2 minuti)

4. Verifica che appaia nella lista dei file allegati

---

## ⚙️ Passo 4: Opzioni Release

- [ ] **Set as the latest release** - ✅ SPUNTA (è la release principale)
- [ ] **Set as a pre-release** - ❌ NON spuntare (è una release stabile)
- [ ] **Create a discussion for this release** - ✅ OPZIONALE (consigliato per feedback)

---

## 🎯 Passo 5: Pubblica!

1. Clicca **"Publish release"** (pulsante verde in basso)

2. La release sarà immediatamente visibile su:
   ```
   https://github.com/dgiovannetti/AMI/releases/tag/v2.0.0
   ```

3. Verifica che:
   - Il titolo sia corretto
   - La descrizione sia formattata bene
   - Il file `AMI-macOS.zip` sia scaricabile
   - Il badge "Latest" appaia sulla release

---

## 📢 Passo 6: Annuncia (Opzionale)

### GitHub
- [ ] Pin la release nella pagina principale del repo
- [ ] Aggiorna il README se necessario
- [ ] Rispondi a eventuali issue aperte

### Social Media
- [ ] Twitter/X
- [ ] LinkedIn
- [ ] Reddit (r/opensource, r/Python, r/networking)
- [ ] Hacker News

### Esempio Post
```
🎉 AMI v2.0.0 is now public!

Active Monitor of Internet - Know if you're really online.

✨ Modern Stripe-inspired UI
♿ WCAG 2.1 accessible (colorblind-friendly)
📜 Apache 2.0 licensed
🌍 Cross-platform (macOS + Windows)

Download: https://github.com/dgiovannetti/AMI/releases/tag/v2.0.0

#opensource #networking #accessibility
```

---

## 🪟 Windows Build (Da Fare)

Quando il build Windows sarà pronto:

1. Vai alla release esistente:
   ```
   https://github.com/dgiovannetti/AMI/releases/tag/v2.0.0
   ```

2. Clicca **"Edit release"** (in alto a destra)

3. Nella sezione file, clicca **"Attach files"**

4. Upload `AMI-Windows.zip`

5. Aggiorna la descrizione rimuovendo la nota "⚠️ Windows build coming soon!"

6. Clicca **"Update release"**

---

## ✅ Checklist Finale

Dopo la pubblicazione, verifica:

- [ ] Release visibile su GitHub
- [ ] File macOS scaricabile
- [ ] Link funzionanti nella descrizione
- [ ] Badge "Latest" presente
- [ ] Tag `v2.0.0` visibile nella lista tags
- [ ] README aggiornato con link alla release
- [ ] Download count inizia a salire

---

## 🔗 Link Utili

- **Release Page**: https://github.com/dgiovannetti/AMI/releases/tag/v2.0.0
- **Repository**: https://github.com/dgiovannetti/AMI
- **Issues**: https://github.com/dgiovannetti/AMI/issues
- **Discussions**: https://github.com/dgiovannetti/AMI/discussions

---

## 🎉 Congratulazioni!

AMI v2.0.0 è ora **pubblico** e disponibile per il download!

**"Sai se sei davvero online."**

© 2025 CiaoIM™ by Daniel Giovannetti
