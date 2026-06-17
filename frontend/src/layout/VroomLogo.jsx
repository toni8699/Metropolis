export default function VroomLogo({ className = "" }) {
  return (
    <img
      src="/vroom-logo.svg"
      alt="VROOM Logo"
      className={`h-12 w-auto text-vroom-accent transition-transform hover:scale-110 ${className}`}
    />
  );
}
