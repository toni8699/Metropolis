import { useEffect } from "react";

/** Close on mousedown outside ref. ponytail: one listener pattern for dropdowns/modals */
export function useClickOutside(ref, onOutside, enabled = true) {
  useEffect(() => {
    if (!enabled) return undefined;
    const handler = (event) => {
      if (ref.current && !ref.current.contains(event.target)) {
        onOutside(event);
      }
    };
    document.addEventListener("mousedown", handler);
    return () => document.removeEventListener("mousedown", handler);
  }, [ref, onOutside, enabled]);
}
