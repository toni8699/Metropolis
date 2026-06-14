import { useEffect, useMemo, useRef, useState } from "react";
import {
  Bluetooth,
  BarChart3,
  Building2,
  CalendarDays,
  CarFront,
  Check,
  Crosshair,
  KeyRound,
  DollarSign,
  LayoutDashboard,
  MapPin,
  RefreshCw,
  ShieldCheck,
  Smartphone,
  Snowflake,
  Sun,
  Pencil,
  Trash2,
  UploadCloud,
  Users,
  X,
} from "lucide-react";
import { GoogleMap, Marker, useJsApiLoader } from "@react-google-maps/api";
import {
  Bar,
  CartesianGrid,
  Cell,
  Line,
  LineChart,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { Link, useLocation } from "react-router-dom";
import { apiDelete, apiGet, apiPatch, apiPost } from "@/shared/api/api";
import Layout from "@/layout/Layout";
import {
  fetchPlacePredictions,
  resolvePredictionCoordinates,
} from "@/shared/lib/placesAutocomplete";
import { CANADA_CENTER, CANADA_MAP_OPTIONS } from "@/shared/lib/location";
import { MIN_LISTING_PHOTOS } from "@/shared/lib/listingPhotos";
import MapPinPicker from "@/features/host/components/MapPinPicker";
import {
  bookingStatusBadgeClass,
  formatBookingStatusLabel,
  isPendingApproval,
} from "@/shared/lib/bookingStatus";
import InstantBookToggle from "@/features/host/components/InstantBookToggle";

function omitUndefined(obj) {
  return Object.fromEntries(
    Object.entries(obj).filter(([, value]) => value !== undefined),
  );
}

const emptyListingForm = {
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

const mapContainerStyle = {
  width: "100%",
  height: "260px",
};

function getNavItems(isAdmin) {
  const items = [{ id: "overview", label: "Overview", icon: LayoutDashboard }];
  if (isAdmin) {
    items.push(
      { id: "fleet_listings", label: "Fleet Listings", icon: CarFront },
      { id: "host_listings", label: "Host Listings", icon: Building2 },
      { id: "create_listing", label: "Create Listing", icon: UploadCloud },
      { id: "users", label: "Users", icon: Users },
      { id: "kyc", label: "KYC Queue", icon: ShieldCheck },
    );
  } else {
    items.push(
      { id: "listings", label: "Listings", icon: CarFront },
      { id: "create_listing", label: "Create Listing", icon: UploadCloud },
    );
  }
  items.push({ id: "bookings", label: "Bookings", icon: CalendarDays });
  return items;
}

const pageTitles = {
  overview: "Overview",
  listings: "Manage Listings",
  fleet_listings: "Fleet Listings",
  host_listings: "Host Listings",
  create_listing: "Create Listing",
  users: "Users",
  kyc: "KYC Queue",
  bookings: "Bookings",
};

const pieColors = ["#4f46e5", "#818cf8", "#c7d2fe"];
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

export default function HostDashboard({ mode = "admin" }) {
  const location = useLocation();
  const isAdmin = mode === "admin";
  const navItems = useMemo(() => getNavItems(isAdmin), [isAdmin]);
  const [activeTab, setActiveTab] = useState("overview");
  const [analytics, setAnalytics] = useState(null);
  const [bookings, setBookings] = useState([]);
  const [listings, setListings] = useState([]);
  const [hostListings, setHostListings] = useState([]);
  const [users, setUsers] = useState([]);
  const [kycQueue, setKycQueue] = useState([]);
  const [companyLocations, setCompanyLocations] = useState({
    areas: [],
    branches: [],
    parkingSpots: [],
    vehicleClasses: [],
  });
  const [listingForm, setListingForm] = useState(() => ({
    ...emptyListingForm,
    isCompanyOwned: isAdmin,
  }));
  const [editingListingId, setEditingListingId] = useState(null);
  const [pendingPhotoFiles, setPendingPhotoFiles] = useState([]);
  const [pendingPhotoPreviewUrls, setPendingPhotoPreviewUrls] = useState([]);
  const [isDragOver, setIsDragOver] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [isSavingListing, setIsSavingListing] = useState(false);
  const [isSyncingFleet, setIsSyncingFleet] = useState(false);
  const [bookingActionId, setBookingActionId] = useState(null);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");
  const [addressQuery, setAddressQuery] = useState("");
  const [placePredictions, setPlacePredictions] = useState([]);
  const [isPlacesLoading, setIsPlacesLoading] = useState(false);
  const [placesError, setPlacesError] = useState("");
  const [isMapModalOpen, setIsMapModalOpen] = useState(false);
  const [isReverseGeocoding, setIsReverseGeocoding] = useState(false);
  const [locationMode, setLocationMode] = useState(isAdmin ? "hub" : "custom");
  const [tempLocation, setTempLocation] = useState({
    lat: null,
    lng: null,
    address: "",
  });
  const fileInputRef = useRef(null);
  const geocoderRef = useRef(null);

  const activePageTitle = useMemo(
    () => pageTitles[activeTab] || (isAdmin ? "Admin Dashboard" : "Host Dashboard"),
    [activeTab, isAdmin],
  );

  const apiKey = import.meta.env.VITE_GOOGLE_MAPS_API_KEY;
  const { isLoaded: isMapLoaded } = useJsApiLoader({
    id: "google-maps-script",
    googleMapsApiKey: apiKey || "",
    libraries: ["places"],
  });

  useEffect(() => {
    if (!isMapLoaded || !window.google?.maps) return;
    if (!geocoderRef.current) {
      geocoderRef.current = new window.google.maps.Geocoder();
    }
  }, [isMapLoaded]);

  useEffect(() => {
    if (!addressQuery.trim() || !window.google?.maps?.places) {
      setPlacePredictions([]);
      setIsPlacesLoading(false);
      setPlacesError("");
      return;
    }
    let cancelled = false;
    const t = window.setTimeout(async () => {
      setIsPlacesLoading(true);
      try {
        const predictions = await fetchPlacePredictions(addressQuery, {
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
      window.clearTimeout(t);
    };
  }, [addressQuery]);

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

  const selectedHubBranch = useMemo(
    () =>
      companyLocations.branches.find(
        (branch) => Number(branch.branchId) === Number(listingForm.branchId),
      ) || null,
    [companyLocations.branches, listingForm.branchId],
  );

  const recentBookings = useMemo(
    () =>
      bookings.slice(0, 5).map((booking) => ({
        user: booking.renterEmail || `User #${booking.renterUserId || "n/a"}`,
        car: booking.listingTitle || "Vehicle",
        dates: formatBookingWindow(booking.startAt, booking.endAt),
        status: booking.status || "PENDING",
      })),
    [bookings],
  );

  const revenueSeries = useMemo(() => buildRevenueSeries(bookings), [bookings]);
  const bookingsByLocationSeries = useMemo(
    () => buildBookingsByLocation(bookings),
    [bookings],
  );

  const pendingApprovalBookings = useMemo(
    () => bookings.filter((booking) => isPendingApproval(booking.status)),
    [bookings],
  );

  const loadAll = async () => {
    setError("");
    setIsLoading(true);
    try {
      if (isAdmin) {
        const [analyticsRes, bookingsRes, listingsRes, hostListingsRes, usersRes, locationsRes, kycRes] =
          await Promise.all([
            apiGet("/api/analytics?scope=fleet", true),
            apiGet("/api/bookings?scope=fleet", true),
            apiGet("/api/listings?scope=fleet", true),
            apiGet("/api/listings?scope=host", true),
            apiGet("/api/users", true),
            apiGet("/api/company-locations", true),
            apiGet("/api/users/kyc?status=pending", true),
          ]);
        setAnalytics(analyticsRes?.analytics || null);
        setBookings(bookingsRes?.bookings || []);
        setListings(listingsRes?.listings || []);
        setHostListings(hostListingsRes?.listings || []);
        setUsers(usersRes?.users || []);
        setKycQueue(kycRes?.queue || []);
        const nextLocations = {
          areas: locationsRes?.areas || [],
          branches: locationsRes?.branches || [],
          parkingSpots: locationsRes?.parkingSpots || [],
          vehicleClasses: locationsRes?.vehicleClasses || [],
        };
        setCompanyLocations(nextLocations);
        if (nextLocations.branches.length) {
          const defaultBranch = nextLocations.branches[0];
          setListingForm((prev) => ({
            ...prev,
            areaId: prev.areaId || String(defaultBranch.areaId),
            branchId: prev.branchId || String(defaultBranch.branchId),
          }));
        }
      } else {
        const [listingsRes, bookingsRes, analyticsRes, vehicleClassesRes] = await Promise.all([
          apiGet("/api/listings?scope=mine", true),
          apiGet("/api/bookings?scope=owner", true).catch(() => ({ bookings: [] })),
          apiGet("/api/analytics?scope=owner", true).catch(() => ({ analytics: null })),
          apiGet("/api/vehicle-classes", true).catch(() => ({ vehicleClasses: [] })),
        ]);
        const ownerListings = listingsRes?.listings || [];
        const ownerBookings = bookingsRes?.bookings || [];
        setListings(ownerListings);
        setBookings(ownerBookings);
        setAnalytics(analyticsRes?.analytics || null);
        setUsers([]);
        setCompanyLocations({
          areas: [],
          branches: [],
          parkingSpots: [],
          vehicleClasses: vehicleClassesRes?.vehicleClasses || [],
        });
      }
    } catch (err) {
      setError(err?.message || `Could not load ${isAdmin ? "admin" : "host"} dashboard.`);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadAll();
  }, [isAdmin, location.pathname]);

  useEffect(() => {
    const urls = pendingPhotoFiles.map((file) => URL.createObjectURL(file));
    setPendingPhotoPreviewUrls(urls);
    return () => {
      urls.forEach((url) => URL.revokeObjectURL(url));
    };
  }, [pendingPhotoFiles]);

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

  const createListing = async (event) => {
    event.preventDefault();
    setError("");
    setSuccess("");

    if (!editingListingId && pendingPhotoCount < MIN_LISTING_PHOTOS) {
      setError(`Add at least ${MIN_LISTING_PHOTOS} photos before saving a new listing.`);
      return;
    }

    setIsSavingListing(true);
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
      if (editingListingId) {
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

      let uploadedCount = 0;
      if (targetListingId && pendingPhotoFiles.length) {
        const uploadResult = await uploadListingPhotos(targetListingId, {
          skipRefresh: true,
          skipSuccess: true,
        });
        uploadedCount = uploadResult?.uploadedCount || 0;
      }
      setListingForm((prev) => ({
        ...emptyListingForm,
        isCompanyOwned: isAdmin,
        areaId: prev.areaId || "",
        branchId: prev.branchId || "",
      }));
      setLocationMode(isAdmin ? "hub" : "custom");
      setEditingListingId(null);
      setSuccess(
        targetListingId
          ? uploadedCount > 0
            ? editingListingId
              ? `Listing updated and ${uploadedCount} photo(s) uploaded.`
              : `Listing created and ${uploadedCount} photo(s) uploaded.`
            : editingListingId
              ? "Listing updated successfully."
              : "Listing created successfully."
          : "Listing created successfully.",
      );
      await loadAll();
    } catch (err) {
      setError(err?.message || (editingListingId ? "Could not update listing." : "Could not create listing."));
    } finally {
      setIsSavingListing(false);
    }
  };

  const startEditListing = (listing) => {
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
  };

  const handleBookingDecision = async (bookingId, action) => {
    setError("");
    setSuccess("");
    setBookingActionId(bookingId);
    const status = action === "approve" ? "CONFIRMED" : "CANCELLED";
    try {
      await apiPatch(`/api/bookings/${bookingId}`, { status }, true);
      setSuccess(action === "approve" ? "Booking approved." : "Booking rejected.");
      await loadAll();
    } catch (err) {
      setError(err?.message || `Could not ${action} booking.`);
    } finally {
      setBookingActionId(null);
    }
  };

  const deleteListing = async (listingId) => {
    setError("");
    setSuccess("");
    try {
      await apiDelete(`/api/listings/${listingId}`, true);
      setSuccess("Listing deleted.");
      await loadAll();
    } catch (err) {
      setError(err?.message || "Could not delete listing.");
    }
  };

  const syncFleet = async () => {
    setError("");
    setSuccess("");
    setIsSyncingFleet(true);
    try {
      await apiPost("/api/fleet/sync", {}, true);
      setSuccess("Fleet synchronized.");
      await loadAll();
    } catch (err) {
      setError(err?.message || "Could not sync fleet.");
    } finally {
      setIsSyncingFleet(false);
    }
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

  const uploadListingPhotos = async (listingId, options = {}) => {
    const { skipRefresh = false, skipSuccess = false } = options;
    if (!pendingPhotoFiles.length) {
      setError("Pick image files first.");
      return;
    }
    if (!listingId) {
      setError("Pick a target listing first.");
      return;
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
        await loadAll();
      }
      return { uploadedCount: filesToUpload.length };
    } catch (err) {
      setError(err?.message || "Could not upload listing photos.");
      throw err;
    }
  };

  const onDropFile = (event) => {
    event.preventDefault();
    setIsDragOver(false);
    selectUploadFiles(event.dataTransfer.files);
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

  const hasConfirmedLocation =
    Number.isFinite(Number(listingForm.latitude)) && Number.isFinite(Number(listingForm.longitude));

  useEffect(() => {
    if (locationMode !== "hub") return;
    if (!listingForm.branchId) return;
    if (listingForm.address) return;
    applyHubBranchSelection(listingForm.branchId);
  }, [locationMode, listingForm.branchId, listingForm.address, companyLocations.branches]);

  const toggleFeature = (featureName) => {
    setListingForm((prev) => ({
      ...prev,
      features: prev.features.includes(featureName)
        ? prev.features.filter((item) => item !== featureName)
        : [...prev.features, featureName],
    }));
  };

  return (
    <Layout>
      <div className="fixed inset-x-0 top-28 md:top-[104px] bottom-0 z-0 flex border-t-4 border-black bg-[#D0F0C0] overflow-hidden">
        <aside className="w-64 shrink-0 border-r-4 border-black bg-[#f5f5d0] flex flex-col overflow-y-auto">
        <div className="p-6 border-b-2 border-black">
          <p className="text-2xl font-extrabold text-[#183B1E]">{isAdmin ? "VROOM Admin" : "VROOM Host"}</p>
        </div>
        <nav className="flex-1 py-6 space-y-2">
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = activeTab === item.id;
            return (
              <button
                key={item.id}
                onClick={() => setActiveTab(item.id)}
                className={`w-[calc(100%-2rem)] mx-4 px-4 py-2 rounded-lg flex items-center gap-3 text-sm transition ${
                  isActive
                    ? "border-2 border-black bg-[#dbe8be] text-[#183B1E] font-extrabold shadow-[3px_3px_0px_0px_rgba(24,59,30,0.35)]"
                    : "text-[#35593b] hover:bg-[#f5f5d0]"
                }`}
              >
                <Icon className="h-4 w-4" />
                {item.label}
              </button>
            );
          })}
        </nav>
        </aside>

        <div className="flex min-h-0 flex-1 flex-col overflow-y-auto">
          <header className="sticky top-0 z-10 flex h-20 shrink-0 items-center justify-between border-b-4 border-black bg-[#f5f5d0] px-11">
            <h1 className="text-3xl font-extrabold text-[#183B1E]">{activePageTitle}</h1>
            {isAdmin && (
              <button
                onClick={syncFleet}
                disabled={isSyncingFleet}
                className="rounded-full border-2 border-black border-b-4 bg-[#E34B31] px-4 py-2 font-extrabold text-white flex items-center gap-2 transition active:border-b-0 disabled:opacity-50"
              >
                <RefreshCw className={`h-4 w-4 ${isSyncingFleet ? "animate-spin" : ""}`} />
                {isSyncingFleet ? "Syncing..." : "Sync Fleet Now"}
              </button>
            )}
          </header>

          <main className="pb-10">
          {error && (
            <div className="mx-11 mt-6 rounded-xl border-2 border-black bg-[#ffd8cf] p-3 text-sm font-semibold text-[#7a2215]">
              {error}
            </div>
          )}
          {success && (
            <div className="mx-11 mt-6 rounded-xl border-2 border-black bg-[#dbe8be] p-3 text-sm font-semibold text-[#183B1E]">
              {success}
            </div>
          )}

          {activeTab === "overview" && (
            <>
              <section className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-6 p-11">
                <AnalyticsCard label="Total Listings" value={analytics?.listingCount ?? 0} />
                <AnalyticsCard label="Total Bookings" value={analytics?.bookingCount ?? 0} />
                <AnalyticsCard
                  label="Gross Daily Revenue"
                  value={`$${Number(analytics?.grossDailyRevenue || 0).toFixed(2)}`}
                />
                <AnalyticsCard
                  label={isAdmin ? "Paid Revenue" : "Active Listings"}
                  value={
                    isAdmin
                      ? `$${Number(analytics?.paidRevenue || 0).toFixed(2)}`
                      : String(analytics?.activeListings ?? 0)
                  }
                />
              </section>

              <section className="grid grid-cols-1 lg:grid-cols-3 gap-6 px-11 mt-2">
                <div className="lg:col-span-2 rounded-2xl border-4 border-black bg-[#f5f5d0] p-6 shadow-[8px_8px_0px_0px_rgba(24,59,30,0.45)]">
                  <h3 className="text-lg font-semibold text-gray-900 mb-4">Revenue (Past 30 Days)</h3>
                  <ResponsiveContainer width="100%" height={300}>
                    <LineChart data={revenueSeries}>
                      <defs>
                        <linearGradient id="revenueFill" x1="0" y1="0" x2="0" y2="1">
                          <stop offset="5%" stopColor="#4f46e5" stopOpacity={0.35} />
                          <stop offset="95%" stopColor="#4f46e5" stopOpacity={0.04} />
                        </linearGradient>
                      </defs>
                      <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                      <XAxis dataKey="day" stroke="#6b7280" />
                      <YAxis stroke="#6b7280" />
                      <Tooltip />
                      <Line
                        type="monotone"
                        dataKey="revenue"
                        stroke="#4f46e5"
                        strokeWidth={3}
                        dot={false}
                      />
                      <Bar dataKey="revenue" fill="url(#revenueFill)" opacity={0.25} barSize={16} />
                    </LineChart>
                  </ResponsiveContainer>
                </div>

                <div className="rounded-2xl border-4 border-black bg-[#f5f5d0] p-6 shadow-[8px_8px_0px_0px_rgba(24,59,30,0.45)]">
                  <h3 className="text-lg font-semibold text-gray-900 mb-4">Bookings by Location</h3>
                  <ResponsiveContainer width="100%" height={300}>
                    <PieChart>
                      <Pie
                        data={bookingsByLocationSeries}
                        dataKey="bookings"
                        nameKey="location"
                        innerRadius={48}
                        outerRadius={88}
                        paddingAngle={3}
                      >
                        {bookingsByLocationSeries.map((entry, index) => (
                          <Cell key={entry.location} fill={pieColors[index % pieColors.length]} />
                        ))}
                      </Pie>
                      <Tooltip />
                    </PieChart>
                  </ResponsiveContainer>
                </div>
              </section>

              <section className="mx-11 mt-6 overflow-hidden rounded-2xl border-4 border-black bg-[#f5f5d0] shadow-[8px_8px_0px_0px_rgba(24,59,30,0.45)]">
                <div className="px-6 py-4 border-b border-gray-200">
                  <h3 className="text-lg font-semibold text-gray-900">Recent Bookings</h3>
                </div>
                <table className="w-full text-left border-collapse">
                  <thead>
                    <tr className="bg-gray-50 border-b border-gray-200 text-xs uppercase text-gray-500 font-semibold tracking-wider">
                      <th className="px-6 py-4">User</th>
                      <th className="px-6 py-4">Car</th>
                      <th className="px-6 py-4">Dates</th>
                      <th className="px-6 py-4">Status</th>
                    </tr>
                  </thead>
                  <tbody>
                    {recentBookings.length === 0 ? (
                      <tr>
                        <td colSpan={4} className="px-6 py-8 text-sm text-gray-500 text-center">
                          {isAdmin
                            ? "No bookings yet."
                            : "No bookings on your listings yet."}
                        </td>
                      </tr>
                    ) : (
                      recentBookings.map((row, idx) => (
                        <tr
                          key={`${row.user}-${idx}`}
                          className="border-b border-gray-100 hover:bg-gray-50 transition"
                        >
                          <td className="px-6 py-4 text-sm text-gray-900">{row.user}</td>
                          <td className="px-6 py-4 text-sm text-gray-900">{row.car}</td>
                          <td className="px-6 py-4 text-sm text-gray-900">{row.dates}</td>
                          <td className="px-6 py-4 text-sm text-gray-900">
                            <span className="px-2.5 py-0.5 rounded-full text-xs font-medium bg-gray-100 text-gray-700">
                              {row.status}
                            </span>
                          </td>
                        </tr>
                      ))
                    )}
                  </tbody>
                </table>
              </section>
            </>
          )}

          {activeTab === "create_listing" && (
            <section className="pb-10">
              <div className="px-11 pt-11">
                <h2 className="text-2xl font-semibold text-gray-900">
                  {editingListingId
                    ? `Edit Listing #${editingListingId}`
                    : isAdmin
                      ? "Create Company Listing"
                      : "Create Listing"}
                </h2>
              </div>
              <div className="max-w-4xl mx-auto mt-6 rounded-2xl border-4 border-black bg-[#f5f5d0] p-8 shadow-[8px_8px_0px_0px_rgba(24,59,30,0.45)]">
                <form className="space-y-6" onSubmit={createListing}>
                  <section className="space-y-4">
                    <h3 className="text-sm font-semibold uppercase tracking-wider text-gray-500">Basic Info</h3>
                    <LabeledInput
                      label="Listing title"
                      value={listingForm.title}
                      onChange={(value) => setListingForm((prev) => ({ ...prev, title: value }))}
                      placeholder="Downtown Toronto SUV"
                      required
                    />
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      <LabeledInput
                        label="Make"
                        value={listingForm.make}
                        onChange={(value) => setListingForm((prev) => ({ ...prev, make: value }))}
                        placeholder="Toyota"
                        required
                      />
                      <LabeledInput
                        label="Model"
                        value={listingForm.model}
                        onChange={(value) => setListingForm((prev) => ({ ...prev, model: value }))}
                        placeholder="RAV4"
                        required
                      />
                    </div>
                    <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                      <LabeledInput
                        label="Year"
                        value={listingForm.year}
                        onChange={(value) => setListingForm((prev) => ({ ...prev, year: value }))}
                        type="number"
                      />
                      <LabeledPriceInput
                        label="Price per day"
                        value={listingForm.pricePerDay}
                        onChange={(value) => setListingForm((prev) => ({ ...prev, pricePerDay: value }))}
                      />
                      <LabeledInput
                        label="Mileage (km)"
                        value={listingForm.mileage}
                        onChange={(value) => setListingForm((prev) => ({ ...prev, mileage: value }))}
                        type="number"
                        placeholder="24500"
                        required={isAdmin}
                      />
                      {companyLocations.vehicleClasses.length > 0 && (
                        <LabeledSelect
                          label="Vehicle class"
                          value={listingForm.vehicleClassId ? String(listingForm.vehicleClassId) : ""}
                          onChange={(value) =>
                            setListingForm((prev) => ({ ...prev, vehicleClassId: value }))
                          }
                          required={isAdmin}
                          options={companyLocations.vehicleClasses.map((vehicleClass) => ({
                            value: String(vehicleClass.vehicleClassId),
                            label: vehicleClass.name || `Class #${vehicleClass.vehicleClassId}`,
                          }))}
                        />
                      )}
                    </div>
                  </section>

                  {!isAdmin && (
                    <section className="space-y-4">
                      <h3 className="text-sm font-semibold uppercase tracking-wider text-gray-500">
                        Booking settings
                      </h3>
                      <InstantBookToggle
                        checked={Boolean(listingForm.instantBook)}
                        onChange={(instantBook) =>
                          setListingForm((prev) => ({ ...prev, instantBook }))
                        }
                      />
                    </section>
                  )}

                  <section className="space-y-4">
                    <h3 className="text-sm font-semibold uppercase tracking-wider text-gray-500">Vehicle Specs</h3>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      <LabeledSelect
                        label="Transmission"
                        value={listingForm.transmission}
                        onChange={(value) => setListingForm((prev) => ({ ...prev, transmission: value }))}
                        options={[
                          { value: "Automatic", label: "Automatic" },
                          { value: "Manual", label: "Manual" },
                        ]}
                      />
                      <LabeledSelect
                        label="Fuel Type"
                        value={listingForm.fuelType}
                        onChange={(value) => setListingForm((prev) => ({ ...prev, fuelType: value }))}
                        options={[
                          { value: "Gas", label: "Gas" },
                          { value: "Electric", label: "Electric" },
                          { value: "Hybrid", label: "Hybrid" },
                          { value: "Diesel", label: "Diesel" },
                        ]}
                      />
                      <LabeledInput
                        label="Seats"
                        value={listingForm.seats}
                        onChange={(value) => setListingForm((prev) => ({ ...prev, seats: value }))}
                        type="number"
                      />
                      <LabeledInput
                        label="Doors"
                        value={listingForm.doors}
                        onChange={(value) => setListingForm((prev) => ({ ...prev, doors: value }))}
                        type="number"
                      />
                    </div>
                  </section>

                  <section className="space-y-4">
                    <h3 className="text-sm font-semibold uppercase tracking-wider text-gray-500">Rich Details</h3>
                    <LabeledTextarea
                      label="Description"
                      value={listingForm.description}
                      onChange={(value) => setListingForm((prev) => ({ ...prev, description: value }))}
                      placeholder="Describe this car like a premium listing."
                    />
                    <LabeledTextarea
                      label="Guidelines"
                      value={listingForm.guidelines}
                      onChange={(value) => setListingForm((prev) => ({ ...prev, guidelines: value }))}
                      placeholder="e.g., No smoking, pet fees..."
                    />
                  </section>

                  <section className="space-y-4">
                    <h3 className="text-sm font-semibold uppercase tracking-wider text-gray-500">Features & Amenities</h3>
                    <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
                      {FEATURE_OPTIONS.map((featureName) => {
                        const Icon = FEATURE_ICONS[featureName] || Check;
                        const active = listingForm.features.includes(featureName);
                        return (
                          <button
                            key={featureName}
                            type="button"
                            onClick={() => toggleFeature(featureName)}
                            className={`flex items-center gap-2 border p-3 rounded-xl text-left transition ${
                              active
                                ? "border-gray-900 bg-gray-50 text-gray-900"
                                : "border-gray-200 hover:border-gray-900"
                            }`}
                          >
                            <Icon className="h-4 w-4 text-gray-500" />
                            <span className="text-sm">{featureName}</span>
                          </button>
                        );
                      })}
                    </div>
                  </section>

                  {isAdmin && (
                    <button
                      type="button"
                      onClick={() =>
                        setListingForm((prev) => ({ ...prev, isCompanyOwned: !prev.isCompanyOwned }))
                      }
                      className="flex items-center gap-3 text-sm text-gray-700"
                    >
                    <span
                      className={`h-5 w-5 rounded border flex items-center justify-center transition ${
                        listingForm.isCompanyOwned
                          ? "bg-gray-900 border-gray-900 text-white"
                          : "border-gray-300 bg-white"
                      }`}
                    >
                      {listingForm.isCompanyOwned && <Check className="h-3 w-3" />}
                    </span>
                    Company owned listing
                    </button>
                  )}

                  <section className="space-y-4">
                    <h3 className="text-sm font-semibold uppercase tracking-wider text-gray-500">
                      Pickup Location
                    </h3>
                    {isAdmin && (
                    <div className="grid grid-cols-2 gap-4 mb-2">
                      <button
                        type="button"
                        onClick={() => {
                          setLocationMode("hub");
                          const nextBranchId =
                            listingForm.branchId ||
                            (companyLocations.branches[0]
                              ? String(companyLocations.branches[0].branchId)
                              : "");
                          if (nextBranchId) {
                            applyHubBranchSelection(nextBranchId);
                          }
                        }}
                        className={`p-4 border-2 rounded-xl cursor-pointer flex items-center gap-3 transition-all ${
                          locationMode === "hub"
                            ? "border-gray-900 bg-gray-50"
                            : "border-gray-200 hover:border-gray-300"
                        }`}
                      >
                        <Building2 className="h-5 w-5 text-gray-700" />
                        <span className="font-medium text-gray-900">Company Hub</span>
                      </button>
                      <button
                        type="button"
                        onClick={() => setLocationMode("custom")}
                        className={`p-4 border-2 rounded-xl cursor-pointer flex items-center gap-3 transition-all ${
                          locationMode === "custom"
                            ? "border-gray-900 bg-gray-50"
                            : "border-gray-200 hover:border-gray-300"
                        }`}
                      >
                        <MapPin className="h-5 w-5 text-gray-700" />
                        <span className="font-medium text-gray-900">Custom Location</span>
                      </button>
                    </div>
                    )}

                    <div className="transition-all duration-200 ease-out space-y-4">
                      {isAdmin && locationMode === "hub" ? (
                        <LabeledSelect
                          label="Company branch"
                          value={listingForm.branchId}
                          onChange={applyHubBranchSelection}
                          required
                          options={companyLocations.branches.map((branch) => ({
                            value: String(branch.branchId),
                            label: `${branch.name} - ${branch.address}`,
                          }))}
                        />
                      ) : (
                        <div className="flex flex-col gap-3">
                          <div className="space-y-2">
                            <label className="block text-sm font-medium text-gray-700">
                              Pickup address
                            </label>
                            <input
                              value={addressQuery}
                              onChange={(event) => {
                                const value = event.target.value;
                                setAddressQuery(value);
                                setListingForm((prev) => ({ ...prev, address: value }));
                              }}
                              placeholder="Type pickup address and choose suggestion"
                              className="w-full border border-gray-300 rounded-lg px-4 py-3 text-gray-900 focus:ring-2 focus:ring-gray-900 focus:border-transparent outline-none transition"
                            />
                            {isPlacesLoading && (
                              <p className="text-xs text-gray-500">
                                Loading address suggestions...
                              </p>
                            )}
                            {placePredictions.length > 0 && (
                              <div className="rounded-xl border border-gray-200 bg-white p-2 max-h-44 overflow-y-auto">
                                {placePredictions.map((prediction) => (
                                  <button
                                    key={prediction.placeId || prediction.place_id}
                                    type="button"
                                    onClick={() => selectAddressPrediction(prediction)}
                                    className="w-full text-left rounded-lg px-3 py-2 hover:bg-gray-50"
                                  >
                                    <p className="text-sm font-medium text-gray-900">
                                      {prediction.structured_formatting?.main_text ||
                                        prediction.description}
                                    </p>
                                    <p className="text-xs text-gray-500">
                                      {prediction.structured_formatting?.secondary_text || ""}
                                    </p>
                                  </button>
                                ))}
                              </div>
                            )}
                            {placesError && <p className="text-xs text-red-600">{placesError}</p>}
                          </div>
                          <button
                            type="button"
                            onClick={openMapPicker}
                            className="w-full py-3 border border-gray-300 rounded-lg flex justify-center items-center gap-2 font-medium hover:bg-gray-50 transition text-gray-900"
                          >
                            <Crosshair className="h-4 w-4" />
                            Drop Pin on Map
                          </button>
                        </div>
                      )}
                    </div>

                    {hasConfirmedLocation && (
                      <p className="text-xs font-medium text-emerald-700 flex items-center gap-2">
                        <Check className="h-3.5 w-3.5" />
                        Location Confirmed
                      </p>
                    )}

                    <AddressPickerMapCard
                      apiKey={apiKey}
                      isMapLoaded={isMapLoaded}
                      latitude={listingForm.latitude}
                      longitude={listingForm.longitude}
                    />
                  </section>

                  <section className="space-y-4">
                    <div className="flex flex-wrap items-end justify-between gap-2">
                      <div>
                        <h3 className="text-sm font-semibold uppercase tracking-wider text-gray-500">
                          Photos
                        </h3>
                        <p className="mt-1 text-sm text-gray-600">
                          {editingListingId
                            ? "Add more images below. New photos upload when you save."
                            : `At least ${MIN_LISTING_PHOTOS} photos required for a new listing.`}
                        </p>
                      </div>
                      {!editingListingId && (
                        <p
                          className={`text-sm font-semibold ${
                            meetsPhotoRequirement ? "text-emerald-700" : "text-amber-700"
                          }`}
                        >
                          {pendingPhotoCount} / {MIN_LISTING_PHOTOS} selected
                        </p>
                      )}
                    </div>

                    {(existingListingPhotoUrls.length > 0 || pendingPhotoPreviewUrls.length > 0) && (
                      <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 md:grid-cols-4">
                        {existingListingPhotoUrls.map((url, index) => (
                          <div
                            key={`existing-${url}-${index}`}
                            className="relative aspect-[4/3] overflow-hidden rounded-xl border border-gray-200 bg-gray-100"
                          >
                            <img
                              src={url}
                              alt={`Listing photo ${index + 1}`}
                              className="h-full w-full object-cover"
                            />
                            <span className="absolute left-2 top-2 rounded-md bg-black/60 px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wide text-white">
                              Saved
                            </span>
                          </div>
                        ))}
                        {pendingPhotoPreviewUrls.map((url, index) => (
                          <div
                            key={`pending-${pendingPhotoFiles[index]?.name}-${index}`}
                            className="relative aspect-[4/3] overflow-hidden rounded-xl border border-gray-200 bg-gray-100"
                          >
                            <img
                              src={url}
                              alt={pendingPhotoFiles[index]?.name || `New photo ${index + 1}`}
                              className="h-full w-full object-cover"
                            />
                            <button
                              type="button"
                              onClick={() => removePendingPhoto(index)}
                              className="absolute right-2 top-2 flex h-7 w-7 items-center justify-center rounded-full bg-black/60 text-white transition hover:bg-black/80"
                              aria-label={`Remove ${pendingPhotoFiles[index]?.name || "photo"}`}
                            >
                              <X className="h-4 w-4" />
                            </button>
                          </div>
                        ))}
                      </div>
                    )}

                    <div
                      onDrop={onDropFile}
                      onDragOver={(event) => {
                        event.preventDefault();
                        setIsDragOver(true);
                      }}
                      onDragLeave={() => setIsDragOver(false)}
                      onClick={() => fileInputRef.current?.click()}
                      className={`border-2 border-dashed rounded-xl p-8 flex flex-col items-center justify-center text-center cursor-pointer transition ${
                        isDragOver
                          ? "border-gray-900 bg-gray-50"
                          : "border-gray-300 hover:border-gray-900 hover:bg-gray-50"
                      }`}
                    >
                      <UploadCloud className="h-10 w-10 text-gray-400 mb-2" />
                      <p className="text-base font-semibold text-gray-800">Add photos</p>
                      <p className="text-sm text-gray-500">
                        Drag images here or click to choose (images only)
                      </p>
                      {pendingPhotoCount > 0 && (
                        <button
                          type="button"
                          onClick={(event) => {
                            event.stopPropagation();
                            setPendingPhotoFiles([]);
                          }}
                          className="mt-3 text-xs font-semibold text-gray-600 hover:text-gray-900"
                        >
                          Clear new selection
                        </button>
                      )}
                      <input
                        ref={fileInputRef}
                        type="file"
                        accept="image/*"
                        multiple
                        className="hidden"
                        onChange={(event) => {
                          selectUploadFiles(event.target.files);
                          event.target.value = "";
                        }}
                      />
                    </div>

                    {pendingPhotoCount > 0 && (
                      <p className="text-sm text-gray-600">
                        New photos upload to S3 when you click{" "}
                        <span className="font-semibold">Save listing</span>.
                      </p>
                    )}
                  </section>

                  <div className="border-t border-gray-200 pt-6 mt-6 flex justify-end gap-4">
                    <button
                      type="button"
                      onClick={() => {
                        setListingForm((prev) => ({
                          ...emptyListingForm,
                          isCompanyOwned: isAdmin,
                          areaId: prev.areaId,
                          branchId: prev.branchId,
                        }));
                        setPendingPhotoFiles([]);
                        setAddressQuery("");
                        setLocationMode(isAdmin ? "hub" : "custom");
                        setEditingListingId(null);
                        setActiveTab("overview");
                      }}
                      className="rounded-lg border border-gray-300 px-4 py-2 text-gray-700 hover:bg-gray-50 transition"
                    >
                      Cancel
                    </button>
                    <button
                      type="submit"
                      disabled={isSavingListing || (!editingListingId && !meetsPhotoRequirement)}
                      className="rounded-lg bg-indigo-600 px-5 py-2 font-semibold text-white transition hover:bg-indigo-700 disabled:cursor-not-allowed disabled:opacity-40"
                    >
                      {isSavingListing ? "Saving..." : editingListingId ? "Update listing" : "Save listing"}
                    </button>
                  </div>
                </form>
              </div>
            </section>
          )}

          {(activeTab === "listings" || activeTab === "fleet_listings" || activeTab === "host_listings") && (
            <ListingsTableSection
              title={
                activeTab === "host_listings"
                  ? "Host Listings"
                  : isAdmin
                    ? "Fleet Listings"
                    : "My Listings"
              }
              listings={activeTab === "host_listings" ? hostListings : listings}
              showHostColumn={activeTab === "host_listings"}
              showTypeColumn={isAdmin && activeTab !== "host_listings"}
              showAddButton={activeTab !== "host_listings"}
              onAdd={() => setActiveTab("create_listing")}
              onEdit={startEditListing}
              onDelete={deleteListing}
            />
          )}

          {isAdmin && activeTab === "kyc" && (
            <section className="mx-11 mt-6 mb-11 rounded-2xl border-4 border-black bg-[#f5f5d0] p-6 shadow-[8px_8px_0px_0px_rgba(24,59,30,0.45)]">
              <h3 className="mb-4 text-lg font-semibold text-gray-900">Host identity review</h3>
              {kycQueue.length === 0 ? (
                <p className="text-sm text-gray-600">No pending verifications.</p>
              ) : (
                <div className="space-y-3">
                  {kycQueue.map((item) => (
                    <div
                      key={item.userId}
                      className="flex flex-wrap items-center justify-between gap-3 rounded-xl border border-gray-100 p-4"
                    >
                      <div>
                        <p className="font-medium text-gray-900">{item.fullName || item.email}</p>
                        <p className="text-sm text-gray-500">{item.email}</p>
                      </div>
                      <div className="flex gap-2">
                        <button
                          type="button"
                          onClick={async () => {
                            await apiPatch(`/api/users/${item.userId}/kyc`, { verificationStatus: "VERIFIED" }, true);
                            await loadAll();
                          }}
                          className="rounded-lg bg-emerald-600 px-3 py-1.5 text-sm font-medium text-white hover:bg-emerald-700"
                        >
                          Approve
                        </button>
                        <button
                          type="button"
                          onClick={async () => {
                            await apiPatch(`/api/users/${item.userId}/kyc`, { verificationStatus: "REJECTED" }, true);
                            await loadAll();
                          }}
                          className="rounded-lg border border-gray-300 px-3 py-1.5 text-sm font-medium text-gray-700 hover:bg-gray-50"
                        >
                          Reject
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </section>
          )}

          {isAdmin && activeTab === "users" && (
            <section className="mx-11 mt-6 mb-11 overflow-hidden rounded-2xl border-4 border-black bg-[#f5f5d0] shadow-[8px_8px_0px_0px_rgba(24,59,30,0.45)]">
              <table className="w-full text-left border-collapse">
                <thead>
                  <tr className="bg-gray-50 border-b border-gray-200 text-xs uppercase text-gray-500 font-semibold tracking-wider">
                    <th className="px-6 py-4">Email</th>
                    <th className="px-6 py-4">Role</th>
                    <th className="px-6 py-4">Created</th>
                  </tr>
                </thead>
                <tbody>
                  {users.map((user) => (
                    <tr key={user.userId} className="border-b border-gray-100 hover:bg-gray-50 transition">
                      <td className="px-6 py-4 text-sm text-gray-900">{user.email}</td>
                      <td className="px-6 py-4 text-sm text-gray-900">
                        <span
                          className={`px-2.5 py-0.5 rounded-full text-xs font-medium ${
                            user.isAdmin ? "bg-purple-100 text-purple-800" : "bg-gray-100 text-gray-700"
                          }`}
                        >
                          {user.role}
                        </span>
                      </td>
                      <td className="px-6 py-4 text-sm text-gray-900">{user.createdAt || "n/a"}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </section>
          )}

          {activeTab === "bookings" && (
            <div className="mx-11 mt-6 mb-11 space-y-6">
              {!isAdmin && pendingApprovalBookings.length > 0 && (
                <section className="rounded-2xl border border-amber-200 bg-amber-50 p-6 shadow-sm">
                  <div className="mb-4 flex flex-wrap items-center justify-between gap-2">
                    <div>
                      <h3 className="text-lg font-semibold text-amber-950">
                        Awaiting your approval
                      </h3>
                      <p className="mt-1 text-sm text-amber-900/80">
                        {pendingApprovalBookings.length} booking
                        {pendingApprovalBookings.length === 1 ? "" : "s"} need a decision.
                      </p>
                    </div>
                    <span className="rounded-full bg-amber-200 px-3 py-1 text-xs font-semibold text-amber-950">
                      {pendingApprovalBookings.length} pending
                    </span>
                  </div>
                  <div className="space-y-3">
                    {pendingApprovalBookings.map((booking) => (
                      <div
                        key={booking.bookingId}
                        className="flex flex-wrap items-center justify-between gap-4 rounded-xl border border-amber-200 bg-white p-4"
                      >
                        <div>
                          <p className="font-semibold text-gray-900">
                            #{booking.bookingId} · {booking.listingTitle || "Listing"}
                          </p>
                          <p className="mt-1 text-sm text-gray-600">
                            {booking.renterEmail || `Renter #${booking.renterUserId || "n/a"}`} ·{" "}
                            {formatBookingWindow(booking.startAt, booking.endAt)}
                          </p>
                        </div>
                        <div className="flex flex-wrap gap-2">
                          <button
                            type="button"
                            disabled={bookingActionId === booking.bookingId}
                            onClick={() => handleBookingDecision(booking.bookingId, "reject")}
                            className="rounded-lg border border-gray-300 px-4 py-2 text-sm font-semibold text-gray-700 hover:bg-gray-50 disabled:opacity-50"
                          >
                            Reject
                          </button>
                          <button
                            type="button"
                            disabled={bookingActionId === booking.bookingId}
                            onClick={() => handleBookingDecision(booking.bookingId, "approve")}
                            className="rounded-lg bg-gray-900 px-4 py-2 text-sm font-semibold text-white hover:bg-black disabled:opacity-50"
                          >
                            {bookingActionId === booking.bookingId ? "Saving..." : "Approve"}
                          </button>
                        </div>
                      </div>
                    ))}
                  </div>
                </section>
              )}

              <section className="overflow-hidden rounded-2xl border-4 border-black bg-[#f5f5d0] shadow-[8px_8px_0px_0px_rgba(24,59,30,0.45)]">
                <table className="w-full border-collapse text-left">
                  <thead>
                    <tr className="border-b border-gray-200 bg-gray-50 text-xs font-semibold uppercase tracking-wider text-gray-500">
                      <th className="px-6 py-4">Booking</th>
                      <th className="px-6 py-4">Listing</th>
                      <th className="px-6 py-4">Window</th>
                      <th className="px-6 py-4">Status</th>
                      {!isAdmin && <th className="px-6 py-4">Actions</th>}
                    </tr>
                  </thead>
                  <tbody>
                    {bookings.length === 0 ? (
                      <tr>
                        <td
                          colSpan={isAdmin ? 4 : 5}
                          className="px-6 py-10 text-center text-sm text-gray-500"
                        >
                          No bookings yet.
                        </td>
                      </tr>
                    ) : (
                      bookings.map((booking) => {
                        const pending = isPendingApproval(booking.status);
                        return (
                          <tr
                            key={booking.bookingId}
                            className={`border-b border-gray-100 transition hover:bg-gray-50 ${
                              pending ? "bg-amber-50/40" : ""
                            }`}
                          >
                            <td className="px-6 py-4 text-sm font-medium text-gray-900">
                              <Link
                                to={`/app/bookings/${booking.bookingId}`}
                                className="font-semibold text-indigo-600 hover:text-indigo-800 hover:underline"
                              >
                                #{booking.bookingId}
                              </Link>
                            </td>
                            <td className="px-6 py-4 text-sm text-gray-900">
                              {booking.listingTitle}
                            </td>
                            <td className="px-6 py-4 text-sm text-gray-900">
                              {formatBookingWindow(booking.startAt, booking.endAt)}
                            </td>
                            <td className="px-6 py-4 text-sm text-gray-900">
                              <span
                                className={`rounded-full px-2.5 py-0.5 text-xs font-medium ${bookingStatusBadgeClass(booking.status)}`}
                              >
                                {formatBookingStatusLabel(booking.status)}
                              </span>
                            </td>
                            {!isAdmin && (
                              <td className="px-6 py-4 text-sm text-gray-900">
                                {pending ? (
                                  <div className="flex flex-wrap gap-2">
                                    <button
                                      type="button"
                                      disabled={bookingActionId === booking.bookingId}
                                      onClick={() =>
                                        handleBookingDecision(booking.bookingId, "reject")
                                      }
                                      className="rounded-lg border border-gray-300 px-3 py-1.5 text-xs font-semibold text-gray-700 hover:bg-gray-50 disabled:opacity-50"
                                    >
                                      Reject
                                    </button>
                                    <button
                                      type="button"
                                      disabled={bookingActionId === booking.bookingId}
                                      onClick={() =>
                                        handleBookingDecision(booking.bookingId, "approve")
                                      }
                                      className="rounded-lg bg-gray-900 px-3 py-1.5 text-xs font-semibold text-white hover:bg-black disabled:opacity-50"
                                    >
                                      Approve
                                    </button>
                                  </div>
                                ) : (
                                  <span className="text-xs text-gray-400">—</span>
                                )}
                              </td>
                            )}
                          </tr>
                        );
                      })
                    )}
                  </tbody>
                </table>
              </section>
            </div>
          )}

          {isMapModalOpen && (
            <div className="fixed inset-0 z-[60] bg-black/60 flex items-center justify-center p-4">
              <div className="relative flex h-[80vh] w-full max-w-4xl flex-col overflow-hidden rounded-2xl border-4 border-black bg-[#f5f5d0] shadow-[8px_8px_0px_0px_rgba(24,59,30,0.45)]">
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
                <div className="flex-grow w-full relative min-h-[320px]">
                  {tempLocation.address && (
                    <div className="absolute inset-x-4 bottom-4 z-10 rounded-lg border border-gray-200 bg-white/95 px-3 py-2 text-sm text-gray-700 shadow-sm">
                      {tempLocation.address}
                    </div>
                  )}
                  <MapPinPicker
                    apiKey={apiKey}
                    isLoaded={isMapLoaded}
                    latitude={tempLocation.lat}
                    longitude={tempLocation.lng}
                    onPinMove={handlePinDrop}
                  />
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
                    disabled={
                      !Number.isFinite(tempLocation.lat) || !Number.isFinite(tempLocation.lng)
                    }
                    onClick={confirmMapPickerLocation}
                    className="rounded-lg bg-indigo-600 px-4 py-2 text-white font-semibold hover:bg-indigo-700 transition disabled:cursor-not-allowed disabled:opacity-40"
                  >
                    Confirm Location
                  </button>
                </div>
              </div>
            </div>
          )}

          {isLoading && (
            <div className="mx-11 rounded-md bg-gray-100 p-3 text-sm text-gray-600">
              Loading dashboard data...
            </div>
          )}
          </main>
        </div>
      </div>
    </Layout>
  );
}

function ListingsTableSection({
  title,
  listings,
  showHostColumn,
  showTypeColumn,
  showAddButton = true,
  onAdd,
  onEdit,
  onDelete,
}) {
  return (
    <section className="mx-11 mt-6 mb-11">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-2xl font-semibold text-gray-900">{title}</h2>
        {showAddButton && (
          <button
            type="button"
            onClick={onAdd}
            className="rounded-lg bg-indigo-600 px-4 py-2 text-sm font-semibold text-white hover:bg-indigo-700 transition"
          >
            Add New Listing
          </button>
        )}
      </div>
      <div className="overflow-hidden rounded-2xl border-4 border-black bg-[#f5f5d0] shadow-[8px_8px_0px_0px_rgba(24,59,30,0.45)]">
        <table className="w-full text-left border-collapse">
          <thead>
            <tr className="bg-gray-50 border-b border-gray-200 text-xs uppercase text-gray-500 font-semibold tracking-wider">
              <th className="px-6 py-4">Listing</th>
              <th className="px-6 py-4">Specs</th>
              {showHostColumn && <th className="px-6 py-4">Host</th>}
              {showTypeColumn && <th className="px-6 py-4">Type</th>}
              <th className="px-6 py-4">Price</th>
              <th className="px-6 py-4">Reviews</th>
              <th className="px-6 py-4">Actions</th>
            </tr>
          </thead>
          <tbody>
            {listings.length === 0 ? (
              <tr>
                <td
                  colSpan={5 + (showHostColumn ? 1 : 0) + (showTypeColumn ? 1 : 0)}
                  className="px-6 py-8 text-sm text-gray-500 text-center"
                >
                  No listings found.
                </td>
              </tr>
            ) : (
              listings.map((listing) => (
                <tr
                  key={listing.listingId}
                  className="border-b border-gray-100 hover:bg-gray-50 transition"
                >
                  <td className="px-6 py-4 text-sm text-gray-900 font-medium">
                    <Link
                      to={`/app/listings/${listing.listingId}`}
                      className="text-indigo-700 hover:text-indigo-900 hover:underline"
                    >
                      {listing.title}
                    </Link>
                  </td>
                  <td className="px-6 py-4 text-sm text-gray-700">
                    {listing.make || "-"} {listing.model || ""}
                  </td>
                  {showHostColumn && (
                    <td className="px-6 py-4 text-sm text-gray-700">
                      {listing.ownerName || `User #${listing.ownerUserId ?? "n/a"}`}
                    </td>
                  )}
                  {showTypeColumn && (
                    <td className="px-6 py-4 text-sm text-gray-900">
                      <span
                        className={`px-2.5 py-0.5 rounded-full text-xs font-medium ${
                          listing.isCompanyOwned
                            ? "bg-purple-100 text-purple-800"
                            : "bg-gray-100 text-gray-700"
                        }`}
                      >
                        {listing.isCompanyOwned ? "Company" : "User"}
                      </span>
                    </td>
                  )}
                  <td className="px-6 py-4 text-sm text-gray-900">${listing.pricePerDay}</td>
                  <td className="px-6 py-4 text-sm text-gray-700">
                    {listing.reviewCount ?? 0} review{(listing.reviewCount ?? 0) === 1 ? "" : "s"}
                    {listing.averageRating != null
                      ? ` · ${Number(listing.averageRating).toFixed(1)}★`
                      : ""}
                  </td>
                  <td className="px-6 py-4 text-sm text-gray-900">
                    <div className="flex items-center gap-2">
                      <button
                        type="button"
                        onClick={() => onEdit(listing)}
                        className="h-9 w-9 rounded-lg text-gray-400 hover:text-indigo-700 hover:bg-indigo-50 transition flex items-center justify-center"
                        aria-label="Edit listing"
                      >
                        <Pencil className="h-4 w-4" />
                      </button>
                      <Link
                        to={`/app/listings/${listing.listingId}`}
                        className="rounded-lg border border-gray-300 px-3 py-1.5 text-xs font-semibold text-gray-700 hover:bg-gray-50 transition"
                      >
                        View
                      </Link>
                      <button
                        type="button"
                        onClick={() => onDelete(listing.listingId)}
                        className="h-9 w-9 rounded-lg text-gray-400 hover:text-red-600 hover:bg-red-50 transition flex items-center justify-center"
                        aria-label="Delete listing"
                      >
                        <Trash2 className="h-4 w-4" />
                      </button>
                    </div>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </section>
  );
}

function buildRevenueSeries(bookings) {
  if (!bookings.length) {
    return [{ day: "—", revenue: 0 }];
  }
  const totals = {};
  for (const booking of bookings) {
    const day = formatShortDay(booking.createdAt || booking.startAt);
    const amount = Number(booking.priceSnapshot?.pricePerDay ?? 0);
    totals[day] = (totals[day] || 0) + amount;
  }
  return Object.entries(totals).map(([day, revenue]) => ({ day, revenue }));
}

function buildBookingsByLocation(bookings) {
  if (!bookings.length) {
    return [{ location: "No bookings", bookings: 0 }];
  }
  const counts = {};
  for (const booking of bookings) {
    const location = booking.cityZone || booking.listingTitle || "Unknown";
    counts[location] = (counts[location] || 0) + 1;
  }
  return Object.entries(counts).map(([location, bookingsCount]) => ({
    location,
    bookings: bookingsCount,
  }));
}

function formatShortDay(isoValue) {
  if (!isoValue) return "—";
  const date = new Date(isoValue);
  if (Number.isNaN(date.getTime())) return "—";
  return date.toLocaleDateString(undefined, { month: "short", day: "numeric" });
}

function formatBookingWindow(startAt, endAt) {
  if (!startAt || !endAt) return "n/a";
  const start = String(startAt).slice(0, 10);
  const end = String(endAt).slice(0, 10);
  return `${start} to ${end}`;
}

function AnalyticsCard({ label, value }) {
  return (
    <div className="bg-[#f5f5d0] border-4 border-black rounded-[1.5rem] p-6 shadow-[8px_8px_0px_0px_rgba(24,59,30,0.45)] flex flex-col gap-2">
      <p className="text-sm font-bold text-[#35593b] uppercase tracking-wider">{label}</p>
      <div className="flex items-center gap-2">
        <BarChart3 className="h-5 w-5 text-[#E34B31]" />
        <p className="text-4xl font-extrabold text-[#183B1E]">{value}</p>
      </div>
    </div>
  );
}

function LabeledInput({ label, value, onChange, type = "text", placeholder, required = false }) {
  return (
    <label className="block">
      <span className="mb-2 block text-sm font-bold text-[#35593b]">{label}</span>
      <input
        type={type}
        value={value}
        onChange={(event) => onChange(event.target.value)}
        placeholder={placeholder}
        required={required}
        className="w-full border-2 border-black rounded-2xl bg-white px-4 py-3 text-[#183B1E] outline-none transition"
      />
    </label>
  );
}

function LabeledTextarea({ label, value, onChange, placeholder }) {
  return (
    <label className="block">
      <span className="mb-2 block text-sm font-bold text-[#35593b]">{label}</span>
      <textarea
        value={value}
        onChange={(event) => onChange(event.target.value)}
        placeholder={placeholder}
        className="w-full min-h-28 border-2 border-black rounded-2xl bg-white px-4 py-3 text-[#183B1E] outline-none transition resize-y"
      />
    </label>
  );
}

function LabeledSelect({ label, value, onChange, options, required = false }) {
  return (
    <label className="block">
      <span className="mb-2 block text-sm font-bold text-[#35593b]">{label}</span>
      <select
        value={value}
        onChange={(event) => onChange(event.target.value)}
        required={required}
        className="w-full border-2 border-black rounded-2xl bg-white px-4 py-3 text-[#183B1E] outline-none transition"
      >
        <option value="">Select option</option>
        {options.map((option) => (
          <option key={option.value} value={option.value}>
            {option.label}
          </option>
        ))}
      </select>
    </label>
  );
}

function LabeledPriceInput({ label, value, onChange }) {
  return (
    <label className="block">
      <span className="mb-2 block text-sm font-bold text-[#35593b]">{label}</span>
      <div className="relative">
        <DollarSign className="absolute left-4 top-1/2 h-4 w-4 -translate-y-1/2 text-[#E34B31]" />
        <input
          type="number"
          value={value}
          onChange={(event) => onChange(event.target.value)}
          required
          className="w-full border-2 border-black rounded-2xl bg-white py-3 pl-10 pr-4 text-[#183B1E] outline-none transition"
        />
      </div>
    </label>
  );
}

function AddressPickerMapCard({ apiKey, isMapLoaded, latitude, longitude }) {
  const lat = Number(latitude);
  const lng = Number(longitude);
  const hasCoordinates = Number.isFinite(lat) && Number.isFinite(lng);
  const center = hasCoordinates ? { lat, lng } : CANADA_CENTER;
  const zoom = hasCoordinates ? 14 : 4;

  return (
    <div className="rounded-xl border border-gray-200 bg-white overflow-hidden">
      <div className="border-b border-gray-200 px-4 py-3 flex items-center gap-2">
        <MapPin className="h-4 w-4 text-gray-500" />
        <p className="text-sm font-medium text-gray-700">Location map preview</p>
      </div>
      <div className="p-4">
        {!apiKey ? (
          <div className="rounded-lg border border-gray-200 bg-gray-50 p-4 text-sm text-gray-600">
            Add `VITE_GOOGLE_MAPS_API_KEY` in `frontend/.env.local` to show map preview.
          </div>
        ) : !isMapLoaded ? (
          <div className="rounded-lg border border-gray-200 bg-gray-50 p-4 text-sm text-gray-600">
            Loading map...
          </div>
        ) : (
          <GoogleMap
            mapContainerStyle={mapContainerStyle}
            center={center}
            zoom={zoom}
            options={CANADA_MAP_OPTIONS}
          >
            {hasCoordinates && <Marker position={{ lat, lng }} />}
          </GoogleMap>
        )}
      </div>
    </div>
  );
}
