// Kontrakt cech modelu — 1:1 z serving/apartment_serving/schemas.py (camelCase).
// 11 pól wymaganych (non-null) + 15 opcjonalnych (mogą być pominięte → NaN/"missing").
export interface ApartmentFeatures {
  // --- wymagane ---
  city: string;
  squareMeters: number;
  rooms: number;
  latitude: number;
  longitude: number;
  centreDistance: number;
  ownership: string;
  hasParkingSpace: boolean;
  hasBalcony: boolean;
  hasSecurity: boolean;
  hasStorageRoom: boolean;
  // --- opcjonalne ---
  type?: string | null;
  floor?: number | null;
  floorCount?: number | null;
  buildYear?: number | null;
  buildingMaterial?: string | null;
  condition?: string | null;
  hasElevator?: boolean | null;
  poiCount?: number | null;
  schoolDistance?: number | null;
  clinicDistance?: number | null;
  postOfficeDistance?: number | null;
  kindergartenDistance?: number | null;
  restaurantDistance?: number | null;
  collegeDistance?: number | null;
  pharmacyDistance?: number | null;
}

// UWAGA: żądanie jest camelCase, ale odpowiedź jest snake_case.
export interface PricePrediction {
  price_pln: number;
}

// Usuń puste pola opcjonalne — backend traktuje brak klucza jako NaN/"missing".
function pruneEmpty(features: ApartmentFeatures): Record<string, unknown> {
  return Object.fromEntries(
    Object.entries(features).filter(([, v]) => v !== null && v !== undefined && v !== ""),
  );
}

export async function predict(features: ApartmentFeatures): Promise<PricePrediction> {
  let res: Response;
  try {
    res = await fetch("/predict", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(pruneEmpty(features)),
    });
  } catch {
    throw new Error("Nie udało się połączyć z serwisem — czy backend działa?");
  }
  if (!res.ok) {
    throw new Error(
      res.status === 422 ? "Błąd walidacji danych wejściowych." : `Błąd serwera (${res.status}).`,
    );
  }
  return res.json();
}

const PLN = new Intl.NumberFormat("pl-PL", {
  style: "currency",
  currency: "PLN",
  maximumFractionDigits: 0,
});

export const formatPln = (value: number): string => PLN.format(value);
