import Footer from "@/layout/Footer";
import Header from "@/layout/Header";

export default function Layout({ children, onSearch, onHome }) {
  return (
    <div className="min-h-screen flex flex-col bg-white text-gray-900">
      <Header onSearch={onSearch} onHome={onHome} />
      <main className="w-full flex-grow pt-20 md:pt-[72px]">{children}</main>
      <Footer />
    </div>
  );
}
