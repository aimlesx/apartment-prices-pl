# web — frontend demo (kalkulator ceny mieszkania)

Minimalistyczny interfejs (Vite + React + TypeScript) do ręcznego sprawdzania
predykcji modelu. Wypełniasz cechy mieszkania, aplikacja wysyła je do `POST /predict`
i pokazuje cenę w PLN. Po wyborze miasta współrzędne uzupełniają się automatycznie,
a pola opcjonalne są schowane pod „Więcej szczegółów".

To narzędzie deweloperskie (demo) — **nie** należy do workspace uv (brak `pyproject.toml`),
więc nie wpływa na `uv sync`, `ruff`, `pytest` ani na obraz Dockera serwisu.

## Uruchomienie

Wymaga uruchomionego backendu (`make serve` w katalogu głównym repo) oraz Node ≥ 20.

```bash
make ui          # z katalogu głównego repo: npm install + Vite na http://localhost:5173
```

Aplikacja odwołuje się do API ścieżkami względnymi (`/predict`, `/health`), a serwer
deweloperski Vite przekierowuje te żądania do backendu — dzięki temu nie trzeba
konfigurować CORS-a. Domyślnie kieruje na `:8000` (tak jak `make serve`); aby wskazać
inny port:

```bash
API_TARGET=http://localhost:8200 npm run dev
```

## Build produkcyjny

```bash
npm run build    # pliki statyczne -> web/dist/ (do wystawienia na dowolnym hostingu)
```
