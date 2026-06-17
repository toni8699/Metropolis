import { Send } from "lucide-react";

export default function ChatComposer({
  inputId,
  value,
  onChange,
  onSubmit,
  isSending = false,
  className = "mt-3 flex gap-2",
  buttonClassName = "inline-flex items-center gap-1 rounded-full border-2 border-black border-b-4 bg-vroom-accent px-3 py-2 text-sm font-extrabold text-white active:border-b-0 disabled:opacity-50",
}) {
  return (
    <form onSubmit={onSubmit} className={className}>
      <label htmlFor={inputId} className="sr-only">
        Message
      </label>
      <input
        id={inputId}
        type="text"
        value={value}
        onChange={onChange}
        placeholder="Write a message…"
        maxLength={4000}
        disabled={isSending}
        className="min-w-0 flex-1 rounded-full border-2 border-black bg-white px-4 py-2 text-sm text-vroom-heading placeholder:text-vroom-muted2 focus:outline-none disabled:bg-gray-100"
      />
      <button
        type="submit"
        disabled={!value.trim() || isSending}
        className={buttonClassName}
      >
        <Send className="h-4 w-4" />
        Send
      </button>
    </form>
  );
}
