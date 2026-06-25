import type { ApartmentFeatures } from "./api";
import { CITIES } from "./cities";

// Słowniki kategorii — wartość = token modelu, etykieta = polski opis.
export const OWNERSHIP: Record<string, string> = {
  condominium: "Pełna własność",
  cooperative: "Spółdzielcze",
};

export const BUILDING_TYPE: Record<string, string> = {
  blockOfFlats: "Blok",
  tenement: "Kamienica",
  apartmentBuilding: "Apartamentowiec",
};

export const BUILDING_MATERIAL: Record<string, string> = {
  brick: "Cegła",
  concreteSlab: "Wielka płyta",
};

export const CONDITION: Record<string, string> = {
  premium: "Wysoki standard",
  low: "Do remontu",
};

// Pola opcjonalne liczbowe — etykieta + jednostka. Puste => pominięte w żądaniu.
export interface NumberFieldDef {
  name: keyof ApartmentFeatures;
  label: string;
  unit?: string;
  min?: number;
  step?: number;
}

export const OPTIONAL_NUMBERS: NumberFieldDef[] = [
  { name: "floor", label: "Piętro", min: 0, step: 1 },
  { name: "floorCount", label: "Liczba pięter", min: 1, step: 1 },
  { name: "buildYear", label: "Rok budowy", min: 1850, step: 1 },
  { name: "poiCount", label: "Liczba POI w okolicy", min: 0, step: 1 },
  { name: "schoolDistance", label: "Szkoła", unit: "km", min: 0, step: 0.1 },
  { name: "clinicDistance", label: "Przychodnia", unit: "km", min: 0, step: 0.1 },
  { name: "postOfficeDistance", label: "Poczta", unit: "km", min: 0, step: 0.1 },
  { name: "kindergartenDistance", label: "Przedszkole", unit: "km", min: 0, step: 0.1 },
  { name: "restaurantDistance", label: "Restauracja", unit: "km", min: 0, step: 0.1 },
  { name: "collegeDistance", label: "Uczelnia", unit: "km", min: 0, step: 0.1 },
  { name: "pharmacyDistance", label: "Apteka", unit: "km", min: 0, step: 0.1 },
];

// Domyślny, wycenialny od razu zestaw — typowe mieszkanie w Warszawie.
export const DEFAULTS: ApartmentFeatures = {
  city: "warszawa",
  squareMeters: 55,
  rooms: 3,
  latitude: CITIES.warszawa.lat,
  longitude: CITIES.warszawa.lng,
  centreDistance: CITIES.warszawa.centreDistance,
  ownership: "condominium",
  hasParkingSpace: false,
  hasBalcony: true,
  hasSecurity: false,
  hasStorageRoom: false,
  // opcjonalne — domyślnie puste (pomijane w żądaniu)
  type: "",
  floor: null,
  floorCount: null,
  buildYear: null,
  buildingMaterial: "",
  condition: "",
  hasElevator: null,
  poiCount: null,
  schoolDistance: null,
  clinicDistance: null,
  postOfficeDistance: null,
  kindergartenDistance: null,
  restaurantDistance: null,
  collegeDistance: null,
  pharmacyDistance: null,
};
