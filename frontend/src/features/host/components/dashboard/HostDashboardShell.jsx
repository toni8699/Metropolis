export default function HostDashboardShell({ children }) {
  return (
    <div className="-mx-4 -mb-[var(--app-content-gap)] -mt-[var(--app-content-gap)] flex min-h-0 flex-1 overflow-hidden bg-vroom-bg sm:-mx-5 md:-mx-6 lg:-mx-7 xl:-mx-8">
      {children}
    </div>
  );
}
