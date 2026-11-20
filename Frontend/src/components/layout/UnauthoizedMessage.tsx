export function UnauthorizedMessage() {
  return (
    <div className="flex flex-col items-center justify-center h-screen bg-gray-100">
      <h1 className="text-2xl font-bold mb-4">Unauthorized Access</h1>
      <p className="text-gray-600 mb-6">
        You do not have permission to view this page.
      </p>
    </div>
  );
}
