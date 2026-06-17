import { useCallback, useRef, useState } from "react";
import { TAB } from "@/features/host/lib/dashboardNav";

export function useHostDashboardTabs() {
  const [activeTab, setActiveTab] = useState(TAB.overview);
  const confirmLeaveRef = useRef(() => true);

  const setConfirmLeaveIfDirty = useCallback((fn) => {
    confirmLeaveRef.current = fn;
  }, []);

  const requestTabChange = useCallback(
    (tabId) => {
      if (
        activeTab === TAB.create_listing &&
        tabId !== TAB.create_listing &&
        !confirmLeaveRef.current()
      ) {
        return;
      }
      setActiveTab(tabId);
    },
    [activeTab],
  );

  return { activeTab, setActiveTab, requestTabChange, setConfirmLeaveIfDirty };
}
