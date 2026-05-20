import { useEffect, useMemo, useRef, useState } from "react";
import { GoogleMap, Marker, useJsApiLoader } from "@react-google-maps/api";
import { APIProvider, AdvancedMarker, Map as VisMap, Pin } from "@vis.gl/react-google-maps";
import {
  Bluetooth,
  CarFront,
  Check,
  ChevronLeft,
  ChevronRight,
  KeyRound,
  Minus,
  Plus,
  Search,
  ShieldCheck,
  Smartphone,
  Snowflake,
  Sun,
  UploadCloud,
  X,
} from "lucide-react";
import { Link, useNavigate } from "react-router-dom";
import { apiPost } from "../utils/api";

const TOTAL_STEPS = 6;
const vehicleTypes = ["Sedan", "SUV", "Truck", "Electric"];
const FEATURE_OPTIONS = [
  "Apple CarPlay",
  "Android Auto",
  "Bluetooth",
  "Sunroof",
  "Heated Seats",
  "AWD",
  "Backup Camera",
  "Blind Spot Warning",
  "Keyless Entry",
];
const FEATURE_ICONS = {
  "Apple CarPlay": Smartphone,
  "Android Auto": Smartphone,
  Bluetooth,
  Sunroof: Sun,
  "Heated Seats": Snowflake,
  AWD: ShieldCheck,
  "Backup Camera": UploadCloud,
  "Blind Spot Warning": ShieldCheck,
  "Keyless Entry": KeyRound,
};
const FALLBACK_CENTER = { lat: 43.6532, lng: -79.3832 };

const stepHeadlines = {
  1: "What kind of car are you listing?",
  2: "Where will guests pick up your car?",
  3: "Show off your car with great photos",
  4: "Add car details guests care about",
  5: "Add features and host guidelines",
  6: "Set your daily price",
};

export default function HostOnboardingFlow() {
  const navigate = useNavigate();
  const [currentStep, setCurrentStep] = useState(1);
  const [listingData, setListingData] = useState({
    make: "",
    model: "",
    year: "",
    type: "",
    address: "",
    lat: null,
    lng: null,
    transmission: "Automatic",
    fuelType: "Gas",
    seats: 5,
    doors: 4,
    description: "",
    guidelines: "",
    features: [],
    price: 50,
    images: [],
    imageFiles: [],
  });

  const [addressQuery, setAddressQuery] = useState("");
  const [placePredictions, setPlacePredictions] = useState([]);
  const [isPlacesLoading, setIsPlacesLoading] = useState(false);
  const [placesError, setPlacesError] = useState("");
  const [isPublishing, setIsPublishing] = useState(false);
  const [publishError, setPublishError] = useState("");
  const [isHeadlineVisible, setIsHeadlineVisible] = useState(true);
  const [isMapModalOpen, setIsMapModalOpen] = useState(false);
  const [isReverseGeocoding, setIsReverseGeocoding] = useState(false);
  const [tempLocation, setTempLocation] = useState({
    lat: FALLBACK_CENTER.lat,
    lng: FALLBACK_CENTER.lng,
    address: "",
  });

  const fileInputRef = useRef(null);
  const autocompleteServiceRef = useRef(null);
  const geocoderRef = useRef(null);

  const apiKey = import.meta.env.VITE_GOOGLE_MAPS_API_KEY;
  const { isLoaded: isPlacesLoaded, loadError: placesLoadError } = useJsApiLoader({
    id: "google-maps-script",
    googleMapsApiKey: apiKey || "",
    libraries: ["places"],
  });

  useEffect(() => {
    setIsHeadlineVisible(false);
    const timer = window.setTimeout(() => setIsHeadlineVisible(true), 50);
    return () => window.clearTimeout(timer);
  }, [currentStep]);

  useEffect(() => {
    if (!isPlacesLoaded || !window.google?.maps) return;
    try {
      if (!autocompleteServiceRef.current && window.google.maps.places) {
        autocompleteServiceRef.current =
          new window.google.maps.places.AutocompleteService();
      }
      if (!geocoderRef.current) {
        geocoderRef.current = new window.google.maps.Geocoder();
      }
    } catch {
      setPlacesError("Google Places failed to initialize.");
    }
  }, [isPlacesLoaded]);

  useEffect(() => {
    if (currentStep !== 2) return;
    if (!addressQuery.trim()) {
      setPlacePredictions([]);
      setPlacesError("");
      setIsPlacesLoading(false);
      return;
    }
    if (placesLoadError) {
      setPlacesError("Google Maps failed to load.");
      setPlacePredictions([]);
      return;
    }
    if (!autocompleteServiceRef.current) {
      setPlacePredictions([]);
      return;
    }

    let cancelled = false;
    const timeoutId = window.setTimeout(() => {
      setIsPlacesLoading(true);
      setPlacesError("");
      autocompleteServiceRef.current.getPlacePredictions(
        { input: addressQuery, types: ["geocode"] },
        (predictions, status) => {
          if (cancelled) return;
          if (
            status === window.google.maps.places.PlacesServiceStatus.OK &&
            predictions
          ) {
            setPlacePredictions(predictions);
          } else if (
            status === window.google.maps.places.PlacesServiceStatus.ZERO_RESULTS
          ) {
            setPlacePredictions([]);
          } else {
            setPlacePredictions([]);
            setPlacesError("Could not fetch location suggestions.");
          }
          setIsPlacesLoading(false);
        },
      );
    }, 300);

    return () => {
      cancelled = true;
      window.clearTimeout(timeoutId);
    };
  }, [addressQuery, currentStep, placesLoadError]);

  useEffect(() => {
    if (!isMapModalOpen) return;
    const lat = Number(listingData.lat);
    const lng = Number(listingData.lng);
    const safeLat = Number.isFinite(lat) ? lat : FALLBACK_CENTER.lat;
    const safeLng = Number.isFinite(lng) ? lng : FALLBACK_CENTER.lng;
    setTempLocation({
      lat: safeLat,
      lng: safeLng,
      address: listingData.address || "",
    });
  }, [isMapModalOpen, listingData.address, listingData.lat, listingData.lng]);

  const progress = (currentStep / TOTAL_STEPS) * 100;

  const canProceed = useMemo(() => {
    if (currentStep === 1) {
      return (
        listingData.make.trim() &&
        listingData.model.trim() &&
        listingData.year.trim() &&
        listingData.type
      );
    }
    if (currentStep === 2) {
      return (
        listingData.address.trim() &&
        Number.isFinite(listingData.lat) &&
        Number.isFinite(listingData.lng)
      );
    }
    if (currentStep === 3) {
      return listingData.images.length > 0;
    }
    if (currentStep === 4) {
      return (
        listingData.transmission &&
        listingData.fuelType &&
        Number(listingData.seats) > 0 &&
        Number(listingData.doors) > 0
      );
    }
    if (currentStep === 5) {
      return listingData.description.trim().length > 0;
    }
    return true;
  }, [currentStep, listingData]);

  const updateListingData = (updates) => {
    setListingData((current) => ({ ...current, ...updates }));
  };

  const geocodePlace = (placeId) =>
    new Promise((resolve, reject) => {
      if (!geocoderRef.current) {
        reject(new Error("Geocoder unavailable"));
        return;
      }
      geocoderRef.current.geocode({ placeId }, (results, status) => {
        if (
          status === "OK" &&
          results?.[0]?.geometry?.location &&
          typeof results[0].geometry.location.lat === "function" &&
          typeof results[0].geometry.location.lng === "function"
        ) {
          const point = results[0].geometry.location;
          resolve({
            lat: point.lat(),
            lng: point.lng(),
            formattedAddress: results[0].formatted_address || "",
          });
          return;
        }
        reject(new Error("Could not geocode selected place"));
      });
    });

  const reverseGeocodeLocation = (lat, lng) =>
    new Promise((resolve) => {
      if (!geocoderRef.current) {
        resolve("");
        return;
      }
      setIsReverseGeocoding(true);
      geocoderRef.current.geocode({ location: { lat, lng } }, (results, status) => {
        setIsReverseGeocoding(false);
        if (status === "OK" && results?.[0]?.formatted_address) {
          resolve(results[0].formatted_address);
          return;
        }
        resolve("");
      });
    });

  const openMapPicker = () => {
    setIsMapModalOpen(true);
  };

  const handlePinDrop = async (newLat, newLng) => {
    setTempLocation((prev) => ({ ...prev, lat: newLat, lng: newLng }));
    const address = await reverseGeocodeLocation(newLat, newLng);
    if (address) {
      setTempLocation((prev) => ({ ...prev, address }));
    }
  };

  const confirmMapLocation = () => {
    updateListingData({
      address: tempLocation.address || listingData.address,
      lat: tempLocation.lat,
      lng: tempLocation.lng,
    });
    if (tempLocation.address) {
      setAddressQuery(tempLocation.address);
    }
    setIsMapModalOpen(false);
  };

  const processFiles = (fileList) => {
    const files = Array.from(fileList || []).filter((file) =>
      file.type.startsWith("image/"),
    );
    if (files.length === 0) return;
    const imageUrls = files.map((file) => URL.createObjectURL(file));
    updateListingData({
      images: [...listingData.images, ...imageUrls],
      imageFiles: [...listingData.imageFiles, ...files],
    });
  };

  const handleDrop = (event) => {
    event.preventDefault();
    processFiles(event.dataTransfer.files);
  };

  const submitListing = async () => {
    setPublishError("");
    setIsPublishing(true);
    try {
      // Ensure backend CORS allows requests from Vite frontend (e.g., http://localhost:5173).
      const cityZoneFromAddress = (listingData.address || "")
        .split(",")[0]
        .trim()
        .toLowerCase()
        .replace(/\s+/g, "-") || "custom-host-zone";

      const payload = {
        title: `${listingData.make} ${listingData.model} ${listingData.year}`.trim(),
        brand: listingData.make || null,
        make: listingData.make || null,
        model: listingData.model || null,
        year: listingData.year ? Number(listingData.year) : null,
        transmission: listingData.transmission || null,
        fuelType: listingData.fuelType || null,
        seats: listingData.seats ? Number(listingData.seats) : null,
        doors: listingData.doors ? Number(listingData.doors) : null,
        description:
          listingData.description ||
          `${listingData.type || "Vehicle"} listed by host at ${listingData.address}.`,
        guidelines: listingData.guidelines || "Please return clean and on time.",
        features: listingData.features || [],
        images: [],
        address: listingData.address || null,
        latitude: listingData.lat,
        longitude: listingData.lng,
        rules: listingData.guidelines || "Please return clean and on time.",
        pickupNotesTemplate: `Pickup location: ${listingData.address}`,
        pricePerDay: Number(listingData.price),
        photos: [],
        lat: listingData.lat,
        lng: listingData.lng,
        cityZone: cityZoneFromAddress,
      };

      const createResult = await apiPost("/api/owner/listings", payload, true);
      const listingId = createResult?.listing?.listingId;
      if (!listingId) {
        throw new Error("Listing created but missing listing id.");
      }

      for (const file of listingData.imageFiles) {
        const contentType = file.type || "application/octet-stream";
        const presign = await apiPost(
          "/api/uploads/presign",
          {
            fileName: file.name,
            contentType,
            scope: "OWNER_LISTING",
            listingId,
          },
          true,
        );
        const uploadResp = await fetch(presign.presignedUrl, {
          method: "PUT",
          headers: { "Content-Type": contentType },
          body: file,
        });
        if (!uploadResp.ok) {
          throw new Error(`S3 upload failed for ${file.name}`);
        }
        await apiPost(
          "/api/uploads/complete",
          {
            objectKey: presign.objectKey,
            contentType,
            sizeBytes: file.size,
            scope: "OWNER_LISTING",
            listingId,
          },
          true,
        );
      }

      setCurrentStep(1);
      listingData.images.forEach((url) => URL.revokeObjectURL(url));
      setListingData({
        make: "",
        model: "",
        year: "",
        type: "",
        address: "",
        lat: null,
        lng: null,
        transmission: "Automatic",
        fuelType: "Gas",
        seats: 5,
        doors: 4,
        description: "",
        guidelines: "",
        features: [],
        price: 50,
        images: [],
        imageFiles: [],
      });
      setAddressQuery("");
      navigate("/owner");
    } catch (err) {
      const message = err?.message || "Could not publish listing. Try again.";
      setPublishError(message);
      window.alert(message);
    } finally {
      setIsPublishing(false);
    }
  };

  const handleNext = async () => {
    if (!canProceed) return;
    if (currentStep < TOTAL_STEPS) {
      setCurrentStep((step) => step + 1);
      return;
    }
    await submitListing();
  };

  const handleBack = () => {
    if (currentStep > 1) {
      setCurrentStep((step) => step - 1);
    }
  };

  return (
    <div className="min-h-screen bg-white text-gray-900">
      <header className="fixed top-0 left-0 right-0 z-50 h-20 border-b bg-white px-10">
        <div className="flex h-full items-center justify-between">
          <Link to="/" className="flex items-center gap-2 text-indigo-600">
            <CarFront className="h-7 w-7" />
            <span className="text-xl font-bold">DriveBnb</span>
          </Link>
          <button
            onClick={() => navigate("/")}
            className="rounded-full px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-100"
          >
            Exit
          </button>
        </div>
      </header>

      <main className="mt-20 mb-24 flex h-[calc(100vh-176px)] flex-grow overflow-y-auto">
        <div className="flex w-full flex-col md:flex-row">
          <section className="flex w-full items-center justify-center bg-gradient-to-br from-indigo-50 to-white p-10 md:w-1/2 lg:p-20">
            <h1
              key={currentStep}
              className={`max-w-xl text-4xl font-semibold leading-tight transition-opacity duration-500 md:text-5xl ${
                isHeadlineVisible ? "opacity-100" : "opacity-0"
              }`}
            >
              {stepHeadlines[currentStep]}
            </h1>
          </section>

          <section className="flex w-full items-center justify-center p-10 md:w-1/2">
            <div className="w-full max-w-xl">
              {currentStep === 1 && (
                <div className="space-y-6">
                  <div className="grid gap-4 md:grid-cols-2">
                    <input
                      value={listingData.make}
                      onChange={(event) =>
                        updateListingData({ make: event.target.value })
                      }
                      placeholder="Make"
                      className="rounded-xl border border-gray-300 px-4 py-3 outline-none focus:border-gray-900"
                    />
                    <input
                      value={listingData.model}
                      onChange={(event) =>
                        updateListingData({ model: event.target.value })
                      }
                      placeholder="Model"
                      className="rounded-xl border border-gray-300 px-4 py-3 outline-none focus:border-gray-900"
                    />
                  </div>
                  <input
                    value={listingData.year}
                    onChange={(event) =>
                      updateListingData({ year: event.target.value })
                    }
                    placeholder="Year"
                    type="number"
                    className="w-full rounded-xl border border-gray-300 px-4 py-3 outline-none focus:border-gray-900"
                  />
                  <div className="grid gap-3 sm:grid-cols-2">
                    {vehicleTypes.map((type) => {
                      const isActive = listingData.type === type;
                      return (
                        <button
                          key={type}
                          onClick={() => updateListingData({ type })}
                          className={`rounded-2xl border p-4 text-left transition ${
                            isActive
                              ? "border-gray-900 bg-gray-900 text-white"
                              : "border-gray-300 bg-white hover:border-gray-900"
                          }`}
                        >
                          <p className="font-semibold">{type}</p>
                        </button>
                      );
                    })}
                  </div>
                </div>
              )}

              {currentStep === 2 && (
                <div className="space-y-3">
                  <div className="relative">
                    <Search className="pointer-events-none absolute left-4 top-1/2 h-5 w-5 -translate-y-1/2 text-gray-400" />
                    <input
                      value={addressQuery}
                      onChange={(event) => {
                        setAddressQuery(event.target.value);
                        updateListingData({ address: "", lat: null, lng: null });
                      }}
                      placeholder="Type your pickup address"
                      className="w-full rounded-2xl border border-gray-300 py-4 pl-12 pr-4 outline-none focus:border-gray-900"
                    />
                    <div className="absolute right-3 top-1/2 -translate-y-1/2">
                      <button
                        type="button"
                        onClick={openMapPicker}
                        className="rounded-lg border border-gray-300 px-3 py-1.5 text-xs font-semibold text-gray-700 hover:bg-gray-50"
                      >
                        Pick from map
                      </button>
                    </div>
                  </div>
                  <div className="rounded-2xl border border-gray-200 bg-white p-2">
                    {isPlacesLoading ? (
                      <p className="px-3 py-4 text-sm text-gray-500">Loading suggestions...</p>
                    ) : placePredictions.length > 0 ? (
                      placePredictions.map((prediction) => {
                        const title =
                          prediction.structured_formatting?.main_text ||
                          prediction.description;
                        const subtitle =
                          prediction.structured_formatting?.secondary_text || "";
                        return (
                          <button
                            key={prediction.place_id}
                            onClick={async () => {
                              try {
                                const result = await geocodePlace(prediction.place_id);
                                setAddressQuery(result.formattedAddress || title);
                                updateListingData({
                                  address: result.formattedAddress || title,
                                  lat: result.lat,
                                  lng: result.lng,
                                });
                                setPlacePredictions([]);
                                setPlacesError("");
                              } catch {
                                setPlacesError("Could not resolve selected address.");
                              }
                            }}
                            className="w-full rounded-xl px-3 py-3 text-left hover:bg-gray-50"
                          >
                            <p className="font-medium text-gray-900">{title}</p>
                            <p className="text-sm text-gray-500">{subtitle}</p>
                          </button>
                        );
                      })
                    ) : (
                      <p className="px-3 py-4 text-sm text-gray-500">
                        Start typing to see address suggestions.
                      </p>
                    )}
                  </div>
                  {placesError && (
                    <p className="text-sm text-red-500">{placesError}</p>
                  )}
                  {listingData.address && (
                    <p className="text-sm text-gray-600">
                      Selected: <span className="font-medium">{listingData.address}</span>
                    </p>
                  )}
                  {Number.isFinite(listingData.lat) && Number.isFinite(listingData.lng) && (
                    <div className="rounded-2xl overflow-hidden border border-gray-200">
                      {!apiKey ? (
                        <div className="p-4 text-sm text-gray-600 bg-gray-50">
                          Add `VITE_GOOGLE_MAPS_API_KEY` to show mini map preview.
                        </div>
                      ) : (
                        <GoogleMap
                          mapContainerStyle={{ width: "100%", height: "220px" }}
                          center={{ lat: listingData.lat, lng: listingData.lng }}
                          zoom={14}
                          options={{
                            zoomControl: true,
                            streetViewControl: false,
                            mapTypeControl: false,
                            fullscreenControl: false,
                          }}
                        >
                          <Marker position={{ lat: listingData.lat, lng: listingData.lng }} />
                        </GoogleMap>
                      )}
                    </div>
                  )}
                </div>
              )}

              {currentStep === 3 && (
                <div className="space-y-4">
                  <div
                    role="button"
                    tabIndex={0}
                    onClick={() => fileInputRef.current?.click()}
                    onKeyDown={(event) => {
                      if (event.key === "Enter" || event.key === " ") {
                        fileInputRef.current?.click();
                      }
                    }}
                    onDragOver={(event) => event.preventDefault()}
                    onDrop={handleDrop}
                    className="flex cursor-pointer flex-col items-center justify-center rounded-2xl border-2 border-dashed border-gray-300 p-10 transition hover:border-gray-900"
                  >
                    <UploadCloud className="mb-3 h-10 w-10 text-gray-500" />
                    <p className="text-lg font-medium text-gray-800">
                      Drag your photos here
                    </p>
                    <p className="text-sm text-gray-500">or click to upload</p>
                  </div>
                  <input
                    ref={fileInputRef}
                    type="file"
                    accept="image/*"
                    multiple
                    className="hidden"
                    onChange={(event) => processFiles(event.target.files)}
                  />
                  {listingData.images.length > 0 && (
                    <div className="grid grid-cols-3 gap-3">
                      {listingData.images.map((image, idx) => (
                        <img
                          key={`${image}-${idx}`}
                          src={image}
                          alt={`Upload ${idx + 1}`}
                          className="h-24 w-full rounded-lg object-cover"
                        />
                      ))}
                    </div>
                  )}
                </div>
              )}

              {currentStep === 4 && (
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <label className="block">
                    <span className="mb-2 block text-sm font-medium text-gray-700">Transmission</span>
                    <select
                      value={listingData.transmission}
                      onChange={(event) => updateListingData({ transmission: event.target.value })}
                      className="w-full rounded-xl border border-gray-300 px-4 py-3 outline-none focus:border-gray-900"
                    >
                      <option>Automatic</option>
                      <option>Manual</option>
                    </select>
                  </label>
                  <label className="block">
                    <span className="mb-2 block text-sm font-medium text-gray-700">Fuel Type</span>
                    <select
                      value={listingData.fuelType}
                      onChange={(event) => updateListingData({ fuelType: event.target.value })}
                      className="w-full rounded-xl border border-gray-300 px-4 py-3 outline-none focus:border-gray-900"
                    >
                      <option>Gas</option>
                      <option>Electric</option>
                      <option>Hybrid</option>
                      <option>Diesel</option>
                    </select>
                  </label>
                  <input
                    value={listingData.seats}
                    onChange={(event) => updateListingData({ seats: event.target.value })}
                    type="number"
                    min="1"
                    placeholder="Seats"
                    className="w-full rounded-xl border border-gray-300 px-4 py-3 outline-none focus:border-gray-900"
                  />
                  <input
                    value={listingData.doors}
                    onChange={(event) => updateListingData({ doors: event.target.value })}
                    type="number"
                    min="1"
                    placeholder="Doors"
                    className="w-full rounded-xl border border-gray-300 px-4 py-3 outline-none focus:border-gray-900"
                  />
                </div>
              )}

              {currentStep === 5 && (
                <div className="space-y-4">
                  <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
                    {FEATURE_OPTIONS.map((featureName) => {
                      const Icon = FEATURE_ICONS[featureName] || Check;
                      const active = listingData.features.includes(featureName);
                      return (
                        <button
                          key={featureName}
                          type="button"
                          onClick={() =>
                            updateListingData({
                              features: active
                                ? listingData.features.filter((item) => item !== featureName)
                                : [...listingData.features, featureName],
                            })
                          }
                          className={`flex items-center gap-2 border p-3 rounded-xl text-left transition ${
                            active
                              ? "border-gray-900 bg-gray-900 text-white"
                              : "border-gray-300 hover:border-gray-900"
                          }`}
                        >
                          <Icon className="h-4 w-4" />
                          <span className="text-sm">{featureName}</span>
                        </button>
                      );
                    })}
                  </div>
                  <textarea
                    value={listingData.description}
                    onChange={(event) => updateListingData({ description: event.target.value })}
                    placeholder="Describe your car and why guests should book it."
                    className="w-full min-h-28 rounded-xl border border-gray-300 px-4 py-3 outline-none focus:border-gray-900"
                  />
                  <textarea
                    value={listingData.guidelines}
                    onChange={(event) => updateListingData({ guidelines: event.target.value })}
                    placeholder="e.g., No smoking, pet fees..."
                    className="w-full min-h-24 rounded-xl border border-gray-300 px-4 py-3 outline-none focus:border-gray-900"
                  />
                </div>
              )}

              {currentStep === 6 && (
                <div className="flex items-center justify-center gap-8">
                  <button
                    onClick={() =>
                      updateListingData({ price: Math.max(5, listingData.price - 5) })
                    }
                    className="rounded-full border border-gray-300 p-3 hover:border-gray-900"
                    aria-label="Decrease price"
                  >
                    <Minus className="h-6 w-6" />
                  </button>
                  <input
                    type="number"
                    value={listingData.price}
                    onChange={(event) =>
                      updateListingData({
                        price: Number(event.target.value || listingData.price),
                      })
                    }
                    className="w-56 border-0 bg-transparent text-center text-6xl font-bold text-gray-900 outline-none"
                  />
                  <button
                    onClick={() =>
                      updateListingData({ price: Math.max(5, listingData.price + 5) })
                    }
                    className="rounded-full border border-gray-300 p-3 hover:border-gray-900"
                    aria-label="Increase price"
                  >
                    <Plus className="h-6 w-6" />
                  </button>
                </div>
              )}

              {publishError && (
                <p className="mt-4 text-sm text-red-500">{publishError}</p>
              )}
            </div>
          </section>
        </div>
      </main>

      {isMapModalOpen && (
        <div className="fixed inset-0 z-[60] bg-black/60 flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl shadow-2xl w-full max-w-4xl h-[80vh] flex flex-col overflow-hidden relative">
            <div className="px-6 py-4 border-b border-gray-200 flex items-center justify-between">
              <div>
                <h3 className="text-lg font-semibold text-gray-900">Drag the pin to your exact location</h3>
                {isReverseGeocoding && (
                  <p className="text-xs text-gray-500 mt-1">Finding address...</p>
                )}
              </div>
              <button
                type="button"
                onClick={() => setIsMapModalOpen(false)}
                className="text-gray-500 hover:text-gray-900"
              >
                <X className="h-5 w-5" />
              </button>
            </div>
            <div className="flex-grow w-full relative">
              {!apiKey ? (
                <div className="rounded-lg border border-gray-200 bg-gray-50 p-4 text-sm text-gray-600 m-6">
                  Add `VITE_GOOGLE_MAPS_API_KEY` in `frontend/.env.local` to use map picker.
                </div>
              ) : !isPlacesLoaded ? (
                <div className="rounded-lg border border-gray-200 bg-gray-50 p-4 text-sm text-gray-600 m-6">
                  Loading map...
                </div>
              ) : (
                <>
                  <div className="absolute z-10 top-4 left-4 right-4 bg-white/95 border border-gray-200 rounded-lg px-3 py-2 text-sm text-gray-700 shadow-sm">
                    {tempLocation.address || "Drop or drag pin to resolve address."}
                  </div>
                  <APIProvider apiKey={apiKey}>
                    <VisMap
                      mapId="DEMO_MAP_ID"
                      defaultCenter={{ lat: tempLocation.lat, lng: tempLocation.lng }}
                      defaultZoom={14}
                      zoomControl={true}
                      streetViewControl={false}
                      mapTypeControl={false}
                      fullscreenControl={false}
                      style={{ width: "100%", height: "100%" }}
                    >
                      <AdvancedMarker
                        position={{ lat: tempLocation.lat, lng: tempLocation.lng }}
                        draggable
                        onDragEnd={(event) => {
                          const newLat = event?.latLng?.lat?.();
                          const newLng = event?.latLng?.lng?.();
                          if (Number.isFinite(newLat) && Number.isFinite(newLng)) {
                            handlePinDrop(newLat, newLng);
                          }
                        }}
                      >
                        <Pin background={"#EF4444"} borderColor={"#7F1D1D"} glyphColor={"#7F1D1D"} />
                      </AdvancedMarker>
                    </VisMap>
                  </APIProvider>
                </>
              )}
            </div>
            <div className="p-4 border-t bg-white flex justify-end gap-3">
              <button
                type="button"
                onClick={() => setIsMapModalOpen(false)}
                className="rounded-lg border border-gray-300 px-4 py-2 text-gray-700 hover:bg-gray-50 transition"
              >
                Cancel
              </button>
              <button
                type="button"
                onClick={confirmMapLocation}
                className="rounded-lg bg-gray-900 px-4 py-2 text-white font-semibold hover:bg-black transition"
              >
                Confirm Location
              </button>
            </div>
          </div>
        </div>
      )}

      <footer className="fixed bottom-0 left-0 right-0 z-50 h-24 border-t bg-white px-10">
        <div className="absolute left-0 right-0 top-0 h-1 w-full bg-gray-200">
          <div
            className="h-full bg-gray-900 transition-all duration-500"
            style={{ width: `${progress}%` }}
          />
        </div>
        <div className="flex h-full items-center justify-between">
          <button
            onClick={handleBack}
            className={`font-medium underline ${
              currentStep === 1 ? "invisible" : "text-gray-900"
            }`}
          >
            Back
          </button>
          <button
            onClick={handleNext}
            disabled={!canProceed || isPublishing}
            className="rounded-md bg-gray-900 px-8 py-3 font-semibold text-white disabled:cursor-not-allowed disabled:opacity-40"
          >
            {currentStep === TOTAL_STEPS
              ? isPublishing
                ? "Publishing..."
                : "Publish Listing"
              : "Next"}
          </button>
        </div>
      </footer>
    </div>
  );
}
