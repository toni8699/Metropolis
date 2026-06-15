import { createContext, useContext } from "react";
import { useJsApiLoader } from "@react-google-maps/api";

const GoogleMapsContext = createContext({
  apiKey: "",
  isLoaded: false,
  loadError: null,
});

export function GoogleMapsProvider({ children }) {
  const apiKey = import.meta.env.VITE_GOOGLE_MAPS_API_KEY || "";
  const { isLoaded, loadError } = useJsApiLoader({
    id: "google-maps-script",
    googleMapsApiKey: apiKey,
    libraries: ["places"],
  });

  return (
    <GoogleMapsContext.Provider value={{ apiKey, isLoaded, loadError }}>
      {children}
    </GoogleMapsContext.Provider>
  );
}

export function useGoogleMaps() {
  return useContext(GoogleMapsContext);
}
