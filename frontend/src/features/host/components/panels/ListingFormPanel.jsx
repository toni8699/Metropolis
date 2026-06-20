import {
  Bluetooth,
  Building2,
  Check,
  Crosshair,
  KeyRound,
  Loader2,
  MapPin,
  ShieldCheck,
  Smartphone,
  Snowflake,
  Sun,
  UploadCloud,
  X,
} from "lucide-react";
import { useEffect, useState } from "react";
import { MIN_LISTING_PHOTOS } from "@/features/host/constants";
import InstantBookToggle from "@/features/host/components/InstantBookToggle";
import AddressPickerMapCard from "@/features/host/components/AddressPickerMapCard";
import ListingCreatedModal from "@/features/host/components/ListingCreatedModal";
import {
  LabeledInput,
  LabeledPriceInput,
  LabeledSelect,
  LabeledTextarea,
} from "@/features/host/components/form/Fields";

const FEATURE_ICONS = {
  Smartphone,
  Bluetooth,
  Sun,
  Snowflake,
  ShieldCheck,
  UploadCloud,
  KeyRound,
  Check,
};

function featureIcon(iconKey) {
  return FEATURE_ICONS[iconKey] || Check;
}

function assetLabel(form) {
  return [form.make, form.model, form.year].filter(Boolean).join(" ").trim();
}

export default function ListingFormPanel({
  form,
  isAdmin,
  companyLocations,
  apiKey,
  isMapLoaded,
  listingsTabId = "listings",
}) {
  const {
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
    dismissCreateSuccess,
    addressQuery,
    setAddressQuery,
    placePredictions,
    isPlacesLoading,
    placesError,
    locationMode,
    setLocationMode,
    existingListingPhotoUrls,
    pendingPhotoCount,
    meetsPhotoRequirement,
    hasConfirmedLocation,
    fileInputRef,
    createListing,
    cancelForm,
    toggleFeature,
    selectUploadFiles,
    removePendingPhoto,
    clearPendingPhotos,
    onDropFile,
    selectAddressPrediction,
    openMapPicker,
    applyHubBranchSelection,
    decodeVin,
    metalFactsLocked,
    setMetalFactsLocked,
    isDecodingVin,
    bodyTypes,
    catalogFeatures,
  } = form;

  const metalReadOnly = metalFactsLocked && !isAdmin;
  const featuresByCategory = catalogFeatures.reduce((acc, feature) => {
    const key = feature.category || "Other";
    acc[key] = acc[key] || [];
    acc[key].push(feature);
    return acc;
  }, {});

  const [saveButtonPhase, setSaveButtonPhase] = useState("idle");
  const [showSaveFlash, setShowSaveFlash] = useState(false);

  useEffect(() => {
    if (isSavingListing) {
      setSaveButtonPhase("saving");
    }
  }, [isSavingListing]);

  useEffect(() => {
    if (updateSaveSignal === 0 || isSavingListing) return undefined;
    setSaveButtonPhase("saved");
    setShowSaveFlash(true);
    const buttonTimer = window.setTimeout(() => setSaveButtonPhase("idle"), 3000);
    const flashTimer = window.setTimeout(() => setShowSaveFlash(false), 1500);
    return () => {
      window.clearTimeout(buttonTimer);
      window.clearTimeout(flashTimer);
    };
  }, [updateSaveSignal, isSavingListing]);

  const saveButtonLabel = () => {
    if (saveButtonPhase === "saving") return "Saving...";
    if (saveButtonPhase === "saved") return "Changes Saved!";
    return editingListingId ? "Save Changes" : "Save listing";
  };

  return (
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
      <div
        className={`max-w-4xl mx-auto mt-6 rounded-2xl border-4 bg-vroom-card p-8 shadow-neo transition-colors duration-500 ${
          showSaveFlash ? "border-[#D0F0C0]" : "border-black"
        }`}
      >
        <form className="space-y-6" onSubmit={createListing}>
          <section className="space-y-4">
            <h3 className="text-sm font-semibold uppercase tracking-wider text-gray-500">Vehicle VIN</h3>
            <div className="flex flex-col gap-3 sm:flex-row">
              <LabeledInput
                label="VIN"
                value={listingForm.vin}
                onChange={(value) =>
                  setListingForm((prev) => ({ ...prev, vin: value.toUpperCase() }))
                }
                placeholder="17-character VIN"
              />
              <div className="flex items-end gap-2">
                <button
                  type="button"
                  onClick={decodeVin}
                  disabled={isDecodingVin}
                  className="rounded-lg border-2 border-black bg-vroom-accent px-4 py-2.5 text-sm font-bold text-white disabled:opacity-50"
                >
                  {isDecodingVin ? "Decoding..." : "Decode VIN"}
                </button>
                {metalFactsLocked && (
                  <button
                    type="button"
                    onClick={() => setMetalFactsLocked(false)}
                    className="rounded-lg border border-gray-300 px-3 py-2.5 text-sm text-gray-700"
                  >
                    Edit specs
                  </button>
                )}
              </div>
            </div>
          </section>

          <section className="space-y-4">
            <h3 className="text-sm font-semibold uppercase tracking-wider text-gray-500">Basic Info</h3>
            <LabeledInput
              label="Listing title (marketing)"
              value={listingForm.listingTitle}
              onChange={(value) =>
                setListingForm((prev) => ({ ...prev, listingTitle: value, title: value }))
              }
              placeholder="Perfect AWD for your weekend ski trip"
              required
            />
            {assetLabel(listingForm) && (
              <p className="text-sm text-gray-600">Vehicle: {assetLabel(listingForm)}</p>
            )}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <LabeledInput
                label="Make"
                value={listingForm.make}
                onChange={(value) => setListingForm((prev) => ({ ...prev, make: value }))}
                placeholder="Toyota"
                required
                disabled={metalReadOnly}
              />
              <LabeledInput
                label="Model"
                value={listingForm.model}
                onChange={(value) => setListingForm((prev) => ({ ...prev, model: value }))}
                placeholder="RAV4"
                required
                disabled={metalReadOnly}
              />
            </div>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <LabeledInput
                label="Year"
                value={listingForm.year}
                onChange={(value) => setListingForm((prev) => ({ ...prev, year: value }))}
                type="number"
                disabled={metalReadOnly}
              />
              <LabeledPriceInput
                label="Price per day"
                value={listingForm.pricePerDay}
                onChange={(value) => setListingForm((prev) => ({ ...prev, pricePerDay: value }))}
              />
              {bodyTypes.length > 0 && (
                <LabeledSelect
                  label="Body type"
                  value={listingForm.bodyTypeId ? String(listingForm.bodyTypeId) : ""}
                  onChange={(value) =>
                    setListingForm((prev) => ({ ...prev, bodyTypeId: value }))
                  }
                  disabled={metalReadOnly}
                  options={bodyTypes.map((bodyType) => ({
                    value: String(bodyType.bodyTypeId),
                    label: bodyType.displayName,
                  }))}
                />
              )}
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
                disabled={metalReadOnly}
                options={[
                  { value: "Automatic", label: "Automatic" },
                  { value: "Manual", label: "Manual" },
                ]}
              />
              <LabeledSelect
                label="Fuel Type"
                value={listingForm.fuelType}
                onChange={(value) => setListingForm((prev) => ({ ...prev, fuelType: value }))}
                disabled={metalReadOnly}
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
                disabled={metalReadOnly}
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
            {Object.entries(featuresByCategory).map(([category, features]) => (
              <div key={category} className="space-y-3">
                <p className="text-xs font-semibold uppercase tracking-wide text-gray-500">{category}</p>
                <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
                  {features.map((feature) => {
                    const Icon = featureIcon(feature.iconKey);
                    const active = listingForm.featureIds.includes(feature.featureId);
                    return (
                      <button
                        key={feature.featureId}
                        type="button"
                        onClick={() => toggleFeature(feature.featureId)}
                        className={`flex items-center gap-2 border p-3 rounded-xl text-left transition ${
                          active
                            ? "border-gray-900 bg-gray-50 text-gray-900"
                            : "border-gray-200 hover:border-gray-900"
                        }`}
                      >
                        <Icon className="h-4 w-4 text-gray-500" />
                        <span className="text-sm">{feature.name}</span>
                      </button>
                    );
                  })}
                </div>
              </div>
            ))}
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
                      <p className="text-xs text-gray-500">Loading address suggestions...</p>
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
                    clearPendingPhotos();
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
              onClick={cancelForm}
              className="rounded-lg border border-gray-300 px-4 py-2 text-gray-700 hover:bg-gray-50 transition"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={
                isSavingListing ||
                saveButtonPhase === "saved" ||
                (!editingListingId && !meetsPhotoRequirement)
              }
              className={`inline-flex items-center gap-2 rounded-full border-2 border-black px-6 py-2.5 font-extrabold transition-all disabled:cursor-not-allowed disabled:opacity-40 ${
                saveButtonPhase === "saved"
                  ? "bg-vroom-bg text-vroom-heading"
                  : "bg-vroom-accent text-white hover:translate-y-[-2px] active:translate-y-0"
              }`}
            >
              {saveButtonPhase === "saving" && <Loader2 className="h-4 w-4 animate-spin" />}
              {saveButtonPhase === "saved" && <Check className="h-4 w-4" />}
              {saveButtonLabel()}
            </button>
          </div>
        </form>
      </div>

      <ListingCreatedModal
        listing={createSuccessListing}
        listingsTabId={listingsTabId}
        onViewListings={(tabId) => dismissCreateSuccess(tabId)}
        onPreview={() => {}}
      />
    </section>
  );
}
