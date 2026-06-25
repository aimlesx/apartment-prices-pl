// Mediany współrzędnych i odległości od centrum per miasto (policzone z danych
// treningowych — training/data/01_raw/apartments_pl_*.csv). Wybór miasta
// auto-uzupełnia latitude/longitude (ukryte) oraz centreDistance (edytowalne) —
// użytkownik nie wpisuje surowej geolokalizacji ręcznie (to zła UX).
export interface CityDefaults {
  lat: number;
  lng: number;
  centreDistance: number;
  label: string;
}

export const CITIES: Record<string, CityDefaults> = {
  warszawa: { lat: 52.2296, lng: 21.0111, centreDistance: 6.0, label: "Warszawa" },
  krakow: { lat: 50.0637, lng: 19.9494, centreDistance: 4.0, label: "Kraków" },
  gdansk: { lat: 54.354, lng: 18.6066, centreDistance: 5.2, label: "Gdańsk" },
  wroclaw: { lat: 51.1095, lng: 17.0338, centreDistance: 2.8, label: "Wrocław" },
  lodz: { lat: 51.7665, lng: 19.4586, centreDistance: 3.7, label: "Łódź" },
  bydgoszcz: { lat: 53.125, lng: 18.0079, centreDistance: 1.8, label: "Bydgoszcz" },
  gdynia: { lat: 54.5142, lng: 18.5021, centreDistance: 4.8, label: "Gdynia" },
  poznan: { lat: 52.4033, lng: 16.9212, centreDistance: 3.4, label: "Poznań" },
  lublin: { lat: 51.2426, lng: 22.547, centreDistance: 2.7, label: "Lublin" },
  szczecin: { lat: 53.4322, lng: 14.5474, centreDistance: 3.1, label: "Szczecin" },
  katowice: { lat: 50.2562, lng: 19.0155, centreDistance: 2.4, label: "Katowice" },
  radom: { lat: 51.4021, lng: 21.1578, centreDistance: 1.8, label: "Radom" },
  bialystok: { lat: 53.1352, lng: 23.1464, centreDistance: 2.1, label: "Białystok" },
  czestochowa: { lat: 50.8092, lng: 19.123, centreDistance: 2.0, label: "Częstochowa" },
  rzeszow: { lat: 50.0369, lng: 22.0004, centreDistance: 2.3, label: "Rzeszów" },
};

export const CITY_SLUGS = Object.keys(CITIES);
