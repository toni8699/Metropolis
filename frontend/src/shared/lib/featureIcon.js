import {
  Bluetooth,
  Check,
  KeyRound,
  ShieldCheck,
  Smartphone,
  Snowflake,
  Sun,
  UploadCloud,
} from "lucide-react";

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

export function featureIcon(iconKey) {
  return FEATURE_ICONS[iconKey] || Check;
}
