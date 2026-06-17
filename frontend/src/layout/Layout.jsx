import Footer from "@/layout/Footer";
import Header from "@/layout/Header";

export default function Layout({ children, onSearch, onHome }) {
  return (
    <div className="min-h-screen flex flex-col bg-[#D0F0C0] text-[#2D5A27]">
      <Header onSearch={onSearch} onHome={onHome} />
      <main className="w-full flex-grow border-t-4 border-black pt-[var(--app-header-offset)]">
        <div className="px-4 py-[var(--app-content-gap)] sm:px-5 md:px-6 lg:px-7 xl:px-8">
          {children}
        </div>
      </main>
      <Footer />
    </div>
  );
}
