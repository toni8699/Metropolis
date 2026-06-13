export default function VroomLogo({ className = "" }) {
  return (
    <img
      src="/vroom-logo.svg"
      alt="VROOM Logo"
      className={`h-12 w-auto text-[#E34B31] transition-transform hover:scale-110 ${className}`}
    />
  );
}
