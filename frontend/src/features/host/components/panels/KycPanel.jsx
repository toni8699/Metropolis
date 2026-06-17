export default function KycPanel({ kycQueue, onDecision }) {
  return (
    <section className="mx-11 mt-6 mb-11 rounded-2xl border-4 border-black bg-vroom-card p-6 shadow-neo">
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
                  onClick={() => onDecision(item.userId, "VERIFIED")}
                  className="rounded-lg bg-emerald-600 px-3 py-1.5 text-sm font-medium text-white hover:bg-emerald-700"
                >
                  Approve
                </button>
                <button
                  type="button"
                  onClick={() => onDecision(item.userId, "REJECTED")}
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
  );
}
