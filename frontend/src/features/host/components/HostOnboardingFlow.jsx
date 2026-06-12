import { useEffect, useMemo, useRef, useState } from "react";
import { useJsApiLoader } from "@react-google-maps/api";
import { CarFront, UploadCloud, X } from "lucide-react";
import { useNavigate } from "react-router-dom";
import { apiPost } from "@/shared/api/api";
import { useAuth } from "@/context/AuthContext";
import {
  fetchPlacePredictions,
  resolvePredictionCoordinates,
} from "@/shared/lib/placesAutocomplete";
import { MIN_LISTING_PHOTOS } from "@/shared/lib/listingPhotos";
import InstantBookToggle from "@/features/host/components/InstantBookToggle";

const TOTAL_STEPS = 4;
const vehicleTypes = ["Sedan", "SUV", "Truck", "Electric"];

export default function HostOnboardingFlow() {
  const navigate = useNavigate();
  const { refreshMe } = useAuth();
  const [currentStep, setCurrentStep] = useState(1);
  const [headlineVisible, setHeadlineVisible] = useState(true);
  const [listingData, setListingData] = useState({
    make: "",
    model: "",
    year: "",
    type: "",
    address: "",
    lat: null,
    lng: null,
    price: 50,
    instantBook: true,
    images: [],
  });
  const [placePredictions, setPlacePredictions] = useState([]);
  const [isPlacesLoading, setIsPlacesLoading] = useState(false);
  const [placesError, setPlacesError] = useState("");
  const [isPublishing, setIsPublishing] = useState(false);
  const [submitError, setSubmitError] = useState("");
  const [imageFiles, setImageFiles] = useState([]);
  const [imagePreviewUrls, setImagePreviewUrls] = useState([]);
  const [imageError, setImageError] = useState("");

  const fileInputRef = useRef(null);
  const apiKey = import.meta.env.VITE_GOOGLE_MAPS_API_KEY;
  const { loadError: placesLoadError } = useJsApiLoader({
    id: "google-maps-script",
    googleMapsApiKey: apiKey || "",
    libraries: ["places"],
  });

  useEffect(() => {
    setHeadlineVisible(false);
    const timer = window.setTimeout(() => setHeadlineVisible(true), 60);
    return () => window.clearTimeout(timer);
  }, [currentStep]);

  useEffect(() => {
    if (currentStep !== 2) return;
    if (!listingData.address.trim() || !window.google?.maps?.places) {
      setPlacePredictions([]);
      setIsPlacesLoading(false);
      setPlacesError("");
      return;
    }
    if (placesLoadError) {
      setPlacesError("Google Maps failed to load.");
      setPlacePredictions([]);
      return;
    }

    let cancelled = false;
    const timeoutId = window.setTimeout(async () => {
      setIsPlacesLoading(true);
      try {
        const predictions = await fetchPlacePredictions(listingData.address, {
          types: ["geocode"],
          country: "ca",
        });
        if (!cancelled) {
          setPlacePredictions(predictions);
          setPlacesError("");
        }
      } catch {
        if (!cancelled) {
          setPlacePredictions([]);
          setPlacesError("Could not fetch location suggestions.");
        }
      } finally {
        if (!cancelled) {
          setIsPlacesLoading(false);
        }
      }
    }, 250);

    return () => {
      cancelled = true;
      window.clearTimeout(timeoutId);
    };
  }, [currentStep, listingData.address, placesLoadError]);

  useEffect(() => {
    const urls = imageFiles.map((file) => URL.createObjectURL(file));
    setImagePreviewUrls(urls);
    return () => {
      urls.forEach((url) => URL.revokeObjectURL(url));
    };
  }, [imageFiles]);

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
        Number.isFinite(Number(listingData.lat)) &&
        Number.isFinite(Number(listingData.lng))
      );
    }
    if (currentStep === 3) {
      return imageFiles.length >= MIN_LISTING_PHOTOS;
    }
    return Number(listingData.price) > 0;
  }, [currentStep, listingData, imageFiles.length]);

  const stepHeadline = {
    1: "What kind of car are you listing?",
    2: "Where can guests find your car?",
    3: "Show guests your car",
    4: "Now set your price",
  }[currentStep];

  const handleBack = () => {
    if (currentStep === 1) return;
    setCurrentStep((step) => Math.max(1, step - 1));
  };

  const handleNext = async () => {
    if (!canProceed) return;
    if (currentStep < TOTAL_STEPS) {
      setCurrentStep((step) => Math.min(TOTAL_STEPS, step + 1));
      return;
    }
    await submitListing();
  };

  const selectAddressPrediction = async (prediction) => {
    try {
      const { lat, lng } = await resolvePredictionCoordinates(prediction);
      setListingData((prev) => ({
        ...prev,
        address: prediction.description || prev.address,
        lat,
        lng,
      }));
      setPlacePredictions([]);
    } catch {
      setPlacesError("Could not resolve that address.");
    }
  };

  const uploadListingPhotos = async (listingId, files) => {
    for (const file of files) {
      const presign = await apiPost(
        "/api/uploads/presign",
        {
          scope: "OWNER_LISTING",
          listingId: Number(listingId),
          fileName: file.name,
          contentType: file.type || "application/octet-stream",
        },
        true,
      );
      const uploadResponse = await fetch(presign.presignedUrl, {
        method: "PUT",
        headers: {
          "Content-Type": file.type || "application/octet-stream",
        },
        body: file,
      });
      if (!uploadResponse.ok) {
        throw new Error(`S3 upload failed for ${file.name}.`);
      }
      await apiPost(
        "/api/uploads/complete",
        {
          scope: "OWNER_LISTING",
          listingId: Number(listingId),
          objectKey: presign.objectKey,
          contentType: file.type || "application/octet-stream",
          sizeBytes: file.size,
        },
        true,
      );
    }
  };

  const submitListing = async () => {
    if (imageFiles.length < MIN_LISTING_PHOTOS) {
      setSubmitError(`Add at least ${MIN_LISTING_PHOTOS} photos before publishing.`);
      return;
    }

    setIsPublishing(true);
    setSubmitError("");
    try {
      const lat = Number(listingData.lat);
      const lng = Number(listingData.lng);
      const cityZone = "toronto-core";
      const title = `${listingData.make} ${listingData.model}`.trim();
      const response = await apiPost(
        "/api/owner/listings",
        {
          title: title || "My listing",
          make: listingData.make,
          model: listingData.model,
          year: listingData.year ? Number(listingData.year) : undefined,
          pricePerDay: Number(listingData.price),
          instantBook: Boolean(listingData.instantBook),
          isCompanyOwned: false,
          address: listingData.address,
          latitude: lat,
          longitude: lng,
          lat,
          lng,
          cityZone,
          description: listingData.type ? `Vehicle type: ${listingData.type}` : undefined,
        },
        true,
      );
      const listingId = response?.listing?.listingId;
      if (!listingId) {
        throw new Error("Listing created but no listing id returned.");
      }

      await apiPost(
        `/api/owner/listings/${listingId}/location`,
        { lat, lng, cityZone },
        true,
      );

      await uploadListingPhotos(listingId, imageFiles);

      await refreshMe();
      navigate("/host/dashboard");
    } catch (error) {
      setSubmitError(error?.message || "Could not publish listing.");
    } finally {
      setIsPublishing(false);
    }
  };

  const applyImageFiles = (files) => {
    const images = Array.from(files || []).filter((file) => file?.type?.startsWith("image/"));
    if (!images.length) {
      setImageError("Choose image files only (JPEG, PNG, WebP, etc.).");
      return;
    }
    setImageError("");
    setImageFiles((prev) => {
      const byKey = new Map(prev.map((f) => [`${f.name}:${f.size}:${f.lastModified}`, f]));
      images.forEach((file) => {
        byKey.set(`${file.name}:${file.size}:${file.lastModified}`, file);
      });
      const merged = Array.from(byKey.values());
      setListingData((prevListing) => ({
        ...prevListing,
        images: merged.map((file) => file.name),
      }));
      return merged;
    });
  };

  const removeImageFile = (index) => {
    setImageFiles((prev) => {
      const next = prev.filter((_, fileIndex) => fileIndex !== index);
      setListingData((prevListing) => ({
        ...prevListing,
        images: next.map((file) => file.name),
      }));
      return next;
    });
  };

  return (
    <div className="min-h-screen bg-white text-gray-900 flex flex-col">
      <header className="fixed top-0 left-0 right-0 h-20 flex justify-between items-center px-10 border-b bg-white z-50">
        <div className="flex items-center gap-3 text-indigo-600">
          <CarFront className="h-8 w-8" />
          <span className="text-2xl font-bold">DriveBnb</span>
        </div>
        <button
          type="button"
          onClick={() => navigate("/app")}
          className="rounded-full px-4 py-2 text-sm font-medium hover:bg-gray-100"
        >
          Exit
        </button>
      </header>

      <div className="fixed top-20 left-0 h-1 bg-gray-200 w-full z-50">
        <div
          className="bg-gray-900 h-full transition-all duration-500"
          style={{ width: `${progress}%` }}
        />
      </div>

      <main className="flex-grow h-[calc(100vh-176px)] mt-20 mb-24 overflow-y-auto flex">
        <div className="flex flex-col md:flex-row w-full">
          <section className="w-full md:w-1/2 flex items-center justify-center p-10 lg:p-20 bg-gradient-to-br from-indigo-50 to-white">
            <h1
              className={`font-semibold text-4xl md:text-5xl leading-tight transition-opacity duration-500 ${
                headlineVisible ? "opacity-100" : "opacity-0"
              }`}
            >
              {stepHeadline}
            </h1>
          </section>

          <section className="w-full md:w-1/2 flex items-center justify-center p-10">
            <div className="w-full max-w-xl space-y-6">
              {currentStep === 1 && (
                <>
                  <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
                    <input
                      value={listingData.make}
                      onChange={(e) => setListingData((prev) => ({ ...prev, make: e.target.value }))}
                      placeholder="Make"
                      className="w-full border border-gray-300 rounded-xl px-4 py-3 outline-none focus:ring-2 focus:ring-gray-900 focus:border-transparent"
                    />
                    <input
                      value={listingData.model}
                      onChange={(e) =>
                        setListingData((prev) => ({ ...prev, model: e.target.value }))
                      }
                      placeholder="Model"
                      className="w-full border border-gray-300 rounded-xl px-4 py-3 outline-none focus:ring-2 focus:ring-gray-900 focus:border-transparent"
                    />
                    <input
                      value={listingData.year}
                      onChange={(e) => setListingData((prev) => ({ ...prev, year: e.target.value }))}
                      type="number"
                      placeholder="Year"
                      className="w-full border border-gray-300 rounded-xl px-4 py-3 outline-none focus:ring-2 focus:ring-gray-900 focus:border-transparent"
                    />
                  </div>
                  <div className="grid grid-cols-2 gap-3">
                    {vehicleTypes.map((type) => {
                      const active = listingData.type === type;
                      return (
                        <button
                          key={type}
                          type="button"
                          onClick={() => setListingData((prev) => ({ ...prev, type }))}
                          className={`rounded-xl border px-4 py-4 text-left font-medium transition ${
                            active
                              ? "border-gray-900 bg-gray-900 text-white"
                              : "border-gray-300 hover:border-gray-900"
                          }`}
                        >
                          {type}
                        </button>
                      );
                    })}
                  </div>
                </>
              )}

              {currentStep === 2 && (
                <div className="space-y-4">
                  <div className="rounded-xl border border-gray-300 px-4 py-3">
                    <input
                      value={listingData.address}
                      onChange={(e) =>
                        setListingData((prev) => ({ ...prev, address: e.target.value }))
                      }
                      placeholder="Type your address"
                      className="w-full bg-transparent outline-none"
                    />
                  </div>
                  {isPlacesLoading && <p className="text-xs text-gray-500">Loading suggestions...</p>}
                  {placePredictions.length > 0 && (
                    <div className="rounded-xl border border-gray-200 p-2 max-h-52 overflow-y-auto">
                      {placePredictions.map((prediction) => (
                        <button
                          key={prediction.placeId || prediction.place_id}
                          type="button"
                          onClick={() => selectAddressPrediction(prediction)}
                          className="w-full text-left rounded-lg px-3 py-2 hover:bg-gray-50"
                        >
                          <p className="text-sm font-medium text-gray-900">
                            {prediction.structured_formatting?.main_text || prediction.description}
                          </p>
                          <p className="text-xs text-gray-500">
                            {prediction.structured_formatting?.secondary_text || ""}
                          </p>
                        </button>
                      ))}
                    </div>
                  )}
                  {placesError && <p className="text-xs text-red-600">{placesError}</p>}
                  <p className="text-xs text-gray-500">
                    Choose one suggested address so coordinates save correctly.
                  </p>
                </div>
              )}

              {currentStep === 3 && (
                <div className="space-y-4">
                  <div className="flex flex-wrap items-center justify-between gap-2">
                    <p className="text-sm text-gray-600">
                      Add at least {MIN_LISTING_PHOTOS} photos of your car.
                    </p>
                    <p
                      className={`text-sm font-semibold ${
                        imageFiles.length >= MIN_LISTING_PHOTOS
                          ? "text-emerald-700"
                          : "text-amber-700"
                      }`}
                    >
                      {imageFiles.length} / {MIN_LISTING_PHOTOS} selected
                    </p>
                  </div>

                  {imagePreviewUrls.length > 0 && (
                    <div className="grid grid-cols-2 gap-3 sm:grid-cols-3">
                      {imagePreviewUrls.map((url, index) => (
                        <div
                          key={`${imageFiles[index]?.name}-${index}`}
                          className="relative aspect-[4/3] overflow-hidden rounded-xl border border-gray-200 bg-gray-100"
                        >
                          <img
                            src={url}
                            alt={imageFiles[index]?.name || `Photo ${index + 1}`}
                            className="h-full w-full object-cover"
                          />
                          <button
                            type="button"
                            onClick={() => removeImageFile(index)}
                            className="absolute right-2 top-2 flex h-7 w-7 items-center justify-center rounded-full bg-black/60 text-white transition hover:bg-black/80"
                            aria-label={`Remove ${imageFiles[index]?.name || "photo"}`}
                          >
                            <X className="h-4 w-4" />
                          </button>
                        </div>
                      ))}
                    </div>
                  )}

                  <div
                    onClick={() => fileInputRef.current?.click()}
                    onDragOver={(e) => e.preventDefault()}
                    onDrop={(e) => {
                      e.preventDefault();
                      applyImageFiles(e.dataTransfer.files);
                    }}
                    className="border-2 border-dashed border-gray-300 rounded-2xl p-10 flex flex-col items-center justify-center hover:border-gray-900 cursor-pointer transition"
                  >
                    <UploadCloud className="h-10 w-10 text-gray-400 mb-2" />
                    <p className="font-semibold text-gray-900">Add photos</p>
                    <p className="text-sm text-gray-500 mt-1">
                      Drag images here or click to choose (images only)
                    </p>
                    {imageFiles.length > 0 && (
                      <button
                        type="button"
                        onClick={(event) => {
                          event.stopPropagation();
                          setImageFiles([]);
                          setListingData((prev) => ({ ...prev, images: [] }));
                          setImageError("");
                        }}
                        className="mt-3 text-xs font-semibold text-gray-600 hover:text-gray-900"
                      >
                        Clear all photos
                      </button>
                    )}
                    <input
                      ref={fileInputRef}
                      type="file"
                      className="hidden"
                      multiple
                      accept="image/*"
                      onChange={(e) => {
                        applyImageFiles(e.target.files);
                        e.target.value = "";
                      }}
                    />
                  </div>

                  {imageError && <p className="text-sm text-red-600">{imageError}</p>}
                </div>
              )}

              {currentStep === 4 && (
                <div className="mx-auto w-full max-w-md space-y-8">
                  <div className="flex items-center justify-center gap-8">
                    <button
                      type="button"
                      onClick={() =>
                        setListingData((prev) => ({
                          ...prev,
                          price: Math.max(5, Number(prev.price) - 5),
                        }))
                      }
                      className="h-12 w-12 rounded-full border border-gray-300 text-2xl hover:bg-gray-50"
                    >
                      -
                    </button>
                    <input
                      value={listingData.price}
                      onChange={(e) =>
                        setListingData((prev) => ({ ...prev, price: Number(e.target.value) || 0 }))
                      }
                      type="number"
                      className="w-44 bg-transparent text-center font-bold text-6xl text-gray-900 outline-none"
                    />
                    <button
                      type="button"
                      onClick={() =>
                        setListingData((prev) => ({ ...prev, price: Number(prev.price) + 5 }))
                      }
                      className="h-12 w-12 rounded-full border border-gray-300 text-2xl hover:bg-gray-50"
                    >
                      +
                    </button>
                  </div>
                  <InstantBookToggle
                    checked={Boolean(listingData.instantBook)}
                    onChange={(instantBook) =>
                      setListingData((prev) => ({ ...prev, instantBook }))
                    }
                  />
                </div>
              )}

              {submitError && (
                <div className="rounded-xl bg-red-50 border border-red-200 p-3 text-sm text-red-700">
                  {submitError}
                </div>
              )}
            </div>
          </section>
        </div>
      </main>

      <footer className="fixed bottom-0 left-0 right-0 h-24 bg-white border-t flex justify-between items-center px-10 z-50">
        <button
          type="button"
          onClick={handleBack}
          className={`underline font-medium ${currentStep === 1 ? "invisible" : ""}`}
        >
          Back
        </button>
        <button
          type="button"
          onClick={handleNext}
          disabled={!canProceed || isPublishing}
          className="bg-gray-900 text-white px-8 py-3 rounded-md font-semibold disabled:opacity-40"
        >
          {currentStep === TOTAL_STEPS ? (isPublishing ? "Publishing..." : "Publish Listing") : "Next"}
        </button>
      </footer>

    </div>
  );
}
