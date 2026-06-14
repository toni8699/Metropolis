import Footer from "@/layout/Footer";
import Header from "@/layout/Header";

export default function Layout({ children, onSearch, onHome }) {
  return (
    <div className="min-h-screen flex flex-col bg-[#D0F0C0] text-[#2D5A27]">
      <Header onSearch={onSearch} onHome={onHome} />
      <main className="w-full flex-grow border-t-4 border-black pt-28 md:pt-[104px]">{children}</main>
      <Footer />
    </div>
  );
}
