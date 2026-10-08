# FC Hegelmann rungtynių kalendorius

Eksperimentinė viešo `fchegelmann.com/tvarkarastis/` tvarkaraščio prenumerata. Skriptas kasdien atsisiunčia svetainės puslapius ir sugeneruoja `calendar.ics`. Pirmasis paleidimas būtinas norint patikrinti, ar svetainės HTML struktūra atitinka parsavimo logiką.

1. Įkelkite `sync.py`, `requirements.txt`, `README.md` ir `.github/workflows/sync.yml` į viešą GitHub repo, išsaugodami aplankus.
2. GitHub skiltyje **Actions > Update public football calendar > Run workflow** paleiskite procesą rankiniu būdu.
3. Patikrinkite logą (ar rodo rungtynių skaičių) ir ar atsirado `calendar.ics`; jei neveikia, NEprenumeruokite jo, kol neištaisytas parsinimas.
4. **Settings > Pages > Deploy from a branch > main / root** įjunkite GitHub Pages. Puslapio prenumeratos URL: `https://domantobalandzio-dev.github.io/fchegelmann-calendar/calendar.ics`.
5. Google Calendar kompiuteryje: Other calendars > + > From URL > įklijuokite nuorodą. Atkreipkite dėmesį, kad Google gali atnaujinti prenumeratas su uždelsimu.

**Apribojimai:** pabaigos laikas svetainėje nepateikiamas, tad kalendoriuje naudojama 2 val. trukmė. Tikrinami visi tvarkaraščio puslapiai iki 20; didesnį kiekį reikės adaptuoti. Kintanti svetainės HTML struktūra gali nutraukti nuskaitymą; tokiu atveju senasis `calendar.ics` išlieka. Tai nėra oficialus klubo API.
