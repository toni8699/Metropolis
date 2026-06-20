import { useEffect, useMemo, useRef, useState } from "react";
import { UploadCloud, X } from "lucide-react";
import { useNavigate } from "react-router-dom";
import VroomLogo from "@/layout/VroomLogo";
import { apiGet, apiPost } from "@/shared/api/api";
import { uploadPresignedFile } from "@/shared/lib/uploadPresigned";
import { useAuth } from "@/context/AuthContext";
import { useGoogleMaps } from "@/context/GoogleMapsProvider";
import { usePlacesAutocomplete } from "@/shared/hooks/usePlacesAutocomplete";
import { resolvePredictionCoordinates } from "@/shared/lib/placesAutocomplete";
import { MIN_LISTING_PHOTOS } from "@/features/host/constants";
import {
  BODY_TYPE_DEFAULTS,
  FUEL_TYPE_OPTIONS,
  REQUIRED_SPEC_FIELDS,
  TRANSMISSION_OPTIONS,
} from "@/features/host/constants/bodyTypeDefaults";
import {
  controlBorderClass,
  FormFieldLabel,
  LabeledInput,
  NeoSelect,
} from "@/features/host/components/form/Fields";
import InstantBookToggle from "@/features/host/components/InstantBookToggle";
import { markRecentListingCreated } from "@/features/host/lib/recentListing";

const TOTAL_STEPS = 5;
const VIN_PATTERN = /^[A-HJ-NPR-Z0-9]{11,17}$/i;

const EMPTY_SPEC_META = {
  seats: { isVerified: false, source: "missing" },
  doors: { isVerified: false, source: "missing" },
  transmission: { isVerified: false, source: "missing" },
  fuelType: { isVerified: false, source: "missing" },
};

function formatAssetLabel(data) {
  return [data.make, data.model, data.year].filter(Boolean).join(" ").trim();
}

function specMetaFromApi(field) {
  if (!field || typeof field !== "object") {
    return { isVerified: false, source: "missing" };
  }
  return {
    isVerified: Boolean(field.isVerified),
    source: field.source || "missing",
  };
}

function specValueFromApi(field) {
  if (!field || field.value == null) return "";
  return String(field.value);
}

function requiredSpecsFilled(data) {
  return REQUIRED_SPEC_FIELDS.every((field) => {
    const value = data[field];
    return value != null && String(value).trim() !== "";
  });
}

function normalizeTransmission(value) {
  if (!value) return "";
  const text = String(value).toLowerCase();
  if (text.includes("manual")) return "Manual";
  if (text.includes("auto") || text.includes("cvt")) return "Automatic";
  return "";
}

function normalizeFuelType(value) {
  if (!value) return "";
  const text = String(value).toLowerCase();
  if (text.includes("electric") || text === "ev") return "Electric";
  if (text.includes("hybrid")) return "Hybrid";
  if (text.includes("diesel")) return "Diesel";
  if (text.includes("gas") || text.includes("petrol")) return "Gas";
  return "";
}

function SpecConfirmField({
  label,
  value,
  meta,
  onChange,
  required = false,
  type = "text",
  options = null,
  placeholder = "",
}) {
  const missing = required && (value == null || String(value).trim() === "");
  const estimated = meta?.source === "default";
  const borderState = missing ? "error" : estimated ? "estimate" : "default";

  const badge = missing ? (
    <span className="rounded-full border-2 border-black bg-red-100 px-2 py-0.5 text-xs font-bold text-red-700">
      Required
    </span>
  ) : estimated ? (
    <span className="rounded-full border-2 border-black bg-amber-100 px-2 py-0.5 text-xs font-bold text-amber-900">
      Estimate
    </span>
  ) : null;

  return (
    <div>
      <FormFieldLabel badge={badge}>{label}</FormFieldLabel>
      {options ? (
        <NeoSelect
          value={value}
          onChange={onChange}
          options={options}
          placeholder={placeholder || `Select ${label.toLowerCase()}`}
          borderState={borderState}
        />
      ) : (
        <input
          type={type}
          value={value}
          onChange={(e) => onChange(e.target.value)}
          className={controlBorderClass(borderState)}
        />
      )}
    </div>
  );
}

function BodyTypeFields({
  bodyTypes,
  bodyTypeId,
  bodyTypeOther,
  onBodyTypeChange,
  onBodyTypeOtherChange,
}) {
  const selected = bodyTypes.find((type) => String(type.bodyTypeId) === String(bodyTypeId));
  const isOther = selected?.code === "OTHER";
  const bodyTypeOptions = bodyTypes.map((type) => ({
    value: String(type.bodyTypeId),
    label: type.displayName,
  }));

  return (
    <div className="space-y-4">
      <label className="block">
        <FormFieldLabel>Body type</FormFieldLabel>
        <NeoSelect
          value={bodyTypeId}
          onChange={onBodyTypeChange}
          options={bodyTypeOptions}
          placeholder="Select body type"
          borderState={bodyTypeId ? "default" : "error"}
        />
      </label>
      {isOther && (
        <>
          <LabeledInput
            label="Describe body type"
            value={bodyTypeOther}
            onChange={onBodyTypeOtherChange}
            placeholder="e.g. Convertible, Van, Limousine"
            borderState={bodyTypeOther.trim() ? "default" : "error"}
          />
          {!bodyTypeOther.trim() && (
            <p className="text-xs font-bold text-red-600">Required when Other is selected</p>
          )}
        </>
      )}
    </div>
  );
}

export default function HostOnboardingFlow() {
  const navigate = useNavigate();
  const { refreshMe, ensureVerifiedEmail } = useAuth();
  const [currentStep, setCurrentStep] = useState(1);
  const [headlineVisible, setHeadlineVisible] = useState(true);
  const [bodyTypes, setBodyTypes] = useState([]);
  const [listingData, setListingData] = useState({
    vin: "",
    make: "",
    model: "",
    year: "",
    transmission: "",
    fuelType: "",
    seats: "",
    doors: "",
    bodyTypeId: "",
    bodyTypeOther: "",
    listingTitle: "",
    address: "",
    lat: null,
    lng: null,
    price: 50,
    instantBook: true,
    images: [],
  });
  const [entryMode, setEntryMode] = useState("vin");
  const [specMeta, setSpecMeta] = useState(EMPTY_SPEC_META);
  const [submitError, setSubmitError] = useState("");
  const [decodeError, setDecodeError] = useState("");
  const [isDecoding, setIsDecoding] = useState(false);
  const [imageFiles, setImageFiles] = useState([]);
  const [imagePreviewUrls, setImagePreviewUrls] = useState([]);
  const [imageError, setImageError] = useState("");
  const [isPublishing, setIsPublishing] = useState(false);

  const fileInputRef = useRef(null);
  const { isLoaded: mapsReady, loadError: placesLoadError } = useGoogleMaps();
  const {
    predictions: placePredictions,
    isLoading: isPlacesLoading,
    placesError,
    setPlacesError,
    setPredictions: setPlacePredictions,
  } = usePlacesAutocomplete(listingData.address, {
    enabled: currentStep === 3,
    debounceMs: 250,
    country: "ca",
    mapsReady,
    placesLoadError,
  });

  useEffect(() => {
    apiGet("/api/body-types")
      .then((data) => setBodyTypes(data?.bodyTypes || []))
      .catch(() => setBodyTypes([]));
  }, []);

  useEffect(() => {
    setHeadlineVisible(false);
    const timer = window.setTimeout(() => setHeadlineVisible(true), 60);
    return () => window.clearTimeout(timer);
  }, [currentStep]);

  useEffect(() => {
    const urls = imageFiles.map((file) => URL.createObjectURL(file));
    setImagePreviewUrls(urls);
    return () => {
      urls.forEach((url) => URL.revokeObjectURL(url));
    };
  }, [imageFiles]);

  const progress = (currentStep / TOTAL_STEPS) * 100;
  const assetLabel = formatAssetLabel(listingData);
  const selectedBodyType = useMemo(
    () => bodyTypes.find((type) => String(type.bodyTypeId) === String(listingData.bodyTypeId)),
    [bodyTypes, listingData.bodyTypeId],
  );
  const isOtherBodyType = selectedBodyType?.code === "OTHER";
  const bodyTypeOk =
    Boolean(listingData.bodyTypeId) &&
    (!isOtherBodyType || Boolean(listingData.bodyTypeOther.trim()));

  const canProceed = useMemo(() => {
    if (currentStep === 1) {
      if (entryMode === "manual") return true;
      return VIN_PATTERN.test(String(listingData.vin).trim());
    }
    if (currentStep === 2) {
      const specsOk = requiredSpecsFilled(listingData);
      if (entryMode === "manual") {
        return Boolean(
          listingData.make &&
            listingData.model &&
            listingData.year &&
            bodyTypeOk &&
            specsOk,
        );
      }
      return Boolean(listingData.make && listingData.model && bodyTypeOk && specsOk);
    }
    if (currentStep === 3) {
      return (
        listingData.address.trim() &&
        Number.isFinite(Number(listingData.lat)) &&
        Number.isFinite(Number(listingData.lng))
      );
    }
    if (currentStep === 4) {
      return imageFiles.length >= MIN_LISTING_PHOTOS;
    }
    return Number(listingData.price) > 0 && Boolean(listingData.listingTitle.trim());
  }, [currentStep, listingData, imageFiles.length, entryMode, bodyTypeOk]);

  const stepHeadline = {
    1: "Start with your VIN",
    2: entryMode === "manual" ? "Tell us about your car" : "Confirm your specs",
    3: "Where can guests find your car?",
    4: "Show guests your car",
    5: "Name your listing and set your price",
  }[currentStep];

  const handleSpecChange = (field, value) => {
    setListingData((prev) => ({ ...prev, [field]: value }));
    setSpecMeta((prev) => ({
      ...prev,
      [field]: { isVerified: false, source: "user" },
    }));
  };

  const handleBodyTypeChange = (bodyTypeId) => {
    const type = bodyTypes.find((item) => String(item.bodyTypeId) === bodyTypeId);
    const defaults = BODY_TYPE_DEFAULTS[type?.code] || {};
    setListingData((prev) => {
      const next = { ...prev, bodyTypeId };
      if (type?.code !== "OTHER") {
        next.bodyTypeOther = "";
      }
      if (specMeta.seats.source !== "nhtsa" && specMeta.seats.source !== "user") {
        next.seats = defaults.seats != null ? String(defaults.seats) : prev.seats;
      }
      if (specMeta.doors.source !== "nhtsa" && specMeta.doors.source !== "user") {
        next.doors = defaults.doors != null ? String(defaults.doors) : prev.doors;
      }
      if (
        specMeta.transmission.source !== "nhtsa" &&
        specMeta.transmission.source !== "user"
      ) {
        next.transmission = defaults.transmission || prev.transmission;
      }
      return next;
    });
    setSpecMeta((prev) => {
      const next = { ...prev };
      if (prev.seats.source !== "nhtsa" && prev.seats.source !== "user") {
        next.seats =
          defaults.seats != null
            ? { isVerified: false, source: "default" }
            : { isVerified: false, source: "missing" };
      }
      if (prev.doors.source !== "nhtsa" && prev.doors.source !== "user") {
        next.doors =
          defaults.doors != null
            ? { isVerified: false, source: "default" }
            : { isVerified: false, source: "missing" };
      }
      if (prev.transmission.source !== "nhtsa" && prev.transmission.source !== "user") {
        next.transmission = defaults.transmission
          ? { isVerified: false, source: "default" }
          : { isVerified: false, source: "missing" };
      }
      return next;
    });
  };

  const skipVinEntry = () => {
    setEntryMode("manual");
    setDecodeError("");
    setListingData((prev) => ({
      ...prev,
      vin: "",
      make: "",
      model: "",
      year: "",
      transmission: "",
      fuelType: "",
      seats: "",
      doors: "",
      bodyTypeId: "",
      bodyTypeOther: "",
    }));
    setSpecMeta(EMPTY_SPEC_META);
    setCurrentStep(2);
  };

  const decodeVin = async () => {
    const vin = String(listingData.vin).trim().toUpperCase();
    if (!VIN_PATTERN.test(vin)) {
      setDecodeError("Enter a valid 11-17 character VIN.");
      return false;
    }
    setIsDecoding(true);
    setDecodeError("");
    try {
      const response = await apiPost("/api/vehicles/vin/decode", { vin }, true);
      const decoded = response?.decoded || {};
      const suggestedId =
        decoded.bodyTypeId ||
        decoded.suggestedBodyType?.bodyTypeId ||
        listingData.bodyTypeId ||
        "";
      setListingData((prev) => ({
        ...prev,
        vin,
        make: decoded.make || prev.make,
        model: decoded.model || prev.model,
        year: decoded.modelYear ? String(decoded.modelYear) : prev.year,
        transmission:
          normalizeTransmission(specValueFromApi(decoded.transmission)) || prev.transmission,
        fuelType: normalizeFuelType(specValueFromApi(decoded.fuelType)) || prev.fuelType,
        seats: specValueFromApi(decoded.seats) || prev.seats,
        doors: specValueFromApi(decoded.doors) || prev.doors,
        bodyTypeId: suggestedId ? String(suggestedId) : prev.bodyTypeId,
        listingTitle:
          prev.listingTitle ||
          [decoded.make, decoded.model].filter(Boolean).join(" ").trim(),
      }));
      setSpecMeta({
        seats: specMetaFromApi(decoded.seats),
        doors: specMetaFromApi(decoded.doors),
        transmission: specMetaFromApi(decoded.transmission),
        fuelType: specMetaFromApi(decoded.fuelType),
      });
      return true;
    } catch (error) {
      setDecodeError(error?.message || "Could not decode VIN.");
      return false;
    } finally {
      setIsDecoding(false);
    }
  };

  const handleBack = () => {
    if (currentStep === 1) return;
    if (currentStep === 2 && entryMode === "manual") {
      setEntryMode("vin");
    }
    setCurrentStep((step) => Math.max(1, step - 1));
  };

  const handleNext = async () => {
    if (!canProceed || isDecoding) return;
    if (currentStep === 1 && entryMode === "vin") {
      const ok = await decodeVin();
      if (!ok) return;
      setCurrentStep(2);
      return;
    }
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
      await uploadPresignedFile(file, {
        presignBody: {
          scope: "OWNER_LISTING",
          listingId: Number(listingId),
          fileName: file.name,
          contentType: file.type || "application/octet-stream",
        },
        completeBody: {
          scope: "OWNER_LISTING",
          listingId: Number(listingId),
        },
      });
    }
  };

  const submitListing = async () => {
    if (!ensureVerifiedEmail()) {
      return;
    }
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
      const listingTitle = listingData.listingTitle.trim();
      const payload = {
        listingTitle,
        title: listingTitle,
        bodyTypeId: Number(listingData.bodyTypeId),
        bodyTypeOther: isOtherBodyType ? listingData.bodyTypeOther.trim() : undefined,
        make: listingData.make,
        model: listingData.model,
        year: listingData.year ? Number(listingData.year) : undefined,
        transmission: listingData.transmission || undefined,
        fuelType: listingData.fuelType || undefined,
        seats: listingData.seats ? Number(listingData.seats) : undefined,
        doors: listingData.doors ? Number(listingData.doors) : undefined,
        pricePerDay: Number(listingData.price),
        instantBook: Boolean(listingData.instantBook),
        isCompanyOwned: false,
        pickupAddress: listingData.address,
        latitude: lat,
        longitude: lng,
        lat,
        lng,
        cityZone,
      };
      if (entryMode === "vin" && listingData.vin.trim()) {
        payload.vin = String(listingData.vin).trim().toUpperCase();
      }
      const response = await apiPost("/api/listings", payload, true);
      const listingId = response?.listing?.listingId;
      if (!listingId) {
        throw new Error("Listing created but no listing id returned.");
      }

      await apiPost(
        `/api/listings/${listingId}/location`,
        { lat, lng, cityZone, pickupAddress: listingData.address },
        true,
      );

      await uploadListingPhotos(listingId, imageFiles);

      await refreshMe();
      markRecentListingCreated();
      navigate(`/host/success/${listingId}`);
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
    <div className="min-h-screen bg-vroom-bg text-vroom-heading flex flex-col">
      <header className="fixed top-0 left-0 right-0 z-50 flex h-20 items-center justify-between border-b-4 border-black bg-vroom-surface px-10">
        <div className="flex items-center">
          <VroomLogo />
        </div>
        <button
          type="button"
          onClick={() => navigate("/app")}
          className="rounded-full border-2 border-black border-b-4 bg-white px-4 py-2 text-sm font-bold active:border-b-0"
        >
          Exit
        </button>
      </header>

      <div className="fixed top-20 left-0 z-50 h-1 w-full bg-vroom-sage">
        <div
          className="h-full bg-vroom-accent transition-all duration-500"
          style={{ width: `${progress}%` }}
        />
      </div>

      <main className="flex-grow h-[calc(100vh-176px)] mt-20 mb-24 overflow-y-auto flex">
        <div className="flex flex-col md:flex-row w-full">
          <section className="w-full md:w-1/2 flex items-center justify-center p-10 lg:p-20 bg-gradient-to-br from-[#f5f5d0] to-[#FCFCE5]">
            <h1
              className={`font-extrabold text-4xl md:text-5xl leading-tight transition-opacity duration-500 ${
                headlineVisible ? "opacity-100" : "opacity-0"
              }`}
            >
              {stepHeadline}
            </h1>
          </section>

          <section className="w-full md:w-1/2 flex items-center justify-center p-10">
            <div className="w-full max-w-xl space-y-6">
              {currentStep === 1 && (
                <div className="space-y-4">
                  {entryMode === "vin" && (
                    <label className="block">
                      <FormFieldLabel>Vehicle VIN</FormFieldLabel>
                      <input
                        value={listingData.vin}
                        onChange={(e) =>
                          setListingData((prev) => ({
                            ...prev,
                            vin: e.target.value.toUpperCase(),
                          }))
                        }
                        placeholder="11–17 characters"
                        className={`${controlBorderClass("default")} uppercase`}
                      />
                    </label>
                  )}
                  {entryMode === "vin" ? (
                    <>
                      <p className="text-sm font-semibold text-vroom-muted">
                        We decode make, model, and specs from your VIN automatically.
                      </p>
                      <button
                        type="button"
                        onClick={skipVinEntry}
                        className="text-sm font-bold text-vroom-heading underline decoration-2 underline-offset-2"
                      >
                        I don&apos;t have my VIN handy
                      </button>
                    </>
                  ) : (
                    <p className="text-sm font-semibold text-vroom-muted">
                      Manual entry — you&apos;ll add make, model, and year on the next step.
                    </p>
                  )}
                  {decodeError && <p className="text-sm font-bold text-red-600">{decodeError}</p>}
                </div>
              )}

              {currentStep === 2 && entryMode === "manual" && (
                <div className="space-y-4">
                  <div className="rounded-2xl border-2 border-black bg-vroom-card p-4 text-sm text-vroom-heading">
                    <p className="font-extrabold">Trust notice</p>
                    <p className="mt-1 font-semibold text-vroom-muted">
                      Listings without a verified VIN may be hidden from search results until
                      you add and verify your VIN later.
                    </p>
                  </div>
                  <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
                    <LabeledInput
                      label="Make"
                      value={listingData.make}
                      onChange={(value) =>
                        setListingData((prev) => ({ ...prev, make: value }))
                      }
                      placeholder="Toyota"
                    />
                    <LabeledInput
                      label="Model"
                      value={listingData.model}
                      onChange={(value) =>
                        setListingData((prev) => ({ ...prev, model: value }))
                      }
                      placeholder="Corolla"
                    />
                    <LabeledInput
                      label="Year"
                      value={listingData.year}
                      onChange={(value) =>
                        setListingData((prev) => ({ ...prev, year: value }))
                      }
                      type="number"
                      placeholder="2020"
                    />
                  </div>
                  <BodyTypeFields
                    bodyTypes={bodyTypes}
                    bodyTypeId={listingData.bodyTypeId}
                    bodyTypeOther={listingData.bodyTypeOther}
                    onBodyTypeChange={handleBodyTypeChange}
                    onBodyTypeOtherChange={(value) =>
                      setListingData((prev) => ({ ...prev, bodyTypeOther: value }))
                    }
                  />
                  <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
                    <SpecConfirmField
                      label="Seats"
                      value={listingData.seats}
                      meta={specMeta.seats}
                      onChange={(value) => handleSpecChange("seats", value)}
                      required
                      type="number"
                    />
                    <SpecConfirmField
                      label="Doors"
                      value={listingData.doors}
                      meta={specMeta.doors}
                      onChange={(value) => handleSpecChange("doors", value)}
                      type="number"
                    />
                    <SpecConfirmField
                      label="Transmission"
                      value={listingData.transmission}
                      meta={specMeta.transmission}
                      onChange={(value) => handleSpecChange("transmission", value)}
                      required
                      options={TRANSMISSION_OPTIONS}
                    />
                    <SpecConfirmField
                      label="Fuel type"
                      value={listingData.fuelType}
                      meta={specMeta.fuelType}
                      onChange={(value) => handleSpecChange("fuelType", value)}
                      required
                      options={FUEL_TYPE_OPTIONS}
                    />
                  </div>
                </div>
              )}

              {currentStep === 2 && entryMode === "vin" && (
                <div className="space-y-4">
                  <div className="rounded-2xl border-2 border-black bg-white p-5 shadow-neo space-y-2">
                    <p className="text-sm font-bold text-vroom-muted uppercase tracking-wider">
                      Decoded vehicle
                    </p>
                    <p className="text-2xl font-extrabold text-vroom-heading">
                      {assetLabel || "Your vehicle"}
                    </p>
                    <p className="text-sm font-semibold text-vroom-heading">VIN: {listingData.vin}</p>
                    <p className="text-sm font-semibold text-vroom-muted">
                      Amber border = estimate from body type — change if wrong.
                    </p>
                  </div>
                  <BodyTypeFields
                    bodyTypes={bodyTypes}
                    bodyTypeId={listingData.bodyTypeId}
                    bodyTypeOther={listingData.bodyTypeOther}
                    onBodyTypeChange={handleBodyTypeChange}
                    onBodyTypeOtherChange={(value) =>
                      setListingData((prev) => ({ ...prev, bodyTypeOther: value }))
                    }
                  />
                  <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
                    <SpecConfirmField
                      label="Seats"
                      value={listingData.seats}
                      meta={specMeta.seats}
                      onChange={(value) => handleSpecChange("seats", value)}
                      required
                      type="number"
                    />
                    <SpecConfirmField
                      label="Doors"
                      value={listingData.doors}
                      meta={specMeta.doors}
                      onChange={(value) => handleSpecChange("doors", value)}
                      type="number"
                    />
                    <SpecConfirmField
                      label="Transmission"
                      value={listingData.transmission}
                      meta={specMeta.transmission}
                      onChange={(value) => handleSpecChange("transmission", value)}
                      required
                      options={TRANSMISSION_OPTIONS}
                    />
                    <SpecConfirmField
                      label="Fuel type"
                      value={listingData.fuelType}
                      meta={specMeta.fuelType}
                      onChange={(value) => handleSpecChange("fuelType", value)}
                      required
                      options={FUEL_TYPE_OPTIONS}
                    />
                  </div>
                </div>
              )}

              {currentStep === 3 && (
                <div className="space-y-4">
                  <label className="block">
                    <FormFieldLabel>Pickup address</FormFieldLabel>
                    <div className="border-2 border-black rounded-2xl bg-white px-4 py-3 focus-within:ring-2 focus-within:ring-vroom-accent focus-within:ring-offset-1">
                      <input
                        value={listingData.address}
                        onChange={(e) =>
                          setListingData((prev) => ({ ...prev, address: e.target.value }))
                        }
                        placeholder="Type your address"
                        className="w-full bg-transparent text-vroom-heading outline-none"
                      />
                    </div>
                  </label>
                  {isPlacesLoading && (
                    <p className="text-sm font-semibold text-vroom-muted">Loading suggestions...</p>
                  )}
                  {placePredictions.length > 0 && (
                    <div className="rounded-2xl border-2 border-black bg-white p-2 max-h-52 overflow-y-auto shadow-neo">
                      {placePredictions.map((prediction) => (
                        <button
                          key={prediction.placeId || prediction.place_id}
                          type="button"
                          onClick={() => selectAddressPrediction(prediction)}
                          className="w-full text-left rounded-xl px-3 py-2 transition hover:bg-vroom-card"
                        >
                          <p className="text-sm font-bold text-vroom-heading">
                            {prediction.structured_formatting?.main_text || prediction.description}
                          </p>
                          <p className="text-xs font-semibold text-vroom-muted">
                            {prediction.structured_formatting?.secondary_text || ""}
                          </p>
                        </button>
                      ))}
                    </div>
                  )}
                  {placesError && <p className="text-sm font-bold text-red-600">{placesError}</p>}
                  <p className="text-sm font-semibold text-vroom-muted">
                    Choose one suggested address so coordinates save correctly.
                  </p>
                </div>
              )}

              {currentStep === 4 && (
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
                    className="flex cursor-pointer flex-col items-center justify-center rounded-[1.5rem] border-2 border-dashed border-black bg-vroom-surface p-10 transition hover:bg-vroom-card"
                  >
                    <UploadCloud className="h-10 w-10 text-gray-400 mb-2" />
                    <p className="font-semibold text-gray-900">Add photos</p>
                    <p className="text-sm text-gray-500 mt-1">
                      Drag images here or click to choose (images only)
                    </p>
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

              {currentStep === 5 && (
                <div className="mx-auto w-full max-w-md space-y-8">
                  <LabeledInput
                    label="Listing title"
                    value={listingData.listingTitle}
                    onChange={(value) =>
                      setListingData((prev) => ({ ...prev, listingTitle: value }))
                    }
                    placeholder="Perfect AWD for your weekend ski trip"
                  />
                  {assetLabel && (
                    <p className="text-sm font-semibold text-vroom-muted">Vehicle: {assetLabel}</p>
                  )}
                  <div className="flex items-center justify-center gap-8">
                    <button
                      type="button"
                      onClick={() =>
                        setListingData((prev) => ({
                          ...prev,
                          price: Math.max(5, Number(prev.price) - 5),
                        }))
                      }
                      className="h-12 w-12 rounded-full border-2 border-black bg-white text-2xl font-bold hover:bg-vroom-card"
                    >
                      -
                    </button>
                    <input
                      value={listingData.price}
                      onChange={(e) =>
                        setListingData((prev) => ({ ...prev, price: Number(e.target.value) || 0 }))
                      }
                      type="number"
                      className="w-44 bg-transparent text-center font-extrabold text-6xl text-vroom-heading outline-none"
                    />
                    <button
                      type="button"
                      onClick={() =>
                        setListingData((prev) => ({ ...prev, price: Number(prev.price) + 5 }))
                      }
                      className="h-12 w-12 rounded-full border-2 border-black bg-white text-2xl font-bold hover:bg-vroom-card"
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

      <footer className="fixed bottom-0 left-0 right-0 z-50 flex h-24 items-center justify-between border-t-4 border-black bg-vroom-surface px-10">
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
          disabled={!canProceed || isPublishing || isDecoding}
          className="rounded-full border-2 border-black border-b-4 bg-vroom-accent px-8 py-3 font-extrabold text-white active:border-b-0 disabled:opacity-40"
        >
          {currentStep === 1 && isDecoding
            ? "Decoding..."
            : currentStep === TOTAL_STEPS
              ? isPublishing
                ? "Publishing..."
                : "Publish Listing"
              : "Next"}
        </button>
      </footer>
    </div>
  );
}
