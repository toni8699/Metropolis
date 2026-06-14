export default function BodyCard({ children, className = "" }) {
  return (
    <div
      className={`rounded-[2rem] border-4 border-black bg-[#f5f5d0] shadow-[8px_8px_0px_0px_rgba(24,59,30,0.45)] ${className}`}
    >
      {children}
    </div>
  );
}
