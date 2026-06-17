export default function HostDashboardAlerts({ error, success }) {
  if (!error && !success) return null;

  return (
    <>
      {error && <p className="neo-error mx-11 mt-6">{error}</p>}
      {success && <p className="neo-success mx-11 mt-6">{success}</p>}
    </>
  );
}
