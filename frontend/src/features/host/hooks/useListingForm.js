import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { apiPatch, apiPost } from "@/shared/api/api";
import { useAuth } from "@/context/AuthContext";
import { resolvePredictionCoordinates } from "@/shared/lib/placesAutocomplete";
import { usePlacesAutocomplete } from "@/shared/hooks/usePlacesAutocomplete";
import { MIN_LISTING_PHOTOS } from "@/features/host/constants";

export const emptyListingForm = {
  title: "",
  make: "",
  model: "",
  year: "",
  mileage: "",
  vehicleClassId: "",
  pricePerDay: 120,
  instantBook: true,
  transmission: "Automatic",
  fuelType: "Gas",
  seats: 5,
  doors: 4,
  description: "",
  guidelines: "",
  features: [],
  images: [],
  address: "",
  latitude: null,
  longitude: null,
  isCompanyOwned: true,
  areaId: "",
  locationSourceType: "BRANCH",
  branchId: "",
  parkingSpotId: "",
  lat: 43.6532,
  lng: -79.3832,
  cityZone: "toronto-core",
};

function omitUndefined(obj) {
  return Object.fromEntries(
    Object.entries(obj).filter(([, value]) => value !== undefined),
  );
}

/** Owns the create/edit listing form: fields, photos, location picking, and persistence. */
export function useListingForm({
  isAdmin,
  companyLocations,
  isMapLoaded,
  refresh,
  refreshMe,
  setError,
  setSuccess,
  setActiveTab,
}) {
  const { ensureVerifiedEmail } = useAuth();
  const [listingForm, setListingForm] = useState(() => ({
    ...emptyListingForm,
    isCompanyOwned: isAdmin,
  }));
  const [editingListingId, setEditingListingId] = useState(null);
  const [pendingPhotoFiles, setPendingPhotoFiles] = useState([]);
  const [pendingPhotoPreviewUrls, setPendingPhotoPreviewUrls] = useState([]);
  const [isDragOver, setIsDragOver] = useState(false);
  const [isSavingListing, setIsSavingListing] = useState(false);
  const [createSuccessListing, setCreateSuccessListing] = useState(null);
  const [updateSaveSignal, setUpdateSaveSignal] = useState(0);
  const [baselineKey, setBaselineKey] = useState(0);
  const baselineRef = useRef("");
  const [addressQuery, setAddressQuery] = useState("");
  const [isMapModalOpen, setIsMapModalOpen] = useState(false);
  const [isReverseGeocoding, setIsReverseGeocoding] = useState(false);
  const [locationMode, setLocationMode] = useState(isAdmin ? "hub" : "custom");
  const [tempLocation, setTempLocation] = useState({ lat: null, lng: null, address: "" });
  const fileInputRef = useRef(null);
  const geocoderRef = useRef(null);

  const {
    predictions: placePredictions,
    isLoading: isPlacesLoading,
    placesError,
    setPlacesError,
    setPredictions: setPlacePredictions,
  } = usePlacesAutocomplete(addressQuery, {
    debounceMs: 250,
    country: "ca",
    mapsReady: isMapLoaded,
  });

  useEffect(() => {
    if (!isMapLoaded || !window.google?.maps) return;
    if (!geocoderRef.current) {
      geocoderRef.current = new window.google.maps.Geocoder();
    }
  }, [isMapLoaded]);

  useEffect(() => {
    if (!isMapModalOpen) return;
    const lat = Number(listingForm.latitude ?? listingForm.lat);
    const lng = Number(listingForm.longitude ?? listingForm.lng);
    setTempLocation({
      lat: Number.isFinite(lat) ? lat : null,
      lng: Number.isFinite(lng) ? lng : null,
      address: listingForm.address || "",
    });
  }, [
    isMapModalOpen,
    listingForm.address,
    listingForm.lat,
    listingForm.latitude,
    listingForm.lng,
    listingForm.longitude,
  ]);

  useEffect(() => {
    const urls = pendingPhotoFiles.map((file) => URL.createObjectURL(file));
    setPendingPhotoPreviewUrls(urls);
    return () => {
      urls.forEach((url) => URL.revokeObjectURL(url));
    };
  }, [pendingPhotoFiles]);

  const selectedHubBranch = useMemo(
    () =>
      companyLocations.branches.find(
        (branch) => Number(branch.branchId) === Number(listingForm.branchId),
      ) || null,
    [companyLocations.branches, listingForm.branchId],
  );

  const existingListingPhotoUrls = useMemo(
    () =>
      (Array.isArray(listingForm.images) ? listingForm.images : [])
        .filter(Boolean)
        .slice(0, 20),
    [listingForm.images],
  );

  const pendingPhotoCount = pendingPhotoFiles.length;
  const meetsPhotoRequirement = editingListingId
    ? true
    : pendingPhotoCount >= MIN_LISTING_PHOTOS;
  const hasConfirmedLocation =
    Number.isFinite(Number(listingForm.latitude)) && Number.isFinite(Number(listingForm.longitude));

  const getFormSnapshot = useCallback(
    () =>
      JSON.stringify({
        listingForm,
        addressQuery,
        pendingPhotoCount,
        locationMode,
        editingListingId,
      }),
    [listingForm, addressQuery, pendingPhotoCount, locationMode, editingListingId],
  );

  const syncFormBaseline = () => {
    baselineRef.current = getFormSnapshot();
  };

  useEffect(() => {
    syncFormBaseline();
  }, [baselineKey, getFormSnapshot]);

  const isDirty = useMemo(() => {
    if (!baselineRef.current) return false;
    return getFormSnapshot() !== baselineRef.current;
  }, [
    baselineKey,
    getFormSnapshot,
    listingForm,
    addressQuery,
    pendingPhotoCount,
    locationMode,
    editingListingId,
  ]);

  const confirmLeaveIfDirty = () => {
    if (!isDirty) return true;
    return window.confirm("You have unsaved changes. Are you sure you want to leave?");
  };

  const applyHubBranchSelection = (branchIdValue) => {
    const selectedBranch =
      companyLocations.branches.find(
        (branch) => Number(branch.branchId) === Number(branchIdValue),
      ) || null;
    if (!selectedBranch) {
      setListingForm((prev) => ({ ...prev, branchId: branchIdValue || "" }));
      return;
    }

    const derivedCityZone =
      (selectedBranch.city || "")
        .toLowerCase()
        .trim()
        .replace(/\s+/g, "-") || "toronto-core";

    setListingForm((prev) => ({
      ...prev,
      isCompanyOwned: true,
      areaId: String(selectedBranch.areaId || ""),
      locationSourceType: "BRANCH",
      branchId: String(selectedBranch.branchId),
      parkingSpotId: "",
      address: selectedBranch.address || "",
      latitude: selectedBranch.lat,
      longitude: selectedBranch.lng,
      lat: selectedBranch.lat,
      lng: selectedBranch.lng,
      cityZone: derivedCityZone,
    }));
    setAddressQuery(selectedBranch.address || "");
  };

  // ponytail: replaces the old loadAll() side effect that seeded default branch ids;
  // runs whenever company branches arrive so admin form has a sane default.
  useEffect(() => {
    if (!isAdmin) return;
    if (!companyLocations.branches.length) return;
    const defaultBranch = companyLocations.branches[0];
    setListingForm((prev) => ({
      ...prev,
      areaId: prev.areaId || String(defaultBranch.areaId),
      branchId: prev.branchId || String(defaultBranch.branchId),
    }));
  }, [isAdmin, companyLocations.branches]);

  useEffect(() => {
    if (locationMode !== "hub") return;
    if (!listingForm.branchId) return;
    if (listingForm.address) return;
    applyHubBranchSelection(listingForm.branchId);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [locationMode, listingForm.branchId, listingForm.address, companyLocations.branches]);

  const toggleFeature = (featureName) => {
    setListingForm((prev) => ({
      ...prev,
      features: prev.features.includes(featureName)
        ? prev.features.filter((item) => item !== featureName)
        : [...prev.features, featureName],
    }));
  };

  const selectUploadFiles = (fileList) => {
    const incoming = Array.from(fileList || []).filter(
      (file) => file && file.type.startsWith("image/"),
    );
    if (!incoming.length) {
      setError("Choose image files only (JPEG, PNG, WebP, etc.).");
      return;
    }
    setPendingPhotoFiles((prev) => {
      const byKey = new Map(prev.map((f) => [`${f.name}:${f.size}:${f.lastModified}`, f]));
      incoming.forEach((file) => {
        byKey.set(`${file.name}:${file.size}:${file.lastModified}`, file);
      });
      return Array.from(byKey.values());
    });
    setError("");
  };

  const removePendingPhoto = (index) => {
    setPendingPhotoFiles((prev) => prev.filter((_, fileIndex) => fileIndex !== index));
  };

  const clearPendingPhotos = () => setPendingPhotoFiles([]);

  const onDropFile = (event) => {
    event.preventDefault();
    setIsDragOver(false);
    selectUploadFiles(event.dataTransfer.files);
  };

  const uploadListingPhotos = async (listingId, options = {}) => {
    const { skipRefresh = false, skipSuccess = false } = options;
    if (!pendingPhotoFiles.length) {
      setError("Pick image files first.");
      return undefined;
    }
    if (!listingId) {
      setError("Pick a target listing first.");
      return undefined;
    }
    setError("");
    setSuccess("");
    const filesToUpload = [...pendingPhotoFiles];
    try {
      for (const file of filesToUpload) {
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
      setPendingPhotoFiles([]);
      if (!skipSuccess) {
        setSuccess(`Uploaded ${filesToUpload.length} photo(s) to listing #${listingId}.`);
      }
      if (!skipRefresh) {
        await refresh();
      }
      return { uploadedCount: filesToUpload.length };
    } catch (err) {
      setError(err?.message || "Could not upload listing photos.");
      throw err;
    }
  };

  const createListing = async (event) => {
    event.preventDefault();
    setError("");
    setSuccess("");

    if (!isAdmin && !editingListingId && !ensureVerifiedEmail()) {
      return;
    }

    if (!editingListingId && pendingPhotoCount < MIN_LISTING_PHOTOS) {
      setError(`Add at least ${MIN_LISTING_PHOTOS} photos before saving a new listing.`);
      return;
    }

    setIsSavingListing(true);
    const wasEditing = Boolean(editingListingId);
    try {
      const usesCompanyDropdown = isAdmin && locationMode === "hub";
      const payload = omitUndefined({
        title: listingForm.title || undefined,
        brand: listingForm.make || undefined,
        make: listingForm.make || undefined,
        model: listingForm.model || undefined,
        year: listingForm.year ? Number(listingForm.year) : undefined,
        mileage: listingForm.mileage ? Number(listingForm.mileage) : undefined,
        vehicleClassId: listingForm.vehicleClassId ? Number(listingForm.vehicleClassId) : undefined,
        transmission: listingForm.transmission || undefined,
        fuelType: listingForm.fuelType || undefined,
        seats: listingForm.seats ? Number(listingForm.seats) : undefined,
        doors: listingForm.doors ? Number(listingForm.doors) : undefined,
        description: listingForm.description || undefined,
        guidelines: listingForm.guidelines,
        features: listingForm.features,
        images: listingForm.images,
        pickupAddress: listingForm.address || undefined,
        latitude: listingForm.latitude ?? undefined,
        longitude: listingForm.longitude ?? undefined,
        pricePerDay: Number(listingForm.pricePerDay),
        instantBook: isAdmin ? undefined : Boolean(listingForm.instantBook),
        lat: usesCompanyDropdown ? undefined : Number(listingForm.lat),
        lng: usesCompanyDropdown ? undefined : Number(listingForm.lng),
        isCompanyOwned: isAdmin ? isAdmin : undefined,
        areaId:
          usesCompanyDropdown && selectedHubBranch?.areaId
            ? Number(selectedHubBranch.areaId)
            : undefined,
        branchId:
          usesCompanyDropdown && listingForm.branchId
            ? Number(listingForm.branchId)
            : undefined,
        parkingSpotId: undefined,
        locationSourceType: usesCompanyDropdown ? "BRANCH" : undefined,
        cityZone: usesCompanyDropdown
          ? selectedHubBranch?.city?.toLowerCase()?.replace(/\s+/g, "-") || "toronto-core"
          : listingForm.cityZone,
      });

      let targetListingId = null;
      if (wasEditing) {
        await apiPatch(`/api/listings/${editingListingId}`, payload, true);
        targetListingId = Number(editingListingId);
      } else {
        const response = await apiPost("/api/listings", payload, true);
        targetListingId = response?.listing?.listingId || null;
      }

      const locationLat = Number(usesCompanyDropdown ? listingForm.lat : payload.lat);
      const locationLng = Number(usesCompanyDropdown ? listingForm.lng : payload.lng);
      const locationZone = payload.cityZone || listingForm.cityZone;
      if (
        targetListingId &&
        Number.isFinite(locationLat) &&
        Number.isFinite(locationLng) &&
        locationZone
      ) {
        await apiPost(
          `/api/listings/${targetListingId}/location`,
          {
            lat: locationLat,
            lng: locationLng,
            cityZone: locationZone,
          },
          true,
        );
      }

      if (targetListingId && pendingPhotoFiles.length) {
        await uploadListingPhotos(targetListingId, {
          skipRefresh: true,
          skipSuccess: true,
        });
      }

      if (wasEditing) {
        setUpdateSaveSignal((count) => count + 1);
        resetFormState();
        await refresh();
      } else {
        setCreateSuccessListing({
          listingId: targetListingId,
          title:
            listingForm.title?.trim() ||
            `${listingForm.make || ""} ${listingForm.model || ""}`.trim() ||
            "Your listing",
          pricePerDay: Number(listingForm.pricePerDay),
        });
        await refreshMe().catch(() => {});
        await refresh();
      }
    } catch (err) {
      setError(err?.message || (editingListingId ? "Could not update listing." : "Could not create listing."));
    } finally {
      setIsSavingListing(false);
    }
  };

  const resetFormState = () => {
    setListingForm((prev) => ({
      ...emptyListingForm,
      isCompanyOwned: isAdmin,
      areaId: prev.areaId || "",
      branchId: prev.branchId || "",
    }));
    setPendingPhotoFiles([]);
    setAddressQuery("");
    setLocationMode(isAdmin ? "hub" : "custom");
    setEditingListingId(null);
    setBaselineKey((key) => key + 1);
  };

  const dismissCreateSuccess = (nextTab = null) => {
    setCreateSuccessListing(null);
    resetFormState();
    if (nextTab) {
      setActiveTab(nextTab);
    }
  };

  const startEditListing = (listing) => {
    if (!confirmLeaveIfDirty()) return;

    const resolvedAddress = listing.pickupAddress || "";
    const resolvedLat = listing.latitude ?? listing.lat ?? null;
    const resolvedLng = listing.longitude ?? listing.lng ?? null;
    const nextMode = listing.locationSourceType === "BRANCH" && listing.branchId ? "hub" : "custom";

    setEditingListingId(listing.listingId);
    setListingForm((prev) => ({
      ...prev,
      title: listing.title || "",
      make: listing.make || listing.brand || "",
      model: listing.model || "",
      year: listing.year ?? "",
      mileage: listing.mileage ?? "",
      vehicleClassId: listing.vehicleClassId ?? "",
      pricePerDay: listing.pricePerDay ?? prev.pricePerDay,
      transmission: listing.transmission || prev.transmission,
      fuelType: listing.fuelType || prev.fuelType,
      seats: listing.seats ?? prev.seats,
      doors: listing.doors ?? prev.doors,
      description: listing.description || "",
      guidelines: listing.guidelines || listing.rules || "",
      features: Array.isArray(listing.features) ? listing.features : [],
      images: Array.isArray(listing.images)
        ? listing.images
        : Array.isArray(listing.photos)
          ? listing.photos
          : [],
      address: resolvedAddress,
      latitude: resolvedLat,
      longitude: resolvedLng,
      lat: resolvedLat,
      lng: resolvedLng,
      cityZone: listing.cityZone || prev.cityZone,
      areaId: listing.areaId ? String(listing.areaId) : prev.areaId,
      branchId: listing.branchId ? String(listing.branchId) : prev.branchId,
      locationSourceType: "BRANCH",
      parkingSpotId: "",
      isCompanyOwned: isAdmin ? true : Boolean(listing.isCompanyOwned),
      instantBook: listing.instantBook !== false,
    }));
    setAddressQuery(resolvedAddress);
    setLocationMode(isAdmin ? nextMode : "custom");
    setPendingPhotoFiles([]);
    setActiveTab("create_listing");
    setError("");
    setSuccess("");
    setBaselineKey((key) => key + 1);
  };

  const cancelForm = () => {
    if (!confirmLeaveIfDirty()) return;
    resetFormState();
    setActiveTab("overview");
  };

  const selectAddressPrediction = async (prediction) => {
    try {
      const { lat, lng } = await resolvePredictionCoordinates(prediction);
      const formatted = prediction.description || addressQuery;
      setAddressQuery(formatted);
      setListingForm((prev) => ({
        ...prev,
        address: formatted,
        latitude: lat,
        longitude: lng,
        lat,
        lng,
      }));
      setPlacePredictions([]);
    } catch {
      setPlacesError("Could not resolve that address.");
    }
  };

  const selectMapPoint = (lat, lng) => {
    setListingForm((prev) => ({
      ...prev,
      latitude: lat,
      longitude: lng,
      lat,
      lng,
    }));

    if (!geocoderRef.current) return;
    geocoderRef.current.geocode({ location: { lat, lng }, region: "ca" }, (results, status) => {
      if (status === "OK" && results?.[0]?.formatted_address) {
        const formatted = results[0].formatted_address;
        setAddressQuery(formatted);
        setListingForm((prev) => ({ ...prev, address: formatted }));
      }
    });
  };

  const reverseGeocodeLocation = (lat, lng) =>
    new Promise((resolve) => {
      if (!geocoderRef.current) {
        resolve("");
        return;
      }
      setIsReverseGeocoding(true);
      geocoderRef.current.geocode({ location: { lat, lng }, region: "ca" }, (results, status) => {
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
    const resolved = await reverseGeocodeLocation(newLat, newLng);
    if (resolved) {
      setTempLocation((prev) => ({ ...prev, address: resolved }));
    }
  };

  const confirmMapPickerLocation = () => {
    selectMapPoint(tempLocation.lat, tempLocation.lng);
    if (tempLocation.address) {
      setAddressQuery(tempLocation.address);
      setListingForm((prev) => ({ ...prev, address: tempLocation.address }));
    }
    setIsMapModalOpen(false);
  };

  return {
    listingForm,
    setListingForm,
    editingListingId,
    pendingPhotoFiles,
    pendingPhotoPreviewUrls,
    isDragOver,
    setIsDragOver,
    isSavingListing,
    createSuccessListing,
    updateSaveSignal,
    isDirty,
    confirmLeaveIfDirty,
    dismissCreateSuccess,
    addressQuery,
    setAddressQuery,
    placePredictions,
    isPlacesLoading,
    placesError,
    isMapModalOpen,
    setIsMapModalOpen,
    isReverseGeocoding,
    tempLocation,
    locationMode,
    setLocationMode,
    selectedHubBranch,
    existingListingPhotoUrls,
    pendingPhotoCount,
    meetsPhotoRequirement,
    hasConfirmedLocation,
    fileInputRef,
    createListing,
    startEditListing,
    cancelForm,
    toggleFeature,
    selectUploadFiles,
    removePendingPhoto,
    clearPendingPhotos,
    onDropFile,
    selectAddressPrediction,
    openMapPicker,
    handlePinDrop,
    confirmMapPickerLocation,
    applyHubBranchSelection,
  };
}
