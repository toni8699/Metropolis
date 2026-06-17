export default function UsersPanel({ users }) {
  return (
    <section className="mx-11 mt-6 mb-11 overflow-hidden rounded-2xl border-4 border-black bg-vroom-card shadow-neo">
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
  );
}
