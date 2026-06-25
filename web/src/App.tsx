import { useState, type FormEvent } from "react";
import { type ApartmentFeatures, type PricePrediction, predict, formatPln } from "./api";
import { CITIES, CITY_SLUGS } from "./cities";
import {
  BUILDING_MATERIAL,
  BUILDING_TYPE,
  CONDITION,
  DEFAULTS,
  OPTIONAL_NUMBERS,
  OWNERSHIP,
} from "./fields";
import { CheckboxField, NumberField, SelectField } from "./Field";

type Status = "idle" | "loading" | "error" | "done";

// Kontekst jakości modelu (z README — holdout grupowy).
const MODEL_NOTE = "Model: R² 0,9154 · MAE 73 156 zł · MAPE 9,51% (holdout)";

export default function App() {
  const [f, setF] = useState<ApartmentFeatures>(DEFAULTS);
  const [status, setStatus] = useState<Status>("idle");
  const [result, setResult] = useState<PricePrediction | null>(null);
  const [error, setError] = useState("");

  // Aktualizacja pojedynczego pola (klucz literałowy → typ wartości sprawdzany).
  const set = <K extends keyof ApartmentFeatures>(name: K, value: ApartmentFeatures[K]) =>
    setF((prev) => ({ ...prev, [name]: value }) as ApartmentFeatures);

  // Aktualizacja pola liczbowego po nazwie dynamicznej (pola opcjonalne).
  const setNum = (name: keyof ApartmentFeatures, value: number | null) =>
    setF((prev) => ({ ...prev, [name]: value }) as ApartmentFeatures);

  const numVal = (name: keyof ApartmentFeatures): number | null => {
    const v = f[name];
    return typeof v === "number" ? v : null;
  };

  // Wybór miasta auto-uzupełnia współrzędne (ukryte) i odległość od centrum.
  const onCity = (slug: string) => {
    const c = CITIES[slug];
    setF((prev) => ({
      ...prev,
      city: slug,
      latitude: c.lat,
      longitude: c.lng,
      centreDistance: c.centreDistance,
    }));
  };

  const onSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setStatus("loading");
    setError("");
    try {
      const prediction = await predict(f);
      setResult(prediction);
      setStatus("done");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Nieznany błąd.");
      setStatus("error");
    }
  };

  const cityOptions = Object.fromEntries(CITY_SLUGS.map((s) => [s, CITIES[s].label]));

  return (
    <div className="app">
      <header className="header">
        <h1>🏙️ Wycena mieszkania</h1>
        <p className="subtitle">
          Predykcja ceny mieszkania w Polsce (model regresji LightGBM). Uzupełnij dane i policz cenę.
        </p>
      </header>

      <form className="form" onSubmit={onSubmit}>
        <div className="grid">
          <SelectField
            id="city"
            label="Miasto"
            value={f.city}
            options={cityOptions}
            onChange={onCity}
          />
          <NumberField
            id="squareMeters"
            label="Metraż"
            unit="m²"
            value={f.squareMeters}
            min={10}
            step={1}
            required
            onChange={(v) => set("squareMeters", v ?? 0)}
          />
          <NumberField
            id="rooms"
            label="Liczba pokoi"
            value={f.rooms}
            min={1}
            step={1}
            required
            onChange={(v) => set("rooms", v ?? 1)}
          />
          <SelectField
            id="ownership"
            label="Forma własności"
            value={f.ownership}
            options={OWNERSHIP}
            onChange={(v) => set("ownership", v)}
          />
          <NumberField
            id="centreDistance"
            label="Odległość od centrum"
            unit="km"
            value={f.centreDistance}
            min={0}
            step={0.1}
            required
            onChange={(v) => set("centreDistance", v ?? 0)}
          />
        </div>

        <fieldset className="toggles">
          <legend>Udogodnienia</legend>
          <CheckboxField
            id="hasParkingSpace"
            label="Miejsce parkingowe"
            checked={f.hasParkingSpace}
            onChange={(v) => set("hasParkingSpace", v)}
          />
          <CheckboxField
            id="hasBalcony"
            label="Balkon"
            checked={f.hasBalcony}
            onChange={(v) => set("hasBalcony", v)}
          />
          <CheckboxField
            id="hasSecurity"
            label="Ochrona"
            checked={f.hasSecurity}
            onChange={(v) => set("hasSecurity", v)}
          />
          <CheckboxField
            id="hasStorageRoom"
            label="Komórka lokatorska"
            checked={f.hasStorageRoom}
            onChange={(v) => set("hasStorageRoom", v)}
          />
        </fieldset>

        <details className="advanced">
          <summary>Więcej szczegółów (opcjonalne)</summary>
          <div className="grid">
            <SelectField
              id="type"
              label="Rodzaj budynku"
              value={f.type ?? ""}
              options={BUILDING_TYPE}
              placeholder="— nie podano —"
              onChange={(v) => set("type", v)}
            />
            <SelectField
              id="buildingMaterial"
              label="Materiał"
              value={f.buildingMaterial ?? ""}
              options={BUILDING_MATERIAL}
              placeholder="— nie podano —"
              onChange={(v) => set("buildingMaterial", v)}
            />
            <SelectField
              id="condition"
              label="Stan"
              value={f.condition ?? ""}
              options={CONDITION}
              placeholder="— nie podano —"
              onChange={(v) => set("condition", v)}
            />
            <label className="field" htmlFor="hasElevator">
              <span className="field-label">Winda</span>
              <select
                id="hasElevator"
                name="hasElevator"
                value={f.hasElevator == null ? "" : String(f.hasElevator)}
                onChange={(e) =>
                  set("hasElevator", e.target.value === "" ? null : e.target.value === "true")
                }
              >
                <option value="">— nie podano —</option>
                <option value="true">Tak</option>
                <option value="false">Nie</option>
              </select>
            </label>
            {OPTIONAL_NUMBERS.map((d) => (
              <NumberField
                key={d.name}
                id={d.name}
                label={d.label}
                unit={d.unit}
                min={d.min}
                step={d.step}
                value={numVal(d.name)}
                onChange={(v) => setNum(d.name, v)}
              />
            ))}
          </div>
        </details>

        <button className="submit" type="submit" disabled={status === "loading"}>
          {status === "loading" ? "Obliczam…" : "Oblicz cenę"}
        </button>
      </form>

      {status === "error" && (
        <p className="error" role="alert">
          {error}
        </p>
      )}

      {status === "done" && result && (
        <section className="result" data-testid="wynik" aria-live="polite">
          <p className="result-label">Szacowana cena</p>
          <p className="result-price" data-testid="cena">
            {formatPln(result.price_pln)}
          </p>
          <p className="result-permeter">{formatPln(result.price_pln / f.squareMeters)} / m²</p>
          <p className="result-note">{MODEL_NOTE}</p>
        </section>
      )}
    </div>
  );
}
